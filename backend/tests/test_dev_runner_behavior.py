from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_dev_module():
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location("dev_runner", root / "dev.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_worker_enabled_defaults_true(monkeypatch):
    monkeypatch.delenv("WORKER_ENABLED", raising=False)
    dev = _load_dev_module()
    assert dev._worker_enabled() is True


def test_build_worker_cmd_uses_in_process_queue_runner(monkeypatch):
    monkeypatch.setenv("WORKER_MAX_JOBS", "7")
    monkeypatch.setenv("WORKER_POLL_SECONDS", "3")
    dev = _load_dev_module()

    cmd = dev._build_worker_cmd()

    assert cmd[:3] == [dev.sys.executable, "-u", "-c"]
    assert "process_queued_jobs" in cmd[3]
    assert "max_jobs=7" in cmd[3]
    assert "time.sleep(3)" in cmd[3]


def test_build_backend_cmd_uses_configured_port(monkeypatch):
    monkeypatch.setenv("BACKEND_PORT", "8123")
    dev = _load_dev_module()

    cmd = dev._build_backend_cmd()

    assert cmd[-1] == "8123"
