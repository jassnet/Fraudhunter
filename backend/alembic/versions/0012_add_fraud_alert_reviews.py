"""add fraud alert reviews

Revision ID: 0012_add_fraud_alert_reviews
Revises: 0011_add_acs_native_fraud
Create Date: 2026-04-05
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0012_add_fraud_alert_reviews"
down_revision = "0011_add_acs_native_fraud"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fraud_alert_reviews",
        sa.Column("finding_key", sa.Text(), nullable=False),
        sa.Column("review_status", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("finding_key"),
    )
    op.create_index(
        "idx_fraud_alert_reviews_status_updated",
        "fraud_alert_reviews",
        ["review_status", "updated_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_fraud_alert_reviews_status_updated", table_name="fraud_alert_reviews")
    op.drop_table("fraud_alert_reviews")
