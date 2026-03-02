from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime

import sqlalchemy as sa

from fraud_checker.repository_pg import PostgresRepository


def _new_repo() -> PostgresRepository:
    return object.__new__(PostgresRepository)


def test_browser_filter_sql_contains_includes_and_excludes():
    # Given
    repo = _new_repo()

    # When
    sql = repo._browser_filter_sql()

    # Then
    assert "useragent ILIKE" in sql
    assert "useragent NOT ILIKE" in sql


def test_datacenter_filter_sql_returns_empty_for_no_prefixes():
    # Given
    repo = _new_repo()

    # When
    sql = repo._datacenter_filter_sql(())

    # Then
    assert sql == ""


def test_count_raw_rows_returns_zero_when_raw_table_does_not_exist(monkeypatch):
    # Given
    repo = _new_repo()
    monkeypatch.setattr(repo, "_table_exists", lambda name: False)

    # When
    count = repo.count_raw_rows(date(2026, 1, 1))

    # Then
    assert count == 0


def test_count_raw_rows_returns_scalar_count(monkeypatch):
    # Given
    repo = _new_repo()
    monkeypatch.setattr(repo, "_table_exists", lambda name: True)

    class DummyResult:
        def scalar_one(self):
            return 7

    class DummyConn:
        def execute(self, stmt, params=None):
            return DummyResult()

    @contextmanager
    def fake_connect():
        yield DummyConn()

    monkeypatch.setattr(repo, "_connect", fake_connect)

    # When
    count = repo.count_raw_rows(date(2026, 1, 1))

    # Then
    assert count == 7


def test_fetch_rollups_maps_rows_to_models(monkeypatch):
    # Given
    repo = _new_repo()
    rows = [
        (
            date(2026, 1, 1),
            "1.1.1.1",
            "Mozilla/5.0",
            10,
            2,
            3,
            datetime(2026, 1, 1, 0, 0, 0),
            datetime(2026, 1, 1, 0, 10, 0),
        )
    ]

    class DummyResult:
        def fetchall(self):
            return rows

    class DummyConn:
        def execute(self, stmt, params=None):
            return DummyResult()

    @contextmanager
    def fake_connect():
        yield DummyConn()

    monkeypatch.setattr(repo, "_connect", fake_connect)

    # When
    rollups = repo.fetch_rollups(date(2026, 1, 1))

    # Then
    assert len(rollups) == 1
    assert rollups[0].ipaddress == "1.1.1.1"
    assert rollups[0].total_clicks == 10


def test_fetch_suspicious_rollups_applies_filters_and_maps_rows(monkeypatch):
    # Given
    repo = _new_repo()
    captured = {}
    rows = [
        (
            date(2026, 1, 1),
            "1.1.1.1",
            "Mozilla/5.0",
            20,
            2,
            2,
            datetime(2026, 1, 1, 0, 0, 0),
            datetime(2026, 1, 1, 0, 1, 0),
        )
    ]

    class DummyResult:
        def fetchall(self):
            return rows

    class DummyConn:
        def execute(self, stmt, params=None):
            captured["sql"] = stmt.text if isinstance(stmt, sa.sql.elements.TextClause) else str(stmt)
            captured["params"] = params
            return DummyResult()

    @contextmanager
    def fake_connect():
        yield DummyConn()

    monkeypatch.setattr(repo, "_connect", fake_connect)

    # When
    rollups = repo.fetch_suspicious_rollups(
        date(2026, 1, 1),
        click_threshold=10,
        media_threshold=2,
        program_threshold=2,
        burst_click_threshold=20,
        browser_only=True,
        exclude_datacenter_ip=True,
    )

    # Then
    assert len(rollups) == 1
    assert "useragent ILIKE" in captured["sql"]
    assert "ipaddress NOT LIKE" in captured["sql"]
    assert captured["params"]["click_threshold"] == 10


def test_fetch_suspicious_conversion_rollups_returns_empty_when_table_missing(monkeypatch):
    # Given
    repo = _new_repo()
    monkeypatch.setattr(repo, "_table_exists", lambda name: False)

    # When
    rows = repo.fetch_suspicious_conversion_rollups(date(2026, 1, 1))

    # Then
    assert rows == []


def test_lookup_clicks_methods_cover_missing_and_found_paths(monkeypatch):
    # Given
    repo = _new_repo()
    monkeypatch.setattr(repo, "_table_exists", lambda name: True)

    class DummyConn:
        def execute(self, stmt, params=None):
            sql = stmt.text if isinstance(stmt, sa.sql.elements.TextClause) else str(stmt)
            if "WHERE id = :cid" in sql:
                class _Result:
                    def first(self_inner):
                        return ("1.1.1.1", "Mozilla/5.0", datetime(2026, 1, 1, 0, 0, 0))

                return _Result()
            if "WHERE id = ANY(:cids)" in sql:
                class _Result:
                    def fetchall(self_inner):
                        return [("cid-1", "1.1.1.1", "Mozilla/5.0", datetime(2026, 1, 1, 0, 0, 0))]

                return _Result()
            raise AssertionError(f"unexpected SQL: {sql}")

    @contextmanager
    def fake_connect():
        yield DummyConn()

    monkeypatch.setattr(repo, "_connect", fake_connect)

    # When
    one = repo.lookup_click_by_cid("cid-1")
    many = repo.lookup_clicks_by_cids(["cid-1"])

    # Then
    assert one is not None
    assert one[0] == "1.1.1.1"
    assert many["cid-1"][1] == "Mozilla/5.0"


def test_get_existing_ids_return_sets(monkeypatch):
    # Given
    repo = _new_repo()
    monkeypatch.setattr(repo, "_table_exists", lambda name: True)

    class DummyConn:
        def execute(self, stmt, params=None):
            sql = stmt.text if isinstance(stmt, sa.sql.elements.TextClause) else str(stmt)
            if "FROM click_raw" in sql:
                class _Result:
                    def fetchall(self_inner):
                        return [("c1",), ("c2",)]

                return _Result()
            if "FROM conversion_raw" in sql:
                class _Result:
                    def fetchall(self_inner):
                        return [("v1",)]

                return _Result()
            raise AssertionError(f"unexpected SQL: {sql}")

    @contextmanager
    def fake_connect():
        yield DummyConn()

    monkeypatch.setattr(repo, "_connect", fake_connect)

    # When
    click_ids = repo.get_existing_click_ids(["c1", "c2", "c3"])
    conv_ids = repo.get_existing_conversion_ids(["v1", "v2"])

    # Then
    assert click_ids == {"c1", "c2"}
    assert conv_ids == {"v1"}


def test_get_suspicious_detail_bulk_methods_map_rows(monkeypatch):
    # Given
    repo = _new_repo()

    class DummyConn:
        def execute(self, stmt, params=None):
            sql = stmt.text if isinstance(stmt, sa.sql.elements.TextClause) else str(stmt)
            if "FROM click_ipua_daily" in sql:
                class _Result:
                    def fetchall(self_inner):
                        return [("1.1.1.1", "UA", "m1", "p1", 9, None, None, None)]

                return _Result()
            if "FROM conversion_ipua_daily" in sql:
                class _Result:
                    def fetchall(self_inner):
                        return [("1.1.1.1", "UA", "m1", "p1", 3, None, None, None)]

                return _Result()
            raise AssertionError(f"unexpected SQL: {sql}")

    @contextmanager
    def fake_connect():
        yield DummyConn()

    monkeypatch.setattr(repo, "_connect", fake_connect)

    # When
    click = repo.get_suspicious_click_details_bulk(date(2026, 1, 1), [("1.1.1.1", "UA")])
    conv = repo.get_suspicious_conversion_details_bulk(date(2026, 1, 1), [("1.1.1.1", "UA")])

    # Then
    assert click[("1.1.1.1", "UA")][0]["media_name"] == "m1"
    assert conv[("1.1.1.1", "UA")][0]["program_name"] == "p1"


def test_save_settings_returns_without_execute_when_empty(monkeypatch):
    # Given
    repo = _new_repo()
    monkeypatch.setattr(repo, "ensure_settings_schema", lambda: None)
    executed = {"count": 0}

    class DummyConn:
        def execute(self, stmt, params=None):
            executed["count"] += 1

    @contextmanager
    def fake_connect():
        yield DummyConn()

    monkeypatch.setattr(repo, "_connect", fake_connect)

    # When
    repo.save_settings({})

    # Then
    assert executed["count"] == 0
