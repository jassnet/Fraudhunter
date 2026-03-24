from __future__ import annotations

from fraud_checker.migrations import infer_legacy_schema_revision


def test_infer_legacy_schema_revision_for_persisted_findings_without_lineage() -> None:
    revision = infer_legacy_schema_revision(
        {
            "click_ipua_daily",
            "conversion_ipua_daily",
            "job_runs",
            "suspicious_click_findings",
            "suspicious_conversion_findings",
        },
        {
            "suspicious_click_findings": {"finding_key", "computed_at"},
            "suspicious_conversion_findings": {"finding_key", "computed_at"},
        },
    )

    assert revision == "0004_add_persisted_findings"


def test_infer_legacy_schema_revision_for_lineage_ready_schema() -> None:
    revision = infer_legacy_schema_revision(
        {
            "click_ipua_daily",
            "conversion_ipua_daily",
            "job_runs",
            "suspicious_click_findings",
            "suspicious_conversion_findings",
        },
        {
            "suspicious_click_findings": {"finding_key", "computed_by_job_id"},
            "suspicious_conversion_findings": {"finding_key", "computed_by_job_id"},
        },
    )

    assert revision == "0005_add_findings_lineage"


def test_infer_legacy_schema_revision_for_job_control_ready_schema() -> None:
    revision = infer_legacy_schema_revision(
        {
            "click_ipua_daily",
            "conversion_ipua_daily",
            "job_runs",
            "suspicious_click_findings",
            "suspicious_conversion_findings",
        },
        {
            "job_runs": {"id", "attempt_count", "next_retry_at"},
            "suspicious_click_findings": {"finding_key", "computed_by_job_id"},
            "suspicious_conversion_findings": {"finding_key", "computed_by_job_id"},
        },
    )

    assert revision == "0006_add_job_run_controls"
