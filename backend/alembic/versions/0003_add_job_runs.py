"""add durable job runs

Revision ID: 0003_add_job_runs
Revises: 0002_add_ipua_date_ip_ua_index
Create Date: 2026-03-23
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0003_add_job_runs"
down_revision = "0002_add_ipua_date_ip_ua_index"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_runs",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("job_type", sa.Text, nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("params_json", sa.Text),
        sa.Column("result_json", sa.Text),
        sa.Column("error_message", sa.Text),
        sa.Column("message", sa.Text),
        sa.Column("queued_at", sa.DateTime, nullable=False),
        sa.Column("started_at", sa.DateTime),
        sa.Column("finished_at", sa.DateTime),
        sa.Column("heartbeat_at", sa.DateTime),
        sa.Column("locked_until", sa.DateTime),
        sa.Column("worker_id", sa.Text),
    )
    op.create_index("idx_job_runs_status_queued_at", "job_runs", ["status", "queued_at"])
    op.create_index("idx_job_runs_job_type_queued_at", "job_runs", ["job_type", "queued_at"])
    op.create_index("idx_job_runs_locked_until", "job_runs", ["locked_until"])


def downgrade() -> None:
    op.drop_index("idx_job_runs_locked_until", table_name="job_runs")
    op.drop_index("idx_job_runs_job_type_queued_at", table_name="job_runs")
    op.drop_index("idx_job_runs_status_queued_at", table_name="job_runs")
    op.drop_table("job_runs")
