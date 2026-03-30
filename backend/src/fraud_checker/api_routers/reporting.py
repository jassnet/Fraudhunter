from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from ..api_dependencies import require_analyst_access
from ..api_models import DailyStatsResponse, SummaryResponse
from ..service_dependencies import get_repository
from ..services import reporting

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["reporting"], dependencies=[Depends(require_analyst_access)])


@router.get("/summary", response_model=SummaryResponse)
def get_summary(target_date: Optional[str] = None):
    try:
        payload = reporting.get_summary(get_repository(), target_date)
        return SummaryResponse(**payload)
    except Exception:
        logger.exception("Error getting summary")
        raise HTTPException(status_code=500, detail="Internal server error") from None


@router.get("/stats/daily", response_model=DailyStatsResponse)
def get_daily_stats(limit: int = 30):
    try:
        data = reporting.get_daily_stats(get_repository(), limit)
        return DailyStatsResponse(data=data)
    except Exception:
        logger.exception("Error getting daily stats")
        raise HTTPException(status_code=500, detail="Internal server error") from None


@router.get("/dates")
def get_available_dates():
    try:
        return {"dates": reporting.get_available_dates(get_repository())}
    except Exception:
        logger.exception("Error getting dates")
        raise HTTPException(status_code=500, detail="Internal server error") from None
