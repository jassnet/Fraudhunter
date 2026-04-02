from __future__ import annotations

import json
from datetime import date, datetime
from typing import Iterable
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..db import Base
from ..models import CheckLog, ClickLog, ConversionLog, ConversionWithClickInfo, EntityDailyMetric, TrackLog
from ..time_utils import now_local
from .base import RepositoryBase


class IngestionRepository(RepositoryBase):
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

    def ensure_fraud_schema(self) -> None:
        Base.metadata.create_all(
            self.engine,
            tables=[
                Base.metadata.tables["check_raw"],
                Base.metadata.tables["track_raw"],
                Base.metadata.tables["click_sum_daily"],
                Base.metadata.tables["access_sum_daily"],
                Base.metadata.tables["imp_sum_daily"],
                Base.metadata.tables["fraud_findings"],
            ],
        )

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
            "click_ipaddress": insert_stmt.excluded.click_ipaddress,
            "click_useragent": insert_stmt.excluded.click_useragent,
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
                "click_ipaddress": getattr(conv, "click_ipaddress", None),
                "click_useragent": getattr(conv, "click_useragent", None),
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

    def lookup_clicks_by_cids(self, cids: list[str]) -> dict[str, tuple[str, str, datetime]]:
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
        self, conversions: list[ConversionLog]
    ) -> list[ConversionWithClickInfo]:
        cids = [c.cid for c in conversions if c.cid]
        if not cids:
            return []
        click_info_map = self.lookup_clicks_by_cids(cids)
        result: list[ConversionWithClickInfo] = []
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

    def get_existing_click_ids(self, click_ids: list[str]) -> set[str]:
        if not click_ids or not self._table_exists("click_raw"):
            return set()
        with self._connect() as conn:
            rows = conn.execute(
                sa.text("SELECT id FROM click_raw WHERE id = ANY(:ids)"),
                {"ids": click_ids},
            ).fetchall()
        return {row[0] for row in rows}

    def get_existing_conversion_ids(self, conversion_ids: list[str]) -> set[str]:
        if not conversion_ids or not self._table_exists("conversion_raw"):
            return set()
        with self._connect() as conn:
            rows = conn.execute(
                sa.text("SELECT id FROM conversion_raw WHERE id = ANY(:ids)"),
                {"ids": conversion_ids},
            ).fetchall()
        return {row[0] for row in rows}

    def merge_clicks(self, clicks: Iterable[ClickLog], *, store_raw: bool) -> tuple[int, int]:
        new_count = 0
        skip_count = 0
        with self._connect() as conn:
            for click in clicks:
                if store_raw:
                    table = Base.metadata.tables["click_raw"]
                    now = now_local()
                    insert_stmt = (
                        pg_insert(table)
                        .values(
                            id=click.click_id or uuid.uuid4().hex,
                            click_time=click.click_time,
                            media_id=click.media_id,
                            program_id=click.program_id,
                            ipaddress=click.ipaddress,
                            useragent=click.useragent,
                            referrer=click.referrer,
                            raw_payload=(
                                json.dumps(click.raw_payload)
                                if click.raw_payload is not None
                                else None
                            ),
                            created_at=now,
                            updated_at=now,
                        )
                        .on_conflict_do_nothing(index_elements=["id"])
                    )
                    result = conn.execute(insert_stmt)
                    if result.rowcount == 0:
                        skip_count += 1
                        continue
                self._upsert_click_aggregate(conn, click)
                new_count += 1
        return new_count, skip_count

    def merge_conversions(self, conversions: Iterable[ConversionLog]) -> tuple[int, int]:
        new_count = 0
        skip_count = 0
        with self._connect() as conn:
            for conv in conversions:
                table = Base.metadata.tables["conversion_raw"]
                now = now_local()
                insert_stmt = (
                    pg_insert(table)
                    .values(
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
                        click_ipaddress=getattr(conv, "click_ipaddress", None),
                        click_useragent=getattr(conv, "click_useragent", None),
                        state=conv.state,
                        raw_payload=(
                            json.dumps(conv.raw_payload)
                            if conv.raw_payload is not None
                            else None
                        ),
                        created_at=now,
                        updated_at=now,
                    )
                    .on_conflict_do_nothing(index_elements=["id"])
                )
                result = conn.execute(insert_stmt)
                if result.rowcount == 0:
                    skip_count += 1
                    continue
                if conv.entry_ipaddress and conv.entry_useragent:
                    self._upsert_conversion_aggregate(conn, conv)
                new_count += 1
        return new_count, skip_count

    def purge_raw_before(self, cutoff: datetime, *, execute: bool) -> dict[str, int]:
        targets = {
            "click_raw": ("click_time < :cutoff", {"cutoff": cutoff}),
            "conversion_raw": ("conversion_time < :cutoff", {"cutoff": cutoff}),
            "check_raw": ("regist_time < :cutoff", {"cutoff": cutoff}),
            "track_raw": ("regist_time < :cutoff", {"cutoff": cutoff}),
        }
        return self._purge_targets(targets, execute=execute)

    def purge_aggregates_before(self, cutoff: date, *, execute: bool) -> dict[str, int]:
        targets = {
            "click_ipua_daily": ("date < :cutoff", {"cutoff": cutoff}),
            "conversion_ipua_daily": ("date < :cutoff", {"cutoff": cutoff}),
            "click_sum_daily": ("date < :cutoff", {"cutoff": cutoff}),
            "access_sum_daily": ("date < :cutoff", {"cutoff": cutoff}),
            "imp_sum_daily": ("date < :cutoff", {"cutoff": cutoff}),
        }
        return self._purge_targets(targets, execute=execute)

    def replace_check_logs(self, target_date: date, checks: Iterable[CheckLog]) -> int:
        if not self._table_exists("check_raw"):
            return 0
        now = now_local()
        rows = [
            {
                "id": check.check_id,
                "affiliate_user_id": check.affiliate_user_id,
                "plid": check.plid,
                "state": check.state,
                "regist_time": check.regist_time,
                "raw_payload": json.dumps(check.raw_payload) if check.raw_payload is not None else None,
                "created_at": now,
                "updated_at": now,
            }
            for check in checks
            if check.regist_time.date() == target_date
        ]
        with self._connect() as conn:
            conn.execute(
                sa.text("DELETE FROM check_raw WHERE CAST(regist_time AS date) = :target_date"),
                {"target_date": target_date},
            )
            if rows:
                stmt = pg_insert(Base.metadata.tables["check_raw"]).on_conflict_do_update(
                    index_elements=["id"],
                    set_={
                        "affiliate_user_id": sa.text("excluded.affiliate_user_id"),
                        "plid": sa.text("excluded.plid"),
                        "state": sa.text("excluded.state"),
                        "regist_time": sa.text("excluded.regist_time"),
                        "raw_payload": sa.text("excluded.raw_payload"),
                        "created_at": sa.text("excluded.created_at"),
                        "updated_at": sa.text("excluded.updated_at"),
                    },
                )
                conn.execute(stmt, rows)
        return len(rows)

    def replace_track_logs(self, target_date: date, tracks: Iterable[TrackLog]) -> int:
        if not self._table_exists("track_raw"):
            return 0
        now = now_local()
        rows = [
            {
                "id": track.track_id,
                "action_log_raw_id": track.action_log_raw_id,
                "auth_type": track.auth_type,
                "auth_get_type": track.auth_get_type,
                "state": track.state,
                "regist_time": track.regist_time,
                "raw_payload": json.dumps(track.raw_payload) if track.raw_payload is not None else None,
                "created_at": now,
                "updated_at": now,
            }
            for track in tracks
            if track.regist_time.date() == target_date
        ]
        with self._connect() as conn:
            conn.execute(
                sa.text("DELETE FROM track_raw WHERE CAST(regist_time AS date) = :target_date"),
                {"target_date": target_date},
            )
            if rows:
                stmt = pg_insert(Base.metadata.tables["track_raw"]).on_conflict_do_update(
                    index_elements=["id"],
                    set_={
                        "action_log_raw_id": sa.text("excluded.action_log_raw_id"),
                        "auth_type": sa.text("excluded.auth_type"),
                        "auth_get_type": sa.text("excluded.auth_get_type"),
                        "state": sa.text("excluded.state"),
                        "regist_time": sa.text("excluded.regist_time"),
                        "raw_payload": sa.text("excluded.raw_payload"),
                        "created_at": sa.text("excluded.created_at"),
                        "updated_at": sa.text("excluded.updated_at"),
                    },
                )
                conn.execute(stmt, rows)
        return len(rows)

    def replace_entity_daily_metrics(
        self,
        target_date: date,
        metrics: Iterable[EntityDailyMetric],
        *,
        table_name: str,
        value_column: str,
    ) -> int:
        if not self._table_exists(table_name):
            return 0
        table = Base.metadata.tables[table_name]
        now = now_local()
        rows = [
            {
                "date": metric.metric_date,
                "user_id": metric.user_id or "",
                "media_id": metric.media_id or "",
                "promotion_id": metric.promotion_id or "",
                value_column: metric.count,
                "created_at": now,
                "updated_at": now,
            }
            for metric in metrics
            if metric.metric_date == target_date
            and metric.user_id
            and metric.media_id
            and metric.promotion_id
        ]
        with self._connect() as conn:
            conn.execute(
                sa.text(f"DELETE FROM {table_name} WHERE date = :target_date"),
                {"target_date": target_date},
            )
            if rows:
                stmt = pg_insert(table).on_conflict_do_update(
                    index_elements=["date", "user_id", "media_id", "promotion_id"],
                    set_={
                        value_column: sa.text(f"excluded.{value_column}"),
                        "created_at": sa.text("excluded.created_at"),
                        "updated_at": sa.text("excluded.updated_at"),
                    },
                )
                conn.execute(stmt, rows)
        return len(rows)

    def _purge_targets(
        self,
        targets: dict[str, tuple[str, dict[str, object]]],
        *,
        execute: bool,
    ) -> dict[str, int]:
        counts: dict[str, int] = {}
        for table_name, (where_sql, params) in targets.items():
            if not self._table_exists(table_name):
                counts[table_name] = 0
                continue
            counts[table_name] = (
                self.delete_rows(table_name, where_sql, params)
                if execute
                else self.count_rows(table_name, where_sql, params)
            )
        return counts
