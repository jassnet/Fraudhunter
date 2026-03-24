from __future__ import annotations

from contextlib import contextmanager

import sqlalchemy as sa

from ..db.session import normalize_database_url
from ..ip_filters import BROWSER_UA_INCLUDES, BOT_UA_MARKERS, DATACENTER_IP_PREFIXES


class RepositoryBase:
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

    def _datacenter_filter_sql(self, prefixes: tuple[str, ...] = DATACENTER_IP_PREFIXES) -> str:
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

    def fetch_all(self, query: str, params: tuple | dict = ()) -> list[dict]:
        sql, bind_params = self._normalize_query(query, params)
        with self._connect() as conn:
            result = conn.execute(sa.text(sql), bind_params)
            return [dict(row) for row in result.mappings().all()]

    def fetch_one(self, query: str, params: tuple | dict = ()) -> dict | None:
        sql, bind_params = self._normalize_query(query, params)
        with self._connect() as conn:
            row = conn.execute(sa.text(sql), bind_params).mappings().first()
            return dict(row) if row else None

    def count_rows(self, table_name: str, where_sql: str = "", params: dict | None = None) -> int:
        where_clause = f" WHERE {where_sql}" if where_sql else ""
        row = self.fetch_one(
            f"SELECT COUNT(*) AS cnt FROM {table_name}{where_clause}",
            params or {},
        )
        return int(row["cnt"] if row else 0)

    def delete_rows(self, table_name: str, where_sql: str = "", params: dict | None = None) -> int:
        where_clause = f" WHERE {where_sql}" if where_sql else ""
        with self._connect() as conn:
            result = conn.execute(
                sa.text(f"DELETE FROM {table_name}{where_clause}"),
                params or {},
            )
        return int(result.rowcount or 0)
