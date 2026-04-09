from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from fraud_checker.models import ClickLog, ConversionIpUaRollup, ConversionLog
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


def test_run_refresh_enqueues_findings_recompute_jobs_per_date(monkeypatch):
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
    captured = {}
    monkeypatch.setattr(
        jobs,
        "enqueue_findings_recompute_jobs",
        lambda dates, **kwargs: captured.update(
            {
                "dates": [target_date.isoformat() for target_date in dates],
                "kwargs": kwargs,
            }
        )
        or [type("QueuedJob", (), {"id": f"job-{index + 1}"})() for index, _ in enumerate(dates)],
    )

    result, message = jobs.run_refresh(hours=25, clicks=True, conversions=True, detect=True)

    assert message == "Refresh completed for last 25 hours"
    assert result["clicks"] == {"new": 2, "skipped": 0}
    assert result["conversions"] == {
        "new": 2,
        "skipped": 0,
        "valid_entry": 2,
        "click_enriched": 2,
    }
    assert captured["dates"] == ["2026-01-01"]
    assert captured["kwargs"]["trigger"] == "refresh"
    assert result["findings_recompute"]["mode"] == "queued"
    assert result["findings_recompute"]["job_ids"] == ["job-1"]


def test_enqueue_job_allows_queueing_when_another_job_is_active(monkeypatch):
    class DummyStore:
        def find_active_duplicate(self, dedupe_key):
            return None

        def enqueue(self, *, job_type, params, message, max_attempts, dedupe_key, priority, concurrency_key=None):
            return type(
                "QueuedJob",
                (),
                {
                    "id": "run-queued",
                    "job_type": job_type,
                    "max_attempts": max_attempts,
                    "priority": priority,
                    "concurrency_key": concurrency_key,
                },
            )()

    monkeypatch.setattr(jobs, "get_job_store", lambda: DummyStore())

    run = jobs.enqueue_job(
        job_type=jobs.JOB_TYPE_REFRESH,
        params={"hours": 1},
        start_message="start",
    )

    assert run.id == "run-queued"


def test_enqueue_job_persists_and_schedules_background_runner(monkeypatch):
    class DummyStore:
        def has_active_job(self):
            return False

        def find_active_duplicate(self, dedupe_key):
            return None

        def enqueue(self, *, job_type, params, message, max_attempts, dedupe_key, priority, concurrency_key=None):
            return type(
                "QueuedJob",
                (),
                {
                    "id": "run-1",
                    "job_type": job_type,
                    "max_attempts": 4,
                    "priority": 10,
                    "concurrency_key": concurrency_key,
                },
            )()

    store = DummyStore()
    background_tasks = _DummyBackgroundTasks()
    monkeypatch.setattr(jobs, "get_job_store", lambda: store)
    monkeypatch.setattr(jobs, "_should_use_in_process_background_kick", lambda: True)

    run = jobs.enqueue_job(
        job_type=jobs.JOB_TYPE_REFRESH,
        params={"hours": 1},
        start_message="start",
        background_tasks=background_tasks,
    )

    assert run.id == "run-1"
    assert background_tasks.tasks[0][0] == jobs.process_queued_jobs


def test_enqueue_job_returns_existing_run_when_dedupe_matches(monkeypatch):
    class DummyStore:
        def has_active_job(self):
            raise AssertionError("has_active_job should not run for duplicates")

        def find_active_duplicate(self, dedupe_key):
            return type(
                "QueuedJob",
                (),
                {
                    "id": "run-existing",
                    "job_type": jobs.JOB_TYPE_REFRESH,
                    "max_attempts": 4,
                    "priority": 10,
                },
            )()

    monkeypatch.setattr(jobs, "get_job_store", lambda: DummyStore())

    run = jobs.enqueue_job(
        job_type=jobs.JOB_TYPE_REFRESH,
        params={"hours": 1},
        start_message="start",
    )

    assert run.id == "run-existing"


def test_enqueue_job_returns_existing_run_when_unique_index_race_occurs(monkeypatch):
    class DummyStore:
        def __init__(self):
            self.calls = 0

        def advisory_lock(self, concurrency_key):
            class _Ctx:
                def __enter__(self_inner):
                    return True

                def __exit__(self_inner, exc_type, exc, tb):
                    return False

            return _Ctx()

        def find_active_duplicate(self, dedupe_key):
            self.calls += 1
            if self.calls == 1:
                return None
            return type(
                "QueuedJob",
                (),
                {
                    "id": "run-race",
                    "job_type": jobs.JOB_TYPE_REFRESH,
                    "max_attempts": 4,
                    "priority": 10,
                    "concurrency_key": None,
                },
            )()

        def enqueue(self, **kwargs):
            raise IntegrityError("insert into job_runs", {}, RuntimeError("duplicate key"))

    monkeypatch.setattr(jobs, "get_job_store", lambda: DummyStore())

    run = jobs.enqueue_job(
        job_type=jobs.JOB_TYPE_REFRESH,
        params={"hours": 1},
        start_message="start",
    )

    assert run.id == "run-race"


def test_enqueue_job_skips_in_process_kick_in_production(monkeypatch):
    class DummyStore:
        def has_active_job(self):
            return False

        def find_active_duplicate(self, dedupe_key):
            return None

        def enqueue(self, *, job_type, params, message, max_attempts, dedupe_key, priority, concurrency_key=None):
            return type(
                "QueuedJob",
                (),
                {
                    "id": "run-1",
                    "job_type": job_type,
                    "max_attempts": max_attempts,
                    "priority": priority,
                    "concurrency_key": concurrency_key,
                },
            )()

    background_tasks = _DummyBackgroundTasks()
    monkeypatch.setattr(jobs, "get_job_store", lambda: DummyStore())
    monkeypatch.setattr(jobs, "_should_use_in_process_background_kick", lambda: False)

    jobs.enqueue_job(
        job_type=jobs.JOB_TYPE_REFRESH,
        params={"hours": 1},
        start_message="start",
        background_tasks=background_tasks,
    )

    assert background_tasks.tasks == []


def test_enqueue_refresh_job_builds_stable_payload(monkeypatch):
    captured = {}

    def fake_enqueue_job(**kwargs):
        captured.update(kwargs)
        return type("QueuedJob", (), {"id": "run-refresh"})()

    monkeypatch.setattr(jobs, "enqueue_job", fake_enqueue_job)

    run = jobs.enqueue_refresh_job(hours=2, clicks=True, conversions=False, detect=True)

    assert run.id == "run-refresh"
    assert captured["job_type"] == jobs.JOB_TYPE_REFRESH
    assert captured["params"] == {
        "hours": 2,
        "clicks": True,
        "conversions": False,
        "detect": True,
    }
    assert captured["start_message"] == "\u76f4\u8fd12\u6642\u9593\u306e\u518d\u53d6\u5f97\u30b8\u30e7\u30d6\u3092\u767b\u9332\u3057\u307e\u3057\u305f"


def test_enqueue_master_sync_job_builds_expected_message(monkeypatch):
    captured = {}

    def fake_enqueue_job(**kwargs):
        captured.update(kwargs)
        return type("QueuedJob", (), {"id": "run-master"})()

    monkeypatch.setattr(jobs, "enqueue_job", fake_enqueue_job)

    run = jobs.enqueue_master_sync_job()

    assert run.id == "run-master"
    assert captured["job_type"] == jobs.JOB_TYPE_MASTER_SYNC
    assert captured["params"] is None
    assert captured["start_message"] == "\u30de\u30b9\u30bf\u540c\u671f\u30b8\u30e7\u30d6\u3092\u767b\u9332\u3057\u307e\u3057\u305f"


def test_process_queued_jobs_acquires_and_executes(monkeypatch):
    executed = []

    class DummyStore:
        def __init__(self):
            self.calls = 0

        def advisory_lock(self, concurrency_key):
            class _Ctx:
                def __enter__(self_inner):
                    return True

                def __exit__(self_inner, exc_type, exc, tb):
                    return False

            return _Ctx()

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
                attempt_count=0,
                max_attempts=2,
                next_retry_at=None,
                dedupe_key="master-sync",
                priority=50,
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


def test_execute_job_run_requeues_retryable_failure(monkeypatch):
    calls = []

    class DummyStore:
        def advisory_lock(self, concurrency_key):
            class _Ctx:
                def __enter__(self_inner):
                    return True

                def __exit__(self_inner, exc_type, exc, tb):
                    return False

            return _Ctx()

        def fail(self, *args, **kwargs):
            calls.append(kwargs)
            return "queued"

        def heartbeat(self, **kwargs):
            return True

    run = jobs.JobRun(
        id="run-1",
        job_type=jobs.JOB_TYPE_REFRESH,
        status="running",
        params={"hours": 1},
        result=None,
        error_message=None,
        message="queued",
        attempt_count=0,
        max_attempts=4,
        next_retry_at=None,
        dedupe_key="refresh-key",
        priority=10,
        queued_at=datetime(2026, 1, 1, 0, 0, 0),
        started_at=datetime(2026, 1, 1, 0, 0, 1),
        finished_at=None,
        heartbeat_at=None,
        locked_until=None,
        worker_id="worker-1",
    )

    monkeypatch.setattr(jobs, "_dispatch_job", lambda run: (_ for _ in ()).throw(RuntimeError("boom")))

    jobs._execute_job_run(
        store=DummyStore(),
        run=run,
        worker_id="worker-1",
        lease_seconds=60,
    )

    assert calls[0]["retryable"] is True


def test_execute_job_run_marks_value_error_non_retryable(monkeypatch):
    calls = []

    class DummyStore:
        def advisory_lock(self, concurrency_key):
            class _Ctx:
                def __enter__(self_inner):
                    return True

                def __exit__(self_inner, exc_type, exc, tb):
                    return False

            return _Ctx()

        def fail(self, *args, **kwargs):
            calls.append(kwargs)
            return "failed"

        def heartbeat(self, **kwargs):
            return True

    run = jobs.JobRun(
        id="run-1",
        job_type=jobs.JOB_TYPE_REFRESH,
        status="running",
        params={"hours": 1},
        result=None,
        error_message=None,
        message="queued",
        attempt_count=0,
        max_attempts=4,
        next_retry_at=None,
        dedupe_key="refresh-key",
        priority=10,
        queued_at=datetime(2026, 1, 1, 0, 0, 0),
        started_at=datetime(2026, 1, 1, 0, 0, 1),
        finished_at=None,
        heartbeat_at=None,
        locked_until=None,
        worker_id="worker-1",
    )

    monkeypatch.setattr(jobs, "_dispatch_job", lambda run: (_ for _ in ()).throw(ValueError("bad input")))

    jobs._execute_job_run(
        store=DummyStore(),
        run=run,
        worker_id="worker-1",
        lease_seconds=60,
    )

    assert calls[0]["retryable"] is False


def test_execute_job_run_requeues_when_concurrency_lock_is_busy(monkeypatch):
    calls = []

    class DummyStore:
        def advisory_lock(self, concurrency_key):
            class _Ctx:
                def __enter__(self_inner):
                    return False

                def __exit__(self_inner, exc_type, exc, tb):
                    return False

            return _Ctx()

        def requeue_blocked(self, run_id, message, *, delay_seconds=15):
            calls.append((run_id, message, delay_seconds))

    run = jobs.JobRun(
        id="run-1",
        job_type=jobs.JOB_TYPE_RECOMPUTE_FINDINGS_DATE,
        status="running",
        params={"date": "2026-01-21", "generation_id": "gen-1"},
        result=None,
        error_message=None,
        message="queued",
        attempt_count=0,
        max_attempts=4,
        next_retry_at=None,
        dedupe_key="recompute:2026-01-21",
        priority=30,
        queued_at=datetime(2026, 1, 1, 0, 0, 0),
        started_at=datetime(2026, 1, 1, 0, 0, 1),
        finished_at=None,
        heartbeat_at=None,
        locked_until=None,
        worker_id="worker-1",
        concurrency_key="date-write:2026-01-21",
    )

    jobs._execute_job_run(
        store=DummyStore(),
        run=run,
        worker_id="worker-1",
        lease_seconds=60,
    )

    assert calls == [("run-1", "recompute_findings_date is waiting for date-write:2026-01-21", 15)]


def test_should_use_in_process_background_kick_defaults_off_in_production(monkeypatch):
    monkeypatch.setenv("FC_ENV", "production")
    monkeypatch.delenv("FC_ENABLE_IN_PROCESS_JOB_KICK", raising=False)

    assert jobs._should_use_in_process_background_kick() is False


def test_should_use_in_process_background_kick_can_be_enabled_in_production(monkeypatch):
    monkeypatch.setenv("FC_ENV", "production")
    monkeypatch.setenv("FC_ENABLE_IN_PROCESS_JOB_KICK", "true")

    assert jobs._should_use_in_process_background_kick() is True


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
        lambda repo, dates, **kwargs: {dates[0].isoformat(): {"suspicious_conversions": 1}},
    )

    result, message = jobs.run_click_ingestion(datetime(2026, 1, 3).date())

    assert result == {"success": True, "count": 1, "findings": {"suspicious_conversions": 1}}
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
        lambda repo, dates, **kwargs: {dates[0].isoformat(): {"suspicious_conversions": 1}},
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


def test_run_recompute_findings_for_date_returns_generation_metadata(monkeypatch):
    class FakeRepo:
        pass

    monkeypatch.setattr(jobs, "get_repository", lambda: FakeRepo())
    monkeypatch.setattr(
        jobs.findings_service,
        "recompute_findings_for_dates",
        lambda repo, dates, **kwargs: {
            dates[0].isoformat(): {"suspicious_conversions": 1}
        },
    )

    result, message = jobs.run_recompute_findings_for_date(
        date(2026, 1, 21),
        generation_id="gen-1",
        trigger="settings_update",
        job_run_id="run-1",
        source_job_id="settings-job",
    )

    assert message == "Recomputed findings for 2026-01-21"
    assert result["generation_id"] == "gen-1"
    assert result["trigger"] == "settings_update"
    assert result["source_job_id"] == "settings-job"
    assert result["findings"] == {"suspicious_conversions": 1}


def test_run_master_sync_enqueues_findings_recompute_for_available_dates(monkeypatch):
    class FakeClient:
        def fetch_all_media_master(self):
            return [{"media_id": "m1"}]

        def fetch_all_promotion_master(self):
            return [{"program_id": "p1"}]

        def fetch_all_user_master(self):
            return [{"user_id": "u1"}]

    class FakeRepo:
        def ensure_master_schema(self):
            return None

        def bulk_upsert_media(self, media_list):
            return len(media_list)

        def bulk_upsert_promotions(self, promo_list):
            return len(promo_list)

        def bulk_upsert_users(self, user_list):
            return len(user_list)

        def fetch_all(self, query, params=None):
            normalized = " ".join(str(query).split())
            if "SELECT DISTINCT date FROM click_ipua_daily" in normalized:
                return [{"date": date(2026, 1, 3)}]
            if "SELECT DISTINCT date FROM conversion_ipua_daily" in normalized:
                return [{"date": date(2026, 1, 2)}]
            raise AssertionError(f"unexpected query: {query}")

    captured = {}
    monkeypatch.setattr(jobs, "get_repository", lambda: FakeRepo())
    monkeypatch.setattr(jobs, "get_acs_client", lambda: FakeClient())
    monkeypatch.setattr(
        jobs,
        "enqueue_findings_recompute_jobs",
        lambda dates, **kwargs: captured.update(
            {
                "dates": [target_date.isoformat() for target_date in dates],
                "kwargs": kwargs,
            }
        )
        or [type("QueuedJob", (), {"id": f"recompute-{index + 1}"})() for index, _ in enumerate(dates)],
    )

    result, message = jobs.run_master_sync(job_run_id="job-master-1")

    assert message == "Master sync completed"
    assert result["media_count"] == 1
    assert result["promotion_count"] == 1
    assert result["user_count"] == 1
    assert captured["dates"] == ["2026-01-03", "2026-01-02"]
    assert captured["kwargs"]["trigger"] == "master_sync"
    assert captured["kwargs"]["source_job_id"] == "job-master-1"
    assert result["findings_recompute"]["job_ids"] == ["recompute-1", "recompute-2"]
