"""drop deprecated click findings storage

Revision ID: 0010_drop_click_findings
Revises: 0009_findings_search_idx
Create Date: 2026-03-31
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0010_drop_click_findings"
down_revision = "0009_findings_search_idx"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())

    if bind.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS idx_scf_search_text_trgm")

    if "findings_generations" in table_names:
        op.execute("DELETE FROM findings_generations WHERE finding_type = 'click'")

    if "suspicious_click_findings" in table_names:
        op.drop_table("suspicious_click_findings")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())

    if "suspicious_click_findings" not in table_names:
        op.create_table(
            "suspicious_click_findings",
            sa.Column("finding_key", sa.Text(), nullable=False),
            sa.Column("date", sa.Date(), nullable=False),
            sa.Column("ipaddress", sa.Text(), nullable=False),
            sa.Column("useragent", sa.Text(), nullable=False),
            sa.Column("ua_hash", sa.Text(), nullable=False),
            sa.Column("media_ids_json", sa.Text(), nullable=True),
            sa.Column("program_ids_json", sa.Text(), nullable=True),
            sa.Column("media_names_json", sa.Text(), nullable=True),
            sa.Column("program_names_json", sa.Text(), nullable=True),
            sa.Column("affiliate_names_json", sa.Text(), nullable=True),
            sa.Column("risk_level", sa.Text(), nullable=False),
            sa.Column("risk_score", sa.Integer(), nullable=False),
            sa.Column("reasons_json", sa.Text(), nullable=False),
            sa.Column("reasons_formatted_json", sa.Text(), nullable=False),
            sa.Column("metrics_json", sa.Text(), nullable=False),
            sa.Column("total_clicks", sa.Integer(), nullable=False),
            sa.Column("media_count", sa.Integer(), nullable=False),
            sa.Column("program_count", sa.Integer(), nullable=False),
            sa.Column("first_time", sa.DateTime(), nullable=False),
            sa.Column("last_time", sa.DateTime(), nullable=False),
            sa.Column("rule_version", sa.Text(), nullable=False),
            sa.Column("computed_at", sa.DateTime(), nullable=False),
            sa.Column("computed_by_job_id", sa.Text(), nullable=True),
            sa.Column("settings_updated_at_snapshot", sa.DateTime(), nullable=True),
            sa.Column("source_click_watermark", sa.DateTime(), nullable=True),
            sa.Column("source_conversion_watermark", sa.DateTime(), nullable=True),
            sa.Column("generation_id", sa.Text(), nullable=True),
            sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("search_text", sa.Text(), nullable=False),
            sa.PrimaryKeyConstraint("finding_key"),
        )
        op.create_index("idx_scf_date_current", "suspicious_click_findings", ["date", "is_current"])
        op.create_index(
            "idx_scf_date_current_risk",
            "suspicious_click_findings",
            ["date", "is_current", "risk_level"],
        )
        op.create_index(
            "idx_scf_date_current_computed",
            "suspicious_click_findings",
            ["date", "is_current", "computed_at"],
        )

    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_scf_search_text_trgm
            ON suspicious_click_findings
            USING gin (search_text gin_trgm_ops)
            WHERE is_current = TRUE
            """
        )
