from __future__ import annotations

import os
from dataclasses import dataclass

from fastapi import Header, HTTPException

from .runtime_guards import current_env


def _env_truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class AccessContext:
    level: str
    token_source: str


def extract_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    if authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip() or None
    return None


def _resolve_admin_access_context(
    *,
    x_api_key: str | None,
    authorization: str | None,
) -> AccessContext:
    expected = os.getenv("FC_ADMIN_API_KEY")
    if not expected:
        allow_insecure = _env_truthy("FC_ALLOW_INSECURE_ADMIN")
        env = current_env()
        if allow_insecure or env in {"dev", "development", "local"}:
            return AccessContext(level="admin", token_source="insecure_local")
        raise HTTPException(status_code=500, detail="FC_ADMIN_API_KEY is not configured")

    token = x_api_key or extract_bearer(authorization)
    if token != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return AccessContext(
        level="admin",
        token_source="x_api_key" if x_api_key else "bearer",
    )


def require_admin(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    authorization: str | None = Header(None),
) -> None:
    _resolve_admin_access_context(x_api_key=x_api_key, authorization=authorization)


def get_admin_access_context(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    authorization: str | None = Header(None),
) -> AccessContext:
    return _resolve_admin_access_context(x_api_key=x_api_key, authorization=authorization)


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


def _resolve_analyst_access_context(
    *,
    x_read_api_key: str | None,
    x_api_key: str | None,
    authorization: str | None,
) -> AccessContext:
    if not _env_truthy("FC_REQUIRE_READ_AUTH"):
        return AccessContext(level="analyst", token_source="public_read")

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

    if x_read_api_key and expected_read and x_read_api_key == expected_read:
        return AccessContext(level="analyst", token_source="x_read_api_key")

    return AccessContext(
        level="admin" if expected_admin and token == expected_admin else "analyst",
        token_source="x_api_key" if x_api_key else "bearer",
    )


def require_analyst_access(
    x_read_api_key: str | None = Header(None, alias="X-Read-API-Key"),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    authorization: str | None = Header(None),
) -> None:
    _resolve_analyst_access_context(
        x_read_api_key=x_read_api_key,
        x_api_key=x_api_key,
        authorization=authorization,
    )


def get_analyst_access_context(
    x_read_api_key: str | None = Header(None, alias="X-Read-API-Key"),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    authorization: str | None = Header(None),
) -> AccessContext:
    return _resolve_analyst_access_context(
        x_read_api_key=x_read_api_key,
        x_api_key=x_api_key,
        authorization=authorization,
    )


def require_read_access(
    x_read_api_key: str | None = Header(None, alias="X-Read-API-Key"),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    authorization: str | None = Header(None),
) -> None:
    require_analyst_access(
        x_read_api_key=x_read_api_key,
        x_api_key=x_api_key,
        authorization=authorization,
    )
