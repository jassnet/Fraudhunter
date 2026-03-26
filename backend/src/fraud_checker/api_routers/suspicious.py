from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..api_dependencies import AccessContext, get_analyst_access_context, require_analyst_access
from ..api_models import SuspiciousResponse
from ..api_parsers import parse_iso_date
from ..api_presenters import (
    present_click_finding_record,
    present_conversion_finding_record,
)
from ..logging_utils import log_event
from ..services import lifecycle, reporting
from ..services.jobs import get_repository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/suspicious", tags=["suspicious"], dependencies=[Depends(require_analyst_access)])


def _resolve_target_date(repo, table: str, target_date: Optional[str]) -> Optional[str]:
    if target_date:
        return target_date
    return reporting.get_latest_date(repo, table)


def _load_click_details(repo, row: dict) -> list[dict]:
    detail_map = repo.get_suspicious_click_details_bulk(
        row["date"],
        [(row["ipaddress"], row["useragent"])],
    )
    return detail_map.get((row["ipaddress"], row["useragent"]), [])


def _load_conversion_details(repo, row: dict) -> list[dict]:
    detail_map = repo.get_suspicious_conversion_details_bulk(
        row["date"],
        [(row["ipaddress"], row["useragent"])],
    )
    return detail_map.get((row["ipaddress"], row["useragent"]), [])


@router.get("/clicks", response_model=SuspiciousResponse)
def get_suspicious_clicks(
    target_date: Optional[str] = Query(None, alias="date"),
    limit: int = Query(500, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None, description="IP/UA/媒体名/案件名で検索"),
    include_names: bool = Query(True, description="媒体/案件名を含める"),
    include_details: bool = Query(True, description="詳細行を含める"),
    mask_sensitive: bool = Query(True, description="IP/UA をマスク表示する"),
    risk_level: Optional[str] = Query(None, pattern="^(high|medium|low)$"),
    sort_by: str = Query("count", pattern="^(count|risk|latest)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
):
    try:
        repo = get_repository()
        resolved_date = _resolve_target_date(repo, "click_ipua_daily", target_date)
        if not resolved_date:
            return SuspiciousResponse(date="", data=[], total=0, limit=limit, offset=offset)

        target_date_obj = parse_iso_date(resolved_date)
        rows, total = repo.list_click_findings(
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
            details_cache = repo.get_suspicious_click_details_bulk(
                target_date_obj,
                [(row["ipaddress"], row["useragent"]) for row in rows],
            )

        data = [
            present_click_finding_record(
                row,
                (
                    details_cache.get((row["ipaddress"], row["useragent"]), [])
                    if include_details and include_names
                    else None
                ),
                mask_sensitive=mask_sensitive,
            )
            for row in rows
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
    include_details: bool = Query(True, description="詳細行を含める"),
    mask_sensitive: bool = Query(True, description="IP/UA をマスク表示する"),
    risk_level: Optional[str] = Query(None, pattern="^(high|medium|low)$"),
    sort_by: str = Query("count", pattern="^(count|risk|latest)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
):
    try:
        repo = get_repository()
        resolved_date = _resolve_target_date(repo, "conversion_ipua_daily", target_date)
        if not resolved_date:
            return SuspiciousResponse(date="", data=[], total=0, limit=limit, offset=offset)

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

        data = [
            present_conversion_finding_record(
                row,
                (
                    details_cache.get((row["ipaddress"], row["useragent"]), [])
                    if include_details and include_names
                    else None
                ),
                mask_sensitive=mask_sensitive,
            )
            for row in rows
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


@router.get("/clicks/{finding_key}")
def get_suspicious_click_detail(
    finding_key: str,
    include_names: bool = Query(True, description="媒体/案件名を含める"),
    include_details: bool = Query(True, description="詳細行を含める"),
    access_context: AccessContext = Depends(get_analyst_access_context),
):
    try:
        repo = get_repository()
        row = repo.get_click_finding_by_key(finding_key)
        if row is None:
            raise HTTPException(status_code=404, detail="Finding not found")

        evidence = lifecycle.describe_evidence_availability(row["date"])
        details = None
        if include_names and include_details and evidence["evidence_available"]:
            details = _load_click_details(repo, row)
        log_event(
            logger,
            "sensitive_detail_access",
            finding_key=finding_key,
            finding_type="click",
            access_level=access_context.level,
            token_source=access_context.token_source,
            include_names=include_names,
            include_details=include_details,
            evidence_status=evidence["evidence_status"],
            unmasked_access=bool(evidence["evidence_available"]),
        )
        return present_click_finding_record(
            row,
            details,
            mask_sensitive=not evidence["evidence_available"],
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error getting suspicious click detail")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/conversions/{finding_key}")
def get_suspicious_conversion_detail(
    finding_key: str,
    include_names: bool = Query(True, description="媒体/案件名を含める"),
    include_details: bool = Query(True, description="詳細行を含める"),
    access_context: AccessContext = Depends(get_analyst_access_context),
):
    try:
        repo = get_repository()
        row = repo.get_conversion_finding_by_key(finding_key)
        if row is None:
            raise HTTPException(status_code=404, detail="Finding not found")

        evidence = lifecycle.describe_evidence_availability(row["date"])
        details = None
        if include_names and include_details and evidence["evidence_available"]:
            details = _load_conversion_details(repo, row)
        log_event(
            logger,
            "sensitive_detail_access",
            finding_key=finding_key,
            finding_type="conversion",
            access_level=access_context.level,
            token_source=access_context.token_source,
            include_names=include_names,
            include_details=include_details,
            evidence_status=evidence["evidence_status"],
            unmasked_access=bool(evidence["evidence_available"]),
        )
        return present_conversion_finding_record(
            row,
            details,
            mask_sensitive=not evidence["evidence_available"],
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error getting suspicious conversion detail")
        raise HTTPException(status_code=500, detail="Internal server error")
