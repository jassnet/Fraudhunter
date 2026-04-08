from __future__ import annotations

from fastapi import HTTPException


def error_code_for_status(status_code: int) -> str:
    return {
        400: "BAD_REQUEST",
        401: "AUTH_FAILED",
        404: "NOT_FOUND",
        429: "RATE_LIMITED",
        500: "INTERNAL_ERROR",
        502: "UPSTREAM_FAILED",
    }.get(status_code, "UNKNOWN_ERROR")


def raise_api_error(status_code: int, detail: str, *, error_code: str | None = None) -> None:
    raise HTTPException(
        status_code=status_code,
        detail={
            "detail": detail,
            "error_code": error_code or error_code_for_status(status_code),
        },
    )
