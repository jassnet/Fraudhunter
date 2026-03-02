from __future__ import annotations

from datetime import date

import pytest

from fraud_checker.services import reporting


class _LatestDateRepo:
    def __init__(self, value):
        self.value = value

    def fetch_one(self, query, params=None):
        return {"last_date": self.value}


def test_get_latest_date_rejects_unsupported_table():
    # Given
    repo = _LatestDateRepo(date(2026, 1, 2))

    # When / Then
    with pytest.raises(ValueError):
        reporting.get_latest_date(repo, "unsupported_table")


def test_get_latest_date_returns_none_when_table_has_no_rows():
    # Given
    repo = _LatestDateRepo(None)

    # When
    resolved = reporting.get_latest_date(repo, "click_ipua_daily")

    # Then
    assert resolved is None


def test_get_latest_date_converts_date_object_to_iso():
    # Given
    repo = _LatestDateRepo(date(2026, 1, 2))

    # When
    resolved = reporting.get_latest_date(repo, "conversion_ipua_daily")

    # Then
    assert resolved == "2026-01-02"


def test_resolve_summary_date_chooses_latest_across_click_and_conversion(monkeypatch):
    # Given
    monkeypatch.setattr(
        reporting,
        "get_latest_date",
        lambda repo, table: "2026-01-02" if table == "click_ipua_daily" else "2026-01-03",
    )

    # When
    resolved = reporting.resolve_summary_date(repo=object(), target_date=None)

    # Then
    assert resolved == "2026-01-03"


def test_resolve_summary_date_falls_back_to_yesterday(monkeypatch):
    # Given
    monkeypatch.setattr(reporting, "get_latest_date", lambda repo, table: None)
    monkeypatch.setattr(reporting, "today_local", lambda: date(2026, 1, 4))

    # When
    resolved = reporting.resolve_summary_date(repo=object(), target_date=None)

    # Then
    assert resolved == "2026-01-03"


def test_get_summary_returns_business_facing_totals(monkeypatch):
    # Given
    class DummyRepo:
        def fetch_one(self, query, params=None):
            if "total_clicks" in query:
                return {"total_clicks": 120, "unique_ips": 12, "active_media": 3}
            if "total_conversions" in query:
                return {"total_conversions": 8, "conversion_ips": 5}
            if "click_ipua_daily" in query and "prev_date" in query:
                return {"total": 100}
            if "conversion_ipua_daily" in query and "prev_date" in query:
                return {"total": 6}
            raise AssertionError(f"Unexpected query: {query}")

    class DummyClickDetector:
        def __init__(self, repo, rules):
            pass

        def find_for_date(self, target_date):
            return [1, 2]

    class DummyConversionDetector:
        def __init__(self, repo, rules):
            pass

        def find_for_date(self, target_date):
            return [1]

    monkeypatch.setattr(reporting, "resolve_summary_date", lambda repo, target_date: "2026-01-03")
    monkeypatch.setattr(reporting.settings_service, "build_rule_sets", lambda repo: ("c", "v"))
    monkeypatch.setattr(reporting, "SuspiciousDetector", DummyClickDetector)
    monkeypatch.setattr(reporting, "ConversionSuspiciousDetector", DummyConversionDetector)

    # When
    payload = reporting.get_summary(DummyRepo(), target_date=None)

    # Then
    assert payload["date"] == "2026-01-03"
    assert payload["stats"]["clicks"]["total"] == 120
    assert payload["stats"]["conversions"]["total"] == 8
    assert payload["stats"]["suspicious"]["click_based"] == 2
    assert payload["stats"]["suspicious"]["conversion_based"] == 1


def test_get_daily_stats_merges_click_and_conversion_rows(monkeypatch):
    # Given
    class DummyRepo:
        def fetch_all(self, query, params=None):
            if "FROM click_ipua_daily" in query:
                return [
                    {"date": date(2026, 1, 2), "clicks": 30},
                    {"date": date(2026, 1, 1), "clicks": 10},
                ]
            if "FROM conversion_ipua_daily" in query:
                return [
                    {"date": date(2026, 1, 2), "conversions": 5},
                    {"date": date(2025, 12, 31), "conversions": 2},
                ]
            raise AssertionError(f"Unexpected query: {query}")

    class DummyClickDetector:
        def __init__(self, repo, rules):
            pass

        def find_for_date(self, target_date):
            return [1] if target_date == date(2026, 1, 2) else []

    class DummyConversionDetector:
        def __init__(self, repo, rules):
            pass

        def find_for_date(self, target_date):
            return [1, 2] if target_date == date(2026, 1, 2) else []

    monkeypatch.setattr(reporting.settings_service, "build_rule_sets", lambda repo: ("c", "v"))
    monkeypatch.setattr(reporting, "SuspiciousDetector", DummyClickDetector)
    monkeypatch.setattr(reporting, "ConversionSuspiciousDetector", DummyConversionDetector)

    # When
    rows = reporting.get_daily_stats(DummyRepo(), limit=30)

    # Then
    assert [row["date"] for row in rows] == ["2025-12-31", "2026-01-01", "2026-01-02"]
    by_date = {row["date"]: row for row in rows}
    assert by_date["2026-01-02"]["clicks"] == 30
    assert by_date["2026-01-02"]["conversions"] == 5
    assert by_date["2026-01-02"]["suspicious_clicks"] == 1
    assert by_date["2026-01-02"]["suspicious_conversions"] == 2
    assert by_date["2025-12-31"]["clicks"] == 0


def test_get_available_dates_returns_unique_descending():
    # Given
    class DummyRepo:
        def fetch_all(self, query, params=None):
            if "click_ipua_daily" in query:
                return [{"date": date(2026, 1, 2)}, {"date": date(2026, 1, 1)}]
            if "conversion_ipua_daily" in query:
                return [{"date": date(2026, 1, 2)}, {"date": date(2025, 12, 31)}]
            raise AssertionError(f"Unexpected query: {query}")

    # When
    dates = reporting.get_available_dates(DummyRepo())

    # Then
    assert dates == ["2026-01-02", "2026-01-01", "2025-12-31"]


def test_get_summary_handles_datetime_style_resolved_date(monkeypatch):
    # Given
    class DummyRepo:
        def fetch_one(self, query, params=None):
            if "total_clicks" in query:
                return {"total_clicks": 0, "unique_ips": 0, "active_media": 0}
            if "total_conversions" in query:
                return {"total_conversions": 0, "conversion_ips": 0}
            if "click_ipua_daily" in query and "prev_date" in query:
                return {"total": 0}
            if "conversion_ipua_daily" in query and "prev_date" in query:
                return {"total": 0}
            raise AssertionError(f"Unexpected query: {query}")

    monkeypatch.setattr(
        reporting,
        "resolve_summary_date",
        lambda repo, target_date: "2026-01-03T12:00:00",
    )
    monkeypatch.setattr(reporting.settings_service, "build_rule_sets", lambda repo: ("c", "v"))

    # When
    payload = reporting.get_summary(DummyRepo(), target_date=None)

    # Then
    assert payload["date"] == "2026-01-03T12:00:00"
    assert payload["stats"]["suspicious"]["click_based"] == 0
    assert payload["stats"]["suspicious"]["conversion_based"] == 0


def test_get_daily_stats_skips_invalid_date_rows(monkeypatch):
    # Given
    class DummyRepo:
        def fetch_all(self, query, params=None):
            if "FROM click_ipua_daily" in query:
                return [{"date": "bad-date", "clicks": 1}]
            if "FROM conversion_ipua_daily" in query:
                return [{"date": date(2026, 1, 2), "conversions": 3}]
            raise AssertionError(f"Unexpected query: {query}")

    class DummyDetector:
        def __init__(self, repo, rules):
            pass

        def find_for_date(self, target_date):
            return []

    monkeypatch.setattr(reporting.settings_service, "build_rule_sets", lambda repo: ("c", "v"))
    monkeypatch.setattr(reporting, "SuspiciousDetector", DummyDetector)
    monkeypatch.setattr(reporting, "ConversionSuspiciousDetector", DummyDetector)

    # When
    rows = reporting.get_daily_stats(DummyRepo(), limit=30)

    # Then
    assert len(rows) == 2
    by_date = {row["date"]: row for row in rows}
    assert by_date["bad-date"]["suspicious_clicks"] == 0
