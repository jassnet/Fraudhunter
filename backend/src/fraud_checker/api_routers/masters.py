from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from ..api_dependencies import require_admin, require_analyst_access
from ..api_models import IngestResponse
from ..service_dependencies import get_repository
from ..services.jobs import JobConflictError, enqueue_master_sync_job

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["masters"])


@router.post("/sync/masters", response_model=IngestResponse, dependencies=[Depends(require_admin)])
def sync_masters(background_tasks: BackgroundTasks):
    try:
        job = enqueue_master_sync_job(background_tasks=background_tasks)
    except JobConflictError:
        raise HTTPException(status_code=409, detail="Another job is already running") from None
    return IngestResponse(
        success=True,
        message="マスタ同期ジョブを登録しました",
        details={"job_id": job.id},
    )


@router.get("/masters/status", dependencies=[Depends(require_analyst_access)])
def get_masters_status():
    try:
        return get_repository().get_all_masters()
    except Exception:
        logger.exception("Error getting master status")
        raise HTTPException(status_code=500, detail="Internal server error") from None
