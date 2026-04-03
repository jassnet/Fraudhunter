from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..api_parsers import parse_iso_date
from ..api_presenters import present_fraud_finding_record
from . import lifecycle, reporting


@dataclass(frozen=True)
class FraudDetailResult:
    payload: dict
    evidence_status: str
    unmasked_access: bool


def get_fraud_findings(
    repo,
    *,
    target_date: Optional[str],
    limit: int,
    offset: int,
    search: Optional[str],
    risk_level: Optional[str],
    sort_by: str,
    sort_order: str,
) -> dict:
    resolved_date = target_date
    if not resolved_date:
        row = repo.fetch_one("SELECT MAX(date) AS last_date FROM fraud_findings WHERE is_current = TRUE")
        if row and row.get("last_date"):
            value = row["last_date"]
            resolved_date = value.isoformat() if hasattr(value, "isoformat") else str(value)
        else:
            resolved_date = reporting.resolve_summary_date(repo, None)
    if not resolved_date:
        return {"date": "", "data": [], "total": 0, "limit": limit, "offset": offset}
    target_date_obj = parse_iso_date(resolved_date)
    rows, total = repo.list_fraud_findings(
        target_date=target_date_obj,
        limit=limit,
        offset=offset,
        search=search,
        risk_level=risk_level,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return {
        "date": target_date_obj.isoformat(),
        "data": [present_fraud_finding_record(row) for row in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


def get_fraud_detail(repo, *, finding_key: str) -> FraudDetailResult | None:
    row = repo.get_fraud_finding_by_key(finding_key)
    if row is None:
        return None
    evidence = lifecycle.describe_evidence_availability(row["date"])
    return FraudDetailResult(
        payload=present_fraud_finding_record(row),
        evidence_status=evidence["evidence_status"],
        unmasked_access=bool(evidence["evidence_available"]),
    )
