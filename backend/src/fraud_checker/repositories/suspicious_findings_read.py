from __future__ import annotations

import json
from datetime import date

import sqlalchemy as sa

from .base import RepositoryBase


class SuspiciousFindingsReadRepository(RepositoryBase):
    def _generation_join_sql(self) -> str:
        if not self._table_exists("findings_generations"):
            return ""
        return """
            JOIN findings_generations fg
              ON fg.generation_id = f.generation_id
             AND fg.target_date = f.date
             AND fg.finding_type = 'conversion'
             AND fg.is_current = TRUE
        """

    def get_suspicious_conversion_details_bulk(
        self,
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
                            SUM(c.conversion_count) AS metric_value,
                            m.name AS media_name,
                            p.name AS program_name,
                            m.user_id AS affiliate_id,
                            u.name AS affiliate_name
                        FROM conversion_ipua_daily c
                        LEFT JOIN master_media m ON c.media_id = m.id
                        LEFT JOIN master_promotion p ON c.program_id = p.id
                        LEFT JOIN master_user u ON m.user_id = u.id
                        WHERE c.date = :target_date
                          AND (c.ipaddress, c.useragent) IN ({placeholders})
                        GROUP BY c.ipaddress, c.useragent, c.media_id, c.program_id, m.name, p.name, m.user_id, u.name
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
                            "conversion_count": row[4],
                            "media_name": row[5] or row[2],
                            "program_name": row[6] or row[3],
                            "affiliate_id": row[7] or None,
                            "affiliate_name": row[8] or None,
                        }
                    )
        return results

    def get_program_unit_prices(self, target_date: date, program_ids: list[str]) -> dict[str, int]:
        if not program_ids or not self._table_exists("conversion_raw"):
            return {}

        unique_program_ids = [program_id for program_id in dict.fromkeys(program_ids) if program_id]
        if not unique_program_ids:
            return {}

        placeholders = ", ".join(f":program_id_{idx}" for idx in range(len(unique_program_ids)))
        params: dict[str, object] = {"target_date": target_date}
        params.update({f"program_id_{idx}": value for idx, value in enumerate(unique_program_ids)})
        rows = self.fetch_all(
            f"""
            SELECT
                program_id,
                raw_payload
            FROM conversion_raw
            WHERE CAST(conversion_time AS date) = :target_date
              AND program_id IN ({placeholders})
            """,
            params,
        )

        grouped_prices: dict[str, list[int]] = {}
        for row in rows:
            program_id = row.get("program_id")
            if not program_id:
                continue
            grouped_prices.setdefault(str(program_id), []).append(_reward_from_payload(row.get("raw_payload")))

        return {
            program_id: price
            for program_id, values in grouped_prices.items()
            if (price := _representative_unit_price(values)) is not None
        }

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
        allowed_sort = {
            "count": "total_conversions",
            "risk": "risk_score",
            "latest": "last_time",
        }
        sort_column = f"f.{allowed_sort.get(sort_by, 'total_conversions')}"
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

        rows = self.fetch_all(
            f"""
            SELECT f.*
            FROM suspicious_conversion_findings f
            {self._generation_join_sql()}
            WHERE {where_sql}
            ORDER BY {sort_column} {direction}, f.finding_key ASC
            LIMIT :limit OFFSET :offset
            """,
            params,
        )
        total_row = self.fetch_one(
            f"""
            SELECT COUNT(*) AS cnt
            FROM suspicious_conversion_findings f
            {self._generation_join_sql()}
            WHERE {where_sql}
            """,
            {key: value for key, value in params.items() if key not in {"limit", "offset"}},
        )
        return [self._deserialize_finding_row(row) for row in rows], int(total_row["cnt"] if total_row else 0)

    def get_conversion_finding_by_key(self, finding_key: str) -> dict | None:
        row = self.fetch_one(
            f"""
            SELECT f.*
            FROM suspicious_conversion_findings f
            {self._generation_join_sql()}
            WHERE finding_key = :finding_key
              AND f.is_current = TRUE
            """,
            {"finding_key": finding_key},
        )
        return self._deserialize_finding_row(row) if row else None

    def get_daily_finding_counts(
        self,
        limit: int,
        *,
        target_date: date | None = None,
    ) -> dict[str, dict[str, int]]:
        merged: dict[str, dict[str, int]] = {}

        params: dict[str, object] = {"limit": limit}
        where_parts = ["f.is_current = TRUE"]
        legacy_where_parts = ["is_current = TRUE"]
        if target_date is not None:
            params["target_date"] = target_date
            where_parts.append("f.date <= :target_date")
            legacy_where_parts.append("date <= :target_date")

        if self._table_exists("suspicious_conversion_findings"):
            if not self._table_exists("findings_generations"):
                merged.update(self._get_daily_finding_counts_legacy(" AND ".join(legacy_where_parts), params))
            else:
                rows = self.fetch_all(
                    f"""
                    SELECT f.date, COUNT(*) AS suspicious_conversions
                    FROM suspicious_conversion_findings f
                    JOIN findings_generations fg
                      ON fg.generation_id = f.generation_id
                     AND fg.target_date = f.date
                     AND fg.finding_type = 'conversion'
                     AND fg.is_current = TRUE
                    WHERE {" AND ".join(where_parts)}
                    GROUP BY f.date
                    ORDER BY f.date DESC
                    LIMIT :limit
                    """,
                    params,
                )
                for row in rows:
                    row_date = row["date"].isoformat() if isinstance(row["date"], date) else row["date"]
                    merged.setdefault(row_date, {})["suspicious_conversions"] = int(
                        row["suspicious_conversions"] or 0
                    )

        return merged

    def count_current_conversion_findings(self, target_date: date) -> int:
        if not self._table_exists("suspicious_conversion_findings"):
            return 0
        if not self._table_exists("findings_generations"):
            return self._count_current_findings_legacy(target_date)
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
        params = {"cutoff": cutoff}
        where_sql = "date < :cutoff"
        counts: dict[str, int] = {}
        for table_name in ("suspicious_conversion_findings",):
            if not self._table_exists(table_name):
                counts[table_name] = 0
                continue
            counts[table_name] = (
                self.delete_rows(table_name, where_sql, params)
                if execute
                else self.count_rows(table_name, where_sql, params)
            )
        return counts

    def _get_daily_finding_counts_legacy(
        self,
        where_sql: str,
        params: dict[str, object],
    ) -> dict[str, dict[str, int]]:
        rows = self.fetch_all(
            f"""
            SELECT date, COUNT(*) AS suspicious_conversions
            FROM suspicious_conversion_findings
            WHERE {where_sql}
            GROUP BY date
            ORDER BY date DESC
            LIMIT :limit
            """,
            params,
        )
        merged: dict[str, dict[str, int]] = {}
        for row in rows:
            row_date = row["date"].isoformat() if isinstance(row["date"], date) else row["date"]
            merged.setdefault(row_date, {})["suspicious_conversions"] = int(
                row["suspicious_conversions"] or 0
            )
        return merged

    def _count_current_findings_legacy(self, target_date: date) -> int:
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
            "affiliate_ids_json",
            "affiliate_names_json",
            "reasons_json",
            "reasons_formatted_json",
            "metrics_json",
            "damage_evidence_json",
        ):
            if key in parsed and parsed[key] is not None:
                parsed[key] = json.loads(parsed[key])
        return parsed


REWARD_KEYS = {
    "reward",
    "reward_amount",
    "commission",
    "commission_amount",
    "payout",
    "payout_amount",
    "amount",
    "price",
    "cv_price",
}
DEFAULT_REWARD_YEN = 3000


def _reward_from_payload(raw_payload) -> int:
    parsed = _parse_json(raw_payload)
    extracted = _extract_reward_value(parsed)
    if extracted is None:
        return DEFAULT_REWARD_YEN
    return extracted


def _extract_reward_value(value) -> int | None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key.lower() in REWARD_KEYS:
                parsed = _coerce_int(nested)
                if parsed is not None:
                    return parsed
            nested_value = _extract_reward_value(nested)
            if nested_value is not None:
                return nested_value
    if isinstance(value, list):
        for item in value:
            nested_value = _extract_reward_value(item)
            if nested_value is not None:
                return nested_value
    return None


def _coerce_int(value) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        stripped = value.replace(",", "").replace("¥", "").strip()
        if not stripped:
            return None
        try:
            return int(float(stripped))
        except ValueError:
            return None
    return None


def _parse_json(value):
    if value is None or isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _representative_unit_price(prices: list[int]) -> int | None:
    positive_prices = [price for price in prices if price > 0]
    if not positive_prices:
        return None
    counts: dict[int, int] = {}
    for price in positive_prices:
        counts[price] = counts.get(price, 0) + 1
    return max(counts.items(), key=lambda item: (item[1], item[0]))[0]
