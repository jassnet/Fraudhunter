"""add date/ip/useragent indexes

Revision ID: 0002_add_ipua_date_ip_ua_index
Revises: 0001_initial
Create Date: 2026-01-28
"""
from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_add_ipua_date_ip_ua_index"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_click_ipua_daily_date_ip_ua",
        "click_ipua_daily",
        ["date", "ipaddress", "useragent"],
    )
    op.create_index(
        "idx_conversion_ipua_daily_date_ip_ua",
        "conversion_ipua_daily",
        ["date", "ipaddress", "useragent"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_conversion_ipua_daily_date_ip_ua",
        table_name="conversion_ipua_daily",
    )
    op.drop_index(
        "idx_click_ipua_daily_date_ip_ua",
        table_name="click_ipua_daily",
    )
