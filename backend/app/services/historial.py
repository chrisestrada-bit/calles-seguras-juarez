"""Contexto del historial inmutable (RN-07).

El trigger trg_reportes_historial escribe en historial_estados cada INSERT/cambio de estado leyendo
estas variables de sesión (SET LOCAL). Si no se fijan, la base de datos rechaza el cambio.
"""

import uuid
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import OrigenCambio


def fijar_contexto(
    db: Session,
    *,
    usuario_id: uuid.UUID | None,
    origen: OrigenCambio,
    motivo: str | None = None,
    fecha_evento: datetime | None = None,
) -> None:
    db.execute(
        text(
            "SELECT set_config('app.usuario_id', :usuario, true),"
            " set_config('app.origen', :origen, true),"
            " set_config('app.motivo', :motivo, true),"
            " set_config('app.fecha_evento', :fecha, true)"
        ),
        {
            "usuario": str(usuario_id) if usuario_id else "",
            "origen": origen.value,
            "motivo": motivo or "",
            "fecha": fecha_evento.isoformat() if fecha_evento else "",
        },
    )
