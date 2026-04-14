from __future__ import annotations

import uuid
from datetime import date, timedelta

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..db import Base
from .base import RepositoryBase


class SuspiciousFindingsWriteRepository(RepositoryBase):
    FOLLOW_UP_TASK_DEFINITIONS = (
        ("payout_hold", "支払保留を実施"),
        ("partner_notice", "関係者へ通知"),
        ("evidence_preservation", "証跡を保全"),
    )
    FOLLOW_UP_TASK_DUE_HOURS = {
        "payout_hold": 1,
        "partner_notice": 4,
        "evidence_preservation": 24,
    }

    def _sequence_placeholders(self, prefix: str, values: list[str]) -> tuple[str, dict[str, object]]:
        placeholders: list[str] = []
        params: dict[str, object] = {}
        for idx, value in enumerate(values):
            key = f"{prefix}{idx}"
            placeholders.append(f":{key}")
            params[key] = value
        return ", ".join(placeholders), params

    def apply_alert_reviews(
        self,
        finding_keys: list[str],
        *,
        status: str,
        updated_at,
        reason: str = "No reason provided",
        reviewed_by: str = "system",
        source_surface: str = "console",
        request_id: str = "system-request",
    ) -> int:
        if not finding_keys:
            return 0
        if not self._table_exists("fraud_alert_review_states"):
            statement = sa.text(
                """
                INSERT INTO fraud_alert_reviews (finding_key, review_status, updated_at)
                VALUES (:finding_key, :review_status, :updated_at)
                ON CONFLICT (finding_key)
                DO UPDATE SET
                    review_status = excluded.review_status,
                    updated_at = excluded.updated_at
                """
            )
            with self._connect() as conn:
                conn.execute(
                    statement,
                    [
                        {
                            "finding_key": finding_key,
                            "review_status": status,
                            "updated_at": updated_at,
                        }
                        for finding_key in finding_keys
                    ],
                )
            return len(finding_keys)

        keys = sorted({value for value in finding_keys if value})
        placeholders, params = self._sequence_placeholders("review_key_", keys)
        case_key_sql = "COALESCE(case_key, finding_key)" if self._column_exists("suspicious_conversion_findings", "case_key") else "finding_key"
        with self._connect() as conn:
            matched_rows = conn.execute(
                sa.text(
                    f"""
                    SELECT DISTINCT
                        {case_key_sql} AS case_key,
                        finding_key
                    FROM suspicious_conversion_findings
                    WHERE is_current = TRUE
                      AND (
                        finding_key IN ({placeholders})
                        OR {case_key_sql} IN ({placeholders})
                      )
                    """
                ),
                params,
            ).mappings().all()

            state_statement = sa.text(
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
                ON CONFLICT (case_key)
                DO UPDATE SET
                    review_status = excluded.review_status,
                    reason = excluded.reason,
                    reviewed_by = excluded.reviewed_by,
                    source_surface = excluded.source_surface,
                    request_id = excluded.request_id,
                    finding_key_at_review = excluded.finding_key_at_review,
                    reviewed_at = excluded.reviewed_at,
                    updated_at = excluded.updated_at
                """
            )
            event_statement = sa.text(
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
            )
            payload_rows = [
                {
                    "id": f"fraud-review-event-{uuid.uuid4().hex[:12]}",
                    "case_key": row["case_key"],
                    "review_status": status,
                    "reason": reason,
                    "reviewed_by": reviewed_by,
                    "source_surface": source_surface,
                    "request_id": request_id,
                    "finding_key_at_review": row["finding_key"],
                    "reviewed_at": updated_at,
                    "updated_at": updated_at,
                }
                for row in matched_rows
                if row.get("case_key")
            ]
            if payload_rows:
                conn.execute(state_statement, payload_rows)
                conn.execute(event_statement, payload_rows)
                self._sync_followup_tasks(
                    conn,
                    payload_rows,
                    status=status,
                    created_by=reviewed_by,
                    created_at=updated_at,
                )
        return len(payload_rows)

    def assign_alert_cases(
        self,
        case_keys: list[str],
        *,
        assignee_user_id: str | None,
        assigned_by: str,
        assigned_at,
    ) -> int:
        keys = sorted({value for value in case_keys if value})
        if not keys or not self._table_exists("fraud_alert_case_assignments"):
            return 0

        placeholders, params = self._sequence_placeholders("assign_key_", keys)
        with self._connect() as conn:
            matched_rows = conn.execute(
                sa.text(
                    f"""
                    SELECT DISTINCT COALESCE(case_key, finding_key) AS case_key
                    FROM suspicious_conversion_findings
                    WHERE is_current = TRUE
                      AND (
                        finding_key IN ({placeholders})
                        OR COALESCE(case_key, finding_key) IN ({placeholders})
                      )
                    """
                ),
                params,
            ).mappings().all()
            resolved_case_keys = [str(row["case_key"]) for row in matched_rows if row.get("case_key")]
            if not resolved_case_keys:
                return 0

            if not assignee_user_id:
                delete_placeholders, delete_params = self._sequence_placeholders("case_key_", resolved_case_keys)
                conn.execute(
                    sa.text(
                        f"""
                        DELETE FROM fraud_alert_case_assignments
                        WHERE case_key IN ({delete_placeholders})
                        """
                    ),
                    delete_params,
                )
                return len(resolved_case_keys)

            statement = sa.text(
                """
                INSERT INTO fraud_alert_case_assignments (
                    case_key,
                    assignee_user_id,
                    assigned_by,
                    assigned_at,
                    updated_at
                ) VALUES (
                    :case_key,
                    :assignee_user_id,
                    :assigned_by,
                    :assigned_at,
                    :updated_at
                )
                ON CONFLICT (case_key)
                DO UPDATE SET
                    assignee_user_id = excluded.assignee_user_id,
                    assigned_by = excluded.assigned_by,
                    assigned_at = excluded.assigned_at,
                    updated_at = excluded.updated_at
                """
            )
            conn.execute(
                statement,
                [
                    {
                        "case_key": case_key,
                        "assignee_user_id": assignee_user_id,
                        "assigned_by": assigned_by,
                        "assigned_at": assigned_at,
                        "updated_at": assigned_at,
                    }
                    for case_key in resolved_case_keys
                ],
            )
            return len(resolved_case_keys)

    def update_followup_task_status(
        self,
        task_id: str,
        *,
        status: str,
        updated_by: str,
        updated_at,
    ) -> dict[str, object] | None:
        if not task_id or not self._table_exists("fraud_alert_followup_tasks"):
            return None

        completed_by = updated_by if status == "completed" else None
        completed_at = updated_at if status == "completed" else None
        with self._connect() as conn:
            row = conn.execute(
                sa.text(
                    """
                    UPDATE fraud_alert_followup_tasks
                    SET task_status = :task_status,
                        completed_by = :completed_by,
                        completed_at = :completed_at
                    WHERE id = :task_id
                    RETURNING
                        id,
                        case_key,
                        task_type,
                        label,
                        task_status,
                        created_by,
                        created_at,
                        due_at,
                        completed_by,
                        completed_at
                    """
                ),
                {
                    "task_id": task_id,
                    "task_status": status,
                    "completed_by": completed_by,
                    "completed_at": completed_at,
                },
            ).mappings().first()
        return dict(row) if row else None

    def replace_conversion_findings(
        self,
        target_date: date,
        rows: list[dict],
        *,
        generation_metadata: dict,
    ) -> None:
        table = Base.metadata.tables["suspicious_conversion_findings"]
        with self._connect() as conn:
            conn.execute(
                sa.text(
                    """
                    UPDATE suspicious_conversion_findings
                    SET is_current = FALSE
                    WHERE date = :target_date
                      AND is_current = TRUE
                    """
                ),
                {"target_date": target_date},
            )
            self._replace_current_generation(conn, generation_metadata)
            if not rows:
                return
            stmt = pg_insert(table).on_conflict_do_update(
                index_elements=["finding_key"],
                set_={
                    "case_key": sa.text("excluded.case_key"),
                    "date": sa.text("excluded.date"),
                    "ipaddress": sa.text("excluded.ipaddress"),
                    "useragent": sa.text("excluded.useragent"),
                    "ua_hash": sa.text("excluded.ua_hash"),
                    "media_ids_json": sa.text("excluded.media_ids_json"),
                    "program_ids_json": sa.text("excluded.program_ids_json"),
                    "media_names_json": sa.text("excluded.media_names_json"),
                    "program_names_json": sa.text("excluded.program_names_json"),
                    "affiliate_ids_json": sa.text("excluded.affiliate_ids_json"),
                    "affiliate_names_json": sa.text("excluded.affiliate_names_json"),
                    "risk_level": sa.text("excluded.risk_level"),
                    "risk_score": sa.text("excluded.risk_score"),
                    "reasons_json": sa.text("excluded.reasons_json"),
                    "reasons_formatted_json": sa.text("excluded.reasons_formatted_json"),
                    "metrics_json": sa.text("excluded.metrics_json"),
                    "total_conversions": sa.text("excluded.total_conversions"),
                    "media_count": sa.text("excluded.media_count"),
                    "program_count": sa.text("excluded.program_count"),
                    "min_click_to_conv_seconds": sa.text("excluded.min_click_to_conv_seconds"),
                    "max_click_to_conv_seconds": sa.text("excluded.max_click_to_conv_seconds"),
                    "first_time": sa.text("excluded.first_time"),
                    "last_time": sa.text("excluded.last_time"),
                    "rule_version": sa.text("excluded.rule_version"),
                    "computed_at": sa.text("excluded.computed_at"),
                    "computed_by_job_id": sa.text("excluded.computed_by_job_id"),
                    "settings_updated_at_snapshot": sa.text("excluded.settings_updated_at_snapshot"),
                    "source_click_watermark": sa.text("excluded.source_click_watermark"),
                    "source_conversion_watermark": sa.text("excluded.source_conversion_watermark"),
                    "estimated_damage_yen": sa.text("excluded.estimated_damage_yen"),
                    "damage_unit_price_source": sa.text("excluded.damage_unit_price_source"),
                    "damage_evidence_json": sa.text("excluded.damage_evidence_json"),
                    "generation_id": sa.text("excluded.generation_id"),
                    "is_current": sa.text("excluded.is_current"),
                    "search_text": sa.text("excluded.search_text"),
                },
            )
            conn.execute(stmt, rows)

    def _replace_current_generation(self, conn, generation_metadata: dict) -> None:
        conn.execute(
            sa.text(
                """
                UPDATE findings_generations
                SET is_current = FALSE
                WHERE finding_type = :finding_type
                  AND target_date = :target_date
                  AND is_current = TRUE
                """
            ),
            {
                "finding_type": generation_metadata["finding_type"],
                "target_date": generation_metadata["target_date"],
            },
        )

        conn.execute(
            sa.text(
                """
                INSERT INTO findings_generations (
                    id,
                    generation_id,
                    finding_type,
                    target_date,
                    computed_by_job_id,
                    settings_version_id,
                    settings_fingerprint,
                    detector_code_version,
                    source_click_watermark,
                    source_conversion_watermark,
                    row_count,
                    is_current,
                    created_at
                ) VALUES (
                    :id,
                    :generation_id,
                    :finding_type,
                    :target_date,
                    :computed_by_job_id,
                    :settings_version_id,
                    :settings_fingerprint,
                    :detector_code_version,
                    :source_click_watermark,
                    :source_conversion_watermark,
                    :row_count,
                    TRUE,
                    :created_at
                )
                """
            ),
            {
                "id": f"fg-{uuid.uuid4().hex[:12]}",
                **generation_metadata,
            },
        )

    def _sync_followup_tasks(
        self,
        conn,
        review_rows: list[dict[str, object]],
        *,
        status: str,
        created_by: str,
        created_at,
    ) -> None:
        if not self._table_exists("fraud_alert_followup_tasks"):
            return

        case_keys = [str(row["case_key"]) for row in review_rows if row.get("case_key")]
        if not case_keys:
            return

        if status == "confirmed_fraud":
            statement = sa.text(
                """
                INSERT INTO fraud_alert_followup_tasks (
                    id,
                    case_key,
                    task_type,
                    label,
                    task_status,
                    created_by,
                    created_at,
                    due_at,
                    completed_by,
                    completed_at
                ) VALUES (
                    :id,
                    :case_key,
                    :task_type,
                    :label,
                    'open',
                    :created_by,
                    :created_at,
                    :due_at,
                    NULL,
                    NULL
                )
                ON CONFLICT (case_key, task_type)
                DO UPDATE SET
                    label = excluded.label,
                    due_at = excluded.due_at,
                    task_status = CASE
                        WHEN fraud_alert_followup_tasks.task_status = 'completed' THEN fraud_alert_followup_tasks.task_status
                        ELSE 'open'
                    END
                """
            )
            conn.execute(
                statement,
                [
                    {
                        "id": f"followup-{uuid.uuid4().hex[:12]}",
                        "case_key": case_key,
                        "task_type": task_type,
                        "label": label,
                        "created_by": created_by,
                        "created_at": created_at,
                        "due_at": created_at + timedelta(hours=self.FOLLOW_UP_TASK_DUE_HOURS.get(task_type, 24)),
                    }
                    for case_key in case_keys
                    for task_type, label in self.FOLLOW_UP_TASK_DEFINITIONS
                ],
            )
            return

        if status in {"white", "unhandled"}:
            placeholders, params = self._sequence_placeholders("followup_case_", case_keys)
            conn.execute(
                sa.text(
                    f"""
                    UPDATE fraud_alert_followup_tasks
                    SET task_status = CASE
                        WHEN task_status = 'completed' THEN task_status
                        ELSE 'cancelled'
                    END
                    WHERE case_key IN ({placeholders})
                    """
                ),
                params,
            )
