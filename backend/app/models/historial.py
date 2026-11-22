import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, pg_enum
from app.models.enums import EstadoReporte, OrigenCambio


class HistorialEstado(Base):
    """Bitácora append-only (RN-07). Las filas las escribe el trigger trg_reportes_historial."""

    __tablename__ = "historial_estados"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    reporte_id: Mapped[int] = mapped_column(ForeignKey("reportes.id", ondelete="RESTRICT"))
    estado_anterior: Mapped[EstadoReporte | None] = mapped_column(pg_enum(EstadoReporte, "estado_reporte"))
    estado_nuevo: Mapped[EstadoReporte] = mapped_column(pg_enum(EstadoReporte, "estado_reporte"))
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    origen: Mapped[OrigenCambio] = mapped_column(pg_enum(OrigenCambio, "origen_cambio"))
    motivo: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
