from __future__ import annotations

from pathlib import Path

from fraud_checker.migrations import infer_legacy_schema_revision


def test_infer_legacy_schema_revision_for_post_drop_click_schema() -> None:
    revision = infer_legacy_schema_revision(
        {
            "click_ipua_daily",
            "conversion_ipua_daily",
            "job_runs",
            "settings_versions",
            "findings_generations",
            "suspicious_conversion_findings",
        },
        {
            "job_runs": {"id", "attempt_count", "next_retry_at", "concurrency_key"},
            "findings_generations": {"generation_id", "settings_version_id"},
            "settings_versions": {"id", "fingerprint"},
        },
    )

    assert revision == "0010_drop_click_findings"


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


def test_infer_legacy_schema_revision_for_provenance_ready_schema() -> None:
    revision = infer_legacy_schema_revision(
        {
            "click_ipua_daily",
            "conversion_ipua_daily",
            "job_runs",
            "settings_versions",
            "findings_generations",
            "suspicious_click_findings",
            "suspicious_conversion_findings",
        },
        {
            "job_runs": {"id", "attempt_count", "next_retry_at"},
            "findings_generations": {"generation_id", "settings_version_id"},
            "settings_versions": {"id", "fingerprint"},
        },
    )

    assert revision == "0007_settings_findings_gen"


def test_infer_legacy_schema_revision_for_queue_concurrency_ready_schema() -> None:
    revision = infer_legacy_schema_revision(
        {
            "click_ipua_daily",
            "conversion_ipua_daily",
            "job_runs",
            "settings_versions",
            "findings_generations",
            "suspicious_click_findings",
            "suspicious_conversion_findings",
        },
        {
            "job_runs": {"id", "attempt_count", "next_retry_at", "concurrency_key"},
            "findings_generations": {"generation_id", "settings_version_id"},
            "settings_versions": {"id", "fingerprint"},
        },
    )

    assert revision == "0008_job_run_concurrency"


def test_head_revision_advances_beyond_findings_search_indexes() -> None:
    from fraud_checker.migrations import ALEMBIC_HEAD_REVISION

    assert ALEMBIC_HEAD_REVISION == "0011_add_acs_native_fraud"


def test_head_revision_fits_alembic_version_column_limit() -> None:
    from fraud_checker.migrations import ALEMBIC_HEAD_REVISION

    assert len(ALEMBIC_HEAD_REVISION) <= 32


def test_findings_search_index_migration_enables_pg_trgm_for_current_findings() -> None:
    migration = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "0009_add_findings_search_indexes.py"
    ).read_text(encoding="utf-8")

    assert "CREATE EXTENSION IF NOT EXISTS pg_trgm" in migration
    assert "idx_scf_search_text_trgm" in migration
    assert "idx_scof_search_text_trgm" in migration
    assert "WHERE is_current = TRUE" in migration


def test_drop_click_findings_migration_removes_table_and_generation_rows() -> None:
    migration = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "0010_drop_click_findings.py"
    ).read_text(encoding="utf-8")

    assert "DELETE FROM findings_generations WHERE finding_type = 'click'" in migration
    assert "op.drop_table(\"suspicious_click_findings\")" in migration
    assert "DROP INDEX IF EXISTS idx_scf_search_text_trgm" in migration


def test_acs_native_fraud_migration_adds_master_promotion_guard_columns() -> None:
    migration = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "0011_add_acs_native_fraud.py"
    ).read_text(encoding="utf-8")

    assert "action_double_state" in migration
    assert "action_double_type_json" in migration
