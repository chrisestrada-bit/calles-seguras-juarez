from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Sector(Base):
    __tablename__ = "sectores"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    clave: Mapped[str] = mapped_column(String(20), unique=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Colonia(Base):
    __tablename__ = "colonias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sector_id: Mapped[int] = mapped_column(ForeignKey("sectores.id", ondelete="RESTRICT"))
    nombre: Mapped[str] = mapped_column(String(120))
    codigo_postal: Mapped[str | None] = mapped_column(String(5))
    latitud_centro: Mapped[float] = mapped_column(Numeric(9, 6, asdecimal=False))
    longitud_centro: Mapped[float] = mapped_column(Numeric(9, 6, asdecimal=False))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sector: Mapped[Sector] = relationship(lazy="joined", innerjoin=True)
