from __future__ import annotations

import pytest

import fraud_checker.db.session as db_session


def test_normalize_database_url_converts_postgres_prefixes():
    # When / Then
    assert db_session.normalize_database_url("postgres://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert db_session.normalize_database_url("postgresql://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert db_session.normalize_database_url("postgresql+psycopg://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert db_session.normalize_database_url("sqlite:///tmp.db") == "sqlite:///tmp.db"


def test_get_database_url_raises_when_env_is_missing(monkeypatch):
    # Given
    monkeypatch.delenv("DATABASE_URL", raising=False)

    # When / Then
    with pytest.raises(RuntimeError, match="DATABASE_URL is not set"):
        db_session.get_database_url()


def test_get_database_url_returns_normalized_env_value(monkeypatch):
    # Given
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h/db")

    # When
    url = db_session.get_database_url()

    # Then
    assert url == "postgresql+psycopg://u:p@h/db"


def test_get_engine_uses_explicit_url(monkeypatch):
    # Given
    captured = {}

    def fake_create_engine(url):
        captured["url"] = url
        return "ENGINE"

    monkeypatch.setattr(db_session, "create_engine", fake_create_engine)

    # When
    engine = db_session.get_engine("postgres://u:p@h/db")

    # Then
    assert engine == "ENGINE"
    assert captured["url"] == "postgresql+psycopg://u:p@h/db"


def test_get_sessionmaker_binds_engine(monkeypatch):
    # Given
    monkeypatch.setattr(db_session, "get_engine", lambda url=None: "ENGINE")
    monkeypatch.setattr(db_session, "sessionmaker", lambda bind: {"bind": bind})

    # When
    maker = db_session.get_sessionmaker("postgres://u:p@h/db")

    # Then
    assert maker == {"bind": "ENGINE"}
