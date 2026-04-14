"""add case keys and review history tables

Revision ID: 0014_case_key_review_hist
Revises: 0013_add_damage_snapshot
Create Date: 2026-04-09
"""

from __future__ import annotations

import hashlib
import uuid

from alembic import op
import sqlalchemy as sa


revision = "0014_case_key_review_hist"
down_revision = "0013_add_damage_snapshot"
branch_labels = None
depends_on = None


def _case_key(target_date, ipaddress: str, useragent: str) -> str:
    payload = f"conversion_case|{target_date}|{ipaddress}|{useragent}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def upgrade() -> None:
    op.add_column(
        "suspicious_conversion_findings",
        sa.Column("case_key", sa.Text(), nullable=True),
    )
    op.create_index(
        "idx_scof_case_current",
        "suspicious_conversion_findings",
        ["case_key", "is_current"],
    )

    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            """
            SELECT finding_key, date, ipaddress, useragent
            FROM suspicious_conversion_findings
            """
        )
    ).mappings()
    for row in rows:
        bind.execute(
            sa.text(
                """
                UPDATE suspicious_conversion_findings
                SET case_key = :case_key
                WHERE finding_key = :finding_key
                """
            ),
            {
                "finding_key": row["finding_key"],
                "case_key": _case_key(row["date"], row["ipaddress"], row["useragent"]),
            },
        )

    op.create_table(
        "fraud_alert_review_states",
        sa.Column("case_key", sa.Text(), nullable=False),
        sa.Column("review_status", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("reviewed_by", sa.Text(), nullable=False),
        sa.Column("source_surface", sa.Text(), nullable=False),
        sa.Column("request_id", sa.Text(), nullable=False),
        sa.Column("finding_key_at_review", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("case_key"),
    )
    op.create_index(
        "idx_fraud_alert_review_states_status_updated",
        "fraud_alert_review_states",
        ["review_status", "updated_at"],
    )

    op.create_table(
        "fraud_alert_review_events",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("case_key", sa.Text(), nullable=False),
        sa.Column("finding_key_at_review", sa.Text(), nullable=True),
        sa.Column("review_status", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("reviewed_by", sa.Text(), nullable=False),
        sa.Column("source_surface", sa.Text(), nullable=False),
        sa.Column("request_id", sa.Text(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_fraud_alert_review_events_case_reviewed",
        "fraud_alert_review_events",
        ["case_key", "reviewed_at"],
    )

    legacy_rows = bind.execute(
        sa.text(
            """
            SELECT
                r.finding_key,
                r.review_status,
                r.updated_at,
                f.case_key
            FROM fraud_alert_reviews r
            JOIN suspicious_conversion_findings f
              ON f.finding_key = r.finding_key
            """
        )
    ).mappings()
    for row in legacy_rows:
        bind.execute(
            sa.text(
                """
                INSERT INTO fraud_alert_review_states (
                    case_key,
                    review_status,
                    reason,
                    reviewed_by,
                    source_surface,
                    request_id,
                    finding_key_at_review,
                    reviewed_at,
                    updated_at
                ) VALUES (
                    :case_key,
                    :review_status,
                    :reason,
                    :reviewed_by,
                    :source_surface,
                    :request_id,
                    :finding_key_at_review,
                    :reviewed_at,
                    :updated_at
                )
                ON CONFLICT (case_key) DO UPDATE SET
                    review_status = excluded.review_status,
                    reason = excluded.reason,
                    reviewed_by = excluded.reviewed_by,
                    source_surface = excluded.source_surface,
                    request_id = excluded.request_id,
                    finding_key_at_review = excluded.finding_key_at_review,
                    reviewed_at = excluded.reviewed_at,
                    updated_at = excluded.updated_at
                """
            ),
            {
                "case_key": row["case_key"],
                "review_status": row["review_status"],
                "reason": "Migrated from legacy fraud_alert_reviews",
                "reviewed_by": "migration",
                "source_surface": "migration_0014",
                "request_id": "migration-0014",
                "finding_key_at_review": row["finding_key"],
                "reviewed_at": row["updated_at"],
                "updated_at": row["updated_at"],
            },
        )
        bind.execute(
            sa.text(
                """
                INSERT INTO fraud_alert_review_events (
                    id,
                    case_key,
                    finding_key_at_review,
                    review_status,
                    reason,
                    reviewed_by,
                    source_surface,
                    request_id,
                    reviewed_at
                ) VALUES (
                    :id,
                    :case_key,
                    :finding_key_at_review,
                    :review_status,
                    :reason,
                    :reviewed_by,
                    :source_surface,
                    :request_id,
                    :reviewed_at
                )
                """
            ),
            {
                "id": f"fraud-review-event-{uuid.uuid4().hex[:12]}",
                "case_key": row["case_key"],
                "finding_key_at_review": row["finding_key"],
                "review_status": row["review_status"],
                "reason": "Migrated from legacy fraud_alert_reviews",
                "reviewed_by": "migration",
                "source_surface": "migration_0014",
                "request_id": "migration-0014",
                "reviewed_at": row["updated_at"],
            },
        )


def downgrade() -> None:
    op.drop_index("idx_fraud_alert_review_events_case_reviewed", table_name="fraud_alert_review_events")
    op.drop_table("fraud_alert_review_events")
    op.drop_index("idx_fraud_alert_review_states_status_updated", table_name="fraud_alert_review_states")
    op.drop_table("fraud_alert_review_states")
    op.drop_index("idx_scof_case_current", table_name="suspicious_conversion_findings")
    op.drop_column("suspicious_conversion_findings", "case_key")
