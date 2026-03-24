from __future__ import annotations

import os

from fastapi import Header, HTTPException

from .runtime_guards import current_env


def _env_truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


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
        allow_insecure = _env_truthy("FC_ALLOW_INSECURE_ADMIN")
        env = current_env()
        if allow_insecure or env in {"dev", "development", "local"}:
            return
        raise HTTPException(status_code=500, detail="FC_ADMIN_API_KEY is not configured")

    token = x_api_key or extract_bearer(authorization)
    if token != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def require_test_mode() -> None:
    env = current_env()
    if env != "test":
        raise HTTPException(status_code=404, detail="Not Found")


def require_test_key(x_test_key: str | None = Header(None, alias="X-Test-Key")) -> None:
    require_test_mode()
    expected = os.getenv("FC_E2E_TEST_KEY")
    if not expected:
        raise HTTPException(status_code=500, detail="FC_E2E_TEST_KEY is not configured")
    if x_test_key != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def require_read_access(
    x_read_api_key: str | None = Header(None, alias="X-Read-API-Key"),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    authorization: str | None = Header(None),
) -> None:
    if not _env_truthy("FC_REQUIRE_READ_AUTH"):
        return

    expected_read = os.getenv("FC_READ_API_KEY")
    expected_admin = os.getenv("FC_ADMIN_API_KEY")
    if not expected_read and not expected_admin:
        raise HTTPException(
            status_code=500,
            detail="FC_READ_API_KEY or FC_ADMIN_API_KEY is not configured",
        )

    token = x_read_api_key or x_api_key or extract_bearer(authorization)
    allowed = {value for value in (expected_read, expected_admin) if value}
    if token not in allowed:
        raise HTTPException(status_code=401, detail="Unauthorized")
