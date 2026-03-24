"""add retry and dedupe controls to job runs

Revision ID: 0006_add_job_run_controls
Revises: 0005_add_findings_lineage
Create Date: 2026-03-24
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0006_add_job_run_controls"
down_revision = "0005_add_findings_lineage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("job_runs", sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("job_runs", sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("job_runs", sa.Column("next_retry_at", sa.DateTime(), nullable=True))
    op.add_column("job_runs", sa.Column("dedupe_key", sa.Text(), nullable=True))
    op.add_column("job_runs", sa.Column("priority", sa.Integer(), nullable=False, server_default="100"))
    op.create_index(
        "idx_job_runs_queue_scan",
        "job_runs",
        ["status", "next_retry_at", "priority", "queued_at"],
    )
    op.create_index(
        "idx_job_runs_dedupe_status",
        "job_runs",
        ["dedupe_key", "status", "queued_at"],
    )
    op.alter_column("job_runs", "attempt_count", server_default=None)
    op.alter_column("job_runs", "max_attempts", server_default=None)
    op.alter_column("job_runs", "priority", server_default=None)


def downgrade() -> None:
    op.drop_index("idx_job_runs_dedupe_status", table_name="job_runs")
    op.drop_index("idx_job_runs_queue_scan", table_name="job_runs")
    op.drop_column("job_runs", "priority")
    op.drop_column("job_runs", "dedupe_key")
    op.drop_column("job_runs", "next_retry_at")
    op.drop_column("job_runs", "max_attempts")
    op.drop_column("job_runs", "attempt_count")
