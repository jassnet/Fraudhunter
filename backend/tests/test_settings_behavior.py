from __future__ import annotations

from fraud_checker.services import settings as settings_service


def test_get_settings_merges_env_defaults_and_db_overrides(monkeypatch):
    # Given
    class DummyRepo:
        def load_settings(self):
            return {"click_threshold": 99}

    monkeypatch.setattr(
        settings_service,
        "_load_settings_from_env",
        lambda: {"click_threshold": 50, "media_threshold": 3},
    )
    settings_service._settings_cache = None

    # When
    settings = settings_service.get_settings(DummyRepo())

    # Then
    assert settings["click_threshold"] == 99
    assert settings["media_threshold"] == 3


def test_get_settings_uses_cache_after_first_load(monkeypatch):
    # Given
    class DummyRepo:
        def __init__(self):
            self.calls = 0

        def load_settings(self):
            self.calls += 1
            return {"click_threshold": 55}

    monkeypatch.setattr(settings_service, "_load_settings_from_env", lambda: {"click_threshold": 50})
    settings_service._settings_cache = None
    repo = DummyRepo()

    # When
    first = settings_service.get_settings(repo)
    second = settings_service.get_settings(repo)

    # Then
    assert first["click_threshold"] == 55
    assert second["click_threshold"] == 55
    assert repo.calls == 1


def test_update_settings_enqueues_findings_recompute_jobs(monkeypatch):
    # Given
    class DummyRepo:
        def save_settings(self, settings, *, fingerprint):
            assert fingerprint
            return "settings-ver-1"

        def get_settings_updated_at(self):
            return None

    monkeypatch.setattr(
        "fraud_checker.services.reporting.get_available_dates",
        lambda repo: ["2026-01-20", "2026-01-21"],
    )
    monkeypatch.setattr(
        "fraud_checker.services.jobs.enqueue_findings_recompute_jobs",
        lambda dates, **kwargs: [type("QueuedJob", (), {"id": f"job-{index + 1}"})() for index, _ in enumerate(dates)],
    )
    settings_service._settings_cache = None
    payload = {"click_threshold": 70}

    # When
    result = settings_service.update_settings(DummyRepo(), payload)

    # Then
    assert result["success"] is True
    assert result["persisted"] is True
    assert result["settings"] == payload
    assert result["settings_version_id"] == "settings-ver-1"
    assert result["settings_fingerprint"]
    assert result["findings_recomputed"] is False
    assert result["findings_recompute_enqueued"] is True
    assert result["recompute_job_ids"] == ["job-1", "job-2"]
    assert result["recompute_target_dates"] == ["2026-01-20", "2026-01-21"]


def test_update_settings_returns_warning_when_save_fails():
    # Given
    class DummyRepo:
        def save_settings(self, settings, *, fingerprint):
            raise RuntimeError("db is down")

    settings_service._settings_cache = None
    payload = {"click_threshold": 70}

    # When
    result = settings_service.update_settings(DummyRepo(), payload)

    # Then
    assert result["success"] is True
    assert result["persisted"] is False
    assert result["settings"] == payload
    assert "db is down" in result["warning"]


def test_update_settings_returns_warning_when_recompute_enqueue_fails(monkeypatch):
    class DummyRepo:
        def save_settings(self, settings, *, fingerprint):
            return "settings-ver-1"

        def get_settings_updated_at(self):
            return None

    monkeypatch.setattr(
        "fraud_checker.services.reporting.get_available_dates",
        lambda repo: ["2026-01-20"],
    )
    monkeypatch.setattr(
        "fraud_checker.services.jobs.enqueue_findings_recompute_jobs",
        lambda dates, **kwargs: (_ for _ in ()).throw(RuntimeError("queue unavailable")),
    )
    settings_service._settings_cache = None

    result = settings_service.update_settings(DummyRepo(), {"click_threshold": 70})

    assert result["success"] is True
    assert result["persisted"] is True
    assert result["findings_recomputed"] is False
    assert result["findings_recompute_enqueued"] is False
    assert "queue unavailable" in result["warning"]
