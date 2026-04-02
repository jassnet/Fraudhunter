from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..api_dependencies import AccessContext, get_analyst_access_context, require_analyst_access
from ..api_models import SuspiciousResponse
from ..logging_utils import log_event
from ..service_dependencies import get_repository
from ..services import fraud as fraud_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/fraud", tags=["fraud"], dependencies=[Depends(require_analyst_access)])


@router.get("/findings", response_model=SuspiciousResponse)
def get_fraud_findings(
    target_date: Optional[str] = Query(None, alias="date"),
    limit: int = Query(500, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None, pattern="^(high|medium|low)$"),
    sort_by: str = Query("count", pattern="^(count|risk|latest)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
):
    try:
        payload = fraud_service.get_fraud_findings(
            get_repository(),
            target_date=target_date,
            limit=limit,
            offset=offset,
            search=search,
            risk_level=risk_level,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return SuspiciousResponse(**payload)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error getting fraud findings")
        raise HTTPException(status_code=500, detail="不正判定一覧の取得に失敗しました") from None


@router.get("/findings/{finding_key}")
def get_fraud_finding_detail(
    finding_key: str,
    access_context: AccessContext = Depends(get_analyst_access_context),
):
    try:
        result = fraud_service.get_fraud_detail(get_repository(), finding_key=finding_key)
        if result is None:
            raise HTTPException(status_code=404, detail="不正判定が見つかりません")
        log_event(
            logger,
            "sensitive_detail_access",
            finding_key=finding_key,
            finding_type="fraud",
            access_level=access_context.level,
            token_source=access_context.token_source,
            evidence_status=result.evidence_status,
            unmasked_access=result.unmasked_access,
        )
        return result.payload
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error getting fraud finding detail")
        raise HTTPException(status_code=500, detail="不正判定詳細の取得に失敗しました") from None
