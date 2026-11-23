import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ReporteFoto(Base):
    """Evidencia fotográfica de un reporte (HU-02.4). `created_at` es inmutable (RN-10)."""

    __tablename__ = "reporte_fotos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reporte_id: Mapped[int] = mapped_column(ForeignKey("reportes.id", ondelete="RESTRICT"))
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    ruta_almacenamiento: Mapped[str] = mapped_column(String(80), unique=True)  # UUIDv4 + extensión
    nombre_original: Mapped[str] = mapped_column(String(150))
    mime_type: Mapped[str] = mapped_column(String(20))
    tamano_bytes: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
