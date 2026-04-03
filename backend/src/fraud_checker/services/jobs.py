from __future__ import annotations

import json
import logging
import os
import socket
import threading
import uuid
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy.exc import IntegrityError

from ..config import resolve_acs_settings
from ..ingestion import ClickLogIngestor, ConversionIngestor
from ..job_status_pg import JobRun, JobStatusStorePG
from ..logging_utils import log_event, log_timed
from ..runtime_guards import current_env
from ..service_dependencies import (
    RuntimeDependencies,
    get_acs_client as default_get_acs_client,
    get_job_store as default_get_job_store,
    get_repository as default_get_repository,
)
from ..time_utils import now_local
from . import findings as findings_service

logger = logging.getLogger(__name__)

JOB_TYPE_CLICK_INGEST = "ingest_clicks"
JOB_TYPE_CONVERSION_INGEST = "ingest_conversions"
JOB_TYPE_REFRESH = "refresh"
JOB_TYPE_RECOMPUTE_FINDINGS_DATE = "recompute_findings_date"
JOB_TYPE_MASTER_SYNC = "master_sync"
DEFAULT_JOB_LEASE_SECONDS = 300
JOB_MAX_ATTEMPTS = {
    JOB_TYPE_CLICK_INGEST: 3,
    JOB_TYPE_CONVERSION_INGEST: 3,
    JOB_TYPE_REFRESH: 4,
    JOB_TYPE_RECOMPUTE_FINDINGS_DATE: 4,
    JOB_TYPE_MASTER_SYNC: 2,
}
JOB_PRIORITIES = {
    JOB_TYPE_CLICK_INGEST: 20,
    JOB_TYPE_CONVERSION_INGEST: 20,
    JOB_TYPE_REFRESH: 10,
    JOB_TYPE_RECOMPUTE_FINDINGS_DATE: 30,
    JOB_TYPE_MASTER_SYNC: 50,
}


class JobConflictError(RuntimeError):
    """Raised when another background job is already queued or running."""


def get_repository():
    return default_get_repository()


def get_job_store():
    return default_get_job_store()


def get_acs_client():
    return default_get_acs_client()


def get_runtime_dependencies() -> RuntimeDependencies:
    return RuntimeDependencies(
        repository_factory=get_repository,
        job_store_factory=get_job_store,
        acs_client_factory=get_acs_client,
        now_provider=now_local,
    )


def _env_truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _deps(deps: RuntimeDependencies | None = None) -> RuntimeDependencies:
    return deps or get_runtime_dependencies()


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


def _date_write_concurrency_key(target_date: date) -> str:
    return f"date-write:{target_date.isoformat()}"


def _job_concurrency_key(job_type: str, params: dict[str, Any] | None) -> str | None:
    params = params or {}
    if job_type in {
        JOB_TYPE_CLICK_INGEST,
        JOB_TYPE_CONVERSION_INGEST,
        JOB_TYPE_RECOMPUTE_FINDINGS_DATE,
    } and params.get("date"):
        return _date_write_concurrency_key(date.fromisoformat(params["date"]))
    if job_type == JOB_TYPE_MASTER_SYNC:
        return "master-sync"
    return None


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
    dedupe_key: str | None = None,
    concurrency_key: str | None = None,
    background_tasks=None,
    deps: RuntimeDependencies | None = None,
) -> JobRun:
    store = _deps(deps).job_store()
    dedupe_key = dedupe_key or _dedupe_key(job_type, params)
    concurrency_key = concurrency_key if concurrency_key is not None else _job_concurrency_key(job_type, params)
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

    try:
        job = store.enqueue(
            job_type=job_type,
            params=params,
            message=start_message,
            max_attempts=_default_max_attempts(job_type),
            dedupe_key=dedupe_key,
            priority=_default_priority(job_type),
            concurrency_key=concurrency_key,
        )
    except IntegrityError:
        duplicate = store.find_active_duplicate(dedupe_key)
        if duplicate is not None:
            log_event(
                logger,
                "job_enqueue_deduplicated_race",
                run_id=duplicate.id,
                job_type=job_type,
                dedupe_key=dedupe_key,
            )
            return duplicate
        raise
    log_event(
        logger,
        "job_enqueued",
        run_id=job.id,
        job_type=job_type,
        params=params,
        dedupe_key=dedupe_key,
        max_attempts=job.max_attempts,
        priority=job.priority,
        concurrency_key=getattr(job, "concurrency_key", concurrency_key),
    )

    if background_tasks is not None and _should_use_in_process_background_kick():
        background_tasks.add_task(process_queued_jobs, 1)

    return job


def process_queued_jobs_after_cli_enqueue(max_jobs: int = 1) -> int:
    """
    Drain the queue in-process when dev-style in-process kick is enabled.

    HTTP enqueue paths use FastAPI BackgroundTasks for the same behavior; CLI enqueue
    commands have no BackgroundTasks, so they call this explicitly.
    """
    if not _should_use_in_process_background_kick():
        return 0
    return process_queued_jobs(max_jobs=max_jobs)


def enqueue_recompute_findings_job(
    target_date: date,
    *,
    generation_id: str,
    trigger: str,
    source_job_id: str | None = None,
    background_tasks=None,
    deps: RuntimeDependencies | None = None,
) -> JobRun:
    params = {
        "date": target_date.isoformat(),
        "generation_id": generation_id,
        "trigger": trigger,
    }
    if source_job_id:
        params["source_job_id"] = source_job_id

    return enqueue_job(
        background_tasks=background_tasks,
        job_type=JOB_TYPE_RECOMPUTE_FINDINGS_DATE,
        params=params,
        start_message=f"\u0066\u0069\u006e\u0064\u0069\u006e\u0067\u0020\u518d\u8a08\u7b97\u30b8\u30e7\u30d6\u3092\u767b\u9332\u3057\u307e\u3057\u305f\uff08{target_date.isoformat()}\uff09",
        deps=deps,
    )


def enqueue_findings_recompute_jobs(
    dates: list[date],
    *,
    generation_id: str,
    trigger: str,
    source_job_id: str | None = None,
    background_tasks=None,
    deps: RuntimeDependencies | None = None,
) -> list[JobRun]:
    jobs: list[JobRun] = []
    for target_date in dates:
        jobs.append(
            enqueue_recompute_findings_job(
                target_date,
                generation_id=generation_id,
                trigger=trigger,
                source_job_id=source_job_id,
                background_tasks=background_tasks,
                deps=deps,
            )
        )
    return jobs


def enqueue_click_ingestion_job(
    target_date: date,
    *,
    background_tasks=None,
    deps: RuntimeDependencies | None = None,
) -> JobRun:
    return enqueue_job(
        background_tasks=background_tasks,
        job_type=JOB_TYPE_CLICK_INGEST,
        params={"date": target_date.isoformat()},
        start_message=f"\u30af\u30ea\u30c3\u30af\u53d6\u308a\u8fbc\u307f\u30b8\u30e7\u30d6\u3092\u767b\u9332\u3057\u307e\u3057\u305f\uff08{target_date.isoformat()}\uff09",
        deps=deps,
    )


def enqueue_conversion_ingestion_job(
    target_date: date,
    *,
    background_tasks=None,
    deps: RuntimeDependencies | None = None,
) -> JobRun:
    return enqueue_job(
        background_tasks=background_tasks,
        job_type=JOB_TYPE_CONVERSION_INGEST,
        params={"date": target_date.isoformat()},
        start_message=f"\u6210\u679c\u53d6\u308a\u8fbc\u307f\u30b8\u30e7\u30d6\u3092\u767b\u9332\u3057\u307e\u3057\u305f\uff08{target_date.isoformat()}\uff09",
        deps=deps,
    )


def enqueue_refresh_job(
    *,
    hours: int,
    clicks: bool,
    conversions: bool,
    detect: bool,
    background_tasks=None,
    deps: RuntimeDependencies | None = None,
) -> JobRun:
    return enqueue_job(
        background_tasks=background_tasks,
        job_type=JOB_TYPE_REFRESH,
        params={
            "hours": hours,
            "clicks": clicks,
            "conversions": conversions,
            "detect": detect,
        },
        start_message=f"\u76f4\u8fd1{hours}\u6642\u9593\u306e\u518d\u53d6\u5f97\u30b8\u30e7\u30d6\u3092\u767b\u9332\u3057\u307e\u3057\u305f",
        deps=deps,
    )


def enqueue_master_sync_job(*, background_tasks=None, deps: RuntimeDependencies | None = None) -> JobRun:
    return enqueue_job(
        background_tasks=background_tasks,
        job_type=JOB_TYPE_MASTER_SYNC,
        params=None,
        start_message="\u30de\u30b9\u30bf\u540c\u671f\u30b8\u30e7\u30d6\u3092\u767b\u9332\u3057\u307e\u3057\u305f",
        deps=deps,
    )


def process_queued_jobs(max_jobs: int = 1, deps: RuntimeDependencies | None = None) -> int:
    runtime = _deps(deps)
    store = runtime.job_store()
    worker_id = _worker_id()
    lease_seconds = _job_lease_seconds()
    processed = 0

    for _ in range(max_jobs):
        run = store.acquire_next(worker_id=worker_id, lease_seconds=lease_seconds)
        if run is None:
            break
        processed += 1
        _execute_job_run(
            store=store,
            run=run,
            worker_id=worker_id,
            lease_seconds=lease_seconds,
            deps=runtime,
        )

    return processed


def _execute_job_run(
    *,
    store: JobStatusStorePG,
    run: JobRun,
    worker_id: str,
    lease_seconds: int,
    deps: RuntimeDependencies | None = None,
) -> None:
    log_event(logger, "job_started", run_id=run.id, job_type=run.job_type, worker_id=worker_id)
    try:
        with store.advisory_lock(run.concurrency_key) as acquired:
            if not acquired:
                store.requeue_blocked(
                    run.id,
                    f"{run.job_type} is waiting for {run.concurrency_key}",
                    delay_seconds=15,
                )
                log_event(
                    logger,
                    "job_requeued_for_concurrency",
                    run_id=run.id,
                    job_type=run.job_type,
                    concurrency_key=run.concurrency_key,
                )
                return

            with _heartbeat(store, run.id, worker_id, lease_seconds), log_timed(
                logger,
                "job_completed",
                run_id=run.id,
                job_type=run.job_type,
            ):
                result, done_message = _dispatch_job_with_optional_deps(run, deps)
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


def _dispatch_job_with_optional_deps(
    run: JobRun,
    deps: RuntimeDependencies | None,
) -> tuple[dict[str, Any], str]:
    if deps is None:
        return _dispatch_job(run)
    try:
        return _dispatch_job(run, deps=deps)
    except TypeError as exc:
        message = str(exc)
        if "unexpected keyword argument 'deps'" not in message:
            raise
        return _dispatch_job(run)


def _dispatch_job(
    run: JobRun,
    *,
    deps: RuntimeDependencies | None = None,
) -> tuple[dict[str, Any], str]:
    runtime = _deps(deps)
    params = run.params or {}
    if run.job_type == JOB_TYPE_CLICK_INGEST:
        return run_click_ingestion(date.fromisoformat(params["date"]), job_run_id=run.id, deps=runtime)
    if run.job_type == JOB_TYPE_CONVERSION_INGEST:
        return run_conversion_ingestion(date.fromisoformat(params["date"]), job_run_id=run.id, deps=runtime)
    if run.job_type == JOB_TYPE_REFRESH:
        return run_refresh(
            hours=int(params["hours"]),
            clicks=bool(params.get("clicks", True)),
            conversions=bool(params.get("conversions", True)),
            detect=bool(params.get("detect", False)),
            job_run_id=run.id,
            deps=runtime,
        )
    if run.job_type == JOB_TYPE_RECOMPUTE_FINDINGS_DATE:
        return run_recompute_findings_for_date(
            date.fromisoformat(params["date"]),
            generation_id=str(params["generation_id"]),
            trigger=str(params.get("trigger") or "job"),
            job_run_id=run.id,
            source_job_id=params.get("source_job_id"),
            deps=runtime,
        )
    if run.job_type == JOB_TYPE_MASTER_SYNC:
        return run_master_sync(job_run_id=run.id, deps=runtime)
    raise ValueError(f"Unsupported job_type: {run.job_type}")


def run_recompute_findings_for_date(
    target_date: date,
    *,
    generation_id: str,
    trigger: str,
    job_run_id: str | None = None,
    source_job_id: str | None = None,
    deps: RuntimeDependencies | None = None,
) -> tuple[dict[str, Any], str]:
    repo = _deps(deps).repository()
    with log_timed(
        logger,
        "recompute_findings_date_job",
        target_date=target_date,
        generation_id=generation_id,
        trigger=trigger,
    ):
        recomputed = findings_service.recompute_findings_for_dates(
            repo,
            [target_date],
            computed_by_job_id=job_run_id,
            generation_id=generation_id,
        )
    return {
        "success": True,
        "target_date": target_date.isoformat(),
        "generation_id": generation_id,
        "trigger": trigger,
        "source_job_id": source_job_id,
        "findings": recomputed.get(target_date.isoformat(), {}),
    }, f"Recomputed findings for {target_date}"


def run_click_ingestion(
    target_date: date,
    *,
    job_run_id: str | None = None,
    deps: RuntimeDependencies | None = None,
) -> tuple[dict[str, Any], str]:
    runtime = _deps(deps)
    repo = runtime.repository()
    client = runtime.acs_client()
    settings = resolve_acs_settings()
    ingestor = ClickLogIngestor(
        client=client,
        repository=repo,
        page_size=settings.page_size,
        store_raw=True,
    )
    with log_timed(logger, "click_ingestion", target_date=target_date):
        count = ingestor.run_for_date(target_date)
        _ingest_fraud_support_for_date(repo, client, target_date, page_size=settings.page_size)
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
    deps: RuntimeDependencies | None = None,
) -> tuple[dict[str, Any], str]:
    runtime = _deps(deps)
    repo = runtime.repository()
    client = runtime.acs_client()
    settings = resolve_acs_settings()
    ingestor = ConversionIngestor(
        client=client,
        repository=repo,
        page_size=settings.page_size,
    )
    with log_timed(logger, "conversion_ingestion", target_date=target_date):
        total, enriched, click_enriched = ingestor.run_for_date(target_date)
        _ingest_fraud_support_for_date(repo, client, target_date, page_size=settings.page_size)
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
    deps: RuntimeDependencies | None = None,
) -> tuple[dict[str, Any], str]:
    runtime = _deps(deps)
    end_time = runtime.now()
    start_time = end_time - timedelta(hours=hours)

    repo = runtime.repository()
    client = runtime.acs_client()
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

        for target_date in sorted(dates_to_recompute):
            _ingest_fraud_support_for_date(repo, client, target_date, page_size=settings.page_size)

        if dates_to_recompute:
            generation_id = f"refresh-{job_run_id or uuid.uuid4().hex[:12]}"
            recompute_jobs = enqueue_findings_recompute_jobs(
                sorted(dates_to_recompute),
                generation_id=generation_id,
                trigger="refresh",
                source_job_id=job_run_id,
                deps=runtime,
            )
            result["findings_recompute"] = {
                "mode": "queued",
                "generation_id": generation_id,
                "job_ids": [job.id for job in recompute_jobs],
                "target_dates": [target_date.isoformat() for target_date in sorted(dates_to_recompute)],
                "detect_requested": detect,
            }

    return result, f"Refresh completed for last {hours} hours"


def _ingest_fraud_support_for_date(repo, client, target_date: date, *, page_size: int) -> dict[str, int]:
    repo.ensure_fraud_schema()
    checks = _fetch_paged(lambda page: client.fetch_check_logs(target_date, page, page_size), page_size)
    tracks = _fetch_paged(lambda page: client.fetch_track_logs(target_date, page, page_size), page_size)
    click_metrics = _fetch_paged(lambda page: client.fetch_click_metrics(target_date, page, page_size), page_size)
    access_metrics = _fetch_paged(lambda page: client.fetch_access_metrics(target_date, page, page_size), page_size)
    imp_metrics = _fetch_paged(lambda page: client.fetch_imp_metrics(target_date, page, page_size), page_size)
    return {
        "checks": repo.replace_check_logs(target_date, checks),
        "tracks": repo.replace_track_logs(target_date, tracks),
        "click_metrics": repo.replace_entity_daily_metrics(
            target_date,
            click_metrics,
            table_name="click_sum_daily",
            value_column="click_count",
        ),
        "access_metrics": repo.replace_entity_daily_metrics(
            target_date,
            access_metrics,
            table_name="access_sum_daily",
            value_column="access_count",
        ),
        "imp_metrics": repo.replace_entity_daily_metrics(
            target_date,
            imp_metrics,
            table_name="imp_sum_daily",
            value_column="imp_count",
        ),
    }


def _fetch_paged(fetch_page, page_size: int):
    rows = []
    page = 1
    while True:
        batch = list(fetch_page(page))
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < page_size:
            break
        page += 1
    return rows


def run_master_sync(
    *,
    job_run_id: str | None = None,
    deps: RuntimeDependencies | None = None,
) -> tuple[dict[str, Any], str]:
    runtime = _deps(deps)
    repo = runtime.repository()
    client = runtime.acs_client()
    repo.ensure_master_schema()

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

    from . import reporting as reporting_service

    dates = [date.fromisoformat(value) for value in reporting_service.get_available_dates(repo) if value]
    if dates:
        generation_id = f"master-sync-{job_run_id or uuid.uuid4().hex[:12]}"
        recompute_jobs = enqueue_findings_recompute_jobs(
            dates,
            generation_id=generation_id,
            trigger="master_sync",
            source_job_id=job_run_id,
            deps=runtime,
        )
        result["findings_recompute"] = {
            "mode": "queued",
            "generation_id": generation_id,
            "job_ids": [job.id for job in recompute_jobs],
            "target_dates": [target_date.isoformat() for target_date in dates],
        }

    return result, "Master sync completed"
