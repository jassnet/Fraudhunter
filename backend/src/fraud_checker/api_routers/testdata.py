from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from ..api_dependencies import require_test_key
from ..api_models import TestDataResponse
from ..service_dependencies import get_repository
from ..services import e2e_seed

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/test", tags=["testdata"])


@router.post("/reset", response_model=TestDataResponse, dependencies=[Depends(require_test_key)])
def reset_test_data():
    try:
        details = e2e_seed.reset_all(get_repository())
        return TestDataResponse(
            success=True,
            message="テストデータの初期化が完了しました",
            details=details,
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error resetting E2E test data")
        raise HTTPException(status_code=500, detail="Internal server error") from None


@router.post("/seed/baseline", response_model=TestDataResponse, dependencies=[Depends(require_test_key)])
def seed_test_baseline():
    try:
        details = e2e_seed.seed_baseline(get_repository())
        return TestDataResponse(
            success=True,
            message="ベースラインのテストデータを投入しました",
            details=details,
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error seeding E2E baseline data")
        raise HTTPException(status_code=500, detail="Internal server error") from None
