from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, List

from .models import (
    AggregatedRow,
    ClickLog,
    ConversionIpUaRollup,
    ConversionLog,
    ConversionWithClickInfo,
    IpUaRollup,
)


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

    def ensure_conversion_schema(self) -> None:
        """成果ログ用のスキーマを作成"""
        with self._connect() as conn:
            # 成果ログ生データ
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversion_raw (
                    id TEXT PRIMARY KEY,
                    cid TEXT,
                    conversion_time TEXT NOT NULL,
                    click_time TEXT,
                    media_id TEXT,
                    program_id TEXT,
                    user_id TEXT,
                    postback_ipaddress TEXT,
                    postback_useragent TEXT,
                    entry_ipaddress TEXT,
                    entry_useragent TEXT,
                    state TEXT,
                    raw_payload TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_conversion_raw_time ON conversion_raw(conversion_time);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_conversion_raw_cid ON conversion_raw(cid);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_conversion_raw_media ON conversion_raw(media_id, conversion_time);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_conversion_raw_program ON conversion_raw(program_id, conversion_time);"
            )

            # 成果のIP/UA日次集計（エントリー時のIP/UAベース = 実ユーザー）
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversion_ipua_daily (
                    date TEXT NOT NULL,
                    media_id TEXT NOT NULL,
                    program_id TEXT NOT NULL,
                    ipaddress TEXT NOT NULL,
                    useragent TEXT NOT NULL,
                    conversion_count INTEGER NOT NULL,
                    first_time TEXT NOT NULL,
                    last_time TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (date, media_id, program_id, ipaddress, useragent)
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_conversion_ipua_daily_date ON conversion_ipua_daily(date);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_conversion_ipua_daily_date_ip ON conversion_ipua_daily(date, ipaddress);"
            )

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

    # ==================== 成果ログ関連メソッド ====================

    def ingest_conversions(
        self, conversions: Iterable[ConversionLog], *, target_date: date
    ) -> int:
        """成果ログを取り込む"""
        self.ensure_conversion_schema()
        count = 0
        with self._connect() as conn:
            self._clear_conversions_date(conn, target_date)
            for conv in conversions:
                if conv.conversion_time.date() != target_date:
                    continue
                self._insert_conversion_raw(conn, conv)
                # エントリー時（実ユーザー）のIP/UAが設定されている場合のみ集計に追加
                if conv.entry_ipaddress and conv.entry_useragent:
                    self._upsert_conversion_aggregate(conn, conv)
                count += 1
        return count

    def _clear_conversions_date(self, conn: sqlite3.Connection, target_date: date) -> None:
        if self._table_exists("conversion_raw", conn):
            conn.execute(
                "DELETE FROM conversion_raw WHERE substr(conversion_time, 1, 10) = ?",
                (target_date.isoformat(),),
            )
        if self._table_exists("conversion_ipua_daily", conn):
            conn.execute(
                "DELETE FROM conversion_ipua_daily WHERE date = ?",
                (target_date.isoformat(),),
            )

    def _insert_conversion_raw(self, conn: sqlite3.Connection, conv: ConversionLog) -> None:
        now = datetime.utcnow().isoformat()
        conn.execute(
            """
            INSERT OR REPLACE INTO conversion_raw (
                id, cid, conversion_time, click_time, media_id, program_id, user_id,
                postback_ipaddress, postback_useragent, entry_ipaddress, entry_useragent,
                state, raw_payload, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conv.conversion_id,
                conv.cid,
                self._iso(conv.conversion_time),
                self._iso(conv.click_time) if conv.click_time else None,
                conv.media_id,
                conv.program_id,
                conv.user_id,
                conv.postback_ipaddress,
                conv.postback_useragent,
                conv.entry_ipaddress,
                conv.entry_useragent,
                conv.state,
                json.dumps(conv.raw_payload) if conv.raw_payload is not None else None,
                now,
                now,
            ),
        )

    def _upsert_conversion_aggregate(self, conn: sqlite3.Connection, conv: ConversionLog) -> None:
        """エントリー時（実ユーザー）のIP/UAで成果を集計"""
        if not conv.entry_ipaddress or not conv.entry_useragent:
            return
        now = datetime.utcnow().isoformat()
        conn.execute(
            """
            INSERT INTO conversion_ipua_daily (
                date, media_id, program_id, ipaddress, useragent,
                conversion_count, first_time, last_time, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(date, media_id, program_id, ipaddress, useragent) DO UPDATE SET
                conversion_count = conversion_ipua_daily.conversion_count + 1,
                first_time = MIN(conversion_ipua_daily.first_time, excluded.first_time),
                last_time = MAX(conversion_ipua_daily.last_time, excluded.last_time),
                updated_at = excluded.updated_at
            """,
            (
                conv.conversion_time.date().isoformat(),
                conv.media_id,
                conv.program_id,
                conv.entry_ipaddress,
                conv.entry_useragent,
                1,
                self._iso(conv.conversion_time),
                self._iso(conv.conversion_time),
                now,
                now,
            ),
        )

    def lookup_click_by_cid(self, cid: str) -> tuple[str, str, datetime] | None:
        """
        cidからクリック時点のIP/UAを検索する。
        click_rawテーブルから検索し、見つかればIP, UA, click_timeを返す。
        """
        if not self._table_exists("click_raw"):
            return None
        with self._connect() as conn:
            cur = conn.execute(
                """
                SELECT ipaddress, useragent, click_time
                FROM click_raw
                WHERE id = ?
                """,
                (cid,),
            )
            row = cur.fetchone()
            if row:
                return row[0], row[1], self._from_iso(row[2])
            return None

    def lookup_clicks_by_cids(self, cids: List[str]) -> dict[str, tuple[str, str, datetime]]:
        """
        複数のcidからクリック時点のIP/UAをバッチ検索する。
        戻り値: {cid: (ipaddress, useragent, click_time)}
        """
        if not cids or not self._table_exists("click_raw"):
            return {}
        result: dict[str, tuple[str, str, datetime]] = {}
        with self._connect() as conn:
            # SQLiteのIN句の制限を考慮してバッチ処理
            batch_size = 500
            for i in range(0, len(cids), batch_size):
                batch = cids[i : i + batch_size]
                placeholders = ",".join("?" * len(batch))
                cur = conn.execute(
                    f"""
                    SELECT id, ipaddress, useragent, click_time
                    FROM click_raw
                    WHERE id IN ({placeholders})
                    """,
                    batch,
                )
                for row in cur.fetchall():
                    result[row[0]] = (row[1], row[2], self._from_iso(row[3]))
        return result

    def enrich_conversions_with_click_info(
        self, conversions: List[ConversionLog]
    ) -> List[ConversionWithClickInfo]:
        """
        成果ログにクリック時点のIP/UA情報を突合して付加する。
        cidがないか、クリックログが見つからない成果はスキップされる。
        """
        # cidを持つ成果のみ抽出
        cids = [c.cid for c in conversions if c.cid]
        if not cids:
            return []

        # バッチでクリック情報を取得
        click_info_map = self.lookup_clicks_by_cids(cids)

        result: List[ConversionWithClickInfo] = []
        for conv in conversions:
            if not conv.cid or conv.cid not in click_info_map:
                continue
            ip, ua, click_time = click_info_map[conv.cid]
            # ConversionLogにクリック情報を設定
            conv.click_ipaddress = ip
            conv.click_useragent = ua
            result.append(
                ConversionWithClickInfo(
                    conversion=conv,
                    click_ipaddress=ip,
                    click_useragent=ua,
                    click_time=click_time,
                )
            )
        return result

    def fetch_conversion_rollups(self, target_date: date) -> List[ConversionIpUaRollup]:
        """日付指定で成果のIP/UAロールアップを取得"""
        if not self._table_exists("conversion_ipua_daily"):
            return []
        with self._connect() as conn:
            cur = conn.execute(
                """
                SELECT
                    date,
                    ipaddress,
                    useragent,
                    SUM(conversion_count) AS total_conversions,
                    COUNT(DISTINCT media_id) AS media_count,
                    COUNT(DISTINCT program_id) AS program_count,
                    MIN(first_time) AS first_time,
                    MAX(last_time) AS last_time
                FROM conversion_ipua_daily
                WHERE date = ?
                GROUP BY date, ipaddress, useragent
                """,
                (target_date.isoformat(),),
            )
            rows = cur.fetchall()
        return [self._to_conversion_rollup(r) for r in rows]

    def fetch_suspicious_conversion_rollups(
        self,
        target_date: date,
        *,
        conversion_threshold: int = 5,
        media_threshold: int = 2,
        program_threshold: int = 2,
        browser_only: bool = False,
        exclude_datacenter_ip: bool = False,
    ) -> List[ConversionIpUaRollup]:
        """疑わしい成果のIP/UAロールアップを抽出"""
        if not self._table_exists("conversion_ipua_daily"):
            return []

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
            """

        datacenter_filter = ""
        if exclude_datacenter_ip:
            datacenter_filter = """
                AND ipaddress NOT LIKE '35.%'
                AND ipaddress NOT LIKE '34.%'
                AND ipaddress NOT LIKE '13.%'
                AND ipaddress NOT LIKE '52.%'
                AND ipaddress NOT LIKE '54.%'
            """

        query = f"""
            SELECT
                date,
                ipaddress,
                useragent,
                SUM(conversion_count) AS total_conversions,
                COUNT(DISTINCT media_id) AS media_count,
                COUNT(DISTINCT program_id) AS program_count,
                MIN(first_time) AS first_time,
                MAX(last_time) AS last_time
            FROM conversion_ipua_daily
            WHERE date = ?
            {browser_filter}
            {datacenter_filter}
            GROUP BY date, ipaddress, useragent
            HAVING
                SUM(conversion_count) >= ?
                OR COUNT(DISTINCT media_id) >= ?
                OR COUNT(DISTINCT program_id) >= ?
        """

        with self._connect() as conn:
            cur = conn.execute(
                query,
                (
                    target_date.isoformat(),
                    conversion_threshold,
                    media_threshold,
                    program_threshold,
                ),
            )
            rows = cur.fetchall()
        return [self._to_conversion_rollup(r) for r in rows]

    def _to_conversion_rollup(self, row: tuple) -> ConversionIpUaRollup:
        return ConversionIpUaRollup(
            date=date.fromisoformat(row[0]),
            ipaddress=row[1],
            useragent=row[2],
            conversion_count=row[3],
            media_count=row[4],
            program_count=row[5],
            first_conversion_time=self._from_iso(row[6]),
            last_conversion_time=self._from_iso(row[7]),
        )

    def update_conversion_click_info(self, conversion_id: str, ip: str, ua: str) -> None:
        """成果ログにクリック時点のIP/UAを更新"""
        if not self._table_exists("conversion_raw"):
            return
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE conversion_raw
                SET click_ipaddress = ?, click_useragent = ?, updated_at = ?
                WHERE id = ?
                """,
                (ip, ua, datetime.utcnow().isoformat(), conversion_id),
            )

    # ==================== マージ機能（重複チェック付き取り込み） ====================

    def get_existing_click_ids(self, click_ids: List[str]) -> set[str]:
        """
        指定されたclick_idのうち、既にDBに存在するものを返す。
        click_rawテーブルが存在しない場合は空setを返す。
        """
        if not click_ids or not self._table_exists("click_raw"):
            return set()
        
        result: set[str] = set()
        with self._connect() as conn:
            batch_size = 500
            for i in range(0, len(click_ids), batch_size):
                batch = click_ids[i : i + batch_size]
                placeholders = ",".join("?" * len(batch))
                cur = conn.execute(
                    f"SELECT id FROM click_raw WHERE id IN ({placeholders})",
                    batch,
                )
                for row in cur.fetchall():
                    result.add(row[0])
        return result

    def get_existing_conversion_ids(self, conversion_ids: List[str]) -> set[str]:
        """
        指定されたconversion_idのうち、既にDBに存在するものを返す。
        """
        if not conversion_ids or not self._table_exists("conversion_raw"):
            return set()
        
        result: set[str] = set()
        with self._connect() as conn:
            batch_size = 500
            for i in range(0, len(conversion_ids), batch_size):
                batch = conversion_ids[i : i + batch_size]
                placeholders = ",".join("?" * len(batch))
                cur = conn.execute(
                    f"SELECT id FROM conversion_raw WHERE id IN ({placeholders})",
                    batch,
                )
                for row in cur.fetchall():
                    result.add(row[0])
        return result

    def merge_clicks(
        self, clicks: Iterable[ClickLog], *, store_raw: bool
    ) -> tuple[int, int]:
        """
        クリックログをマージ（重複チェック付き）。
        既存データはスキップし、新規データのみ追加する。
        
        Returns:
            tuple[int, int]: (新規追加件数, スキップ件数)
        """
        self.ensure_schema(store_raw=store_raw)
        clicks_list = list(clicks)
        
        # 既存IDをチェック
        if store_raw:
            all_ids = [c.click_id for c in clicks_list if c.click_id]
            existing_ids = self.get_existing_click_ids(all_ids)
        else:
            existing_ids = set()
        
        new_count = 0
        skip_count = 0
        
        with self._connect() as conn:
            for click in clicks_list:
                # store_rawの場合、IDで重複チェック
                if store_raw and click.click_id and click.click_id in existing_ids:
                    skip_count += 1
                    continue
                
                if store_raw:
                    self._insert_raw(conn, click)
                self._upsert_aggregate(conn, click)
                new_count += 1
        
        return new_count, skip_count

    def merge_conversions(
        self, conversions: Iterable[ConversionLog]
    ) -> tuple[int, int]:
        """
        成果ログをマージ（重複チェック付き）。
        既存データはスキップし、新規データのみ追加する。
        
        Returns:
            tuple[int, int]: (新規追加件数, スキップ件数)
        """
        self.ensure_conversion_schema()
        conversions_list = list(conversions)
        
        # 既存IDをチェック
        all_ids = [c.conversion_id for c in conversions_list if c.conversion_id]
        existing_ids = self.get_existing_conversion_ids(all_ids)
        
        new_count = 0
        skip_count = 0
        
        with self._connect() as conn:
            for conv in conversions_list:
                if conv.conversion_id and conv.conversion_id in existing_ids:
                    skip_count += 1
                    continue
                
                self._insert_conversion_raw(conn, conv)
                # エントリー時（実ユーザー）のIP/UAが設定されている場合のみ集計に追加
                if conv.entry_ipaddress and conv.entry_useragent:
                    self._upsert_conversion_aggregate(conn, conv)
                new_count += 1
        
        return new_count, skip_count
