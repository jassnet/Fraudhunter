from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..api_models import SuspiciousResponse
from ..api_parsers import parse_iso_date
from ..api_presenters import (
    filter_findings_by_search,
    present_click_finding,
    present_conversion_finding,
)
from ..services import reporting, settings as settings_service
from ..services.jobs import get_repository
from ..suspicious import ConversionSuspiciousDetector, SuspiciousDetector

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/suspicious", tags=["suspicious"])


def _resolve_target_date(repo, table: str, target_date: Optional[str]) -> Optional[str]:
    if target_date:
        return target_date
    return reporting.get_latest_date(repo, table)


@router.get("/clicks", response_model=SuspiciousResponse)
def get_suspicious_clicks(
    target_date: Optional[str] = Query(None, alias="date"),
    limit: int = Query(500, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None, description="IP/UA/媒体名/案件名で検索"),
    include_names: bool = Query(True, description="媒体/案件名を含める"),
):
    try:
        repo = get_repository()
        resolved_date = _resolve_target_date(repo, "click_ipua_daily", target_date)
        if not resolved_date:
            return SuspiciousResponse(date="", data=[], total=0, limit=limit, offset=offset)

        target_date_obj = parse_iso_date(resolved_date)
        click_rules, _ = settings_service.build_rule_sets(repo)
        findings = SuspiciousDetector(repo, click_rules).find_for_date(target_date_obj)

        details_cache = {}
        if include_names and search:
            details_cache = repo.get_suspicious_click_details_bulk(
                target_date_obj,
                [(finding.ipaddress, finding.useragent) for finding in findings],
            )

        findings = filter_findings_by_search(findings, details_cache, search, include_names)
        total = len(findings)
        paginated = sorted(findings, key=lambda finding: finding.total_clicks, reverse=True)[offset : offset + limit]

        if include_names and not details_cache:
            details_cache = repo.get_suspicious_click_details_bulk(
                target_date_obj,
                [(finding.ipaddress, finding.useragent) for finding in paginated],
            )

        data = [
            present_click_finding(
                finding,
                include_names,
                details_cache.get((finding.ipaddress, finding.useragent), []),
            )
            for finding in paginated
        ]
        return SuspiciousResponse(
            date=target_date_obj.isoformat(),
            data=data,
            total=total,
            limit=limit,
            offset=offset,
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error getting suspicious clicks")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/conversions", response_model=SuspiciousResponse)
def get_suspicious_conversions(
    target_date: Optional[str] = Query(None, alias="date"),
    limit: int = Query(500, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None, description="IP/UA/媒体名/案件名で検索"),
    include_names: bool = Query(True, description="媒体/案件名を含める"),
):
    try:
        repo = get_repository()
        resolved_date = _resolve_target_date(repo, "conversion_ipua_daily", target_date)
        if not resolved_date:
            return SuspiciousResponse(date="", data=[], total=0, limit=limit, offset=offset)

        target_date_obj = parse_iso_date(resolved_date)
        _, conversion_rules = settings_service.build_rule_sets(repo)
        findings = ConversionSuspiciousDetector(repo, conversion_rules).find_for_date(target_date_obj)

        details_cache = {}
        if include_names and search:
            details_cache = repo.get_suspicious_conversion_details_bulk(
                target_date_obj,
                [(finding.ipaddress, finding.useragent) for finding in findings],
            )

        findings = filter_findings_by_search(findings, details_cache, search, include_names)
        total = len(findings)
        paginated = sorted(
            findings,
            key=lambda finding: finding.conversion_count,
            reverse=True,
        )[offset : offset + limit]

        if include_names and not details_cache:
            details_cache = repo.get_suspicious_conversion_details_bulk(
                target_date_obj,
                [(finding.ipaddress, finding.useragent) for finding in paginated],
            )

        data = [
            present_conversion_finding(
                finding,
                include_names,
                details_cache.get((finding.ipaddress, finding.useragent), []),
            )
            for finding in paginated
        ]
        return SuspiciousResponse(
            date=target_date_obj.isoformat(),
            data=data,
            total=total,
            limit=limit,
            offset=offset,
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error getting suspicious conversions")
        raise HTTPException(status_code=500, detail="Internal server error")
