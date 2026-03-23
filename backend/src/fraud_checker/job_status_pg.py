from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import sqlalchemy as sa

from .db import Base
from .db.session import normalize_database_url
import fraud_checker.db.models  # noqa: F401
from .time_utils import now_local

JOB_RUN_STATUSES = {"queued", "running", "succeeded", "failed", "cancelled"}


@dataclass
class JobStatus:
    status: str
    job_id: str | None
    message: str | None
    started_at: str | datetime | None
    completed_at: str | datetime | None
    result: dict[str, Any] | None


@dataclass
class JobRun:
    id: str
    job_type: str
    status: str
    params: dict[str, Any] | None
    result: dict[str, Any] | None
    error_message: str | None
    message: str | None
    queued_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    heartbeat_at: datetime | None
    locked_until: datetime | None
    worker_id: str | None


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
                           queued_at, started_at, finished_at, heartbeat_at, locked_until, worker_id
                    FROM job_runs
                    ORDER BY COALESCE(finished_at, started_at, queued_at) DESC, queued_at DESC
                    LIMIT 1
                    """
                )
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
                    WHERE status = 'queued'
                       OR (status = 'running' AND (locked_until IS NULL OR locked_until >= :now))
                    """
                ),
                {"now": now},
            ).scalar_one()
        return bool(count)

    def enqueue(self, *, job_type: str, params: dict[str, Any] | None, message: str | None) -> JobRun:
        queued_at = now_local()
        run_id = uuid.uuid4().hex
        with self.engine.begin() as conn:
            conn.execute(
                sa.text(
                    """
                    INSERT INTO job_runs (
                        id, job_type, status, params_json, message, queued_at
                    ) VALUES (
                        :id, :job_type, 'queued', :params_json, :message, :queued_at
                    )
                    """
                ),
                {
                    "id": run_id,
                    "job_type": job_type,
                    "params_json": self._dumps(params),
                    "message": message,
                    "queued_at": queued_at,
                },
            )
        return JobRun(
            id=run_id,
            job_type=job_type,
            status="queued",
            params=params,
            result=None,
            error_message=None,
            message=message,
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
                        locked_until = NULL
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
                        ORDER BY queued_at ASC
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
                        locked_until = NULL
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
    ) -> None:
        finished_at = now_local()
        with self.engine.begin() as conn:
            conn.execute(
                sa.text(
                    """
                    UPDATE job_runs
                    SET status = 'failed',
                        message = :message,
                        result_json = :result_json,
                        error_message = :error_message,
                        finished_at = :finished_at,
                        heartbeat_at = :finished_at,
                        locked_until = NULL
                    WHERE id = :run_id
                    """
                ),
                {
                    "run_id": run_id,
                    "message": message,
                    "result_json": self._dumps(result),
                    "error_message": error_message,
                    "finished_at": finished_at,
                },
            )

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
                        locked_until = NULL
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

    def get_latest_run(self) -> JobRun | None:
        return self._fetch_latest_run()

    def get(self) -> JobStatus:
        run = self._fetch_latest_run()
        if not run:
            return JobStatus(
                status="idle",
                job_id=None,
                message="まだジョブは実行されていません",
                started_at=None,
                completed_at=None,
                result=None,
            )

        if run.status == "queued":
            status = "running"
            message = run.message or "ジョブを待機列に登録しました"
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
        )
