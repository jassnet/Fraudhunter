from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .env import load_env
from .suspicious import SuspiciousRuleSet

DEFAULT_PAGE_SIZE = 500
DEFAULT_CLICK_THRESHOLD = 50
DEFAULT_MEDIA_THRESHOLD = 3
DEFAULT_PROGRAM_THRESHOLD = 3
DEFAULT_BURST_CLICK_THRESHOLD = 20
DEFAULT_BURST_WINDOW_SECONDS = 600
DEFAULT_LOG_ENDPOINT = "track_log/search"
DEFAULT_BROWSER_ONLY = False
DEFAULT_EXCLUDE_DATACENTER_IP = False


@dataclass
class AcsSettings:
    base_url: str
    access_key: str
    secret_key: str
    page_size: int
    log_endpoint: str


def _require(value: Optional[str], name: str) -> str:
    if value is None or value.strip() == "":
        raise ValueError(f"{name} is required. Set it via environment or CLI.")
    return value.strip()


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer.") from exc


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _parse_token(token: str) -> tuple[str, str]:
    token = token.strip()
    if ":" not in token:
        raise ValueError("ACS_TOKEN must be in the form 'access_key:secret_key'.")
    access, secret = token.split(":", 1)
    return access, secret


def resolve_db_path(explicit: Optional[str]) -> Path:
    load_env()
    env_val = os.getenv("FRAUD_DB_PATH")
    value = explicit or env_val
    path_text = _require(value, "FRAUD_DB_PATH or --db")
    return Path(path_text)


def resolve_acs_settings(
    *,
    base_url: Optional[str],
    access_key: Optional[str],
    secret_key: Optional[str],
    page_size: Optional[int],
    log_endpoint: Optional[str] = None,
) -> AcsSettings:
    load_env()
    resolved_base_url = _require(base_url or os.getenv("ACS_BASE_URL"), "ACS_BASE_URL or --base-url")
    if not resolved_base_url.startswith("http"):
        raise ValueError("ACS_BASE_URL must be a full URL (e.g. https://acs.example.com).")

    resolved_access = access_key or os.getenv("ACS_ACCESS_KEY")
    resolved_secret = secret_key or os.getenv("ACS_SECRET_KEY")
    token = os.getenv("ACS_TOKEN")
    if (not resolved_access or not resolved_secret) and token:
        parsed_access, parsed_secret = _parse_token(token)
        resolved_access = resolved_access or parsed_access
        resolved_secret = resolved_secret or parsed_secret

    resolved_access = _require(
        resolved_access,
        "ACS_ACCESS_KEY or ACS_TOKEN or --access-key",
    )
    resolved_secret = _require(
        resolved_secret,
        "ACS_SECRET_KEY or ACS_TOKEN or --secret-key",
    )

    if page_size is not None:
        resolved_page_size = page_size
    else:
        resolved_page_size = _env_int("FRAUD_PAGE_SIZE", DEFAULT_PAGE_SIZE)
    if resolved_page_size <= 0:
        raise ValueError("Page size must be a positive integer.")

    endpoint = log_endpoint or os.getenv("ACS_LOG_ENDPOINT") or DEFAULT_LOG_ENDPOINT
    endpoint = endpoint.lstrip("/")  # urljoin tolerates leading slash, but keep consistent

    return AcsSettings(
        base_url=resolved_base_url.rstrip("/"),
        access_key=resolved_access,
        secret_key=resolved_secret,
        page_size=resolved_page_size,
        log_endpoint=endpoint,
    )


def resolve_store_raw(explicit: Optional[bool]) -> bool:
    load_env()
    env_default = _env_bool("FRAUD_STORE_RAW", False)
    if explicit is None:
        return env_default
    return explicit


def resolve_rules(
    *,
    click_threshold: Optional[int],
    media_threshold: Optional[int],
    program_threshold: Optional[int],
    burst_click_threshold: Optional[int],
    burst_window_seconds: Optional[int],
    browser_only: Optional[bool] = None,
    exclude_datacenter_ip: Optional[bool] = None,
) -> SuspiciousRuleSet:
    load_env()
    click = click_threshold if click_threshold is not None else _env_int(
        "FRAUD_CLICK_THRESHOLD", DEFAULT_CLICK_THRESHOLD
    )
    media = media_threshold if media_threshold is not None else _env_int(
        "FRAUD_MEDIA_THRESHOLD", DEFAULT_MEDIA_THRESHOLD
    )
    program = program_threshold if program_threshold is not None else _env_int(
        "FRAUD_PROGRAM_THRESHOLD", DEFAULT_PROGRAM_THRESHOLD
    )
    burst_clicks = (
        burst_click_threshold
        if burst_click_threshold is not None
        else _env_int("FRAUD_BURST_CLICK_THRESHOLD", DEFAULT_BURST_CLICK_THRESHOLD)
    )
    burst_window = (
        burst_window_seconds
        if burst_window_seconds is not None
        else _env_int("FRAUD_BURST_WINDOW_SECONDS", DEFAULT_BURST_WINDOW_SECONDS)
    )
    browser = (
        browser_only
        if browser_only is not None
        else _env_bool("FRAUD_BROWSER_ONLY", DEFAULT_BROWSER_ONLY)
    )
    exclude_dc = (
        exclude_datacenter_ip
        if exclude_datacenter_ip is not None
        else _env_bool("FRAUD_EXCLUDE_DATACENTER_IP", DEFAULT_EXCLUDE_DATACENTER_IP)
    )

    return SuspiciousRuleSet(
        click_threshold=click,
        media_threshold=media,
        program_threshold=program,
        burst_click_threshold=burst_clicks,
        burst_window_seconds=burst_window,
        browser_only=browser,
        exclude_datacenter_ip=exclude_dc,
    )
