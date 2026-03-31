from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..api_parsers import parse_iso_date
from ..api_presenters import present_conversion_finding_record
from . import lifecycle, reporting


@dataclass(frozen=True)
class SuspiciousDetailResult:
    payload: dict
    evidence_status: str
    unmasked_access: bool


def resolve_target_date(repo, table: str, target_date: Optional[str]) -> Optional[str]:
    if target_date:
        return target_date
    return reporting.get_latest_date(repo, table)


def get_conversion_findings(
    repo,
    *,
    target_date: Optional[str],
    limit: int,
    offset: int,
    search: Optional[str],
    risk_level: Optional[str],
    sort_by: str,
    sort_order: str,
    include_names: bool,
    include_details: bool,
    mask_sensitive: bool,
) -> dict:
    resolved_date = resolve_target_date(repo, "conversion_ipua_daily", target_date)
    if not resolved_date:
        return {"date": "", "data": [], "total": 0, "limit": limit, "offset": offset}

    target_date_obj = parse_iso_date(resolved_date)
    rows, total = repo.list_conversion_findings(
        target_date=target_date_obj,
        limit=limit,
        offset=offset,
        search=search,
        risk_level=risk_level,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    details_cache = {}
    if include_details and include_names and rows:
        details_cache = repo.get_suspicious_conversion_details_bulk(
            target_date_obj,
            [(row["ipaddress"], row["useragent"]) for row in rows],
        )
    return {
        "date": target_date_obj.isoformat(),
        "data": [
            present_conversion_finding_record(
                row,
                details_cache.get((row["ipaddress"], row["useragent"]), [])
                if include_details and include_names
                else None,
                mask_sensitive=mask_sensitive,
            )
            for row in rows
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


def get_conversion_detail(
    repo,
    *,
    finding_key: str,
    include_names: bool,
    include_details: bool,
) -> SuspiciousDetailResult | None:
    row = repo.get_conversion_finding_by_key(finding_key)
    if row is None:
        return None
    evidence = lifecycle.describe_evidence_availability(row["date"])
    details = None
    if include_names and include_details and evidence["evidence_available"]:
        detail_map = repo.get_suspicious_conversion_details_bulk(
            row["date"],
            [(row["ipaddress"], row["useragent"])],
        )
        details = detail_map.get((row["ipaddress"], row["useragent"]), [])
    payload = present_conversion_finding_record(
        row,
        details,
        mask_sensitive=not evidence["evidence_available"],
    )
    return SuspiciousDetailResult(
        payload=payload,
        evidence_status=evidence["evidence_status"],
        unmasked_access=bool(evidence["evidence_available"]),
    )
