from __future__ import annotations

import json
from datetime import datetime, timedelta

from fraud_checker import job_status_pg
from fraud_checker import job_status_queue


class _DummyContext:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self.conn

    def __exit__(self, exc_type, exc, tb):
        return False


def _new_store() -> job_status_pg.JobStatusStorePG:
    return object.__new__(job_status_pg.JobStatusStorePG)


def test_ensure_schema_creates_job_runs_table(monkeypatch):
    store = _new_store()
    calls = {"create_all": 0}
    store.engine = object()
    monkeypatch.setattr(
        job_status_pg.Base.metadata,
        "create_all",
        lambda engine, tables: calls.__setitem__("create_all", calls["create_all"] + 1),
    )

    store.ensure_schema()

    assert calls["create_all"] == 1


def test_get_returns_idle_when_no_job_has_run(monkeypatch):
    store = _new_store()
    monkeypatch.setattr(store, "_fetch_latest_run", lambda: None)
    monkeypatch.setattr(
        store,
        "get_queue_metrics",
        lambda: {
            "queued_jobs_count": 0,
            "retry_scheduled_jobs_count": 0,
            "running_jobs_count": 0,
            "failed_jobs_count": 0,
            "oldest_queued_at": None,
            "oldest_queued_age_seconds": None,
        },
    )

    status = store.get()

    assert status.status == "idle"
    assert status.job_id is None
    assert status.message == "まだジョブは実行されていません"
    assert status.queue == {
        "queued": 0,
        "retry_scheduled": 0,
        "running": 0,
        "failed": 0,
        "oldest_queued_at": None,
        "oldest_queued_age_seconds": None,
    }


def test_get_preserves_queued_job_status(monkeypatch):
    store = _new_store()
    monkeypatch.setattr(
        store,
        "_fetch_latest_run",
        lambda: job_status_pg.JobRun(
            id="run-1",
            job_type="refresh",
            status="queued",
            params={"hours": 1},
            result=None,
            error_message=None,
            message="直近1時間の再取得ジョブを登録しました",
            attempt_count=0,
            max_attempts=4,
            next_retry_at=None,
            dedupe_key='refresh:{"hours":1}',
            priority=10,
            queued_at=datetime(2026, 1, 1, 0, 0, 0),
            started_at=None,
            finished_at=None,
            heartbeat_at=None,
            locked_until=None,
            worker_id=None,
        ),
    )
    monkeypatch.setattr(
        store,
        "get_queue_metrics",
        lambda: {
            "queued_jobs_count": 1,
            "retry_scheduled_jobs_count": 0,
            "running_jobs_count": 0,
            "failed_jobs_count": 0,
            "oldest_queued_at": None,
            "oldest_queued_age_seconds": None,
        },
    )

    status = store.get()

    assert status.status == "queued"
    assert status.job_id == "run-1"
    assert status.message == "直近1時間の再取得ジョブを登録しました"
    assert status.queue == {
        "queued": 1,
        "retry_scheduled": 0,
        "running": 0,
        "failed": 0,
        "oldest_queued_at": None,
        "oldest_queued_age_seconds": None,
    }


def test_enqueue_persists_json_payload_and_control_columns(monkeypatch):
    store = _new_store()
    captured = {}
    fixed_now = datetime(2026, 1, 1, 0, 0, 0)
    monkeypatch.setattr(job_status_queue, "now_local", lambda: fixed_now)
    monkeypatch.setattr(job_status_queue.uuid, "uuid4", lambda: type("U", (), {"hex": "run-1"})())

    class DummyConn:
        def execute(self, stmt, params=None):
            captured["params"] = params
            return None

    class DummyEngine:
        def begin(self):
            return _DummyContext(DummyConn())

    store.engine = DummyEngine()

    run = store.enqueue(
        job_type="refresh",
        params={"hours": 4, "clicks": True},
        message="queued",
        max_attempts=4,
        dedupe_key="refresh-key",
        priority=10,
        concurrency_key="date-write:2026-01-01",
    )

    assert run.id == "run-1"
    assert run.max_attempts == 4
    assert run.priority == 10
    assert run.concurrency_key == "date-write:2026-01-01"
    assert json.loads(captured["params"]["params_json"]) == {"hours": 4, "clicks": True}
    assert captured["params"]["dedupe_key"] == "refresh-key"
    assert captured["params"]["concurrency_key"] == "date-write:2026-01-01"
    assert captured["params"]["queued_at"] == fixed_now


def test_find_active_duplicate_returns_existing_run():
    store = _new_store()
    fixed_now = datetime(2026, 1, 1, 0, 0, 0)

    class DummyResult:
        def mappings(self):
            return self

        def first(self):
            return {
                "id": "run-dup",
                "job_type": "refresh",
                "status": "queued",
                "params_json": json.dumps({"hours": 1}),
                "result_json": None,
                "error_message": None,
                "message": "queued",
                "attempt_count": 0,
                "max_attempts": 4,
                "next_retry_at": None,
                "dedupe_key": "refresh-key",
                "priority": 10,
                "queued_at": fixed_now,
                "started_at": None,
                "finished_at": None,
                "heartbeat_at": None,
                "locked_until": None,
                "worker_id": None,
            }

    class DummyConn:
        def execute(self, stmt, params=None):
            return DummyResult()

    class DummyEngine:
        def begin(self):
            return _DummyContext(DummyConn())

    store.engine = DummyEngine()
    run = store.find_active_duplicate("refresh-key")

    assert run is not None
    assert run.id == "run-dup"
    assert run.dedupe_key == "refresh-key"


def test_acquire_next_sets_running_and_lease(monkeypatch):
    store = _new_store()
    fixed_now = datetime(2026, 1, 1, 0, 0, 0)
    monkeypatch.setattr(job_status_queue, "now_local", lambda: fixed_now)
    monkeypatch.setattr(store, "recover_stale_runs", lambda: 0)

    row = {
        "id": "run-1",
        "job_type": "refresh",
        "status": "running",
        "params_json": json.dumps({"hours": 1}),
        "result_json": None,
        "error_message": None,
        "message": "queued",
        "attempt_count": 0,
        "max_attempts": 4,
        "next_retry_at": None,
        "dedupe_key": "refresh-key",
        "priority": 10,
        "queued_at": fixed_now,
        "started_at": fixed_now,
        "finished_at": None,
        "heartbeat_at": fixed_now,
        "locked_until": fixed_now + timedelta(seconds=300),
        "worker_id": "worker-1",
    }
    captured = {}

    class DummyResult:
        def mappings(self):
            return self

        def first(self):
            return row

    class DummyConn:
        def execute(self, stmt, params=None):
            captured["params"] = params
            return DummyResult()

    class DummyEngine:
        def begin(self):
            return _DummyContext(DummyConn())

    store.engine = DummyEngine()

    run = store.acquire_next(worker_id="worker-1", lease_seconds=300)

    assert run is not None
    assert run.id == "run-1"
    assert captured["params"]["worker_id"] == "worker-1"
    assert captured["params"]["locked_until"] == fixed_now + timedelta(seconds=300)


def test_fail_requeues_when_attempts_remain(monkeypatch):
    store = _new_store()
    fixed_now = datetime(2026, 1, 1, 0, 5, 0)
    monkeypatch.setattr(job_status_queue, "now_local", lambda: fixed_now)
    monkeypatch.setattr(store, "_get_attempt_state", lambda run_id: {"attempt_count": 0, "max_attempts": 3})
    calls = []

    class DummyConn:
        def execute(self, stmt, params=None):
            calls.append(params)
            return None

    class DummyEngine:
        def begin(self):
            return _DummyContext(DummyConn())

    store.engine = DummyEngine()

    next_status = store.fail("run-1", "failed", {"success": False}, error_message="boom")

    assert next_status == "queued"
    assert calls[0]["attempt_count"] == 1
    assert calls[0]["next_retry_at"] == fixed_now + timedelta(seconds=30)
    assert calls[0]["finished_at"] is None


def test_fail_marks_terminal_failure_when_attempts_exhausted(monkeypatch):
    store = _new_store()
    fixed_now = datetime(2026, 1, 1, 0, 5, 0)
    monkeypatch.setattr(job_status_queue, "now_local", lambda: fixed_now)
    monkeypatch.setattr(store, "_get_attempt_state", lambda run_id: {"attempt_count": 2, "max_attempts": 3})
    calls = []

    class DummyConn:
        def execute(self, stmt, params=None):
            calls.append(params)
            return None

    class DummyEngine:
        def begin(self):
            return _DummyContext(DummyConn())

    store.engine = DummyEngine()

    next_status = store.fail("run-1", "failed", {"success": False}, error_message="boom")

    assert next_status == "failed"
    assert calls[0]["attempt_count"] == 3
    assert calls[0]["next_retry_at"] is None
    assert calls[0]["finished_at"] == fixed_now


def test_get_queue_metrics_returns_operational_counts(monkeypatch):
    store = _new_store()
    fixed_now = datetime(2026, 1, 1, 1, 0, 0)
    monkeypatch.setattr(job_status_queue, "now_local", lambda: fixed_now)

    class DummyResult:
        def mappings(self):
            return self

        def one(self):
            return {
                "queued_jobs_count": 2,
                "retry_scheduled_jobs_count": 1,
                "running_jobs_count": 1,
                "failed_jobs_count": 3,
                "oldest_queued_at": fixed_now - timedelta(minutes=15),
            }

    class DummyConn:
        def execute(self, stmt, params=None):
            return DummyResult()

    class DummyEngine:
        def begin(self):
            return _DummyContext(DummyConn())

    store.engine = DummyEngine()
    metrics = store.get_queue_metrics()

    assert metrics["queued_jobs_count"] == 2
    assert metrics["retry_scheduled_jobs_count"] == 1
    assert metrics["running_jobs_count"] == 1
    assert metrics["failed_jobs_count"] == 3
    assert metrics["oldest_queued_age_seconds"] == 900


def test_has_active_job_returns_true_for_running_or_queued():
    store = _new_store()

    class DummyConn:
        def execute(self, stmt, params=None):
            return type("ScalarResult", (), {"scalar_one": lambda self: 1})()

    class DummyEngine:
        def begin(self):
            return _DummyContext(DummyConn())

    store.engine = DummyEngine()

    assert store.has_active_job() is True
