from __future__ import annotations

from datetime import date
from typing import Iterable, Protocol

from .models import ClickLog
from .repository import SQLiteRepository


class AcsClient(Protocol):
    def fetch_click_logs(self, target_date: date, page: int, limit: int) -> Iterable[ClickLog]:
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
