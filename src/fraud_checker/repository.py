from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, List

from .models import AggregatedRow, ClickLog, IpUaRollup


class SQLiteRepository:
    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.raw_schema_created = False

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        try:
            self._configure_connection(conn)
            yield conn
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _configure_connection(conn: sqlite3.Connection) -> None:
        # Lightweight performance tuning for batch inserts.
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")

    def ensure_schema(self, store_raw: bool = False) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS click_ipua_daily (
                    date TEXT NOT NULL,
                    media_id TEXT NOT NULL,
                    program_id TEXT NOT NULL,
                    ipaddress TEXT NOT NULL,
                    useragent TEXT NOT NULL,
                    click_count INTEGER NOT NULL,
                    first_time TEXT NOT NULL,
                    last_time TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (date, media_id, program_id, ipaddress, useragent)
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_click_ipua_daily_date ON click_ipua_daily(date);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_click_ipua_daily_date_ip ON click_ipua_daily(date, ipaddress);"
            )

            if store_raw:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS click_raw (
                        id TEXT PRIMARY KEY,
                        click_time TEXT NOT NULL,
                        media_id TEXT,
                        program_id TEXT,
                        ipaddress TEXT,
                        useragent TEXT,
                        referrer TEXT,
                        raw_payload TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                    """
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_click_raw_time ON click_raw(click_time);"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_click_raw_media ON click_raw(media_id, click_time);"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_click_raw_program ON click_raw(program_id, click_time);"
                )
                self.raw_schema_created = True

    def ingest_clicks(
        self, clicks: Iterable[ClickLog], *, target_date: date, store_raw: bool
    ) -> int:
        self.ensure_schema(store_raw=store_raw)
        count = 0
        with self._connect() as conn:
            self._clear_date(conn, target_date, store_raw)
            for click in clicks:
                if click.click_time.date() != target_date:
                    continue
                if store_raw:
                    self._insert_raw(conn, click)
                self._upsert_aggregate(conn, click)
                count += 1
        return count

    def fetch_aggregates(self, target_date: date) -> List[AggregatedRow]:
        with self._connect() as conn:
            cur = conn.execute(
                """
                SELECT date, media_id, program_id, ipaddress, useragent,
                       click_count, first_time, last_time, created_at, updated_at
                FROM click_ipua_daily
                WHERE date = ?
                """,
                (target_date.isoformat(),),
            )
            rows = cur.fetchall()
        return [self._to_aggregated_row(r) for r in rows]

    def count_raw_rows(self, target_date: date) -> int:
        if not self.raw_schema_created and not self._table_exists("click_raw"):
            return 0
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT COUNT(*) FROM click_raw WHERE substr(click_time, 1, 10) = ?",
                (target_date.isoformat(),),
            )
            (count,) = cur.fetchone()
            return count

    def fetch_rollups(self, target_date: date) -> List[IpUaRollup]:
        with self._connect() as conn:
            cur = conn.execute(
                """
                SELECT
                    date,
                    ipaddress,
                    useragent,
                    SUM(click_count) AS total_clicks,
                    COUNT(DISTINCT media_id) AS media_count,
                    COUNT(DISTINCT program_id) AS program_count,
                    MIN(first_time) AS first_time,
                    MAX(last_time) AS last_time
                FROM click_ipua_daily
                WHERE date = ?
                GROUP BY date, ipaddress, useragent
                """,
                (target_date.isoformat(),),
            )
            rows = cur.fetchall()
        return [self._to_rollup(r) for r in rows]

    def fetch_suspicious_rollups(
        self,
        target_date: date,
        *,
        click_threshold: int,
        media_threshold: int,
        program_threshold: int,
        burst_click_threshold: int,
        browser_only: bool = False,
        exclude_datacenter_ip: bool = False,
    ) -> List[IpUaRollup]:
        """
        SQL-level suspicious extraction to keep filtering close to the data.

        Thresholds mirror the SuspiciousRuleSet defaults; burst detection is evaluated
        in Python because it needs first/last timestamps.

        If browser_only is True, only records with browser-like UserAgents are included.
        If exclude_datacenter_ip is True, known datacenter IP ranges are excluded.
        """
        # ブラウザ由来UAのみを対象とするフィルタ条件
        browser_filter = ""
        if browser_only:
            browser_filter = """
                AND (
                    useragent LIKE '%Chrome/%'
                    OR useragent LIKE '%Firefox/%'
                    OR useragent LIKE '%Safari/%'
                    OR useragent LIKE '%Edg/%'
                    OR useragent LIKE '%Edge/%'
                    OR useragent LIKE '%Opera/%'
                    OR useragent LIKE '%OPR/%'
                    OR useragent LIKE '%MSIE %'
                    OR useragent LIKE '%Trident/%'
                )
                AND useragent NOT LIKE '%bot%'
                AND useragent NOT LIKE '%Bot%'
                AND useragent NOT LIKE '%crawler%'
                AND useragent NOT LIKE '%Crawler%'
                AND useragent NOT LIKE '%spider%'
                AND useragent NOT LIKE '%Spider%'
                AND useragent NOT LIKE '%curl%'
                AND useragent NOT LIKE '%python%'
                AND useragent NOT LIKE '%Python%'
                AND useragent NOT LIKE '%axios%'
                AND useragent NOT LIKE '%node-fetch%'
                AND useragent NOT LIKE '%Go-http-client%'
                AND useragent NOT LIKE '%Java/%'
                AND useragent NOT LIKE '%Apache-HttpClient%'
                AND useragent NOT LIKE '%libwww-perl%'
                AND useragent NOT LIKE '%Wget%'
                AND useragent NOT LIKE '%HeadlessChrome%'
            """

        # データセンターIP除外フィルタ（Google, AWS, Azure, GCP等）
        datacenter_filter = ""
        if exclude_datacenter_ip:
            datacenter_filter = """
                AND ipaddress NOT LIKE '74.125.%'
                AND ipaddress NOT LIKE '172.253.%'
                AND ipaddress NOT LIKE '142.250.%'
                AND ipaddress NOT LIKE '142.251.%'
                AND ipaddress NOT LIKE '173.194.%'
                AND ipaddress NOT LIKE '209.85.%'
                AND ipaddress NOT LIKE '216.58.%'
                AND ipaddress NOT LIKE '216.239.%'
                AND ipaddress NOT LIKE '35.%'
                AND ipaddress NOT LIKE '34.%'
                AND ipaddress NOT LIKE '104.%'
                AND ipaddress NOT LIKE '13.%'
                AND ipaddress NOT LIKE '52.%'
                AND ipaddress NOT LIKE '54.%'
                AND ipaddress NOT LIKE '18.%'
                AND ipaddress NOT LIKE '3.%'
                AND ipaddress NOT LIKE '20.%'
                AND ipaddress NOT LIKE '40.%'
                AND ipaddress NOT LIKE '51.%'
                AND ipaddress NOT LIKE '52.%'
                AND ipaddress NOT LIKE '157.%'
                AND ipaddress NOT LIKE '168.63.%'
                AND ipaddress NOT LIKE '23.%'
                AND ipaddress NOT LIKE '45.%'
                AND ipaddress NOT LIKE '64.%'
                AND ipaddress NOT LIKE '66.%'
                AND ipaddress NOT LIKE '108.%'
            """

        query = f"""
            SELECT
                date,
                ipaddress,
                useragent,
                SUM(click_count) AS total_clicks,
                COUNT(DISTINCT media_id) AS media_count,
                COUNT(DISTINCT program_id) AS program_count,
                MIN(first_time) AS first_time,
                MAX(last_time) AS last_time
            FROM click_ipua_daily
            WHERE date = ?
            {browser_filter}
            {datacenter_filter}
            GROUP BY date, ipaddress, useragent
            HAVING
                SUM(click_count) >= ?
                OR COUNT(DISTINCT media_id) >= ?
                OR COUNT(DISTINCT program_id) >= ?
                OR SUM(click_count) >= ?
        """

        with self._connect() as conn:
            cur = conn.execute(
                query,
                (
                    target_date.isoformat(),
                    click_threshold,
                    media_threshold,
                    program_threshold,
                    burst_click_threshold,
                ),
            )
            rows = cur.fetchall()
        return [self._to_rollup(r) for r in rows]

    def clear_date(self, target_date: date, *, store_raw: bool) -> None:
        with self._connect() as conn:
            self._clear_date(conn, target_date, store_raw)

    def _clear_date(self, conn: sqlite3.Connection, target_date: date, store_raw: bool) -> None:
        conn.execute("DELETE FROM click_ipua_daily WHERE date = ?", (target_date.isoformat(),))
        if self.raw_schema_created or self._table_exists("click_raw", conn):
            conn.execute(
                "DELETE FROM click_raw WHERE substr(click_time, 1, 10) = ?",
                (target_date.isoformat(),),
            )

    def _insert_raw(self, conn: sqlite3.Connection, click: ClickLog) -> None:
        now = datetime.utcnow().isoformat()
        conn.execute(
            """
            INSERT OR REPLACE INTO click_raw (
                id, click_time, media_id, program_id, ipaddress, useragent,
                referrer, raw_payload, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                click.click_id or uuid.uuid4().hex,
                self._iso(click.click_time),
                click.media_id,
                click.program_id,
                click.ipaddress,
                click.useragent,
                click.referrer,
                json.dumps(click.raw_payload) if click.raw_payload is not None else None,
                now,
                now,
            ),
        )

    def _upsert_aggregate(self, conn: sqlite3.Connection, click: ClickLog) -> None:
        now = datetime.utcnow().isoformat()
        conn.execute(
            """
            INSERT INTO click_ipua_daily (
                date, media_id, program_id, ipaddress, useragent,
                click_count, first_time, last_time, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(date, media_id, program_id, ipaddress, useragent) DO UPDATE SET
                click_count = click_ipua_daily.click_count + 1,
                first_time = MIN(click_ipua_daily.first_time, excluded.first_time),
                last_time = MAX(click_ipua_daily.last_time, excluded.last_time),
                updated_at = excluded.updated_at
            """,
            (
                # Date bucket is derived from the click timestamp; ACS times are assumed UTC.
                click.click_time.date().isoformat(),
                click.media_id,
                click.program_id,
                click.ipaddress,
                click.useragent,
                1,
                self._iso(click.click_time),
                self._iso(click.click_time),
                now,
                now,
            ),
        )

    def _to_aggregated_row(self, row: tuple) -> AggregatedRow:
        return AggregatedRow(
            date=date.fromisoformat(row[0]),
            media_id=row[1],
            program_id=row[2],
            ipaddress=row[3],
            useragent=row[4],
            click_count=row[5],
            first_time=self._from_iso(row[6]),
            last_time=self._from_iso(row[7]),
            created_at=self._from_iso(row[8]),
            updated_at=self._from_iso(row[9]),
        )

    def _to_rollup(self, row: tuple) -> IpUaRollup:
        return IpUaRollup(
            date=date.fromisoformat(row[0]),
            ipaddress=row[1],
            useragent=row[2],
            total_clicks=row[3],
            media_count=row[4],
            program_count=row[5],
            first_time=self._from_iso(row[6]),
            last_time=self._from_iso(row[7]),
        )

    def _table_exists(self, name: str, conn: sqlite3.Connection | None = None) -> bool:
        if conn is None:
            with self._connect() as conn_local:
                return self._table_exists(name, conn_local)
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (name,)
        )
        return cur.fetchone() is not None

    @staticmethod
    def _iso(dt: datetime) -> str:
        return dt.isoformat()

    @staticmethod
    def _from_iso(text: str) -> datetime:
        return datetime.fromisoformat(text)
