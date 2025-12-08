from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Callable, Dict, Tuple

from ..acs_client import AcsHttpClient
from ..config import resolve_acs_settings, resolve_db_path, resolve_store_raw
from ..ingestion import ClickLogIngestor, ConversionIngestor
from ..job_status import JobStatusStore
from ..repository import SQLiteRepository


class JobConflictError(RuntimeError):
    """Raised when another background job is already running."""


def get_repository() -> SQLiteRepository:
    """Create a repository with required schemas ensured."""
    db_path = resolve_db_path(None)
    repo = SQLiteRepository(db_path)
    repo.ensure_schema(store_raw=resolve_store_raw(None))
    repo.ensure_conversion_schema()
    repo.ensure_master_schema()
    return repo


def get_acs_client() -> AcsHttpClient:
    """Create an ACS HTTP client from environment/settings."""
    settings = resolve_acs_settings()
    return AcsHttpClient(
        base_url=settings.base_url,
        access_key=settings.access_key,
        secret_key=settings.secret_key,
        endpoint_path=settings.log_endpoint,
    )


def get_job_store() -> JobStatusStore:
    """Get persistent job status store."""
    db_path = resolve_db_path(None)
    return JobStatusStore(db_path)


def enqueue_job(
    *,
    background_tasks,
    job_id: str,
    start_message: str,
    run_fn: Callable[[], Tuple[Dict, str]],
) -> None:
    """
    Common background job runner.
    - Ensures only one job runs at a time.
    - Persists start/completion/failure state to SQLite.
    """
    store = get_job_store()
    current = store.get()
    if current.status == "running":
        raise JobConflictError("Another job is already running")

    store.start(job_id, start_message)

    def _runner():
        try:
            result, done_message = run_fn()
            store.complete(job_id, done_message, result)
        except Exception as exc:  # pragma: no cover - defensive guard
            store.fail(job_id, f"{job_id} failed: {exc}", {"success": False, "error": str(exc)})

    background_tasks.add_task(_runner)


def run_click_ingestion(target_date: date) -> Tuple[Dict, str]:
    repo = get_repository()
    client = get_acs_client()
    settings = resolve_acs_settings()
    ingestor = ClickLogIngestor(
        client=client,
        repository=repo,
        page_size=settings.page_size,
        store_raw=True,
    )
    count = ingestor.run_for_date(target_date)
    return {"success": True, "count": count}, f"Ingested {count} clicks for {target_date}"


def run_conversion_ingestion(target_date: date) -> Tuple[Dict, str]:
    repo = get_repository()
    client = get_acs_client()
    settings = resolve_acs_settings()
    ingestor = ConversionIngestor(
        client=client,
        repository=repo,
        page_size=settings.page_size,
    )
    total, enriched = ingestor.run_for_date(target_date)
    message = f"Ingested {total} conversions for {target_date}"
    return {"success": True, "total": total, "enriched": enriched}, message


def run_refresh(hours: int, clicks: bool, conversions: bool) -> Tuple[Dict, str]:
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)

    repo = get_repository()
    client = get_acs_client()
    settings = resolve_acs_settings()

    result = {"success": True, "clicks": None, "conversions": None}

    if clicks:
        click_ingestor = ClickLogIngestor(
            client=client,
            repository=repo,
            page_size=settings.page_size,
            store_raw=True,
        )
        click_new, click_skip = click_ingestor.run_for_time_range(start_time, end_time)
        result["clicks"] = {"new": click_new, "skipped": click_skip}

    if conversions:
        conv_ingestor = ConversionIngestor(
            client=client,
            repository=repo,
            page_size=settings.page_size,
        )
        conv_new, conv_skip, conv_valid = conv_ingestor.run_for_time_range(start_time, end_time)
        result["conversions"] = {"new": conv_new, "skipped": conv_skip, "valid_entry": conv_valid}

    return result, f"Refresh completed for last {hours} hours"


def run_master_sync() -> Tuple[Dict, str]:
    repo = get_repository()
    client = get_acs_client()

    media_list = client.fetch_all_media_master()
    media_count = repo.bulk_upsert_media(media_list)

    promo_list = client.fetch_all_promotion_master()
    promo_count = repo.bulk_upsert_promotions(promo_list)

    user_list = client.fetch_all_user_master()
    user_count = repo.bulk_upsert_users(user_list)

    result = {
        "success": True,
        "media_count": media_count,
        "promotion_count": promo_count,
        "user_count": user_count,
    }
    return result, "Master sync completed"
