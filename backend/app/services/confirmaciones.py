"""Confirmaciones de reportes (HU-02.3) y vigencia de encharcamientos (RN-06, HU-03.2, HU-03.3)."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errores import ErrorAPI
from app.core.tiempo import ahora_utc
from app.models import (
    ESTADOS_PAVIMENTO_ABIERTOS,
    ConfirmacionReporte,
    EstadoReporte,
    OrigenCambio,
    Reporte,
    TipoConfirmacion,
    TipoDano,
    Usuario,
)
from app.schemas.reportes import ConfirmacionOut
from app.services.historial import fijar_contexto
from app.services.presentacion import conteos_confirmaciones, vigencia_de
from app.services.vigencia import (
    DESMENTIDOS_PARA_HISTORICO,
    MOTIVO_DESMENTIDO,
    MOTIVO_VENCIMIENTO,
    VIGENCIA,
)

_ES_ENCHARCAMIENTO = {TipoConfirmacion.SIGUE_AHI, TipoConfirmacion.YA_NO_HAY_AGUA}


def _no_confirmable(mensaje: str) -> ErrorAPI:
    return ErrorAPI(400, "REPORTE_NO_CONFIRMABLE", mensaje)


def confirmar(db: Session, folio: str, usuario: Usuario, tipo: TipoConfirmacion) -> ConfirmacionOut:
    # Bloqueo de fila: serializa confirmaciones simultáneas y evita carreras en el conteo de vigencia.
    reporte = db.scalar(
        select(Reporte)
        .where(Reporte.folio == folio, Reporte.estado != EstadoReporte.RECHAZADO)
        .with_for_update(of=Reporte)
    )
    if reporte is None:
        db.rollback()
        raise ErrorAPI(404, "NO_ENCONTRADO", f"No existe un reporte con el folio {folio}.")

    es_enc = reporte.tipo_dano == TipoDano.ENCHARCAMIENTO
    if (tipo in _ES_ENCHARCAMIENTO) != es_enc:
        db.rollback()
        raise ErrorAPI(
            400,
            "CONFIRMACION_NO_APLICA",
            "Este tipo de confirmación no corresponde al tipo de daño del reporte.",
        )
    if reporte.usuario_id == usuario.id:
        db.rollback()
        raise ErrorAPI(
            400, "AUTOCONFIRMACION_NO_PERMITIDA", "No puedes confirmar ni desmentir tu propio reporte."
        )

    ahora = ahora_utc()
    if es_enc:
        if reporte.estado == EstadoReporte.ACTIVO and reporte.vigente_hasta <= ahora:
            # Venció sin confirmaciones: se materializa el cierre y se informa.
            fijar_contexto(
                db,
                usuario_id=None,
                origen=OrigenCambio.SISTEMA,
                motivo=MOTIVO_VENCIMIENTO,
                fecha_evento=reporte.vigente_hasta,
            )
            reporte.estado = EstadoReporte.HISTORICO
            db.flush()
            db.commit()
        if reporte.estado != EstadoReporte.ACTIVO:
            db.rollback()
            raise _no_confirmable("El encharcamiento ya no está vigente y no admite más confirmaciones.")
    elif reporte.estado not in ESTADOS_PAVIMENTO_ABIERTOS:
        db.rollback()
        raise _no_confirmable("El reporte ya está cerrado y no admite más confirmaciones.")

    ya = db.scalar(
        select(ConfirmacionReporte.id).where(
            ConfirmacionReporte.reporte_id == reporte.id,
            ConfirmacionReporte.usuario_id == usuario.id,
            ConfirmacionReporte.ciclo_vigencia == reporte.ciclo_vigencia,
        )
    )
    if ya is not None:
        db.rollback()
        raise ErrorAPI(409, "CONFIRMACION_DUPLICADA", "Ya confirmaste este reporte.")

    mensaje = "Gracias. Tu confirmación quedó registrada."
    if tipo == TipoConfirmacion.SIGUE_AHI:
        # RN-06: reinicia las 6 h y abre una nueva vigencia (los "Ya no hay agua" previos dejan de contar).
        reporte.ciclo_vigencia += 1
        reporte.vigencia_inicio = ahora
        reporte.vigente_hasta = ahora + VIGENCIA
        db.flush()
        mensaje = "Gracias. La vigencia del encharcamiento se extendió 6 horas."

    db.add(
        ConfirmacionReporte(
            reporte_id=reporte.id, usuario_id=usuario.id, tipo=tipo, ciclo_vigencia=reporte.ciclo_vigencia
        )
    )
    db.flush()

    if tipo == TipoConfirmacion.YA_NO_HAY_AGUA:
        distintos = db.scalar(
            select(func.count(func.distinct(ConfirmacionReporte.usuario_id))).where(
                ConfirmacionReporte.reporte_id == reporte.id,
                ConfirmacionReporte.tipo == TipoConfirmacion.YA_NO_HAY_AGUA,
                ConfirmacionReporte.ciclo_vigencia == reporte.ciclo_vigencia,
                ConfirmacionReporte.usuario_id != reporte.usuario_id,  # el autor nunca cuenta
            )
        )
        if (distintos or 0) >= DESMENTIDOS_PARA_HISTORICO:
            fijar_contexto(db, usuario_id=None, origen=OrigenCambio.SISTEMA, motivo=MOTIVO_DESMENTIDO)
            reporte.estado = EstadoReporte.HISTORICO
            db.flush()
            mensaje = "Gracias. Con tu confirmación, el encharcamiento pasó a histórico."
        else:
            mensaje = "Gracias. Registramos que ya no hay agua."

    conteos = conteos_confirmaciones(db, [reporte])
    resultado = ConfirmacionOut(
        folio=reporte.folio,
        tipo=tipo,
        estado_reporte=reporte.estado,
        vigencia=vigencia_de(reporte, conteos),
        mensaje=mensaje,
    )
    db.commit()
    return resultado
