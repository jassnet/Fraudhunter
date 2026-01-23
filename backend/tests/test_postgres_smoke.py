import os

import pytest

from fraud_checker.repository_pg import PostgresRepository


def test_postgres_smoke():
    database_url = os.getenv("FRAUD_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set FRAUD_TEST_DATABASE_URL to run Postgres smoke test.")

    repo = PostgresRepository(database_url)
    repo.ensure_schema(store_raw=False)
    repo.ensure_conversion_schema()
    repo.ensure_master_schema()

    rows = repo.fetch_all("SELECT 1 as ok")
    assert rows and rows[0]["ok"] == 1
