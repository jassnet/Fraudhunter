from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Iterable, Protocol

from .models import ClickLog, ConversionLog
from .repository_pg import PostgresRepository

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
        repository: PostgresRepository,
        *,
        page_size: int = 1000,
        store_raw: bool = False,
    ):
        self.client = client
        self.repository = repository
        self.page_size = page_size
        self.store_raw = store_raw
        self.last_affected_dates: list[date] = []

    def run_for_date(self, target_date: date) -> int:
        page = 1
        all_clicks: list[ClickLog] = []
        while True:
            batch = list(self.client.fetch_click_logs(target_date, page, self.page_size))
            if not batch:
                break
            all_clicks.extend(batch)
            if len(batch) < self.page_size:
                break
            page += 1

        if not all_clicks:
            self.repository.clear_date(target_date, store_raw=self.store_raw)
            self.last_affected_dates = [target_date]
            return 0

        self.last_affected_dates = sorted({click.click_time.date() for click in all_clicks})
        return self.repository.ingest_clicks(
            all_clicks, target_date=target_date, store_raw=self.store_raw
        )

    def run_for_time_range(
        self, start_time: datetime, end_time: datetime
    ) -> tuple[int, int]:
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

            filtered = [
                click for click in batch if start_time <= click.click_time <= end_time
            ]
            all_clicks.extend(filtered)

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
            self.last_affected_dates = []
            return 0, 0

        new_count, skip_count = self.repository.merge_clicks(all_clicks, store_raw=self.store_raw)
        affected_dates = getattr(self.repository, "last_merged_click_dates", None)
        if isinstance(affected_dates, list):
            self.last_affected_dates = list(affected_dates)
        elif new_count > 0:
            self.last_affected_dates = sorted({click.click_time.date() for click in all_clicks})
        else:
            self.last_affected_dates = []
        return new_count, skip_count


class ConversionIngestor:
    def __init__(
        self,
        client: AcsClient,
        repository: PostgresRepository,
        *,
        page_size: int = 500,
    ):
        self.client = client
        self.repository = repository
        self.page_size = page_size
        self.last_affected_dates: list[date] = []

    def run_for_date(self, target_date: date) -> tuple[int, int, int]:
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
            self.last_affected_dates = []
            return 0, 0, 0

        valid_entry_count = sum(
            1 for conversion in all_conversions if conversion.entry_ipaddress and conversion.entry_useragent
        )
        logger.info(
            "Found %d conversions with valid entry IP/UA out of %d total",
            valid_entry_count,
            len(all_conversions),
        )

        click_enriched_count = len(
            self.repository.enrich_conversions_with_click_info(all_conversions)
        )
        total_count = self.repository.ingest_conversions(
            all_conversions, target_date=target_date
        )
        self.last_affected_dates = [target_date] if total_count > 0 else []
        return total_count, valid_entry_count, click_enriched_count

    def run_for_time_range(
        self, start_time: datetime, end_time: datetime
    ) -> tuple[int, int, int, int]:
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

            filtered = [
                conversion
                for conversion in batch
                if start_time <= conversion.conversion_time <= end_time
            ]
            all_conversions.extend(filtered)

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
            self.last_affected_dates = []
            return 0, 0, 0, 0

        valid_entry_count = sum(
            1 for conversion in all_conversions if conversion.entry_ipaddress and conversion.entry_useragent
        )
        click_enriched_count = len(
            self.repository.enrich_conversions_with_click_info(all_conversions)
        )
        new_count, skip_count = self.repository.merge_conversions(all_conversions)
        affected_dates = getattr(self.repository, "last_merged_conversion_dates", None)
        if isinstance(affected_dates, list):
            self.last_affected_dates = list(affected_dates)
        elif new_count > 0:
            self.last_affected_dates = sorted(
                {conversion.conversion_time.date() for conversion in all_conversions}
            )
        else:
            self.last_affected_dates = []
        return new_count, skip_count, valid_entry_count, click_enriched_count
