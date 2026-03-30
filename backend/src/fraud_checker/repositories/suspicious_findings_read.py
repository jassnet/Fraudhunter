from __future__ import annotations

import json
from datetime import date

import sqlalchemy as sa

from .base import RepositoryBase


class SuspiciousFindingsReadRepository(RepositoryBase):
    def _generation_join_sql(self, table_alias: str, finding_type: str) -> str:
        if not self._table_exists("findings_generations"):
            return ""
        return f"""
            JOIN findings_generations fg
              ON fg.generation_id = {table_alias}.generation_id
             AND fg.target_date = {table_alias}.date
             AND fg.finding_type = '{finding_type}'
             AND fg.is_current = TRUE
        """

    def get_suspicious_click_details_bulk(
        self, target_date: date, ip_ua_pairs: list[tuple[str, str]]
    ) -> dict[tuple[str, str], list[dict]]:
        return self._get_detail_rows(
            table_name="click_ipua_daily",
            metric_column="click_count",
            target_date=target_date,
            ip_ua_pairs=ip_ua_pairs,
        )

    def get_suspicious_conversion_details_bulk(
        self, target_date: date, ip_ua_pairs: list[tuple[str, str]]
    ) -> dict[tuple[str, str], list[dict]]:
        return self._get_detail_rows(
            table_name="conversion_ipua_daily",
            metric_column="conversion_count",
            target_date=target_date,
            ip_ua_pairs=ip_ua_pairs,
        )

    def _get_detail_rows(
        self,
        *,
        table_name: str,
        metric_column: str,
        target_date: date,
        ip_ua_pairs: list[tuple[str, str]],
    ) -> dict[tuple[str, str], list[dict]]:
        if not ip_ua_pairs:
            return {}

        results: dict[tuple[str, str], list[dict]] = {}
        chunk_size = 400
        with self._connect() as conn:
            for index in range(0, len(ip_ua_pairs), chunk_size):
                chunk = ip_ua_pairs[index : index + chunk_size]
                placeholders = ",".join(f"(:ip{idx}, :ua{idx})" for idx in range(len(chunk)))
                params: dict[str, object] = {"target_date": target_date}
                for idx, (ipaddress, useragent) in enumerate(chunk):
                    params[f"ip{idx}"] = ipaddress
                    params[f"ua{idx}"] = useragent

                rows = conn.execute(
                    sa.text(
                        f"""
                        SELECT
                            c.ipaddress,
                            c.useragent,
                            c.media_id,
                            c.program_id,
                            SUM(c.{metric_column}) AS metric_value,
                            m.name AS media_name,
                            p.name AS program_name,
                            u.name AS affiliate_name
                        FROM {table_name} c
                        LEFT JOIN master_media m ON c.media_id = m.id
                        LEFT JOIN master_promotion p ON c.program_id = p.id
                        LEFT JOIN master_user u ON m.user_id = u.id
                        WHERE c.date = :target_date
                          AND (c.ipaddress, c.useragent) IN ({placeholders})
                        GROUP BY c.ipaddress, c.useragent, c.media_id, c.program_id, m.name, p.name, u.name
                        ORDER BY metric_value DESC
                        """
                    ),
                    params,
                ).fetchall()
                for row in rows:
                    key = (row[0], row[1])
                    results.setdefault(key, []).append(
                        {
                            "media_id": row[2],
                            "program_id": row[3],
                            metric_column: row[4],
                            "media_name": row[5] or row[2],
                            "program_name": row[6] or row[3],
                            "affiliate_name": row[7] or None,
                        }
                    )
        return results

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
        sort_column = f"f.{allowed_sort.get(sort_by, metric_column)}"
        direction = "ASC" if sort_order.lower() == "asc" else "DESC"
        conditions = ["f.date = :target_date", "f.is_current = TRUE"]
        params: dict[str, object] = {"target_date": target_date, "limit": limit, "offset": offset}
        if risk_level:
            conditions.append("f.risk_level = :risk_level")
            params["risk_level"] = risk_level
        if search:
            conditions.append("f.search_text LIKE :search")
            params["search"] = f"%{search.lower()}%"
        where_sql = " AND ".join(conditions)
        finding_type = "click" if table_name == "suspicious_click_findings" else "conversion"

        rows = self.fetch_all(
            f"""
            SELECT f.*
            FROM {table_name} f
            {self._generation_join_sql('f', finding_type)}
            WHERE {where_sql}
            ORDER BY {sort_column} {direction}, f.finding_key ASC
            LIMIT :limit OFFSET :offset
            """,
            params,
        )
        total_row = self.fetch_one(
            f"""
            SELECT COUNT(*) AS cnt
            FROM {table_name} f
            {self._generation_join_sql('f', finding_type)}
            WHERE {where_sql}
            """,
            {key: value for key, value in params.items() if key not in {"limit", "offset"}},
        )
        return [self._deserialize_finding_row(row) for row in rows], int(total_row["cnt"] if total_row else 0)

    def get_click_finding_by_key(self, finding_key: str) -> dict | None:
        row = self.fetch_one(
            f"""
            SELECT f.*
            FROM suspicious_click_findings f
            {self._generation_join_sql('f', 'click')}
            WHERE finding_key = :finding_key
              AND f.is_current = TRUE
            """,
            {"finding_key": finding_key},
        )
        return self._deserialize_finding_row(row) if row else None

    def get_conversion_finding_by_key(self, finding_key: str) -> dict | None:
        row = self.fetch_one(
            f"""
            SELECT f.*
            FROM suspicious_conversion_findings f
            {self._generation_join_sql('f', 'conversion')}
            WHERE finding_key = :finding_key
              AND f.is_current = TRUE
            """,
            {"finding_key": finding_key},
        )
        return self._deserialize_finding_row(row) if row else None

    def get_daily_finding_counts(self, limit: int) -> dict[str, dict[str, int]]:
        if not self._table_exists("findings_generations"):
            return self._get_daily_finding_counts_legacy(limit)

        click_rows = self.fetch_all(
            """
            SELECT f.date, COUNT(*) AS suspicious_clicks
            FROM suspicious_click_findings f
            JOIN findings_generations fg
              ON fg.generation_id = f.generation_id
             AND fg.target_date = f.date
             AND fg.finding_type = 'click'
             AND fg.is_current = TRUE
            WHERE f.is_current = TRUE
            GROUP BY f.date
            ORDER BY f.date DESC
            LIMIT :limit
            """,
            {"limit": limit},
        )
        conversion_rows = self.fetch_all(
            """
            SELECT f.date, COUNT(*) AS suspicious_conversions
            FROM suspicious_conversion_findings f
            JOIN findings_generations fg
              ON fg.generation_id = f.generation_id
             AND fg.target_date = f.date
             AND fg.finding_type = 'conversion'
             AND fg.is_current = TRUE
            WHERE f.is_current = TRUE
            GROUP BY f.date
            ORDER BY f.date DESC
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
        if not self._table_exists("findings_generations"):
            return self._count_current_findings_legacy("suspicious_click_findings", target_date)
        row = self.fetch_one(
            """
            SELECT COUNT(*) AS cnt
            FROM suspicious_click_findings f
            JOIN findings_generations fg
              ON fg.generation_id = f.generation_id
             AND fg.target_date = f.date
             AND fg.finding_type = 'click'
             AND fg.is_current = TRUE
            WHERE f.date = :target_date
              AND f.is_current = TRUE
            """,
            {"target_date": target_date},
        )
        return int(row["cnt"] if row else 0)

    def count_current_conversion_findings(self, target_date: date) -> int:
        if not self._table_exists("findings_generations"):
            return self._count_current_findings_legacy("suspicious_conversion_findings", target_date)
        row = self.fetch_one(
            """
            SELECT COUNT(*) AS cnt
            FROM suspicious_conversion_findings f
            JOIN findings_generations fg
              ON fg.generation_id = f.generation_id
             AND fg.target_date = f.date
             AND fg.finding_type = 'conversion'
             AND fg.is_current = TRUE
            WHERE f.date = :target_date
              AND f.is_current = TRUE
            """,
            {"target_date": target_date},
        )
        return int(row["cnt"] if row else 0)

    def purge_findings_before(self, cutoff: date, *, execute: bool) -> dict[str, int]:
        counts: dict[str, int] = {}
        for table_name in ("suspicious_click_findings", "suspicious_conversion_findings"):
            if not self._table_exists(table_name):
                counts[table_name] = 0
                continue
            params = {"cutoff": cutoff}
            where_sql = "date < :cutoff"
            counts[table_name] = (
                self.delete_rows(table_name, where_sql, params)
                if execute
                else self.count_rows(table_name, where_sql, params)
            )
        return counts

    def _get_daily_finding_counts_legacy(self, limit: int) -> dict[str, dict[str, int]]:
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

    def _count_current_findings_legacy(self, table_name: str, target_date: date) -> int:
        row = self.fetch_one(
            f"""
            SELECT COUNT(*) AS cnt
            FROM {table_name}
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
