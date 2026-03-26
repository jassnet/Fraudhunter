"""add concurrency controls to job runs

Revision ID: 0008_job_run_concurrency
Revises: 0007_settings_findings_gen
Create Date: 2026-03-26
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0008_job_run_concurrency"
down_revision = "0007_settings_findings_gen"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("job_runs", sa.Column("concurrency_key", sa.Text(), nullable=True))
    op.create_index(
        "idx_job_runs_concurrency_status",
        "job_runs",
        ["concurrency_key", "status", "queued_at"],
    )
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            CREATE UNIQUE INDEX ux_job_runs_active_dedupe_key
            ON job_runs (dedupe_key)
            WHERE dedupe_key IS NOT NULL AND status IN ('queued', 'running')
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ux_job_runs_active_dedupe_key")
    op.drop_index("idx_job_runs_concurrency_status", table_name="job_runs")
    op.drop_column("job_runs", "concurrency_key")
