"""Fase 3 de requisitos opcionales: fusión, cuadrillas, enlace municipal, catálogos y colonias favoritas.

* rol_usuario + 'enlace_municipal' (HU-05.5). Un valor de ENUM no se puede quitar en PostgreSQL: el downgrade lo deja.
* reportes.reporte_principal_id (HU-05.3): el secundario de una fusión apunta al folio principal.
* cuadrillas, asignaciones_cuadrilla (historial; sólo una activa por reporte) y usuario_cuadrillas (HU-05.4, HU-05.5).
* catalogo_tipos_dano y catalogo_motivos_rechazo con `activo` (HU-06.3). Se insertan los valores base necesarios para
  operar (db/seed.py los completa de forma idempotente).
* usuario_colonias_favoritas N:M con llave compuesta (HU-01.4).

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-25
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MOTIVOS_BASE = [
    ("Duplicado", "Ya existe un reporte abierto del mismo daño (se usa al fusionar)."),
    ("Fuera de la vía pública", "El daño está en propiedad privada o fuera de la calle."),
    ("Información insuficiente", "La ubicación o la descripción no permiten identificar el daño."),
    ("No corresponde a un daño", "Lo reportado no es un bache, alcantarilla sin tapa ni encharcamiento."),
    ("Contenido inapropiado", "El reporte contiene lenguaje ofensivo o datos personales."),
]
TIPOS_BASE = [
    ("Bache", "Bache", "Hoyo o hundimiento en el pavimento."),
    ("Alcantarilla sin tapa", "Alcantarilla sin tapa", "Registro o pozo de visita sin tapa (severidad Alta fija)."),
    ("Encharcamiento", "Encharcamiento", "Agua acumulada en la calle."),
]


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE rol_usuario ADD VALUE IF NOT EXISTS 'enlace_municipal'")

    op.execute("ALTER TABLE reportes ADD COLUMN IF NOT EXISTS reporte_principal_id BIGINT REFERENCES reportes(id) ON DELETE RESTRICT")
    op.execute(
        "ALTER TABLE reportes ADD CONSTRAINT ck_principal_distinto CHECK (reporte_principal_id IS NULL OR reporte_principal_id <> id)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_reportes_principal ON reportes (reporte_principal_id) WHERE reporte_principal_id IS NOT NULL")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS cuadrillas (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(120) NOT NULL CHECK (char_length(trim(nombre)) >= 3),
            responsable VARCHAR(120) NOT NULL CHECK (char_length(trim(responsable)) >= 3),
            telefono_contacto VARCHAR(20) NOT NULL CHECK (telefono_contacto ~ '^[0-9 +()-]{7,20}$'),
            activa BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_cuadrillas_nombre ON cuadrillas (lower(nombre))")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS asignaciones_cuadrilla (
            id BIGSERIAL PRIMARY KEY,
            reporte_id BIGINT NOT NULL REFERENCES reportes(id) ON DELETE RESTRICT,
            cuadrilla_id INTEGER NOT NULL REFERENCES cuadrillas(id) ON DELETE RESTRICT,
            fecha_programada DATE NOT NULL,
            asignado_por_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
            activa BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_asignacion_activa ON asignaciones_cuadrilla (reporte_id) WHERE activa")
    op.execute("CREATE INDEX IF NOT EXISTS idx_asignaciones_cuadrilla ON asignaciones_cuadrilla (cuadrilla_id, activa)")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS usuario_cuadrillas (
            usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
            cuadrilla_id INTEGER NOT NULL REFERENCES cuadrillas(id) ON DELETE RESTRICT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (usuario_id, cuadrilla_id)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS catalogo_tipos_dano (
            id SERIAL PRIMARY KEY,
            clave tipo_dano NOT NULL UNIQUE,
            nombre VARCHAR(80) NOT NULL,
            descripcion VARCHAR(300),
            activo BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS catalogo_motivos_rechazo (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(120) NOT NULL CHECK (char_length(trim(nombre)) >= 3),
            descripcion VARCHAR(300),
            activo BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_motivos_nombre ON catalogo_motivos_rechazo (lower(nombre))")
    for clave, nombre, descripcion in TIPOS_BASE:
        op.execute(
            "INSERT INTO catalogo_tipos_dano (clave, nombre, descripcion) "
            f"VALUES ('{clave}', '{nombre}', '{descripcion}') ON CONFLICT (clave) DO NOTHING"
        )
    for nombre, descripcion in MOTIVOS_BASE:
        op.execute(
            "INSERT INTO catalogo_motivos_rechazo (nombre, descripcion) "
            f"SELECT '{nombre}', '{descripcion}' WHERE NOT EXISTS "
            f"(SELECT 1 FROM catalogo_motivos_rechazo WHERE lower(nombre) = lower('{nombre}'))"
        )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS usuario_colonias_favoritas (
            usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
            colonia_id INTEGER NOT NULL REFERENCES colonias(id) ON DELETE RESTRICT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_usuario_colonia_favorita PRIMARY KEY (usuario_id, colonia_id)
        )
        """
    )


def downgrade() -> None:
    for tabla in (
        "usuario_colonias_favoritas", "catalogo_motivos_rechazo", "catalogo_tipos_dano",
        "usuario_cuadrillas", "asignaciones_cuadrilla", "cuadrillas",
    ):
        op.execute(f"DROP TABLE IF EXISTS {tabla}")
    op.execute("DROP INDEX IF EXISTS idx_reportes_principal")
    op.execute("ALTER TABLE reportes DROP CONSTRAINT IF EXISTS ck_principal_distinto")
    op.execute("ALTER TABLE reportes DROP COLUMN IF EXISTS reporte_principal_id")
    # El valor 'enlace_municipal' de rol_usuario no se puede eliminar de un ENUM: se conserva.
