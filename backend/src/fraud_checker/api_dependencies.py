from __future__ import annotations

import hmac
import os
from dataclasses import dataclass

from fastapi import Header, HTTPException

from .runtime_guards import _env_truthy, current_env


@dataclass(frozen=True)
class AccessContext:
    token_source: str


@dataclass(frozen=True)
class ConsoleAccessContext:
    user_id: str
    email: str
    request_id: str
    token_source: str = "console_proxy"


def _matches_secret(token: str | None, expected: str | None) -> bool:
    return token is not None and expected is not None and hmac.compare_digest(token, expected)


def extract_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    if authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip() or None
    return None


def _resolve_protected_access_context(
    *,
    x_api_key: str | None,
    authorization: str | None,
) -> AccessContext:
    expected = os.getenv("FC_ADMIN_API_KEY")
    if not expected:
        allow_insecure = _env_truthy("FC_ALLOW_INSECURE_ADMIN")
        env = current_env()
        if allow_insecure or env in {"dev", "development", "local"}:
            return AccessContext(token_source="insecure_local")
        raise HTTPException(status_code=500, detail="FC_ADMIN_API_KEY is not configured")

    token = x_api_key or extract_bearer(authorization)
    if not _matches_secret(token, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")

    return AccessContext(token_source="x_api_key" if x_api_key else "bearer")


def require_protected_access(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    authorization: str | None = Header(None),
) -> None:
    _resolve_protected_access_context(x_api_key=x_api_key, authorization=authorization)


def get_protected_access_context(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    authorization: str | None = Header(None),
) -> AccessContext:
    return _resolve_protected_access_context(x_api_key=x_api_key, authorization=authorization)


def require_test_mode() -> None:
    env = current_env()
    if env != "test":
        raise HTTPException(status_code=404, detail="Not Found")


def require_test_key(x_test_key: str | None = Header(None, alias="X-Test-Key")) -> None:
    require_test_mode()
    expected = os.getenv("FC_E2E_TEST_KEY")
    if not expected:
        raise HTTPException(status_code=500, detail="FC_E2E_TEST_KEY is not configured")
    if not _matches_secret(x_test_key, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")


def _resolve_read_access_context(
    *,
    x_read_api_key: str | None,
    x_api_key: str | None,
    authorization: str | None,
) -> AccessContext:
    if not _env_truthy("FC_REQUIRE_READ_AUTH"):
        return AccessContext(token_source="public_read")

    expected_read = os.getenv("FC_READ_API_KEY")
    expected_protected = os.getenv("FC_ADMIN_API_KEY")
    if not expected_read and not expected_protected:
        raise HTTPException(
            status_code=500,
            detail="FC_READ_API_KEY or FC_ADMIN_API_KEY is not configured",
        )

    token = x_read_api_key or x_api_key or extract_bearer(authorization)
    matched_read = _matches_secret(token, expected_read)
    matched_protected = _matches_secret(token, expected_protected)
    if not matched_read and not matched_protected:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if x_read_api_key and matched_read:
        return AccessContext(token_source="x_read_api_key")

    return AccessContext(token_source="x_api_key" if x_api_key else "bearer")


def require_read_access(
    x_read_api_key: str | None = Header(None, alias="X-Read-API-Key"),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    authorization: str | None = Header(None),
) -> None:
    _resolve_read_access_context(
        x_read_api_key=x_read_api_key,
        x_api_key=x_api_key,
        authorization=authorization,
    )


def get_read_access_context(
    x_read_api_key: str | None = Header(None, alias="X-Read-API-Key"),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    authorization: str | None = Header(None),
) -> AccessContext:
    return _resolve_read_access_context(
        x_read_api_key=x_read_api_key,
        x_api_key=x_api_key,
        authorization=authorization,
    )


def _resolve_console_access_context(
    *,
    x_console_user_id: str | None,
    x_console_user_email: str | None,
    x_console_request_id: str | None,
    x_console_user_signature: str | None,
) -> ConsoleAccessContext:
    secret = os.getenv("FC_INTERNAL_PROXY_SECRET")
    if not secret:
        raise HTTPException(status_code=500, detail="FC_INTERNAL_PROXY_SECRET is not configured")

    user_id = (x_console_user_id or "").strip()
    email = (x_console_user_email or "").strip()
    request_id = (x_console_request_id or "").strip()
    signature = (x_console_user_signature or "").strip()

    if not user_id or not email or not request_id or not signature:
        raise HTTPException(status_code=401, detail="Unauthorized")

    expected_signature = hmac.new(
        secret.encode("utf-8"),
        f"{user_id}\n{email}\n{request_id}".encode("utf-8"),
        "sha256",
    ).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=401, detail="Unauthorized")

    return ConsoleAccessContext(
        user_id=user_id,
        email=email,
        request_id=request_id,
    )


def require_console_access(
    x_console_user_id: str | None = Header(None, alias="X-Console-User-Id"),
    x_console_user_email: str | None = Header(None, alias="X-Console-User-Email"),
    x_console_request_id: str | None = Header(None, alias="X-Console-Request-Id"),
    x_console_user_signature: str | None = Header(None, alias="X-Console-User-Signature"),
) -> None:
    _resolve_console_access_context(
        x_console_user_id=x_console_user_id,
        x_console_user_email=x_console_user_email,
        x_console_request_id=x_console_request_id,
        x_console_user_signature=x_console_user_signature,
    )


def get_console_access_context(
    x_console_user_id: str | None = Header(None, alias="X-Console-User-Id"),
    x_console_user_email: str | None = Header(None, alias="X-Console-User-Email"),
    x_console_request_id: str | None = Header(None, alias="X-Console-Request-Id"),
    x_console_user_signature: str | None = Header(None, alias="X-Console-User-Signature"),
) -> ConsoleAccessContext:
    return _resolve_console_access_context(
        x_console_user_id=x_console_user_id,
        x_console_user_email=x_console_user_email,
        x_console_request_id=x_console_request_id,
        x_console_user_signature=x_console_user_signature,
    )
