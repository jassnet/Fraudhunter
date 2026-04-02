from __future__ import annotations

from datetime import datetime

import json

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..db import Base
from ..time_utils import now_local
from .base import RepositoryBase


class MasterRepository(RepositoryBase):
    def ensure_master_schema(self) -> None:
        Base.metadata.create_all(
            self.engine,
            tables=[
                Base.metadata.tables["master_media"],
                Base.metadata.tables["master_promotion"],
                Base.metadata.tables["master_user"],
            ],
        )

    def upsert_media(
        self, media_id: str, name: str, user_id: str | None = None, state: str | None = None
    ) -> None:
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

    def upsert_promotion(
        self,
        promotion_id: str,
        name: str,
        state: str | None = None,
        action_double_state: int | None = None,
        action_double_type_json: str | list[str] | None = None,
    ) -> None:
        table = Base.metadata.tables["master_promotion"]
        now = now_local()
        action_double_type_value = (
            json.dumps(action_double_type_json, ensure_ascii=False)
            if isinstance(action_double_type_json, list)
            else action_double_type_json
        )
        stmt = pg_insert(table).values(
            id=promotion_id,
            name=name,
            state=state,
            action_double_state=action_double_state,
            action_double_type_json=action_double_type_value,
            updated_at=now,
        ).on_conflict_do_update(
            index_elements=["id"],
            set_={
                "name": name,
                "state": state,
                "action_double_state": action_double_state,
                "action_double_type_json": action_double_type_value,
                "updated_at": now,
            },
        )
        with self._connect() as conn:
            conn.execute(stmt)

    def upsert_user(
        self, user_id: str, name: str, company: str | None = None, state: str | None = None
    ) -> None:
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

    def bulk_upsert_media(self, media_list: list[dict]) -> int:
        if not media_list:
            return 0
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

    def bulk_upsert_promotions(self, promo_list: list[dict]) -> int:
        if not promo_list:
            return 0
        table = Base.metadata.tables["master_promotion"]
        now = now_local()
        rows = [
            {
                "id": p.get("id"),
                "name": p.get("name", ""),
                "state": p.get("state"),
                "action_double_state": p.get("action_double_state"),
                "action_double_type_json": (
                    json.dumps(p.get("action_double_type_json"), ensure_ascii=False)
                    if isinstance(p.get("action_double_type_json"), list)
                    else p.get("action_double_type_json")
                ),
                "updated_at": now,
            }
            for p in promo_list
        ]
        stmt = pg_insert(table).on_conflict_do_update(
            index_elements=["id"],
            set_={
                "name": sa.text("excluded.name"),
                "state": sa.text("excluded.state"),
                "action_double_state": sa.text("excluded.action_double_state"),
                "action_double_type_json": sa.text("excluded.action_double_type_json"),
                "updated_at": sa.text("excluded.updated_at"),
            },
        )
        with self._connect() as conn:
            conn.execute(stmt, rows)
        return len(rows)

    def bulk_upsert_users(self, user_list: list[dict]) -> int:
        if not user_list:
            return 0
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
