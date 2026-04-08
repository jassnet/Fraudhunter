from __future__ import annotations

import hashlib
import logging
import time
from datetime import date, datetime
from typing import Iterable
from urllib.parse import urljoin

import requests

from .models import ClickLog, ConversionLog
from .time_utils import parse_datetime

logger = logging.getLogger(__name__)


class AcsHttpClient:
    def __init__(
        self,
        base_url: str,
        access_key: str,
        secret_key: str,
        *,
        endpoint_path: str = "track_log/search",
        session: requests.Session | None = None,
        timeout: int = 30,
        retry_attempts: int = 3,
        retry_backoff_seconds: float = 0.25,
    ):
        self.base_url = base_url.rstrip("/") + "/"
        self.session = session or requests.Session()
        self.token = f"{access_key}:{secret_key}"
        self.endpoint_path = endpoint_path.lstrip("/")
        self.timeout = timeout
        self.retry_attempts = max(1, retry_attempts)
        self.retry_backoff_seconds = max(0.0, retry_backoff_seconds)

    def fetch_click_logs(self, target_date: date, page: int, limit: int) -> Iterable[ClickLog]:
        records = self._fetch_records(
            self.endpoint_path,
            self._between_date_params(target_date, prefix="regist_unix", page=page, limit=limit),
        )
        return [self._to_click(record) for record in records]

    def fetch_conversion_logs(
        self,
        target_date: date,
        page: int,
        limit: int,
    ) -> Iterable[ConversionLog]:
        records = self._fetch_records(
            "action_log_raw/search",
            self._between_date_params(target_date, prefix="regist_unix", page=page, limit=limit),
        )
        return [self._to_conversion(record) for record in records]

    def fetch_click_logs_for_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        page: int,
        limit: int,
    ) -> Iterable[ClickLog]:
        records = self._fetch_records(
            self.endpoint_path,
            self._between_range_params(start_time.date(), end_time.date(), prefix="regist_unix", page=page, limit=limit),
        )
        return [self._to_click(record) for record in records]

    def fetch_conversion_logs_for_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        page: int,
        limit: int,
    ) -> Iterable[ConversionLog]:
        records = self._fetch_records(
            "action_log_raw/search",
            self._between_range_params(start_time.date(), end_time.date(), prefix="regist_unix", page=page, limit=limit),
        )
        return [self._to_conversion(record) for record in records]

    def fetch_media_master(self, page: int = 1, limit: int = 500) -> list[dict]:
        records = self._fetch_records("media/search", {"limit": limit, "offset": (page - 1) * limit})
        return [
            {
                "id": record.get("id", ""),
                "name": record.get("name", ""),
                "user": record.get("user"),
                "state": record.get("state"),
            }
            for record in records
        ]

    def fetch_promotion_master(self, page: int = 1, limit: int = 500) -> list[dict]:
        records = self._fetch_records("promotion/search", {"limit": limit, "offset": (page - 1) * limit})
        return [
            {
                "id": record.get("id", ""),
                "name": record.get("name", ""),
                "state": record.get("state"),
                "action_double_state": self._to_int(record.get("action_double_state")),
                "action_double_type_json": record.get("action_double_type"),
            }
            for record in records
        ]

    def fetch_user_master(self, page: int = 1, limit: int = 500) -> list[dict]:
        records = self._fetch_records("user/search", {"limit": limit, "offset": (page - 1) * limit})
        return [
            {
                "id": record.get("id", ""),
                "name": record.get("name", ""),
                "company": record.get("company"),
                "state": record.get("state"),
            }
            for record in records
        ]

    def fetch_all_media_master(self) -> list[dict]:
        return self._fetch_all_paged(self.fetch_media_master)

    def fetch_all_promotion_master(self) -> list[dict]:
        return self._fetch_all_paged(self.fetch_promotion_master)

    def fetch_all_user_master(self) -> list[dict]:
        return self._fetch_all_paged(self.fetch_user_master)

    def ping(self) -> dict[str, object]:
        started = time.perf_counter()
        self._request_json("media/search", {"limit": 1, "offset": 0})
        return {
            "ok": True,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        }

    def _fetch_all_paged(self, fetch_page) -> list[dict]:
        records: list[dict] = []
        page = 1
        while True:
            batch = fetch_page(page=page, limit=500)
            if not batch:
                break
            records.extend(batch)
            if len(batch) < 500:
                break
            page += 1
        return records

    def _fetch_records(self, endpoint_path: str, params: dict[str, object]) -> list[dict]:
        body = self._request_json(endpoint_path, params)
        records = body.get("records", [])
        if isinstance(records, list):
            return records
        if isinstance(records, dict):
            return [records]
        return []

    def _fetch_sum(self, endpoint_path: str, params: dict[str, object], key: str) -> int:
        body = self._request_json(endpoint_path, params)
        payload = body.get("sum") or {}
        return self._to_int(payload.get(key)) or 0

    def _request_json(self, endpoint_path: str, params: dict[str, object]) -> dict:
        url = urljoin(self.base_url, endpoint_path.lstrip("/"))
        logger.info("ACS request %s params=%s", url, params)
        last_error: Exception | None = None
        for attempt in range(1, self.retry_attempts + 1):
            try:
                response = self.session.get(
                    url,
                    headers={"X-Auth-Token": self.token},
                    params=params,
                    timeout=self.timeout,
                )
                if response.status_code != 200:
                    logger.error("ACS returned %s for %s: %s", response.status_code, response.url, response.text)
                    response.raise_for_status()
                try:
                    return response.json()
                except ValueError:
                    logger.error("ACS response was not JSON: %s", response.text)
                    raise
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                if attempt >= self.retry_attempts:
                    raise
                sleep_seconds = self.retry_backoff_seconds * (2 ** (attempt - 1))
                logger.warning(
                    "ACS request failed on attempt %s/%s, retrying in %.2fs: %s",
                    attempt,
                    self.retry_attempts,
                    sleep_seconds,
                    exc,
                )
                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)
        if last_error is not None:
            raise last_error
        raise RuntimeError("ACS request failed without an explicit error")

    @staticmethod
    def _between_date_params(
        target_date: date,
        *,
        prefix: str,
        page: int,
        limit: int,
    ) -> dict[str, object]:
        return AcsHttpClient._between_range_params(
            target_date,
            target_date,
            prefix=prefix,
            page=page,
            limit=limit,
        )

    @staticmethod
    def _between_range_params(
        start_date: date,
        end_date: date,
        *,
        prefix: str,
        page: int,
        limit: int,
    ) -> dict[str, object]:
        return {
            "limit": limit,
            "offset": (page - 1) * limit,
            prefix: "between_date",
            f"{prefix}_A_Y": start_date.year,
            f"{prefix}_A_M": start_date.month,
            f"{prefix}_A_D": start_date.day,
            f"{prefix}_B_Y": end_date.year,
            f"{prefix}_B_M": end_date.month,
            f"{prefix}_B_D": end_date.day,
        }

    def _to_click(self, record: dict) -> ClickLog:
        click_time_raw = (
            record.get("click_time")
            or record.get("access_time")
            or record.get("accessed_at")
            or record.get("regist_unix")
            or record.get("time")
            or record.get("created_at")
            or record.get("date_unix")
        )
        click_id = record.get("track_cid") or record.get("id")
        return ClickLog(
            click_id=click_id,
            click_time=self._parse_datetime(click_time_raw),
            media_id=record.get("media_id") or record.get("media") or record.get("mediaId") or "",
            program_id=record.get("program_id") or record.get("promotion") or record.get("programId") or "",
            ipaddress=record.get("ipaddress") or record.get("ip") or record.get("ip_address") or "",
            useragent=record.get("useragent") or record.get("ua") or record.get("user_agent") or "",
            referrer=record.get("referrer") or record.get("referer"),
            raw_payload=record,
        )

    def _to_conversion(self, record: dict) -> ConversionLog:
        conversion_time = self._parse_datetime(
            record.get("regist_unix") or record.get("regist_time") or record.get("created_at")
        )
        click_time_raw = record.get("click_unix") or record.get("click_time")
        return ConversionLog(
            conversion_id=record.get("id", ""),
            cid=record.get("check_log_raw") or record.get("cid"),
            conversion_time=conversion_time,
            click_time=self._parse_datetime(click_time_raw) if click_time_raw else None,
            media_id=record.get("media") or record.get("media_id") or "",
            program_id=record.get("promotion") or record.get("program_id") or "",
            user_id=record.get("user") or record.get("user_id"),
            postback_ipaddress=record.get("ipaddress") or record.get("ip"),
            postback_useragent=record.get("useragent") or record.get("ua"),
            entry_ipaddress=record.get("entry_ipaddress"),
            entry_useragent=record.get("entry_useragent"),
            state=str(record.get("state")) if record.get("state") is not None else None,
            raw_payload=record,
        )

    @staticmethod
    def _fallback_record_id(prefix: str, payload: dict) -> str:
        digest = hashlib.sha256(repr(sorted(payload.items())).encode("utf-8")).hexdigest()[:24]
        return f"{prefix}-{digest}"

    @staticmethod
    def _to_int(value: object) -> int | None:
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_datetime(value: object) -> datetime:
        return parse_datetime(value)
