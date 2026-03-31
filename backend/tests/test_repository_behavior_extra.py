from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime

import sqlalchemy as sa

from fraud_checker.repository_pg import PostgresRepository


def _new_repo() -> PostgresRepository:
    return object.__new__(PostgresRepository)


def test_browser_filter_sql_contains_includes_and_excludes():
    repo = _new_repo()

    sql = repo._browser_filter_sql()

    assert "useragent ILIKE" in sql
    assert "useragent NOT ILIKE" in sql


def test_datacenter_filter_sql_returns_empty_for_no_prefixes():
    repo = _new_repo()

    sql = repo._datacenter_filter_sql(())

    assert sql == ""


def test_count_raw_rows_returns_zero_when_raw_table_does_not_exist(monkeypatch):
    repo = _new_repo()
    monkeypatch.setattr(repo, "_table_exists", lambda name: False)

    count = repo.count_raw_rows(date(2026, 1, 1))

    assert count == 0


def test_count_raw_rows_returns_scalar_count(monkeypatch):
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

    count = repo.count_raw_rows(date(2026, 1, 1))

    assert count == 7


def test_fetch_suspicious_conversion_rollups_returns_empty_when_table_missing(monkeypatch):
    repo = _new_repo()
    monkeypatch.setattr(repo, "_table_exists", lambda name: False)

    rows = repo.fetch_suspicious_conversion_rollups(date(2026, 1, 1))

    assert rows == []


def test_lookup_clicks_methods_cover_missing_and_found_paths(monkeypatch):
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

    one = repo.lookup_click_by_cid("cid-1")
    many = repo.lookup_clicks_by_cids(["cid-1"])

    assert one is not None
    assert one[0] == "1.1.1.1"
    assert many["cid-1"][1] == "Mozilla/5.0"


def test_get_existing_ids_return_sets(monkeypatch):
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

    click_ids = repo.get_existing_click_ids(["c1", "c2", "c3"])
    conv_ids = repo.get_existing_conversion_ids(["v1", "v2"])

    assert click_ids == {"c1", "c2"}
    assert conv_ids == {"v1"}


def test_get_suspicious_conversion_detail_bulk_maps_rows(monkeypatch):
    repo = _new_repo()

    class DummyConn:
        def execute(self, stmt, params=None):
            sql = stmt.text if isinstance(stmt, sa.sql.elements.TextClause) else str(stmt)
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

    conv = repo.get_suspicious_conversion_details_bulk(date(2026, 1, 1), [("1.1.1.1", "UA")])

    assert conv[("1.1.1.1", "UA")][0]["program_name"] == "p1"


def test_get_daily_finding_counts_uses_generation_join(monkeypatch):
    repo = _new_repo()
    monkeypatch.setattr(repo, "_table_exists", lambda name: True)
    captured = {}

    def fake_fetch_all(query, params=None):
        captured["query"] = query
        captured["params"] = params
        return [{"date": date(2026, 1, 1), "suspicious_conversions": 3}]

    monkeypatch.setattr(repo, "fetch_all", fake_fetch_all)

    counts = repo.get_daily_finding_counts(7, target_date=date(2026, 1, 10))

    assert "findings_generations" in captured["query"]
    assert captured["params"]["target_date"] == date(2026, 1, 10)
    assert counts == {"2026-01-01": {"suspicious_conversions": 3}}


def test_save_settings_returns_without_execute_when_empty(monkeypatch):
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

    repo.save_settings({}, fingerprint="unused")

    assert executed["count"] == 0
