"""add case assignments and follow-up tasks

Revision ID: 0015_case_assignment_followups
Revises: 0014_case_key_review_hist
Create Date: 2026-04-13
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0015_case_assignment_followups"
down_revision = "0014_case_key_review_hist"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fraud_alert_case_assignments",
        sa.Column("case_key", sa.Text(), nullable=False),
        sa.Column("assignee_user_id", sa.Text(), nullable=False),
        sa.Column("assigned_by", sa.Text(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("case_key"),
    )
    op.create_index(
        "idx_fraud_alert_case_assignments_user_updated",
        "fraud_alert_case_assignments",
        ["assignee_user_id", "updated_at"],
    )

    op.create_table(
        "fraud_alert_followup_tasks",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("case_key", sa.Text(), nullable=False),
        sa.Column("task_type", sa.Text(), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("task_status", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_by", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_key", "task_type", name="uq_fraud_alert_followup_tasks_case_type"),
    )
    op.create_index(
        "idx_fraud_alert_followup_tasks_case_status",
        "fraud_alert_followup_tasks",
        ["case_key", "task_status"],
    )


def downgrade() -> None:
    op.drop_index("idx_fraud_alert_followup_tasks_case_status", table_name="fraud_alert_followup_tasks")
    op.drop_table("fraud_alert_followup_tasks")
    op.drop_index("idx_fraud_alert_case_assignments_user_updated", table_name="fraud_alert_case_assignments")
    op.drop_table("fraud_alert_case_assignments")
