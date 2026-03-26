from __future__ import annotations

from datetime import date

from fastapi import HTTPException


DATE_ERROR_DETAIL = "日付形式が不正です。YYYY-MM-DD を指定してください。"


def parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=DATE_ERROR_DETAIL) from exc
