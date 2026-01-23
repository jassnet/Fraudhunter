from __future__ import annotations

import os
from datetime import datetime, date, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo

DEFAULT_TIMEZONE = "Asia/Tokyo"


def _timezone_name() -> str:
    raw = os.getenv("FRAUD_TIMEZONE", DEFAULT_TIMEZONE)
    name = raw.strip() if raw else DEFAULT_TIMEZONE
    return name or DEFAULT_TIMEZONE


@lru_cache(maxsize=8)
def _get_tz(name: str) -> ZoneInfo:
    return ZoneInfo(name)


def get_timezone() -> ZoneInfo:
    name = _timezone_name()
    try:
        return _get_tz(name)
    except Exception:
        try:
            return _get_tz(DEFAULT_TIMEZONE)
        except Exception:
            return timezone.utc


def now_local() -> datetime:
    return datetime.now(get_timezone()).replace(tzinfo=None)


def today_local() -> date:
    return datetime.now(get_timezone()).date()


def _normalize_epoch(value: float) -> float:
    # Treat values larger than ~10^10 as milliseconds.
    if value > 1e10:
        return value / 1000.0
    return value


def _parse_numeric(text: str) -> float | None:
    try:
        return float(text)
    except ValueError:
        return None


def parse_datetime(value) -> datetime:
    tz = get_timezone()

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value
        return value.astimezone(tz).replace(tzinfo=None)

    if isinstance(value, (int, float)):
        epoch = _normalize_epoch(float(value))
        return datetime.fromtimestamp(epoch, tz=timezone.utc).astimezone(tz).replace(tzinfo=None)

    if not value:
        return now_local()

    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return now_local()
        # Handle ISO8601 with trailing Z
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        numeric = _parse_numeric(raw)
        if numeric is not None:
            epoch = _normalize_epoch(numeric)
            return (
                datetime.fromtimestamp(epoch, tz=timezone.utc)
                .astimezone(tz)
                .replace(tzinfo=None)
            )
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
                try:
                    parsed = datetime.strptime(raw, fmt)
                    break
                except ValueError:
                    parsed = None
            if parsed is None:
                return now_local()
        if parsed.tzinfo is None:
            # Assume naive strings are already in local time.
            return parsed
        return parsed.astimezone(tz).replace(tzinfo=None)

    return now_local()
