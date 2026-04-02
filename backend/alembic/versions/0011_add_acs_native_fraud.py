"""add ACS-native fraud storage

Revision ID: 0011_add_acs_native_fraud
Revises: 0010_drop_click_findings
Create Date: 2026-04-02
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0011_add_acs_native_fraud"
down_revision = "0010_drop_click_findings"
branch_labels = None
depends_on = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_table(inspector, "master_promotion"):
        if not _has_column(inspector, "master_promotion", "action_double_state"):
            op.add_column("master_promotion", sa.Column("action_double_state", sa.Integer(), nullable=True))
        if not _has_column(inspector, "master_promotion", "action_double_type_json"):
            op.add_column("master_promotion", sa.Column("action_double_type_json", sa.Text(), nullable=True))

    if not _has_table(inspector, "check_raw"):
        op.create_table(
            "check_raw",
            sa.Column("id", sa.Text(), nullable=False),
            sa.Column("affiliate_user_id", sa.Text(), nullable=True),
            sa.Column("plid", sa.Text(), nullable=True),
            sa.Column("state", sa.Integer(), nullable=True),
            sa.Column("regist_time", sa.DateTime(), nullable=False),
            sa.Column("raw_payload", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("idx_check_raw_time", "check_raw", ["regist_time"])
        op.create_index("idx_check_raw_user", "check_raw", ["affiliate_user_id", "regist_time"])
        op.create_index("idx_check_raw_state", "check_raw", ["state", "regist_time"])
        op.create_index("idx_check_raw_plid", "check_raw", ["plid"])

    if not _has_table(inspector, "track_raw"):
        op.create_table(
            "track_raw",
            sa.Column("id", sa.Text(), nullable=False),
            sa.Column("action_log_raw_id", sa.Text(), nullable=True),
            sa.Column("auth_type", sa.Text(), nullable=True),
            sa.Column("auth_get_type", sa.Text(), nullable=True),
            sa.Column("state", sa.Integer(), nullable=True),
            sa.Column("regist_time", sa.DateTime(), nullable=False),
            sa.Column("raw_payload", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("idx_track_raw_time", "track_raw", ["regist_time"])
        op.create_index("idx_track_raw_action", "track_raw", ["action_log_raw_id"])
        op.create_index("idx_track_raw_auth_type", "track_raw", ["auth_type", "regist_time"])

    for table_name, value_column, count_index_name, user_index_name, media_index_name, promo_index_name in (
        ("click_sum_daily", "click_count", "idx_click_sum_daily_date", "idx_click_sum_daily_user", "idx_click_sum_daily_media", "idx_click_sum_daily_promotion"),
        ("access_sum_daily", "access_count", "idx_access_sum_daily_date", "idx_access_sum_daily_user", "idx_access_sum_daily_media", "idx_access_sum_daily_promotion"),
        ("imp_sum_daily", "imp_count", "idx_imp_sum_daily_date", "idx_imp_sum_daily_user", "idx_imp_sum_daily_media", "idx_imp_sum_daily_promotion"),
    ):
        if _has_table(inspector, table_name):
            continue
        op.create_table(
            table_name,
            sa.Column("date", sa.Date(), nullable=False),
            sa.Column("user_id", sa.Text(), nullable=False),
            sa.Column("media_id", sa.Text(), nullable=False),
            sa.Column("promotion_id", sa.Text(), nullable=False),
            sa.Column(value_column, sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("date", "user_id", "media_id", "promotion_id"),
        )
        op.create_index(count_index_name, table_name, ["date"])
        op.create_index(user_index_name, table_name, ["date", "user_id"])
        op.create_index(media_index_name, table_name, ["date", "media_id"])
        op.create_index(promo_index_name, table_name, ["date", "promotion_id"])

    if not _has_table(inspector, "fraud_findings"):
        op.create_table(
            "fraud_findings",
            sa.Column("finding_key", sa.Text(), nullable=False),
            sa.Column("date", sa.Date(), nullable=False),
            sa.Column("user_id", sa.Text(), nullable=False),
            sa.Column("media_id", sa.Text(), nullable=False),
            sa.Column("promotion_id", sa.Text(), nullable=False),
            sa.Column("user_name", sa.Text(), nullable=True),
            sa.Column("media_name", sa.Text(), nullable=True),
            sa.Column("promotion_name", sa.Text(), nullable=True),
            sa.Column("risk_level", sa.Text(), nullable=False),
            sa.Column("risk_score", sa.Integer(), nullable=False),
            sa.Column("reasons_json", sa.Text(), nullable=False),
            sa.Column("reasons_formatted_json", sa.Text(), nullable=False),
            sa.Column("metrics_json", sa.Text(), nullable=False),
            sa.Column("primary_metric", sa.Integer(), nullable=False),
            sa.Column("first_time", sa.DateTime(), nullable=True),
            sa.Column("last_time", sa.DateTime(), nullable=True),
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
        op.create_index("idx_ff_date_current", "fraud_findings", ["date", "is_current"])
        op.create_index(
            "idx_ff_date_current_risk",
            "fraud_findings",
            ["date", "is_current", "risk_level"],
        )
        op.create_index(
            "idx_ff_date_current_entity",
            "fraud_findings",
            ["date", "is_current", "user_id", "media_id", "promotion_id"],
        )
        op.create_index(
            "idx_ff_date_current_computed",
            "fraud_findings",
            ["date", "is_current", "computed_at"],
        )

        if bind.dialect.name == "postgresql":
            op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
            op.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_ff_search_text_trgm
                ON fraud_findings
                USING gin (search_text gin_trgm_ops)
                WHERE is_current = TRUE
                """
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if bind.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS idx_ff_search_text_trgm")

    if _has_table(inspector, "fraud_findings"):
        op.drop_table("fraud_findings")
    for table_name in ("imp_sum_daily", "access_sum_daily", "click_sum_daily", "track_raw", "check_raw"):
        if _has_table(inspector, table_name):
            op.drop_table(table_name)

    if _has_table(inspector, "master_promotion"):
        if _has_column(inspector, "master_promotion", "action_double_type_json"):
            op.drop_column("master_promotion", "action_double_type_json")
        if _has_column(inspector, "master_promotion", "action_double_state"):
            op.drop_column("master_promotion", "action_double_state")
