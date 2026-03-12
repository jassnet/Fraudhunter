"""FastAPI backend for Fraud Checker v2."""
from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api_dependencies import extract_bearer as _extract_bearer
from .api_dependencies import require_admin, require_test_key, require_test_mode
from .api_presenters import calculate_risk_level, format_reasons
from .api_routers import (
    health_router,
    jobs_router,
    masters_router,
    reporting_router,
    settings_router,
    suspicious_router,
    testdata_router,
)
from .env import load_env
from .services import e2e_seed, reporting, settings as settings_service
from .services.jobs import (
    JobConflictError,
    enqueue_job,
    get_job_store,
    get_repository,
    run_click_ingestion,
    run_conversion_ingestion,
    run_master_sync,
    run_refresh,
)
from .suspicious import ConversionSuspiciousDetector, SuspiciousDetector

load_env()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s - %(message)s")

app = FastAPI(
    title="Fraud Checker API",
    description="Fraud detection API",
    version="2.0.0",
)

_cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "FC_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (
    health_router,
    reporting_router,
    suspicious_router,
    jobs_router,
    masters_router,
    settings_router,
    testdata_router,
):
    app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
