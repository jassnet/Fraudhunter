from __future__ import annotations

import csv
import io
from datetime import date


def build_alert_csv(rows: list[dict], *, exported_at: str | None = None) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "case_key",
            "latest_detected_at",
            "environment_date",
            "environment_ipaddress",
            "environment_useragent",
            "affected_affiliate_count",
            "affected_affiliates",
            "affected_program_count",
            "affected_programs",
            "risk_score",
            "risk_level",
            "status",
            "reward_amount",
            "reward_amount_source",
            "reward_amount_is_estimated",
            "transaction_count",
            "primary_reason",
        ]
    )
    for row in rows:
        writer.writerow(
            [
                row.get("case_key", ""),
                row.get("latest_detected_at", ""),
                (row.get("environment") or {}).get("date", ""),
                (row.get("environment") or {}).get("ipaddress", ""),
                (row.get("environment") or {}).get("useragent", ""),
                row.get("affected_affiliate_count", 0),
                ", ".join(
                    filter(
                        None,
                        [
                            item.get("name") or item.get("id")
                            for item in row.get("affected_affiliates", [])
                            if isinstance(item, dict)
                        ],
                    )
                ),
                row.get("affected_program_count", 0),
                ", ".join(
                    filter(
                        None,
                        [
                            item.get("name") or item.get("id")
                            for item in row.get("affected_programs", [])
                            if isinstance(item, dict)
                        ],
                    )
                ),
                row.get("risk_score", ""),
                row.get("risk_level", ""),
                row.get("status", ""),
                row.get("reward_amount", 0),
                row.get("reward_amount_source", ""),
                "true" if row.get("reward_amount_is_estimated") else "false",
                row.get("transaction_count", 0),
                row.get("primary_reason", ""),
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
