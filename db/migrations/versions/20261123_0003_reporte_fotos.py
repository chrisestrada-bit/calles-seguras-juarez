"""Evidencia fotográfica de reportes (HU-02.4).

* reporte_fotos: hasta 3 fotos por persona y reporte (se valida en la API); `created_at` es inmutable (RN-10),
  lo garantiza un trigger que rechaza cualquier UPDATE de las columnas de identidad y de fecha.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-23
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS reporte_fotos (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            reporte_id BIGINT NOT NULL REFERENCES reportes(id) ON DELETE RESTRICT,
            usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
            ruta_almacenamiento VARCHAR(80) NOT NULL UNIQUE,
            nombre_original VARCHAR(150) NOT NULL,
            mime_type VARCHAR(20) NOT NULL CHECK (mime_type IN ('image/jpeg', 'image/png')),
            tamano_bytes INTEGER NOT NULL CHECK (tamano_bytes > 0 AND tamano_bytes <= 5242880),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_reporte_fotos_reporte ON reporte_fotos (reporte_id, created_at)")
    op.execute(
        """
        CREATE OR REPLACE FUNCTION fn_reporte_fotos_inmutable() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'Las fotografías de un reporte son inmutables (RN-10).';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute("DROP TRIGGER IF EXISTS trg_reporte_fotos_inmutable ON reporte_fotos")
    op.execute(
        "CREATE TRIGGER trg_reporte_fotos_inmutable BEFORE UPDATE ON reporte_fotos "
        "FOR EACH ROW EXECUTE FUNCTION fn_reporte_fotos_inmutable()"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_reporte_fotos_inmutable ON reporte_fotos")
    op.execute("DROP FUNCTION IF EXISTS fn_reporte_fotos_inmutable()")
    op.execute("DROP TABLE IF EXISTS reporte_fotos")
