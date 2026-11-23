"""Exportación de reportes a CSV y XML (HU-07.3) y validación XSD. Nunca incluye datos personales (RN-04)."""

import csv
import io
from pathlib import Path

from lxml import etree

from app.core.config import get_settings
from app.core.errores import ErrorAPI
from app.core.tiempo import a_local, ahora_utc
from app.models import Reporte

LIMITE_EXPORTACION = 50_000
COLUMNAS_CSV = ["folio", "tipo_dano", "ubicacion", "colonia", "estado", "fecha_creacion", "fecha_actualizacion"]
NS_REPORTES = "https://callesseguras.juarez.mx/esquemas/reportes/v1"
_PREFIJOS_FORMULA = ("=", "+", "-", "@", "\t", "\r")


def directorio_esquemas() -> Path:
    """docs/esquemas en el repositorio o /srv/docs/esquemas en la imagen Docker."""
    aqui = Path(__file__).resolve()
    for padre in aqui.parents:
        candidato = padre / "docs" / "esquemas"
        if candidato.is_dir():
            return candidato
    raise RuntimeError("No se encontró el directorio docs/esquemas con los esquemas XSD.")


_cache_xsd: dict[str, etree.XMLSchema] = {}


def cargar_esquema(nombre: str) -> etree.XMLSchema:
    if nombre not in _cache_xsd:
        _cache_xsd[nombre] = etree.XMLSchema(etree.parse(str(directorio_esquemas() / nombre)))
    return _cache_xsd[nombre]


def _fecha_iso(valor) -> str:
    return a_local(valor).replace(microsecond=0).isoformat()  # RN-02


def _celda_segura(valor: str) -> str:
    """Evita inyección de fórmulas al abrir el CSV en una hoja de cálculo."""
    return "'" + valor if valor.startswith(_PREFIJOS_FORMULA) else valor


def _valores(r: Reporte, *, csv_seguro: bool) -> list[str]:
    proteger = _celda_segura if csv_seguro else (lambda v: v)
    return [
        r.folio,
        r.tipo_dano.value,
        proteger(r.calle),
        proteger(r.colonia.nombre),
        r.estado.value,
        _fecha_iso(r.created_at),
        _fecha_iso(r.updated_at),
    ]


def generar_csv(reportes: list[Reporte]) -> bytes:
    """UTF-8 con BOM para que Excel respete acentos y la letra «ñ»."""
    salida = io.StringIO(newline="")
    escritor = csv.writer(salida, lineterminator="\r\n")
    escritor.writerow(COLUMNAS_CSV)
    for r in reportes:
        escritor.writerow(_valores(r, csv_seguro=True))
    return salida.getvalue().encode("utf-8-sig")


def generar_xml(reportes: list[Reporte]) -> bytes:
    raiz = etree.Element(
        f"{{{NS_REPORTES}}}reportes",
        nsmap={None: NS_REPORTES},
        version="1",
        generado=_fecha_iso(ahora_utc()),
        zona_horaria=get_settings().app_timezone,
        total=str(len(reportes)),
    )
    for r in reportes:
        nodo = etree.SubElement(raiz, f"{{{NS_REPORTES}}}reporte")
        for nombre, valor in zip(COLUMNAS_CSV, _valores(r, csv_seguro=False), strict=True):
            etree.SubElement(nodo, f"{{{NS_REPORTES}}}{nombre}").text = valor
    esquema = cargar_esquema("reportes_v1.xsd")
    if not esquema.validate(raiz):
        raise ErrorAPI(
            500,
            "XML_INVALIDO",
            "No se pudo generar un XML válido. Intenta de nuevo o avisa a un coordinador.",
            [{"mensaje": str(e.message)} for e in list(esquema.error_log)[:5]],
        )
    return etree.tostring(raiz, xml_declaration=True, encoding="UTF-8", pretty_print=True)
