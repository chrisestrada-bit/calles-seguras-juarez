"""Fase 2 de requisitos opcionales: notificaciones (HU-08.2) e idempotencia de envíos offline (HU-08.4).

* notificaciones: aviso al autor cuando cambia el estado de su reporte. Cada persona sólo ve las suyas (API).
* reportes.idempotency_key: UUID generado por el cliente (borradores sin conexión). El índice único parcial
  (usuario_id, idempotency_key) garantiza que reenviar el mismo borrador nunca duplique folios (RN-03).
* Índice parcial de encharcamientos para acelerar la detección de puntos recurrentes (HU-03.4).

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-24
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS notificaciones (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
            reporte_id BIGINT NOT NULL REFERENCES reportes(id) ON DELETE RESTRICT,
            folio VARCHAR(15) NOT NULL,
            mensaje VARCHAR(800) NOT NULL,
            leida BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_notificaciones_usuario ON notificaciones (usuario_id, leida, created_at DESC)"
    )
    op.execute("ALTER TABLE reportes ADD COLUMN IF NOT EXISTS idempotency_key UUID")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_reportes_idempotencia ON reportes (usuario_id, idempotency_key) "
        "WHERE idempotency_key IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_reportes_enc_anio ON reportes (latitud, longitud, created_at) "
        "WHERE tipo_dano = 'Encharcamiento' AND estado <> 'Rechazado'"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_reportes_enc_anio")
    op.execute("DROP INDEX IF EXISTS uq_reportes_idempotencia")
    op.execute("ALTER TABLE reportes DROP COLUMN IF EXISTS idempotency_key")
    op.execute("DROP TABLE IF EXISTS notificaciones")
