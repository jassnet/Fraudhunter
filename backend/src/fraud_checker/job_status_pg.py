from __future__ import annotations

import json
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from .db import Base
from .db.session import normalize_database_url
import fraud_checker.db.models  # noqa: F401
from .time_utils import now_local

JOB_RUN_STATUSES = {"queued", "running", "succeeded", "failed", "cancelled"}
JOB_RUN_ACTIVE_STATUSES = {"queued", "running"}
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_PRIORITY = 100
DEFAULT_RETRY_BASE_SECONDS = 30
MAX_RETRY_BACKOFF_SECONDS = 900


@dataclass
class JobStatus:
    status: str
    job_id: str | None
    message: str | None
    started_at: str | datetime | None
    completed_at: str | datetime | None
    result: dict[str, Any] | None
    queue: dict[str, Any] | None = None


@dataclass
class JobRun:
    id: str
    job_type: str
    status: str
    params: dict[str, Any] | None
    result: dict[str, Any] | None
    error_message: str | None
    message: str | None
    attempt_count: int
    max_attempts: int
    next_retry_at: datetime | None
    dedupe_key: str | None
    priority: int
    queued_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    heartbeat_at: datetime | None
    locked_until: datetime | None
    worker_id: str | None
    concurrency_key: str | None = None


class JobStatusStorePG:
    def __init__(self, database_url: str):
        self.database_url = normalize_database_url(database_url)
        self.engine = sa.create_engine(self.database_url, pool_pre_ping=True)

    def ensure_schema(self) -> None:
        Base.metadata.create_all(self.engine, tables=[Base.metadata.tables["job_runs"]])

    def _loads(self, value: str | None) -> dict[str, Any] | None:
        if not value:
            return None
        return json.loads(value)

    def _dumps(self, value: dict[str, Any] | None) -> str | None:
        if value is None:
            return None
        return json.dumps(value, ensure_ascii=False)

    def _to_run(self, row) -> JobRun:
        return JobRun(
            id=row["id"],
            job_type=row["job_type"],
            status=row["status"],
            params=self._loads(row.get("params_json")),
            result=self._loads(row.get("result_json")),
            error_message=row.get("error_message"),
            message=row.get("message"),
            attempt_count=int(row.get("attempt_count") or 0),
            max_attempts=int(row.get("max_attempts") or 1),
            next_retry_at=row.get("next_retry_at"),
            dedupe_key=row.get("dedupe_key"),
            priority=int(row.get("priority") or DEFAULT_PRIORITY),
            concurrency_key=row.get("concurrency_key"),
            queued_at=row["queued_at"],
            started_at=row.get("started_at"),
            finished_at=row.get("finished_at"),
            heartbeat_at=row.get("heartbeat_at"),
            locked_until=row.get("locked_until"),
            worker_id=row.get("worker_id"),
        )

    def _fetch_latest_run(self) -> JobRun | None:
        with self.engine.begin() as conn:
            row = conn.execute(
                sa.text(
                    """
                    SELECT id, job_type, status, params_json, result_json, error_message, message,
                           attempt_count, max_attempts, next_retry_at, dedupe_key, priority, concurrency_key,
                           queued_at, started_at, finished_at, heartbeat_at, locked_until, worker_id
                    FROM job_runs
                    ORDER BY COALESCE(finished_at, started_at, queued_at) DESC, queued_at DESC
                    LIMIT 1
                    """
                )
            ).mappings().first()
        return self._to_run(row) if row else None

    def get_by_id(self, run_id: str) -> JobRun | None:
        with self.engine.begin() as conn:
            row = conn.execute(
                sa.text(
                    """
                    SELECT id, job_type, status, params_json, result_json, error_message, message,
                           attempt_count, max_attempts, next_retry_at, dedupe_key, priority, concurrency_key,
                           queued_at, started_at, finished_at, heartbeat_at, locked_until, worker_id
                    FROM job_runs
                    WHERE id = :run_id
                    """
                ),
                {"run_id": run_id},
            ).mappings().first()
        return self._to_run(row) if row else None

    def find_active_duplicate(self, dedupe_key: str) -> JobRun | None:
        with self.engine.begin() as conn:
            row = conn.execute(
                sa.text(
                    """
                    SELECT id, job_type, status, params_json, result_json, error_message, message,
                           attempt_count, max_attempts, next_retry_at, dedupe_key, priority, concurrency_key,
                           queued_at, started_at, finished_at, heartbeat_at, locked_until, worker_id
                    FROM job_runs
                    WHERE dedupe_key = :dedupe_key
                      AND status IN ('queued', 'running')
                    ORDER BY queued_at DESC
                    LIMIT 1
                    """
                ),
                {"dedupe_key": dedupe_key},
            ).mappings().first()
        return self._to_run(row) if row else None

    def has_active_job(self) -> bool:
        now = now_local()
        with self.engine.begin() as conn:
            count = conn.execute(
                sa.text(
                    """
                    SELECT COUNT(*)
                    FROM job_runs
                    WHERE (status = 'queued' AND (next_retry_at IS NULL OR next_retry_at <= :now))
                       OR (status = 'running' AND (locked_until IS NULL OR locked_until >= :now))
                    """
                ),
                {"now": now},
            ).scalar_one()
        return bool(count)

    def enqueue(
        self,
        *,
        job_type: str,
        params: dict[str, Any] | None,
        message: str | None,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        dedupe_key: str | None = None,
        priority: int = DEFAULT_PRIORITY,
        concurrency_key: str | None = None,
    ) -> JobRun:
        queued_at = now_local()
        run_id = uuid.uuid4().hex
        try:
            with self.engine.begin() as conn:
                conn.execute(
                    sa.text(
                        """
                        INSERT INTO job_runs (
                            id, job_type, status, params_json, message,
                            attempt_count, max_attempts, next_retry_at, dedupe_key, priority, concurrency_key, queued_at
                        ) VALUES (
                            :id, :job_type, 'queued', :params_json, :message,
                            0, :max_attempts, NULL, :dedupe_key, :priority, :concurrency_key, :queued_at
                        )
                        """
                    ),
                    {
                        "id": run_id,
                        "job_type": job_type,
                        "params_json": self._dumps(params),
                        "message": message,
                        "max_attempts": max(1, int(max_attempts)),
                        "dedupe_key": dedupe_key,
                        "priority": priority,
                        "concurrency_key": concurrency_key,
                        "queued_at": queued_at,
                    },
                )
        except IntegrityError:
            raise
        return JobRun(
            id=run_id,
            job_type=job_type,
            status="queued",
            params=params,
            result=None,
            error_message=None,
            message=message,
            attempt_count=0,
            max_attempts=max(1, int(max_attempts)),
            next_retry_at=None,
            dedupe_key=dedupe_key,
            priority=priority,
            concurrency_key=concurrency_key,
            queued_at=queued_at,
            started_at=None,
            finished_at=None,
            heartbeat_at=None,
            locked_until=None,
            worker_id=None,
        )

    def recover_stale_runs(self) -> int:
        now = now_local()
        with self.engine.begin() as conn:
            result = conn.execute(
                sa.text(
                    """
                    UPDATE job_runs
                    SET status = 'queued',
                        message = COALESCE(message, job_type) || ' (lease recovered)',
                        worker_id = NULL,
                        locked_until = NULL,
                        next_retry_at = COALESCE(next_retry_at, :now)
                    WHERE status = 'running'
                      AND locked_until IS NOT NULL
                      AND locked_until < :now
                    """
                ),
                {"now": now},
            )
        return int(result.rowcount or 0)

    def acquire_next(self, *, worker_id: str, lease_seconds: int) -> JobRun | None:
        self.recover_stale_runs()
        now = now_local()
        locked_until = now + timedelta(seconds=lease_seconds)
        with self.engine.begin() as conn:
            row = conn.execute(
                sa.text(
                    """
                    WITH candidate AS (
                        SELECT id
                        FROM job_runs
                        WHERE status = 'queued'
                          AND (next_retry_at IS NULL OR next_retry_at <= :now)
                        ORDER BY priority ASC, queued_at ASC
                        LIMIT 1
                        FOR UPDATE SKIP LOCKED
                    )
                    UPDATE job_runs
                    SET status = 'running',
                        started_at = COALESCE(started_at, :now),
                        heartbeat_at = :now,
                        locked_until = :locked_until,
                        worker_id = :worker_id
                    WHERE id IN (SELECT id FROM candidate)
                    RETURNING id, job_type, status, params_json, result_json, error_message, message,
                              attempt_count, max_attempts, next_retry_at, dedupe_key, priority, concurrency_key,
                              queued_at, started_at, finished_at, heartbeat_at, locked_until, worker_id
                    """
                ),
                {"now": now, "locked_until": locked_until, "worker_id": worker_id},
            ).mappings().first()
        return self._to_run(row) if row else None

    def heartbeat(self, *, run_id: str, worker_id: str, lease_seconds: int) -> bool:
        now = now_local()
        with self.engine.begin() as conn:
            result = conn.execute(
                sa.text(
                    """
                    UPDATE job_runs
                    SET heartbeat_at = :now,
                        locked_until = :locked_until
                    WHERE id = :run_id
                      AND status = 'running'
                      AND worker_id = :worker_id
                    """
                ),
                {
                    "run_id": run_id,
                    "worker_id": worker_id,
                    "now": now,
                    "locked_until": now + timedelta(seconds=lease_seconds),
                },
            )
        return result.rowcount == 1

    def requeue_blocked(self, run_id: str, message: str, *, delay_seconds: int = 15) -> None:
        retry_at = now_local() + timedelta(seconds=max(1, int(delay_seconds)))
        with self.engine.begin() as conn:
            conn.execute(
                sa.text(
                    """
                    UPDATE job_runs
                    SET status = 'queued',
                        message = :message,
                        worker_id = NULL,
                        locked_until = NULL,
                        heartbeat_at = :retry_at,
                        next_retry_at = :retry_at
                    WHERE id = :run_id
                    """
                ),
                {"run_id": run_id, "message": message, "retry_at": retry_at},
            )

    def complete(self, run_id: str, message: str, result: dict[str, Any] | None = None) -> None:
        finished_at = now_local()
        with self.engine.begin() as conn:
            conn.execute(
                sa.text(
                    """
                    UPDATE job_runs
                    SET status = 'succeeded',
                        message = :message,
                        result_json = :result_json,
                        error_message = NULL,
                        finished_at = :finished_at,
                        heartbeat_at = :finished_at,
                        locked_until = NULL,
                        next_retry_at = NULL
                    WHERE id = :run_id
                    """
                ),
                {
                    "run_id": run_id,
                    "message": message,
                    "result_json": self._dumps(result),
                    "finished_at": finished_at,
                },
            )

    def fail(
        self,
        run_id: str,
        message: str,
        result: dict[str, Any] | None = None,
        *,
        error_message: str | None = None,
        retryable: bool = True,
        backoff_seconds: int | None = None,
    ) -> str:
        finished_at = now_local()
        attempt_state = self._get_attempt_state(run_id)
        next_attempt = attempt_state["attempt_count"] + 1
        max_attempts = max(1, attempt_state["max_attempts"])
        should_retry = retryable and next_attempt < max_attempts
        next_retry_at = (
            finished_at + timedelta(seconds=backoff_seconds or self._retry_backoff_seconds(next_attempt))
            if should_retry
            else None
        )
        next_status = "queued" if should_retry else "failed"
        terminal_finished_at = None if should_retry else finished_at

        with self.engine.begin() as conn:
            conn.execute(
                sa.text(
                    """
                    UPDATE job_runs
                    SET status = :status,
                        message = :message,
                        result_json = :result_json,
                        error_message = :error_message,
                        attempt_count = :attempt_count,
                        finished_at = :finished_at,
                        heartbeat_at = :heartbeat_at,
                        locked_until = NULL,
                        worker_id = NULL,
                        next_retry_at = :next_retry_at
                    WHERE id = :run_id
                    """
                ),
                {
                    "run_id": run_id,
                    "status": next_status,
                    "message": message,
                    "result_json": self._dumps(result),
                    "error_message": error_message,
                    "attempt_count": next_attempt,
                    "finished_at": terminal_finished_at,
                    "heartbeat_at": finished_at,
                    "next_retry_at": next_retry_at,
                },
            )
        return next_status

    def cancel(self, run_id: str, message: str) -> None:
        finished_at = now_local()
        with self.engine.begin() as conn:
            conn.execute(
                sa.text(
                    """
                    UPDATE job_runs
                    SET status = 'cancelled',
                        message = :message,
                        finished_at = :finished_at,
                        heartbeat_at = :finished_at,
                        locked_until = NULL,
                        next_retry_at = NULL
                    WHERE id = :run_id
                    """
                ),
                {"run_id": run_id, "message": message, "finished_at": finished_at},
            )

    def get_latest_successful_finished_at(self, job_types: list[str]) -> datetime | None:
        if not job_types:
            return None
        placeholders = ", ".join([f":job_type_{idx}" for idx in range(len(job_types))])
        params = {f"job_type_{idx}": job_type for idx, job_type in enumerate(job_types)}
        with self.engine.begin() as conn:
            value = conn.execute(
                sa.text(
                    f"""
                    SELECT MAX(finished_at)
                    FROM job_runs
                    WHERE status = 'succeeded'
                      AND job_type IN ({placeholders})
                    """
                ),
                params,
            ).scalar_one()
        return value

    def purge_finished_runs_before(self, cutoff: datetime, *, execute: bool) -> int:
        params = {"cutoff": cutoff}
        where_sql = (
            "status IN ('succeeded', 'failed', 'cancelled') "
            "AND finished_at IS NOT NULL "
            "AND finished_at < :cutoff"
        )
        if execute:
            with self.engine.begin() as conn:
                result = conn.execute(
                    sa.text(f"DELETE FROM job_runs WHERE {where_sql}"),
                    params,
                )
            return int(result.rowcount or 0)
        with self.engine.begin() as conn:
            count = conn.execute(
                sa.text(f"SELECT COUNT(*) FROM job_runs WHERE {where_sql}"),
                params,
            ).scalar_one()
        return int(count)

    def get_queue_metrics(self) -> dict[str, Any]:
        now = now_local()
        with self.engine.begin() as conn:
            row = conn.execute(
                sa.text(
                    """
                    SELECT
                        COUNT(*) FILTER (WHERE status = 'queued') AS queued_jobs_count,
                        COUNT(*) FILTER (
                            WHERE status = 'queued'
                              AND next_retry_at IS NOT NULL
                              AND next_retry_at > :now
                        ) AS retry_scheduled_jobs_count,
                        COUNT(*) FILTER (
                            WHERE status = 'running'
                              AND (locked_until IS NULL OR locked_until >= :now)
                        ) AS running_jobs_count,
                        COUNT(*) FILTER (WHERE status = 'failed') AS failed_jobs_count,
                        MIN(queued_at) FILTER (WHERE status = 'queued') AS oldest_queued_at
                    FROM job_runs
                    """
                ),
                {"now": now},
            ).mappings().one()
        oldest_queued_at = row["oldest_queued_at"]
        oldest_queued_age_seconds = None
        if oldest_queued_at is not None:
            oldest_queued_age_seconds = int((now - oldest_queued_at).total_seconds())
        return {
            "queued_jobs_count": int(row["queued_jobs_count"] or 0),
            "retry_scheduled_jobs_count": int(row["retry_scheduled_jobs_count"] or 0),
            "running_jobs_count": int(row["running_jobs_count"] or 0),
            "failed_jobs_count": int(row["failed_jobs_count"] or 0),
            "oldest_queued_at": oldest_queued_at,
            "oldest_queued_age_seconds": oldest_queued_age_seconds,
        }

    def get_latest_run(self) -> JobRun | None:
        return self._fetch_latest_run()

    @contextmanager
    def advisory_lock(self, concurrency_key: str | None):
        if not concurrency_key:
            yield True
            return

        conn = self.engine.connect()
        acquired = False
        try:
            acquired = bool(
                conn.execute(
                    sa.text("SELECT pg_try_advisory_lock(hashtext(:concurrency_key))"),
                    {"concurrency_key": concurrency_key},
                ).scalar_one()
            )
            yield acquired
        finally:
            if acquired:
                conn.execute(
                    sa.text("SELECT pg_advisory_unlock(hashtext(:concurrency_key))"),
                    {"concurrency_key": concurrency_key},
                )
            conn.close()

    def get(self) -> JobStatus:
        run = self._fetch_latest_run()
        queue = self._serialize_queue_metrics(self.get_queue_metrics())
        if not run:
            return JobStatus(
                status="idle",
                job_id=None,
                message="まだジョブは実行されていません",
                started_at=None,
                completed_at=None,
                result=None,
                queue=queue,
            )

        if run.status == "queued":
            status = "running"
            message = run.message or "ジョブを実行待ちに登録しました"
        elif run.status == "succeeded":
            status = "completed"
            message = run.message
        else:
            status = run.status
            message = run.message

        return JobStatus(
            status=status,
            job_id=run.id,
            message=message,
            started_at=run.started_at,
            completed_at=run.finished_at,
            result=run.result,
            queue=queue,
        )

    def _get_attempt_state(self, run_id: str) -> dict[str, int]:
        with self.engine.begin() as conn:
            row = conn.execute(
                sa.text(
                    """
                    SELECT attempt_count, max_attempts
                    FROM job_runs
                    WHERE id = :run_id
                    """
                ),
                {"run_id": run_id},
            ).mappings().first()
        if row is None:
            raise RuntimeError(f"Unknown job run: {run_id}")
        return {
            "attempt_count": int(row.get("attempt_count") or 0),
            "max_attempts": int(row.get("max_attempts") or 1),
        }

    def _retry_backoff_seconds(self, next_attempt: int) -> int:
        seconds = DEFAULT_RETRY_BASE_SECONDS * (2 ** max(0, next_attempt - 1))
        return min(MAX_RETRY_BACKOFF_SECONDS, seconds)

    def _serialize_queue_metrics(self, metrics: dict[str, Any]) -> dict[str, Any]:
        serialized = dict(metrics)
        if isinstance(serialized.get("oldest_queued_at"), datetime):
            serialized["oldest_queued_at"] = serialized["oldest_queued_at"].isoformat()
        return serialized
