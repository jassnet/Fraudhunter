
from __future__ import annotations

import json
import uuid
from contextlib import contextmanager
from datetime import date, datetime
from typing import Dict, Iterable, List

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from .ip_filters import BROWSER_UA_INCLUDES, BOT_UA_MARKERS, DATACENTER_IP_PREFIXES
from .time_utils import now_local

from .db import Base
from .db.session import normalize_database_url
import fraud_checker.db.models  # noqa: F401
from .models import (
    AggregatedRow,
    ClickLog,
    ConversionIpUaRollup,
    ConversionLog,
    ConversionWithClickInfo,
    IpUaRollup,
)


class PostgresRepository:
    def __init__(self, database_url: str):
        self.database_url = normalize_database_url(database_url)
        self.engine = sa.create_engine(self.database_url, pool_pre_ping=True)

    @contextmanager
    def _connect(self):
        with self.engine.begin() as conn:
            yield conn

    def _table_exists(self, name: str) -> bool:
        return sa.inspect(self.engine).has_table(name)

    def _browser_filter_sql(self) -> str:
        if not BROWSER_UA_INCLUDES:
            return ""
        include_sql = " OR ".join(
            [f"useragent ILIKE '%{token}%'" for token in BROWSER_UA_INCLUDES]
        )
        exclude_sql = " AND ".join(
            [f"useragent NOT ILIKE '%{marker}%'" for marker in BOT_UA_MARKERS]
        )
        return f"""
                AND ({include_sql})
                AND {exclude_sql}
            """

    def _datacenter_filter_sql(self, prefixes: tuple[str, ...]) -> str:
        if not prefixes:
            return ""
        return "\n                " + "\n                ".join(
            [f"AND ipaddress NOT LIKE '{prefix}%'" for prefix in prefixes]
        )

    def _normalize_query(self, query: str, params: tuple | dict) -> tuple[str, dict]:
        if isinstance(params, dict):
            return query, params
        if not params:
            return query, {}
        parts = query.split("?")
        if len(parts) - 1 != len(params):
            raise ValueError("Parameter count does not match placeholders")
        new_query = ""
        bind_params: dict[str, object] = {}
        for idx, part in enumerate(parts):
            new_query += part
            if idx < len(params):
                key = f"p{idx}"
                new_query += f":{key}"
                bind_params[key] = params[idx]
        return new_query, bind_params

    def fetch_all(self, query: str, params: tuple | dict = ()) -> List[dict]:
        sql, bind_params = self._normalize_query(query, params)
        with self._connect() as conn:
            result = conn.execute(sa.text(sql), bind_params)
            return [dict(row) for row in result.mappings().all()]

    def fetch_one(self, query: str, params: tuple | dict = ()) -> dict | None:
        sql, bind_params = self._normalize_query(query, params)
        with self._connect() as conn:
            row = conn.execute(sa.text(sql), bind_params).mappings().first()
            return dict(row) if row else None

    def ensure_schema(self, store_raw: bool = False) -> None:
        tables = [Base.metadata.tables["click_ipua_daily"]]
        if store_raw:
            tables.append(Base.metadata.tables["click_raw"])
        Base.metadata.create_all(self.engine, tables=tables)

    def ensure_conversion_schema(self) -> None:
        Base.metadata.create_all(
            self.engine,
            tables=[
                Base.metadata.tables["conversion_raw"],
                Base.metadata.tables["conversion_ipua_daily"],
            ],
        )

    def ensure_master_schema(self) -> None:
        Base.metadata.create_all(
            self.engine,
            tables=[
                Base.metadata.tables["master_media"],
                Base.metadata.tables["master_promotion"],
                Base.metadata.tables["master_user"],
            ],
        )

    def ensure_settings_schema(self) -> None:
        Base.metadata.create_all(self.engine, tables=[Base.metadata.tables["app_settings"]])

    def _insert_click_raw(self, conn: sa.Connection, click: ClickLog) -> None:
        table = Base.metadata.tables["click_raw"]
        now = now_local()
        insert_stmt = pg_insert(table)
        update_stmt = {
            "click_time": insert_stmt.excluded.click_time,
            "media_id": insert_stmt.excluded.media_id,
            "program_id": insert_stmt.excluded.program_id,
            "ipaddress": insert_stmt.excluded.ipaddress,
            "useragent": insert_stmt.excluded.useragent,
            "referrer": insert_stmt.excluded.referrer,
            "raw_payload": insert_stmt.excluded.raw_payload,
            "created_at": insert_stmt.excluded.created_at,
            "updated_at": insert_stmt.excluded.updated_at,
        }
        stmt = insert_stmt.on_conflict_do_update(index_elements=["id"], set_=update_stmt)
        payload = {
            "id": click.click_id or uuid.uuid4().hex,
            "click_time": click.click_time,
            "media_id": click.media_id,
            "program_id": click.program_id,
            "ipaddress": click.ipaddress,
            "useragent": click.useragent,
            "referrer": click.referrer,
            "raw_payload": json.dumps(click.raw_payload) if click.raw_payload is not None else None,
            "created_at": now,
            "updated_at": now,
        }
        conn.execute(stmt, payload)

    def _upsert_click_aggregate(self, conn: sa.Connection, click: ClickLog) -> None:
        table = Base.metadata.tables["click_ipua_daily"]
        now = now_local()
        insert_stmt = pg_insert(table).values(
            date=click.click_time.date(),
            media_id=click.media_id,
            program_id=click.program_id,
            ipaddress=click.ipaddress,
            useragent=click.useragent,
            click_count=1,
            first_time=click.click_time,
            last_time=click.click_time,
            created_at=now,
            updated_at=now,
        )
        stmt = insert_stmt.on_conflict_do_update(
            index_elements=["date", "media_id", "program_id", "ipaddress", "useragent"],
            set_={
                "click_count": table.c.click_count + 1,
                "first_time": sa.func.least(table.c.first_time, insert_stmt.excluded.first_time),
                "last_time": sa.func.greatest(table.c.last_time, insert_stmt.excluded.last_time),
                "updated_at": insert_stmt.excluded.updated_at,
            },
        )
        conn.execute(stmt)

    def clear_date(self, target_date: date, *, store_raw: bool) -> None:
        with self._connect() as conn:
            conn.execute(
                sa.text("DELETE FROM click_ipua_daily WHERE date = :target_date"),
                {"target_date": target_date},
            )
            if store_raw and self._table_exists("click_raw"):
                conn.execute(
                    sa.text("DELETE FROM click_raw WHERE CAST(click_time AS date) = :target_date"),
                    {"target_date": target_date},
                )

    def ingest_clicks(self, clicks: Iterable[ClickLog], *, target_date: date, store_raw: bool) -> int:
        self.ensure_schema(store_raw=store_raw)
        self.clear_date(target_date, store_raw=store_raw)

        count = 0
        with self._connect() as conn:
            for click in clicks:
                if click.click_time.date() != target_date:
                    continue
                if store_raw:
                    self._insert_click_raw(conn, click)
                self._upsert_click_aggregate(conn, click)
                count += 1
        return count

    def fetch_aggregates(self, target_date: date) -> List[AggregatedRow]:
        with self._connect() as conn:
            result = conn.execute(
                sa.text(
                    """
                    SELECT date, media_id, program_id, ipaddress, useragent,
                           click_count, first_time, last_time, created_at, updated_at
                    FROM click_ipua_daily
                    WHERE date = :target_date
                    """
                ),
                {"target_date": target_date},
            )
            rows = result.fetchall()
        return [
            AggregatedRow(
                date=row[0],
                media_id=row[1],
                program_id=row[2],
                ipaddress=row[3],
                useragent=row[4],
                click_count=row[5],
                first_time=row[6],
                last_time=row[7],
                created_at=row[8],
                updated_at=row[9],
            )
            for row in rows
        ]

    def count_raw_rows(self, target_date: date) -> int:
        if not self._table_exists("click_raw"):
            return 0
        with self._connect() as conn:
            result = conn.execute(
                sa.text("SELECT COUNT(*) FROM click_raw WHERE CAST(click_time AS date) = :target_date"),
                {"target_date": target_date},
            ).scalar_one()
        return int(result)

    def fetch_rollups(self, target_date: date) -> List[IpUaRollup]:
        with self._connect() as conn:
            result = conn.execute(
                sa.text(
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
                    WHERE date = :target_date
                    GROUP BY date, ipaddress, useragent
                    """
                ),
                {"target_date": target_date},
            )
            rows = result.fetchall()
        return [
            IpUaRollup(
                date=row[0],
                ipaddress=row[1],
                useragent=row[2],
                total_clicks=row[3],
                media_count=row[4],
                program_count=row[5],
                first_time=row[6],
                last_time=row[7],
            )
            for row in rows
        ]
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
        browser_filter = ""
        if browser_only:
            browser_filter = self._browser_filter_sql()

        datacenter_filter = ""
        if exclude_datacenter_ip:
            datacenter_filter = self._datacenter_filter_sql(DATACENTER_IP_PREFIXES)

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
            WHERE date = :target_date
            {browser_filter}
            {datacenter_filter}
            GROUP BY date, ipaddress, useragent
            HAVING
                SUM(click_count) >= :click_threshold
                OR COUNT(DISTINCT media_id) >= :media_threshold
                OR COUNT(DISTINCT program_id) >= :program_threshold
                OR SUM(click_count) >= :burst_click_threshold
        """

        with self._connect() as conn:
            result = conn.execute(
                sa.text(query),
                {
                    "target_date": target_date,
                    "click_threshold": click_threshold,
                    "media_threshold": media_threshold,
                    "program_threshold": program_threshold,
                    "burst_click_threshold": burst_click_threshold,
                },
            )
            rows = result.fetchall()
        return [
            IpUaRollup(
                date=row[0],
                ipaddress=row[1],
                useragent=row[2],
                total_clicks=row[3],
                media_count=row[4],
                program_count=row[5],
                first_time=row[6],
                last_time=row[7],
            )
            for row in rows
        ]

    def _clear_conversions_date(self, conn: sa.Connection, target_date: date) -> None:
        if self._table_exists("conversion_raw"):
            conn.execute(
                sa.text("DELETE FROM conversion_raw WHERE CAST(conversion_time AS date) = :target_date"),
                {"target_date": target_date},
            )
        if self._table_exists("conversion_ipua_daily"):
            conn.execute(
                sa.text("DELETE FROM conversion_ipua_daily WHERE date = :target_date"),
                {"target_date": target_date},
            )

    def _insert_conversion_raw(self, conn: sa.Connection, conv: ConversionLog) -> None:
        table = Base.metadata.tables["conversion_raw"]
        now = now_local()
        insert_stmt = pg_insert(table)
        update_stmt = {
            "cid": insert_stmt.excluded.cid,
            "conversion_time": insert_stmt.excluded.conversion_time,
            "click_time": insert_stmt.excluded.click_time,
            "media_id": insert_stmt.excluded.media_id,
            "program_id": insert_stmt.excluded.program_id,
            "user_id": insert_stmt.excluded.user_id,
            "postback_ipaddress": insert_stmt.excluded.postback_ipaddress,
            "postback_useragent": insert_stmt.excluded.postback_useragent,
            "entry_ipaddress": insert_stmt.excluded.entry_ipaddress,
            "entry_useragent": insert_stmt.excluded.entry_useragent,
            "state": insert_stmt.excluded.state,
            "raw_payload": insert_stmt.excluded.raw_payload,
            "created_at": insert_stmt.excluded.created_at,
            "updated_at": insert_stmt.excluded.updated_at,
        }
        stmt = insert_stmt.on_conflict_do_update(index_elements=["id"], set_=update_stmt)
        conn.execute(
            stmt,
            {
                "id": conv.conversion_id,
                "cid": conv.cid,
                "conversion_time": conv.conversion_time,
                "click_time": conv.click_time,
                "media_id": conv.media_id,
                "program_id": conv.program_id,
                "user_id": conv.user_id,
                "postback_ipaddress": conv.postback_ipaddress,
                "postback_useragent": conv.postback_useragent,
                "entry_ipaddress": conv.entry_ipaddress,
                "entry_useragent": conv.entry_useragent,
                "state": conv.state,
                "raw_payload": json.dumps(conv.raw_payload) if conv.raw_payload is not None else None,
                "created_at": now,
                "updated_at": now,
            },
        )

    def _upsert_conversion_aggregate(self, conn: sa.Connection, conv: ConversionLog) -> None:
        table = Base.metadata.tables["conversion_ipua_daily"]
        now = now_local()
        insert_stmt = pg_insert(table).values(
            date=conv.conversion_time.date(),
            media_id=conv.media_id,
            program_id=conv.program_id,
            ipaddress=conv.entry_ipaddress,
            useragent=conv.entry_useragent,
            conversion_count=1,
            first_time=conv.conversion_time,
            last_time=conv.conversion_time,
            created_at=now,
            updated_at=now,
        )
        stmt = insert_stmt.on_conflict_do_update(
            index_elements=["date", "media_id", "program_id", "ipaddress", "useragent"],
            set_={
                "conversion_count": table.c.conversion_count + 1,
                "first_time": sa.func.least(table.c.first_time, insert_stmt.excluded.first_time),
                "last_time": sa.func.greatest(table.c.last_time, insert_stmt.excluded.last_time),
                "updated_at": insert_stmt.excluded.updated_at,
            },
        )
        conn.execute(stmt)

    def ingest_conversions(self, conversions: Iterable[ConversionLog], *, target_date: date) -> int:
        self.ensure_conversion_schema()
        count = 0
        with self._connect() as conn:
            self._clear_conversions_date(conn, target_date)
            for conv in conversions:
                if conv.conversion_time.date() != target_date:
                    continue
                self._insert_conversion_raw(conn, conv)
                if conv.entry_ipaddress and conv.entry_useragent:
                    self._upsert_conversion_aggregate(conn, conv)
                count += 1
        return count

    def fetch_conversion_rollups(self, target_date: date) -> List[ConversionIpUaRollup]:
        if not self._table_exists("conversion_ipua_daily"):
            return []
        with self._connect() as conn:
            result = conn.execute(
                sa.text(
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
                    WHERE date = :target_date
                    GROUP BY date, ipaddress, useragent
                    """
                ),
                {"target_date": target_date},
            )
            rows = result.fetchall()
        return [
            ConversionIpUaRollup(
                date=row[0],
                ipaddress=row[1],
                useragent=row[2],
                conversion_count=row[3],
                media_count=row[4],
                program_count=row[5],
                first_conversion_time=row[6],
                last_conversion_time=row[7],
            )
            for row in rows
        ]

    def fetch_click_to_conversion_gaps(self, target_date: date) -> Dict[tuple[str, str], Dict[str, float]]:
        if not self._table_exists("conversion_raw"):
            return {}
        with self._connect() as conn:
            rows = conn.execute(
                sa.text(
                    """
                    SELECT entry_ipaddress, entry_useragent, conversion_time, click_time
                    FROM conversion_raw
                    WHERE CAST(conversion_time AS date) = :target_date
                      AND click_time IS NOT NULL
                      AND entry_ipaddress IS NOT NULL
                      AND entry_useragent IS NOT NULL
                    """
                ),
                {"target_date": target_date},
            ).fetchall()

        stats: Dict[tuple[str, str], Dict[str, float]] = {}
        for entry_ip, entry_ua, conv_dt, click_dt in rows:
            if not conv_dt or not click_dt:
                continue
            gap_seconds = (conv_dt - click_dt).total_seconds()
            key = (entry_ip, entry_ua)
            if key not in stats:
                stats[key] = {"min": gap_seconds, "max": gap_seconds, "count": 1}
            else:
                stats[key]["min"] = min(stats[key]["min"], gap_seconds)
                stats[key]["max"] = max(stats[key]["max"], gap_seconds)
                stats[key]["count"] += 1
        return stats

    def fetch_suspicious_conversion_rollups(
        self,
        target_date: date,
        *,
        conversion_threshold: int = 5,
        media_threshold: int = 2,
        program_threshold: int = 2,
        burst_conversion_threshold: int = 3,
        browser_only: bool = False,
        exclude_datacenter_ip: bool = False,
    ) -> List[ConversionIpUaRollup]:
        if not self._table_exists("conversion_ipua_daily"):
            return []

        browser_filter = ""
        if browser_only:
            browser_filter = self._browser_filter_sql()

        datacenter_filter = ""
        if exclude_datacenter_ip:
            datacenter_filter = self._datacenter_filter_sql(DATACENTER_IP_PREFIXES)

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
            WHERE date = :target_date
            {browser_filter}
            {datacenter_filter}
            GROUP BY date, ipaddress, useragent
            HAVING
                SUM(conversion_count) >= :conversion_threshold
                OR COUNT(DISTINCT media_id) >= :media_threshold
                OR COUNT(DISTINCT program_id) >= :program_threshold
                OR SUM(conversion_count) >= :burst_conversion_threshold
        """

        with self._connect() as conn:
            rows = conn.execute(
                sa.text(query),
                {
                    "target_date": target_date,
                    "conversion_threshold": conversion_threshold,
                    "media_threshold": media_threshold,
                    "program_threshold": program_threshold,
                    "burst_conversion_threshold": burst_conversion_threshold,
                },
            ).fetchall()
        return [
            ConversionIpUaRollup(
                date=row[0],
                ipaddress=row[1],
                useragent=row[2],
                conversion_count=row[3],
                media_count=row[4],
                program_count=row[5],
                first_conversion_time=row[6],
                last_conversion_time=row[7],
            )
            for row in rows
        ]

    def update_conversion_click_info(self, conversion_id: str, ip: str, ua: str) -> None:
        if not self._table_exists("conversion_raw"):
            return
        with self._connect() as conn:
            conn.execute(
                sa.text(
                    """
                    UPDATE conversion_raw
                    SET click_ipaddress = :ip, click_useragent = :ua, updated_at = :updated_at
                    WHERE id = :conversion_id
                    """
                ),
                {"ip": ip, "ua": ua, "updated_at": now_local(), "conversion_id": conversion_id},
            )

    def lookup_click_by_cid(self, cid: str) -> tuple[str, str, datetime] | None:
        if not self._table_exists("click_raw"):
            return None
        with self._connect() as conn:
            row = conn.execute(
                sa.text(
                    """
                    SELECT ipaddress, useragent, click_time
                    FROM click_raw
                    WHERE id = :cid
                    """
                ),
                {"cid": cid},
            ).first()
        if row:
            return row[0], row[1], row[2]
        return None

    def lookup_clicks_by_cids(self, cids: List[str]) -> dict[str, tuple[str, str, datetime]]:
        if not cids or not self._table_exists("click_raw"):
            return {}
        result: dict[str, tuple[str, str, datetime]] = {}
        with self._connect() as conn:
            rows = conn.execute(
                sa.text(
                    """
                    SELECT id, ipaddress, useragent, click_time
                    FROM click_raw
                    WHERE id = ANY(:cids)
                    """
                ),
                {"cids": cids},
            ).fetchall()
        for row in rows:
            result[row[0]] = (row[1], row[2], row[3])
        return result

    def enrich_conversions_with_click_info(
        self, conversions: List[ConversionLog]
    ) -> List[ConversionWithClickInfo]:
        cids = [c.cid for c in conversions if c.cid]
        if not cids:
            return []
        click_info_map = self.lookup_clicks_by_cids(cids)
        result: List[ConversionWithClickInfo] = []
        for conv in conversions:
            if not conv.cid or conv.cid not in click_info_map:
                continue
            ip, ua, click_time = click_info_map[conv.cid]
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

    def get_existing_click_ids(self, click_ids: List[str]) -> set[str]:
        if not click_ids or not self._table_exists("click_raw"):
            return set()
        with self._connect() as conn:
            rows = conn.execute(
                sa.text("SELECT id FROM click_raw WHERE id = ANY(:ids)"),
                {"ids": click_ids},
            ).fetchall()
        return {row[0] for row in rows}

    def get_existing_conversion_ids(self, conversion_ids: List[str]) -> set[str]:
        if not conversion_ids or not self._table_exists("conversion_raw"):
            return set()
        with self._connect() as conn:
            rows = conn.execute(
                sa.text("SELECT id FROM conversion_raw WHERE id = ANY(:ids)"),
                {"ids": conversion_ids},
            ).fetchall()
        return {row[0] for row in rows}

    def merge_clicks(self, clicks: Iterable[ClickLog], *, store_raw: bool) -> tuple[int, int]:
        self.ensure_schema(store_raw=store_raw)
        new_count = 0
        skip_count = 0
        with self._connect() as conn:
            for click in clicks:
                if store_raw:
                    table = Base.metadata.tables["click_raw"]
                    now = now_local()
                    insert_stmt = pg_insert(table).values(
                        id=click.click_id or uuid.uuid4().hex,
                        click_time=click.click_time,
                        media_id=click.media_id,
                        program_id=click.program_id,
                        ipaddress=click.ipaddress,
                        useragent=click.useragent,
                        referrer=click.referrer,
                        raw_payload=json.dumps(click.raw_payload) if click.raw_payload is not None else None,
                        created_at=now,
                        updated_at=now,
                    ).on_conflict_do_nothing(index_elements=["id"])
                    result = conn.execute(insert_stmt)
                    if result.rowcount == 0:
                        skip_count += 1
                        continue
                self._upsert_click_aggregate(conn, click)
                new_count += 1
        return new_count, skip_count

    def merge_conversions(self, conversions: Iterable[ConversionLog]) -> tuple[int, int]:
        self.ensure_conversion_schema()
        new_count = 0
        skip_count = 0
        with self._connect() as conn:
            for conv in conversions:
                table = Base.metadata.tables["conversion_raw"]
                now = now_local()
                insert_stmt = pg_insert(table).values(
                    id=conv.conversion_id,
                    cid=conv.cid,
                    conversion_time=conv.conversion_time,
                    click_time=conv.click_time,
                    media_id=conv.media_id,
                    program_id=conv.program_id,
                    user_id=conv.user_id,
                    postback_ipaddress=conv.postback_ipaddress,
                    postback_useragent=conv.postback_useragent,
                    entry_ipaddress=conv.entry_ipaddress,
                    entry_useragent=conv.entry_useragent,
                    state=conv.state,
                    raw_payload=json.dumps(conv.raw_payload) if conv.raw_payload is not None else None,
                    created_at=now,
                    updated_at=now,
                ).on_conflict_do_nothing(index_elements=["id"])
                result = conn.execute(insert_stmt)
                if result.rowcount == 0:
                    skip_count += 1
                    continue
                if conv.entry_ipaddress and conv.entry_useragent:
                    self._upsert_conversion_aggregate(conn, conv)
                new_count += 1
        return new_count, skip_count

    def upsert_media(self, media_id: str, name: str, user_id: str | None = None, state: str | None = None) -> None:
        self.ensure_master_schema()
        table = Base.metadata.tables["master_media"]
        now = now_local()
        stmt = pg_insert(table).values(
            id=media_id,
            name=name,
            user_id=user_id,
            state=state,
            updated_at=now,
        ).on_conflict_do_update(
            index_elements=["id"],
            set_={"name": name, "user_id": user_id, "state": state, "updated_at": now},
        )
        with self._connect() as conn:
            conn.execute(stmt)

    def upsert_promotion(self, promotion_id: str, name: str, state: str | None = None) -> None:
        self.ensure_master_schema()
        table = Base.metadata.tables["master_promotion"]
        now = now_local()
        stmt = pg_insert(table).values(
            id=promotion_id,
            name=name,
            state=state,
            updated_at=now,
        ).on_conflict_do_update(
            index_elements=["id"],
            set_={"name": name, "state": state, "updated_at": now},
        )
        with self._connect() as conn:
            conn.execute(stmt)

    def upsert_user(self, user_id: str, name: str, company: str | None = None, state: str | None = None) -> None:
        self.ensure_master_schema()
        table = Base.metadata.tables["master_user"]
        now = now_local()
        stmt = pg_insert(table).values(
            id=user_id,
            name=name,
            company=company,
            state=state,
            updated_at=now,
        ).on_conflict_do_update(
            index_elements=["id"],
            set_={"name": name, "company": company, "state": state, "updated_at": now},
        )
        with self._connect() as conn:
            conn.execute(stmt)

    def bulk_upsert_media(self, media_list: List[dict]) -> int:
        if not media_list:
            return 0
        self.ensure_master_schema()
        table = Base.metadata.tables["master_media"]
        now = now_local()
        rows = [
            {
                "id": m.get("id"),
                "name": m.get("name", ""),
                "user_id": m.get("user"),
                "state": m.get("state"),
                "updated_at": now,
            }
            for m in media_list
        ]
        stmt = pg_insert(table).on_conflict_do_update(
            index_elements=["id"],
            set_={
                "name": sa.text("excluded.name"),
                "user_id": sa.text("excluded.user_id"),
                "state": sa.text("excluded.state"),
                "updated_at": sa.text("excluded.updated_at"),
            },
        )
        with self._connect() as conn:
            conn.execute(stmt, rows)
        return len(rows)

    def bulk_upsert_promotions(self, promo_list: List[dict]) -> int:
        if not promo_list:
            return 0
        self.ensure_master_schema()
        table = Base.metadata.tables["master_promotion"]
        now = now_local()
        rows = [
            {
                "id": p.get("id"),
                "name": p.get("name", ""),
                "state": p.get("state"),
                "updated_at": now,
            }
            for p in promo_list
        ]
        stmt = pg_insert(table).on_conflict_do_update(
            index_elements=["id"],
            set_={
                "name": sa.text("excluded.name"),
                "state": sa.text("excluded.state"),
                "updated_at": sa.text("excluded.updated_at"),
            },
        )
        with self._connect() as conn:
            conn.execute(stmt, rows)
        return len(rows)

    def bulk_upsert_users(self, user_list: List[dict]) -> int:
        if not user_list:
            return 0
        self.ensure_master_schema()
        table = Base.metadata.tables["master_user"]
        now = now_local()
        rows = [
            {
                "id": u.get("id"),
                "name": u.get("name", ""),
                "company": u.get("company"),
                "state": u.get("state"),
                "updated_at": now,
            }
            for u in user_list
        ]
        stmt = pg_insert(table).on_conflict_do_update(
            index_elements=["id"],
            set_={
                "name": sa.text("excluded.name"),
                "company": sa.text("excluded.company"),
                "state": sa.text("excluded.state"),
                "updated_at": sa.text("excluded.updated_at"),
            },
        )
        with self._connect() as conn:
            conn.execute(stmt, rows)
        return len(rows)

    def get_all_masters(self) -> dict:
        self.ensure_master_schema()
        with self._connect() as conn:
            media_count = conn.execute(sa.text("SELECT COUNT(*) FROM master_media")).scalar_one()
            promo_count = conn.execute(sa.text("SELECT COUNT(*) FROM master_promotion")).scalar_one()
            user_count = conn.execute(sa.text("SELECT COUNT(*) FROM master_user")).scalar_one()
            last_synced_row = conn.execute(
                sa.text(
                    """
                    SELECT MAX(updated_at) FROM (
                        SELECT updated_at FROM master_media
                        UNION ALL
                        SELECT updated_at FROM master_promotion
                        UNION ALL
                        SELECT updated_at FROM master_user
                    ) t
                    """
                )
            ).first()
            last_synced_at = last_synced_row[0] if last_synced_row else None
        return {
            "media_count": media_count,
            "promotion_count": promo_count,
            "user_count": user_count,
            "last_synced_at": last_synced_at,
        }

    def get_suspicious_click_details_bulk(
        self, target_date: date, ip_ua_pairs: List[tuple[str, str]]
    ) -> Dict[tuple[str, str], List[dict]]:
        if not ip_ua_pairs:
            return {}

        results: Dict[tuple[str, str], List[dict]] = {}
        chunk_size = 400

        with self._connect() as conn:
            for i in range(0, len(ip_ua_pairs), chunk_size):
                chunk = ip_ua_pairs[i : i + chunk_size]
                placeholders = ",".join([f"(:ip{idx}, :ua{idx})" for idx in range(len(chunk))])
                params: dict[str, object] = {"target_date": target_date}
                for idx, (ip, ua) in enumerate(chunk):
                    params[f"ip{idx}"] = ip
                    params[f"ua{idx}"] = ua

                query = f"""
                    SELECT
                        c.ipaddress,
                        c.useragent,
                        c.media_id,
                        c.program_id,
                        SUM(c.click_count) as click_count,
                        m.name as media_name,
                        p.name as program_name,
                        u.name as affiliate_name
                    FROM click_ipua_daily c
                    LEFT JOIN master_media m ON c.media_id = m.id
                    LEFT JOIN master_promotion p ON c.program_id = p.id
                    LEFT JOIN master_user u ON m.user_id = u.id
                    WHERE c.date = :target_date AND (c.ipaddress, c.useragent) IN ({placeholders})
                    GROUP BY c.ipaddress, c.useragent, c.media_id, c.program_id, m.name, p.name, u.name
                    ORDER BY click_count DESC
                """

                rows = conn.execute(sa.text(query), params).fetchall()
                for row in rows:
                    key = (row[0], row[1])
                    results.setdefault(key, []).append(
                        {
                            "media_id": row[2],
                            "program_id": row[3],
                            "click_count": row[4],
                            "media_name": row[5] or row[2],
                            "program_name": row[6] or row[3],
                            "affiliate_name": row[7] or None,
                        }
                    )
        return results

    def get_suspicious_conversion_details_bulk(
        self, target_date: date, ip_ua_pairs: List[tuple[str, str]]
    ) -> Dict[tuple[str, str], List[dict]]:
        if not ip_ua_pairs:
            return {}

        results: Dict[tuple[str, str], List[dict]] = {}
        chunk_size = 400

        with self._connect() as conn:
            for i in range(0, len(ip_ua_pairs), chunk_size):
                chunk = ip_ua_pairs[i : i + chunk_size]
                placeholders = ",".join([f"(:ip{idx}, :ua{idx})" for idx in range(len(chunk))])
                params: dict[str, object] = {"target_date": target_date}
                for idx, (ip, ua) in enumerate(chunk):
                    params[f"ip{idx}"] = ip
                    params[f"ua{idx}"] = ua

                query = f"""
                    SELECT
                        c.ipaddress,
                        c.useragent,
                        c.media_id,
                        c.program_id,
                        SUM(c.conversion_count) as conversion_count,
                        m.name as media_name,
                        p.name as program_name,
                        u.name as affiliate_name
                    FROM conversion_ipua_daily c
                    LEFT JOIN master_media m ON c.media_id = m.id
                    LEFT JOIN master_promotion p ON c.program_id = p.id
                    LEFT JOIN master_user u ON m.user_id = u.id
                    WHERE c.date = :target_date AND (c.ipaddress, c.useragent) IN ({placeholders})
                    GROUP BY c.ipaddress, c.useragent, c.media_id, c.program_id, m.name, p.name, u.name
                    ORDER BY conversion_count DESC
                """

                rows = conn.execute(sa.text(query), params).fetchall()
                for row in rows:
                    key = (row[0], row[1])
                    results.setdefault(key, []).append(
                        {
                            "media_id": row[2],
                            "program_id": row[3],
                            "conversion_count": row[4],
                            "media_name": row[5] or row[2],
                            "program_name": row[6] or row[3],
                            "affiliate_name": row[7] or None,
                        }
                    )
        return results

    def save_settings(self, settings: dict) -> None:
        self.ensure_settings_schema()
        table = Base.metadata.tables["app_settings"]
        now = now_local()
        rows = [
            {"key": key, "value": json.dumps(value), "updated_at": now}
            for key, value in settings.items()
        ]
        if not rows:
            return
        stmt = pg_insert(table).on_conflict_do_update(
            index_elements=["key"],
            set_={"value": sa.text("excluded.value"), "updated_at": sa.text("excluded.updated_at")},
        )
        with self._connect() as conn:
            conn.execute(stmt, rows)

    def load_settings(self) -> dict | None:
        self.ensure_settings_schema()
        with self._connect() as conn:
            rows = conn.execute(sa.text("SELECT key, value FROM app_settings")).fetchall()
        if not rows:
            return None
        settings: dict = {}
        for key, value in rows:
            try:
                settings[key] = json.loads(value)
            except json.JSONDecodeError:
                settings[key] = value
        return settings or None
