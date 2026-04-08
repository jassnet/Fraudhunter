"""FastAPI backend for Fraud Checker v2."""
from __future__ import annotations

import logging
import os
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
from .api_errors import error_code_for_status
from .env import load_env
from .logging_utils import log_event
from .rate_limit import RateLimitRule, SlidingWindowRateLimiter
from .runtime_guards import should_enable_docs, validate_runtime_guards

load_env()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s - %(message)s")
logger = logging.getLogger(__name__)
docs_enabled = should_enable_docs()
rate_limiter = SlidingWindowRateLimiter()

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


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _rate_limit_rule(request: Request) -> RateLimitRule | None:
    if not request.url.path.startswith("/api/"):
        return None
    if request.url.path.startswith("/api/health/public"):
        return RateLimitRule(limit=180, window_seconds=60)
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        return RateLimitRule(limit=30, window_seconds=60)
    return RateLimitRule(limit=120, window_seconds=60)


def _error_payload(detail: object, status_code: int) -> dict[str, object]:
    if isinstance(detail, dict) and "detail" in detail:
        return {
            "detail": detail["detail"],
            "error_code": detail.get("error_code") or error_code_for_status(status_code),
        }
    return {
        "detail": str(detail),
        "error_code": error_code_for_status(status_code),
    }


@app.on_event("startup")
def startup() -> None:
    validate_runtime_guards()
    log_event(logger, "api_startup_completed", docs_enabled=docs_enabled)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content=_error_payload(exc.detail, exc.status_code))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Request validation failed", "error_code": "VALIDATION_ERROR"},
    )


@app.middleware("http")
async def enforce_rate_limit(request: Request, call_next):
    rule = _rate_limit_rule(request)
    if rule is not None:
        allowed, retry_after = rate_limiter.allow(f"{_client_ip(request)}:{request.url.path}:{request.method}", rule)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests", "error_code": "RATE_LIMITED"},
                headers={"Retry-After": str(retry_after)},
            )
    return await call_next(request)


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
