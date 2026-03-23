"""add persisted suspicious findings

Revision ID: 0004_add_persisted_findings
Revises: 0003_add_job_runs
Create Date: 2026-03-23
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0004_add_persisted_findings"
down_revision = "0003_add_job_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "suspicious_click_findings",
        sa.Column("finding_key", sa.Text, primary_key=True),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("ipaddress", sa.Text, nullable=False),
        sa.Column("useragent", sa.Text, nullable=False),
        sa.Column("ua_hash", sa.Text, nullable=False),
        sa.Column("media_ids_json", sa.Text),
        sa.Column("program_ids_json", sa.Text),
        sa.Column("media_names_json", sa.Text),
        sa.Column("program_names_json", sa.Text),
        sa.Column("affiliate_names_json", sa.Text),
        sa.Column("risk_level", sa.Text, nullable=False),
        sa.Column("risk_score", sa.Integer, nullable=False),
        sa.Column("reasons_json", sa.Text, nullable=False),
        sa.Column("reasons_formatted_json", sa.Text, nullable=False),
        sa.Column("metrics_json", sa.Text, nullable=False),
        sa.Column("total_clicks", sa.Integer, nullable=False),
        sa.Column("media_count", sa.Integer, nullable=False),
        sa.Column("program_count", sa.Integer, nullable=False),
        sa.Column("first_time", sa.DateTime, nullable=False),
        sa.Column("last_time", sa.DateTime, nullable=False),
        sa.Column("rule_version", sa.Text, nullable=False),
        sa.Column("computed_at", sa.DateTime, nullable=False),
        sa.Column("is_current", sa.Boolean, nullable=False),
        sa.Column("search_text", sa.Text, nullable=False),
    )
    op.create_index("idx_scf_date_current", "suspicious_click_findings", ["date", "is_current"])
    op.create_index(
        "idx_scf_date_current_risk",
        "suspicious_click_findings",
        ["date", "is_current", "risk_level"],
    )

    op.create_table(
        "suspicious_conversion_findings",
        sa.Column("finding_key", sa.Text, primary_key=True),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("ipaddress", sa.Text, nullable=False),
        sa.Column("useragent", sa.Text, nullable=False),
        sa.Column("ua_hash", sa.Text, nullable=False),
        sa.Column("media_ids_json", sa.Text),
        sa.Column("program_ids_json", sa.Text),
        sa.Column("media_names_json", sa.Text),
        sa.Column("program_names_json", sa.Text),
        sa.Column("affiliate_names_json", sa.Text),
        sa.Column("risk_level", sa.Text, nullable=False),
        sa.Column("risk_score", sa.Integer, nullable=False),
        sa.Column("reasons_json", sa.Text, nullable=False),
        sa.Column("reasons_formatted_json", sa.Text, nullable=False),
        sa.Column("metrics_json", sa.Text, nullable=False),
        sa.Column("total_conversions", sa.Integer, nullable=False),
        sa.Column("media_count", sa.Integer, nullable=False),
        sa.Column("program_count", sa.Integer, nullable=False),
        sa.Column("min_click_to_conv_seconds", sa.Integer),
        sa.Column("max_click_to_conv_seconds", sa.Integer),
        sa.Column("first_time", sa.DateTime, nullable=False),
        sa.Column("last_time", sa.DateTime, nullable=False),
        sa.Column("rule_version", sa.Text, nullable=False),
        sa.Column("computed_at", sa.DateTime, nullable=False),
        sa.Column("is_current", sa.Boolean, nullable=False),
        sa.Column("search_text", sa.Text, nullable=False),
    )
    op.create_index("idx_scof_date_current", "suspicious_conversion_findings", ["date", "is_current"])
    op.create_index(
        "idx_scof_date_current_risk",
        "suspicious_conversion_findings",
        ["date", "is_current", "risk_level"],
    )


def downgrade() -> None:
    op.drop_index("idx_scof_date_current_risk", table_name="suspicious_conversion_findings")
    op.drop_index("idx_scof_date_current", table_name="suspicious_conversion_findings")
    op.drop_table("suspicious_conversion_findings")
    op.drop_index("idx_scf_date_current_risk", table_name="suspicious_click_findings")
    op.drop_index("idx_scf_date_current", table_name="suspicious_click_findings")
    op.drop_table("suspicious_click_findings")
