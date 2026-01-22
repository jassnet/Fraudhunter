"""initial postgres schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-01-22
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "click_ipua_daily",
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("media_id", sa.Text, nullable=False),
        sa.Column("program_id", sa.Text, nullable=False),
        sa.Column("ipaddress", sa.Text, nullable=False),
        sa.Column("useragent", sa.Text, nullable=False),
        sa.Column("click_count", sa.Integer, nullable=False),
        sa.Column("first_time", sa.DateTime, nullable=False),
        sa.Column("last_time", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.PrimaryKeyConstraint("date", "media_id", "program_id", "ipaddress", "useragent"),
    )
    op.create_index("idx_click_ipua_daily_date", "click_ipua_daily", ["date"])
    op.create_index("idx_click_ipua_daily_date_ip", "click_ipua_daily", ["date", "ipaddress"])
    op.create_index("idx_click_ipua_daily_media", "click_ipua_daily", ["date", "media_id"])
    op.create_index("idx_click_ipua_daily_program", "click_ipua_daily", ["date", "program_id"])

    op.create_table(
        "click_raw",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("click_time", sa.DateTime, nullable=False),
        sa.Column("media_id", sa.Text),
        sa.Column("program_id", sa.Text),
        sa.Column("ipaddress", sa.Text),
        sa.Column("useragent", sa.Text),
        sa.Column("referrer", sa.Text),
        sa.Column("raw_payload", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("idx_click_raw_time", "click_raw", ["click_time"])
    op.create_index("idx_click_raw_media", "click_raw", ["media_id", "click_time"])
    op.create_index("idx_click_raw_program", "click_raw", ["program_id", "click_time"])

    op.create_table(
        "conversion_raw",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("cid", sa.Text),
        sa.Column("conversion_time", sa.DateTime, nullable=False),
        sa.Column("click_time", sa.DateTime),
        sa.Column("media_id", sa.Text),
        sa.Column("program_id", sa.Text),
        sa.Column("user_id", sa.Text),
        sa.Column("postback_ipaddress", sa.Text),
        sa.Column("postback_useragent", sa.Text),
        sa.Column("entry_ipaddress", sa.Text),
        sa.Column("entry_useragent", sa.Text),
        sa.Column("click_ipaddress", sa.Text),
        sa.Column("click_useragent", sa.Text),
        sa.Column("state", sa.Text),
        sa.Column("raw_payload", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("idx_conversion_raw_time", "conversion_raw", ["conversion_time"])
    op.create_index("idx_conversion_raw_cid", "conversion_raw", ["cid"])
    op.create_index("idx_conversion_raw_media", "conversion_raw", ["media_id", "conversion_time"])
    op.create_index("idx_conversion_raw_program", "conversion_raw", ["program_id", "conversion_time"])

    op.create_table(
        "conversion_ipua_daily",
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("media_id", sa.Text, nullable=False),
        sa.Column("program_id", sa.Text, nullable=False),
        sa.Column("ipaddress", sa.Text, nullable=False),
        sa.Column("useragent", sa.Text, nullable=False),
        sa.Column("conversion_count", sa.Integer, nullable=False),
        sa.Column("first_time", sa.DateTime, nullable=False),
        sa.Column("last_time", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.PrimaryKeyConstraint("date", "media_id", "program_id", "ipaddress", "useragent"),
    )
    op.create_index("idx_conversion_ipua_daily_date", "conversion_ipua_daily", ["date"])
    op.create_index("idx_conversion_ipua_daily_date_ip", "conversion_ipua_daily", ["date", "ipaddress"])
    op.create_index("idx_conversion_ipua_daily_media", "conversion_ipua_daily", ["date", "media_id"])
    op.create_index("idx_conversion_ipua_daily_program", "conversion_ipua_daily", ["date", "program_id"])

    op.create_table(
        "master_media",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("user_id", sa.Text),
        sa.Column("state", sa.Text),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_table(
        "master_promotion",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("state", sa.Text),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_table(
        "master_user",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("company", sa.Text),
        sa.Column("state", sa.Text),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "app_settings",
        sa.Column("key", sa.Text, primary_key=True),
        sa.Column("value", sa.Text, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "job_status",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("job_id", sa.Text),
        sa.Column("message", sa.Text),
        sa.Column("started_at", sa.DateTime),
        sa.Column("completed_at", sa.DateTime),
        sa.Column("result_json", sa.Text),
        sa.CheckConstraint("id = 1", name="job_status_singleton"),
    )
    op.execute(
        "INSERT INTO job_status (id, status, message) "
        "VALUES (1, 'idle', 'No job has been run yet') "
        "ON CONFLICT (id) DO NOTHING;"
    )


def downgrade() -> None:
    op.drop_table("job_status")
    op.drop_table("app_settings")
    op.drop_table("master_user")
    op.drop_table("master_promotion")
    op.drop_table("master_media")
    op.drop_index("idx_conversion_ipua_daily_program", table_name="conversion_ipua_daily")
    op.drop_index("idx_conversion_ipua_daily_media", table_name="conversion_ipua_daily")
    op.drop_index("idx_conversion_ipua_daily_date_ip", table_name="conversion_ipua_daily")
    op.drop_index("idx_conversion_ipua_daily_date", table_name="conversion_ipua_daily")
    op.drop_table("conversion_ipua_daily")
    op.drop_index("idx_conversion_raw_program", table_name="conversion_raw")
    op.drop_index("idx_conversion_raw_media", table_name="conversion_raw")
    op.drop_index("idx_conversion_raw_cid", table_name="conversion_raw")
    op.drop_index("idx_conversion_raw_time", table_name="conversion_raw")
    op.drop_table("conversion_raw")
    op.drop_index("idx_click_raw_program", table_name="click_raw")
    op.drop_index("idx_click_raw_media", table_name="click_raw")
    op.drop_index("idx_click_raw_time", table_name="click_raw")
    op.drop_table("click_raw")
    op.drop_index("idx_click_ipua_daily_program", table_name="click_ipua_daily")
    op.drop_index("idx_click_ipua_daily_media", table_name="click_ipua_daily")
    op.drop_index("idx_click_ipua_daily_date_ip", table_name="click_ipua_daily")
    op.drop_index("idx_click_ipua_daily_date", table_name="click_ipua_daily")
    op.drop_table("click_ipua_daily")
