"""Esquemas de notificaciones (HU-08.2). Sólo datos del propio usuario."""

import uuid

from pydantic import BaseModel

from app.schemas.comun import FechaLocal, Pagina


class NotificacionOut(BaseModel):
    id: uuid.UUID
    folio: str
    mensaje: str
    leida: bool
    created_at: FechaLocal


class PaginaNotificaciones(Pagina[NotificacionOut]):
    no_leidas: int


class LeerTodasOut(BaseModel):
    marcadas: int
    no_leidas: int
    mensaje: str
