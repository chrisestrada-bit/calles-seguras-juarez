import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, SmallInteger, String, func, text
from sqlalchemy.dialects.postgresql import CITEXT, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, pg_enum
from app.models.enums import RolUsuario


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    nombre: Mapped[str] = mapped_column(String(120))  # dato personal (RN-04)
    correo: Mapped[str] = mapped_column(CITEXT, unique=True)  # dato personal (RN-04)
    password_hash: Mapped[str] = mapped_column(String(255))
    rol: Mapped[RolUsuario] = mapped_column(
        pg_enum(RolUsuario, "rol_usuario"), default=RolUsuario.CIUDADANO, server_default="ciudadano"
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    token_version: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    intentos_fallidos: Mapped[int] = mapped_column(SmallInteger, default=0, server_default=text("0"))
    bloqueado_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
