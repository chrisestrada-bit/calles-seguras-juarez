from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CacheClima(Base):
    __tablename__ = "cache_clima"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    clave_consulta: Mapped[str] = mapped_column(String(60), unique=True)
    latitud: Mapped[float] = mapped_column(Numeric(9, 6, asdecimal=False))
    longitud: Mapped[float] = mapped_column(Numeric(9, 6, asdecimal=False))
    respuesta: Mapped[dict[str, Any]] = mapped_column(JSONB)
    probabilidad_lluvia_pct: Mapped[float | None] = mapped_column(Numeric(5, 2, asdecimal=False))
    precipitacion_mm: Mapped[float | None] = mapped_column(Numeric(6, 2, asdecimal=False))
    obtenido_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expira_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
