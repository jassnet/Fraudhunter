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

    def add_task(self, fn, *args):
        self.tasks.append((fn, args))


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

        def merge_clicks(self, clicks, *, store_raw):
            self.merged_clicks.extend(list(clicks))
            return len(self.merged_clicks), 0

        def merge_conversions(self, conversions):
            self.merged_conversions.extend(list(conversions))
            return len(self.merged_conversions), 0

        def enrich_conversions_with_click_info(self, conversions):
            return list(conversions)

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

        def fetch_suspicious_rollups(self, target_date: date, **kwargs):
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

        def fetch_suspicious_conversion_rollups(self, target_date: date, **kwargs):
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
    monkeypatch.setattr(
        jobs.findings_service,
        "recompute_findings_for_dates",
        lambda repo, dates: {
            target_date.isoformat(): {"suspicious_clicks": 1, "suspicious_conversions": 1}
            for target_date in dates
        },
    )
    jobs.settings_service._settings_cache = None

    result, message = jobs.run_refresh(hours=25, clicks=True, conversions=True, detect=True)

    assert message == "Refresh completed for last 25 hours"
    assert result["clicks"] == {"new": 2, "skipped": 0}
    assert result["conversions"] == {
        "new": 2,
        "skipped": 0,
        "valid_entry": 2,
        "click_enriched": 2,
    }
    assert result["detect"]["2026-01-02"]["high_risk"] == 1


def test_enqueue_job_raises_conflict_when_active_job_exists(monkeypatch):
    class DummyStore:
        def has_active_job(self):
            return True

    monkeypatch.setattr(jobs, "get_job_store", lambda: DummyStore())

    with pytest.raises(jobs.JobConflictError):
        jobs.enqueue_job(
            job_type=jobs.JOB_TYPE_REFRESH,
            params={"hours": 1},
            start_message="start",
        )


def test_enqueue_job_persists_and_schedules_background_runner(monkeypatch):
    class DummyStore:
        def has_active_job(self):
            return False

        def enqueue(self, *, job_type, params, message):
            return type("QueuedJob", (), {"id": "run-1", "job_type": job_type})()

    store = DummyStore()
    background_tasks = _DummyBackgroundTasks()
    monkeypatch.setattr(jobs, "get_job_store", lambda: store)

    run = jobs.enqueue_job(
        job_type=jobs.JOB_TYPE_REFRESH,
        params={"hours": 1},
        start_message="start",
        background_tasks=background_tasks,
    )

    assert run.id == "run-1"
    assert background_tasks.tasks[0][0] == jobs.process_queued_jobs


def test_process_queued_jobs_acquires_and_executes(monkeypatch):
    executed = []

    class DummyStore:
        def __init__(self):
            self.calls = 0

        def acquire_next(self, *, worker_id, lease_seconds):
            self.calls += 1
            if self.calls > 1:
                return None
            return jobs.JobRun(
                id="run-1",
                job_type=jobs.JOB_TYPE_MASTER_SYNC,
                status="running",
                params=None,
                result=None,
                error_message=None,
                message="queued",
                queued_at=datetime(2026, 1, 1, 0, 0, 0),
                started_at=datetime(2026, 1, 1, 0, 0, 1),
                finished_at=None,
                heartbeat_at=None,
                locked_until=None,
                worker_id=worker_id,
            )

        def complete(self, run_id, message, result):
            executed.append(("complete", run_id, message, result))

        def fail(self, *args, **kwargs):
            raise AssertionError("fail should not be called")

        def heartbeat(self, **kwargs):
            return True

    monkeypatch.setattr(jobs, "get_job_store", lambda: DummyStore())
    monkeypatch.setattr(jobs, "_dispatch_job", lambda run: ({"success": True}, "done"))
    monkeypatch.setattr(jobs, "_job_lease_seconds", lambda: 60)
    monkeypatch.setattr(jobs, "_worker_id", lambda: "worker-1")

    processed = jobs.process_queued_jobs(max_jobs=2)

    assert processed == 1
    assert executed == [("complete", "run-1", "done", {"success": True})]


def test_run_click_ingestion_returns_summary_message(monkeypatch):
    class FakeClient:
        def fetch_click_logs(self, target_date, page, limit):
            if page == 1:
                return [_click("c1", datetime(2026, 1, 3, 12, 0, 0))]
            return []

    class FakeRepo:
        def clear_date(self, target_date, *, store_raw):
            return None

        def ingest_clicks(self, clicks, *, target_date, store_raw):
            return len(list(clicks))

    monkeypatch.setattr(jobs, "get_repository", lambda: FakeRepo())
    monkeypatch.setattr(jobs, "get_acs_client", lambda: FakeClient())
    monkeypatch.setattr(jobs, "resolve_acs_settings", lambda: _DummySettings())
    monkeypatch.setattr(
        jobs.findings_service,
        "recompute_findings_for_dates",
        lambda repo, dates: {dates[0].isoformat(): {"suspicious_clicks": 1}},
    )

    result, message = jobs.run_click_ingestion(datetime(2026, 1, 3).date())

    assert result == {"success": True, "count": 1, "findings": {"suspicious_clicks": 1}}
    assert message == "Ingested 1 clicks for 2026-01-03"


def test_run_conversion_ingestion_returns_summary_message(monkeypatch):
    class FakeClient:
        def fetch_conversion_logs(self, target_date, page, limit):
            if page == 1:
                return [_conversion("v1", datetime(2026, 1, 3, 12, 0, 0))]
            return []

    class FakeRepo:
        def enrich_conversions_with_click_info(self, conversions):
            return list(conversions)

        def ingest_conversions(self, conversions, *, target_date):
            return len(list(conversions))

    monkeypatch.setattr(jobs, "get_repository", lambda: FakeRepo())
    monkeypatch.setattr(jobs, "get_acs_client", lambda: FakeClient())
    monkeypatch.setattr(jobs, "resolve_acs_settings", lambda: _DummySettings())
    monkeypatch.setattr(
        jobs.findings_service,
        "recompute_findings_for_dates",
        lambda repo, dates: {dates[0].isoformat(): {"suspicious_conversions": 1}},
    )

    result, message = jobs.run_conversion_ingestion(datetime(2026, 1, 3).date())

    assert result == {
        "success": True,
        "total": 1,
        "enriched": 1,
        "click_enriched": 1,
        "findings": {"suspicious_conversions": 1},
    }
    assert message == "Ingested 1 conversions for 2026-01-03"
