"""Geocodificación (HU-02.1, HU-04.3): proxy hacia LocationIQ restringido a Ciudad Juárez (RN-01).

* Búsqueda por texto (calle, cruce, colonia) o por código postal de Juárez (32000–32730).
* Geocodificación inversa: de una coordenada dentro de Juárez a calle y colonia sugeridas.
* Si LocationIQ no está configurado o falla, se responde con el catálogo local de colonias.

La llave GEOCODING_API_KEY sólo vive aquí (backend): jamás se devuelve, ni se registra en logs.
"""

import logging
import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errores import fuera_de_juarez
from app.models import Colonia
from app.schemas.comun import SectorRef, Ubicacion
from app.schemas.geocoding import (
    ColoniaCercana,
    ColoniaSugerida,
    RespuestaGeocodificacion,
    RespuestaGeocodificacionInversa,
    ResultadoGeocodificacion,
)
from app.services.sqlutil import error_validacion
from app.services import catalogos, geo

logger = logging.getLogger("calles_seguras.geocoding")

# httpx registra la URL completa (con ?key=...) en nivel INFO: se silencia para no filtrar la llave.
for _nombre in ("httpx", "httpcore"):
    logging.getLogger(_nombre).setLevel(logging.WARNING)

SUFIJO_CIUDAD = "Ciudad Juárez, Chihuahua"
ATRIBUCION = "Búsqueda por LocationIQ.com · Datos © colaboradores de OpenStreetMap"
MENSAJE_FALLBACK = (
    "El buscador de direcciones no está disponible en este momento. Te mostramos colonias que coinciden "
    "(ubicación aproximada al centro de la colonia); para indicar el punto exacto usa tu ubicación GPS "
    "estando en el lugar del daño."
)
MENSAJE_CP = "Colonias del código postal {cp} (ubicación aproximada al centro de cada colonia)."
MENSAJE_CP_SIN_COLONIAS = "No tenemos colonias registradas con el código postal {cp}. Prueba con el nombre de la colonia."
MENSAJE_INVERSA_LOCAL = (
    "Sugerimos la colonia registrada más cercana al punto. Confirma la colonia y escribe el nombre de la calle."
)
DISTANCIA_MAX_COLONIA_M = 1_500
COLONIAS_CERCANAS = 3
SIMILITUD_NOMBRE = 0.8


class _ProveedorNoDisponible(Exception):
    pass


def limpiar_consulta(texto: str) -> str:
    sin_control = "".join(c for c in texto if unicodedata.category(c)[0] != "C" or c in "\t ")
    return re.sub(r"\s+", " ", sin_control).strip()


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", texto.lower())
    return re.sub(r"[^a-z0-9 ]", "", "".join(c for c in base if not unicodedata.combining(c))).strip()


def _consultar_locationiq(q: str, limite: int) -> list[dict[str, Any]]:
    s = get_settings()
    try:
        respuesta = httpx.get(
            f"{s.geocoding_api_url.rstrip('/')}/search",
            params={
                "key": s.geocoding_api_key.get_secret_value(),
                "q": f"{q}, {SUFIJO_CIUDAD}",
                "format": "json",
                "addressdetails": 1,
                "countrycodes": "mx",
                "accept-language": "es",
                "viewbox": f"{geo.LON_MIN},{geo.LAT_MAX},{geo.LON_MAX},{geo.LAT_MIN}",
                "bounded": 1,
                "limit": limite,
            },
            timeout=s.geocoding_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        # Sólo el tipo: el texto de la excepción puede contener la URL con la llave.
        logger.warning("LocationIQ no respondió (%s)", type(exc).__name__)
        raise _ProveedorNoDisponible from None

    if respuesta.status_code == 404:  # LocationIQ responde 404 cuando no hay coincidencias
        return []
    if respuesta.status_code != 200:
        logger.warning("LocationIQ respondió HTTP %s", respuesta.status_code)
        raise _ProveedorNoDisponible
    try:
        datos = respuesta.json()
    except ValueError:
        logger.warning("LocationIQ devolvió un cuerpo no JSON")
        raise _ProveedorNoDisponible from None
    if not isinstance(datos, list):
        raise _ProveedorNoDisponible
    return datos


def _sugerir_colonia(colonias: list[Colonia], barrio: str | None, lat: float, lon: float) -> ColoniaSugerida | None:
    elegida: Colonia | None = None
    if barrio:
        objetivo = _normalizar(barrio)
        mejor = 0.0
        for c in colonias:
            similitud = SequenceMatcher(None, objetivo, _normalizar(c.nombre)).ratio()
            if similitud > mejor:
                mejor, elegida = similitud, c
        if mejor < SIMILITUD_NOMBRE:
            elegida = None
    if elegida is None:
        distancia, cercana = min(
            ((geo.haversine_m(lat, lon, c.latitud_centro, c.longitud_centro), c) for c in colonias),
            key=lambda par: par[0],
            default=(float("inf"), None),
        )
        if cercana is not None and distancia <= DISTANCIA_MAX_COLONIA_M:
            elegida = cercana
    if elegida is None:
        return None
    return _sugerida(elegida)


def _sugerida(c: Colonia) -> ColoniaSugerida:
    return ColoniaSugerida(
        id=c.id,
        nombre=c.nombre,
        codigo_postal=c.codigo_postal,
        sector=SectorRef(id=c.sector.id, nombre=c.sector.nombre),
    )


def _resultado(item: dict[str, Any], colonias: list[Colonia]) -> ResultadoGeocodificacion | None:
    try:
        lat, lon = float(item["lat"]), float(item["lon"])
    except (KeyError, TypeError, ValueError):
        return None
    if not geo.dentro_de_juarez(lat, lon):  # RN-01: se descarta lo que quede fuera del municipio
        return None
    direccion = item.get("address") or {}
    calle = direccion.get("road") or direccion.get("pedestrian") or direccion.get("footway")
    barrio = direccion.get("neighbourhood") or direccion.get("suburb") or direccion.get("quarter")
    if direccion.get("house_number"):
        precision = "direccion"
    elif calle:
        precision = "calle"
    elif barrio:
        precision = "colonia"
    else:
        precision = "aproximada"
    partes = [p for p in (calle, barrio) if p]
    etiqueta = ", ".join([*partes, SUFIJO_CIUDAD]) if partes else str(item.get("display_name", SUFIJO_CIUDAD))
    return ResultadoGeocodificacion(
        etiqueta=etiqueta,
        calle=calle,
        ubicacion=Ubicacion(latitud=round(lat, 6), longitud=round(lon, 6)),
        precision=precision,  # type: ignore[arg-type]
        colonia_sugerida=_sugerir_colonia(colonias, barrio, lat, lon),
    )


def _fallback_local(db: Session, q: str, limite: int) -> RespuestaGeocodificacion:
    """Si LocationIQ falla: colonias del catálogo local, con su centro como coordenada aproximada."""
    encontradas, _ = catalogos.buscar_colonias(db, q=q, sector_id=None, limite=limite)
    datos = [
        ResultadoGeocodificacion(
            etiqueta=f"{c.nombre}, {c.sector.nombre}, {SUFIJO_CIUDAD}",
            calle=None,
            ubicacion=Ubicacion(latitud=c.latitud_centro, longitud=c.longitud_centro),
            precision="aproximada",
            colonia_sugerida=_sugerida(c),
        )
        for c in encontradas
    ]
    return RespuestaGeocodificacion(
        fuente="catalogo_local", degradado=True, datos=datos, atribucion=None, mensaje=MENSAJE_FALLBACK
    )


def _por_codigo_postal(db: Session, cp: str, limite: int) -> RespuestaGeocodificacion:
    """Un código postal se resuelve con el catálogo local: es la fuente de verdad de colonias y CP."""
    if not geo.es_codigo_postal_juarez(cp):  # RN-01: sólo códigos postales del municipio
        raise error_validacion(
            "q", f"El código postal {cp} no pertenece a Ciudad Juárez ({geo.CP_MIN}–{geo.CP_MAX})."
        )
    encontradas, _ = catalogos.buscar_colonias(db, q=cp, sector_id=None, limite=limite)
    datos = [
        ResultadoGeocodificacion(
            etiqueta=f"{c.nombre}, C.P. {c.codigo_postal}, {SUFIJO_CIUDAD}",
            calle=None,
            ubicacion=Ubicacion(latitud=c.latitud_centro, longitud=c.longitud_centro),
            precision="colonia",
            colonia_sugerida=_sugerida(c),
        )
        for c in encontradas
    ]
    mensaje = (MENSAJE_CP if datos else MENSAJE_CP_SIN_COLONIAS).format(cp=cp)
    return RespuestaGeocodificacion(
        fuente="catalogo_local", degradado=False, datos=datos, atribucion=None, mensaje=mensaje
    )


def buscar(db: Session, q: str, limite: int) -> RespuestaGeocodificacion:
    """Nunca propaga errores del proveedor: degrada al catálogo local (siempre HTTP 200)."""
    if catalogos.es_prefijo_cp(q) and len(q) == 5:
        return _por_codigo_postal(db, q, limite)
    if get_settings().geocoding_api_key.get_secret_value():
        try:
            crudos = _consultar_locationiq(q, limite)
        except _ProveedorNoDisponible:
            return _fallback_local(db, q, limite)
        colonias = list(db.scalars(select(Colonia).where(Colonia.activo)))
        datos = [r for r in (_resultado(i, colonias) for i in crudos) if r is not None][:limite]
        return RespuestaGeocodificacion(
            fuente="locationiq", degradado=False, datos=datos, atribucion=ATRIBUCION, mensaje=None
        )
    logger.warning("GEOCODING_API_KEY no está configurada; se usa el catálogo local")
    return _fallback_local(db, q, limite)


# --------------------------------------------------------------------------- geocodificación inversa


def _consultar_locationiq_inversa(latitud: float, longitud: float) -> dict[str, Any]:
    s = get_settings()
    try:
        respuesta = httpx.get(
            f"{s.geocoding_api_url.rstrip('/')}/reverse",
            params={
                "key": s.geocoding_api_key.get_secret_value(),
                "lat": latitud,
                "lon": longitud,
                "format": "json",
                "addressdetails": 1,
                "accept-language": "es",
            },
            timeout=s.geocoding_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        # Sólo el tipo: el texto de la excepción puede contener la URL con la llave.
        logger.warning("LocationIQ (inversa) no respondió (%s)", type(exc).__name__)
        raise _ProveedorNoDisponible from None
    if respuesta.status_code != 200:
        logger.warning("LocationIQ (inversa) respondió HTTP %s", respuesta.status_code)
        raise _ProveedorNoDisponible
    try:
        datos = respuesta.json()
    except ValueError:
        raise _ProveedorNoDisponible from None
    if not isinstance(datos, dict):
        raise _ProveedorNoDisponible
    return datos


def _cercanas(colonias: list[Colonia], latitud: float, longitud: float) -> list[ColoniaCercana]:
    ordenadas = sorted(
        ((geo.haversine_m(latitud, longitud, c.latitud_centro, c.longitud_centro), c) for c in colonias),
        key=lambda par: par[0],
    )[:COLONIAS_CERCANAS]
    return [ColoniaCercana(**_sugerida(c).model_dump(), distancia_metros=round(d, 1)) for d, c in ordenadas]


def inversa(db: Session, latitud: float, longitud: float) -> RespuestaGeocodificacionInversa:
    """Coordenada → calle y colonia. RN-01: fuera de Juárez responde 422 FUERA_DE_JUAREZ."""
    if not geo.dentro_de_juarez(latitud, longitud):
        campo = "latitud" if not geo.LAT_MIN <= latitud <= geo.LAT_MAX else "longitud"
        raise fuera_de_juarez(campo, "La coordenada debe estar dentro de Ciudad Juárez, Chihuahua.")
    colonias = list(db.scalars(select(Colonia).where(Colonia.activo)))
    cercanas = _cercanas(colonias, latitud, longitud)
    ubicacion = Ubicacion(latitud=round(latitud, 6), longitud=round(longitud, 6))

    if get_settings().geocoding_api_key.get_secret_value():
        try:
            crudo: dict[str, Any] | None = _consultar_locationiq_inversa(latitud, longitud)
        except _ProveedorNoDisponible:
            crudo = None
        if crudo is not None:
            direccion = crudo.get("address") or {}
            calle = direccion.get("road") or direccion.get("pedestrian") or direccion.get("footway")
            barrio = direccion.get("neighbourhood") or direccion.get("suburb") or direccion.get("quarter")
            partes = [p for p in (calle, barrio) if p]
            return RespuestaGeocodificacionInversa(
                fuente="locationiq",
                degradado=False,
                ubicacion=ubicacion,
                calle=calle,
                etiqueta=", ".join([*partes, SUFIJO_CIUDAD]),
                colonia_sugerida=_sugerir_colonia(colonias, barrio, latitud, longitud),
                colonias_cercanas=cercanas,
                atribucion=ATRIBUCION,
                mensaje=None,
            )

    sugerida = None
    if cercanas and cercanas[0].distancia_metros <= DISTANCIA_MAX_COLONIA_M:
        sugerida = ColoniaSugerida(**cercanas[0].model_dump(exclude={"distancia_metros"}))
    return RespuestaGeocodificacionInversa(
        fuente="catalogo_local",
        degradado=True,
        ubicacion=ubicacion,
        calle=None,
        etiqueta=f"{sugerida.nombre}, {SUFIJO_CIUDAD}" if sugerida else SUFIJO_CIUDAD,
        colonia_sugerida=sugerida,
        colonias_cercanas=cercanas,
        atribucion=None,
        mensaje=MENSAJE_INVERSA_LOCAL,
    )
