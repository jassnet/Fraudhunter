from __future__ import annotations

import uuid
from datetime import date

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..db import Base
from .base import RepositoryBase


class SuspiciousFindingsWriteRepository(RepositoryBase):
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
                    "date": sa.text("excluded.date"),
                    "ipaddress": sa.text("excluded.ipaddress"),
                    "useragent": sa.text("excluded.useragent"),
                    "ua_hash": sa.text("excluded.ua_hash"),
                    "media_ids_json": sa.text("excluded.media_ids_json"),
                    "program_ids_json": sa.text("excluded.program_ids_json"),
                    "media_names_json": sa.text("excluded.media_names_json"),
                    "program_names_json": sa.text("excluded.program_names_json"),
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
