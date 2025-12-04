from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Iterable, Protocol

from .models import ClickLog, ConversionLog
from .repository import SQLiteRepository

logger = logging.getLogger(__name__)


class AcsClient(Protocol):
    def fetch_click_logs(self, target_date: date, page: int, limit: int) -> Iterable[ClickLog]:
        ...

    def fetch_conversion_logs(
        self, target_date: date, page: int, limit: int
    ) -> Iterable[ConversionLog]:
        ...

    def fetch_click_logs_for_time_range(
        self, start_time: datetime, end_time: datetime, page: int, limit: int
    ) -> Iterable[ClickLog]:
        ...

    def fetch_conversion_logs_for_time_range(
        self, start_time: datetime, end_time: datetime, page: int, limit: int
    ) -> Iterable[ConversionLog]:
        ...


class ClickLogIngestor:
    def __init__(
        self,
        client: AcsClient,
        repository: SQLiteRepository,
        *,
        page_size: int = 1000,
        store_raw: bool = False,
    ):
        self.client = client
        self.repository = repository
        self.page_size = page_size
        self.store_raw = store_raw

    def run_for_date(self, target_date: date) -> int:
        """
        Fetch click logs for a single date and persist them.

        Policy: any client or DB exception aborts the run so operators can rerun after fixing
        the root cause. Retries can be layered outside this class if needed.
        """
        self.repository.ensure_schema(store_raw=self.store_raw)
        page = 1
        all_clicks: list[ClickLog] = []
        while True:
            batch = list(self.client.fetch_click_logs(target_date, page, self.page_size))
            if not batch:
                break
            all_clicks.extend(batch)
            # Stop when the API returns less than a full page, assuming no further data.
            if len(batch) < self.page_size:
                break
            page += 1

        if not all_clicks:
            # Still clear the date to support reruns that intentionally wipe a day.
            self.repository.clear_date(target_date, store_raw=self.store_raw)
            return 0

        return self.repository.ingest_clicks(
            all_clicks, target_date=target_date, store_raw=self.store_raw
        )

    def run_for_time_range(
        self, start_time: datetime, end_time: datetime
    ) -> tuple[int, int]:
        """
        指定された時間範囲のクリックログを取得し、既存データとマージする。
        
        日次バッチとの重複を避けるため、IDベースで重複チェックを行い、
        新規データのみを追加する。
        
        Returns:
            tuple[int, int]: (新規追加件数, スキップ件数)
        """
        self.repository.ensure_schema(store_raw=self.store_raw)
        page = 1
        all_clicks: list[ClickLog] = []
        
        while True:
            batch = list(
                self.client.fetch_click_logs_for_time_range(
                    start_time, end_time, page, self.page_size
                )
            )
            if not batch:
                break
            all_clicks.extend(batch)
            if len(batch) < self.page_size:
                break
            page += 1

        logger.info(
            "Fetched %d clicks for time range %s to %s",
            len(all_clicks),
            start_time.isoformat(),
            end_time.isoformat(),
        )

        if not all_clicks:
            return 0, 0

        # マージ処理（重複チェック付き）
        return self.repository.merge_clicks(all_clicks, store_raw=self.store_raw)


class ConversionIngestor:
    """
    成果ログを取り込む。

    フロー:
    1. ACSから成果ログ（action_log_raw）を取得
    2. entry_ipaddress/entry_useragent（実ユーザーIP/UA）を使用して集計
    
    Note: クリックログとの突合は不要。成果ログに直接ユーザーのIP/UAが含まれている。
    """

    def __init__(
        self,
        client: AcsClient,
        repository: SQLiteRepository,
        *,
        page_size: int = 500,
    ):
        self.client = client
        self.repository = repository
        self.page_size = page_size

    def run_for_date(self, target_date: date) -> tuple[int, int]:
        """
        指定日の成果ログを取得して保存する。

        Returns:
            tuple[int, int]: (取得した成果数, entry_ipaddress/entry_useragentが有効な成果数)
        """
        self.repository.ensure_conversion_schema()

        # 1. 成果ログを全て取得
        page = 1
        all_conversions: list[ConversionLog] = []
        while True:
            batch = list(
                self.client.fetch_conversion_logs(target_date, page, self.page_size)
            )
            if not batch:
                break
            all_conversions.extend(batch)
            if len(batch) < self.page_size:
                break
            page += 1

        logger.info(
            "Fetched %d conversions for %s", len(all_conversions), target_date.isoformat()
        )

        if not all_conversions:
            return 0, 0

        # 2. entry_ipaddress/entry_useragentが有効な成果をカウント
        valid_entry_count = sum(
            1 for c in all_conversions 
            if c.entry_ipaddress and c.entry_useragent
        )
        logger.info(
            "Found %d conversions with valid entry IP/UA out of %d total",
            valid_entry_count, len(all_conversions)
        )

        # 3. 保存（entry IP/UAが有効なものは集計にも追加される）
        total_count = self.repository.ingest_conversions(
            all_conversions, target_date=target_date
        )

        return total_count, valid_entry_count

    def run_for_time_range(
        self, start_time: datetime, end_time: datetime
    ) -> tuple[int, int, int]:
        """
        指定された時間範囲の成果ログを取得し、既存データとマージする。
        
        日次バッチとの重複を避けるため、IDベースで重複チェックを行い、
        新規データのみを追加する。
        
        Returns:
            tuple[int, int, int]: (新規追加件数, スキップ件数, entry IP/UA有効件数)
        """
        self.repository.ensure_conversion_schema()
        page = 1
        all_conversions: list[ConversionLog] = []
        
        while True:
            batch = list(
                self.client.fetch_conversion_logs_for_time_range(
                    start_time, end_time, page, self.page_size
                )
            )
            if not batch:
                break
            all_conversions.extend(batch)
            if len(batch) < self.page_size:
                break
            page += 1

        logger.info(
            "Fetched %d conversions for time range %s to %s",
            len(all_conversions),
            start_time.isoformat(),
            end_time.isoformat(),
        )

        if not all_conversions:
            return 0, 0, 0

        # entry IP/UAが有効な件数をカウント
        valid_entry_count = sum(
            1 for c in all_conversions 
            if c.entry_ipaddress and c.entry_useragent
        )

        # マージ処理（重複チェック付き）
        new_count, skip_count = self.repository.merge_conversions(all_conversions)
        
        return new_count, skip_count, valid_entry_count
