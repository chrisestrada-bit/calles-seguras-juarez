"""Modelos de la Fase 3: cuadrillas (HU-05.4/05.5), catálogos administrables (HU-06.3) y colonias favoritas (HU-01.4)."""

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, pg_enum
from app.models.enums import TipoDano
from app.models.territorio import Colonia


class Cuadrilla(Base):
    __tablename__ = "cuadrillas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(120))
    responsable: Mapped[str] = mapped_column(String(120))
    telefono_contacto: Mapped[str] = mapped_column(String(20))
    activa: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AsignacionCuadrilla(Base):
    """Historial de asignaciones: un reporte puede pasar por varias cuadrillas; sólo una está activa."""

    __tablename__ = "asignaciones_cuadrilla"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    reporte_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("reportes.id", ondelete="RESTRICT"))
    cuadrilla_id: Mapped[int] = mapped_column(ForeignKey("cuadrillas.id", ondelete="RESTRICT"))
    fecha_programada: Mapped[date] = mapped_column(Date)
    asignado_por_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    activa: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    cuadrilla: Mapped[Cuadrilla] = relationship(lazy="joined", innerjoin=True)


class UsuarioCuadrilla(Base):
    """Vincula una cuenta `enlace_municipal` con las cuadrillas cuyo avance puede reportar."""

    __tablename__ = "usuario_cuadrillas"

    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), primary_key=True)
    cuadrilla_id: Mapped[int] = mapped_column(ForeignKey("cuadrillas.id", ondelete="RESTRICT"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CatalogoTipoDano(Base):
    __tablename__ = "catalogo_tipos_dano"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    clave: Mapped[TipoDano] = mapped_column(pg_enum(TipoDano, "tipo_dano"), unique=True)
    nombre: Mapped[str] = mapped_column(String(80))
    descripcion: Mapped[str | None] = mapped_column(String(300))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CatalogoMotivoRechazo(Base):
    __tablename__ = "catalogo_motivos_rechazo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(120))
    descripcion: Mapped[str | None] = mapped_column(String(300))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ColoniaFavorita(Base):
    __tablename__ = "usuario_colonias_favoritas"

    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), primary_key=True)
    colonia_id: Mapped[int] = mapped_column(ForeignKey("colonias.id", ondelete="RESTRICT"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    colonia: Mapped[Colonia] = relationship(lazy="joined", innerjoin=True)
