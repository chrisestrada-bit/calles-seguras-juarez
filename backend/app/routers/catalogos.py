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
from app.schemas.operacion import ListaMotivos, MotivoRechazo
from app.services import catalogos as servicio
from app.services import catalogos_admin

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
    summary="Colonias activas; filtro por nombre o código postal (q) y por sector (sector_id)",
    responses=respuestas(422),
)
def colonias(
    q: Annotated[str | None, Query(min_length=2, max_length=80, description="Nombre (parcial, tolera errores) o código postal (32000–32730, completo o prefijo).")] = None,
    sector_id: Annotated[int | None, Query(ge=1)] = None,
    pag: ParametrosPagina = Depends(),
    db: Session = Depends(get_db),
) -> dict:
    filas, total = servicio.buscar_colonias(db, q=q.strip() if q else None, sector_id=sector_id, pag=pag)
    return armar_pagina([colonia_catalogo(c) for c in filas], total, pag)


@router.get("/tipos-dano", response_model=CatalogoTiposDano, summary="Formulario dinámico de los tipos de daño ACTIVOS")
def tipos_dano(db: Session = Depends(get_db)) -> dict:
    base = servicio.tipos_dano()
    activos = {t.clave.value: t for t in catalogos_admin.tipos(db, solo_activos=True)}  # HU-06.3
    base["datos"] = [
        {**d, "nombre": activos[d["tipo_dano"]].nombre, "descripcion": activos[d["tipo_dano"]].descripcion}
        for d in base["datos"]
        if d["tipo_dano"] in activos
    ]
    return base


@router.get("/motivos-rechazo", response_model=ListaMotivos, summary="Motivos de rechazo activos (HU-06.3)")
def motivos_rechazo(db: Session = Depends(get_db)) -> ListaMotivos:
    return ListaMotivos(
        datos=[MotivoRechazo(id=m.id, nombre=m.nombre, descripcion=m.descripcion, activo=m.activo) for m in catalogos_admin.motivos(db, solo_activos=True)]
    )


@router.get("/estados", response_model=CatalogoEstados, summary="Estados y transiciones permitidas")
def estados() -> dict:
    return servicio.estados()
