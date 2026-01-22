from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

from ..repository import SQLiteRepository


def get_latest_date(repo: SQLiteRepository, table: str) -> Optional[str]:
    row = repo.fetch_one(f"SELECT MAX(date) as last_date FROM {table}")
    return row["last_date"] if row and row.get("last_date") else None


def resolve_summary_date(repo: SQLiteRepository, target_date: Optional[str]) -> str:
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
    return (date.today() - timedelta(days=1)).isoformat()


def get_summary(repo: SQLiteRepository, target_date: Optional[str]) -> dict:
    resolved_date = resolve_summary_date(repo, target_date)

    click_row = repo.fetch_one(
        """
        SELECT
            COALESCE(SUM(click_count), 0) as total_clicks,
            COUNT(DISTINCT ipaddress) as unique_ips,
            COUNT(DISTINCT media_id) as active_media
        FROM click_ipua_daily
        WHERE date = ?
        """,
        (resolved_date,),
    )

    conv_row = repo.fetch_one(
        """
        SELECT
            COALESCE(SUM(conversion_count), 0) as total_conversions,
            COUNT(DISTINCT ipaddress) as conversion_ips
        FROM conversion_ipua_daily
        WHERE date = ?
        """,
        (resolved_date,),
    )

    prev_date = (
        datetime.fromisoformat(resolved_date) - timedelta(days=1)
    ).strftime("%Y-%m-%d")

    prev_click = repo.fetch_one(
        "SELECT COALESCE(SUM(click_count), 0) as total FROM click_ipua_daily WHERE date = ?",
        (prev_date,),
    )
    prev_conv = repo.fetch_one(
        "SELECT COALESCE(SUM(conversion_count), 0) as total FROM conversion_ipua_daily WHERE date = ?",
        (prev_date,),
    )

    susp_clicks = repo.fetch_one(
        """
        SELECT COUNT(*) as count FROM (
            SELECT ipaddress, useragent
            FROM click_ipua_daily
            WHERE date = ?
            GROUP BY ipaddress, useragent
            HAVING SUM(click_count) >= 50
        )
        """,
        (resolved_date,),
    )

    susp_convs = repo.fetch_one(
        """
        SELECT COUNT(*) as count FROM (
            SELECT ipaddress, useragent
            FROM conversion_ipua_daily
            WHERE date = ?
            GROUP BY ipaddress, useragent
            HAVING SUM(conversion_count) >= 5
        )
        """,
        (resolved_date,),
    )

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
                "click_based": susp_clicks["count"] if susp_clicks else 0,
                "conversion_based": susp_convs["count"] if susp_convs else 0,
            },
        },
    }


def get_daily_stats(repo: SQLiteRepository, limit: int) -> list[dict]:
    click_rows = repo.fetch_all(
        """
        SELECT date, SUM(click_count) as clicks
        FROM click_ipua_daily
        GROUP BY date
        ORDER BY date DESC
        LIMIT ?
        """,
        (limit,),
    )

    conv_rows = repo.fetch_all(
        """
        SELECT date, SUM(conversion_count) as conversions
        FROM conversion_ipua_daily
        GROUP BY date
        ORDER BY date DESC
        LIMIT ?
        """,
        (limit,),
    )

    susp_click_rows = repo.fetch_all(
        """
        SELECT date, COUNT(*) as suspicious_count
        FROM (
            SELECT date, ipaddress, useragent
            FROM click_ipua_daily
            GROUP BY date, ipaddress, useragent
            HAVING SUM(click_count) >= 50
        )
        GROUP BY date
        ORDER BY date DESC
        LIMIT ?
        """,
        (limit,),
    )

    susp_conv_rows = repo.fetch_all(
        """
        SELECT date, COUNT(*) as suspicious_count
        FROM (
            SELECT date, ipaddress, useragent
            FROM conversion_ipua_daily
            GROUP BY date, ipaddress, useragent
            HAVING SUM(conversion_count) >= 5
        )
        GROUP BY date
        ORDER BY date DESC
        LIMIT ?
        """,
        (limit,),
    )

    merged: dict[str, dict] = {}
    for row in click_rows:
        merged[row["date"]] = {
            "date": row["date"],
            "clicks": row["clicks"],
            "conversions": 0,
            "suspicious_clicks": 0,
            "suspicious_conversions": 0,
        }
    for row in conv_rows:
        if row["date"] in merged:
            merged[row["date"]]["conversions"] = row["conversions"]
        else:
            merged[row["date"]] = {
                "date": row["date"],
                "clicks": 0,
                "conversions": row["conversions"],
                "suspicious_clicks": 0,
                "suspicious_conversions": 0,
            }
    for row in susp_click_rows:
        if row["date"] in merged:
            merged[row["date"]]["suspicious_clicks"] = row["suspicious_count"]
    for row in susp_conv_rows:
        if row["date"] in merged:
            merged[row["date"]]["suspicious_conversions"] = row["suspicious_count"]

    return sorted(merged.values(), key=lambda item: item["date"])


def get_available_dates(repo: SQLiteRepository) -> list[str]:
    click_dates = repo.fetch_all(
        "SELECT DISTINCT date FROM click_ipua_daily ORDER BY date DESC"
    )
    conv_dates = repo.fetch_all(
        "SELECT DISTINCT date FROM conversion_ipua_daily ORDER BY date DESC"
    )

    all_dates = {row["date"] for row in click_dates} | {row["date"] for row in conv_dates}
    return sorted(all_dates, reverse=True)
