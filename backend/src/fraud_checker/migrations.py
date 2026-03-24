from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

from alembic import command
from alembic.config import Config
import sqlalchemy as sa

from .db.session import normalize_database_url

ALEMBIC_HEAD_REVISION = "0005_add_findings_lineage"


def infer_legacy_schema_revision(
    table_names: set[str],
    table_columns: Mapping[str, set[str]],
) -> str | None:
    if {
        "suspicious_click_findings",
        "suspicious_conversion_findings",
    }.issubset(table_names):
        if "computed_by_job_id" in table_columns.get("suspicious_click_findings", set()):
            return ALEMBIC_HEAD_REVISION
        return "0004_add_persisted_findings"
    if "job_runs" in table_names:
        return "0003_add_job_runs"
    if {"click_ipua_daily", "conversion_ipua_daily"}.issubset(table_names):
        return "0002_add_ipua_date_ip_ua_index"
    return None


def prepare_database_for_current_head(database_url: str | None = None) -> None:
    url = normalize_database_url(database_url or os.getenv("DATABASE_URL", ""))
    if not url:
        raise RuntimeError("DATABASE_URL is required to prepare the database")

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
