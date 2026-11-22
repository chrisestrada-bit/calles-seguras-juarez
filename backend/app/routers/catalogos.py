from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.schemas.catalogos import (
    CatalogoEstados,
    CatalogoTiposDano,
    ColoniaCatalogo,
    ListaSectores,
    SectorCatalogo,
)
from app.schemas.comun import Pagina, ParametrosPagina, armar_pagina, respuestas
from app.services import catalogos as servicio

router = APIRouter(prefix="/catalogos", tags=["catalogos"])


def colonia_catalogo(c) -> dict:
    return {
        "id": c.id,
        "nombre": c.nombre,
        "codigo_postal": c.codigo_postal,
        "sector": {"id": c.sector.id, "nombre": c.sector.nombre},
        "centro": {"latitud": c.latitud_centro, "longitud": c.longitud_centro},
    }


@router.get("/sectores", response_model=ListaSectores, summary="Sectores activos")
def sectores(db: Session = Depends(get_db)) -> ListaSectores:
    return ListaSectores(
        datos=[SectorCatalogo(id=s.id, clave=s.clave, nombre=s.nombre) for s in servicio.listar_sectores(db)]
    )


@router.get(
    "/colonias",
    response_model=Pagina[ColoniaCatalogo],
    summary="Colonias activas; filtro por nombre (q) y por sector (sector_id)",
    responses=respuestas(422),
)
def colonias(
    q: Annotated[str | None, Query(min_length=2, max_length=80, description="Nombre (parcial, tolera errores).")] = None,
    sector_id: Annotated[int | None, Query(ge=1)] = None,
    pag: ParametrosPagina = Depends(),
    db: Session = Depends(get_db),
) -> dict:
    filas, total = servicio.buscar_colonias(db, q=q.strip() if q else None, sector_id=sector_id, pag=pag)
    return armar_pagina([colonia_catalogo(c) for c in filas], total, pag)


@router.get("/tipos-dano", response_model=CatalogoTiposDano, summary="Formulario dinámico por tipo de daño")
def tipos_dano() -> dict:
    return servicio.tipos_dano()


@router.get("/estados", response_model=CatalogoEstados, summary="Estados y transiciones permitidas")
def estados() -> dict:
    return servicio.estados()
