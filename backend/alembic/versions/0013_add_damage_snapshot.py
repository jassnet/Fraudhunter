"""add damage snapshot columns to suspicious conversion findings

Revision ID: 0013_add_damage_snapshot
Revises: 0012_add_fraud_alert_reviews
Create Date: 2026-04-08
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0013_add_damage_snapshot"
down_revision = "0012_add_fraud_alert_reviews"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "suspicious_conversion_findings",
        sa.Column("affiliate_ids_json", sa.Text(), nullable=True),
    )
    op.add_column(
        "suspicious_conversion_findings",
        sa.Column("estimated_damage_yen", sa.Integer(), nullable=True),
    )
    op.add_column(
        "suspicious_conversion_findings",
        sa.Column("damage_unit_price_source", sa.Text(), nullable=True),
    )
    op.add_column(
        "suspicious_conversion_findings",
        sa.Column("damage_evidence_json", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("suspicious_conversion_findings", "damage_evidence_json")
    op.drop_column("suspicious_conversion_findings", "damage_unit_price_source")
    op.drop_column("suspicious_conversion_findings", "estimated_damage_yen")
    op.drop_column("suspicious_conversion_findings", "affiliate_ids_json")
