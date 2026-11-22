"""Base declarativa y utilidades de tipos compartidas por los modelos."""

import enum
from datetime import datetime
from typing import TypeVar

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

E = TypeVar("E", bound=enum.Enum)


class Base(DeclarativeBase):
    pass


def pg_enum(clase: type[E], nombre: str) -> PGEnum:
    """ENUM nativo de PostgreSQL ya creado por Alembic (no se vuelve a crear)."""
    return PGEnum(
        clase,
        name=nombre,
        values_callable=lambda e: [m.value for m in e],
        create_type=False,
        validate_strings=True,
    )


def columna_fecha_creacion() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
