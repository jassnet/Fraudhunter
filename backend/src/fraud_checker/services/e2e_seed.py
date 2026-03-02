from __future__ import annotations

from datetime import date, datetime, timedelta

import sqlalchemy as sa

from ..db import Base
from ..job_status_pg import JobStatusStorePG
from ..repository_pg import PostgresRepository
from . import settings as settings_service
import fraud_checker.db.models  # noqa: F401

TARGET_DATE = date(2026, 1, 21)
PREVIOUS_DATE = date(2026, 1, 20)

RESET_TABLES = (
    "click_raw",
    "conversion_raw",
    "click_ipua_daily",
    "conversion_ipua_daily",
    "master_media",
    "master_promotion",
    "master_user",
    "app_settings",
    "job_status",
)


def _table(name: str) -> sa.Table:
    return Base.metadata.tables[name]


def _ensure_seed_schemas(repo: PostgresRepository) -> None:
    repo.ensure_schema(store_raw=True)
    repo.ensure_conversion_schema()
    repo.ensure_master_schema()
    repo.ensure_settings_schema()
    JobStatusStorePG(repo.database_url).ensure_schema()


def reset_all(repo: PostgresRepository) -> dict:
    _ensure_seed_schemas(repo)
    inspector = sa.inspect(repo.engine)
    deleted: dict[str, int] = {}

    with repo.engine.begin() as conn:
        for table_name in RESET_TABLES:
            if not inspector.has_table(table_name):
                deleted[table_name] = 0
                continue
            result = conn.execute(sa.delete(_table(table_name)))
            deleted[table_name] = int(result.rowcount or 0)

    # Recreate the singleton job status row after cleanup.
    JobStatusStorePG(repo.database_url).ensure_schema()
    settings_service._settings_cache = None

    return {"deleted": deleted}


def seed_baseline(repo: PostgresRepository) -> dict:
    reset_details = reset_all(repo)
    now = datetime(2026, 1, 21, 8, 0, 0)

    click_rows: list[dict] = []
    ua_base = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0."
    )
    for idx in range(55):
        media_id = "media-alpha" if idx == 0 else f"media-{(idx % 4) + 1}"
        program_id = "program-alpha" if idx == 0 else f"program-{(idx % 5) + 1}"
        first_time = datetime(2026, 1, 21, 9, 0, 0) + timedelta(minutes=idx)
        click_rows.append(
            {
                "date": TARGET_DATE,
                "media_id": media_id,
                "program_id": program_id,
                "ipaddress": f"100.64.0.{idx + 1}",
                "useragent": f"{ua_base}{idx} Safari/537.36",
                "click_count": 60,
                "first_time": first_time,
                "last_time": first_time + timedelta(minutes=3),
                "created_at": now,
                "updated_at": now,
            }
        )

    previous_click_rows = [
        {
            "date": PREVIOUS_DATE,
            "media_id": "media-1",
            "program_id": "program-1",
            "ipaddress": "203.0.113.10",
            "useragent": "Mozilla/5.0 Chrome/122.0",
            "click_count": 10,
            "first_time": datetime(2026, 1, 20, 9, 0, 0),
            "last_time": datetime(2026, 1, 20, 9, 10, 0),
            "created_at": now,
            "updated_at": now,
        },
        {
            "date": PREVIOUS_DATE,
            "media_id": "media-2",
            "program_id": "program-2",
            "ipaddress": "203.0.113.11",
            "useragent": "Mozilla/5.0 Safari/605.1.15",
            "click_count": 12,
            "first_time": datetime(2026, 1, 20, 10, 0, 0),
            "last_time": datetime(2026, 1, 20, 10, 8, 0),
            "created_at": now,
            "updated_at": now,
        },
    ]

    conversion_rows = [
        {
            "date": TARGET_DATE,
            "media_id": "media-alpha",
            "program_id": "program-alpha",
            "ipaddress": "100.64.0.1",
            "useragent": f"{ua_base}0 Safari/537.36",
            "conversion_count": 6,
            "first_time": datetime(2026, 1, 21, 11, 0, 0),
            "last_time": datetime(2026, 1, 21, 11, 12, 0),
            "created_at": now,
            "updated_at": now,
        },
        {
            "date": PREVIOUS_DATE,
            "media_id": "media-1",
            "program_id": "program-1",
            "ipaddress": "203.0.113.10",
            "useragent": "Mozilla/5.0 Chrome/122.0",
            "conversion_count": 1,
            "first_time": datetime(2026, 1, 20, 11, 0, 0),
            "last_time": datetime(2026, 1, 20, 11, 0, 0),
            "created_at": now,
            "updated_at": now,
        },
    ]

    conversion_raw_rows = [
        {
            "id": f"conv-alpha-{idx + 1}",
            "cid": f"click-alpha-{idx + 1}",
            "conversion_time": datetime(2026, 1, 21, 11, 0, 0) + timedelta(minutes=idx),
            "click_time": datetime(2026, 1, 21, 10, 58, 0) + timedelta(minutes=idx),
            "media_id": "media-alpha",
            "program_id": "program-alpha",
            "user_id": "affiliate-alpha",
            "postback_ipaddress": None,
            "postback_useragent": None,
            "entry_ipaddress": "100.64.0.1",
            "entry_useragent": f"{ua_base}0 Safari/537.36",
            "click_ipaddress": "100.64.0.1",
            "click_useragent": f"{ua_base}0 Safari/537.36",
            "state": "approved",
            "raw_payload": None,
            "created_at": now,
            "updated_at": now,
        }
        for idx in range(6)
    ]
    conversion_raw_rows.append(
        {
            "id": "conv-prev-1",
            "cid": "click-prev-1",
            "conversion_time": datetime(2026, 1, 20, 11, 0, 0),
            "click_time": datetime(2026, 1, 20, 10, 45, 0),
            "media_id": "media-1",
            "program_id": "program-1",
            "user_id": "affiliate-1",
            "postback_ipaddress": None,
            "postback_useragent": None,
            "entry_ipaddress": "203.0.113.10",
            "entry_useragent": "Mozilla/5.0 Chrome/122.0",
            "click_ipaddress": "203.0.113.10",
            "click_useragent": "Mozilla/5.0 Chrome/122.0",
            "state": "approved",
            "raw_payload": None,
            "created_at": now,
            "updated_at": now,
        }
    )

    user_rows = [
        {"id": "affiliate-alpha", "name": "Affiliate Alpha", "company": "Alpha Inc.", "state": "active", "updated_at": now},
        {"id": "affiliate-1", "name": "Affiliate One", "company": "One LLC", "state": "active", "updated_at": now},
        {"id": "affiliate-2", "name": "Affiliate Two", "company": "Two LLC", "state": "active", "updated_at": now},
        {"id": "affiliate-3", "name": "Affiliate Three", "company": "Three LLC", "state": "active", "updated_at": now},
        {"id": "affiliate-4", "name": "Affiliate Four", "company": "Four LLC", "state": "active", "updated_at": now},
    ]

    media_rows = [
        {"id": "media-alpha", "name": "Media Alpha", "user_id": "affiliate-alpha", "state": "active", "updated_at": now},
        {"id": "media-1", "name": "Media One", "user_id": "affiliate-1", "state": "active", "updated_at": now},
        {"id": "media-2", "name": "Media Two", "user_id": "affiliate-2", "state": "active", "updated_at": now},
        {"id": "media-3", "name": "Media Three", "user_id": "affiliate-3", "state": "active", "updated_at": now},
        {"id": "media-4", "name": "Media Four", "user_id": "affiliate-4", "state": "active", "updated_at": now},
    ]

    promotion_rows = [
        {"id": "program-alpha", "name": "Program Alpha", "state": "active", "updated_at": now},
        {"id": "program-1", "name": "Program One", "state": "active", "updated_at": now},
        {"id": "program-2", "name": "Program Two", "state": "active", "updated_at": now},
        {"id": "program-3", "name": "Program Three", "state": "active", "updated_at": now},
        {"id": "program-4", "name": "Program Four", "state": "active", "updated_at": now},
        {"id": "program-5", "name": "Program Five", "state": "active", "updated_at": now},
    ]

    with repo.engine.begin() as conn:
        conn.execute(sa.insert(_table("master_user")), user_rows)
        conn.execute(sa.insert(_table("master_media")), media_rows)
        conn.execute(sa.insert(_table("master_promotion")), promotion_rows)
        conn.execute(sa.insert(_table("click_ipua_daily")), click_rows + previous_click_rows)
        conn.execute(sa.insert(_table("conversion_ipua_daily")), conversion_rows)
        conn.execute(sa.insert(_table("conversion_raw")), conversion_raw_rows)

    settings_service._settings_cache = None

    return {
        "target_date": TARGET_DATE.isoformat(),
        "previous_date": PREVIOUS_DATE.isoformat(),
        "counts": {
            "click_ipua_daily": len(click_rows) + len(previous_click_rows),
            "conversion_ipua_daily": len(conversion_rows),
            "conversion_raw": len(conversion_raw_rows),
            "master_media": len(media_rows),
            "master_promotion": len(promotion_rows),
            "master_user": len(user_rows),
        },
        "reset": reset_details,
    }
