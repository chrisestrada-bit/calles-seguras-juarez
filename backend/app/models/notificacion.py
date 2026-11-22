import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Notificacion(Base):
    """Aviso para el autor de un reporte (HU-08.2). Sólo lo lee su dueño."""

    __tablename__ = "notificaciones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    reporte_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("reportes.id", ondelete="RESTRICT"))
    folio: Mapped[str] = mapped_column(String(15))
    mensaje: Mapped[str] = mapped_column(String(800))
    leida: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
