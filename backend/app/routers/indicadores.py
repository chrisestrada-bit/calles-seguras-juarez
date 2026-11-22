from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import MODERACION, SOLO_COORDINADOR, get_db
from app.models import Usuario
from app.schemas.comun import respuestas
from app.schemas.indicadores import (
    PuntosRecurrentes,
    IndicadoresLongevidad,
    IndicadoresModeracion,
    IndicadoresResumen,
    IndicadoresSectores,
)
from app.services import indicadores as servicio
from app.services import recurrentes
from app.services.vigencia import expirar_vencidos

router = APIRouter(prefix="/indicadores", tags=["indicadores"])


@router.get("/resumen", response_model=IndicadoresResumen, summary="Resumen público", responses=respuestas(422))
def resumen(
    desde: date | None = None,
    hasta: date | None = None,
    sector_id: Annotated[int | None, Query(ge=1)] = None,
    db: Session = Depends(get_db),
) -> dict:
    expirar_vencidos(db)
    return servicio.resumen(db, desde, hasta, sector_id)


@router.get("/sectores", response_model=IndicadoresSectores, summary="Indicadores por sector", responses=respuestas(422))
def sectores(desde: date | None = None, hasta: date | None = None, db: Session = Depends(get_db)) -> dict:
    expirar_vencidos(db)
    return {"datos": servicio.por_sector(db, desde, hasta)}


@router.get(
    "/longevidad",
    response_model=IndicadoresLongevidad,
    summary="Baches abiertos más antiguos (RN-10)",
    responses=respuestas(422),
)
def longevidad(
    sector_id: Annotated[int | None, Query(ge=1)] = None,
    limite: Annotated[int, Query(ge=1, le=50)] = 10,
    db: Session = Depends(get_db),
) -> dict:
    return {"datos": servicio.mas_antiguos(db, sector_id, limite)}


@router.get(
    "/moderacion",
    response_model=IndicadoresModeracion,
    summary="Indicadores de moderación",
    responses=respuestas(401, 403, 422),
)
def moderacion(
    desde: date | None = None,
    hasta: date | None = None,
    _: Usuario = Depends(MODERACION),
    db: Session = Depends(get_db),
) -> dict:
    expirar_vencidos(db)
    return servicio.moderacion(db, desde, hasta)


@router.get(
    "/puntos-recurrentes",
    response_model=PuntosRecurrentes,
    summary="Puntos de inundación recurrente del año (HU-03.4, sólo coordinación)",
    description=(
        "Encharcamientos activos e históricos agrupados en radios de 50 m (Haversine) con al menos 3 días "
        "distintos (fecha local de Ciudad Juárez) en el año calendario en curso."
    ),
    responses=respuestas(401, 403),
)
def puntos_recurrentes(_: Usuario = Depends(SOLO_COORDINADOR), db: Session = Depends(get_db)) -> PuntosRecurrentes:
    expirar_vencidos(db)
    puntos = recurrentes.listar_puntos(db)
    return PuntosRecurrentes(
        anio=recurrentes.inicio_de_anio().year,
        radio_metros=recurrentes.RADIO_RECURRENTE_M,
        minimo_dias=recurrentes.MINIMO_DIAS,
        datos=[
            {
                "ubicacion": {"latitud": p.latitud, "longitud": p.longitud},
                "calle": p.calle,
                "colonia": {"id": p.colonia_id, "nombre": p.colonia},
                "dias_distintos_anio": p.dias_distintos_anio,
                "total_reportes": p.total_reportes,
                "ultima_ocurrencia": p.ultima_ocurrencia,
                "folios": p.folios,
            }
            for p in puntos
        ],
    )
