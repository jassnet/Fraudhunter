from __future__ import annotations

import json
import logging
import os
import socket
import threading
from contextlib import contextmanager
from datetime import date, timedelta
from typing import Any

from ..acs_client import AcsHttpClient
from ..config import resolve_acs_settings, resolve_store_raw
from ..ingestion import ClickLogIngestor, ConversionIngestor
from ..job_status_pg import JobRun, JobStatusStorePG
from ..logging_utils import log_event, log_timed
from ..repository_pg import PostgresRepository
from ..runtime_guards import current_env
from ..suspicious import CombinedSuspiciousDetector
from ..time_utils import now_local
from . import findings as findings_service
from . import settings as settings_service

logger = logging.getLogger(__name__)

JOB_TYPE_CLICK_INGEST = "ingest_clicks"
JOB_TYPE_CONVERSION_INGEST = "ingest_conversions"
JOB_TYPE_REFRESH = "refresh"
JOB_TYPE_MASTER_SYNC = "master_sync"
DEFAULT_JOB_LEASE_SECONDS = 300
JOB_MAX_ATTEMPTS = {
    JOB_TYPE_CLICK_INGEST: 3,
    JOB_TYPE_CONVERSION_INGEST: 3,
    JOB_TYPE_REFRESH: 4,
    JOB_TYPE_MASTER_SYNC: 2,
}
JOB_PRIORITIES = {
    JOB_TYPE_CLICK_INGEST: 20,
    JOB_TYPE_CONVERSION_INGEST: 20,
    JOB_TYPE_REFRESH: 10,
    JOB_TYPE_MASTER_SYNC: 50,
}


class JobConflictError(RuntimeError):
    """Raised when another background job is already queued or running."""


def _env_truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _require_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for Postgres mode.")
    return database_url


def get_repository() -> PostgresRepository:
    database_url = _require_database_url()
    return PostgresRepository(database_url)


def get_acs_client() -> AcsHttpClient:
    settings = resolve_acs_settings()
    return AcsHttpClient(
        base_url=settings.base_url,
        access_key=settings.access_key,
        secret_key=settings.secret_key,
        endpoint_path=settings.log_endpoint,
    )


def get_job_store() -> JobStatusStorePG:
    return JobStatusStorePG(_require_database_url())


def _job_lease_seconds() -> int:
    raw = os.getenv("FC_JOB_LEASE_SECONDS", str(DEFAULT_JOB_LEASE_SECONDS))
    try:
        return max(30, int(raw))
    except ValueError:
        return DEFAULT_JOB_LEASE_SECONDS


def _worker_id() -> str:
    return f"{socket.gethostname()}:{os.getpid()}"


def _default_max_attempts(job_type: str) -> int:
    return JOB_MAX_ATTEMPTS.get(job_type, 3)


def _default_priority(job_type: str) -> int:
    return JOB_PRIORITIES.get(job_type, 100)


def _dedupe_key(job_type: str, params: dict[str, Any] | None) -> str:
    canonical_params = json.dumps(params or {}, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return f"{job_type}:{canonical_params}"


def _should_use_in_process_background_kick() -> bool:
    override = os.getenv("FC_ENABLE_IN_PROCESS_JOB_KICK")
    if override is not None:
        return _env_truthy("FC_ENABLE_IN_PROCESS_JOB_KICK")
    return current_env() not in {"prod", "production"}


def _is_retryable_job_error(exc: Exception) -> bool:
    return not isinstance(exc, ValueError)


@contextmanager
def _heartbeat(store: JobStatusStorePG, run_id: str, worker_id: str, lease_seconds: int):
    stop_event = threading.Event()
    interval = max(10, lease_seconds // 3)

    def _beat() -> None:
        while not stop_event.wait(interval):
            store.heartbeat(run_id=run_id, worker_id=worker_id, lease_seconds=lease_seconds)

    thread = threading.Thread(target=_beat, name=f"job-heartbeat-{run_id}", daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop_event.set()
        thread.join(timeout=1)


def enqueue_job(
    *,
    job_type: str,
    params: dict[str, Any] | None,
    start_message: str,
    background_tasks=None,
) -> JobRun:
    store = get_job_store()
    dedupe_key = _dedupe_key(job_type, params)
    duplicate = store.find_active_duplicate(dedupe_key)
    if duplicate is not None:
        log_event(
            logger,
            "job_enqueue_deduplicated",
            run_id=duplicate.id,
            job_type=job_type,
            dedupe_key=dedupe_key,
        )
        return duplicate

    if store.has_active_job():
        raise JobConflictError("Another job is already running")

    job = store.enqueue(
        job_type=job_type,
        params=params,
        message=start_message,
        max_attempts=_default_max_attempts(job_type),
        dedupe_key=dedupe_key,
        priority=_default_priority(job_type),
    )
    log_event(
        logger,
        "job_enqueued",
        run_id=job.id,
        job_type=job_type,
        params=params,
        dedupe_key=dedupe_key,
        max_attempts=job.max_attempts,
        priority=job.priority,
    )

    if background_tasks is not None and _should_use_in_process_background_kick():
        background_tasks.add_task(process_queued_jobs, 1)

    return job


def process_queued_jobs(max_jobs: int = 1) -> int:
    store = get_job_store()
    worker_id = _worker_id()
    lease_seconds = _job_lease_seconds()
    processed = 0

    for _ in range(max_jobs):
        run = store.acquire_next(worker_id=worker_id, lease_seconds=lease_seconds)
        if run is None:
            break
        processed += 1
        _execute_job_run(store=store, run=run, worker_id=worker_id, lease_seconds=lease_seconds)

    return processed


def _execute_job_run(
    *,
    store: JobStatusStorePG,
    run: JobRun,
    worker_id: str,
    lease_seconds: int,
) -> None:
    log_event(logger, "job_started", run_id=run.id, job_type=run.job_type, worker_id=worker_id)
    try:
        with _heartbeat(store, run.id, worker_id, lease_seconds), log_timed(
            logger,
            "job_completed",
            run_id=run.id,
            job_type=run.job_type,
        ):
            result, done_message = _dispatch_job(run)
            store.complete(run.id, done_message, result)
    except Exception as exc:
        message = f"{run.job_type} failed: {exc}"
        next_status = store.fail(
            run.id,
            message,
            {"success": False, "error": str(exc)},
            error_message=str(exc),
            retryable=_is_retryable_job_error(exc),
        )
        log_event(
            logger,
            "job_failed",
            run_id=run.id,
            job_type=run.job_type,
            next_status=next_status,
            retryable=next_status == "queued",
        )
        logger.exception("Job execution failed", extra={"run_id": run.id, "job_type": run.job_type})


def _dispatch_job(run: JobRun) -> tuple[dict[str, Any], str]:
    params = run.params or {}
    if run.job_type == JOB_TYPE_CLICK_INGEST:
        return run_click_ingestion(date.fromisoformat(params["date"]), job_run_id=run.id)
    if run.job_type == JOB_TYPE_CONVERSION_INGEST:
        return run_conversion_ingestion(date.fromisoformat(params["date"]), job_run_id=run.id)
    if run.job_type == JOB_TYPE_REFRESH:
        return run_refresh(
            hours=int(params["hours"]),
            clicks=bool(params.get("clicks", True)),
            conversions=bool(params.get("conversions", True)),
            detect=bool(params.get("detect", False)),
            job_run_id=run.id,
        )
    if run.job_type == JOB_TYPE_MASTER_SYNC:
        return run_master_sync()
    raise ValueError(f"Unsupported job_type: {run.job_type}")


def run_click_ingestion(target_date: date, *, job_run_id: str | None = None) -> tuple[dict[str, Any], str]:
    repo = get_repository()
    client = get_acs_client()
    settings = resolve_acs_settings()
    ingestor = ClickLogIngestor(
        client=client,
        repository=repo,
        page_size=settings.page_size,
        store_raw=True,
    )
    with log_timed(logger, "click_ingestion", target_date=target_date):
        count = ingestor.run_for_date(target_date)
        finding_counts = findings_service.recompute_findings_for_dates(
            repo,
            [target_date],
            computed_by_job_id=job_run_id,
            generation_id=job_run_id,
        )
    return {
        "success": True,
        "count": count,
        "findings": finding_counts.get(target_date.isoformat(), {}),
    }, f"Ingested {count} clicks for {target_date}"


def run_conversion_ingestion(
    target_date: date,
    *,
    job_run_id: str | None = None,
) -> tuple[dict[str, Any], str]:
    repo = get_repository()
    client = get_acs_client()
    settings = resolve_acs_settings()
    ingestor = ConversionIngestor(
        client=client,
        repository=repo,
        page_size=settings.page_size,
    )
    with log_timed(logger, "conversion_ingestion", target_date=target_date):
        total, enriched, click_enriched = ingestor.run_for_date(target_date)
        finding_counts = findings_service.recompute_findings_for_dates(
            repo,
            [target_date],
            computed_by_job_id=job_run_id,
            generation_id=job_run_id,
        )
    message = f"Ingested {total} conversions for {target_date}"
    return {
        "success": True,
        "total": total,
        "enriched": enriched,
        "click_enriched": click_enriched,
        "findings": finding_counts.get(target_date.isoformat(), {}),
    }, message


def run_refresh(
    hours: int,
    clicks: bool,
    conversions: bool,
    detect: bool,
    *,
    job_run_id: str | None = None,
) -> tuple[dict[str, Any], str]:
    end_time = now_local()
    start_time = end_time - timedelta(hours=hours)

    repo = get_repository()
    client = get_acs_client()
    settings = resolve_acs_settings()

    result: dict[str, Any] = {"success": True, "clicks": None, "conversions": None}
    with log_timed(
        logger,
        "refresh_job",
        hours=hours,
        clicks=clicks,
        conversions=conversions,
        detect=detect,
    ):
        dates_to_recompute: set[date] = set()

        if clicks:
            click_ingestor = ClickLogIngestor(
                client=client,
                repository=repo,
                page_size=settings.page_size,
                store_raw=True,
            )
            click_new, click_skip = click_ingestor.run_for_time_range(start_time, end_time)
            result["clicks"] = {"new": click_new, "skipped": click_skip}
            current = start_time.date()
            while current <= end_time.date():
                dates_to_recompute.add(current)
                current += timedelta(days=1)

        if conversions:
            conv_ingestor = ConversionIngestor(
                client=client,
                repository=repo,
                page_size=settings.page_size,
            )
            conv_new, conv_skip, conv_valid, click_enriched = conv_ingestor.run_for_time_range(
                start_time, end_time
            )
            result["conversions"] = {
                "new": conv_new,
                "skipped": conv_skip,
                "valid_entry": conv_valid,
                "click_enriched": click_enriched,
            }
            current = start_time.date()
            while current <= end_time.date():
                dates_to_recompute.add(current)
                current += timedelta(days=1)

        if dates_to_recompute:
            persisted_results = findings_service.recompute_findings_for_dates(
                repo,
                sorted(dates_to_recompute),
                computed_by_job_id=job_run_id,
                generation_id=job_run_id,
            )
            if detect:
                click_rules, conv_rules = settings_service.build_rule_sets(repo)
                detect_results: dict[str, dict[str, int]] = {}
                for target_date in sorted(dates_to_recompute):
                    combined = CombinedSuspiciousDetector(
                        repository=repo,
                        click_rules=click_rules,
                        conversion_rules=conv_rules,
                    )
                    _, _, high_risk = combined.find_for_date(target_date)
                    base = persisted_results.get(target_date.isoformat(), {})
                    detect_results[target_date.isoformat()] = {
                        "suspicious_clicks": int(base.get("suspicious_clicks", 0)),
                        "suspicious_conversions": int(base.get("suspicious_conversions", 0)),
                        "high_risk": len(high_risk),
                    }
                result["detect"] = detect_results

    return result, f"Refresh completed for last {hours} hours"


def run_master_sync() -> tuple[dict[str, Any], str]:
    repo = get_repository()
    client = get_acs_client()

    with log_timed(logger, "master_sync"):
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
