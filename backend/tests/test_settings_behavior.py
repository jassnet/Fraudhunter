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


def test_update_settings_returns_persisted_true_when_save_succeeds():
    # Given
    class DummyRepo:
        def save_settings(self, settings, *, fingerprint):
            assert fingerprint
            return "settings-ver-1"

        def get_settings_updated_at(self):
            return None

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
