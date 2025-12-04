from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Iterable, Optional
from urllib.parse import urljoin

import requests

from .models import ClickLog

logger = logging.getLogger(__name__)


class AcsHttpClient:
    def __init__(
        self,
        base_url: str,
        access_key: str,
        secret_key: str,
        *,
        endpoint_path: str = "access_log/search",
        session: Optional[requests.Session] = None,
    ):
        # Normalize base URL to avoid double slashes when joining paths.
        self.base_url = base_url.rstrip("/") + "/"
        self.session = session or requests.Session()
        self.token = f"{access_key}:{secret_key}"
        self.endpoint_path = endpoint_path.lstrip("/")

    def fetch_click_logs(self, target_date: date, page: int, limit: int) -> Iterable[ClickLog]:
        url = urljoin(self.base_url, self.endpoint_path)
        offset = (page - 1) * limit
        params = {
            "limit": limit,
            "offset": offset,
            # Track Logの日付検索は regist_unix の between_date を推奨（仕様書に準拠）
            "regist_unix": "between_date",
            "regist_unix_A_Y": target_date.year,
            "regist_unix_A_M": target_date.month,
            "regist_unix_A_D": target_date.day,
            "regist_unix_B_Y": target_date.year,
            "regist_unix_B_M": target_date.month,
            "regist_unix_B_D": target_date.day,
        }
        logger.info("ACS request %s params=%s", url, params)
        response = self.session.get(
            url,
            headers={"X-Auth-Token": self.token},
            params=params,
            timeout=30,
        )

        if response.status_code != 200:
            # Bubble up with body to ease operational troubleshooting; retries are handled by caller.
            logger.error(
                "ACS returned %s for %s: %s", response.status_code, response.url, response.text
            )
            response.raise_for_status()

        try:
            body = response.json()
        except ValueError as exc:  # pragma: no cover - defensive guard
            logger.error("ACS response was not JSON: %s", response.text)
            raise

        records = body.get("records", [])
        logger.info("ACS response status=%s records=%s", response.status_code, len(records))
        if records:
            logger.debug("ACS first record sample=%s", records[0])
        return [self._to_click(record) for record in records]

    def _to_click(self, record: dict) -> ClickLog:
        click_time_raw = (
            record.get("click_time")
            or record.get("access_time")
            or record.get("accessed_at")
            or record.get("regist_unix")
            or record.get("time")
            or record.get("created_at", "")
        )
        click_time = self._parse_datetime(click_time_raw)
        return ClickLog(
            click_id=record.get("id"),
            click_time=click_time,
            media_id=record.get("media_id") or record.get("mediaId") or "",
            program_id=record.get("program_id") or record.get("programId") or "",
            ipaddress=record.get("ipaddress") or record.get("ip") or record.get("ip_address") or "",
            useragent=record.get("useragent")
            or record.get("ua")
            or record.get("user_agent")
            or "",
            referrer=record.get("referrer") or record.get("referer"),
            raw_payload=record,
        )

    @staticmethod
    def _parse_datetime(value) -> datetime:
        # Handles ISO8601, epoch seconds, or simple "%Y-%m-%d %H:%M:%S"
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value)
        if not value:
            return datetime.utcnow()
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except Exception:
                try:
                    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    # Try epoch seconds encoded as string
                    try:
                        return datetime.fromtimestamp(float(value))
                    except Exception:
                        pass
        # Last resort: now() to avoid crashes; record is still stored in raw_payload.
        return datetime.utcnow()
