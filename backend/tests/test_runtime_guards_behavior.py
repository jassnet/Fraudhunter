from __future__ import annotations

import pytest

from fraud_checker import runtime_guards


def test_validate_runtime_guards_rejects_insecure_admin_in_production(monkeypatch):
    monkeypatch.setenv("FC_ENV", "production")
    monkeypatch.setenv("FC_ALLOW_INSECURE_ADMIN", "true")
    monkeypatch.delenv("ACS_ALLOW_INSECURE", raising=False)

    with pytest.raises(RuntimeError, match="FC_ALLOW_INSECURE_ADMIN"):
        runtime_guards.validate_runtime_guards()


def test_validate_runtime_guards_rejects_insecure_acs_in_production(monkeypatch):
    monkeypatch.setenv("FC_ENV", "production")
    monkeypatch.setenv("ACS_ALLOW_INSECURE", "true")
    monkeypatch.delenv("FC_ALLOW_INSECURE_ADMIN", raising=False)

    with pytest.raises(RuntimeError, match="ACS_ALLOW_INSECURE"):
        runtime_guards.validate_runtime_guards()


def test_should_enable_docs_defaults_to_disabled_in_production(monkeypatch):
    monkeypatch.setenv("FC_ENV", "production")
    monkeypatch.delenv("FC_ENABLE_API_DOCS", raising=False)

    assert runtime_guards.should_enable_docs() is False


def test_validate_runtime_guards_requires_explicit_read_access_mode_in_production(monkeypatch):
    monkeypatch.setenv("FC_ENV", "production")
    monkeypatch.delenv("FC_ALLOW_INSECURE_ADMIN", raising=False)
    monkeypatch.delenv("ACS_ALLOW_INSECURE", raising=False)
    monkeypatch.delenv("FC_REQUIRE_READ_AUTH", raising=False)
    monkeypatch.delenv("FC_EXTERNAL_READ_PROTECTION", raising=False)
    monkeypatch.delenv("FC_ALLOW_PUBLIC_READ", raising=False)

    with pytest.raises(RuntimeError, match="read-access posture"):
        runtime_guards.validate_runtime_guards()


def test_read_access_mode_accepts_exactly_one_configuration(monkeypatch):
    monkeypatch.setenv("FC_ENV", "production")
    monkeypatch.setenv("FC_REQUIRE_READ_AUTH", "true")
    monkeypatch.delenv("FC_EXTERNAL_READ_PROTECTION", raising=False)
    monkeypatch.delenv("FC_ALLOW_PUBLIC_READ", raising=False)

    assert runtime_guards.read_access_mode() == "read_auth"
