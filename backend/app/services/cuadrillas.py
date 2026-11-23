"""Cuadrillas (HU-05.4) y avance operativo del enlace municipal (HU-05.5)."""

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errores import ErrorAPI
from app.core.tiempo import ahora_utc, fecha_local, hoy_local
from app.models import (
    AsignacionCuadrilla,
    Cuadrilla,
    EstadoReporte,
    OrigenCambio,
    Reporte,
    RolUsuario,
    TipoDano,
    Usuario,
    UsuarioCuadrilla,
)
from app.services import notificaciones, transiciones
from app.services.historial import fijar_contexto
from app.services.sqlutil import error_validacion

PENDIENTES = (EstadoReporte.PROGRAMADO, EstadoReporte.EN_REPARACION)


# ------------------------------------------------------------------------------- catálogo de cuadrillas


def obtener(db: Session, cuadrilla_id: int) -> Cuadrilla:
    c = db.get(Cuadrilla, cuadrilla_id)
    if c is None:
        raise ErrorAPI(404, "NO_ENCONTRADO", "La cuadrilla no existe.")
    return c


def pendientes_por_cuadrilla(db: Session, ids: list[int] | None = None) -> dict[int, int]:
    stmt = (
        select(AsignacionCuadrilla.cuadrilla_id, func.count())
        .join(Reporte, Reporte.id == AsignacionCuadrilla.reporte_id)
        .where(AsignacionCuadrilla.activa, Reporte.estado.in_(PENDIENTES))
        .group_by(AsignacionCuadrilla.cuadrilla_id)
    )
    if ids is not None:
        stmt = stmt.where(AsignacionCuadrilla.cuadrilla_id.in_(ids))
    return {cid: n for cid, n in db.execute(stmt).all()}


def listar(db: Session, *, solo_activas: bool = False) -> list[Cuadrilla]:
    stmt = select(Cuadrilla).order_by(Cuadrilla.nombre)
    if solo_activas:
        stmt = stmt.where(Cuadrilla.activa)
    return list(db.scalars(stmt))


def _guardar(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ErrorAPI(409, "CUADRILLA_DUPLICADA", "Ya existe una cuadrilla con ese nombre.") from None


def crear(db: Session, datos) -> Cuadrilla:
    c = Cuadrilla(nombre=datos.nombre, responsable=datos.responsable, telefono_contacto=datos.telefono_contacto)
    db.add(c)
    _guardar(db)
    db.refresh(c)
    return c


def editar(db: Session, cuadrilla_id: int, datos) -> Cuadrilla:
    c = obtener(db, cuadrilla_id)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        if valor is None:
            raise error_validacion(campo, "Este campo no admite valores nulos.")
        setattr(c, campo, valor)
    _guardar(db)
    db.refresh(c)
    return c


def eliminar(db: Session, cuadrilla_id: int) -> None:
    """Sólo se elimina si nunca tuvo trabajo ni enlaces; con baches sin terminar se bloquea (se puede desactivar)."""
    c = obtener(db, cuadrilla_id)
    if pendientes_por_cuadrilla(db, [c.id]).get(c.id, 0) > 0:
        raise ErrorAPI(
            409, "CUADRILLA_CON_PENDIENTES",
            "La cuadrilla tiene baches «Programado» o «En reparación». Termínalos o reasígnalos; también puedes desactivarla.",
        )
    con_historial = db.scalar(select(func.count()).where(AsignacionCuadrilla.cuadrilla_id == c.id)) or 0
    con_enlaces = db.scalar(select(func.count()).where(UsuarioCuadrilla.cuadrilla_id == c.id)) or 0
    if con_historial or con_enlaces:
        raise ErrorAPI(
            409, "CUADRILLA_CON_HISTORIAL",
            "La cuadrilla tiene historial de asignaciones o enlaces municipales; para conservar la trazabilidad, desactívala.",
        )
    db.delete(c)
    db.commit()


# ------------------------------------------------------------------------------- asignaciones


def asignaciones(db: Session, cuadrilla_id: int, *, solo_activas: bool) -> list[tuple[AsignacionCuadrilla, Reporte]]:
    stmt = (
        select(AsignacionCuadrilla, Reporte)
        .join(Reporte, Reporte.id == AsignacionCuadrilla.reporte_id)
        .where(AsignacionCuadrilla.cuadrilla_id == cuadrilla_id)
        .order_by(AsignacionCuadrilla.activa.desc(), AsignacionCuadrilla.fecha_programada, AsignacionCuadrilla.id)
    )
    if solo_activas:
        stmt = stmt.where(AsignacionCuadrilla.activa)
    return [(a, r) for a, r in db.execute(stmt).all()]


def asignar(db: Session, actor: Usuario, cuadrilla_id: int, folio: str, fecha_programada: date) -> tuple[AsignacionCuadrilla, Reporte]:
    """Validado → Programado con cuadrilla y fecha; un bache ya programado se puede reasignar (queda en el historial)."""
    cuadrilla = obtener(db, cuadrilla_id)
    if not cuadrilla.activa:
        raise ErrorAPI(409, "CUADRILLA_INACTIVA", "La cuadrilla está desactivada; actívala o elige otra.")
    reporte = db.scalar(select(Reporte).where(Reporte.folio == folio).with_for_update(of=Reporte))
    if reporte is None:
        raise ErrorAPI(404, "NO_ENCONTRADO", f"No existe un reporte con el folio {folio}.")
    if reporte.tipo_dano == TipoDano.ENCHARCAMIENTO:
        raise ErrorAPI(422, "ASIGNACION_INVALIDA", "Sólo los baches y alcantarillas se asignan a cuadrillas.")
    if fecha_programada < hoy_local():
        raise error_validacion("fecha_programada", "La fecha programada no puede ser anterior a hoy.")
    if fecha_programada < fecha_local(reporte.created_at):
        raise error_validacion("fecha_programada", "La fecha programada no puede ser anterior al reporte.")
    if reporte.estado not in (EstadoReporte.VALIDADO, EstadoReporte.PROGRAMADO):
        raise ErrorAPI(
            409, "ASIGNACION_INVALIDA",
            f"Sólo se asignan baches «Validado» (o se reasignan «Programado»); {folio} está «{reporte.estado.value}».",
        )

    for previa in db.scalars(
        select(AsignacionCuadrilla).where(AsignacionCuadrilla.reporte_id == reporte.id, AsignacionCuadrilla.activa)
    ):
        previa.activa = False  # se conserva como historial
    db.flush()
    asignacion = AsignacionCuadrilla(
        reporte_id=reporte.id, cuadrilla_id=cuadrilla.id, fecha_programada=fecha_programada, asignado_por_id=actor.id
    )
    db.add(asignacion)
    reporte.fecha_programada = fecha_programada
    if reporte.estado == EstadoReporte.VALIDADO:
        transiciones.validar_transicion(reporte.tipo_dano, reporte.estado, EstadoReporte.PROGRAMADO, actor.rol)
        fijar_contexto(
            db, usuario_id=actor.id, origen=OrigenCambio.MODERACION, fecha_evento=ahora_utc(),
            motivo=f"Asignado a la cuadrilla «{cuadrilla.nombre}» para el {fecha_programada.strftime('%d/%m/%Y')}",
        )
        reporte.estado = EstadoReporte.PROGRAMADO
        db.flush()
        notificaciones.notificar_cambio_estado(db, reporte, EstadoReporte.PROGRAMADO, actor)
    db.commit()
    db.refresh(asignacion)
    return asignacion, reporte


# ------------------------------------------------------------------------------- enlaces municipales


def vincular_enlace(db: Session, cuadrilla_id: int, usuario_id: uuid.UUID) -> None:
    obtener(db, cuadrilla_id)
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise ErrorAPI(404, "NO_ENCONTRADO", "El usuario no existe.")
    if usuario.rol != RolUsuario.ENLACE_MUNICIPAL:
        raise ErrorAPI(422, "ROL_INCOMPATIBLE", "Sólo se vinculan cuentas con rol «enlace_municipal».")
    if db.get(UsuarioCuadrilla, (usuario_id, cuadrilla_id)) is None:
        db.add(UsuarioCuadrilla(usuario_id=usuario_id, cuadrilla_id=cuadrilla_id))
        db.commit()


def desvincular_enlace(db: Session, cuadrilla_id: int, usuario_id: uuid.UUID) -> None:
    vinculo = db.get(UsuarioCuadrilla, (usuario_id, cuadrilla_id))
    if vinculo is None:
        raise ErrorAPI(404, "NO_ENCONTRADO", "Ese enlace no está vinculado a la cuadrilla.")
    db.delete(vinculo)
    db.commit()


def enlaces_de(db: Session, cuadrilla_id: int) -> list[Usuario]:
    return list(
        db.scalars(
            select(Usuario).join(UsuarioCuadrilla, UsuarioCuadrilla.usuario_id == Usuario.id)
            .where(UsuarioCuadrilla.cuadrilla_id == cuadrilla_id).order_by(Usuario.nombre)
        )
    )


def cuadrillas_de_enlace(db: Session, enlace: Usuario) -> list[Cuadrilla]:
    return list(
        db.scalars(
            select(Cuadrilla).join(UsuarioCuadrilla, UsuarioCuadrilla.cuadrilla_id == Cuadrilla.id)
            .where(UsuarioCuadrilla.usuario_id == enlace.id).order_by(Cuadrilla.nombre)
        )
    )


def _asignacion_del_enlace(db: Session, enlace: Usuario, reporte: Reporte) -> AsignacionCuadrilla | None:
    return db.scalar(
        select(AsignacionCuadrilla)
        .join(UsuarioCuadrilla, UsuarioCuadrilla.cuadrilla_id == AsignacionCuadrilla.cuadrilla_id)
        .where(
            AsignacionCuadrilla.reporte_id == reporte.id,
            AsignacionCuadrilla.activa,
            UsuarioCuadrilla.usuario_id == enlace.id,
        )
    )


def listar_del_enlace(db: Session, enlace: Usuario, *, incluir_reparados: bool) -> list[tuple[AsignacionCuadrilla, Reporte]]:
    """Sólo baches con asignación ACTIVA a alguna cuadrilla vinculada a este enlace (aislamiento por identidad)."""
    estados = [*PENDIENTES, EstadoReporte.REPARADO] if incluir_reparados else list(PENDIENTES)
    stmt = (
        select(AsignacionCuadrilla, Reporte)
        .join(Reporte, Reporte.id == AsignacionCuadrilla.reporte_id)
        .join(UsuarioCuadrilla, UsuarioCuadrilla.cuadrilla_id == AsignacionCuadrilla.cuadrilla_id)
        .where(UsuarioCuadrilla.usuario_id == enlace.id, AsignacionCuadrilla.activa, Reporte.estado.in_(estados))
        .order_by(AsignacionCuadrilla.fecha_programada, Reporte.id)
    )
    return [(a, r) for a, r in db.execute(stmt).all()]


def reporte_del_enlace(db: Session, enlace: Usuario, folio: str, *, bloquear: bool = False) -> tuple[AsignacionCuadrilla, Reporte]:
    stmt = select(Reporte).where(Reporte.folio == folio)
    if bloquear:
        stmt = stmt.with_for_update(of=Reporte)
    reporte = db.scalar(stmt)
    asignacion = _asignacion_del_enlace(db, enlace, reporte) if reporte is not None else None
    if reporte is None or asignacion is None:
        # Misma respuesta exista o no el folio: no se revela trabajo de otras cuadrillas.
        raise ErrorAPI(403, "REPORTE_AJENO", "Este bache no está asignado a ninguna de tus cuadrillas.")
    return asignacion, reporte


def avanzar(db: Session, enlace: Usuario, folio: str, nuevo: EstadoReporte, fecha_reparacion: date | None) -> tuple[AsignacionCuadrilla, Reporte, EstadoReporte]:
    asignacion, reporte = reporte_del_enlace(db, enlace, folio, bloquear=True)
    anterior = reporte.estado
    if (anterior, nuevo) not in ((EstadoReporte.PROGRAMADO, EstadoReporte.EN_REPARACION), (EstadoReporte.EN_REPARACION, EstadoReporte.REPARADO)):
        raise ErrorAPI(
            400, "TRANSICION_INVALIDA",
            f'Como enlace municipal sólo puedes avanzar «Programado → En reparación → Reparado»; no de "{anterior.value}" a "{nuevo.value}".',
        )
    transiciones.validar_transicion(reporte.tipo_dano, anterior, nuevo, enlace.rol)
    if nuevo == EstadoReporte.REPARADO:
        inicio = fecha_local(reporte.created_at)
        if fecha_reparacion is None:
            raise error_validacion("fecha_reparacion", "La fecha de reparación es obligatoria.")
        if not inicio <= fecha_reparacion <= hoy_local():
            raise ErrorAPI(
                422, "FECHA_REPARACION_INVALIDA",
                "La fecha de reparación debe ser igual o posterior a la fecha del reporte y no puede ser futura.",
                [{"campo": "fecha_reparacion", "mensaje": f"Debe estar entre {inicio.isoformat()} y {hoy_local().isoformat()}."}],
            )
        reporte.fecha_reparacion = fecha_reparacion
    elif fecha_reparacion is not None:
        raise error_validacion("fecha_reparacion", "Sólo se indica al pasar a «Reparado».")
    fijar_contexto(
        db, usuario_id=enlace.id, origen=OrigenCambio.MODERACION, fecha_evento=ahora_utc(),
        motivo=f"Avance reportado por enlace municipal (cuadrilla «{asignacion.cuadrilla.nombre}»)",
    )
    reporte.estado = nuevo
    db.flush()
    notificaciones.notificar_cambio_estado(db, reporte, nuevo, enlace)
    db.commit()
    db.refresh(reporte)
    return asignacion, reporte, anterior
