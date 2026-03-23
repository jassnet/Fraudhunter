from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

from ..repository_pg import PostgresRepository
from ..job_status_pg import JobStatusStorePG
from ..time_utils import today_local


def get_latest_date(repo: PostgresRepository, table: str) -> Optional[str]:
    allowed_tables = {"click_ipua_daily", "conversion_ipua_daily"}
    if table not in allowed_tables:
        raise ValueError(f"Unsupported table: {table}")
    row = repo.fetch_one(f"SELECT MAX(date) as last_date FROM {table}")
    if not row or not row.get("last_date"):
        return None
    value = row["last_date"]
    if isinstance(value, date):
        return value.isoformat()
    return value


def resolve_summary_date(repo: PostgresRepository, target_date: Optional[str]) -> str:
    if target_date:
        return target_date

    click_date = get_latest_date(repo, "click_ipua_daily")
    conv_date = get_latest_date(repo, "conversion_ipua_daily")

    if click_date and conv_date:
        return max(click_date, conv_date)
    if click_date:
        return click_date
    if conv_date:
        return conv_date
    return (today_local() - timedelta(days=1)).isoformat()


def get_summary(repo: PostgresRepository, target_date: Optional[str]) -> dict:
    resolved_date = resolve_summary_date(repo, target_date)

    click_row = repo.fetch_one(
        """
        SELECT
            COALESCE(SUM(click_count), 0) as total_clicks,
            COUNT(DISTINCT ipaddress) as unique_ips,
            COUNT(DISTINCT media_id) as active_media
        FROM click_ipua_daily
        WHERE date = :resolved_date
        """,
        {"resolved_date": resolved_date},
    )

    conv_row = repo.fetch_one(
        """
        SELECT
            COALESCE(SUM(conversion_count), 0) as total_conversions,
            COUNT(DISTINCT ipaddress) as conversion_ips
        FROM conversion_ipua_daily
        WHERE date = :resolved_date
        """,
        {"resolved_date": resolved_date},
    )

    prev_date = (
        datetime.fromisoformat(resolved_date) - timedelta(days=1)
    ).strftime("%Y-%m-%d")

    prev_click = repo.fetch_one(
        "SELECT COALESCE(SUM(click_count), 0) as total FROM click_ipua_daily WHERE date = :prev_date",
        {"prev_date": prev_date},
    )
    prev_conv = repo.fetch_one(
        "SELECT COALESCE(SUM(conversion_count), 0) as total FROM conversion_ipua_daily WHERE date = :prev_date",
        {"prev_date": prev_date},
    )

    try:
        target_date_obj = date.fromisoformat(resolved_date)
    except ValueError:
        target_date_obj = None

    if target_date_obj:
        susp_click_count = repo.count_current_click_findings(target_date_obj)
        susp_conv_count = repo.count_current_conversion_findings(target_date_obj)
        click_coverage = repo.get_click_ipua_coverage(target_date_obj)
        conversion_enrichment = repo.get_conversion_click_enrichment(target_date_obj)
    else:
        susp_click_count = 0
        susp_conv_count = 0
        click_coverage = None
        conversion_enrichment = None

    last_successful_ingest = JobStatusStorePG(repo.database_url).get_latest_successful_finished_at(
        ["ingest_clicks", "ingest_conversions", "refresh"]
    )
    masters = repo.get_all_masters()
    last_master_sync = masters.get("last_synced_at")
    if isinstance(last_master_sync, datetime):
        last_master_sync = last_master_sync.isoformat()

    return {
        "date": resolved_date,
        "stats": {
            "clicks": {
                "total": click_row["total_clicks"] if click_row else 0,
                "unique_ips": click_row["unique_ips"] if click_row else 0,
                "media_count": click_row["active_media"] if click_row else 0,
                "prev_total": prev_click["total"] if prev_click else 0,
            },
            "conversions": {
                "total": conv_row["total_conversions"] if conv_row else 0,
                "unique_ips": conv_row["conversion_ips"] if conv_row else 0,
                "prev_total": prev_conv["total"] if prev_conv else 0,
            },
            "suspicious": {
                "click_based": susp_click_count,
                "conversion_based": susp_conv_count,
            },
        },
        "quality": {
            "last_successful_ingest_at": (
                last_successful_ingest.isoformat() if last_successful_ingest else None
            ),
            "click_ip_ua_coverage": click_coverage,
            "conversion_click_enrichment": conversion_enrichment,
            "master_sync": {
                "last_synced_at": last_master_sync,
            },
        },
    }


def get_daily_stats(repo: PostgresRepository, limit: int) -> list[dict]:
    click_rows = repo.fetch_all(
        """
        SELECT date, SUM(click_count) as clicks
        FROM click_ipua_daily
        GROUP BY date
        ORDER BY date DESC
        LIMIT :limit
        """,
        {"limit": limit},
    )

    conv_rows = repo.fetch_all(
        """
        SELECT date, SUM(conversion_count) as conversions
        FROM conversion_ipua_daily
        GROUP BY date
        ORDER BY date DESC
        LIMIT :limit
        """,
        {"limit": limit},
    )

    merged: dict[str, dict] = {}
    for row in click_rows:
        row_date = row["date"].isoformat() if isinstance(row["date"], date) else row["date"]
        merged[row_date] = {
            "date": row_date,
            "clicks": row["clicks"],
            "conversions": 0,
            "suspicious_clicks": 0,
            "suspicious_conversions": 0,
        }
    for row in conv_rows:
        row_date = row["date"].isoformat() if isinstance(row["date"], date) else row["date"]
        if row_date in merged:
            merged[row_date]["conversions"] = row["conversions"]
        else:
            merged[row_date] = {
                "date": row_date,
                "clicks": 0,
                "conversions": row["conversions"],
                "suspicious_clicks": 0,
                "suspicious_conversions": 0,
            }
    finding_counts = repo.get_daily_finding_counts(limit)
    for row_date, counts in finding_counts.items():
        merged.setdefault(
            row_date,
            {
                "date": row_date,
                "clicks": 0,
                "conversions": 0,
                "suspicious_clicks": 0,
                "suspicious_conversions": 0,
            },
        )
        merged[row_date]["suspicious_clicks"] = counts.get("suspicious_clicks", 0)
        merged[row_date]["suspicious_conversions"] = counts.get("suspicious_conversions", 0)

    return sorted(merged.values(), key=lambda item: item["date"])


def get_available_dates(repo: PostgresRepository) -> list[str]:
    click_dates = repo.fetch_all(
        "SELECT DISTINCT date FROM click_ipua_daily ORDER BY date DESC"
    )
    conv_dates = repo.fetch_all(
        "SELECT DISTINCT date FROM conversion_ipua_daily ORDER BY date DESC"
    )

    all_dates = {
        (row["date"].isoformat() if isinstance(row["date"], date) else row["date"])
        for row in click_dates
    } | {
        (row["date"].isoformat() if isinstance(row["date"], date) else row["date"])
        for row in conv_dates
    }
    return sorted(all_dates, reverse=True)
