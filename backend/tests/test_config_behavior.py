from __future__ import annotations

import pytest

from fraud_checker import config


def test_resolve_acs_settings_parses_token_and_normalizes_values(monkeypatch):
    # Given
    monkeypatch.setattr(config, "load_env", lambda *args, **kwargs: None)
    monkeypatch.delenv("ACS_ACCESS_KEY", raising=False)
    monkeypatch.delenv("ACS_SECRET_KEY", raising=False)
    monkeypatch.setenv("ACS_BASE_URL", "https://acs.example.com/")
    monkeypatch.setenv("ACS_TOKEN", "access:secret")
    monkeypatch.setenv("FRAUD_PAGE_SIZE", "250")
    monkeypatch.setenv("ACS_LOG_ENDPOINT", "/track_log/search")

    # When
    settings = config.resolve_acs_settings()

    # Then
    assert settings.base_url == "https://acs.example.com"
    assert settings.access_key == "access"
    assert settings.secret_key == "secret"
    assert settings.page_size == 250
    assert settings.log_endpoint == "track_log/search"


def test_resolve_acs_settings_rejects_insecure_url_by_default(monkeypatch):
    # Given
    monkeypatch.setattr(config, "load_env", lambda *args, **kwargs: None)
    monkeypatch.setenv("ACS_BASE_URL", "http://acs.example.com")
    monkeypatch.setenv("ACS_ACCESS_KEY", "access")
    monkeypatch.setenv("ACS_SECRET_KEY", "secret")
    monkeypatch.delenv("ACS_ALLOW_INSECURE", raising=False)

    # When / Then
    with pytest.raises(ValueError, match="must use https"):
        config.resolve_acs_settings()


def test_resolve_acs_settings_requires_positive_page_size(monkeypatch):
    # Given
    monkeypatch.setattr(config, "load_env", lambda *args, **kwargs: None)
    monkeypatch.setenv("ACS_BASE_URL", "https://acs.example.com")
    monkeypatch.setenv("ACS_ACCESS_KEY", "access")
    monkeypatch.setenv("ACS_SECRET_KEY", "secret")
    monkeypatch.setenv("FRAUD_PAGE_SIZE", "0")

    # When / Then
    with pytest.raises(ValueError, match="positive integer"):
        config.resolve_acs_settings()


def test_resolve_rules_reads_env_and_overrides_explicit(monkeypatch):
    # Given
    monkeypatch.setattr(config, "load_env", lambda *args, **kwargs: None)
    monkeypatch.setenv("FRAUD_CLICK_THRESHOLD", "40")
    monkeypatch.setenv("FRAUD_MEDIA_THRESHOLD", "2")
    monkeypatch.setenv("FRAUD_PROGRAM_THRESHOLD", "3")
    monkeypatch.setenv("FRAUD_BURST_CLICK_THRESHOLD", "10")
    monkeypatch.setenv("FRAUD_BURST_WINDOW_SECONDS", "300")
    monkeypatch.setenv("FRAUD_BROWSER_ONLY", "true")
    monkeypatch.setenv("FRAUD_EXCLUDE_DATACENTER_IP", "true")

    # When
    rules = config.resolve_rules(click_threshold=44)

    # Then
    assert rules.click_threshold == 44
    assert rules.media_threshold == 2
    assert rules.program_threshold == 3
    assert rules.burst_click_threshold == 10
    assert rules.burst_window_seconds == 300
    assert rules.browser_only is True
    assert rules.exclude_datacenter_ip is True


def test_resolve_conversion_rules_uses_explicit_values(monkeypatch):
    # Given
    monkeypatch.setattr(config, "load_env", lambda *args, **kwargs: None)

    # When
    rules = config.resolve_conversion_rules(
        conversion_threshold=6,
        media_threshold=4,
        program_threshold=3,
        burst_conversion_threshold=2,
        burst_window_seconds=1200,
        browser_only=True,
        exclude_datacenter_ip=True,
        min_click_to_conv_seconds=8,
        max_click_to_conv_seconds=600,
    )

    # Then
    assert rules.conversion_threshold == 6
    assert rules.media_threshold == 4
    assert rules.program_threshold == 3
    assert rules.burst_conversion_threshold == 2
    assert rules.burst_window_seconds == 1200
    assert rules.browser_only is True
    assert rules.exclude_datacenter_ip is True
    assert rules.min_click_to_conv_seconds == 8
    assert rules.max_click_to_conv_seconds == 600
