"""Límites territoriales (RN-01) y distancia de Haversine."""

import math

LAT_MIN, LAT_MAX = 31.45, 31.80
LON_MIN, LON_MAX = -106.65, -106.25
RADIO_TIERRA_M = 6_371_008.8
METROS_POR_GRADO_LAT = 111_320.0

RADIO_DUPLICADO_PAVIMENTO_M = 30  # HU-02.3
RADIO_DUPLICADO_ENCHARCAMIENTO_M = 50  # HU-03.1


def dentro_de_juarez(latitud: float, longitud: float) -> bool:
    return LAT_MIN <= latitud <= LAT_MAX and LON_MIN <= longitud <= LON_MAX


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia en metros entre dos puntos (idéntica a distancia_haversine_m en PostgreSQL)."""
    f1, f2 = math.radians(lat1), math.radians(lat2)
    df, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(df / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(dl / 2) ** 2
    return 2 * RADIO_TIERRA_M * math.asin(min(1.0, math.sqrt(a)))


def caja_envolvente(latitud: float, longitud: float, radio_m: float) -> tuple[float, float, float, float]:
    """(lat_min, lat_max, lon_min, lon_max) con 20 % de margen para prefiltrar con índice."""
    margen = radio_m * 1.2
    dlat = margen / METROS_POR_GRADO_LAT
    dlon = margen / (METROS_POR_GRADO_LAT * math.cos(math.radians(latitud)))
    return latitud - dlat, latitud + dlat, longitud - dlon, longitud + dlon
