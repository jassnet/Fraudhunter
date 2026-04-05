from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import date, datetime
from typing import Any

import sqlalchemy as sa

from ..api_parsers import parse_iso_date
from ..db import Base
from ..db import models as _db_models  # noqa: F401
from ..time_utils import now_local
from . import reporting

DEFAULT_REWARD_YEN = 3000
ALERT_REVIEW_STATUSES = {"unhandled", "investigating", "confirmed_fraud", "white"}
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


def get_dashboard(repo, target_date: str | None = None) -> dict[str, Any]:
    _ensure_review_schema(repo)
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
    transaction_summary = _fetch_alert_transaction_summary(repo, alert_rows)
    affiliate_totals = _fetch_affiliate_conversion_totals(repo, parse_iso_date(resolved_date))

    impacted_conversions = sum(item["transaction_count"] for item in transaction_summary.values())
    total_conversions = int(summary.get("stats", {}).get("conversions", {}).get("total", 0) or 0)
    fraud_rate = round((impacted_conversions / total_conversions) * 100, 1) if total_conversions else 0.0
    unhandled_alerts = sum(1 for row in alert_rows if row["review_status"] == "unhandled")
    estimated_damage = sum(item["reward_amount"] for item in transaction_summary.values())

    trend_source = reporting.get_daily_stats(repo, 14, resolved_date)
    trend = [
        {
            "date": item["date"],
            "alerts": int(item.get("fraud_findings", 0) or 0),
        }
        for item in trend_source
    ]

    ranking = _build_affiliate_ranking(alert_rows, transaction_summary, affiliate_totals)[:10]

    return {
        "date": resolved_date,
        "available_dates": available_dates,
        "kpis": {
            "fraud_rate": {"value": fraud_rate, "label": "全体フラウド率", "unit": "%"},
            "unhandled_alerts": {"value": unhandled_alerts, "label": "未対応アラート件数", "unit": "件"},
            "estimated_damage": {"value": estimated_damage, "label": "被害推定額", "unit": "円"},
        },
        "trend": trend,
        "ranking": ranking,
    }


def list_alerts(
    repo,
    *,
    status: str | None = "unhandled",
    start_date: str | None = None,
    end_date: str | None = None,
    sort: str = "risk_desc",
) -> dict[str, Any]:
    _ensure_review_schema(repo)
    resolved_start, resolved_end = _resolve_alert_window(repo, start_date, end_date)
    all_rows = _fetch_alert_rows(
        repo,
        start_date=resolved_start,
        end_date=resolved_end,
        status=None,
        sort=sort,
    )
    filtered_rows = [row for row in all_rows if status in (None, "", "all") or row["review_status"] == status]
    transaction_summary = _fetch_alert_transaction_summary(repo, filtered_rows)

    items = [_build_alert_item(row, transaction_summary.get(row["finding_key"])) for row in filtered_rows]
    status_counts = Counter(row["review_status"] for row in all_rows)

    return {
        "available_dates": reporting.get_available_dates(repo),
        "applied_filters": {
            "status": status or "all",
            "start_date": resolved_start,
            "end_date": resolved_end,
            "sort": sort,
        },
        "status_counts": {
            "unhandled": status_counts.get("unhandled", 0),
            "investigating": status_counts.get("investigating", 0),
            "confirmed_fraud": status_counts.get("confirmed_fraud", 0),
            "white": status_counts.get("white", 0),
        },
        "items": items,
        "total": len(items),
    }


def get_alert_detail(repo, finding_key: str) -> dict[str, Any] | None:
    _ensure_review_schema(repo)
    row = _fetch_alert_detail_row(repo, finding_key)
    if row is None:
        return None

    entity_transactions = _fetch_entity_transactions(
        repo,
        row["date"],
        row["user_id"],
        row["media_id"],
        row["promotion_id"],
    )
    recent_transactions = _fetch_recent_affiliate_transactions(repo, row["user_id"])

    summary = _summarize_transactions(entity_transactions)
    reasons = row.get("reasons_formatted_json") or row.get("reasons_json") or []

    return {
        "finding_key": row["finding_key"],
        "affiliate_id": row["user_id"],
        "affiliate_name": row["user_name"],
        "risk_score": row["risk_score"],
        "risk_level": row["risk_level"],
        "status": row["review_status"],
        "reward_amount": summary["reward_amount"],
        "detected_at": _iso(row.get("computed_at")),
        "outcome_type": _derive_outcome_type(row),
        "program_name": row.get("promotion_name"),
        "reasons": reasons,
        "transactions": [_present_transaction(item) for item in recent_transactions],
        "actions": ["confirmed_fraud", "white", "investigating"],
    }


def apply_review_action(repo, finding_keys: list[str], status: str) -> dict[str, Any]:
    if status not in ALERT_REVIEW_STATUSES:
        raise ValueError(f"Unsupported review status: {status}")

    unique_keys = sorted({value for value in finding_keys if value})
    if not unique_keys:
        return {"updated_count": 0, "status": status}

    _ensure_review_schema(repo)
    now = now_local()
    statement = sa.text(
        """
        INSERT INTO fraud_alert_reviews (finding_key, review_status, updated_at)
        VALUES (:finding_key, :review_status, :updated_at)
        ON CONFLICT (finding_key)
        DO UPDATE SET
            review_status = excluded.review_status,
            updated_at = excluded.updated_at
        """
    )

    with repo.engine.begin() as conn:
        for finding_key in unique_keys:
            conn.execute(
                statement,
                {
                    "finding_key": finding_key,
                    "review_status": status,
                    "updated_at": now,
                },
            )

    return {"updated_count": len(unique_keys), "status": status}


def _resolve_alert_window(
    repo,
    start_date: str | None,
    end_date: str | None,
) -> tuple[str | None, str | None]:
    if start_date and end_date:
        return start_date, end_date
    if start_date:
        return start_date, start_date
    if end_date:
        return end_date, end_date

    latest_fraud_date = repo.fetch_one(
        """
        SELECT MAX(date) AS latest_date
        FROM fraud_findings
        WHERE is_current = TRUE
        """
    )
    value = latest_fraud_date.get("latest_date") if latest_fraud_date else None
    if value is None:
        fallback = reporting.resolve_summary_date(repo, None)
        return fallback, fallback
    resolved = value.isoformat() if hasattr(value, "isoformat") else str(value)
    return resolved, resolved


def _fetch_alert_rows(
    repo,
    *,
    start_date: str | None,
    end_date: str | None,
    status: str | None,
    sort: str,
) -> list[dict[str, Any]]:
    params: dict[str, object] = {}
    conditions = ["f.is_current = TRUE"]
    review_status_sql = "COALESCE(r.review_status, 'unhandled')"

    if start_date:
        params["start_date"] = parse_iso_date(start_date)
        conditions.append("f.date >= :start_date")
    if end_date:
        params["end_date"] = parse_iso_date(end_date)
        conditions.append("f.date <= :end_date")
    if status and status != "all":
        params["review_status"] = status
        conditions.append(f"{review_status_sql} = :review_status")

    order_by = {
        "risk_desc": "f.risk_score DESC, f.computed_at DESC",
        "risk_asc": "f.risk_score ASC, f.computed_at DESC",
        "detected_desc": "f.computed_at DESC, f.risk_score DESC",
        "detected_asc": "f.computed_at ASC, f.risk_score DESC",
    }.get(sort, "f.risk_score DESC, f.computed_at DESC")

    rows = repo.fetch_all(
        f"""
        SELECT
            f.finding_key,
            f.date,
            f.user_id,
            COALESCE(f.user_name, f.user_id) AS user_name,
            f.media_id,
            COALESCE(f.media_name, f.media_id) AS media_name,
            f.promotion_id,
            COALESCE(f.promotion_name, f.promotion_id) AS promotion_name,
            f.risk_level,
            f.risk_score,
            f.reasons_json,
            f.reasons_formatted_json,
            f.metrics_json,
            f.primary_metric,
            f.first_time,
            f.last_time,
            f.computed_at,
            {review_status_sql} AS review_status
        FROM fraud_findings f
        LEFT JOIN fraud_alert_reviews r
          ON r.finding_key = f.finding_key
        WHERE {" AND ".join(conditions)}
        ORDER BY {order_by}, f.finding_key ASC
        """,
        params,
    )
    return [_deserialize_alert_row(row) for row in rows]


def _fetch_alert_detail_row(repo, finding_key: str) -> dict[str, Any] | None:
    rows = repo.fetch_all(
        """
        SELECT
            f.finding_key,
            f.date,
            f.user_id,
            COALESCE(f.user_name, f.user_id) AS user_name,
            f.media_id,
            COALESCE(f.media_name, f.media_id) AS media_name,
            f.promotion_id,
            COALESCE(f.promotion_name, f.promotion_id) AS promotion_name,
            f.risk_level,
            f.risk_score,
            f.reasons_json,
            f.reasons_formatted_json,
            f.metrics_json,
            f.primary_metric,
            f.first_time,
            f.last_time,
            f.computed_at,
            COALESCE(r.review_status, 'unhandled') AS review_status
        FROM fraud_findings f
        LEFT JOIN fraud_alert_reviews r
          ON r.finding_key = f.finding_key
        WHERE f.finding_key = :finding_key
          AND f.is_current = TRUE
        LIMIT 1
        """,
        {"finding_key": finding_key},
    )
    if not rows:
        return None
    return _deserialize_alert_row(rows[0])


def _fetch_alert_transaction_summary(repo, rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if not rows or not repo._table_exists("conversion_raw"):
        return {}

    keys = [
        (row["finding_key"], row["date"], row["user_id"], row["media_id"], row["promotion_id"])
        for row in rows
    ]
    placeholders = ", ".join(
        f"(:finding_key{idx}, :target_date{idx}, :user_id{idx}, :media_id{idx}, :promotion_id{idx})"
        for idx in range(len(keys))
    )
    params: dict[str, object] = {}
    for idx, (finding_key, target_date, user_id, media_id, promotion_id) in enumerate(keys):
        params[f"finding_key{idx}"] = finding_key
        params[f"target_date{idx}"] = target_date
        params[f"user_id{idx}"] = user_id
        params[f"media_id{idx}"] = media_id
        params[f"promotion_id{idx}"] = promotion_id

    rows = repo.fetch_all(
        f"""
        WITH target_entities AS (
            SELECT *
            FROM (VALUES {placeholders})
            AS t(finding_key, target_date, user_id, media_id, promotion_id)
        )
        SELECT
            t.finding_key,
            c.id AS transaction_id,
            c.conversion_time,
            c.state,
            c.raw_payload
        FROM target_entities t
        JOIN conversion_raw c
          ON CAST(c.conversion_time AS date) = t.target_date
         AND c.user_id = t.user_id
         AND c.media_id = t.media_id
         AND c.program_id = t.promotion_id
        ORDER BY c.conversion_time DESC
        """,
        params,
    )

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["finding_key"])].append(row)

    return {finding_key: _summarize_transactions(items) for finding_key, items in grouped.items()}


def _fetch_affiliate_conversion_totals(repo, target_date: date) -> dict[str, int]:
    if not repo._table_exists("conversion_raw"):
        return {}
    rows = repo.fetch_all(
        """
        SELECT user_id, COUNT(*) AS total_conversions
        FROM conversion_raw
        WHERE CAST(conversion_time AS date) = :target_date
          AND user_id IS NOT NULL
        GROUP BY user_id
        """,
        {"target_date": target_date},
    )
    return {str(row["user_id"]): int(row["total_conversions"] or 0) for row in rows}


def _fetch_entity_transactions(
    repo,
    target_date: date,
    user_id: str,
    media_id: str,
    promotion_id: str,
) -> list[dict[str, Any]]:
    if not repo._table_exists("conversion_raw"):
        return []
    return repo.fetch_all(
        """
        SELECT
            c.id AS transaction_id,
            c.conversion_time,
            c.state,
            c.raw_payload,
            c.program_id,
            COALESCE(p.name, c.program_id, '成果') AS promotion_name
        FROM conversion_raw c
        LEFT JOIN master_promotion p
          ON p.id = c.program_id
        WHERE CAST(c.conversion_time AS date) = :target_date
          AND c.user_id = :user_id
          AND c.media_id = :media_id
          AND c.program_id = :promotion_id
        ORDER BY c.conversion_time DESC
        """,
        {
            "target_date": target_date,
            "user_id": user_id,
            "media_id": media_id,
            "promotion_id": promotion_id,
        },
    )


def _fetch_recent_affiliate_transactions(repo, user_id: str) -> list[dict[str, Any]]:
    if not repo._table_exists("conversion_raw"):
        return []
    return repo.fetch_all(
        """
        SELECT
            c.id AS transaction_id,
            c.conversion_time,
            c.state,
            c.raw_payload,
            c.program_id,
            COALESCE(p.name, c.program_id, '成果') AS promotion_name
        FROM conversion_raw c
        LEFT JOIN master_promotion p
          ON p.id = c.program_id
        WHERE c.user_id = :user_id
        ORDER BY c.conversion_time DESC
        LIMIT 10
        """,
        {"user_id": user_id},
    )


def _build_affiliate_ranking(
    alert_rows: list[dict[str, Any]],
    transaction_summary: dict[str, dict[str, Any]],
    affiliate_totals: dict[str, int],
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in alert_rows:
        affiliate_id = row["user_id"]
        state = grouped.setdefault(
            affiliate_id,
            {
                "affiliate_id": affiliate_id,
                "affiliate_name": row["user_name"],
                "alert_count": 0,
                "fraud_conversions": 0,
                "estimated_damage": 0,
            },
        )
        summary = transaction_summary.get(row["finding_key"], {"transaction_count": 0, "reward_amount": 0})
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
    summary = transaction_summary or {"transaction_count": 0, "reward_amount": 0, "latest_occurred_at": None}
    reasons = row.get("reasons_formatted_json") or row.get("reasons_json") or []
    return {
        "finding_key": row["finding_key"],
        "detected_at": _iso(row.get("computed_at")) or _iso(row.get("last_time")),
        "affiliate_id": row["user_id"],
        "affiliate_name": row["user_name"],
        "outcome_type": _derive_outcome_type(row),
        "risk_score": row["risk_score"],
        "risk_level": row["risk_level"],
        "pattern": reasons[0] if reasons else "不正パターンあり",
        "status": row["review_status"],
        "reward_amount": summary["reward_amount"],
        "transaction_count": summary["transaction_count"],
    }


def _present_transaction(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "transaction_id": row["transaction_id"],
        "occurred_at": _iso(row.get("conversion_time")),
        "outcome_type": row.get("promotion_name") or "成果",
        "reward_amount": _reward_from_payload(row.get("raw_payload")),
        "state": row.get("state") or "unknown",
    }


def _summarize_transactions(rows: list[dict[str, Any]]) -> dict[str, Any]:
    reward_amount = 0
    for row in rows:
        reward_amount += _reward_from_payload(row.get("raw_payload"))
    return {
        "transaction_count": len(rows),
        "reward_amount": reward_amount,
        "latest_occurred_at": _iso(rows[0].get("conversion_time")) if rows else None,
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


def _derive_outcome_type(row: dict[str, Any]) -> str:
    return row.get("promotion_name") or "成果"


def _deserialize_alert_row(row: dict[str, Any]) -> dict[str, Any]:
    parsed = dict(row)
    for key in ("reasons_json", "reasons_formatted_json", "metrics_json"):
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


def _ensure_review_schema(repo) -> None:
    Base.metadata.create_all(
        repo.engine,
        tables=[Base.metadata.tables["fraud_alert_reviews"]],
    )
