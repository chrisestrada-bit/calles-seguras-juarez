"""Avisos sobre mis reportes (HU-08.2). Aislamiento estricto por usuario: nunca se lee una notificación ajena."""

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.errores import ErrorAPI
from app.models import EstadoReporte, Notificacion, Reporte, Usuario
from app.schemas.comun import ParametrosPagina


def _fecha(valor) -> str:
    return valor.strftime("%d/%m/%Y")


def mensaje_de_cambio(reporte: Reporte, nuevo: EstadoReporte, motivo: str | None) -> str:
    folio = reporte.folio
    if nuevo == EstadoReporte.VALIDADO:
        return f"Tu reporte {folio} fue validado por moderación y ya aparece como confirmado."
    if nuevo == EstadoReporte.RECHAZADO:
        return f"Tu reporte {folio} fue rechazado. Motivo: {motivo or reporte.motivo_rechazo or 'no especificado'}."
    if nuevo == EstadoReporte.PROGRAMADO:
        cuando = f" para el {_fecha(reporte.fecha_programada)}" if reporte.fecha_programada else ""
        return f"La reparación de tu reporte {folio} quedó programada{cuando}."
    if nuevo == EstadoReporte.EN_REPARACION:
        return f"Tu reporte {folio} está en reparación."
    if nuevo == EstadoReporte.REPARADO:
        cuando = f" el {_fecha(reporte.fecha_reparacion)}" if reporte.fecha_reparacion else ""
        return f"Tu reporte {folio} fue reparado{cuando}. Gracias por avisar."
    return f'Tu reporte {folio} cambió al estado "{nuevo.value}".'


def notificar(db: Session, reporte: Reporte, mensaje: str) -> Notificacion:
    """Agrega la notificación a la transacción en curso (el llamador hace commit)."""
    n = Notificacion(usuario_id=reporte.usuario_id, reporte_id=reporte.id, folio=reporte.folio, mensaje=mensaje[:800])
    db.add(n)
    return n


def notificar_cambio_estado(
    db: Session, reporte: Reporte, nuevo: EstadoReporte, actor: Usuario, motivo: str | None = None
) -> None:
    """Avisa al autor. Quien hace el cambio no se notifica a sí mismo."""
    if actor.id == reporte.usuario_id:
        return
    notificar(db, reporte, mensaje_de_cambio(reporte, nuevo, motivo))


def contar_no_leidas(db: Session, usuario: Usuario) -> int:
    return db.scalar(
        select(func.count()).where(Notificacion.usuario_id == usuario.id, Notificacion.leida.is_(False))
    ) or 0


def listar(db: Session, usuario: Usuario, *, solo_no_leidas: bool, pag: ParametrosPagina) -> tuple[list[Notificacion], int]:
    condiciones = [Notificacion.usuario_id == usuario.id]
    if solo_no_leidas:
        condiciones.append(Notificacion.leida.is_(False))
    total = db.scalar(select(func.count()).select_from(Notificacion).where(*condiciones)) or 0
    filas = db.scalars(
        select(Notificacion)
        .where(*condiciones)
        .order_by(Notificacion.created_at.desc(), Notificacion.id)
        .limit(pag.por_pagina)
        .offset(pag.offset)
    ).all()
    return list(filas), total


def marcar_leida(db: Session, usuario: Usuario, notificacion_id: uuid.UUID) -> Notificacion:
    n = db.scalar(
        select(Notificacion).where(Notificacion.id == notificacion_id, Notificacion.usuario_id == usuario.id)
    )
    if n is None:  # ajena o inexistente: misma respuesta, sin revelar que existe
        raise ErrorAPI(404, "NO_ENCONTRADO", "La notificación no existe.")
    n.leida = True
    db.commit()
    return n


def marcar_todas(db: Session, usuario: Usuario) -> int:
    resultado = db.execute(
        update(Notificacion)
        .where(Notificacion.usuario_id == usuario.id, Notificacion.leida.is_(False))
        .values(leida=True)
    )
    db.commit()
    return resultado.rowcount or 0
