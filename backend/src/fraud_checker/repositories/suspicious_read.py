from __future__ import annotations

import json
from datetime import date

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..db import Base
from .base import RepositoryBase


class SuspiciousReadRepository(RepositoryBase):
    def get_suspicious_click_details_bulk(
        self, target_date: date, ip_ua_pairs: list[tuple[str, str]]
    ) -> dict[tuple[str, str], list[dict]]:
        if not ip_ua_pairs:
            return {}

        results: dict[tuple[str, str], list[dict]] = {}
        chunk_size = 400

        with self._connect() as conn:
            for i in range(0, len(ip_ua_pairs), chunk_size):
                chunk = ip_ua_pairs[i : i + chunk_size]
                placeholders = ",".join([f"(:ip{idx}, :ua{idx})" for idx in range(len(chunk))])
                params: dict[str, object] = {"target_date": target_date}
                for idx, (ip, ua) in enumerate(chunk):
                    params[f"ip{idx}"] = ip
                    params[f"ua{idx}"] = ua

                query = f"""
                    SELECT
                        c.ipaddress,
                        c.useragent,
                        c.media_id,
                        c.program_id,
                        SUM(c.click_count) as click_count,
                        m.name as media_name,
                        p.name as program_name,
                        u.name as affiliate_name
                    FROM click_ipua_daily c
                    LEFT JOIN master_media m ON c.media_id = m.id
                    LEFT JOIN master_promotion p ON c.program_id = p.id
                    LEFT JOIN master_user u ON m.user_id = u.id
                    WHERE c.date = :target_date AND (c.ipaddress, c.useragent) IN ({placeholders})
                    GROUP BY c.ipaddress, c.useragent, c.media_id, c.program_id, m.name, p.name, u.name
                    ORDER BY click_count DESC
                """

                rows = conn.execute(sa.text(query), params).fetchall()
                for row in rows:
                    key = (row[0], row[1])
                    results.setdefault(key, []).append(
                        {
                            "media_id": row[2],
                            "program_id": row[3],
                            "click_count": row[4],
                            "media_name": row[5] or row[2],
                            "program_name": row[6] or row[3],
                            "affiliate_name": row[7] or None,
                        }
                    )
        return results

    def get_suspicious_conversion_details_bulk(
        self, target_date: date, ip_ua_pairs: list[tuple[str, str]]
    ) -> dict[tuple[str, str], list[dict]]:
        if not ip_ua_pairs:
            return {}

        results: dict[tuple[str, str], list[dict]] = {}
        chunk_size = 400

        with self._connect() as conn:
            for i in range(0, len(ip_ua_pairs), chunk_size):
                chunk = ip_ua_pairs[i : i + chunk_size]
                placeholders = ",".join([f"(:ip{idx}, :ua{idx})" for idx in range(len(chunk))])
                params: dict[str, object] = {"target_date": target_date}
                for idx, (ip, ua) in enumerate(chunk):
                    params[f"ip{idx}"] = ip
                    params[f"ua{idx}"] = ua

                query = f"""
                    SELECT
                        c.ipaddress,
                        c.useragent,
                        c.media_id,
                        c.program_id,
                        SUM(c.conversion_count) as conversion_count,
                        m.name as media_name,
                        p.name as program_name,
                        u.name as affiliate_name
                    FROM conversion_ipua_daily c
                    LEFT JOIN master_media m ON c.media_id = m.id
                    LEFT JOIN master_promotion p ON c.program_id = p.id
                    LEFT JOIN master_user u ON m.user_id = u.id
                    WHERE c.date = :target_date AND (c.ipaddress, c.useragent) IN ({placeholders})
                    GROUP BY c.ipaddress, c.useragent, c.media_id, c.program_id, m.name, p.name, u.name
                    ORDER BY conversion_count DESC
                """

                rows = conn.execute(sa.text(query), params).fetchall()
                for row in rows:
                    key = (row[0], row[1])
                    results.setdefault(key, []).append(
                        {
                            "media_id": row[2],
                            "program_id": row[3],
                            "conversion_count": row[4],
                            "media_name": row[5] or row[2],
                            "program_name": row[6] or row[3],
                            "affiliate_name": row[7] or None,
                        }
                    )
        return results

    def replace_click_findings(self, target_date: date, rows: list[dict]) -> None:
        self._replace_findings("suspicious_click_findings", target_date, rows)

    def replace_conversion_findings(self, target_date: date, rows: list[dict]) -> None:
        self._replace_findings("suspicious_conversion_findings", target_date, rows)

    def _replace_findings(self, table_name: str, target_date: date, rows: list[dict]) -> None:
        table = Base.metadata.tables[table_name]
        with self._connect() as conn:
            conn.execute(
                sa.text(
                    f"""
                    UPDATE {table_name}
                    SET is_current = FALSE
                    WHERE date = :target_date
                      AND is_current = TRUE
                    """
                ),
                {"target_date": target_date},
            )
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
                    "rule_version": sa.text("excluded.rule_version"),
                    "computed_at": sa.text("excluded.computed_at"),
                    "computed_by_job_id": sa.text("excluded.computed_by_job_id"),
                    "settings_updated_at_snapshot": sa.text("excluded.settings_updated_at_snapshot"),
                    "source_click_watermark": sa.text("excluded.source_click_watermark"),
                    "source_conversion_watermark": sa.text("excluded.source_conversion_watermark"),
                    "generation_id": sa.text("excluded.generation_id"),
                    "is_current": sa.text("excluded.is_current"),
                    "search_text": sa.text("excluded.search_text"),
                    "first_time": sa.text("excluded.first_time"),
                    "last_time": sa.text("excluded.last_time"),
                    "media_count": sa.text("excluded.media_count"),
                    "program_count": sa.text("excluded.program_count"),
                    **(
                        {"total_clicks": sa.text("excluded.total_clicks")}
                        if "total_clicks" in table.c
                        else {"total_conversions": sa.text("excluded.total_conversions")}
                    ),
                    **(
                        {
                            "min_click_to_conv_seconds": sa.text("excluded.min_click_to_conv_seconds"),
                            "max_click_to_conv_seconds": sa.text("excluded.max_click_to_conv_seconds"),
                        }
                        if "min_click_to_conv_seconds" in table.c
                        else {}
                    ),
                },
            )
            conn.execute(stmt, rows)

    def list_click_findings(
        self,
        *,
        target_date: date,
        limit: int,
        offset: int,
        search: str | None,
        risk_level: str | None,
        sort_by: str,
        sort_order: str,
    ) -> tuple[list[dict], int]:
        return self._list_findings(
            table_name="suspicious_click_findings",
            target_date=target_date,
            limit=limit,
            offset=offset,
            search=search,
            risk_level=risk_level,
            sort_by=sort_by,
            sort_order=sort_order,
            metric_column="total_clicks",
        )

    def list_conversion_findings(
        self,
        *,
        target_date: date,
        limit: int,
        offset: int,
        search: str | None,
        risk_level: str | None,
        sort_by: str,
        sort_order: str,
    ) -> tuple[list[dict], int]:
        return self._list_findings(
            table_name="suspicious_conversion_findings",
            target_date=target_date,
            limit=limit,
            offset=offset,
            search=search,
            risk_level=risk_level,
            sort_by=sort_by,
            sort_order=sort_order,
            metric_column="total_conversions",
        )

    def _list_findings(
        self,
        *,
        table_name: str,
        target_date: date,
        limit: int,
        offset: int,
        search: str | None,
        risk_level: str | None,
        sort_by: str,
        sort_order: str,
        metric_column: str,
    ) -> tuple[list[dict], int]:
        allowed_sort = {"count": metric_column, "risk": "risk_score", "latest": "last_time"}
        sort_column = allowed_sort.get(sort_by, metric_column)
        direction = "ASC" if sort_order.lower() == "asc" else "DESC"
        conditions = ["date = :target_date", "is_current = TRUE"]
        params: dict[str, object] = {"target_date": target_date, "limit": limit, "offset": offset}
        if risk_level:
            conditions.append("risk_level = :risk_level")
            params["risk_level"] = risk_level
        if search:
            conditions.append("search_text LIKE :search")
            params["search"] = f"%{search.lower()}%"
        where_sql = " AND ".join(conditions)

        rows = self.fetch_all(
            f"""
            SELECT *
            FROM {table_name}
            WHERE {where_sql}
            ORDER BY {sort_column} {direction}, finding_key ASC
            LIMIT :limit OFFSET :offset
            """,
            params,
        )
        total_row = self.fetch_one(
            f"SELECT COUNT(*) AS cnt FROM {table_name} WHERE {where_sql}",
            {key: value for key, value in params.items() if key not in {"limit", "offset"}},
        )
        return [self._deserialize_finding_row(row) for row in rows], int(total_row["cnt"] if total_row else 0)

    def get_click_finding_by_key(self, finding_key: str) -> dict | None:
        row = self.fetch_one(
            "SELECT * FROM suspicious_click_findings WHERE finding_key = :finding_key AND is_current = TRUE",
            {"finding_key": finding_key},
        )
        return self._deserialize_finding_row(row) if row else None

    def get_conversion_finding_by_key(self, finding_key: str) -> dict | None:
        row = self.fetch_one(
            "SELECT * FROM suspicious_conversion_findings WHERE finding_key = :finding_key AND is_current = TRUE",
            {"finding_key": finding_key},
        )
        return self._deserialize_finding_row(row) if row else None

    def get_daily_finding_counts(self, limit: int) -> dict[str, dict[str, int]]:
        click_rows = self.fetch_all(
            """
            SELECT date, COUNT(*) AS suspicious_clicks
            FROM suspicious_click_findings
            WHERE is_current = TRUE
            GROUP BY date
            ORDER BY date DESC
            LIMIT :limit
            """,
            {"limit": limit},
        )
        conversion_rows = self.fetch_all(
            """
            SELECT date, COUNT(*) AS suspicious_conversions
            FROM suspicious_conversion_findings
            WHERE is_current = TRUE
            GROUP BY date
            ORDER BY date DESC
            LIMIT :limit
            """,
            {"limit": limit},
        )
        merged: dict[str, dict[str, int]] = {}
        for row in click_rows:
            row_date = row["date"].isoformat() if isinstance(row["date"], date) else row["date"]
            merged.setdefault(row_date, {})["suspicious_clicks"] = int(row["suspicious_clicks"] or 0)
        for row in conversion_rows:
            row_date = row["date"].isoformat() if isinstance(row["date"], date) else row["date"]
            merged.setdefault(row_date, {})["suspicious_conversions"] = int(row["suspicious_conversions"] or 0)
        return merged

    def count_current_click_findings(self, target_date: date) -> int:
        row = self.fetch_one(
            """
            SELECT COUNT(*) AS cnt
            FROM suspicious_click_findings
            WHERE date = :target_date
              AND is_current = TRUE
            """,
            {"target_date": target_date},
        )
        return int(row["cnt"] if row else 0)

    def count_current_conversion_findings(self, target_date: date) -> int:
        row = self.fetch_one(
            """
            SELECT COUNT(*) AS cnt
            FROM suspicious_conversion_findings
            WHERE date = :target_date
              AND is_current = TRUE
            """,
            {"target_date": target_date},
        )
        return int(row["cnt"] if row else 0)

    def _deserialize_finding_row(self, row: dict) -> dict:
        parsed = dict(row)
        for key in (
            "media_ids_json",
            "program_ids_json",
            "media_names_json",
            "program_names_json",
            "affiliate_names_json",
            "reasons_json",
            "reasons_formatted_json",
            "metrics_json",
        ):
            if key in parsed and parsed[key] is not None:
                parsed[key] = json.loads(parsed[key])
        return parsed
