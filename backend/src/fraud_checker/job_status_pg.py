from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

import sqlalchemy as sa

from .db import Base
from .db.session import normalize_database_url
import fraud_checker.db.models  # noqa: F401
from .time_utils import now_local


@dataclass
class JobStatus:
    status: str
    job_id: str | None
    message: str | None
    started_at: str | None
    completed_at: str | None
    result: dict | None


class JobStatusStorePG:
    def __init__(self, database_url: str):
        self.database_url = normalize_database_url(database_url)
        self.engine = sa.create_engine(self.database_url, pool_pre_ping=True)

    def ensure_schema(self) -> None:
        Base.metadata.create_all(self.engine, tables=[Base.metadata.tables["job_status"]])
        with self.engine.begin() as conn:
            conn.execute(
                sa.text(
                    """
                    INSERT INTO job_status (id, status, message)
                    VALUES (1, 'idle', 'No job has been run yet')
                    ON CONFLICT (id) DO NOTHING
                    """
                )
            )

    def get(self) -> JobStatus:
        self.ensure_schema()
        with self.engine.begin() as conn:
            row = conn.execute(
                sa.text(
                    """
                    SELECT status, job_id, message, started_at, completed_at, result_json
                    FROM job_status WHERE id = 1
                    """
                )
            ).mappings().first()
        result = json.loads(row["result_json"]) if row and row.get("result_json") else None
        return JobStatus(
            status=row["status"] if row else "idle",
            job_id=row["job_id"] if row else None,
            message=row["message"] if row else "No job has been run yet",
            started_at=row["started_at"] if row else None,
            completed_at=row["completed_at"] if row else None,
            result=result,
        )

    def start(self, job_id: str, message: str) -> bool:
        self.ensure_schema()
        now = now_local()
        with self.engine.begin() as conn:
            result = conn.execute(
                sa.text(
                    """
                    UPDATE job_status
                    SET status = 'running',
                        job_id = :job_id,
                        message = :message,
                        started_at = :started_at,
                        completed_at = NULL,
                        result_json = NULL
                    WHERE id = 1 AND status != 'running'
                    """
                ),
                {"job_id": job_id, "message": message, "started_at": now},
            )
        return result.rowcount == 1

    def complete(self, job_id: str, message: str, result: dict | None = None) -> None:
        self._finish(job_id, "completed", message, result)

    def fail(self, job_id: str, message: str, result: dict | None = None) -> None:
        self._finish(job_id, "failed", message, result)

    def _finish(self, job_id: str, status: str, message: str, result: dict | None) -> None:
        self.ensure_schema()
        now = now_local()
        result_json = json.dumps(result) if result is not None else None
        with self.engine.begin() as conn:
            conn.execute(
                sa.text(
                    """
                    UPDATE job_status
                    SET status = :status,
                        job_id = :job_id,
                        message = :message,
                        completed_at = :completed_at,
                        result_json = :result_json
                    WHERE id = 1
                    """
                ),
                {
                    "status": status,
                    "job_id": job_id,
                    "message": message,
                    "completed_at": now,
                    "result_json": result_json,
                },
            )
