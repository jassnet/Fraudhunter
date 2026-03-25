from __future__ import annotations

from datetime import date

import sqlalchemy as sa

from ..ip_filters import DATACENTER_IP_PREFIXES
from ..models import AggregatedRow, ConversionIpUaRollup, IpUaRollup
from .base import RepositoryBase


class ReportingReadRepository(RepositoryBase):
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

    def _get_findings_lineage(self, table_name: str, target_date: date) -> dict | None:
        if self._table_exists("findings_generations"):
            finding_type = "click" if table_name == "suspicious_click_findings" else "conversion"
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
                WHERE finding_type = :finding_type
                  AND target_date = :target_date
                  AND is_current = TRUE
                ORDER BY created_at DESC
                LIMIT 1
                """,
                {"finding_type": finding_type, "target_date": target_date},
            )
        if not self._table_exists(table_name):
            return None
        return self.fetch_one(
            f"""
            SELECT
                MAX(computed_at) AS findings_last_computed_at,
                MAX(settings_updated_at_snapshot) AS settings_updated_at_snapshot,
                MAX(source_click_watermark) AS source_click_watermark,
                MAX(source_conversion_watermark) AS source_conversion_watermark
            FROM {table_name}
            WHERE date = :target_date
              AND is_current = TRUE
            """,
            {"target_date": target_date},
        )

    def get_click_findings_lineage(self, target_date: date) -> dict | None:
        return self._get_findings_lineage("suspicious_click_findings", target_date)

    def get_conversion_findings_lineage(self, target_date: date) -> dict | None:
        return self._get_findings_lineage("suspicious_conversion_findings", target_date)

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

    def fetch_rollups(self, target_date: date) -> list[IpUaRollup]:
        with self._connect() as conn:
            result = conn.execute(
                sa.text(
                    """
                    SELECT
                        date,
                        ipaddress,
                        useragent,
                        SUM(click_count) AS total_clicks,
                        COUNT(DISTINCT media_id) AS media_count,
                        COUNT(DISTINCT program_id) AS program_count,
                        MIN(first_time) AS first_time,
                        MAX(last_time) AS last_time
                    FROM click_ipua_daily
                    WHERE date = :target_date
                    GROUP BY date, ipaddress, useragent
                    """
                ),
                {"target_date": target_date},
            )
            rows = result.fetchall()
        return [
            IpUaRollup(
                date=row[0],
                ipaddress=row[1],
                useragent=row[2],
                total_clicks=row[3],
                media_count=row[4],
                program_count=row[5],
                first_time=row[6],
                last_time=row[7],
            )
            for row in rows
        ]

    def fetch_suspicious_rollups(
        self,
        target_date: date,
        *,
        click_threshold: int,
        media_threshold: int,
        program_threshold: int,
        burst_click_threshold: int,
        browser_only: bool = False,
        exclude_datacenter_ip: bool = False,
    ) -> list[IpUaRollup]:
        browser_filter = self._browser_filter_sql() if browser_only else ""
        datacenter_filter = (
            self._datacenter_filter_sql(DATACENTER_IP_PREFIXES) if exclude_datacenter_ip else ""
        )

        query = f"""
            SELECT
                date,
                ipaddress,
                useragent,
                SUM(click_count) AS total_clicks,
                COUNT(DISTINCT media_id) AS media_count,
                COUNT(DISTINCT program_id) AS program_count,
                MIN(first_time) AS first_time,
                MAX(last_time) AS last_time
            FROM click_ipua_daily
            WHERE date = :target_date
            {browser_filter}
            {datacenter_filter}
            GROUP BY date, ipaddress, useragent
            HAVING
                SUM(click_count) >= :click_threshold
                OR COUNT(DISTINCT media_id) >= :media_threshold
                OR COUNT(DISTINCT program_id) >= :program_threshold
                OR SUM(click_count) >= :burst_click_threshold
        """

        with self._connect() as conn:
            result = conn.execute(
                sa.text(query),
                {
                    "target_date": target_date,
                    "click_threshold": click_threshold,
                    "media_threshold": media_threshold,
                    "program_threshold": program_threshold,
                    "burst_click_threshold": burst_click_threshold,
                },
            )
            rows = result.fetchall()
        return [
            IpUaRollup(
                date=row[0],
                ipaddress=row[1],
                useragent=row[2],
                total_clicks=row[3],
                media_count=row[4],
                program_count=row[5],
                first_time=row[6],
                last_time=row[7],
            )
            for row in rows
        ]

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

    def fetch_click_to_conversion_gaps(self, target_date: date) -> dict[tuple[str, str], dict[str, float]]:
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
