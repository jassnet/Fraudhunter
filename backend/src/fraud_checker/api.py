"""FastAPI backend for Fraud Checker v2."""
from __future__ import annotations

import logging
import os
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api_routers import (
    console_router,
    health_router,
    jobs_router,
    masters_router,
    reporting_router,
    settings_router,
    suspicious_router,
    testdata_router,
)
from .env import load_env
from .logging_utils import log_event
from .runtime_guards import should_enable_docs, validate_runtime_guards

load_env()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s - %(message)s")
logger = logging.getLogger(__name__)
docs_enabled = should_enable_docs()

app = FastAPI(
    title="Fraud Checker API",
    description="Fraud monitoring API",
    version="2.0.0",
    docs_url="/docs" if docs_enabled else None,
    redoc_url=None,
    openapi_url="/openapi.json" if docs_enabled else None,
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


@app.on_event("startup")
def startup() -> None:
    validate_runtime_guards()
    log_event(logger, "api_startup_completed", docs_enabled=docs_enabled)


@app.middleware("http")
async def log_request_timing(request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    log_event(
        logger,
        "http_request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    return response

for router in (
    health_router,
    console_router,
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
