from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.schemas.clima import Pronostico, RiesgoInundacion
from app.schemas.comun import respuestas
from app.services import clima as servicio
from app.services.vigencia import expirar_vencidos

router = APIRouter(prefix="/clima", tags=["clima"])


@router.get(
    "/pronostico",
    response_model=Pronostico,
    summary="Pronóstico de lluvia (con caché)",
    responses=respuestas(503),
)
def pronostico(db: Session = Depends(get_db)) -> dict:
    return servicio.obtener_pronostico(db)


@router.get(
    "/riesgo-inundacion",
    response_model=RiesgoInundacion,
    summary="Calles con riesgo de inundación",
    responses=respuestas(422),
)
def riesgo_inundacion(
    sector_id: Annotated[int | None, Query(ge=1)] = None,
    colonia_id: Annotated[int | None, Query(ge=1)] = None,
    calle: Annotated[str | None, Query(min_length=3, max_length=100)] = None,
    bbox: Annotated[str | None, Query(description="lon_min,lat_min,lon_max,lat_max")] = None,
    limite: Annotated[int, Query(ge=1, le=100)] = 20,
    db: Session = Depends(get_db),
) -> dict:
    expirar_vencidos(db)
    return servicio.riesgo_inundacion(
        db, sector_id=sector_id, colonia_id=colonia_id, calle=calle, bbox=bbox, limite=limite
    )
