from __future__ import annotations

from datetime import date, datetime

import pytest

from fraud_checker.services import reporting


class _LatestDateRepo:
    def __init__(self, value):
        self.value = value

    def fetch_one(self, query, params=None):
        return {"last_date": self.value}


def test_get_latest_date_rejects_unsupported_table():
    repo = _LatestDateRepo(date(2026, 1, 2))

    with pytest.raises(ValueError):
        reporting.get_latest_date(repo, "unsupported_table")


def test_get_latest_date_returns_none_when_table_has_no_rows():
    repo = _LatestDateRepo(None)

    resolved = reporting.get_latest_date(repo, "click_ipua_daily")

    assert resolved is None


def test_get_latest_date_converts_date_object_to_iso():
    repo = _LatestDateRepo(date(2026, 1, 2))

    resolved = reporting.get_latest_date(repo, "conversion_ipua_daily")

    assert resolved == "2026-01-02"


def test_resolve_summary_date_chooses_latest_across_click_and_conversion(monkeypatch):
    monkeypatch.setattr(reporting, "get_latest_findings_date", lambda repo: None)
    monkeypatch.setattr(
        reporting,
        "get_latest_date",
        lambda repo, table: "2026-01-02" if table == "click_ipua_daily" else "2026-01-03",
    )

    resolved = reporting.resolve_summary_date(repo=object(), target_date=None)

    assert resolved == "2026-01-03"


def test_resolve_summary_date_prefers_latest_findings_date(monkeypatch):
    monkeypatch.setattr(reporting, "get_latest_findings_date", lambda repo: "2026-01-02")
    monkeypatch.setattr(
        reporting,
        "get_latest_date",
        lambda repo, table: "2026-01-03",
    )

    resolved = reporting.resolve_summary_date(repo=object(), target_date=None)

    assert resolved == "2026-01-02"


def test_resolve_summary_date_falls_back_to_yesterday(monkeypatch):
    monkeypatch.setattr(reporting, "get_latest_findings_date", lambda repo: None)
    monkeypatch.setattr(reporting, "get_latest_date", lambda repo, table: None)
    monkeypatch.setattr(reporting, "today_local", lambda: date(2026, 1, 4))

    resolved = reporting.resolve_summary_date(repo=object(), target_date=None)

    assert resolved == "2026-01-03"


def test_get_summary_returns_business_facing_totals(monkeypatch):
    class DummyRepo:
        database_url = "postgresql://example/db"

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

        def get_click_ipua_coverage(self, target_date):
            return {"total": 100, "missing": 4, "missing_rate": 0.04}

        def get_conversion_click_enrichment(self, target_date):
            return {"total": 10, "enriched": 8, "success_rate": 0.8}

        def get_all_masters(self):
            return {"last_synced_at": datetime(2026, 1, 3, 8, 0, 0)}

        def get_settings_updated_at(self):
            return datetime(2026, 1, 3, 7, 30, 0)

        def get_latest_settings_version_id(self):
            return "settings-ver-1"

        def get_conversion_data_watermark(self, target_date):
            return datetime(2026, 1, 3, 9, 5, 0)

        def get_conversion_findings_lineage(self, target_date):
            return {
                "findings_last_computed_at": datetime(2026, 1, 3, 9, 12, 0),
                "settings_version_id": "settings-ver-1",
                "source_click_watermark": datetime(2026, 1, 3, 9, 0, 0),
                "source_conversion_watermark": datetime(2026, 1, 3, 9, 5, 0),
            }

        def get_fraud_data_watermark(self, target_date):
            return datetime(2026, 1, 3, 9, 5, 0)

        def get_fraud_findings_lineage(self, target_date):
            return {
                "findings_last_computed_at": datetime(2026, 1, 3, 9, 12, 0),
                "settings_version_id": "settings-ver-1",
                "source_click_watermark": datetime(2026, 1, 3, 9, 0, 0),
                "source_conversion_watermark": datetime(2026, 1, 3, 9, 5, 0),
            }

        def count_current_conversion_findings(self, target_date):
            return 1

        def count_current_fraud_findings(self, target_date):
            return 0

    monkeypatch.setattr(reporting, "resolve_summary_date", lambda repo, target_date: "2026-01-03")
    monkeypatch.setattr(
        reporting.JobStatusStorePG,
        "get_latest_successful_finished_at",
        lambda self, job_types: datetime(2026, 1, 3, 9, 0, 0),
    )

    payload = reporting.get_summary(DummyRepo(), target_date=None)

    assert payload["date"] == "2026-01-03"
    assert payload["stats"]["clicks"]["total"] == 120
    assert payload["stats"]["conversions"]["total"] == 8
    assert payload["stats"]["suspicious"]["conversion_based"] == 1
    assert "click_based" not in payload["stats"]["suspicious"]
    assert payload["quality"]["last_successful_ingest_at"] == "2026-01-03T09:00:00"
    assert payload["quality"]["click_ip_ua_coverage"]["missing_rate"] == 0.04
    assert payload["quality"]["findings"]["findings_last_computed_at"] == "2026-01-03T09:12:00"
    assert payload["quality"]["findings"]["conversion_findings_last_computed_at"] == "2026-01-03T09:12:00"
    assert "click_findings_last_computed_at" not in payload["quality"]["findings"]
    assert payload["quality"]["findings"]["stale"] is False


def test_get_daily_stats_merges_click_and_conversion_rows():
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

        def get_daily_finding_counts(self, limit, *, target_date=None):
            assert limit == 30
            assert target_date is None
            return {
                "2026-01-02": {"suspicious_conversions": 2, "fraud_findings": 1},
            }

    rows = reporting.get_daily_stats(DummyRepo(), limit=30)

    assert [row["date"] for row in rows] == ["2025-12-31", "2026-01-01", "2026-01-02"]
    by_date = {row["date"]: row for row in rows}
    assert by_date["2026-01-02"]["clicks"] == 30
    assert by_date["2026-01-02"]["conversions"] == 5
    assert by_date["2026-01-02"]["suspicious_conversions"] == 2
    assert by_date["2026-01-02"]["fraud_findings"] == 1
    assert "suspicious_clicks" not in by_date["2026-01-02"]
    assert by_date["2025-12-31"]["clicks"] == 0


def test_get_daily_stats_does_not_alias_conversion_findings_into_fraud_findings():
    class DummyRepo:
        def fetch_all(self, query, params=None):
            if "FROM click_ipua_daily" in query:
                return [{"date": date(2026, 1, 2), "clicks": 30}]
            if "FROM conversion_ipua_daily" in query:
                return []
            raise AssertionError(f"Unexpected query: {query}")

        def get_daily_finding_counts(self, limit, *, target_date=None):
            return {
                "2026-01-02": {"suspicious_conversions": 2},
            }

    rows = reporting.get_daily_stats(DummyRepo(), limit=30)

    by_date = {row["date"]: row for row in rows}
    assert by_date["2026-01-02"]["suspicious_conversions"] == 2
    assert by_date["2026-01-02"]["fraud_findings"] == 0


def test_get_daily_stats_forwards_target_date_as_date():
    class DummyRepo:
        def fetch_all(self, query, params=None):
            return []

        def get_daily_finding_counts(self, limit, *, target_date=None):
            assert limit == 14
            assert target_date == date(2026, 1, 10)
            return {}

    rows = reporting.get_daily_stats(DummyRepo(), limit=14, target_date="2026-01-10")

    assert rows == []


def test_get_available_dates_returns_unique_descending():
    class DummyRepo:
        def fetch_all(self, query, params=None):
            if "click_ipua_daily" in query:
                return [{"date": date(2026, 1, 2)}, {"date": date(2026, 1, 1)}]
            if "conversion_ipua_daily" in query:
                return [{"date": date(2026, 1, 2)}, {"date": date(2025, 12, 31)}]
            raise AssertionError(f"Unexpected query: {query}")

    dates = reporting.get_available_dates(DummyRepo())

    assert dates == ["2026-01-02", "2026-01-01", "2025-12-31"]


def test_get_summary_handles_datetime_style_resolved_date(monkeypatch):
    class DummyRepo:
        database_url = "postgresql://example/db"

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

        def get_click_ipua_coverage(self, target_date):
            return None

        def get_conversion_click_enrichment(self, target_date):
            return None

        def get_all_masters(self):
            return {"last_synced_at": None}

        def get_latest_settings_version_id(self):
            return None

    monkeypatch.setattr(
        reporting,
        "resolve_summary_date",
        lambda repo, target_date: "2026-01-03T12:00:00",
    )
    monkeypatch.setattr(
        reporting.JobStatusStorePG,
        "get_latest_successful_finished_at",
        lambda self, job_types: None,
    )
    DummyRepo.count_current_conversion_findings = lambda self, target_date: 0

    payload = reporting.get_summary(DummyRepo(), target_date=None)

    assert payload["date"] == "2026-01-03T12:00:00"
    assert payload["stats"]["suspicious"]["conversion_based"] == 0


def test_get_summary_marks_findings_stale_when_conversion_source_advances(monkeypatch):
    class DummyRepo:
        database_url = "postgresql://example/db"

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

        def get_click_ipua_coverage(self, target_date):
            return None

        def get_conversion_click_enrichment(self, target_date):
            return None

        def get_all_masters(self):
            return {"last_synced_at": None}

        def get_settings_updated_at(self):
            return datetime(2026, 1, 3, 7, 30, 0)

        def get_latest_settings_version_id(self):
            return "settings-ver-3"

        def get_conversion_data_watermark(self, target_date):
            return datetime(2026, 1, 3, 9, 30, 0)

        def get_conversion_findings_lineage(self, target_date):
            return {
                "findings_last_computed_at": datetime(2026, 1, 3, 9, 12, 0),
                "settings_version_id": "settings-ver-2",
                "source_conversion_watermark": datetime(2026, 1, 3, 9, 5, 0),
            }

        def get_fraud_data_watermark(self, target_date):
            return datetime(2026, 1, 3, 9, 30, 0)

        def get_fraud_findings_lineage(self, target_date):
            return {}

        def count_current_conversion_findings(self, target_date):
            return 1

        def count_current_fraud_findings(self, target_date):
            return 0

    monkeypatch.setattr(reporting, "resolve_summary_date", lambda repo, target_date: "2026-01-03")
    monkeypatch.setattr(
        reporting.JobStatusStorePG,
        "get_latest_successful_finished_at",
        lambda self, job_types: datetime(2026, 1, 3, 9, 0, 0),
    )

    payload = reporting.get_summary(DummyRepo(), target_date=None)

    assert payload["quality"]["findings"]["stale"] is True
    assert "conversion_source_advanced" in payload["quality"]["findings"]["stale_reasons"]
    assert "settings_changed_after_conversion_findings" in payload["quality"]["findings"]["stale_reasons"]


def test_get_summary_uses_legacy_settings_timestamp_for_conversion_findings(monkeypatch):
    class DummyRepo:
        database_url = "postgresql://example/db"

        def fetch_one(self, query, params=None):
            if "total_clicks" in query:
                return {"total_clicks": 120, "unique_ips": 12, "active_media": 3}
            if "total_conversions" in query:
                return {"total_conversions": 2, "conversion_ips": 1}
            if "click_ipua_daily" in query and "prev_date" in query:
                return {"total": 100}
            if "conversion_ipua_daily" in query and "prev_date" in query:
                return {"total": 1}
            raise AssertionError(f"Unexpected query: {query}")

        def get_click_ipua_coverage(self, target_date):
            return None

        def get_conversion_click_enrichment(self, target_date):
            return None

        def get_all_masters(self):
            return {"last_synced_at": None}

        def get_settings_updated_at(self):
            return datetime(2026, 1, 3, 7, 30, 0)

        def get_latest_settings_version_id(self):
            return None

        def get_conversion_data_watermark(self, target_date):
            return datetime(2026, 1, 3, 9, 0, 0)

        def get_conversion_findings_lineage(self, target_date):
            return {
                "findings_last_computed_at": datetime(2026, 1, 3, 9, 10, 0),
                "settings_updated_at_snapshot": datetime(2026, 1, 3, 7, 0, 0),
                "source_conversion_watermark": datetime(2026, 1, 3, 9, 0, 0),
            }

        def get_fraud_data_watermark(self, target_date):
            return datetime(2026, 1, 3, 9, 0, 0)

        def get_fraud_findings_lineage(self, target_date):
            return {}

        def count_current_conversion_findings(self, target_date):
            return 0

        def count_current_fraud_findings(self, target_date):
            return 0

    monkeypatch.setattr(reporting, "resolve_summary_date", lambda repo, target_date: "2026-01-03")
    monkeypatch.setattr(
        reporting.JobStatusStorePG,
        "get_latest_successful_finished_at",
        lambda self, job_types: datetime(2026, 1, 3, 9, 0, 0),
    )

    payload = reporting.get_summary(DummyRepo(), target_date=None)

    assert payload["quality"]["findings"]["stale"] is True
    assert "settings_changed_after_conversion_findings" in payload["quality"]["findings"]["stale_reasons"]


def test_get_daily_stats_skips_invalid_date_rows():
    class DummyRepo:
        def fetch_all(self, query, params=None):
            if "FROM click_ipua_daily" in query:
                return [{"date": "bad-date", "clicks": 1}]
            if "FROM conversion_ipua_daily" in query:
                return [{"date": date(2026, 1, 2), "conversions": 3}]
            raise AssertionError(f"Unexpected query: {query}")

        def get_daily_finding_counts(self, limit, *, target_date=None):
            return {}

    rows = reporting.get_daily_stats(DummyRepo(), limit=30)

    assert len(rows) == 2
    by_date = {row["date"]: row for row in rows}
    assert by_date["bad-date"]["suspicious_conversions"] == 0
