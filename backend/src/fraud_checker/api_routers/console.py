from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..api_dependencies import require_admin, require_analyst_access
from ..api_models import ConsoleReviewRequest, ConsoleReviewResponse
from ..service_dependencies import get_repository
from ..services import console as console_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/console", tags=["console"])


@router.get("/dashboard", dependencies=[Depends(require_analyst_access)])
def get_dashboard(target_date: Optional[str] = Query(None)):
    try:
        return console_service.get_dashboard(get_repository(), target_date=target_date)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error getting console dashboard")
        raise HTTPException(status_code=500, detail="ダッシュボードの取得に失敗しました") from None


@router.get("/alerts", dependencies=[Depends(require_analyst_access)])
def get_alerts(
    status: Optional[str] = Query("unhandled"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    sort: str = Query("risk_desc"),
):
    try:
        return console_service.list_alerts(
            get_repository(),
            status=status,
            start_date=start_date,
            end_date=end_date,
            sort=sort,
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error getting console alerts")
        raise HTTPException(status_code=500, detail="アラート一覧の取得に失敗しました") from None


@router.get("/alerts/{finding_key}", dependencies=[Depends(require_analyst_access)])
def get_alert_detail(finding_key: str):
    try:
        result = console_service.get_alert_detail(get_repository(), finding_key)
        if result is None:
            raise HTTPException(status_code=404, detail="アラートが見つかりません")
        return result
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error getting console alert detail")
        raise HTTPException(status_code=500, detail="アラート詳細の取得に失敗しました") from None


@router.post("/alerts/review", response_model=ConsoleReviewResponse, dependencies=[Depends(require_admin)])
def review_alerts(request: ConsoleReviewRequest):
    try:
        payload = console_service.apply_review_action(
            get_repository(),
            request.finding_keys,
            request.status,
        )
        return ConsoleReviewResponse(**payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error reviewing console alerts")
        raise HTTPException(status_code=500, detail="アラート更新に失敗しました") from None
