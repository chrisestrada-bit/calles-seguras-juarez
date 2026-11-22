"""Hora oficial (RN-02): se almacena en UTC y se muestra/calcula en America/Ciudad_Juarez."""

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from app.core.config import get_settings

ZONA = ZoneInfo(get_settings().app_timezone)


def ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


def a_local(valor: datetime) -> datetime:
    """Convierte un datetime (UTC si es ingenuo) a la zona horaria oficial."""
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(ZONA)


def hoy_local() -> date:
    return a_local(ahora_utc()).date()


def fecha_local(valor: datetime) -> date:
    return a_local(valor).date()
