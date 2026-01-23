from datetime import date, datetime, timedelta, timezone

from fraud_checker.ingestion import ClickLogIngestor
from fraud_checker.models import ClickLog
from fraud_checker.repository import SQLiteRepository


class FakeAcsClient:
    def __init__(self, pages):
        self.pages = pages
        self.requested_pages = []

    def fetch_click_logs(self, target_date: date, page: int, limit: int):
        self.requested_pages.append(page)
        return self.pages.get(page, [])


def _click(idx: int, target_date: date, seconds: int):
    base = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
    return ClickLog(
        click_id=f"id-{idx}",
        click_time=base + timedelta(seconds=seconds),
        media_id="m1",
        program_id="p1",
        ipaddress="1.1.1.1",
        useragent="UA",
        referrer=None,
        raw_payload=None,
    )


def test_ingestor_walks_pages_and_persists(tmp_path):
    target = date(2024, 1, 6)
    pages = {
        1: [_click(1, target, 0)],
        2: [_click(2, target, 30)],
    }
    client = FakeAcsClient(pages)

    repo = SQLiteRepository(tmp_path / "ingest.db")
    repo.ensure_schema(store_raw=True)

    ingestor = ClickLogIngestor(client=client, repository=repo, page_size=1, store_raw=True)
    ingestor.run_for_date(target)

    assert client.requested_pages == [1, 2, 3]  # third page is empty and stops the loop

    aggregates = repo.fetch_aggregates(target)
    assert len(aggregates) == 1
    assert aggregates[0].click_count == 2
    assert aggregates[0].first_time < aggregates[0].last_time

    assert repo.count_raw_rows(target) == 2
