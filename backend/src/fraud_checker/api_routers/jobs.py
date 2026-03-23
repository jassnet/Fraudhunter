from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from ..api_dependencies import require_admin
from ..api_models import IngestRequest, IngestResponse, JobStatusResponse, RefreshRequest
from ..api_parsers import parse_iso_date
from ..api_presenters import build_job_status_response
from ..services.jobs import (
    JOB_TYPE_CLICK_INGEST,
    JOB_TYPE_CONVERSION_INGEST,
    JOB_TYPE_REFRESH,
    JobConflictError,
    enqueue_job,
    get_job_store,
)

router = APIRouter(prefix="/api", tags=["jobs"])


@router.post("/ingest/clicks", response_model=IngestResponse, dependencies=[Depends(require_admin)])
def ingest_clicks(request: IngestRequest, background_tasks: BackgroundTasks):
    parse_iso_date(request.date)
    try:
        job = enqueue_job(
            background_tasks=background_tasks,
            job_type=JOB_TYPE_CLICK_INGEST,
            params={"date": request.date},
            start_message=f"クリック取り込みを開始しました（{request.date}）",
        )
    except JobConflictError:
        raise HTTPException(status_code=409, detail="Another job is already running")
    return IngestResponse(
        success=True,
        message=f"クリック取り込みを開始しました（{request.date}）",
        details={"job_id": job.id},
    )


@router.post("/ingest/conversions", response_model=IngestResponse, dependencies=[Depends(require_admin)])
def ingest_conversions(request: IngestRequest, background_tasks: BackgroundTasks):
    parse_iso_date(request.date)
    try:
        job = enqueue_job(
            background_tasks=background_tasks,
            job_type=JOB_TYPE_CONVERSION_INGEST,
            params={"date": request.date},
            start_message=f"成果取り込みを開始しました（{request.date}）",
        )
    except JobConflictError:
        raise HTTPException(status_code=409, detail="Another job is already running")
    return IngestResponse(
        success=True,
        message=f"成果取り込みを開始しました（{request.date}）",
        details={"job_id": job.id},
    )


@router.post("/refresh", response_model=IngestResponse, dependencies=[Depends(require_admin)])
def refresh_data(request: RefreshRequest, background_tasks: BackgroundTasks):
    try:
        job = enqueue_job(
            background_tasks=background_tasks,
            job_type=JOB_TYPE_REFRESH,
            params={
                "hours": request.hours,
                "clicks": request.clicks,
                "conversions": request.conversions,
                "detect": request.detect,
            },
            start_message=f"直近{request.hours}時間の再取得を開始しました",
        )
    except JobConflictError:
        raise HTTPException(status_code=409, detail="Another job is already running")
    return IngestResponse(
        success=True,
        message=f"直近{request.hours}時間の再取得を開始しました",
        details={
            "job_id": job.id,
            "hours": request.hours,
            "clicks": request.clicks,
            "conversions": request.conversions,
        },
    )


@router.get("/job/status", response_model=JobStatusResponse)
def get_job_status():
    status = get_job_store().get()
    return build_job_status_response(status)
