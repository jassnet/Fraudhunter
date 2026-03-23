from __future__ import annotations

from datetime import date, datetime, timedelta

from fraud_checker.ingestion import ClickLogIngestor, ConversionIngestor
from fraud_checker.models import ClickLog, ConversionLog


def _click(click_id: str, at: datetime) -> ClickLog:
    return ClickLog(
        click_id=click_id,
        click_time=at,
        media_id="m1",
        program_id="p1",
        ipaddress="1.1.1.1",
        useragent="Mozilla/5.0",
        referrer=None,
        raw_payload={},
    )


def _conversion(conversion_id: str, at: datetime, *, valid_entry: bool) -> ConversionLog:
    return ConversionLog(
        conversion_id=conversion_id,
        cid="c1",
        conversion_time=at,
        click_time=at - timedelta(seconds=10),
        media_id="m1",
        program_id="p1",
        user_id="u1",
        postback_ipaddress="10.0.0.1",
        postback_useragent="postback",
        entry_ipaddress="2.2.2.2" if valid_entry else None,
        entry_useragent="Mozilla/5.0" if valid_entry else None,
        state="approved",
        raw_payload={},
    )


def test_click_run_for_date_clears_target_date_when_no_clicks():
    # Given
    class DummyClient:
        def fetch_click_logs(self, target_date, page, limit):
            return []

    class DummyRepo:
        def __init__(self):
            self.cleared = None

        def clear_date(self, target_date, *, store_raw):
            self.cleared = (target_date, store_raw)

    target = date(2026, 1, 2)
    repo = DummyRepo()
    ingestor = ClickLogIngestor(DummyClient(), repo, page_size=2, store_raw=True)

    # When
    count = ingestor.run_for_date(target)

    # Then
    assert count == 0
    assert repo.cleared == (target, True)


def test_click_run_for_date_paginates_and_ingests():
    # Given
    t = datetime(2026, 1, 2, 10, 0, 0)
    pages = {
        1: [_click("a", t), _click("b", t + timedelta(seconds=1))],
        2: [_click("c", t + timedelta(seconds=2))],
        3: [],
    }

    class DummyClient:
        def fetch_click_logs(self, target_date, page, limit):
            return pages.get(page, [])

    class DummyRepo:
        def __init__(self):
            self.ingest_args = None

        def ingest_clicks(self, clicks, *, target_date, store_raw):
            self.ingest_args = (list(clicks), target_date, store_raw)
            return len(self.ingest_args[0])

    repo = DummyRepo()
    ingestor = ClickLogIngestor(DummyClient(), repo, page_size=2, store_raw=False)

    # When
    count = ingestor.run_for_date(date(2026, 1, 2))

    # Then
    assert count == 3
    assert repo.ingest_args is not None
    clicks, target_date, store_raw = repo.ingest_args
    assert target_date == date(2026, 1, 2)
    assert store_raw is False
    assert [c.click_id for c in clicks] == ["a", "b", "c"]


def test_click_run_for_time_range_filters_and_merges():
    # Given
    start = datetime(2026, 1, 2, 0, 0, 0)
    end = datetime(2026, 1, 2, 1, 0, 0)
    inside = _click("inside", start + timedelta(minutes=10))
    outside = _click("outside", end + timedelta(minutes=1))

    class DummyClient:
        def fetch_click_logs_for_time_range(self, start_time, end_time, page, limit):
            if page == 1:
                return [inside, outside]
            return []

    class DummyRepo:
        def __init__(self):
            self.merged = None

        def merge_clicks(self, clicks, *, store_raw):
            self.merged = (list(clicks), store_raw)
            return 1, 0

    repo = DummyRepo()
    ingestor = ClickLogIngestor(DummyClient(), repo, page_size=100, store_raw=True)

    # When
    new_count, skip_count = ingestor.run_for_time_range(start, end)

    # Then
    assert (new_count, skip_count) == (1, 0)
    assert repo.merged is not None
    merged_clicks, store_raw = repo.merged
    assert store_raw is True
    assert [c.click_id for c in merged_clicks] == ["inside"]


def test_conversion_run_for_date_counts_valid_entries_and_ingests():
    # Given
    t = datetime(2026, 1, 2, 10, 0, 0)

    class DummyClient:
        def fetch_conversion_logs(self, target_date, page, limit):
            if page == 1:
                return [_conversion("a", t, valid_entry=True), _conversion("b", t, valid_entry=False)]
            return []

    class DummyRepo:
        def __init__(self):
            self.ingested = None

        def enrich_conversions_with_click_info(self, conversions):
            return [conversions[0]]

        def ingest_conversions(self, conversions, *, target_date):
            self.ingested = (list(conversions), target_date)
            return len(self.ingested[0])

    repo = DummyRepo()
    ingestor = ConversionIngestor(DummyClient(), repo, page_size=10)

    # When
    total_count, valid_entry_count, click_enriched_count = ingestor.run_for_date(date(2026, 1, 2))

    # Then
    assert total_count == 2
    assert valid_entry_count == 1
    assert click_enriched_count == 1
    assert repo.ingested is not None
    conversions, target = repo.ingested
    assert target == date(2026, 1, 2)
    assert [c.conversion_id for c in conversions] == ["a", "b"]


def test_conversion_run_for_time_range_filters_and_returns_counts():
    # Given
    start = datetime(2026, 1, 2, 0, 0, 0)
    end = datetime(2026, 1, 2, 1, 0, 0)
    inside_valid = _conversion("inside-valid", start + timedelta(minutes=10), valid_entry=True)
    inside_invalid = _conversion("inside-invalid", start + timedelta(minutes=20), valid_entry=False)
    outside = _conversion("outside", end + timedelta(minutes=1), valid_entry=True)

    class DummyClient:
        def fetch_conversion_logs_for_time_range(self, start_time, end_time, page, limit):
            if page == 1:
                return [inside_valid, outside]
            if page == 2:
                return [inside_invalid]
            return []

    class DummyRepo:
        def __init__(self):
            self.merged = None

        def enrich_conversions_with_click_info(self, conversions):
            return [conversions[0]]

        def merge_conversions(self, conversions):
            self.merged = list(conversions)
            return 2, 0

    repo = DummyRepo()
    ingestor = ConversionIngestor(DummyClient(), repo, page_size=1)

    # When
    new_count, skip_count, valid_entry_count, click_enriched_count = ingestor.run_for_time_range(start, end)

    # Then
    assert (new_count, skip_count, valid_entry_count, click_enriched_count) == (2, 0, 1, 1)
    assert repo.merged is not None
    assert [c.conversion_id for c in repo.merged] == ["inside-valid", "inside-invalid"]
