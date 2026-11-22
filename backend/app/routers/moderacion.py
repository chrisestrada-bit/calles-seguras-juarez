import uuid
from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.dependencies import MODERACION, get_db
from app.models import EstadoReporte, Severidad, TipoDano, Usuario
from app.schemas.comun import Pagina, ParametrosPagina, armar_pagina, respuestas
from app.schemas.moderacion import ReporteModeracion, ReporteModeracionItem, TransicionIn, TransicionOut
from app.services import moderacion as servicio
from app.services import reportes as servicio_reportes
from app.services import tiempo_real
from app.services.vigencia import expirar_vencidos

router = APIRouter(prefix="/moderacion", tags=["moderacion"])

FolioPath = Annotated[str, Path(pattern=r"^(BCH|ENC)-[0-9]{4}-[0-9]{6}$")]


@router.get(
    "/reportes",
    response_model=Pagina[ReporteModeracionItem],
    summary="Cola de moderación (incluye todos los estados)",
    responses=respuestas(401, 403, 422),
)
def cola(
    estado: Annotated[list[EstadoReporte] | None, Query()] = None,
    tipo_dano: TipoDano | None = None,
    sector_id: Annotated[int | None, Query(ge=1)] = None,
    colonia_id: Annotated[int | None, Query(ge=1)] = None,
    severidad: Severidad | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    autor_id: uuid.UUID | None = None,
    orden: Literal["antiguos", "recientes", "severidad", "confirmaciones"] = "antiguos",
    pag: ParametrosPagina = Depends(),
    usuario: Usuario = Depends(MODERACION),
    db: Session = Depends(get_db),
) -> dict:
    expirar_vencidos(db)
    items, total = servicio.listar_cola(
        db,
        usuario,
        estados=estado,
        tipo=tipo_dano,
        sector_id=sector_id,
        colonia_id=colonia_id,
        severidad=severidad,
        desde=desde,
        hasta=hasta,
        autor_id=autor_id,
        orden=orden,
        pag=pag,
    )
    return armar_pagina(items, total, pag)


@router.get(
    "/reportes/{folio}",
    response_model=ReporteModeracion,
    summary="Detalle completo con historial y actores",
    responses=respuestas(401, 403, 404, 422),
)
def detalle(folio: FolioPath, usuario: Usuario = Depends(MODERACION), db: Session = Depends(get_db)) -> ReporteModeracion:
    expirar_vencidos(db)
    return servicio.detalle(db, usuario, folio)


@router.post(
    "/reportes/{folio}/transiciones",
    response_model=TransicionOut,
    summary="Cambiar el estado de un reporte (RN-05)",
    responses=respuestas(400, 401, 403, 404, 422),
)
def transicionar(
    folio: FolioPath,
    datos: TransicionIn,
    usuario: Usuario = Depends(MODERACION),
    db: Session = Depends(get_db),
) -> TransicionOut:
    expirar_vencidos(db)
    resultado = servicio.transicionar(db, usuario, folio, datos)
    tiempo_real.emitir(
        db, servicio_reportes.obtener_por_folio(db, folio), "retirado" if resultado.estado.value == "Rechazado" else "actualizado"
    )  # HU-08.3
    return resultado
