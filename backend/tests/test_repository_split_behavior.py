from __future__ import annotations

from fraud_checker.repositories import (
    IngestionRepository,
    MasterRepository,
    ReportingReadRepository,
    SettingsRepository,
    SuspiciousReadRepository,
)
from fraud_checker.repository_pg import PostgresRepository


def test_postgres_repository_is_backward_compatible_facade():
    assert issubclass(PostgresRepository, IngestionRepository)
    assert issubclass(PostgresRepository, ReportingReadRepository)
    assert issubclass(PostgresRepository, SuspiciousReadRepository)
    assert issubclass(PostgresRepository, MasterRepository)
    assert issubclass(PostgresRepository, SettingsRepository)


def test_postgres_repository_keeps_split_methods_available():
    repo = object.__new__(PostgresRepository)

    assert callable(repo.merge_clicks)
    assert callable(repo.fetch_rollups)
    assert callable(repo.list_click_findings)
    assert callable(repo.bulk_upsert_media)
    assert callable(repo.load_settings)
