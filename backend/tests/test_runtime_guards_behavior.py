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
