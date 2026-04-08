from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from ..api_dependencies import require_admin, require_analyst_access
from ..api_models import ConsoleReviewRequest, ConsoleReviewResponse
from ..console_service_support import date_to_filename_fragment
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
    risk_level: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort: str = Query("risk_desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    try:
        return console_service.list_alerts(
            get_repository(),
            status=status,
            risk_level=risk_level,
            start_date=start_date,
            end_date=end_date,
            search=search,
            sort=sort,
            page=page,
            page_size=page_size,
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error getting console alerts")
        raise HTTPException(status_code=500, detail="アラート一覧の取得に失敗しました") from None


@router.get("/alerts/export", dependencies=[Depends(require_analyst_access)])
def export_alerts(
    status: Optional[str] = Query("unhandled"),
    risk_level: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort: str = Query("risk_desc"),
):
    try:
        csv_text = console_service.export_alerts_csv(
            get_repository(),
            status=status,
            risk_level=risk_level,
            start_date=start_date,
            end_date=end_date,
            search=search,
            sort=sort,
        )
        filename_date = date_to_filename_fragment(start_date or end_date)
        return Response(
            content=csv_text,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="fraud-alerts-{filename_date}.csv"',
            },
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error exporting console alerts")
        raise HTTPException(status_code=500, detail="CSV エクスポートに失敗しました") from None


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
