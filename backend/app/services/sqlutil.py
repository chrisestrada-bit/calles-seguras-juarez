"""Utilidades de consulta compartidas."""

from datetime import date

from sqlalchemy import Date, cast, func
from sqlalchemy.sql.elements import ColumnElement

from app.core.config import get_settings
from app.core.errores import ErrorAPI
from app.services.geo import LAT_MAX, LAT_MIN, LON_MAX, LON_MIN


def fecha_local_sql(columna: ColumnElement) -> ColumnElement:
    """Fecha calendario en America/Ciudad_Juarez de una columna timestamptz (RN-02)."""
    return cast(func.timezone(get_settings().app_timezone, columna), Date)


def hoy_local_sql() -> ColumnElement:
    return fecha_local_sql(func.now())


def escapar_like(texto: str) -> str:
    return texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def error_validacion(campo: str, mensaje: str) -> ErrorAPI:
    return ErrorAPI(422, "VALIDACION", "Revisa los datos marcados.", [{"campo": campo, "mensaje": mensaje}])


def validar_rango_fechas(desde: date | None, hasta: date | None) -> None:
    if desde and hasta and desde > hasta:
        raise error_validacion("desde", "La fecha inicial no puede ser posterior a la final.")


def parsear_bbox(bbox: str) -> tuple[float, float, float, float]:
    """'lon_min,lat_min,lon_max,lat_max' recortado a los límites de Ciudad Juárez (RN-01)."""
    try:
        lon_min, lat_min, lon_max, lat_max = (float(p) for p in bbox.split(","))
    except ValueError:
        raise error_validacion("bbox", "Usa el formato lon_min,lat_min,lon_max,lat_max.") from None
    if lon_min >= lon_max or lat_min >= lat_max:
        raise error_validacion("bbox", "Los valores mínimos deben ser menores que los máximos.")
    return (
        max(lon_min, LON_MIN),
        max(lat_min, LAT_MIN),
        min(lon_max, LON_MAX),
        min(lat_max, LAT_MAX),
    )
