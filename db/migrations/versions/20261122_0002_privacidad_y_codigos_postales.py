"""Consentimiento del aviso de privacidad (HU-01.2) y códigos postales de Ciudad Juárez.

* usuarios.aviso_privacidad_aceptado_at: fecha (UTC, RN-02) en que la persona aceptó el aviso de privacidad
  al registrarse (LFPDPPP). Las cuentas creadas antes de esta migración quedan en NULL.
* colonias.codigo_postal: se restringe al rango del municipio (32000–32730, SEPOMEX) y se indexa para
  la búsqueda por código postal (?q=32xxx).

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-22
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS aviso_privacidad_aceptado_at TIMESTAMPTZ")
    op.execute(
        "ALTER TABLE colonias ADD CONSTRAINT ck_colonias_cp_juarez "
        "CHECK (codigo_postal IS NULL OR codigo_postal BETWEEN '32000' AND '32730')"
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_colonias_codigo_postal ON colonias (codigo_postal)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_colonias_codigo_postal")
    op.execute("ALTER TABLE colonias DROP CONSTRAINT IF EXISTS ck_colonias_cp_juarez")
    op.execute("ALTER TABLE usuarios DROP COLUMN IF EXISTS aviso_privacidad_aceptado_at")
