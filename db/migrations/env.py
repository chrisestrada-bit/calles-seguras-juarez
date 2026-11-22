"""Entorno de Alembic. La URL sale de DATABASE_URL (variable de entorno o .env), sin secretos en el repo."""

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, pool

# Permite ejecutar fuera de Docker: agrega backend/ al path para importar app.core.config.
_RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_RAIZ / "backend"))

from app.core.config import get_settings  # noqa: E402

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# El esquema se define con SQL explícito en las migraciones (enums, CHECK, triggers, índices parciales).
target_metadata = None


def run_migrations_offline() -> None:
    context.configure(url=get_settings().database_url, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(get_settings().database_url, poolclass=pool.NullPool)
    with engine.connect() as conexion:
        context.configure(connection=conexion, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
