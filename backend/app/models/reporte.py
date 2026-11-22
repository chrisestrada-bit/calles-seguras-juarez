import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, pg_enum
from app.models.enums import (
    CarrilAfectado,
    EstadoReporte,
    NivelAgua,
    ProfundidadBache,
    Severidad,
    TamanoBache,
    TipoDano,
)
from app.models.territorio import Colonia


class Reporte(Base):
    """Tabla única para baches, alcantarillas sin tapa y encharcamientos (ver docs/arquitectura.md §4.4)."""

    __tablename__ = "reportes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)  # nunca se expone
    folio: Mapped[str] = mapped_column(String(15), unique=True)
    tipo_dano: Mapped[TipoDano] = mapped_column(pg_enum(TipoDano, "tipo_dano"))
    estado: Mapped[EstadoReporte] = mapped_column(pg_enum(EstadoReporte, "estado_reporte"))
    severidad: Mapped[Severidad] = mapped_column(pg_enum(Severidad, "severidad"))
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    colonia_id: Mapped[int] = mapped_column(ForeignKey("colonias.id", ondelete="RESTRICT"))
    latitud: Mapped[float] = mapped_column(Numeric(9, 6, asdecimal=False))
    longitud: Mapped[float] = mapped_column(Numeric(9, 6, asdecimal=False))
    calle: Mapped[str] = mapped_column(String(150))
    referencia: Mapped[str | None] = mapped_column(String(200))
    descripcion: Mapped[str | None] = mapped_column(String(500))

    # Campos condicionales por tipo de daño (HU-02.2 / HU-03.1)
    tamano: Mapped[TamanoBache | None] = mapped_column(pg_enum(TamanoBache, "tamano_bache"))
    profundidad: Mapped[ProfundidadBache | None] = mapped_column(
        pg_enum(ProfundidadBache, "profundidad_bache")
    )
    carril_afectado: Mapped[CarrilAfectado | None] = mapped_column(
        pg_enum(CarrilAfectado, "carril_afectado")
    )
    esta_senalizado: Mapped[bool | None] = mapped_column(Boolean)
    nivel_agua: Mapped[NivelAgua | None] = mapped_column(pg_enum(NivelAgua, "nivel_agua"))
    hay_riesgo_personas_vehiculos: Mapped[bool | None] = mapped_column(Boolean)

    # Vigencia de encharcamientos (RN-06)
    vigencia_inicio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    vigente_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ciclo_vigencia: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))

    fecha_programada: Mapped[date | None] = mapped_column(Date)
    fecha_reparacion: Mapped[date | None] = mapped_column(Date)
    motivo_rechazo: Mapped[str | None] = mapped_column(String(500))
    # HU-08.4: UUID del cliente para que reenviar un borrador offline nunca duplique el folio (RN-03).
    idempotency_key: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    forzado_como_nuevo: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    colonia: Mapped[Colonia] = relationship(lazy="joined", innerjoin=True)
