"""add trigram search indexes for findings

Revision ID: 0009_findings_search_idx
Revises: 0008_job_run_concurrency
Create Date: 2026-03-26
"""
from __future__ import annotations

from alembic import op


revision = "0009_findings_search_idx"
down_revision = "0008_job_run_concurrency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_scf_search_text_trgm
        ON suspicious_click_findings
        USING gin (search_text gin_trgm_ops)
        WHERE is_current = TRUE
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_scof_search_text_trgm
        ON suspicious_conversion_findings
        USING gin (search_text gin_trgm_ops)
        WHERE is_current = TRUE
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute("DROP INDEX IF EXISTS idx_scof_search_text_trgm")
    op.execute("DROP INDEX IF EXISTS idx_scf_search_text_trgm")
