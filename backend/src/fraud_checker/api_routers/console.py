from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response

from ..api_dependencies import (
    ConsoleAccessContext,
    get_console_access_context,
    require_console_admin_access,
    require_console_analyst_access,
)
from ..api_models import ConsoleReviewRequest, ConsoleReviewResponse, IngestResponse, RefreshRequest
from ..console_service_support import date_to_filename_fragment
from ..service_dependencies import get_job_store, get_repository
from ..services import console as console_service
from ..services.jobs import JobConflictError, enqueue_master_sync_job, enqueue_refresh_job

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/console", tags=["console"])


@router.get("/dashboard", dependencies=[Depends(require_console_analyst_access)])
def get_dashboard(target_date: Optional[str] = Query(None)):
    try:
        return console_service.get_dashboard(get_repository(), target_date=target_date)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error getting console dashboard")
        raise HTTPException(status_code=500, detail="ダッシュボードの取得に失敗しました") from None


@router.get("/alerts", dependencies=[Depends(require_console_analyst_access)])
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


@router.get("/alerts/export", dependencies=[Depends(require_console_analyst_access)])
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


@router.get("/alerts/{finding_key}", dependencies=[Depends(require_console_analyst_access)])
def get_alert_detail(
    finding_key: str,
    access_context: ConsoleAccessContext = Depends(get_console_access_context),
):
    try:
        result = console_service.get_alert_detail(
            get_repository(),
            finding_key,
            access_context=access_context,
        )
        if result is None:
            raise HTTPException(status_code=404, detail="アラートが見つかりません")
        return result
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error getting console alert detail")
        raise HTTPException(status_code=500, detail="アラート詳細の取得に失敗しました") from None


@router.post(
    "/alerts/review",
    response_model=ConsoleReviewResponse,
    dependencies=[Depends(require_console_admin_access)],
)
def review_alerts(
    request: ConsoleReviewRequest,
    access_context: ConsoleAccessContext = Depends(get_console_access_context),
):
    try:
        payload = console_service.apply_review_action(
            get_repository(),
            request.finding_keys,
            request.status,
            access_context=access_context,
        )
        return ConsoleReviewResponse(**payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error reviewing console alerts")
        raise HTTPException(status_code=500, detail="アラート更新に失敗しました") from None


@router.post("/admin/refresh", response_model=IngestResponse, dependencies=[Depends(require_console_admin_access)])
def refresh_console_data(request: RefreshRequest, background_tasks: BackgroundTasks):
    try:
        job = enqueue_refresh_job(
            background_tasks=background_tasks,
            hours=request.hours,
            clicks=request.clicks,
            conversions=request.conversions,
            detect=request.detect,
        )
    except JobConflictError:
        raise HTTPException(status_code=409, detail="別のジョブが実行中です") from None
    return IngestResponse(
        success=True,
        message=f"直近{request.hours}時間の再取得ジョブを登録しました",
        details={
            "job_id": job.id,
            "hours": request.hours,
            "clicks": request.clicks,
            "conversions": request.conversions,
        },
    )


@router.post(
    "/admin/master-sync",
    response_model=IngestResponse,
    dependencies=[Depends(require_console_admin_access)],
)
def master_sync_console_data(background_tasks: BackgroundTasks):
    try:
        job = enqueue_master_sync_job(background_tasks=background_tasks)
    except JobConflictError:
        raise HTTPException(status_code=409, detail="別のジョブが実行中です") from None
    return IngestResponse(
        success=True,
        message="マスタ同期ジョブを登録しました",
        details={"job_id": job.id},
    )


@router.get("/job-status/{job_id}", dependencies=[Depends(require_console_analyst_access)])
def get_console_job_status(job_id: str):
    status = get_job_store().get_by_id(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail="ジョブが見つかりません")
    queue = get_job_store()._serialize_queue_metrics(get_job_store().get_queue_metrics())
    return {
        "status": "completed" if status.status == "succeeded" else status.status,
        "job_id": status.id,
        "message": status.message,
        "started_at": status.started_at.isoformat() if status.started_at else None,
        "completed_at": status.finished_at.isoformat() if status.finished_at else None,
        "result": status.result,
        "queue": queue,
    }
