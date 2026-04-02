from __future__ import annotations

import json
from datetime import date

from .base import RepositoryBase


class FraudFindingsReadRepository(RepositoryBase):
    def list_fraud_findings(
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
            "count": "primary_metric",
            "risk": "risk_score",
            "latest": "last_time",
        }
        sort_column = f"f.{allowed_sort.get(sort_by, 'primary_metric')}"
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
            FROM fraud_findings f
            WHERE {where_sql}
            ORDER BY {sort_column} {direction}, f.finding_key ASC
            LIMIT :limit OFFSET :offset
            """,
            params,
        )
        total_row = self.fetch_one(
            f"""
            SELECT COUNT(*) AS cnt
            FROM fraud_findings f
            WHERE {where_sql}
            """,
            {key: value for key, value in params.items() if key not in {"limit", "offset"}},
        )
        return [self._deserialize_finding_row(row) for row in rows], int(total_row["cnt"] if total_row else 0)

    def get_fraud_finding_by_key(self, finding_key: str) -> dict | None:
        row = self.fetch_one(
            """
            SELECT *
            FROM fraud_findings
            WHERE finding_key = :finding_key
              AND is_current = TRUE
            """,
            {"finding_key": finding_key},
        )
        return self._deserialize_finding_row(row) if row else None

    def count_current_fraud_findings(self, target_date: date) -> int:
        if not self._table_exists("fraud_findings"):
            return 0
        row = self.fetch_one(
            """
            SELECT COUNT(*) AS cnt
            FROM fraud_findings
            WHERE date = :target_date
              AND is_current = TRUE
            """,
            {"target_date": target_date},
        )
        return int(row["cnt"] if row else 0)

    def get_daily_fraud_finding_counts(
        self,
        limit: int,
        *,
        target_date: date | None = None,
    ) -> dict[str, int]:
        if not self._table_exists("fraud_findings"):
            return {}
        params: dict[str, object] = {"limit": limit}
        where_parts = ["is_current = TRUE"]
        if target_date is not None:
            params["target_date"] = target_date
            where_parts.append("date <= :target_date")
        rows = self.fetch_all(
            f"""
            SELECT date, COUNT(*) AS fraud_findings
            FROM fraud_findings
            WHERE {" AND ".join(where_parts)}
            GROUP BY date
            ORDER BY date DESC
            LIMIT :limit
            """,
            params,
        )
        return {
            (row["date"].isoformat() if isinstance(row["date"], date) else row["date"]): int(row["fraud_findings"] or 0)
            for row in rows
        }

    def purge_fraud_findings_before(self, cutoff: date, *, execute: bool) -> dict[str, int]:
        table_name = "fraud_findings"
        if not self._table_exists(table_name):
            return {table_name: 0}
        params = {"cutoff": cutoff}
        where_sql = "date < :cutoff"
        count = self.delete_rows(table_name, where_sql, params) if execute else self.count_rows(table_name, where_sql, params)
        return {table_name: count}

    def _deserialize_finding_row(self, row: dict) -> dict:
        parsed = dict(row)
        for key in ("reasons_json", "reasons_formatted_json", "metrics_json"):
            if key in parsed and parsed[key] is not None:
                parsed[key] = json.loads(parsed[key])
        return parsed
