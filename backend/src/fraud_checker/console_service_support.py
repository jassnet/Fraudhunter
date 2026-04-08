from __future__ import annotations

import csv
import io
from datetime import date


def build_alert_csv(rows: list[dict], *, exported_at: str | None = None) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "finding_key",
            "detected_at",
            "affiliate_id",
            "affiliate_name",
            "outcome_type",
            "risk_score",
            "risk_level",
            "status",
            "reward_amount",
            "reward_amount_source",
            "reward_amount_is_estimated",
            "transaction_count",
            "pattern",
        ]
    )
    for row in rows:
        writer.writerow(
            [
                row.get("finding_key", ""),
                row.get("detected_at", ""),
                row.get("affiliate_id", ""),
                row.get("affiliate_name", ""),
                row.get("outcome_type", ""),
                row.get("risk_score", ""),
                row.get("risk_level", ""),
                row.get("status", ""),
                row.get("reward_amount", 0),
                row.get("reward_amount_source", ""),
                "true" if row.get("reward_amount_is_estimated") else "false",
                row.get("transaction_count", 0),
                row.get("pattern", ""),
            ]
        )
    if exported_at:
        writer.writerow([])
        writer.writerow(["exported_at", exported_at])
    return output.getvalue()


def normalize_reward_amount_source(source: str | None) -> str:
    if not source:
        return "unknown"
    return source


def reward_amount_is_estimated(source: str | None) -> bool:
    return normalize_reward_amount_source(source) not in {"program_observed", "observed_transactions"}


def date_to_filename_fragment(value: str | None) -> str:
    if not value:
        return "all"
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        return value
