"""Pronóstico (caché en cache_clima) y riesgo de inundación por calle."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errores import ErrorAPI
from app.core.tiempo import ahora_utc
from app.models import CacheClima, Colonia, EstadoReporte, NivelAgua, Reporte, TipoDano
from app.schemas.comun import ColoniaRef, SectorRef
from app.services.sqlutil import escapar_like, parsear_bbox

logger = logging.getLogger("calles_seguras.clima")

CLAVE_CONSULTA = "pronostico:juarez"
LATITUD_CENTRO, LONGITUD_CENTRO = 31.690400, -106.424500
HORAS_PRONOSTICO = 6
UMBRAL_PROBABILIDAD_PCT = 60
UMBRAL_PRECIPITACION_MM = 1.0

# D-24: después de un fallo del proveedor no se vuelve a consultar hasta este instante (por proceso).
_sin_reintentos_hasta: datetime | None = None

_DESCRIPCIONES = {
    0: "Cielo despejado", 1: "Mayormente despejado", 2: "Parcialmente nublado", 3: "Nublado",
    45: "Niebla", 48: "Niebla con escarcha", 51: "Llovizna ligera", 53: "Llovizna moderada",
    55: "Llovizna intensa", 61: "Lluvia ligera", 63: "Lluvia moderada", 65: "Lluvia fuerte",
    66: "Lluvia helada ligera", 67: "Lluvia helada fuerte", 71: "Nevada ligera", 73: "Nevada moderada",
    75: "Nevada fuerte", 80: "Chubascos ligeros", 81: "Chubascos moderados", 82: "Chubascos fuertes",
    95: "Tormenta eléctrica", 96: "Tormenta con granizo ligero", 99: "Tormenta con granizo fuerte",
}


def _consultar_proveedor() -> dict[str, Any]:
    s = get_settings()
    respuesta = httpx.get(
        s.weather_api_url,
        params={
            "latitude": LATITUD_CENTRO,
            "longitude": LONGITUD_CENTRO,
            "current": "temperature_2m,precipitation,weather_code",
            "hourly": "precipitation_probability,precipitation",
            "forecast_days": 2,
            "timezone": "UTC",
        },
        headers={"User-Agent": s.weather_user_agent, "Accept": "application/json"},
        timeout=s.weather_timeout_seconds,
        follow_redirects=True,
    )
    respuesta.raise_for_status()
    crudo = respuesta.json()
    actual = crudo["current"]
    horas = crudo["hourly"]
    return {  # respuesta normalizada: sin encabezados ni datos del proveedor
        "actual": {
            "temperatura_c": actual.get("temperature_2m"),
            "precipitacion_mm": actual.get("precipitation"),
            "descripcion": _DESCRIPCIONES.get(actual.get("weather_code"), "Sin descripción"),
        },
        "horas": [
            {"hora": f"{hora}:00+00:00" if len(hora) == 16 else hora, "prob": prob, "mm": mm}
            for hora, prob, mm in zip(
                horas["time"], horas["precipitation_probability"], horas["precipitation"], strict=True
            )
        ],
    }


def _proximas_horas(normalizada: dict[str, Any], ahora: datetime) -> list[dict[str, Any]]:
    inicio = ahora.replace(minute=0, second=0, microsecond=0)
    resultado = []
    for h in normalizada["horas"]:
        hora = datetime.fromisoformat(h["hora"]).astimezone(timezone.utc)
        if hora >= inicio:
            resultado.append({"hora": hora, "probabilidad_lluvia_pct": h["prob"], "precipitacion_mm": h["mm"]})
        if len(resultado) == HORAS_PRONOSTICO:
            break
    return resultado


def _armar(normalizada: dict[str, Any], obtenido: datetime, desactualizado: bool) -> dict[str, Any]:
    ahora = ahora_utc()
    horas = _proximas_horas(normalizada, ahora)
    actual = normalizada["actual"]
    alerta = (actual.get("precipitacion_mm") or 0) > 0 or any(
        (h["probabilidad_lluvia_pct"] or 0) >= UMBRAL_PROBABILIDAD_PCT
        or (h["precipitacion_mm"] or 0) >= UMBRAL_PRECIPITACION_MM
        for h in horas
    )
    return {
        "ubicacion": "Ciudad Juárez, Chihuahua",
        "actual": actual,
        "proximas_horas": horas,
        "alerta_lluvia": alerta,
        "mensaje_alerta": (
            "Se esperan lluvias en las próximas horas. Consulta las calles con riesgo de inundación antes de salir."
            if alerta
            else None
        ),
        "obtenido_en": obtenido,
        "desactualizado": desactualizado,
    }


def _degradado(cache: CacheClima | None) -> dict[str, Any]:
    """Degradación elegante: última respuesta guardada (marcada desactualizada) o 503 si no hay ninguna."""
    if cache is not None:
        return _armar(cache.respuesta, cache.obtenido_at, True)
    raise ErrorAPI(503, "CLIMA_NO_DISPONIBLE", "El servicio de clima no está disponible en este momento.")


def reiniciar_retroceso() -> None:
    global _sin_reintentos_hasta
    _sin_reintentos_hasta = None


def obtener_pronostico(db: Session) -> dict[str, Any]:
    s = get_settings()
    ahora = ahora_utc()
    cache = db.scalar(select(CacheClima).where(CacheClima.clave_consulta == CLAVE_CONSULTA))
    if cache is not None:  # RN-02: las columnas son UTC; si llegaran ingenuas, se asume UTC para poder restar/comparar
        for campo in ("obtenido_at", "expira_at"):
            valor = getattr(cache, campo)
            if valor.tzinfo is None:
                setattr(cache, campo, valor.replace(tzinfo=timezone.utc))
    if cache is not None and cache.expira_at > ahora:
        return _armar(cache.respuesta, cache.obtenido_at, False)

    global _sin_reintentos_hasta
    if _sin_reintentos_hasta is not None and ahora < _sin_reintentos_hasta:
        return _degradado(cache)  # retroceso: no se espera otro timeout del proveedor

    try:
        normalizada = _consultar_proveedor()
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        # Sólo el tipo de error: el mensaje de httpx puede incluir la URL completa.
        estado_http = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else "-"
        logger.warning("Proveedor de clima no disponible (%s, HTTP %s)", type(exc).__name__, estado_http)
        _sin_reintentos_hasta = ahora + timedelta(minutes=s.weather_backoff_minutes)
        return _degradado(cache)
    _sin_reintentos_hasta = None

    horas = _proximas_horas(normalizada, ahora)
    valores = {
        "clave_consulta": CLAVE_CONSULTA,
        "latitud": LATITUD_CENTRO,
        "longitud": LONGITUD_CENTRO,
        "respuesta": normalizada,
        "probabilidad_lluvia_pct": max((h["probabilidad_lluvia_pct"] or 0 for h in horas), default=None),
        "precipitacion_mm": round(sum(h["precipitacion_mm"] or 0 for h in horas), 2) if horas else None,
        "obtenido_at": ahora,
        "expira_at": ahora + timedelta(minutes=s.weather_cache_ttl_minutes),
    }
    db.execute(
        pg_insert(CacheClima)
        .values(**valores)
        .on_conflict_do_update(index_elements=[CacheClima.clave_consulta], set_={k: v for k, v in valores.items() if k != "clave_consulta"})
    )
    db.commit()
    return _armar(normalizada, ahora, False)


def hay_alerta_lluvia(db: Session) -> bool:
    try:
        return bool(obtener_pronostico(db)["alerta_lluvia"])
    except ErrorAPI:
        return False


# --------------------------------------------------------------------------- riesgo por calle

CRITERIO_RIESGO = (
    "Alto: activo 'intransitable' o 'a media llanta', o ≥ 10 históricos con alerta de lluvia; "
    "Medio: cualquier activo o ≥ 3 históricos; Bajo: resto."
)
_GRAVEDAD = {
    NivelAgua.A_UN_LADO: 0,
    NivelAgua.CUBRE_CARRIL: 1,
    NivelAgua.A_MEDIA_LLANTA: 2,
    NivelAgua.INTRANSITABLE: 3,
}
_ORDEN_RIESGO = {"Alto": 0, "Medio": 1, "Bajo": 2}


def _nivel(activos: list[Reporte], historicos: int, alerta: bool) -> str:
    peor = max((_GRAVEDAD[r.nivel_agua] for r in activos), default=-1)  # type: ignore[index]
    if peor >= _GRAVEDAD[NivelAgua.A_MEDIA_LLANTA] or (historicos >= 10 and alerta):
        return "Alto"
    if activos or historicos >= 3:
        return "Medio"
    return "Bajo"


def _recomendacion(nivel: str, activos: list[Reporte]) -> str:
    if any(r.nivel_agua == NivelAgua.INTRANSITABLE for r in activos):
        return "Evita circular por esta calle: hay un encharcamiento intransitable reportado."
    if nivel == "Alto":
        return "Circula con extrema precaución o busca una ruta alterna: hay riesgo alto de inundación."
    if nivel == "Medio":
        return "Circula con precaución: la calle ha presentado encharcamientos."
    return "Sin riesgo relevante por ahora."


def riesgo_inundacion(
    db: Session,
    *,
    sector_id: int | None,
    colonia_id: int | None,
    calle: str | None,
    bbox: str | None,
    limite: int,
) -> dict[str, Any]:
    ahora = ahora_utc()
    condiciones = [
        Reporte.tipo_dano == TipoDano.ENCHARCAMIENTO,
        Reporte.estado.in_([EstadoReporte.ACTIVO, EstadoReporte.HISTORICO]),  # los históricos siguen contando
        Reporte.created_at >= ahora - timedelta(days=365),
    ]
    if sector_id:
        condiciones.append(Colonia.sector_id == sector_id)
    if colonia_id:
        condiciones.append(Reporte.colonia_id == colonia_id)
    if calle:
        condiciones.append(Reporte.calle.ilike(f"%{escapar_like(calle)}%", escape="\\"))
    if bbox:
        lon_min, lat_min, lon_max, lat_max = parsear_bbox(bbox)
        condiciones += [Reporte.latitud.between(lat_min, lat_max), Reporte.longitud.between(lon_min, lon_max)]

    reportes = db.scalars(
        select(Reporte).join(Colonia, Reporte.colonia_id == Colonia.id).where(*condiciones).order_by(Reporte.created_at.desc())
    ).all()

    por_calle: dict[str, list[Reporte]] = {}
    for r in reportes:  # más recientes primero: la colonia mostrada es la del reporte más reciente
        por_calle.setdefault(" ".join(r.calle.lower().split()), []).append(r)

    alerta = hay_alerta_lluvia(db)
    filas = []
    for grupo in por_calle.values():
        activos = [r for r in grupo if r.estado == EstadoReporte.ACTIVO and r.vigente_hasta and r.vigente_hasta > ahora]
        historicos = len(grupo) - len(activos)
        nivel = _nivel(activos, historicos, alerta)
        reciente = grupo[0]
        peor = max(activos, key=lambda r: _GRAVEDAD[r.nivel_agua], default=None)  # type: ignore[index]
        filas.append(
            {
                "calle": reciente.calle,
                "colonia": ColoniaRef(id=reciente.colonia.id, nombre=reciente.colonia.nombre),
                "sector": SectorRef(id=reciente.colonia.sector.id, nombre=reciente.colonia.sector.nombre),
                "nivel_riesgo": nivel,
                "encharcamientos_activos": len(activos),
                "nivel_agua_maximo_activo": peor.nivel_agua.value if peor else None,
                "encharcamientos_historicos_12_meses": historicos,
                "ultimo_reporte": reciente.created_at,
                "folios_activos": [r.folio for r in activos],
                "recomendacion": _recomendacion(nivel, activos),
            }
        )
    filas.sort(
        key=lambda f: (
            _ORDEN_RIESGO[f["nivel_riesgo"]],
            -f["encharcamientos_activos"],
            -f["encharcamientos_historicos_12_meses"],
            f["calle"],
        )
    )
    return {"alerta_lluvia": alerta, "datos": filas[:limite], "criterio": CRITERIO_RIESGO, "obtenido_en": ahora}
