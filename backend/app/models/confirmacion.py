import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, pg_enum
from app.models.enums import TipoConfirmacion


class ConfirmacionReporte(Base):
    __tablename__ = "confirmaciones_reporte"
    __table_args__ = (UniqueConstraint("reporte_id", "usuario_id", "ciclo_vigencia"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    reporte_id: Mapped[int] = mapped_column(ForeignKey("reportes.id", ondelete="RESTRICT"))
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    tipo: Mapped[TipoConfirmacion] = mapped_column(pg_enum(TipoConfirmacion, "tipo_confirmacion"))
    ciclo_vigencia: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
