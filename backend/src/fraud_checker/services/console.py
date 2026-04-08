from __future__ import annotations

import json
import logging
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta
from typing import Any

import sqlalchemy as sa

from ..api_parsers import parse_iso_date
from ..api_presenters import format_reasons
from ..console_service_support import (
    build_alert_csv,
    normalize_reward_amount_source,
    reward_amount_is_estimated,
)
from ..constants import DEFAULT_REWARD_YEN
from ..service_protocols import ConsoleRepository
from ..time_utils import now_local
from . import reporting

logger = logging.getLogger(__name__)
ALERT_REVIEW_STATUSES = {"unhandled", "investigating", "confirmed_fraud", "white"}
DEFAULT_AFFILIATE_ID = "unassigned"
DEFAULT_AFFILIATE_NAME = "Unassigned"
DEFAULT_OUTCOME_TYPE = "Unknown Outcome"
DEFAULT_ALERT_PAGE = 1
DEFAULT_ALERT_PAGE_SIZE = 50
MAX_ALERT_PAGE_SIZE = 200
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


def _findings_column_exists(repo: ConsoleRepository, column_name: str) -> bool:
    exists = getattr(repo, "_column_exists", None)
    if not callable(exists):
        return False
    try:
        return bool(exists("suspicious_conversion_findings", column_name))
    except Exception:
        logger.exception("Failed to inspect suspicious_conversion_findings column '%s'", column_name)
        return False


def _optional_findings_column(repo: ConsoleRepository, column_name: str, sql_type: str) -> str:
    if _findings_column_exists(repo, column_name):
        return f"f.{column_name}"
    return f"CAST(NULL AS {sql_type}) AS {column_name}"


def _findings_select_columns(repo: ConsoleRepository) -> str:
    return ",\n                ".join(
        [
            "f.finding_key",
            "f.date",
            "f.ipaddress",
            "f.useragent",
            "f.program_ids_json",
            "f.program_names_json",
            _optional_findings_column(repo, "affiliate_ids_json", "TEXT"),
            "f.affiliate_names_json",
            "f.risk_level",
            "f.risk_score",
            "f.reasons_json",
            "f.reasons_formatted_json",
            "f.metrics_json",
            "f.total_conversions",
            "f.first_time",
            "f.last_time",
            "f.computed_at",
            _optional_findings_column(repo, "estimated_damage_yen", "INTEGER"),
            _optional_findings_column(repo, "damage_unit_price_source", "TEXT"),
            _optional_findings_column(repo, "damage_evidence_json", "TEXT"),
        ]
    )


def get_dashboard(repo: ConsoleRepository, target_date: str | None = None) -> dict[str, Any]:
    summary = reporting.get_summary(repo, target_date)
    resolved_date = summary["date"]
    available_dates = reporting.get_available_dates(repo)
    alert_rows = _fetch_alert_rows(
        repo,
        start_date=resolved_date,
        end_date=resolved_date,
        status=None,
        sort="risk_desc",
    )
    transaction_summary = _fetch_alert_transaction_summary(
        repo,
        [row for row in alert_rows if _requires_summary_fallback(row)],
    )
    affiliate_totals = _fetch_affiliate_conversion_totals(repo, parse_iso_date(resolved_date))

    impacted_conversions = sum(int(row.get("total_conversions") or 0) for row in alert_rows)
    total_conversions = int(summary.get("stats", {}).get("conversions", {}).get("total", 0) or 0)
    fraud_rate = round((impacted_conversions / total_conversions) * 100, 1) if total_conversions else 0.0
    unhandled_alerts = sum(1 for row in alert_rows if row["review_status"] == "unhandled")
    estimated_damage = sum(
        _resolve_alert_summary(row, transaction_summary.get(str(row["finding_key"])))["reward_amount"]
        for row in alert_rows
    )

    trend_source = reporting.get_daily_stats(repo, 14, resolved_date)
    trend = [
        {
            "date": item["date"],
            "alerts": int(item.get("suspicious_conversions", 0) or 0),
        }
        for item in trend_source
    ]

    ranking = _build_affiliate_ranking(alert_rows, transaction_summary, affiliate_totals)[:10]

    return {
        "date": resolved_date,
        "available_dates": available_dates,
        "kpis": {
            "fraud_rate": {"value": fraud_rate, "label": "Fraud Rate", "unit": "%"},
            "unhandled_alerts": {"value": unhandled_alerts, "label": "Unhandled Alerts", "unit": "items"},
            "estimated_damage": {"value": estimated_damage, "label": "Estimated Damage", "unit": "JPY"},
        },
        "trend": trend,
        "ranking": ranking,
    }


def list_alerts(
    repo: ConsoleRepository,
    *,
    status: str | None = "unhandled",
    risk_level: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    search: str | None = None,
    sort: str = "risk_desc",
    page: int = DEFAULT_ALERT_PAGE,
    page_size: int = DEFAULT_ALERT_PAGE_SIZE,
) -> dict[str, Any]:
    resolved_start, resolved_end = _resolve_alert_window(repo, start_date, end_date)
    resolved_page = max(DEFAULT_ALERT_PAGE, int(page or DEFAULT_ALERT_PAGE))
    resolved_page_size = min(MAX_ALERT_PAGE_SIZE, max(1, int(page_size or DEFAULT_ALERT_PAGE_SIZE)))
    offset = (resolved_page - 1) * resolved_page_size

    filtered_rows = _fetch_alert_rows(
        repo,
        start_date=resolved_start,
        end_date=resolved_end,
        risk_level=risk_level,
        search=search,
        status=status,
        sort=sort,
        limit=resolved_page_size,
        offset=offset,
    )
    transaction_summary = _fetch_alert_transaction_summary(
        repo,
        [row for row in filtered_rows if _requires_summary_fallback(row)],
    )

    items = [_build_alert_item(row, transaction_summary.get(str(row["finding_key"]))) for row in filtered_rows]
    status_counts = _fetch_alert_status_counts(
        repo,
        start_date=resolved_start,
        end_date=resolved_end,
    )
    total = _count_alert_rows(
        repo,
        start_date=resolved_start,
        end_date=resolved_end,
        risk_level=risk_level,
        search=search,
        status=status,
    )

    return {
        "available_dates": reporting.get_available_dates(repo),
        "applied_filters": {
            "status": status or "all",
            "risk_level": (risk_level or "").strip() or None,
            "start_date": resolved_start,
            "end_date": resolved_end,
            "search": (search or "").strip() or None,
            "sort": sort,
        },
        "status_counts": {
            "unhandled": status_counts.get("unhandled", 0),
            "investigating": status_counts.get("investigating", 0),
            "confirmed_fraud": status_counts.get("confirmed_fraud", 0),
            "white": status_counts.get("white", 0),
        },
        "items": items,
        "total": total,
        "page": resolved_page,
        "page_size": resolved_page_size,
        "has_next": offset + len(items) < total,
    }


def export_alerts_csv(
    repo: ConsoleRepository,
    *,
    status: str | None = "unhandled",
    risk_level: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    search: str | None = None,
    sort: str = "risk_desc",
) -> str:
    resolved_start, resolved_end = _resolve_alert_window(repo, start_date, end_date)
    rows = _fetch_alert_rows(
        repo,
        start_date=resolved_start,
        end_date=resolved_end,
        risk_level=risk_level,
        search=search,
        status=status,
        sort=sort,
    )
    transaction_summary = _fetch_alert_transaction_summary(
        repo,
        [row for row in rows if _requires_summary_fallback(row)],
    )
    items = [_build_alert_item(row, transaction_summary.get(str(row["finding_key"]))) for row in rows]
    return build_alert_csv(items, exported_at=now_local().isoformat())


def get_alert_detail(repo: ConsoleRepository, finding_key: str) -> dict[str, Any] | None:
    row = _fetch_alert_detail_row(repo, finding_key)
    if row is None:
        return None

    fallback_summary = None
    if _requires_summary_fallback(row):
        fallback_summary = _fetch_alert_transaction_summary(repo, [row]).get(str(row["finding_key"]))

    entity_transactions = _fetch_entity_transactions(
        repo,
        row["date"],
        row["ipaddress"],
        row["useragent"],
    )
    summary = _resolve_alert_summary(row, fallback_summary)
    affiliate_id = summary["affiliate_id"]
    recent_transactions = (
        _fetch_recent_affiliate_transactions(repo, affiliate_id)
        if affiliate_id and affiliate_id != DEFAULT_AFFILIATE_ID
        else entity_transactions[:10]
    )
    raw_reasons = row.get("reasons_json") or []
    reasons = format_reasons(raw_reasons) if raw_reasons else []

    return {
        "finding_key": row["finding_key"],
        "affiliate_id": affiliate_id,
        "affiliate_name": summary["affiliate_name"],
        "risk_score": row["risk_score"],
        "risk_level": row["risk_level"],
        "status": row["review_status"],
        "reward_amount": summary["reward_amount"],
        "detected_at": _iso(row.get("computed_at")),
        "outcome_type": summary["outcome_type"],
        "program_name": summary["outcome_type"],
        "reward_amount_source": summary["reward_amount_source"],
        "reward_amount_is_estimated": summary["reward_amount_is_estimated"],
        "reasons": reasons,
        "transactions": [_present_transaction(item) for item in recent_transactions],
        "actions": ["confirmed_fraud", "white", "investigating"],
    }


def apply_review_action(repo: ConsoleRepository, finding_keys: list[str], status: str) -> dict[str, Any]:
    if status not in ALERT_REVIEW_STATUSES:
        raise ValueError(f"Unsupported review status: {status}")

    unique_keys = sorted({value for value in finding_keys if value})
    if not unique_keys:
        return {"updated_count": 0, "status": status}

    updated_count = repo.apply_alert_reviews(unique_keys, status=status, updated_at=now_local())
    return {"updated_count": updated_count, "status": status}


def _resolve_alert_window(
    repo: ConsoleRepository,
    start_date: str | None,
    end_date: str | None,
) -> tuple[str | None, str | None]:
    if start_date and end_date:
        return start_date, end_date
    if start_date:
        return start_date, start_date
    if end_date:
        return end_date, end_date

    try:
        latest_finding_date = repo.fetch_one(
            """
            SELECT MAX(date) AS latest_date
            FROM suspicious_conversion_findings
            WHERE is_current = TRUE
            """
        )
    except sa.exc.SQLAlchemyError:
        logger.exception("Failed to resolve latest alert window")
        latest_finding_date = None
    value = latest_finding_date.get("latest_date") if latest_finding_date else None
    if value is None:
        fallback = reporting.resolve_summary_date(repo, None)
        return fallback, fallback
    resolved = value.isoformat() if hasattr(value, "isoformat") else str(value)
    return resolved, resolved


def _fetch_alert_rows(
    repo: ConsoleRepository,
    *,
    start_date: str | None,
    end_date: str | None,
    risk_level: str | None = None,
    search: str | None = None,
    status: str | None,
    sort: str,
    limit: int | None = None,
    offset: int | None = None,
) -> list[dict[str, Any]]:
    select_columns = _findings_select_columns(repo)
    params: dict[str, object] = {}
    conditions = ["f.is_current = TRUE"]
    review_status_sql = "COALESCE(r.review_status, 'unhandled')"

    if start_date:
        params["start_date"] = parse_iso_date(start_date)
        conditions.append("f.date >= :start_date")
    if end_date:
        params["end_date"] = parse_iso_date(end_date)
        conditions.append("f.date <= :end_date")
    if risk_level and risk_level.strip():
        params["risk_level"] = risk_level.strip()
        conditions.append("f.risk_level = :risk_level")
    if search and search.strip():
        params["search"] = f"%{search.strip().lower()}%"
        conditions.append("f.search_text LIKE :search")
    if status and status != "all":
        params["review_status"] = status
        conditions.append(f"{review_status_sql} = :review_status")

    order_by = {
        "risk_desc": "f.risk_score DESC, f.computed_at DESC",
        "risk_asc": "f.risk_score ASC, f.computed_at DESC",
        "detected_desc": "f.computed_at DESC, f.risk_score DESC",
        "detected_asc": "f.computed_at ASC, f.risk_score DESC",
    }.get(sort, "f.risk_score DESC, f.computed_at DESC")
    pagination_sql = ""
    if limit is not None:
        params["limit"] = limit
        pagination_sql += " LIMIT :limit"
    if offset is not None:
        params["offset"] = max(0, offset)
        pagination_sql += " OFFSET :offset"

    try:
        rows = repo.fetch_all(
            f"""
            SELECT
                {select_columns},
                {review_status_sql} AS review_status
            FROM suspicious_conversion_findings f
            LEFT JOIN fraud_alert_reviews r
              ON r.finding_key = f.finding_key
            WHERE {" AND ".join(conditions)}
            ORDER BY {order_by}, f.finding_key ASC
            {pagination_sql}
            """,
            params,
        )
    except sa.exc.SQLAlchemyError:
        logger.exception("Failed to fetch console alert rows")
        return []
    return [_deserialize_alert_row(row) for row in rows]


def _fetch_alert_detail_row(repo: ConsoleRepository, finding_key: str) -> dict[str, Any] | None:
    select_columns = _findings_select_columns(repo)
    try:
        rows = repo.fetch_all(
            f"""
            SELECT
                {select_columns},
                COALESCE(r.review_status, 'unhandled') AS review_status
            FROM suspicious_conversion_findings f
            LEFT JOIN fraud_alert_reviews r
              ON r.finding_key = f.finding_key
            WHERE f.finding_key = :finding_key
              AND f.is_current = TRUE
            LIMIT 1
            """,
            {"finding_key": finding_key},
        )
    except sa.exc.SQLAlchemyError:
        logger.exception("Failed to fetch console alert detail row")
        return None
    if not rows:
        return None
    return _deserialize_alert_row(rows[0])


def _fetch_alert_status_counts(
    repo: ConsoleRepository,
    *,
    start_date: str | None,
    end_date: str | None,
) -> dict[str, int]:
    params: dict[str, object] = {}
    conditions = ["f.is_current = TRUE"]

    if start_date:
        params["start_date"] = parse_iso_date(start_date)
        conditions.append("f.date >= :start_date")
    if end_date:
        params["end_date"] = parse_iso_date(end_date)
        conditions.append("f.date <= :end_date")

    try:
        rows = repo.fetch_all(
            f"""
            SELECT
                COALESCE(r.review_status, 'unhandled') AS review_status,
                COUNT(*) AS row_count
            FROM suspicious_conversion_findings f
            LEFT JOIN fraud_alert_reviews r
              ON r.finding_key = f.finding_key
            WHERE {" AND ".join(conditions)}
            GROUP BY COALESCE(r.review_status, 'unhandled')
            """,
            params,
        )
    except sa.exc.SQLAlchemyError:
        logger.exception("Failed to fetch console alert status counts")
        return {}

    return {
        str(row["review_status"]): int(row.get("row_count") or 0)
        for row in rows
        if row.get("review_status")
    }


def _count_alert_rows(
    repo: ConsoleRepository,
    *,
    start_date: str | None,
    end_date: str | None,
    risk_level: str | None = None,
    search: str | None = None,
    status: str | None,
) -> int:
    params: dict[str, object] = {}
    conditions = ["f.is_current = TRUE"]
    review_status_sql = "COALESCE(r.review_status, 'unhandled')"

    if start_date:
        params["start_date"] = parse_iso_date(start_date)
        conditions.append("f.date >= :start_date")
    if end_date:
        params["end_date"] = parse_iso_date(end_date)
        conditions.append("f.date <= :end_date")
    if risk_level and risk_level.strip():
        params["risk_level"] = risk_level.strip()
        conditions.append("f.risk_level = :risk_level")
    if search and search.strip():
        params["search"] = f"%{search.strip().lower()}%"
        conditions.append("f.search_text LIKE :search")
    if status and status != "all":
        params["review_status"] = status
        conditions.append(f"{review_status_sql} = :review_status")

    try:
        row = repo.fetch_one(
            f"""
            SELECT COUNT(*) AS row_count
            FROM suspicious_conversion_findings f
            LEFT JOIN fraud_alert_reviews r
              ON r.finding_key = f.finding_key
            WHERE {" AND ".join(conditions)}
            """,
            params,
        )
    except sa.exc.SQLAlchemyError:
        logger.exception("Failed to count console alert rows")
        return 0

    return int((row or {}).get("row_count") or 0)


def _fetch_alert_transaction_summary(repo: ConsoleRepository, rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    findings = rows
    if not findings or not repo._table_exists("conversion_raw"):
        return {}

    keys = [
        (
            row["finding_key"],
            row["date"],
            *_date_time_bounds(row["date"]),
            row["ipaddress"],
            row["useragent"],
        )
        for row in findings
    ]
    placeholders = ", ".join(
        f"(:finding_key{idx}, :target_date{idx}, :target_start{idx}, :target_end{idx}, :ipaddress{idx}, :useragent{idx})"
        for idx in range(len(keys))
    )
    params: dict[str, object] = {}
    for idx, (finding_key, target_date, target_start, target_end, ipaddress, useragent) in enumerate(keys):
        params[f"finding_key{idx}"] = finding_key
        params[f"target_date{idx}"] = target_date
        params[f"target_start{idx}"] = target_start
        params[f"target_end{idx}"] = target_end
        params[f"ipaddress{idx}"] = ipaddress
        params[f"useragent{idx}"] = useragent

    matched_records = repo.fetch_all(
        f"""
        WITH target_entities AS (
            SELECT *
            FROM (VALUES {placeholders})
            AS t(finding_key, target_date, target_start, target_end, ipaddress, useragent)
        )
        SELECT
            t.finding_key,
            c.id AS transaction_id,
            c.conversion_time,
            c.state,
            c.raw_payload,
            c.user_id,
            COALESCE(u.name, c.user_id, :default_affiliate_name) AS affiliate_name,
            c.program_id,
            COALESCE(p.name, c.program_id, :default_outcome_type) AS promotion_name
        FROM target_entities t
        JOIN conversion_raw c
          ON c.conversion_time >= t.target_start
         AND c.conversion_time < t.target_end
         AND c.entry_ipaddress = t.ipaddress
         AND c.entry_useragent = t.useragent
        LEFT JOIN master_user u
          ON u.id = c.user_id
        LEFT JOIN master_promotion p
          ON p.id = c.program_id
        ORDER BY c.conversion_time DESC
        """,
        {
            **params,
            "default_affiliate_name": DEFAULT_AFFILIATE_NAME,
            "default_outcome_type": DEFAULT_OUTCOME_TYPE,
        },
    )

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in matched_records:
        grouped[str(row["finding_key"])].append(dict(row))

    summaries = {finding_key: _summarize_transactions(items) for finding_key, items in grouped.items()}
    price_index = _fetch_program_unit_prices(repo, findings)

    for finding in findings:
        finding_key = str(finding["finding_key"])
        matched_rows = grouped.get(finding_key, [])
        summary = summaries.get(finding_key)
        summaries[finding_key] = _merge_summary_with_fallback(
            finding,
            matched_rows=matched_rows,
            summary=summary,
            price_index=price_index,
        )

    return summaries


def _fetch_program_unit_prices(repo: ConsoleRepository, findings: list[dict[str, Any]]) -> dict[tuple[date, str], int]:
    requested_dates = sorted({row["date"] for row in findings if isinstance(row.get("date"), date)})
    requested_program_ids = sorted(
        {
            str(program_id)
            for row in findings
            for program_id in (row.get("program_ids_json") or [])
            if program_id
        }
    )
    if not requested_dates or not requested_program_ids:
        return {}

    program_placeholders = ", ".join(f":program_id_{idx}" for idx in range(len(requested_program_ids)))
    date_ranges = {value: _date_time_bounds(value) for value in requested_dates}
    overall_start = min(bounds[0] for bounds in date_ranges.values())
    overall_end = max(bounds[1] for bounds in date_ranges.values())
    params: dict[str, object] = {
        "overall_start": overall_start,
        "overall_end": overall_end,
        **{f"program_id_{idx}": value for idx, value in enumerate(requested_program_ids)},
    }
    rows = repo.fetch_all(
        f"""
        SELECT
            conversion_time,
            program_id,
            raw_payload
        FROM conversion_raw
        WHERE conversion_time >= :overall_start
          AND conversion_time < :overall_end
          AND program_id IN ({program_placeholders})
        """,
        params,
    )

    grouped_prices: dict[tuple[date, str], list[int]] = defaultdict(list)
    for row in rows:
        conversion_time = row.get("conversion_time")
        target_date = conversion_time.date() if isinstance(conversion_time, datetime) else None
        program_id = row.get("program_id")
        if not isinstance(target_date, date) or target_date not in date_ranges or not program_id:
            continue
        grouped_prices[(target_date, str(program_id))].append(_reward_from_payload(row.get("raw_payload")))

    index: dict[tuple[date, str], int] = {}
    for key, prices in grouped_prices.items():
        representative = _representative_unit_price(prices)
        if representative is not None:
            index[key] = representative
    return index


def _merge_summary_with_fallback(
    finding: dict[str, Any],
    *,
    matched_rows: list[dict[str, Any]],
    summary: dict[str, Any] | None,
    price_index: dict[tuple[date, str], int],
) -> dict[str, Any]:
    total_conversions = int(finding.get("total_conversions") or 0)
    matched_count = len(matched_rows)
    resolved_count = max(total_conversions, matched_count)

    if summary is None:
        summary = {
            "transaction_count": 0,
            "reward_amount": 0,
            "latest_occurred_at": _iso(finding.get("last_time")) or _iso(finding.get("computed_at")),
            "affiliate_id": DEFAULT_AFFILIATE_ID,
            "affiliate_name": _first_non_empty(finding.get("affiliate_names_json")) or DEFAULT_AFFILIATE_NAME,
            "outcome_type": _first_non_empty(finding.get("program_names_json")) or DEFAULT_OUTCOME_TYPE,
            "reward_amount_source": "unknown",
        }

    summary["transaction_count"] = resolved_count

    missing_count = max(total_conversions - matched_count, 0)
    if missing_count <= 0:
        return summary

    direct_unit_price = _representative_unit_price(
        [_reward_from_payload(row.get("raw_payload")) for row in matched_rows]
    )
    fallback_unit_price = direct_unit_price
    if fallback_unit_price is None:
        fallback_unit_price = _resolve_finding_unit_price(finding, price_index)
    if fallback_unit_price is None:
        fallback_unit_price = DEFAULT_REWARD_YEN

    summary["reward_amount"] += fallback_unit_price * missing_count
    summary["reward_amount_source"] = "mixed" if matched_count > 0 else "fallback_default"
    return summary


def _resolve_finding_unit_price(
    finding: dict[str, Any],
    price_index: dict[tuple[date, str], int],
) -> int | None:
    target_date = finding.get("date")
    if not isinstance(target_date, date):
        return None
    prices = [
        price_index[(target_date, str(program_id))]
        for program_id in (finding.get("program_ids_json") or [])
        if program_id and (target_date, str(program_id)) in price_index
    ]
    return _representative_unit_price(prices)


def _representative_unit_price(prices: list[int]) -> int | None:
    positive_prices = [price for price in prices if price > 0]
    if not positive_prices:
        return None
    return Counter(positive_prices).most_common(1)[0][0]


def _first_non_empty(values: Any) -> str | None:
    if not isinstance(values, list):
        return None
    for value in values:
        if isinstance(value, str) and value.strip():
            return value
    return None


def _date_time_bounds(target_date: date) -> tuple[datetime, datetime]:
    start = datetime.combine(target_date, time.min)
    return start, start + timedelta(days=1)


def _fetch_affiliate_conversion_totals(repo: ConsoleRepository, target_date: date) -> dict[str, int]:
    if not repo._table_exists("conversion_raw"):
        return {}
    target_start, target_end = _date_time_bounds(target_date)
    rows = repo.fetch_all(
        """
        SELECT user_id, COUNT(*) AS total_conversions
        FROM conversion_raw
        WHERE conversion_time >= :target_start
          AND conversion_time < :target_end
          AND user_id IS NOT NULL
        GROUP BY user_id
        """,
        {"target_start": target_start, "target_end": target_end},
    )
    return {str(row["user_id"]): int(row["total_conversions"] or 0) for row in rows}


def _fetch_entity_transactions(
    repo: ConsoleRepository,
    target_date: date,
    ipaddress: str,
    useragent: str,
) -> list[dict[str, Any]]:
    if not repo._table_exists("conversion_raw"):
        return []
    target_start, target_end = _date_time_bounds(target_date)
    return repo.fetch_all(
        """
        SELECT
            c.id AS transaction_id,
            c.conversion_time,
            c.state,
            c.raw_payload,
            c.user_id,
            COALESCE(u.name, c.user_id, :default_affiliate_name) AS affiliate_name,
            c.program_id,
            COALESCE(p.name, c.program_id, :default_outcome_type) AS promotion_name
        FROM conversion_raw c
        LEFT JOIN master_user u
          ON u.id = c.user_id
        LEFT JOIN master_promotion p
          ON p.id = c.program_id
        WHERE c.conversion_time >= :target_start
          AND c.conversion_time < :target_end
          AND c.entry_ipaddress = :ipaddress
          AND c.entry_useragent = :useragent
        ORDER BY c.conversion_time DESC
        """,
        {
            "target_start": target_start,
            "target_end": target_end,
            "ipaddress": ipaddress,
            "useragent": useragent,
            "default_affiliate_name": DEFAULT_AFFILIATE_NAME,
            "default_outcome_type": DEFAULT_OUTCOME_TYPE,
        },
    )


def _fetch_recent_affiliate_transactions(repo: ConsoleRepository, user_id: str) -> list[dict[str, Any]]:
    if not user_id or user_id == DEFAULT_AFFILIATE_ID or not repo._table_exists("conversion_raw"):
        return []
    return repo.fetch_all(
        """
        SELECT
            c.id AS transaction_id,
            c.conversion_time,
            c.state,
            c.raw_payload,
            c.user_id,
            COALESCE(u.name, c.user_id, :default_affiliate_name) AS affiliate_name,
            c.program_id,
            COALESCE(p.name, c.program_id, :default_outcome_type) AS promotion_name
        FROM conversion_raw c
        LEFT JOIN master_user u
          ON u.id = c.user_id
        LEFT JOIN master_promotion p
          ON p.id = c.program_id
        WHERE c.user_id = :user_id
        ORDER BY c.conversion_time DESC
        LIMIT 10
        """,
        {
            "user_id": user_id,
            "default_affiliate_name": DEFAULT_AFFILIATE_NAME,
            "default_outcome_type": DEFAULT_OUTCOME_TYPE,
        },
    )


def _build_affiliate_ranking(
    rows: list[dict[str, Any]],
    transaction_summary: dict[str, dict[str, Any]],
    affiliate_totals: dict[str, int],
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        summary = _resolve_alert_summary(row, transaction_summary.get(str(row["finding_key"])))
        affiliate_id = summary["affiliate_id"]
        if not affiliate_id or affiliate_id == DEFAULT_AFFILIATE_ID:
            continue
        state = grouped.setdefault(
            affiliate_id,
            {
                "affiliate_id": affiliate_id,
                "affiliate_name": summary["affiliate_name"],
                "alert_count": 0,
                "fraud_conversions": 0,
                "estimated_damage": 0,
            },
        )
        state["alert_count"] += 1
        state["fraud_conversions"] += summary["transaction_count"]
        state["estimated_damage"] += summary["reward_amount"]

    ranking = []
    for affiliate_id, values in grouped.items():
        total_conversions = affiliate_totals.get(affiliate_id, 0)
        fraud_rate = round((values["fraud_conversions"] / total_conversions) * 100, 1) if total_conversions else 0.0
        ranking.append(
            {
                "affiliate_id": affiliate_id,
                "affiliate_name": values["affiliate_name"],
                "fraud_rate": fraud_rate,
                "alert_count": values["alert_count"],
                "total_conversions": total_conversions,
                "estimated_damage": values["estimated_damage"],
            }
        )
    return sorted(
        ranking,
        key=lambda item: (item["fraud_rate"], item["estimated_damage"], item["alert_count"]),
        reverse=True,
    )


def _build_alert_item(row: dict[str, Any], transaction_summary: dict[str, Any] | None) -> dict[str, Any]:
    summary = _resolve_alert_summary(row, transaction_summary)
    raw_reasons = row.get("reasons_json") or []
    reasons = format_reasons(raw_reasons) if raw_reasons else []
    return {
        "finding_key": row["finding_key"],
        "detected_at": _iso(row.get("computed_at")) or _iso(row.get("last_time")),
        "affiliate_id": summary["affiliate_id"],
        "affiliate_name": summary["affiliate_name"],
        "outcome_type": summary["outcome_type"],
        "risk_score": row["risk_score"],
        "risk_level": row["risk_level"],
        "pattern": reasons[0] if reasons else "No pattern available",
        "status": row["review_status"],
        "reward_amount": summary["reward_amount"],
        "reward_amount_source": summary["reward_amount_source"],
        "reward_amount_is_estimated": summary["reward_amount_is_estimated"],
        "transaction_count": summary["transaction_count"],
    }


def _requires_summary_fallback(row: dict[str, Any]) -> bool:
    affiliate_ids = row.get("affiliate_ids_json") or []
    estimated_damage = row.get("estimated_damage_yen")
    return not affiliate_ids or estimated_damage is None


def _resolve_alert_summary(
    row: dict[str, Any],
    fallback_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    affiliate_id = _first_non_empty(row.get("affiliate_ids_json")) or (
        fallback_summary["affiliate_id"] if fallback_summary else DEFAULT_AFFILIATE_ID
    )
    affiliate_name = _first_non_empty(row.get("affiliate_names_json")) or (
        fallback_summary["affiliate_name"] if fallback_summary else DEFAULT_AFFILIATE_NAME
    )
    outcome_type = _first_non_empty(row.get("program_names_json")) or (
        fallback_summary["outcome_type"] if fallback_summary else DEFAULT_OUTCOME_TYPE
    )
    reward_amount = row.get("estimated_damage_yen")
    if reward_amount is None:
        reward_amount = fallback_summary["reward_amount"] if fallback_summary else 0
    reward_amount_source = normalize_reward_amount_source(
        row.get("damage_unit_price_source")
        or (fallback_summary.get("reward_amount_source") if fallback_summary else None)
    )

    return {
        "transaction_count": int(row.get("total_conversions") or (fallback_summary["transaction_count"] if fallback_summary else 0)),
        "reward_amount": int(reward_amount or 0),
        "reward_amount_source": reward_amount_source,
        "reward_amount_is_estimated": reward_amount_is_estimated(reward_amount_source),
        "latest_occurred_at": _iso(row.get("last_time")) or _iso(row.get("computed_at")),
        "affiliate_id": affiliate_id,
        "affiliate_name": affiliate_name,
        "outcome_type": outcome_type,
    }


def _present_transaction(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "transaction_id": row["transaction_id"],
        "occurred_at": _iso(row.get("conversion_time")),
        "outcome_type": row.get("promotion_name") or DEFAULT_OUTCOME_TYPE,
        "reward_amount": _reward_from_payload(row.get("raw_payload")),
        "state": row.get("state") or "unknown",
    }


def _summarize_transactions(rows: list[dict[str, Any]]) -> dict[str, Any]:
    reward_amount = 0
    affiliate_counts: Counter[str] = Counter()
    program_counts: Counter[str] = Counter()
    affiliate_names: dict[str, str] = {}

    for row in rows:
        reward_amount += _reward_from_payload(row.get("raw_payload"))
        user_id = row.get("user_id")
        if user_id:
            affiliate_counts[str(user_id)] += 1
            affiliate_names[str(user_id)] = row.get("affiliate_name") or str(user_id)
        promotion_name = row.get("promotion_name")
        if promotion_name:
            program_counts[str(promotion_name)] += 1

    affiliate_id = affiliate_counts.most_common(1)[0][0] if affiliate_counts else DEFAULT_AFFILIATE_ID
    affiliate_name = affiliate_names.get(affiliate_id, DEFAULT_AFFILIATE_NAME)
    outcome_type = program_counts.most_common(1)[0][0] if program_counts else DEFAULT_OUTCOME_TYPE
    latest_occurred_at = _iso(rows[0].get("conversion_time")) if rows else None

    return {
        "transaction_count": len(rows),
        "reward_amount": reward_amount,
        "reward_amount_source": "observed_transactions",
        "latest_occurred_at": latest_occurred_at,
        "affiliate_id": affiliate_id,
        "affiliate_name": affiliate_name,
        "outcome_type": outcome_type,
    }


def _reward_from_payload(raw_payload: Any) -> int:
    parsed = _parse_json(raw_payload)
    extracted = _extract_reward_value(parsed)
    if extracted is None:
        return DEFAULT_REWARD_YEN
    return extracted


def _extract_reward_value(value: Any) -> int | None:
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


def _coerce_int(value: Any) -> int | None:
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


def _deserialize_alert_row(row: dict[str, Any]) -> dict[str, Any]:
    parsed = dict(row)
    for key in (
        "reasons_json",
        "reasons_formatted_json",
        "metrics_json",
        "program_ids_json",
        "program_names_json",
        "affiliate_ids_json",
        "affiliate_names_json",
        "damage_evidence_json",
    ):
        parsed[key] = _parse_json(parsed.get(key))
    if isinstance(parsed.get("date"), str):
        parsed["date"] = parse_iso_date(parsed["date"])
    return parsed


def _parse_json(value: Any) -> Any:
    if value is None or isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)
