from __future__ import annotations

import json
from datetime import datetime, timedelta

from fraud_checker import job_status_pg


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

    status = store.get()

    assert status.status == "idle"
    assert status.job_id is None
    assert status.message == "まだジョブは実行されていません"


def test_get_maps_queued_job_to_running_for_api(monkeypatch):
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
            message="直近1時間の再取得を開始しました",
            queued_at=datetime(2026, 1, 1, 0, 0, 0),
            started_at=None,
            finished_at=None,
            heartbeat_at=None,
            locked_until=None,
            worker_id=None,
        ),
    )

    status = store.get()

    assert status.status == "running"
    assert status.job_id == "run-1"
    assert status.message == "直近1時間の再取得を開始しました"


def test_enqueue_persists_json_payload(monkeypatch):
    store = _new_store()
    captured = {}
    fixed_now = datetime(2026, 1, 1, 0, 0, 0)
    monkeypatch.setattr(job_status_pg, "now_local", lambda: fixed_now)
    monkeypatch.setattr(job_status_pg.uuid, "uuid4", lambda: type("U", (), {"hex": "run-1"})())

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
    )

    assert run.id == "run-1"
    assert json.loads(captured["params"]["params_json"]) == {"hours": 4, "clicks": True}
    assert captured["params"]["queued_at"] == fixed_now


def test_acquire_next_sets_running_and_lease(monkeypatch):
    store = _new_store()
    fixed_now = datetime(2026, 1, 1, 0, 0, 0)
    monkeypatch.setattr(job_status_pg, "now_local", lambda: fixed_now)
    monkeypatch.setattr(store, "recover_stale_runs", lambda: 0)

    row = {
        "id": "run-1",
        "job_type": "refresh",
        "status": "running",
        "params_json": json.dumps({"hours": 1}),
        "result_json": None,
        "error_message": None,
        "message": "queued",
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


def test_complete_and_fail_write_terminal_state(monkeypatch):
    store = _new_store()
    fixed_now = datetime(2026, 1, 1, 0, 5, 0)
    monkeypatch.setattr(job_status_pg, "now_local", lambda: fixed_now)
    calls = []

    class DummyConn:
        def execute(self, stmt, params=None):
            calls.append(params)
            return None

    class DummyEngine:
        def begin(self):
            return _DummyContext(DummyConn())

    store.engine = DummyEngine()

    store.complete("run-1", "done", {"success": True})
    store.fail("run-2", "failed", {"success": False}, error_message="boom")

    assert calls[0]["run_id"] == "run-1"
    assert json.loads(calls[0]["result_json"]) == {"success": True}
    assert calls[1]["run_id"] == "run-2"
    assert calls[1]["error_message"] == "boom"


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
