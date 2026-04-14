"""add due_at to follow-up tasks

Revision ID: 0016_followup_due_at
Revises: 0015_case_assignment_followups
Create Date: 2026-04-13
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0016_followup_due_at"
down_revision = "0015_case_assignment_followups"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("fraud_alert_followup_tasks", sa.Column("due_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("fraud_alert_followup_tasks", "due_at")
