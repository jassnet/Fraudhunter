from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime

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


def test_ensure_schema_creates_table_and_inserts_singleton_row(monkeypatch):
    # Given
    store = _new_store()
    calls = {"create_all": 0, "executed": 0}

    class DummyConn:
        def execute(self, stmt, params=None):
            calls["executed"] += 1

    class DummyEngine:
        def begin(self):
            return _DummyContext(DummyConn())

    store.engine = DummyEngine()
    monkeypatch.setattr(
        job_status_pg.Base.metadata,
        "create_all",
        lambda engine, tables: calls.__setitem__("create_all", calls["create_all"] + 1),
    )

    # When
    store.ensure_schema()

    # Then
    assert calls["create_all"] == 1
    assert calls["executed"] == 2


def test_get_returns_default_idle_when_row_is_missing(monkeypatch):
    # Given
    store = _new_store()
    monkeypatch.setattr(store, "ensure_schema", lambda: None)

    class DummyResult:
        def mappings(self):
            return self

        def first(self):
            return None

    class DummyConn:
        def execute(self, stmt, params=None):
            return DummyResult()

    class DummyEngine:
        def begin(self):
            return _DummyContext(DummyConn())

    store.engine = DummyEngine()

    # When
    status = store.get()

    # Then
    assert status.status == "idle"
    assert status.job_id is None
    assert status.message == "まだジョブは実行されていません"
    assert status.result is None


def test_get_normalizes_legacy_english_messages(monkeypatch):
    # Given
    store = _new_store()
    monkeypatch.setattr(store, "ensure_schema", lambda: None)
    row = {
        "status": "idle",
        "job_id": None,
        "message": "No job has been run yet",
        "started_at": None,
        "completed_at": None,
        "result_json": None,
    }

    class DummyResult:
        def mappings(self):
            return self

        def first(self):
            return row

    class DummyConn:
        def execute(self, stmt, params=None):
            return DummyResult()

    class DummyEngine:
        def begin(self):
            return _DummyContext(DummyConn())

    store.engine = DummyEngine()

    # When
    status = store.get()

    # Then
    assert status.message == "まだジョブは実行されていません"


def test_get_parses_json_result_when_row_exists(monkeypatch):
    # Given
    store = _new_store()
    monkeypatch.setattr(store, "ensure_schema", lambda: None)
    row = {
        "status": "completed",
        "job_id": "refresh_1h",
        "message": "done",
        "started_at": "2026-01-01T00:00:00",
        "completed_at": "2026-01-01T00:01:00",
        "result_json": json.dumps({"success": True}),
    }

    class DummyResult:
        def mappings(self):
            return self

        def first(self):
            return row

    class DummyConn:
        def execute(self, stmt, params=None):
            return DummyResult()

    class DummyEngine:
        def begin(self):
            return _DummyContext(DummyConn())

    store.engine = DummyEngine()

    # When
    status = store.get()

    # Then
    assert status.status == "completed"
    assert status.job_id == "refresh_1h"
    assert status.result == {"success": True}


def test_start_returns_true_when_update_succeeds(monkeypatch):
    # Given
    store = _new_store()
    monkeypatch.setattr(store, "ensure_schema", lambda: None)
    monkeypatch.setattr(job_status_pg, "now_local", lambda: datetime(2026, 1, 1, 0, 0, 0))

    class DummyResult:
        rowcount = 1

    class DummyConn:
        def execute(self, stmt, params=None):
            return DummyResult()

    class DummyEngine:
        def begin(self):
            return _DummyContext(DummyConn())

    store.engine = DummyEngine()

    # When
    ok = store.start("refresh_1h", "start")

    # Then
    assert ok is True


def test_start_returns_false_when_update_does_not_change_rows(monkeypatch):
    # Given
    store = _new_store()
    monkeypatch.setattr(store, "ensure_schema", lambda: None)
    monkeypatch.setattr(job_status_pg, "now_local", lambda: datetime(2026, 1, 1, 0, 0, 0))

    class DummyResult:
        rowcount = 0

    class DummyConn:
        def execute(self, stmt, params=None):
            return DummyResult()

    class DummyEngine:
        def begin(self):
            return _DummyContext(DummyConn())

    store.engine = DummyEngine()

    # When
    ok = store.start("refresh_1h", "start")

    # Then
    assert ok is False


def test_complete_and_fail_delegate_to_finish(monkeypatch):
    # Given
    store = _new_store()
    called = []
    monkeypatch.setattr(
        store,
        "_finish",
        lambda job_id, status, message, result: called.append((job_id, status, message, result)),
    )

    # When
    store.complete("j1", "done", {"success": True})
    store.fail("j2", "failed", {"success": False})

    # Then
    assert called == [
        ("j1", "completed", "done", {"success": True}),
        ("j2", "failed", "failed", {"success": False}),
    ]


def test_finish_serializes_result_and_executes_update(monkeypatch):
    # Given
    store = _new_store()
    monkeypatch.setattr(store, "ensure_schema", lambda: None)
    monkeypatch.setattr(job_status_pg, "now_local", lambda: datetime(2026, 1, 1, 0, 0, 0))
    captured = {}

    class DummyConn:
        def execute(self, stmt, params=None):
            captured["params"] = params
            return None

    class DummyEngine:
        def begin(self):
            return _DummyContext(DummyConn())

    store.engine = DummyEngine()

    # When
    store._finish("refresh_1h", "completed", "done", {"success": True})

    # Then
    assert captured["params"]["job_id"] == "refresh_1h"
    assert captured["params"]["status"] == "completed"
    assert json.loads(captured["params"]["result_json"]) == {"success": True}
