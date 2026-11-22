"""Motor y sesiones de SQLAlchemy 2.0. La sesión de PostgreSQL siempre trabaja en UTC (RN-02)."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

_settings = get_settings()

engine = create_engine(
    _settings.database_url,
    echo=_settings.db_echo,
    pool_pre_ping=True,
    connect_args={"options": "-c timezone=utc"},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
