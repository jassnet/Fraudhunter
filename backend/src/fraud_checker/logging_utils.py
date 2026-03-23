from __future__ import annotations

import json
import logging
import time
from contextlib import contextmanager
from typing import Iterator


def _normalize_fields(fields: dict) -> dict:
    normalized: dict[str, object] = {}
    for key, value in fields.items():
        if value is None:
            continue
        if hasattr(value, "isoformat"):
            normalized[key] = value.isoformat()
        else:
            normalized[key] = value
    return normalized


def log_event(logger: logging.Logger, event: str, **fields) -> None:
    payload = {"event": event, **_normalize_fields(fields)}
    logger.info(json.dumps(payload, ensure_ascii=False, sort_keys=True))


@contextmanager
def log_timed(logger: logging.Logger, event: str, **fields) -> Iterator[None]:
    started = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        log_event(logger, event, duration_ms=duration_ms, **fields)
