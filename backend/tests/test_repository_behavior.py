from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime

import pytest
import sqlalchemy as sa

from fraud_checker.models import ConversionLog
from fraud_checker.repository_pg import PostgresRepository


def _new_repo() -> PostgresRepository:
    return object.__new__(PostgresRepository)


def _conversion(conversion_id: str, cid: str | None) -> ConversionLog:
    return ConversionLog(
        conversion_id=conversion_id,
        cid=cid,
        conversion_time=datetime(2026, 1, 1, 12, 0, 0),
        click_time=datetime(2026, 1, 1, 11, 59, 50),
        media_id="m1",
        program_id="p1",
        user_id="u1",
        postback_ipaddress="10.0.0.1",
        postback_useragent="postback",
        entry_ipaddress="2.2.2.2",
        entry_useragent="Mozilla/5.0",
        state="approved",
        raw_payload={},
    )


def test_normalize_query_converts_positional_parameters():
    # Given
    repo = _new_repo()

    # When
    query, params = repo._normalize_query("SELECT * FROM t WHERE a = ? AND b = ?", (10, "x"))

    # Then
    assert query == "SELECT * FROM t WHERE a = :p0 AND b = :p1"
    assert params == {"p0": 10, "p1": "x"}


def test_normalize_query_raises_when_placeholder_count_mismatches():
    # Given
    repo = _new_repo()

    # When / Then
    with pytest.raises(ValueError):
        repo._normalize_query("SELECT * FROM t WHERE a = ? AND b = ?", (10,))


def test_fetch_click_to_conversion_gaps_returns_empty_when_table_missing(monkeypatch):
    # Given
    repo = _new_repo()
    monkeypatch.setattr(repo, "_table_exists", lambda name: False)

    # When
    result = repo.fetch_click_to_conversion_gaps(datetime(2026, 1, 1).date())

    # Then
    assert result == {}


def test_fetch_click_to_conversion_gaps_aggregates_min_max_and_count(monkeypatch):
    # Given
    repo = _new_repo()
    monkeypatch.setattr(repo, "_table_exists", lambda name: True)
    rows = [
        (
            "1.1.1.1",
            "Mozilla/5.0",
            datetime(2026, 1, 1, 12, 0, 5),
            datetime(2026, 1, 1, 12, 0, 0),
        ),
        (
            "1.1.1.1",
            "Mozilla/5.0",
            datetime(2026, 1, 1, 12, 1, 0),
            datetime(2026, 1, 1, 12, 0, 0),
        ),
        (
            "2.2.2.2",
            "Safari/605",
            datetime(2026, 1, 1, 12, 0, 3),
            datetime(2026, 1, 1, 12, 0, 0),
        ),
    ]

    class DummyResult:
        def fetchall(self):
            return rows

    class DummyConn:
        def execute(self, stmt, params):
            return DummyResult()

    @contextmanager
    def fake_connect():
        yield DummyConn()

    monkeypatch.setattr(repo, "_connect", fake_connect)

    # When
    result = repo.fetch_click_to_conversion_gaps(datetime(2026, 1, 1).date())

    # Then
    assert result[("1.1.1.1", "Mozilla/5.0")]["min"] == 5.0
    assert result[("1.1.1.1", "Mozilla/5.0")]["max"] == 60.0
    assert result[("1.1.1.1", "Mozilla/5.0")]["count"] == 2
    assert result[("2.2.2.2", "Safari/605")]["min"] == 3.0


def test_enrich_conversions_with_click_info_matches_by_cid(monkeypatch):
    # Given
    repo = _new_repo()
    conversions = [_conversion("conv-1", "cid-1"), _conversion("conv-2", "cid-2"), _conversion("conv-3", None)]
    monkeypatch.setattr(
        repo,
        "lookup_clicks_by_cids",
        lambda cids: {"cid-1": ("3.3.3.3", "Chrome/120", datetime(2026, 1, 1, 11, 0, 0))},
    )

    # When
    enriched = repo.enrich_conversions_with_click_info(conversions)

    # Then
    assert len(enriched) == 1
    assert enriched[0].conversion.conversion_id == "conv-1"
    assert enriched[0].click_ipaddress == "3.3.3.3"
    assert getattr(conversions[0], "click_ipaddress") == "3.3.3.3"


def test_get_all_masters_returns_counts_and_last_synced(monkeypatch):
    # Given
    repo = _new_repo()
    monkeypatch.setattr(repo, "ensure_master_schema", lambda: None)
    last_synced = datetime(2026, 1, 1, 12, 34, 56)

    class ScalarResult:
        def __init__(self, value):
            self.value = value

        def scalar_one(self):
            return self.value

    class FirstResult:
        def __init__(self, value):
            self.value = value

        def first(self):
            return (self.value,)

    class DummyConn:
        def execute(self, stmt):
            sql = stmt.text if isinstance(stmt, sa.sql.elements.TextClause) else str(stmt)
            if "COUNT(*) FROM master_media" in sql:
                return ScalarResult(3)
            if "COUNT(*) FROM master_promotion" in sql:
                return ScalarResult(2)
            if "COUNT(*) FROM master_user" in sql:
                return ScalarResult(5)
            return FirstResult(last_synced)

    @contextmanager
    def fake_connect():
        yield DummyConn()

    monkeypatch.setattr(repo, "_connect", fake_connect)

    # When
    stats = repo.get_all_masters()

    # Then
    assert stats["media_count"] == 3
    assert stats["promotion_count"] == 2
    assert stats["user_count"] == 5
    assert stats["last_synced_at"] == last_synced


def test_load_settings_parses_json_and_keeps_plain_text(monkeypatch):
    # Given
    repo = _new_repo()
    monkeypatch.setattr(repo, "ensure_settings_schema", lambda: None)
    rows = [("click_threshold", "50"), ("feature_note", "plain-text")]

    class DummyResult:
        def fetchall(self):
            return rows

    class DummyConn:
        def execute(self, stmt):
            return DummyResult()

    @contextmanager
    def fake_connect():
        yield DummyConn()

    monkeypatch.setattr(repo, "_connect", fake_connect)

    # When
    settings = repo.load_settings()

    # Then
    assert settings is not None
    assert settings["click_threshold"] == 50
    assert settings["feature_note"] == "plain-text"
