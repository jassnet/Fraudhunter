from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from ..api_dependencies import require_admin
from ..api_models import IngestRequest, IngestResponse, JobStatusResponse, RefreshRequest
from ..api_parsers import parse_iso_date
from ..api_presenters import build_job_status_response
from ..services.jobs import (
    JobConflictError,
    enqueue_job,
    get_job_store,
    run_click_ingestion,
    run_conversion_ingestion,
    run_refresh,
)

router = APIRouter(prefix="/api", tags=["jobs"])


@router.post("/ingest/clicks", response_model=IngestResponse, dependencies=[Depends(require_admin)])
def ingest_clicks(request: IngestRequest, background_tasks: BackgroundTasks):
    target_date = parse_iso_date(request.date)
    try:
        enqueue_job(
            background_tasks=background_tasks,
            job_id=f"ingest_clicks_{request.date}",
            start_message=f"クリック取り込みを開始しました（{request.date}）",
            run_fn=lambda: run_click_ingestion(target_date),
        )
    except JobConflictError:
        raise HTTPException(status_code=409, detail="Another job is already running")
    return IngestResponse(
        success=True,
        message=f"クリック取り込みを開始しました（{request.date}）",
        details={"job_id": f"ingest_clicks_{request.date}"},
    )


@router.post("/ingest/conversions", response_model=IngestResponse, dependencies=[Depends(require_admin)])
def ingest_conversions(request: IngestRequest, background_tasks: BackgroundTasks):
    target_date = parse_iso_date(request.date)
    try:
        enqueue_job(
            background_tasks=background_tasks,
            job_id=f"ingest_conversions_{request.date}",
            start_message=f"成果取り込みを開始しました（{request.date}）",
            run_fn=lambda: run_conversion_ingestion(target_date),
        )
    except JobConflictError:
        raise HTTPException(status_code=409, detail="Another job is already running")
    return IngestResponse(
        success=True,
        message=f"成果取り込みを開始しました（{request.date}）",
        details={"job_id": f"ingest_conversions_{request.date}"},
    )


@router.post("/refresh", response_model=IngestResponse, dependencies=[Depends(require_admin)])
def refresh_data(request: RefreshRequest, background_tasks: BackgroundTasks):
    try:
        enqueue_job(
            background_tasks=background_tasks,
            job_id=f"refresh_{request.hours}h",
            start_message=f"直近{request.hours}時間の再取得を開始しました",
            run_fn=lambda: run_refresh(
                request.hours,
                request.clicks,
                request.conversions,
                request.detect,
            ),
        )
    except JobConflictError:
        raise HTTPException(status_code=409, detail="Another job is already running")
    return IngestResponse(
        success=True,
        message=f"直近{request.hours}時間の再取得を開始しました",
        details={"hours": request.hours, "clicks": request.clicks, "conversions": request.conversions},
    )


@router.get("/job/status", response_model=JobStatusResponse)
def get_job_status():
    status = get_job_store().get()
    return build_job_status_response(status)
