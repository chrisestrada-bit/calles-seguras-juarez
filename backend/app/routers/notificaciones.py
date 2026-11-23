import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import CUALQUIER_ROL, get_db
from app.models import Usuario
from app.schemas.comun import ParametrosPagina, armar_pagina, respuestas
from app.schemas.notificaciones import LeerTodasOut, NotificacionOut, PaginaNotificaciones
from app.services import notificaciones as servicio

router = APIRouter(prefix="/notificaciones", tags=["notificaciones"])


def _out(n) -> NotificacionOut:
    return NotificacionOut(id=n.id, folio=n.folio, mensaje=n.mensaje, leida=n.leida, created_at=n.created_at)


@router.get(
    "",
    response_model=PaginaNotificaciones,
    summary="Mis avisos sobre cambios de estado de mis reportes (HU-08.2)",
    responses=respuestas(401, 422),
)
def listar(
    solo_no_leidas: bool = False,
    pag: ParametrosPagina = Depends(),
    usuario: Usuario = Depends(CUALQUIER_ROL),
    db: Session = Depends(get_db),
) -> dict:
    filas, total = servicio.listar(db, usuario, solo_no_leidas=solo_no_leidas, pag=pag)
    pagina = armar_pagina([_out(n) for n in filas], total, pag)
    pagina["no_leidas"] = servicio.contar_no_leidas(db, usuario)
    return pagina


@router.patch(
    "/leer-todas",
    response_model=LeerTodasOut,
    summary="Marcar todos mis avisos como leídos",
    responses=respuestas(401),
)
def leer_todas(usuario: Usuario = Depends(CUALQUIER_ROL), db: Session = Depends(get_db)) -> LeerTodasOut:
    marcadas = servicio.marcar_todas(db, usuario)
    return LeerTodasOut(marcadas=marcadas, no_leidas=0, mensaje="Marcaste todos tus avisos como leídos.")


@router.patch(
    "/{notificacion_id}/leer",
    response_model=NotificacionOut,
    summary="Marcar un aviso como leído (404 si es de otra persona)",
    responses=respuestas(401, 404, 422),
)
def leer(
    notificacion_id: uuid.UUID,
    usuario: Usuario = Depends(CUALQUIER_ROL),
    db: Session = Depends(get_db),
) -> NotificacionOut:
    return _out(servicio.marcar_leida(db, usuario, notificacion_id))
