from __future__ import annotations

import os

from fastapi import Header, HTTPException


def extract_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    if authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip() or None
    return None


def require_admin(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    authorization: str | None = Header(None),
) -> None:
    expected = os.getenv("FC_ADMIN_API_KEY")
    if not expected:
        allow_insecure = os.getenv("FC_ALLOW_INSECURE_ADMIN", "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        env = os.getenv("FC_ENV", "production").strip().lower()
        if allow_insecure or env in {"dev", "development", "local"}:
            return
        raise HTTPException(status_code=500, detail="FC_ADMIN_API_KEY is not configured")

    token = x_api_key or extract_bearer(authorization)
    if token != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def require_test_mode() -> None:
    env = os.getenv("FC_ENV", "production").strip().lower()
    if env != "test":
        raise HTTPException(status_code=404, detail="Not Found")


def require_test_key(x_test_key: str | None = Header(None, alias="X-Test-Key")) -> None:
    require_test_mode()
    expected = os.getenv("FC_E2E_TEST_KEY")
    if not expected:
        raise HTTPException(status_code=500, detail="FC_E2E_TEST_KEY is not configured")
    if x_test_key != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")
