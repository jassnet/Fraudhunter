from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from ..api_dependencies import require_admin, require_read_access
from ..api_models import IngestRequest, IngestResponse, JobStatusResponse, RefreshRequest
from ..api_parsers import parse_iso_date
from ..api_presenters import build_job_status_response
from ..services.jobs import (
    JobConflictError,
    enqueue_click_ingestion_job,
    enqueue_conversion_ingestion_job,
    enqueue_refresh_job,
    get_job_store,
)

router = APIRouter(prefix="/api", tags=["jobs"])


@router.post("/ingest/clicks", response_model=IngestResponse, dependencies=[Depends(require_admin)])
def ingest_clicks(request: IngestRequest, background_tasks: BackgroundTasks):
    target_date = parse_iso_date(request.date)
    try:
        job = enqueue_click_ingestion_job(target_date, background_tasks=background_tasks)
    except JobConflictError:
        raise HTTPException(status_code=409, detail="Another job is already running")
    return IngestResponse(
        success=True,
        message=f"クリック取り込みジョブを登録しました（{request.date}）",
        details={"job_id": job.id},
    )


@router.post("/ingest/conversions", response_model=IngestResponse, dependencies=[Depends(require_admin)])
def ingest_conversions(request: IngestRequest, background_tasks: BackgroundTasks):
    target_date = parse_iso_date(request.date)
    try:
        job = enqueue_conversion_ingestion_job(target_date, background_tasks=background_tasks)
    except JobConflictError:
        raise HTTPException(status_code=409, detail="Another job is already running")
    return IngestResponse(
        success=True,
        message=f"成果取り込みジョブを登録しました（{request.date}）",
        details={"job_id": job.id},
    )


@router.post("/refresh", response_model=IngestResponse, dependencies=[Depends(require_admin)])
def refresh_data(request: RefreshRequest, background_tasks: BackgroundTasks):
    try:
        job = enqueue_refresh_job(
            background_tasks=background_tasks,
            hours=request.hours,
            clicks=request.clicks,
            conversions=request.conversions,
            detect=request.detect,
        )
    except JobConflictError:
        raise HTTPException(status_code=409, detail="Another job is already running")
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


@router.get("/job/status", response_model=JobStatusResponse, dependencies=[Depends(require_read_access)])
def get_job_status():
    status = get_job_store().get()
    return build_job_status_response(status)
