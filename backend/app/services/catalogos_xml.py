"""Importación de catálogos territoriales desde XML validado con XSD (Punto extra 4.4)."""

from dataclasses import dataclass, field

from lxml import etree
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errores import ErrorAPI
from app.models import Colonia, Sector
from app.services.exportacion import cargar_esquema
from app.services.geo import es_codigo_postal_juarez

NS = "{https://callesseguras.juarez.mx/esquemas/catalogos/v1}"
MAX_BYTES_XML = 2 * 1024 * 1024
_MSG_INTEGRIDAD = "El XML rompe la integridad de los catálogos. No se importó nada."


@dataclass
class Resultado:
    sectores_creados: int = 0
    sectores_actualizados: int = 0
    colonias_creadas: int = 0
    colonias_actualizadas: int = 0
    errores: list[dict] = field(default_factory=list)


def _error(status: int, mensaje: str, detalles: list[dict]) -> ErrorAPI:
    return ErrorAPI(status, "XML_INVALIDO", mensaje, detalles)


def analizar(contenido: bytes):
    """Analiza el XML sin resolver entidades externas ni acceder a la red (previene XXE y «billion laughs»)."""
    if not contenido.strip():
        raise _error(422, "El archivo XML está vacío.", [])
    if len(contenido) > MAX_BYTES_XML:
        raise _error(413, "El archivo XML supera el máximo de 2 MB.", [])
    parser = etree.XMLParser(
        resolve_entities=False, no_network=True, huge_tree=False, load_dtd=False, dtd_validation=False
    )
    try:
        raiz = etree.fromstring(contenido, parser)
    except etree.XMLSyntaxError as exc:
        raise _error(
            422, "El XML está mal formado.", [{"linea": exc.lineno, "mensaje": f"Error de sintaxis XML: {exc.msg}."}]
        ) from None
    if raiz.getroottree().docinfo.doctype:
        raise _error(422, "No se permiten declaraciones DOCTYPE en el XML.", [])
    esquema = cargar_esquema("catalogos_v1.xsd")
    if not esquema.validate(raiz):
        raise _error(
            422,
            "El XML no cumple con el esquema catalogos_v1.xsd.",
            [{"linea": e.line, "mensaje": str(e.message)} for e in list(esquema.error_log)[:20]],
        )
    return raiz


def _bool(valor: str | None) -> bool:
    return valor is None or valor.lower() in ("true", "1")


def _validar_integridad(db: Session, sectores_xml: list, colonias_xml: list) -> list[dict]:
    errores: list[dict] = []
    conocidas = {s.get("clave") for s in sectores_xml} | set(db.scalars(select(Sector.clave)))
    vistas: set[tuple[str, str]] = set()
    for c in colonias_xml:
        nombre, clave = c.get("nombre"), c.get("sector_clave")
        if clave not in conocidas:
            errores.append(
                {
                    "linea": c.sourceline,
                    "campo": "sector_clave",
                    "mensaje": f"La colonia «{nombre}» referencia el sector «{clave}», "
                    "que no existe en la base ni se declara en el XML.",
                }
            )
        cp = c.get("codigo_postal")
        if cp and not es_codigo_postal_juarez(cp):
            errores.append(
                {"linea": c.sourceline, "campo": "codigo_postal", "mensaje": f"El código postal {cp} no es de Ciudad Juárez."}
            )
        llave = (clave, nombre.lower())
        if llave in vistas:
            errores.append(
                {"linea": c.sourceline, "campo": "nombre", "mensaje": f"La colonia «{nombre}» está repetida en el XML."}
            )
        vistas.add(llave)
    return errores


def importar(db: Session, contenido: bytes) -> Resultado:
    raiz = analizar(contenido)
    sectores_xml = raiz.findall(f"{NS}sectores/{NS}sector")
    colonias_xml = raiz.findall(f"{NS}colonias/{NS}colonia")

    errores = _validar_integridad(db, sectores_xml, colonias_xml)
    if errores:
        raise _error(422, _MSG_INTEGRIDAD, errores)

    res = Resultado()
    sectores: dict[str, Sector] = {s.clave: s for s in db.scalars(select(Sector))}
    for nodo in sectores_xml:
        clave, nombre, activo = nodo.get("clave"), nodo.get("nombre"), _bool(nodo.get("activo"))
        sector = sectores.get(clave)
        if sector is None:
            choque = db.scalar(select(Sector.id).where(func.lower(Sector.nombre) == nombre.lower()))
            if choque is not None:
                res.errores.append(
                    {"linea": nodo.sourceline, "campo": "nombre", "mensaje": f"Ya existe otro sector llamado «{nombre}»."}
                )
                continue
            sector = Sector(clave=clave, nombre=nombre, activo=activo)
            db.add(sector)
            db.flush()
            sectores[clave] = sector
            res.sectores_creados += 1
        elif sector.nombre != nombre or sector.activo != activo:
            sector.nombre, sector.activo = nombre, activo
            res.sectores_actualizados += 1
    if res.errores:
        db.rollback()
        raise _error(422, _MSG_INTEGRIDAD, res.errores)

    for nodo in colonias_xml:
        sector = sectores[nodo.get("sector_clave")]
        nombre = nodo.get("nombre")
        existente = db.scalar(
            select(Colonia).where(Colonia.sector_id == sector.id, func.lower(Colonia.nombre) == nombre.lower())
        )
        valores = {
            "codigo_postal": nodo.get("codigo_postal"),
            "latitud_centro": float(nodo.get("latitud_centro")),
            "longitud_centro": float(nodo.get("longitud_centro")),
            "activo": _bool(nodo.get("activo")),
        }
        if existente is None:
            db.add(Colonia(sector_id=sector.id, nombre=nombre, **valores))
            res.colonias_creadas += 1
        else:
            for campo, valor in valores.items():
                setattr(existente, campo, valor)
            res.colonias_actualizadas += 1
    db.commit()  # todo o nada
    return res
