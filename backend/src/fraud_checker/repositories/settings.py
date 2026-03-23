from __future__ import annotations

import json
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..db import Base
from ..time_utils import now_local
from .base import RepositoryBase


class SettingsRepository(RepositoryBase):
    def ensure_settings_schema(self) -> None:
        Base.metadata.create_all(self.engine, tables=[Base.metadata.tables["app_settings"]])

    def save_settings(self, settings: dict) -> None:
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

    def get_settings_updated_at(self) -> datetime | None:
        if not self._table_exists("app_settings"):
            return None
        row = self.fetch_one("SELECT MAX(updated_at) AS updated_at FROM app_settings")
        return row["updated_at"] if row else None
