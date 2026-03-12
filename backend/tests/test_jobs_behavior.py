from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

from fraud_checker.models import ClickLog, ConversionIpUaRollup, ConversionLog, IpUaRollup
from fraud_checker.services import jobs


class _DummySettings:
    page_size = 10


class _DummyBackgroundTasks:
    def __init__(self) -> None:
        self.tasks = []

    def add_task(self, fn):
        self.tasks.append(fn)


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


def _conversion(conversion_id: str, at: datetime) -> ConversionLog:
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
        entry_ipaddress="1.1.1.1",
        entry_useragent="Mozilla/5.0",
        state="approved",
        raw_payload={},
    )


def test_run_refresh_collects_detect_results_per_date(monkeypatch):
    # Given
    class FakeClient:
        def fetch_click_logs_for_time_range(self, start_time, end_time, page, limit):
            if page == 1:
                return [
                    _click("c1", datetime(2026, 1, 1, 0, 30, 0)),
                    _click("c2", datetime(2026, 1, 1, 1, 0, 0)),
                ]
            return []

        def fetch_conversion_logs_for_time_range(self, start_time, end_time, page, limit):
            if page == 1:
                return [
                    _conversion("v1", datetime(2026, 1, 1, 0, 45, 0)),
                    _conversion("v2", datetime(2026, 1, 1, 1, 15, 0)),
                ]
            return []

    class FakeRepo:
        def __init__(self) -> None:
            self.merged_clicks = []
            self.merged_conversions = []

        def ensure_schema(self, store_raw=False):
            return None

        def ensure_conversion_schema(self):
            return None

        def merge_clicks(self, clicks, *, store_raw):
            self.merged_clicks.extend(list(clicks))
            return len(list(clicks)), 0

        def merge_conversions(self, conversions):
            self.merged_conversions.extend(list(conversions))
            return len(list(conversions)), 0

        def load_settings(self):
            return {
                "click_threshold": 1,
                "media_threshold": 99,
                "program_threshold": 99,
                "burst_click_threshold": 99,
                "burst_window_seconds": 600,
                "conversion_threshold": 1,
                "conv_media_threshold": 99,
                "conv_program_threshold": 99,
                "burst_conversion_threshold": 99,
                "burst_conversion_window_seconds": 1800,
                "min_click_to_conv_seconds": None,
                "max_click_to_conv_seconds": None,
                "browser_only": False,
                "exclude_datacenter_ip": False,
            }

        def fetch_suspicious_rollups(
            self,
            target_date: date,
            *,
            click_threshold: int,
            media_threshold: int,
            program_threshold: int,
            burst_click_threshold: int,
            browser_only: bool,
            exclude_datacenter_ip: bool,
        ):
            start = datetime.combine(target_date, datetime.min.time())
            return [
                IpUaRollup(
                    date=target_date,
                    ipaddress="1.1.1.1",
                    useragent="Mozilla/5.0",
                    total_clicks=2,
                    media_count=1,
                    program_count=1,
                    first_time=start,
                    last_time=start + timedelta(seconds=10),
                )
            ]

        def fetch_suspicious_conversion_rollups(
            self,
            target_date: date,
            *,
            conversion_threshold: int,
            media_threshold: int,
            program_threshold: int,
            burst_conversion_threshold: int,
            browser_only: bool,
            exclude_datacenter_ip: bool,
        ):
            start = datetime.combine(target_date, datetime.min.time())
            return [
                ConversionIpUaRollup(
                    date=target_date,
                    ipaddress="1.1.1.1",
                    useragent="Mozilla/5.0",
                    conversion_count=2,
                    media_count=1,
                    program_count=1,
                    first_conversion_time=start,
                    last_conversion_time=start + timedelta(seconds=10),
                )
            ]

        def fetch_click_to_conversion_gaps(self, target_date):
            return {}

        def fetch_conversion_rollups(self, target_date):
            return []

    fixed_now = datetime(2026, 1, 2, 0, 0, 0)
    repo = FakeRepo()
    monkeypatch.setattr(jobs, "now_local", lambda: fixed_now)
    monkeypatch.setattr(jobs, "get_repository", lambda: repo)
    monkeypatch.setattr(jobs, "get_acs_client", lambda: FakeClient())
    monkeypatch.setattr(jobs, "resolve_acs_settings", lambda: _DummySettings())
    jobs.settings_service._settings_cache = None

    # When
    result, message = jobs.run_refresh(hours=25, clicks=True, conversions=True, detect=True)

    # Then
    assert message == "Refresh completed for last 25 hours"
    assert result["clicks"] == {"new": 2, "skipped": 0}
    assert result["conversions"] == {"new": 2, "skipped": 0, "valid_entry": 2}
    assert set(result["detect"].keys()) == {"2025-12-31", "2026-01-01", "2026-01-02"}
    assert result["detect"]["2026-01-02"] == {
        "suspicious_clicks": 1,
        "suspicious_conversions": 1,
        "high_risk": 1,
    }


def test_run_refresh_without_detect_does_not_add_detect_key(monkeypatch):
    # Given
    class FakeClient:
        def fetch_click_logs_for_time_range(self, start_time, end_time, page, limit):
            if page == 1:
                return [_click("c1", datetime(2026, 1, 2, 0, 30, 0))]
            return []

        def fetch_conversion_logs_for_time_range(self, start_time, end_time, page, limit):
            if page == 1:
                return [_conversion("v1", datetime(2026, 1, 2, 0, 45, 0))]
            return []

    class FakeRepo:
        def ensure_schema(self, store_raw=False):
            return None

        def ensure_conversion_schema(self):
            return None

        def merge_clicks(self, clicks, *, store_raw):
            return len(list(clicks)), 0

        def merge_conversions(self, conversions):
            return len(list(conversions)), 0

    monkeypatch.setattr(jobs, "now_local", lambda: datetime(2026, 1, 2, 1, 0, 0))
    monkeypatch.setattr(jobs, "get_repository", lambda: FakeRepo())
    monkeypatch.setattr(jobs, "get_acs_client", lambda: FakeClient())
    monkeypatch.setattr(jobs, "resolve_acs_settings", lambda: _DummySettings())

    # When
    result, message = jobs.run_refresh(hours=1, clicks=True, conversions=True, detect=False)

    # Then
    assert message == "Refresh completed for last 1 hours"
    assert "detect" not in result
    assert result["clicks"]["new"] == 1
    assert result["conversions"]["new"] == 1


def test_enqueue_job_raises_conflict_when_another_job_is_running(monkeypatch):
    # Given
    class DummyStore:
        def start(self, job_id, message):
            return False

    monkeypatch.setattr(jobs, "get_job_store", lambda: DummyStore())
    background_tasks = _DummyBackgroundTasks()

    # When / Then
    with pytest.raises(jobs.JobConflictError):
        jobs.enqueue_job(
            background_tasks=background_tasks,
            job_id="refresh_1h",
            start_message="start",
            run_fn=lambda: ({"success": True}, "done"),
        )


def test_enqueue_job_persists_failure_when_runner_raises(monkeypatch):
    # Given
    class DummyStore:
        def __init__(self) -> None:
            self.fail_calls = []

        def start(self, job_id, message):
            return True

        def complete(self, job_id, message, result):
            raise AssertionError("失敗系では complete を呼び出してはいけない")

        def fail(self, job_id, message, result):
            self.fail_calls.append((job_id, message, result))

    store = DummyStore()
    monkeypatch.setattr(jobs, "get_job_store", lambda: store)
    background_tasks = _DummyBackgroundTasks()

    def boom():
        raise RuntimeError("boom")

    # When
    jobs.enqueue_job(
        background_tasks=background_tasks,
        job_id="refresh_1h",
        start_message="start",
        run_fn=boom,
    )
    background_tasks.tasks[0]()

    # Then
    assert len(store.fail_calls) == 1
    job_id, message, result = store.fail_calls[0]
    assert job_id == "refresh_1h"
    assert "boom" in message
    assert result == {"success": False, "error": "boom"}


def test_enqueue_job_completes_when_runner_succeeds(monkeypatch):
    # Given
    class DummyStore:
        def __init__(self) -> None:
            self.complete_calls = []

        def start(self, job_id, message):
            return True

        def complete(self, job_id, message, result):
            self.complete_calls.append((job_id, message, result))

        def fail(self, job_id, message, result):
            raise AssertionError("成功系では fail を呼び出してはいけない")

    store = DummyStore()
    monkeypatch.setattr(jobs, "get_job_store", lambda: store)
    background_tasks = _DummyBackgroundTasks()

    # When
    jobs.enqueue_job(
        background_tasks=background_tasks,
        job_id="refresh_2h",
        start_message="start",
        run_fn=lambda: ({"success": True, "count": 3}, "done"),
    )
    background_tasks.tasks[0]()

    # Then
    assert store.complete_calls == [("refresh_2h", "done", {"success": True, "count": 3})]


def test_run_click_ingestion_returns_summary_message(monkeypatch):
    # Given
    class FakeClient:
        def fetch_click_logs(self, target_date, page, limit):
            if page == 1:
                return [_click("c1", datetime(2026, 1, 3, 12, 0, 0))]
            return []

    class FakeRepo:
        def ensure_schema(self, store_raw=False):
            return None

        def clear_date(self, target_date, *, store_raw):
            return None

        def ingest_clicks(self, clicks, *, target_date, store_raw):
            return len(list(clicks))

    monkeypatch.setattr(jobs, "get_repository", lambda: FakeRepo())
    monkeypatch.setattr(jobs, "get_acs_client", lambda: FakeClient())
    monkeypatch.setattr(jobs, "resolve_acs_settings", lambda: _DummySettings())

    # When
    result, message = jobs.run_click_ingestion(datetime(2026, 1, 3).date())

    # Then
    assert result == {"success": True, "count": 1}
    assert message == "Ingested 1 clicks for 2026-01-03"


def test_run_conversion_ingestion_returns_summary_message(monkeypatch):
    # Given
    class FakeClient:
        def fetch_conversion_logs(self, target_date, page, limit):
            if page == 1:
                return [_conversion("v1", datetime(2026, 1, 3, 12, 0, 0))]
            return []

    class FakeRepo:
        def ensure_conversion_schema(self):
            return None

        def ingest_conversions(self, conversions, *, target_date):
            return len(list(conversions))

    monkeypatch.setattr(jobs, "get_repository", lambda: FakeRepo())
    monkeypatch.setattr(jobs, "get_acs_client", lambda: FakeClient())
    monkeypatch.setattr(jobs, "resolve_acs_settings", lambda: _DummySettings())

    # When
    result, message = jobs.run_conversion_ingestion(datetime(2026, 1, 3).date())

    # Then
    assert result == {"success": True, "total": 1, "enriched": 1}
    assert message == "Ingested 1 conversions for 2026-01-03"


def test_run_master_sync_returns_upsert_counts(monkeypatch):
    # Given
    class FakeClient:
        def fetch_all_media_master(self):
            return [{"id": "m1"}]

        def fetch_all_promotion_master(self):
            return [{"id": "p1"}, {"id": "p2"}]

        def fetch_all_user_master(self):
            return [{"id": "u1"}, {"id": "u2"}, {"id": "u3"}]

    class FakeRepo:
        def bulk_upsert_media(self, media_list):
            return len(media_list)

        def bulk_upsert_promotions(self, promo_list):
            return len(promo_list)

        def bulk_upsert_users(self, user_list):
            return len(user_list)

    monkeypatch.setattr(jobs, "get_repository", lambda: FakeRepo())
    monkeypatch.setattr(jobs, "get_acs_client", lambda: FakeClient())

    # When
    result, message = jobs.run_master_sync()

    # Then
    assert result == {
        "success": True,
        "media_count": 1,
        "promotion_count": 2,
        "user_count": 3,
    }
    assert message == "Master sync completed"

