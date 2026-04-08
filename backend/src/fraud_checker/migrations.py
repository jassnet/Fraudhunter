from __future__ import annotations

import os
from pathlib import Path
import time
from typing import Mapping

from alembic import command
from alembic.config import Config
import sqlalchemy as sa

from .db.session import normalize_database_url

ALEMBIC_HEAD_REVISION = "0013_add_damage_snapshot"
DEFAULT_DB_CONNECT_MAX_ATTEMPTS = 20
DEFAULT_DB_CONNECT_RETRY_SECONDS = 3.0


def infer_legacy_schema_revision(
    table_names: set[str],
    table_columns: Mapping[str, set[str]],
) -> str | None:
    if "suspicious_conversion_findings" in table_names and "suspicious_click_findings" not in table_names:
        if {
            "fraud_findings",
            "check_raw",
            "track_raw",
            "click_sum_daily",
            "access_sum_daily",
            "imp_sum_daily",
        }.issubset(table_names):
            return "0011_add_acs_native_fraud"
        if {"settings_versions", "findings_generations"}.issubset(table_names):
            return "0010_drop_click_findings"
    if {
        "suspicious_click_findings",
        "suspicious_conversion_findings",
    }.issubset(table_names):
        if {"settings_versions", "findings_generations"}.issubset(table_names):
            if "concurrency_key" in table_columns.get("job_runs", set()):
                return "0008_job_run_concurrency"
            return "0007_settings_findings_gen"
        if "attempt_count" in table_columns.get("job_runs", set()):
            return "0006_add_job_run_controls"
        if "computed_by_job_id" in table_columns.get("suspicious_click_findings", set()):
            return "0005_add_findings_lineage"
        return "0004_add_persisted_findings"
    if "job_runs" in table_names:
        return "0003_add_job_runs"
    if {"click_ipua_daily", "conversion_ipua_daily"}.issubset(table_names):
        return "0002_add_ipua_date_ip_ua_index"
    return None


def prepare_database_for_current_head(
    database_url: str | None = None,
    *,
    max_attempts: int | None = None,
    retry_delay_seconds: float | None = None,
) -> None:
    url = normalize_database_url(database_url or os.getenv("DATABASE_URL", ""))
    if not url:
        raise RuntimeError("DATABASE_URL is required to prepare the database")

    max_attempts = _get_retry_attempts() if max_attempts is None else max_attempts
    retry_delay_seconds = _get_retry_delay_seconds() if retry_delay_seconds is None else retry_delay_seconds
    if max_attempts < 1:
        raise RuntimeError("max_attempts must be at least 1")
    if retry_delay_seconds < 0:
        raise RuntimeError("retry_delay_seconds must be non-negative")
    last_error: sa.exc.OperationalError | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            _prepare_database_for_current_head_once(url)
            return
        except sa.exc.OperationalError as exc:
            last_error = exc
            if attempt >= max_attempts:
                break
            print(
                "[migrations] database unavailable during prepare "
                f"(attempt {attempt}/{max_attempts}); retrying in {retry_delay_seconds:.1f}s"
            )
            time.sleep(retry_delay_seconds)

    if last_error is not None:
        raise last_error


def _prepare_database_for_current_head_once(url: str) -> None:
    engine = sa.create_engine(url, pool_pre_ping=True)
    inspector = sa.inspect(engine)
    table_names = set(inspector.get_table_names())
    has_version_table = "alembic_version" in table_names

    if has_version_table:
        current_revision = _read_current_revision(engine)
    else:
        table_columns = {
            table_name: {column["name"] for column in inspector.get_columns(table_name)}
            for table_name in table_names
        }
        current_revision = infer_legacy_schema_revision(table_names, table_columns)

    alembic_cfg = _build_alembic_config(url)
    if not has_version_table and current_revision:
        command.stamp(alembic_cfg, current_revision)

    if current_revision != ALEMBIC_HEAD_REVISION:
        command.upgrade(alembic_cfg, "head")


def _get_retry_attempts() -> int:
    value = os.getenv("FC_DB_CONNECT_MAX_ATTEMPTS")
    if value is None:
        return DEFAULT_DB_CONNECT_MAX_ATTEMPTS
    attempts = int(value)
    if attempts < 1:
        raise RuntimeError("FC_DB_CONNECT_MAX_ATTEMPTS must be at least 1")
    return attempts


def _get_retry_delay_seconds() -> float:
    value = os.getenv("FC_DB_CONNECT_RETRY_SECONDS")
    if value is None:
        return DEFAULT_DB_CONNECT_RETRY_SECONDS
    seconds = float(value)
    if seconds < 0:
        raise RuntimeError("FC_DB_CONNECT_RETRY_SECONDS must be non-negative")
    return seconds


def _read_current_revision(engine: sa.Engine) -> str | None:
    with engine.begin() as conn:
        return conn.execute(sa.text("SELECT version_num FROM alembic_version")).scalar_one_or_none()


def _build_alembic_config(database_url: str) -> Config:
    backend_dir = Path(__file__).resolve().parents[2]
    alembic_ini = backend_dir / "alembic.ini"
    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str(backend_dir / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


if __name__ == "__main__":
    prepare_database_for_current_head()
