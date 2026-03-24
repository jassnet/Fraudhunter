"""add findings lineage columns

Revision ID: 0005_add_findings_lineage
Revises: 0004_add_persisted_findings
Create Date: 2026-03-24
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0005_add_findings_lineage"
down_revision = "0004_add_persisted_findings"
branch_labels = None
depends_on = None


def _add_columns(table_name: str) -> None:
    op.add_column(table_name, sa.Column("computed_by_job_id", sa.Text, nullable=True))
    op.add_column(table_name, sa.Column("settings_updated_at_snapshot", sa.DateTime, nullable=True))
    op.add_column(table_name, sa.Column("source_click_watermark", sa.DateTime, nullable=True))
    op.add_column(table_name, sa.Column("source_conversion_watermark", sa.DateTime, nullable=True))
    op.add_column(table_name, sa.Column("generation_id", sa.Text, nullable=True))


def _drop_columns(table_name: str) -> None:
    op.drop_column(table_name, "generation_id")
    op.drop_column(table_name, "source_conversion_watermark")
    op.drop_column(table_name, "source_click_watermark")
    op.drop_column(table_name, "settings_updated_at_snapshot")
    op.drop_column(table_name, "computed_by_job_id")


def upgrade() -> None:
    _add_columns("suspicious_click_findings")
    _add_columns("suspicious_conversion_findings")
    op.create_index(
        "idx_scf_date_current_computed",
        "suspicious_click_findings",
        ["date", "is_current", "computed_at"],
    )
    op.create_index(
        "idx_scof_date_current_computed",
        "suspicious_conversion_findings",
        ["date", "is_current", "computed_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_scof_date_current_computed", table_name="suspicious_conversion_findings")
    op.drop_index("idx_scf_date_current_computed", table_name="suspicious_click_findings")
    _drop_columns("suspicious_conversion_findings")
    _drop_columns("suspicious_click_findings")
