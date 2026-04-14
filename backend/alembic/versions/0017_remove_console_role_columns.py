"""remove console role columns

Revision ID: 0017_remove_console_roles
Revises: 0016_followup_due_at
Create Date: 2026-04-14
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0017_remove_console_roles"
down_revision = "0016_followup_due_at"
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    if _column_exists("fraud_alert_review_states", "reviewed_role"):
        with op.batch_alter_table("fraud_alert_review_states") as batch_op:
            batch_op.drop_column("reviewed_role")

    if _column_exists("fraud_alert_review_events", "reviewed_role"):
        with op.batch_alter_table("fraud_alert_review_events") as batch_op:
            batch_op.drop_column("reviewed_role")

    if _column_exists("fraud_alert_case_assignments", "assignee_role"):
        with op.batch_alter_table("fraud_alert_case_assignments") as batch_op:
            batch_op.drop_column("assignee_role")


def downgrade() -> None:
    with op.batch_alter_table("fraud_alert_review_states") as batch_op:
        batch_op.add_column(sa.Column("reviewed_role", sa.Text(), nullable=False, server_default="system"))

    with op.batch_alter_table("fraud_alert_review_events") as batch_op:
        batch_op.add_column(sa.Column("reviewed_role", sa.Text(), nullable=False, server_default="system"))

    with op.batch_alter_table("fraud_alert_case_assignments") as batch_op:
        batch_op.add_column(sa.Column("assignee_role", sa.Text(), nullable=False, server_default="system"))
