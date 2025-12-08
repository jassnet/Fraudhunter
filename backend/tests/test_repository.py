from datetime import date, datetime, timedelta, timezone

from fraud_checker.models import ClickLog
from fraud_checker.repository import SQLiteRepository


def _click(
    idx: int,
    *,
    click_date: date,
    seconds: int,
    media: str = "m1",
    program: str = "p1",
    ip: str = "1.1.1.1",
    ua: str = "UA",
):
    base = datetime.combine(click_date, datetime.min.time(), tzinfo=timezone.utc)
    return ClickLog(
        click_id=f"c{idx}",
        click_time=base + timedelta(seconds=seconds),
        media_id=media,
        program_id=program,
        ipaddress=ip,
        useragent=ua,
        referrer="https://example.com",
        raw_payload={"seq": idx},
    )


def test_upsert_clicks_aggregates_counts_and_times(tmp_path):
    repo = SQLiteRepository(tmp_path / "agg.db")
    repo.ensure_schema(store_raw=True)

    clicks = [
        _click(1, click_date=date(2024, 1, 1), seconds=10),
        _click(2, click_date=date(2024, 1, 1), seconds=70),
    ]

    repo.ingest_clicks(clicks, target_date=date(2024, 1, 1), store_raw=True)

    aggregates = repo.fetch_aggregates(date(2024, 1, 1))
    assert len(aggregates) == 1
    agg = aggregates[0]
    assert agg.click_count == 2
    assert agg.first_time == clicks[0].click_time
    assert agg.last_time == clicks[1].click_time

    # raw persisted when store_raw=True
    assert repo.count_raw_rows(date(2024, 1, 1)) == 2


def test_rerun_replaces_existing_rows(tmp_path):
    repo = SQLiteRepository(tmp_path / "rerun.db")
    repo.ensure_schema(store_raw=False)

    first_batch = [
        _click(1, click_date=date(2024, 1, 2), seconds=5),
        _click(2, click_date=date(2024, 1, 2), seconds=8),
    ]
    repo.ingest_clicks(first_batch, target_date=date(2024, 1, 2), store_raw=False)
    assert repo.fetch_aggregates(date(2024, 1, 2))[0].click_count == 2

    replacement = [_click(3, click_date=date(2024, 1, 2), seconds=20)]
    repo.ingest_clicks(replacement, target_date=date(2024, 1, 2), store_raw=False)

    aggregates = repo.fetch_aggregates(date(2024, 1, 2))
    assert len(aggregates) == 1
    assert aggregates[0].click_count == 1
    assert aggregates[0].first_time == replacement[0].click_time
    assert aggregates[0].last_time == replacement[0].click_time


def test_raw_storage_is_optional(tmp_path):
    repo = SQLiteRepository(tmp_path / "raw.db")
    repo.ensure_schema(store_raw=True)

    clicks = [_click(1, click_date=date(2024, 1, 3), seconds=0)]

    repo.ingest_clicks(clicks, target_date=date(2024, 1, 3), store_raw=False)
    assert repo.count_raw_rows(date(2024, 1, 3)) == 0

    repo.ingest_clicks(
        [_click(2, click_date=date(2024, 1, 4), seconds=0)],
        target_date=date(2024, 1, 4),
        store_raw=True,
    )
    assert repo.count_raw_rows(date(2024, 1, 4)) == 1
