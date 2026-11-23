"""Revisar mi trayecto (HU-04.6).

1. Ruta sugerida desde OSRM (`ROUTING_API_URL`, perfil «driving»). Si el proveedor falla, tarda o no está configurado,
   se usa el segmento directo origen–destino y la respuesta lo indica (`degradado: true`).
2. Distancia mínima punto–polilínea de cada encharcamiento vigente (Activo y dentro de sus 6 h) a la ruta, con una
   proyección equirectangular local (error < 0.1 % a esta escala). Se incluyen los que quedan a <= 100 m.
3. Orden: primero los «intransitable», después por distancia. Sin datos de la persona reportante (RN-04).
"""

import logging
import math
from dataclasses import dataclass

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.tiempo import ahora_utc
from app.models import EstadoReporte, NivelAgua, Reporte, TipoDano
from app.services import geo

logger = logging.getLogger("calles_seguras")

RADIO_TRAYECTO_M = 100
MAX_PUNTOS_RUTA = 2000
_M_POR_GRADO = geo.RADIO_TIERRA_M * math.pi / 180


@dataclass
class Ruta:
    puntos: list[tuple[float, float]]  # (lat, lon)
    fuente: str
    degradado: bool
    distancia_metros: float
    duracion_segundos: float | None
    mensaje: str | None


def _linea_recta(origen: tuple[float, float], destino: tuple[float, float], mensaje: str) -> Ruta:
    return Ruta([origen, destino], "linea_recta", True, geo.haversine_m(*origen, *destino), None, mensaje)


def obtener_ruta(origen: tuple[float, float], destino: tuple[float, float]) -> Ruta:
    s = get_settings()
    if not s.routing_api_url:
        return _linea_recta(origen, destino, "El servicio de rutas no está configurado; se usa una línea recta entre los puntos.")
    url = (
        f"{s.routing_api_url.rstrip('/')}/route/v1/driving/"
        f"{origen[1]:.6f},{origen[0]:.6f};{destino[1]:.6f},{destino[0]:.6f}"
    )
    try:
        r = httpx.get(url, params={"overview": "full", "geometries": "geojson"}, timeout=s.routing_timeout_seconds)
        r.raise_for_status()
        datos = r.json()
        ruta = datos["routes"][0]
        coords = ruta["geometry"]["coordinates"]
        if datos.get("code") != "Ok" or len(coords) < 2:
            raise ValueError("Respuesta sin ruta")
        paso = max(1, len(coords) // MAX_PUNTOS_RUTA)
        puntos = [(lat, lon) for lon, lat in coords[::paso]]
        if puntos[-1] != (coords[-1][1], coords[-1][0]):
            puntos.append((coords[-1][1], coords[-1][0]))
        return Ruta(puntos, "osrm", False, float(ruta["distance"]), float(ruta["duration"]), None)
    except Exception as exc:  # noqa: BLE001 - cualquier falla del proveedor degrada a línea recta
        logger.warning("Proveedor de rutas no disponible (%s); se usa línea recta.", type(exc).__name__)
        return _linea_recta(origen, destino, "El servicio de rutas no respondió; se revisó la línea recta entre origen y destino.")


def distancia_a_polilinea(lat: float, lon: float, puntos: list[tuple[float, float]]) -> float:
    """Metros desde (lat, lon) al segmento más cercano de la polilínea."""
    escala_x = _M_POR_GRADO * math.cos(math.radians(lat))
    proyectados = [((p_lon - lon) * escala_x, (p_lat - lat) * _M_POR_GRADO) for p_lat, p_lon in puntos]
    minimo = math.inf
    for (ax, ay), (bx, by) in zip(proyectados, proyectados[1:]):
        dx, dy = bx - ax, by - ay
        largo2 = dx * dx + dy * dy
        t = 0.0 if largo2 == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / largo2))
        minimo = min(minimo, math.hypot(ax + t * dx, ay + t * dy))
    if len(proyectados) == 1:
        minimo = math.hypot(*proyectados[0])
    return minimo


def encharcamientos_cercanos(db: Session, ruta: Ruta) -> list[tuple[Reporte, float]]:
    lats = [p[0] for p in ruta.puntos]
    lons = [p[1] for p in ruta.puntos]
    margen_lat = RADIO_TRAYECTO_M * 1.2 / geo.METROS_POR_GRADO_LAT
    margen_lon = margen_lat / max(0.1, math.cos(math.radians(sum(lats) / len(lats))))
    candidatos = db.scalars(
        select(Reporte).where(
            Reporte.tipo_dano == TipoDano.ENCHARCAMIENTO,
            Reporte.estado == EstadoReporte.ACTIVO,
            Reporte.vigente_hasta > ahora_utc(),
            Reporte.latitud.between(min(lats) - margen_lat, max(lats) + margen_lat),
            Reporte.longitud.between(min(lons) - margen_lon, max(lons) + margen_lon),
        )
    ).all()
    cercanos = []
    for r in candidatos:
        d = distancia_a_polilinea(r.latitud, r.longitud, ruta.puntos)
        if d <= RADIO_TRAYECTO_M:
            cercanos.append((r, d))
    cercanos.sort(key=lambda par: (par[0].nivel_agua != NivelAgua.INTRANSITABLE, par[1]))
    return cercanos
