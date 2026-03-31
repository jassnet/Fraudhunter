from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

from ..job_status_pg import JobStatusStorePG
from ..service_protocols import ReportingRepository
from ..time_utils import today_local


def _iso(value: object) -> str | None:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _build_findings_freshness(
    repo: ReportingRepository,
    target_date: date | None,
    *,
    has_click_data: bool,
    has_conversion_data: bool,
) -> dict:
    if target_date is None:
        return {"findings_last_computed_at": None, "stale": False, "stale_reasons": []}

    del has_click_data
    settings_updated_at = repo.get_settings_updated_at()
    latest_settings_version_id = repo.get_latest_settings_version_id()
    conversion_watermark = repo.get_conversion_data_watermark(target_date)
    conversion_lineage = repo.get_conversion_findings_lineage(target_date) or {}

    conversion_last = conversion_lineage.get("findings_last_computed_at")
    last_computed = conversion_last

    stale_reasons: list[str] = []
    if has_conversion_data:
        if conversion_last is None:
            stale_reasons.append("conversion_findings_missing")
        if conversion_lineage.get("source_conversion_watermark") != conversion_watermark:
            stale_reasons.append("conversion_source_advanced")
        if latest_settings_version_id:
            if conversion_lineage.get("settings_version_id") != latest_settings_version_id:
                stale_reasons.append("settings_changed_after_conversion_findings")
        elif settings_updated_at and conversion_lineage.get("settings_updated_at_snapshot") != settings_updated_at:
            stale_reasons.append("settings_changed_after_conversion_findings")

    return {
        "findings_last_computed_at": _iso(last_computed),
        "stale": bool(stale_reasons),
        "stale_reasons": stale_reasons,
        "click_findings_last_computed_at": None,
        "conversion_findings_last_computed_at": _iso(conversion_last),
    }


def get_latest_date(repo: ReportingRepository, table: str) -> Optional[str]:
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


def resolve_summary_date(repo: ReportingRepository, target_date: Optional[str]) -> str:
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


def get_summary(
    repo: ReportingRepository,
    target_date: Optional[str],
    *,
    job_store: JobStatusStorePG | None = None,
) -> dict:
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
        susp_click_count = 0
        susp_conv_count = repo.count_current_conversion_findings(target_date_obj)
        click_coverage = repo.get_click_ipua_coverage(target_date_obj)
        conversion_enrichment = repo.get_conversion_click_enrichment(target_date_obj)
        findings_freshness = _build_findings_freshness(
            repo,
            target_date_obj,
            has_click_data=bool((click_row or {}).get("total_clicks")),
            has_conversion_data=bool((conv_row or {}).get("total_conversions")),
        )
    else:
        susp_click_count = 0
        susp_conv_count = 0
        click_coverage = None
        conversion_enrichment = None
        findings_freshness = {"findings_last_computed_at": None, "stale": False, "stale_reasons": []}

    status_store = job_store or JobStatusStorePG(repo.database_url)
    last_successful_ingest = status_store.get_latest_successful_finished_at(
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
            "findings": findings_freshness,
            "master_sync": {
                "last_synced_at": last_master_sync,
            },
        },
    }


def get_daily_stats(
    repo: ReportingRepository, limit: int, target_date: str | None = None
) -> list[dict]:
    params = {"limit": limit}
    daily_where = ""
    findings_where = ""
    if target_date:
        params["target_date"] = target_date
        daily_where = "WHERE date <= :target_date"
        findings_where = "WHERE date <= :target_date AND is_current = TRUE"

    click_rows = repo.fetch_all(
        """
        SELECT date, SUM(click_count) as clicks
        FROM click_ipua_daily
        {daily_where}
        GROUP BY date
        ORDER BY date DESC
        LIMIT :limit
        """.format(daily_where=daily_where),
        params,
    )

    conv_rows = repo.fetch_all(
        """
        SELECT date, SUM(conversion_count) as conversions
        FROM conversion_ipua_daily
        {daily_where}
        GROUP BY date
        ORDER BY date DESC
        LIMIT :limit
        """,
        params,
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
    finding_rows = repo.fetch_all(
        """
        SELECT date, COUNT(*) as suspicious_conversions
        FROM suspicious_conversion_findings
        {findings_where}
        GROUP BY date
        ORDER BY date DESC
        LIMIT :limit
        """.format(findings_where=findings_where),
        params,
    )
    for row in finding_rows:
        row_date = row["date"].isoformat() if isinstance(row["date"], date) else row["date"]
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
        merged[row_date]["suspicious_conversions"] = row.get("suspicious_conversions", 0)

    return sorted(merged.values(), key=lambda item: item["date"])


def get_available_dates(repo: ReportingRepository) -> list[str]:
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
