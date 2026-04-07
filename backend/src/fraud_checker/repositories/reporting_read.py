from __future__ import annotations

from datetime import date, timedelta

import sqlalchemy as sa

from ..ip_filters import DATACENTER_IP_PREFIXES
from ..models import AggregatedRow, ConversionIpUaRollup
from .base import RepositoryBase


class ReportingReadRepository(RepositoryBase):
    def _sequence_placeholders(
        self,
        prefix: str,
        values: list[str],
    ) -> tuple[str, dict[str, object]]:
        placeholders: list[str] = []
        params: dict[str, object] = {}
        for idx, value in enumerate(values):
            key = f"{prefix}{idx}"
            placeholders.append(f":{key}")
            params[key] = value
        return ", ".join(placeholders), params

    def _max_timestamp_for_date(self, table_name: str, target_date: date) -> object | None:
        row = self.fetch_one(
            f"""
            SELECT MAX(updated_at) AS watermark
            FROM {table_name}
            WHERE date = :target_date
            """,
            {"target_date": target_date},
        )
        return row["watermark"] if row else None

    def get_click_data_watermark(self, target_date: date):
        if not self._table_exists("click_ipua_daily"):
            return None
        return self._max_timestamp_for_date("click_ipua_daily", target_date)

    def get_conversion_data_watermark(self, target_date: date):
        if not self._table_exists("conversion_ipua_daily"):
            return None
        return self._max_timestamp_for_date("conversion_ipua_daily", target_date)

    def get_conversion_findings_lineage(self, target_date: date) -> dict | None:
        if self._table_exists("findings_generations"):
            return self.fetch_one(
                """
                SELECT
                    created_at AS findings_last_computed_at,
                    settings_version_id,
                    settings_fingerprint,
                    detector_code_version,
                    source_click_watermark,
                    source_conversion_watermark,
                    row_count,
                    generation_id,
                    computed_by_job_id
                FROM findings_generations
                WHERE finding_type = 'conversion'
                  AND target_date = :target_date
                  AND is_current = TRUE
                ORDER BY created_at DESC
                LIMIT 1
                """,
                {"target_date": target_date},
            )
        if not self._table_exists("suspicious_conversion_findings"):
            return None
        return self.fetch_one(
            """
            SELECT
                MAX(computed_at) AS findings_last_computed_at,
                MAX(settings_updated_at_snapshot) AS settings_updated_at_snapshot,
                MAX(source_click_watermark) AS source_click_watermark,
                MAX(source_conversion_watermark) AS source_conversion_watermark
            FROM suspicious_conversion_findings
            WHERE date = :target_date
              AND is_current = TRUE
            """,
            {"target_date": target_date},
        )

    def fetch_aggregates(self, target_date: date) -> list[AggregatedRow]:
        with self._connect() as conn:
            result = conn.execute(
                sa.text(
                    """
                    SELECT date, media_id, program_id, ipaddress, useragent,
                           click_count, first_time, last_time, created_at, updated_at
                    FROM click_ipua_daily
                    WHERE date = :target_date
                    """
                ),
                {"target_date": target_date},
            )
            rows = result.fetchall()
        return [
            AggregatedRow(
                date=row[0],
                media_id=row[1],
                program_id=row[2],
                ipaddress=row[3],
                useragent=row[4],
                click_count=row[5],
                first_time=row[6],
                last_time=row[7],
                created_at=row[8],
                updated_at=row[9],
            )
            for row in rows
        ]

    def count_raw_rows(self, target_date: date) -> int:
        if not self._table_exists("click_raw"):
            return 0
        with self._connect() as conn:
            result = conn.execute(
                sa.text("SELECT COUNT(*) FROM click_raw WHERE CAST(click_time AS date) = :target_date"),
                {"target_date": target_date},
            ).scalar_one()
        return int(result)

    def fetch_conversion_rollups(self, target_date: date) -> list[ConversionIpUaRollup]:
        if not self._table_exists("conversion_ipua_daily"):
            return []
        with self._connect() as conn:
            result = conn.execute(
                sa.text(
                    """
                    SELECT
                        date,
                        ipaddress,
                        useragent,
                        SUM(conversion_count) AS total_conversions,
                        COUNT(DISTINCT media_id) AS media_count,
                        COUNT(DISTINCT program_id) AS program_count,
                        MIN(first_time) AS first_time,
                        MAX(last_time) AS last_time
                    FROM conversion_ipua_daily
                    WHERE date = :target_date
                    GROUP BY date, ipaddress, useragent
                    """
                ),
                {"target_date": target_date},
            )
            rows = result.fetchall()
        return [
            ConversionIpUaRollup(
                date=row[0],
                ipaddress=row[1],
                useragent=row[2],
                conversion_count=row[3],
                media_count=row[4],
                program_count=row[5],
                first_conversion_time=row[6],
                last_conversion_time=row[7],
            )
            for row in rows
        ]

    def fetch_click_to_conversion_gaps(
        self,
        target_date: date,
    ) -> dict[tuple[str, str], dict[str, float]]:
        if not self._table_exists("conversion_raw"):
            return {}
        with self._connect() as conn:
            rows = conn.execute(
                sa.text(
                    """
                    SELECT entry_ipaddress, entry_useragent, conversion_time, click_time
                    FROM conversion_raw
                    WHERE CAST(conversion_time AS date) = :target_date
                      AND click_time IS NOT NULL
                      AND entry_ipaddress IS NOT NULL
                      AND entry_useragent IS NOT NULL
                    """
                ),
                {"target_date": target_date},
            ).fetchall()

        stats: dict[tuple[str, str], dict[str, float]] = {}
        for entry_ip, entry_ua, conv_dt, click_dt in rows:
            if not conv_dt or not click_dt:
                continue
            gap_seconds = (conv_dt - click_dt).total_seconds()
            key = (entry_ip, entry_ua)
            if key not in stats:
                stats[key] = {"min": gap_seconds, "max": gap_seconds, "count": 1}
            else:
                stats[key]["min"] = min(stats[key]["min"], gap_seconds)
                stats[key]["max"] = max(stats[key]["max"], gap_seconds)
                stats[key]["count"] += 1
        return stats

    def fetch_conversion_click_padding_metrics(
        self,
        target_date: date,
        ip_ua_pairs: list[tuple[str, str]],
        *,
        extra_window_seconds: int,
    ) -> dict[tuple[str, str], dict[str, object]]:
        if (
            not ip_ua_pairs
            or not self._table_exists("conversion_raw")
            or not self._table_exists("click_raw")
        ):
            return {}

        metrics: dict[tuple[str, str], dict[str, object]] = {}
        chunk_size = 200
        for index in range(0, len(ip_ua_pairs), chunk_size):
            chunk = ip_ua_pairs[index : index + chunk_size]
            conversion_rows = self._fetch_conversion_padding_conversion_rows(target_date, chunk)
            if not conversion_rows:
                continue
            metrics.update(
                self._build_conversion_click_padding_metrics(
                    target_date,
                    conversion_rows,
                    extra_window_seconds=extra_window_seconds,
                )
            )
        return metrics

    def _fetch_conversion_padding_conversion_rows(
        self,
        target_date: date,
        ip_ua_pairs: list[tuple[str, str]],
    ) -> list[dict]:
        placeholders = ",".join(f"(:ip{idx}, :ua{idx})" for idx in range(len(ip_ua_pairs)))
        params: dict[str, object] = {"target_date": target_date}
        for idx, (ipaddress, useragent) in enumerate(ip_ua_pairs):
            params[f"ip{idx}"] = ipaddress
            params[f"ua{idx}"] = useragent

        with self._connect() as conn:
            return [
                dict(row)
                for row in conn.execute(
                    sa.text(
                        f"""
                        SELECT
                            id,
                            cid,
                            user_id,
                            program_id,
                            entry_ipaddress AS ipaddress,
                            entry_useragent AS useragent,
                            conversion_time
                        FROM conversion_raw
                        WHERE CAST(conversion_time AS date) = :target_date
                          AND entry_ipaddress IS NOT NULL
                          AND entry_useragent IS NOT NULL
                          AND (entry_ipaddress, entry_useragent) IN ({placeholders})
                        """
                    ),
                    params,
                ).mappings()
            ]

    def _fetch_direct_linked_click_rows(
        self,
        conversion_ids: list[str],
        cids: list[str],
    ) -> list[dict]:
        if not conversion_ids and not cids:
            return []

        conditions: list[str] = []
        params: dict[str, object] = {}
        if conversion_ids:
            placeholders, placeholder_params = self._sequence_placeholders(
                "conversion_id_",
                conversion_ids,
            )
            conditions.append(
                f"NULLIF(raw_payload::jsonb->>'action_log_raw', '') IN ({placeholders})"
            )
            params.update(placeholder_params)
        if cids:
            placeholders, placeholder_params = self._sequence_placeholders("cid_", cids)
            conditions.append(f"NULLIF(raw_payload::jsonb->>'track_cid', '') IN ({placeholders})")
            params.update(placeholder_params)

        with self._connect() as conn:
            return [
                dict(row)
                for row in conn.execute(
                    sa.text(
                        f"""
                        SELECT
                            id AS click_id,
                            NULLIF(raw_payload::jsonb->>'action_log_raw', '') AS action_log_raw_id,
                            NULLIF(raw_payload::jsonb->>'track_cid', '') AS track_cid
                        FROM click_raw
                        WHERE {" OR ".join(conditions)}
                        """
                    ),
                    params,
                ).mappings()
            ]

    def _fetch_bucket_click_rows(
        self,
        target_date: date,
        bucket_keys: list[tuple[str, str]],
    ) -> list[dict]:
        if not bucket_keys:
            return []

        placeholders = ",".join(
            f"(:affiliate_user_id{idx}, :program_id{idx})"
            for idx in range(len(bucket_keys))
        )
        params: dict[str, object] = {"target_date": target_date}
        for idx, (affiliate_user_id, program_id) in enumerate(bucket_keys):
            params[f"affiliate_user_id{idx}"] = affiliate_user_id
            params[f"program_id{idx}"] = program_id

        with self._connect() as conn:
            return [
                dict(row)
                for row in conn.execute(
                    sa.text(
                        f"""
                        SELECT
                            id AS click_id,
                            click_time,
                            useragent,
                            NULLIF(raw_payload::jsonb->>'user', '') AS affiliate_user_id,
                            NULLIF(raw_payload::jsonb->>'promotion', '') AS program_id
                        FROM click_raw
                        WHERE CAST(click_time AS date) = :target_date
                          AND (
                            NULLIF(raw_payload::jsonb->>'user', ''),
                            NULLIF(raw_payload::jsonb->>'promotion', '')
                          ) IN ({placeholders})
                        """
                    ),
                    params,
                ).mappings()
            ]

    def _build_conversion_click_padding_metrics(
        self,
        target_date: date,
        conversion_rows: list[dict],
        *,
        extra_window_seconds: int,
    ) -> dict[tuple[str, str], dict[str, object]]:
        grouped: dict[tuple[str, str], dict[str, object]] = {}
        conversion_ids: set[str] = set()
        cids: set[str] = set()
        bucket_keys: set[tuple[str, str]] = set()

        for row in conversion_rows:
            key = (row["ipaddress"], row["useragent"])
            state = grouped.setdefault(
                key,
                {
                    "conversion_ids": set(),
                    "cids": set(),
                    "bucket_keys": set(),
                    "first_time": row["conversion_time"],
                    "last_time": row["conversion_time"],
                },
            )
            state["conversion_ids"].add(row["id"])
            conversion_ids.add(row["id"])
            if row.get("cid"):
                state["cids"].add(row["cid"])
                cids.add(row["cid"])
            if row.get("user_id") and row.get("program_id"):
                bucket_key = (row["user_id"], row["program_id"])
                state["bucket_keys"].add(bucket_key)
                bucket_keys.add(bucket_key)
            if row["conversion_time"] < state["first_time"]:
                state["first_time"] = row["conversion_time"]
            if row["conversion_time"] > state["last_time"]:
                state["last_time"] = row["conversion_time"]

        direct_rows = self._fetch_direct_linked_click_rows(sorted(conversion_ids), sorted(cids))
        action_log_to_click_ids: dict[str, set[str]] = {}
        cid_to_click_ids: dict[str, set[str]] = {}
        for row in direct_rows:
            click_id = row["click_id"]
            action_log_raw_id = row.get("action_log_raw_id")
            track_cid = row.get("track_cid")
            if action_log_raw_id:
                action_log_to_click_ids.setdefault(action_log_raw_id, set()).add(click_id)
            if track_cid:
                cid_to_click_ids.setdefault(track_cid, set()).add(click_id)

        bucket_click_rows = self._fetch_bucket_click_rows(target_date, sorted(bucket_keys))
        bucket_to_click_rows: dict[tuple[str, str], list[dict]] = {}
        for row in bucket_click_rows:
            bucket_key = (row["affiliate_user_id"], row["program_id"])
            bucket_to_click_rows.setdefault(bucket_key, []).append(row)

        window_delta = timedelta(seconds=extra_window_seconds)
        metrics: dict[tuple[str, str], dict[str, object]] = {}
        for key, state in grouped.items():
            direct_click_ids: set[str] = set()
            for conversion_id in state["conversion_ids"]:
                direct_click_ids.update(action_log_to_click_ids.get(conversion_id, set()))
            for cid in state["cids"]:
                direct_click_ids.update(cid_to_click_ids.get(cid, set()))

            window_start = state["first_time"] - window_delta
            window_end = state["last_time"] + window_delta
            extra_click_rows: dict[str, dict] = {}
            for bucket_key in state["bucket_keys"]:
                for row in bucket_to_click_rows.get(bucket_key, []):
                    click_id = row["click_id"]
                    click_time = row.get("click_time")
                    if click_id in direct_click_ids or click_time is None:
                        continue
                    if click_time < window_start or click_time > window_end:
                        continue
                    extra_click_rows.setdefault(click_id, row)

            metrics[key] = {
                "linked_click_count": len(direct_click_ids),
                "extra_window_click_count": len(extra_click_rows),
                "extra_window_useragents": [
                    row.get("useragent") or ""
                    for row in extra_click_rows.values()
                ],
            }
        return metrics

    def fetch_suspicious_conversion_rollups(
        self,
        target_date: date,
        *,
        conversion_threshold: int = 5,
        media_threshold: int = 2,
        program_threshold: int = 2,
        burst_conversion_threshold: int = 3,
        browser_only: bool = False,
        exclude_datacenter_ip: bool = False,
    ) -> list[ConversionIpUaRollup]:
        if not self._table_exists("conversion_ipua_daily"):
            return []

        browser_filter = self._browser_filter_sql() if browser_only else ""
        datacenter_filter = (
            self._datacenter_filter_sql(DATACENTER_IP_PREFIXES) if exclude_datacenter_ip else ""
        )

        query = f"""
            SELECT
                date,
                ipaddress,
                useragent,
                SUM(conversion_count) AS total_conversions,
                COUNT(DISTINCT media_id) AS media_count,
                COUNT(DISTINCT program_id) AS program_count,
                MIN(first_time) AS first_time,
                MAX(last_time) AS last_time
            FROM conversion_ipua_daily
            WHERE date = :target_date
            {browser_filter}
            {datacenter_filter}
            GROUP BY date, ipaddress, useragent
            HAVING
                SUM(conversion_count) >= :conversion_threshold
                OR COUNT(DISTINCT media_id) >= :media_threshold
                OR COUNT(DISTINCT program_id) >= :program_threshold
                OR SUM(conversion_count) >= :burst_conversion_threshold
        """

        with self._connect() as conn:
            rows = conn.execute(
                sa.text(query),
                {
                    "target_date": target_date,
                    "conversion_threshold": conversion_threshold,
                    "media_threshold": media_threshold,
                    "program_threshold": program_threshold,
                    "burst_conversion_threshold": burst_conversion_threshold,
                },
            ).fetchall()
        return [
            ConversionIpUaRollup(
                date=row[0],
                ipaddress=row[1],
                useragent=row[2],
                conversion_count=row[3],
                media_count=row[4],
                program_count=row[5],
                first_conversion_time=row[6],
                last_conversion_time=row[7],
            )
            for row in rows
        ]

    def get_click_ipua_coverage(self, target_date: date) -> dict | None:
        if not self._table_exists("click_raw"):
            return None
        row = self.fetch_one(
            """
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (
                    WHERE COALESCE(NULLIF(ipaddress, ''), '') = ''
                       OR COALESCE(NULLIF(useragent, ''), '') = ''
                ) AS missing
            FROM click_raw
            WHERE CAST(click_time AS date) = :target_date
            """,
            {"target_date": target_date},
        )
        if not row or int(row["total"] or 0) == 0:
            return None
        total = int(row["total"])
        missing = int(row["missing"] or 0)
        return {
            "total": total,
            "missing": missing,
            "missing_rate": round(missing / total, 4),
        }

    def get_conversion_click_enrichment(self, target_date: date) -> dict | None:
        if not self._table_exists("conversion_raw"):
            return None
        row = self.fetch_one(
            """
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (
                    WHERE COALESCE(NULLIF(click_ipaddress, ''), '') <> ''
                      AND COALESCE(NULLIF(click_useragent, ''), '') <> ''
                ) AS enriched
            FROM conversion_raw
            WHERE CAST(conversion_time AS date) = :target_date
            """,
            {"target_date": target_date},
        )
        if not row or int(row["total"] or 0) == 0:
            return None
        total = int(row["total"])
        enriched = int(row["enriched"] or 0)
        return {
            "total": total,
            "enriched": enriched,
            "success_rate": round(enriched / total, 4),
        }
