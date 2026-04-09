from __future__ import annotations

import uuid
from datetime import date

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..db import Base
from .base import RepositoryBase


class SuspiciousFindingsWriteRepository(RepositoryBase):
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
        reviewed_role: str = "system",
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
                    reviewed_role,
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
                    :reviewed_role,
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
                    reviewed_role = excluded.reviewed_role,
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
                    reviewed_role,
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
                    :reviewed_role,
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
                    "reviewed_role": reviewed_role,
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
        return len(payload_rows)

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
