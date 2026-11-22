"""Vigencia de encharcamientos (RN-06): 6 horas, evaluada dinámicamente y materializada en consulta."""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.tiempo import ahora_utc
from app.models import EstadoReporte, OrigenCambio, Reporte, TipoDano
from app.services.historial import fijar_contexto

HORAS_VIGENCIA = 6
DESMENTIDOS_PARA_HISTORICO = 3
VIGENCIA = timedelta(hours=HORAS_VIGENCIA)

MOTIVO_VENCIMIENTO = "Sin confirmaciones durante 6 horas"
MOTIVO_DESMENTIDO = "3 usuarios reportaron que ya no hay agua"


def expirar_vencidos(db: Session) -> int:
    """Pasa a Histórico los encharcamientos cuya vigencia terminó. Se llama al inicio de las consultas.

    El historial registra el instante real del vencimiento (vigente_hasta), no la hora de ejecución.
    Hace commit sólo si cambió algo; debe invocarse antes de iniciar trabajo de escritura propio.
    """
    vencidos = db.scalars(
        select(Reporte)
        .where(
            Reporte.tipo_dano == TipoDano.ENCHARCAMIENTO,
            Reporte.estado == EstadoReporte.ACTIVO,
            Reporte.vigente_hasta <= ahora_utc(),
        )
        .with_for_update(skip_locked=True, of=Reporte)
    ).all()
    for reporte in vencidos:
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
    return len(vencidos)


def esta_vigente(reporte: Reporte) -> bool:
    return (
        reporte.estado == EstadoReporte.ACTIVO
        and reporte.vigente_hasta is not None
        and reporte.vigente_hasta > ahora_utc()
    )
