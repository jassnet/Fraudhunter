from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Iterable, List, Optional, Tuple
from urllib.parse import urljoin

import requests

from .models import ClickLog, ConversionLog

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
        timeout: int = 30,
    ):
        # Normalize base URL to avoid double slashes when joining paths.
        self.base_url = base_url.rstrip("/") + "/"
        self.session = session or requests.Session()
        self.token = f"{access_key}:{secret_key}"
        self.endpoint_path = endpoint_path.lstrip("/")
        self.timeout = timeout

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
            timeout=self.timeout,
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
        # track_cid を優先（成果ログの check_log_raw と突合するため）
        # track_cid がない場合は id にフォールバック
        click_id = record.get("track_cid") or record.get("id")
        return ClickLog(
            click_id=click_id,
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

    def fetch_conversion_logs(
        self, target_date: date, page: int, limit: int
    ) -> Iterable[ConversionLog]:
        """
        成果ログ（action_log_raw）を取得する。
        ポストバック経由の成果を取得するためのメソッド。
        """
        url = urljoin(self.base_url, "action_log_raw/search")
        offset = (page - 1) * limit
        params = {
            "limit": limit,
            "offset": offset,
            # 成果発生日時（regist_unix）で検索
            "regist_unix": "between_date",
            "regist_unix_A_Y": target_date.year,
            "regist_unix_A_M": target_date.month,
            "regist_unix_A_D": target_date.day,
            "regist_unix_B_Y": target_date.year,
            "regist_unix_B_M": target_date.month,
            "regist_unix_B_D": target_date.day,
        }
        logger.info("ACS conversion request %s params=%s", url, params)
        response = self.session.get(
            url,
            headers={"X-Auth-Token": self.token},
            params=params,
            timeout=self.timeout,
        )

        if response.status_code != 200:
            logger.error(
                "ACS returned %s for %s: %s",
                response.status_code,
                response.url,
                response.text,
            )
            response.raise_for_status()

        try:
            body = response.json()
        except ValueError:
            logger.error("ACS response was not JSON: %s", response.text)
            raise

        records = body.get("records", [])
        logger.info(
            "ACS conversion response status=%s records=%s",
            response.status_code,
            len(records),
        )
        if records:
            logger.debug("ACS first conversion record sample=%s", records[0])
        return [self._to_conversion(record) for record in records]

    def _to_conversion(self, record: dict) -> ConversionLog:
        """APIレスポンスをConversionLogに変換"""
        # 成果発生日時
        regist_time_raw = (
            record.get("regist_unix")
            or record.get("regist_time")
            or record.get("created_at", "")
        )
        conversion_time = self._parse_datetime(regist_time_raw)

        # クリック日時（あれば）
        click_time_raw = record.get("click_unix") or record.get("click_time")
        click_time = self._parse_datetime(click_time_raw) if click_time_raw else None

        # cid（check_log_raw）: クリックIDへの参照（将来のクリックベース検知用に残置）
        cid = record.get("check_log_raw") or record.get("cid")

        return ConversionLog(
            conversion_id=record.get("id", ""),
            cid=cid,
            conversion_time=conversion_time,
            click_time=click_time,
            media_id=record.get("media") or record.get("media_id") or "",
            program_id=record.get("promotion") or record.get("program_id") or "",
            user_id=record.get("user") or record.get("user_id"),
            # ポストバック経由の場合、これらはポストバックサーバーのIP/UA
            postback_ipaddress=record.get("ipaddress") or record.get("ip"),
            postback_useragent=record.get("useragent") or record.get("ua"),
            # エントリー時（実ユーザー）のIP/UA - 成果ログから直接取得
            entry_ipaddress=record.get("entry_ipaddress"),
            entry_useragent=record.get("entry_useragent"),
            state=record.get("state"),
            raw_payload=record,
        )

    def fetch_click_logs_for_time_range(
        self, start_time: datetime, end_time: datetime, page: int, limit: int
    ) -> Iterable[ClickLog]:
        """
        時間範囲でクリックログを取得する。
        
        APIは日付単位なので、start_time〜end_timeにまたがる日付のデータを取得し、
        時間でフィルタリングして返す。
        """
        # 日付範囲を計算（最大2日にまたがる可能性）
        start_date = start_time.date()
        end_date = end_time.date()
        
        url = urljoin(self.base_url, self.endpoint_path)
        offset = (page - 1) * limit
        params = {
            "limit": limit,
            "offset": offset,
            "regist_unix": "between_date",
            "regist_unix_A_Y": start_date.year,
            "regist_unix_A_M": start_date.month,
            "regist_unix_A_D": start_date.day,
            "regist_unix_B_Y": end_date.year,
            "regist_unix_B_M": end_date.month,
            "regist_unix_B_D": end_date.day,
        }
        logger.info("ACS time range request %s params=%s", url, params)
        response = self.session.get(
            url,
            headers={"X-Auth-Token": self.token},
            params=params,
            timeout=self.timeout,
        )

        if response.status_code != 200:
            logger.error(
                "ACS returned %s for %s: %s", response.status_code, response.url, response.text
            )
            response.raise_for_status()

        try:
            body = response.json()
        except ValueError as exc:
            logger.error("ACS response was not JSON: %s", response.text)
            raise

        records = body.get("records", [])
        logger.info("ACS response status=%s records=%s", response.status_code, len(records))
        
        # 時間範囲でフィルタリング
        result = []
        for record in records:
            click = self._to_click(record)
            if start_time <= click.click_time <= end_time:
                result.append(click)
        
        logger.info("Filtered to %d records within time range", len(result))
        return result

    def fetch_conversion_logs_for_time_range(
        self, start_time: datetime, end_time: datetime, page: int, limit: int
    ) -> Iterable[ConversionLog]:
        """
        時間範囲で成果ログを取得する。
        """
        start_date = start_time.date()
        end_date = end_time.date()
        
        url = urljoin(self.base_url, "action_log_raw/search")
        offset = (page - 1) * limit
        params = {
            "limit": limit,
            "offset": offset,
            "regist_unix": "between_date",
            "regist_unix_A_Y": start_date.year,
            "regist_unix_A_M": start_date.month,
            "regist_unix_A_D": start_date.day,
            "regist_unix_B_Y": end_date.year,
            "regist_unix_B_M": end_date.month,
            "regist_unix_B_D": end_date.day,
        }
        logger.info("ACS conversion time range request %s params=%s", url, params)
        response = self.session.get(
            url,
            headers={"X-Auth-Token": self.token},
            params=params,
            timeout=self.timeout,
        )

        if response.status_code != 200:
            logger.error(
                "ACS returned %s for %s: %s",
                response.status_code,
                response.url,
                response.text,
            )
            response.raise_for_status()

        try:
            body = response.json()
        except ValueError:
            logger.error("ACS response was not JSON: %s", response.text)
            raise

        records = body.get("records", [])
        logger.info(
            "ACS conversion response status=%s records=%s",
            response.status_code,
            len(records),
        )
        
        # 時間範囲でフィルタリング
        result = []
        for record in records:
            conv = self._to_conversion(record)
            if start_time <= conv.conversion_time <= end_time:
                result.append(conv)
        
        logger.info("Filtered to %d conversions within time range", len(result))
        return result

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

    # ========== マスタデータ取得 ==========

    def fetch_media_master(self, page: int = 1, limit: int = 500) -> List[dict]:
        """媒体マスタを取得"""
        url = urljoin(self.base_url, "media/search")
        offset = (page - 1) * limit
        params = {"limit": limit, "offset": offset}
        
        logger.info("ACS media master request %s params=%s", url, params)
        response = self.session.get(
            url,
            headers={"X-Auth-Token": self.token},
            params=params,
            timeout=self.timeout,
        )

        if response.status_code != 200:
            logger.error("ACS returned %s: %s", response.status_code, response.text)
            response.raise_for_status()

        body = response.json()
        records = body.get("records", [])
        logger.info("ACS media master response: %d records", len(records))
        
        return [
            {
                "id": r.get("id", ""),
                "name": r.get("name", ""),
                "user": r.get("user"),
                "state": r.get("state"),
            }
            for r in records
        ]

    def fetch_promotion_master(self, page: int = 1, limit: int = 500) -> List[dict]:
        """案件マスタを取得"""
        url = urljoin(self.base_url, "promotion/search")
        offset = (page - 1) * limit
        params = {"limit": limit, "offset": offset}
        
        logger.info("ACS promotion master request %s params=%s", url, params)
        response = self.session.get(
            url,
            headers={"X-Auth-Token": self.token},
            params=params,
            timeout=self.timeout,
        )

        if response.status_code != 200:
            logger.error("ACS returned %s: %s", response.status_code, response.text)
            response.raise_for_status()

        body = response.json()
        records = body.get("records", [])
        logger.info("ACS promotion master response: %d records", len(records))
        
        return [
            {
                "id": r.get("id", ""),
                "name": r.get("name", ""),
                "state": r.get("state"),
            }
            for r in records
        ]

    def fetch_user_master(self, page: int = 1, limit: int = 500) -> List[dict]:
        """ユーザー（アフィリエイター）マスタを取得"""
        url = urljoin(self.base_url, "user/search")
        offset = (page - 1) * limit
        params = {"limit": limit, "offset": offset}
        
        logger.info("ACS user master request %s params=%s", url, params)
        response = self.session.get(
            url,
            headers={"X-Auth-Token": self.token},
            params=params,
            timeout=self.timeout,
        )

        if response.status_code != 200:
            logger.error("ACS returned %s: %s", response.status_code, response.text)
            response.raise_for_status()

        body = response.json()
        records = body.get("records", [])
        logger.info("ACS user master response: %d records", len(records))
        
        return [
            {
                "id": r.get("id", ""),
                "name": r.get("name", ""),
                "company": r.get("company"),
                "state": r.get("state"),
            }
            for r in records
        ]

    def fetch_all_media_master(self) -> List[dict]:
        """全媒体マスタを取得（ページング付き）"""
        all_media = []
        page = 1
        while True:
            batch = self.fetch_media_master(page=page, limit=500)
            if not batch:
                break
            all_media.extend(batch)
            if len(batch) < 500:
                break
            page += 1
        return all_media

    def fetch_all_promotion_master(self) -> List[dict]:
        """全案件マスタを取得（ページング付き）"""
        all_promos = []
        page = 1
        while True:
            batch = self.fetch_promotion_master(page=page, limit=500)
            if not batch:
                break
            all_promos.extend(batch)
            if len(batch) < 500:
                break
            page += 1
        return all_promos

    def fetch_all_user_master(self) -> List[dict]:
        """全ユーザーマスタを取得（ページング付き）"""
        all_users = []
        page = 1
        while True:
            batch = self.fetch_user_master(page=page, limit=500)
            if not batch:
                break
            all_users.extend(batch)
            if len(batch) < 500:
                break
            page += 1
        return all_users
