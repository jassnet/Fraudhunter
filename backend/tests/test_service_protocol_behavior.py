from __future__ import annotations

from datetime import date, datetime

from fraud_checker.services import lifecycle, reporting


class StubReportingRepo:
    database_url = "postgresql://example/db"

    def fetch_one(self, query, params=None):
        if "MAX(date)" in query:
            return {"last_date": date(2026, 1, 21)}
        if "total_clicks" in query:
            return {"total_clicks": 12, "unique_ips": 3, "active_media": 2}
        if "total_conversions" in query:
            return {"total_conversions": 4, "conversion_ips": 2}
        if "click_ipua_daily" in query and "prev_date" in query:
            return {"total": 10}
        if "conversion_ipua_daily" in query and "prev_date" in query:
            return {"total": 3}
        raise AssertionError(f"Unexpected query: {query}")

    def fetch_all(self, query, params=None):
        if "click_ipua_daily" in query:
            return [{"date": date(2026, 1, 21)}]
        if "conversion_ipua_daily" in query:
            return [{"date": date(2026, 1, 20)}]
        raise AssertionError(f"Unexpected query: {query}")

    def get_click_ipua_coverage(self, target_date: date):
        return None

    def get_conversion_click_enrichment(self, target_date: date):
        return None

    def get_all_masters(self):
        return {"last_synced_at": None}

    def get_settings_updated_at(self):
        return None

    def get_latest_settings_version_id(self):
        return None

    def get_conversion_data_watermark(self, target_date: date):
        return None

    def get_conversion_findings_lineage(self, target_date: date):
        return None

    def count_current_conversion_findings(self, target_date: date) -> int:
        return 0

    def get_daily_finding_counts(self, limit: int, *, target_date: date | None = None) -> dict[str, dict[str, int]]:
        return {}


class StubLifecycleRepo:
    def purge_raw_before(self, cutoff: datetime, *, execute: bool) -> dict[str, int]:
        return {"click_raw": 5}

    def purge_aggregates_before(self, cutoff: date, *, execute: bool) -> dict[str, int]:
        return {"click_ipua_daily": 3}

    def purge_findings_before(self, cutoff: date, *, execute: bool) -> dict[str, int]:
        return {"suspicious_conversion_findings": 2}


class StubJobStore:
    def purge_finished_runs_before(self, cutoff: datetime, *, execute: bool) -> int:
        return 7


def test_reporting_service_accepts_narrow_repository_interface(monkeypatch):
    monkeypatch.setattr(
        reporting.JobStatusStorePG,
        "get_latest_successful_finished_at",
        lambda self, job_types: None,
    )

    dates = reporting.get_available_dates(StubReportingRepo())
    summary = reporting.get_summary(StubReportingRepo(), target_date=None)

    assert dates == ["2026-01-21", "2026-01-20"]
    assert summary["date"] == "2026-01-21"
    assert summary["stats"]["clicks"]["total"] == 12


def test_lifecycle_service_accepts_narrow_repository_interface():
    result = lifecycle.purge_old_data(
        StubLifecycleRepo(),
        StubJobStore(),
        policy=lifecycle.RetentionPolicy(raw_days=30, aggregate_days=60, findings_days=90, job_run_days=15),
        execute=False,
        reference_time=datetime(2026, 1, 21, 9, 0, 0),
    )

    assert result["counts"]["raw"]["click_raw"] == 5
    assert result["counts"]["aggregates"]["click_ipua_daily"] == 3
    assert result["counts"]["findings"]["suspicious_conversion_findings"] == 2
    assert result["counts"]["job_runs"]["job_runs"] == 7
