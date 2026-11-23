"""Puntos recurrentes de inundación (HU-03.4).

Definición (documentada en docs/arquitectura.md §11.1):
* Radio: 50 m (Haversine) alrededor del encharcamiento.
* Reportes considerados: encharcamientos `Activo` e `Histórico` (nunca `Rechazado`).
* Periodo: año calendario en curso en America/Ciudad_Juarez, del 1 de enero local hasta hoy.
* Días: fechas LOCALES distintas de `created_at`; varios reportes el mismo día cuentan como 1.
* Es punto recurrente si hay >= 3 días distintos.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import Float, func, select
from sqlalchemy.orm import Session

from app.core.tiempo import fecha_local, hoy_local
from app.models import EstadoReporte, Reporte, TipoDano
from app.services import geo
from app.services.sqlutil import fecha_local_sql

RADIO_RECURRENTE_M = 50
MINIMO_DIAS = 3
_ESTADOS = (EstadoReporte.ACTIVO, EstadoReporte.HISTORICO)


@dataclass(frozen=True)
class Recurrencia:
    dias_distintos_anio: int
    ultima_ocurrencia: datetime | None

    @property
    def es_punto_recurrente(self) -> bool:
        return self.dias_distintos_anio >= MINIMO_DIAS


def inicio_de_anio(hoy: date | None = None) -> date:
    return date((hoy or hoy_local()).year, 1, 1)


def recurrencia_de(db: Session, latitud: float, longitud: float) -> Recurrencia:
    lat_min, lat_max, lon_min, lon_max = geo.caja_envolvente(latitud, longitud, RADIO_RECURRENTE_M)
    distancia = func.distancia_haversine_m(Reporte.latitud, Reporte.longitud, latitud, longitud, type_=Float)
    fecha = fecha_local_sql(Reporte.created_at)
    dias, ultima = db.execute(
        select(func.count(func.distinct(fecha)), func.max(Reporte.created_at)).where(
            Reporte.tipo_dano == TipoDano.ENCHARCAMIENTO,
            Reporte.estado.in_(_ESTADOS),
            Reporte.latitud.between(lat_min, lat_max),
            Reporte.longitud.between(lon_min, lon_max),
            distancia <= RADIO_RECURRENTE_M,
            fecha >= inicio_de_anio(),
            fecha <= hoy_local(),
        )
    ).one()
    return Recurrencia(int(dias or 0), ultima)


def anotar(db: Session, reportes: Iterable[Reporte]) -> None:
    """Deja la recurrencia en cada encharcamiento para que `presentacion` la incluya en la respuesta."""
    for r in reportes:
        if r.tipo_dano == TipoDano.ENCHARCAMIENTO:
            r._recurrencia = recurrencia_de(db, r.latitud, r.longitud)  # type: ignore[attr-defined]


@dataclass
class PuntoRecurrente:
    latitud: float
    longitud: float
    calle: str
    colonia_id: int
    colonia: str
    dias_distintos_anio: int
    total_reportes: int
    ultima_ocurrencia: datetime
    folios: list[str]


def listar_puntos(db: Session) -> list[PuntoRecurrente]:
    """Agrupa los encharcamientos del año en puntos de 50 m y devuelve los que tienen >= 3 días distintos."""
    filas = db.scalars(
        select(Reporte)
        .where(
            Reporte.tipo_dano == TipoDano.ENCHARCAMIENTO,
            Reporte.estado.in_(_ESTADOS),
            fecha_local_sql(Reporte.created_at) >= inicio_de_anio(),
            fecha_local_sql(Reporte.created_at) <= hoy_local(),
        )
        .order_by(Reporte.created_at.desc(), Reporte.id)
    ).all()
    pendientes = list(filas)
    puntos: list[PuntoRecurrente] = []
    while pendientes:
        semilla = pendientes[0]
        grupo = [
            r for r in pendientes
            if geo.haversine_m(semilla.latitud, semilla.longitud, r.latitud, r.longitud) <= RADIO_RECURRENTE_M
        ]
        ids = {r.id for r in grupo}
        pendientes = [r for r in pendientes if r.id not in ids]
        dias = {fecha_local(r.created_at) for r in grupo}
        if len(dias) >= MINIMO_DIAS:
            puntos.append(
                PuntoRecurrente(
                    latitud=semilla.latitud,
                    longitud=semilla.longitud,
                    calle=semilla.calle,
                    colonia_id=semilla.colonia.id,
                    colonia=semilla.colonia.nombre,
                    dias_distintos_anio=len(dias),
                    total_reportes=len(grupo),
                    ultima_ocurrencia=max(r.created_at for r in grupo),
                    folios=[r.folio for r in grupo[:10]],
                )
            )
    puntos.sort(key=lambda p: (-p.dias_distintos_anio, -p.ultima_ocurrencia.timestamp()))
    return puntos
