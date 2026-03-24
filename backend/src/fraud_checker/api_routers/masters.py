from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from ..api_dependencies import require_admin, require_read_access
from ..api_models import IngestResponse
from ..services.jobs import (
    JOB_TYPE_MASTER_SYNC,
    JobConflictError,
    enqueue_job,
    get_repository,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["masters"])


@router.post("/sync/masters", response_model=IngestResponse, dependencies=[Depends(require_admin)])
def sync_masters(background_tasks: BackgroundTasks):
    try:
        job = enqueue_job(
            background_tasks=background_tasks,
            job_type=JOB_TYPE_MASTER_SYNC,
            params=None,
            start_message="マスタ同期を開始しました",
        )
    except JobConflictError:
        raise HTTPException(status_code=409, detail="Another job is already running")
    return IngestResponse(
        success=True,
        message="マスタ同期を開始しました",
        details={"job_id": job.id},
    )


@router.get("/masters/status", dependencies=[Depends(require_read_access)])
def get_masters_status():
    try:
        repo = get_repository()
        return repo.get_all_masters()
    except Exception:
        logger.exception("Error getting master status")
        raise HTTPException(status_code=500, detail="Internal server error")
