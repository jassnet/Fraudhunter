from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..api_dependencies import AccessContext, get_analyst_access_context, require_analyst_access
from ..api_models import SuspiciousResponse
from ..logging_utils import log_event
from ..service_dependencies import get_repository
from ..services import suspicious as suspicious_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/suspicious", tags=["suspicious"], dependencies=[Depends(require_analyst_access)])


@router.get("/conversions", response_model=SuspiciousResponse)
def get_suspicious_conversions(
    target_date: Optional[str] = Query(None, alias="date"),
    limit: int = Query(500, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None, description="IP/UA/media/program search"),
    include_names: bool = Query(True, description="Include media/program names"),
    include_details: bool = Query(True, description="Include supporting details"),
    mask_sensitive: bool = Query(True, description="Mask IP/UA in list responses"),
    risk_level: Optional[str] = Query(None, pattern="^(high|medium|low)$"),
    sort_by: str = Query("count", pattern="^(count|risk|latest)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
):
    try:
        payload = suspicious_service.get_conversion_findings(
            get_repository(),
            target_date=target_date,
            limit=limit,
            offset=offset,
            search=search,
            risk_level=risk_level,
            sort_by=sort_by,
            sort_order=sort_order,
            include_names=include_names,
            include_details=include_details,
            mask_sensitive=mask_sensitive,
        )
        return SuspiciousResponse(**payload)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error getting suspicious conversions")
        raise HTTPException(status_code=500, detail="Internal server error") from None


@router.get("/conversions/{finding_key}")
def get_suspicious_conversion_detail(
    finding_key: str,
    include_names: bool = Query(True, description="Include media/program names"),
    include_details: bool = Query(True, description="Include supporting details"),
    access_context: AccessContext = Depends(get_analyst_access_context),
):
    try:
        result = suspicious_service.get_conversion_detail(
            get_repository(),
            finding_key=finding_key,
            include_names=include_names,
            include_details=include_details,
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Finding not found")
        log_event(
            logger,
            "sensitive_detail_access",
            finding_key=finding_key,
            finding_type="conversion",
            access_level=access_context.level,
            token_source=access_context.token_source,
            include_names=include_names,
            include_details=include_details,
            evidence_status=result.evidence_status,
            unmasked_access=result.unmasked_access,
        )
        return result.payload
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error getting suspicious conversion detail")
        raise HTTPException(status_code=500, detail="Internal server error") from None
