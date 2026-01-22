from __future__ import annotations

import argparse
import sqlite3
from datetime import date, datetime
from typing import Any, Iterable

import sqlalchemy as sa

from .models import Base


DATE_COLUMNS = {
    "click_ipua_daily": {"date"},
    "conversion_ipua_daily": {"date"},
}

DATETIME_COLUMNS = {
    "click_ipua_daily": {"first_time", "last_time", "created_at", "updated_at"},
    "click_raw": {"click_time", "created_at", "updated_at"},
    "conversion_raw": {
        "conversion_time",
        "click_time",
        "created_at",
        "updated_at",
    },
    "conversion_ipua_daily": {"first_time", "last_time", "created_at", "updated_at"},
    "master_media": {"updated_at"},
    "master_promotion": {"updated_at"},
    "master_user": {"updated_at"},
    "app_settings": {"updated_at"},
    "job_status": {"started_at", "completed_at"},
}

TABLE_ORDER = [
    "click_ipua_daily",
    "click_raw",
    "conversion_ipua_daily",
    "conversion_raw",
    "master_media",
    "master_promotion",
    "master_user",
    "app_settings",
    "job_status",
]


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def sqlite_table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row[1] for row in rows}


def row_to_dict(table: str, row: sqlite3.Row, available_columns: set[str]) -> dict[str, Any]:
    payload = {}
    for key in row.keys():
        if key not in available_columns:
            continue
        value = row[key]
        if key in DATE_COLUMNS.get(table, set()):
            value = parse_date(value)
        elif key in DATETIME_COLUMNS.get(table, set()):
            value = parse_datetime(value)
        payload[key] = value
    return payload


def iter_sqlite_rows(conn: sqlite3.Connection, table: str, batch_size: int) -> Iterable[list[sqlite3.Row]]:
    cursor = conn.execute(f"SELECT * FROM {table}")
    while True:
        batch = cursor.fetchmany(batch_size)
        if not batch:
            return
        yield batch


def migrate_table(
    sqlite_conn: sqlite3.Connection,
    pg_conn: sa.Connection,
    table: str,
    batch_size: int,
) -> int:
    available_columns = sqlite_table_columns(sqlite_conn, table)
    target_table = Base.metadata.tables[table]

    migrated = 0
    for batch in iter_sqlite_rows(sqlite_conn, table, batch_size):
        rows = [row_to_dict(table, row, available_columns) for row in batch]
        if not rows:
            continue
        pg_conn.execute(target_table.insert(), rows)
        migrated += len(rows)
    return migrated


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
        (name,),
    ).fetchone()
    return row is not None


def truncate_tables(pg_conn: sa.Connection, tables: list[str]) -> None:
    for table in tables:
        pg_conn.execute(sa.text(f"DELETE FROM {table}"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate SQLite data into PostgreSQL")
    parser.add_argument("--sqlite", required=True, help="SQLite DB path")
    parser.add_argument("--database-url", required=True, help="PostgreSQL URL")
    parser.add_argument("--batch-size", type=int, default=2000)
    parser.add_argument("--skip-raw", action="store_true", help="Skip raw tables")
    parser.add_argument("--truncate", action="store_true", help="Delete existing rows before insert.")

    args = parser.parse_args()

    sqlite_conn = sqlite3.connect(args.sqlite)
    sqlite_conn.row_factory = sqlite3.Row

    engine = sa.create_engine(args.database_url)
    Base.metadata.create_all(engine)

    tables = list(TABLE_ORDER)
    if args.skip_raw:
        tables = [t for t in tables if t not in {"click_raw", "conversion_raw"}]

    with engine.begin() as pg_conn:
        if args.truncate:
            truncate_tables(pg_conn, list(reversed(tables)))

        for table in tables:
            if not table_exists(sqlite_conn, table):
                print(f"[skip] {table} (not found)")
                continue
            migrated = migrate_table(sqlite_conn, pg_conn, table, args.batch_size)
            print(f"[ok] {table}: {migrated} rows")

    sqlite_conn.close()


if __name__ == "__main__":
    main()
