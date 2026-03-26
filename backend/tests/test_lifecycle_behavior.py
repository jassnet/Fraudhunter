from __future__ import annotations

from datetime import date, datetime, timedelta

from fraud_checker.services import lifecycle


class _FakeRepo:
    def __init__(self) -> None:
        self.click_raw = [
            datetime(2026, 1, 1, 0, 0, 0),
            datetime(2026, 3, 20, 0, 0, 0),
        ]
        self.conversion_raw = [
            datetime(2026, 1, 2, 0, 0, 0),
            datetime(2026, 3, 20, 0, 0, 0),
        ]
        self.click_aggregates = [date(2026, 1, 1), date(2026, 3, 20)]
        self.conversion_aggregates = [date(2026, 1, 2), date(2026, 3, 20)]
        self.click_findings = [date(2026, 1, 1), date(2026, 3, 20)]
        self.conversion_findings = [date(2026, 1, 2), date(2026, 3, 20)]

    def purge_raw_before(self, cutoff: datetime, *, execute: bool) -> dict[str, int]:
        click_matches = [value for value in self.click_raw if value < cutoff]
        conversion_matches = [value for value in self.conversion_raw if value < cutoff]
        if execute:
            self.click_raw = [value for value in self.click_raw if value >= cutoff]
            self.conversion_raw = [value for value in self.conversion_raw if value >= cutoff]
        return {
            "click_raw": len(click_matches),
            "conversion_raw": len(conversion_matches),
        }

    def purge_aggregates_before(self, cutoff: date, *, execute: bool) -> dict[str, int]:
        click_matches = [value for value in self.click_aggregates if value < cutoff]
        conversion_matches = [value for value in self.conversion_aggregates if value < cutoff]
        if execute:
            self.click_aggregates = [value for value in self.click_aggregates if value >= cutoff]
            self.conversion_aggregates = [value for value in self.conversion_aggregates if value >= cutoff]
        return {
            "click_ipua_daily": len(click_matches),
            "conversion_ipua_daily": len(conversion_matches),
        }

    def purge_findings_before(self, cutoff: date, *, execute: bool) -> dict[str, int]:
        click_matches = [value for value in self.click_findings if value < cutoff]
        conversion_matches = [value for value in self.conversion_findings if value < cutoff]
        if execute:
            self.click_findings = [value for value in self.click_findings if value >= cutoff]
            self.conversion_findings = [value for value in self.conversion_findings if value >= cutoff]
        return {
            "suspicious_click_findings": len(click_matches),
            "suspicious_conversion_findings": len(conversion_matches),
        }


class _FakeJobStore:
    def __init__(self) -> None:
        self.finished_runs = [
            datetime(2026, 1, 1, 0, 0, 0),
            datetime(2026, 3, 20, 0, 0, 0),
        ]

    def purge_finished_runs_before(self, cutoff: datetime, *, execute: bool) -> int:
        matches = [value for value in self.finished_runs if value < cutoff]
        if execute:
            self.finished_runs = [value for value in self.finished_runs if value >= cutoff]
        return len(matches)


def test_resolve_retention_policy_uses_defaults_when_not_overridden() -> None:
    policy = lifecycle.resolve_retention_policy()

    assert policy.raw_days == lifecycle.DEFAULT_RAW_RETENTION_DAYS
    assert policy.aggregate_days == lifecycle.DEFAULT_AGGREGATE_RETENTION_DAYS
    assert policy.findings_days == lifecycle.DEFAULT_FINDINGS_RETENTION_DAYS
    assert policy.job_run_days == lifecycle.DEFAULT_JOB_RUN_RETENTION_DAYS


def test_purge_old_data_dry_run_reports_counts_without_deleting() -> None:
    repo = _FakeRepo()
    job_store = _FakeJobStore()
    reference_time = datetime(2026, 3, 24, 0, 0, 0)
    policy = lifecycle.RetentionPolicy(raw_days=30, aggregate_days=30, findings_days=30, job_run_days=30)

    result = lifecycle.purge_old_data(
        repo,
        job_store,
        policy=policy,
        execute=False,
        reference_time=reference_time,
    )

    assert result["execute"] is False
    assert result["counts"]["raw"] == {"click_raw": 1, "conversion_raw": 1}
    assert result["counts"]["aggregates"] == {"click_ipua_daily": 1, "conversion_ipua_daily": 1}
    assert result["counts"]["findings"] == {
        "suspicious_click_findings": 1,
        "suspicious_conversion_findings": 1,
    }
    assert result["counts"]["job_runs"] == {"job_runs": 1}
    assert len(repo.click_raw) == 2
    assert len(job_store.finished_runs) == 2


def test_purge_old_data_execute_deletes_only_older_rows() -> None:
    repo = _FakeRepo()
    job_store = _FakeJobStore()
    reference_time = datetime(2026, 3, 24, 0, 0, 0)
    policy = lifecycle.RetentionPolicy(raw_days=30, aggregate_days=30, findings_days=30, job_run_days=30)

    result = lifecycle.purge_old_data(
        repo,
        job_store,
        policy=policy,
        execute=True,
        reference_time=reference_time,
    )

    assert result["execute"] is True
    assert repo.click_raw == [datetime(2026, 3, 20, 0, 0, 0)]
    assert repo.conversion_raw == [datetime(2026, 3, 20, 0, 0, 0)]
    assert repo.click_aggregates == [date(2026, 3, 20)]
    assert repo.conversion_aggregates == [date(2026, 3, 20)]
    assert repo.click_findings == [date(2026, 3, 20)]
    assert repo.conversion_findings == [date(2026, 3, 20)]
    assert job_store.finished_runs == [datetime(2026, 3, 20, 0, 0, 0)]


def test_describe_evidence_availability_marks_old_findings_as_expired() -> None:
    result = lifecycle.describe_evidence_availability(
        date(2025, 12, 1),
        reference_time=datetime(2026, 3, 24, 0, 0, 0),
        retention_days=90,
    )

    assert result["evidence_status"] == "expired"
    assert result["evidence_available"] is False
    assert result["evidence_expired"] is True
    assert result["evidence_expires_on"] == "2026-03-01"


def test_describe_evidence_availability_keeps_recent_findings_available() -> None:
    result = lifecycle.describe_evidence_availability(
        date(2026, 3, 1),
        reference_time=datetime(2026, 3, 24, 0, 0, 0),
        retention_days=90,
    )

    assert result["evidence_status"] == "available"
    assert result["evidence_available"] is True
    assert result["evidence_expired"] is False
