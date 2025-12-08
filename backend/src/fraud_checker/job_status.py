from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class JobStatus:
    status: str
    job_id: Optional[str]
    message: str
    started_at: Optional[str]
    completed_at: Optional[str]
    result: Optional[dict]


class JobStatusStore:
    """Lightweight job status persistence backed by SQLite."""

    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS job_status (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    status TEXT NOT NULL,
                    job_id TEXT,
                    message TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    result_json TEXT
                );
                """
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO job_status (id, status, message)
                VALUES (1, 'idle', 'No job has been run yet');
                """
            )

    def get(self) -> JobStatus:
        self.ensure_schema()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT status, job_id, message, started_at, completed_at, result_json FROM job_status WHERE id = 1"
            ).fetchone()
        result = json.loads(row["result_json"]) if row and row["result_json"] else None
        return JobStatus(
            status=row["status"] if row else "idle",
            job_id=row["job_id"] if row else None,
            message=row["message"] if row else "No job has been run yet",
            started_at=row["started_at"] if row else None,
            completed_at=row["completed_at"] if row else None,
            result=result,
        )

    def start(self, job_id: str, message: str) -> None:
        self.ensure_schema()
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE job_status
                SET status = 'running',
                    job_id = ?,
                    message = ?,
                    started_at = ?,
                    completed_at = NULL,
                    result_json = NULL
                WHERE id = 1
                """,
                (job_id, message, now),
            )

    def complete(self, job_id: str, message: str, result: Optional[dict] = None) -> None:
        self._finish(job_id, "completed", message, result)

    def fail(self, job_id: str, message: str, result: Optional[dict] = None) -> None:
        self._finish(job_id, "failed", message, result)

    def _finish(self, job_id: str, status: str, message: str, result: Optional[dict]) -> None:
        self.ensure_schema()
        now = datetime.utcnow().isoformat()
        result_json = json.dumps(result) if result is not None else None
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE job_status
                SET status = ?,
                    job_id = ?,
                    message = ?,
                    completed_at = ?,
                    result_json = ?
                WHERE id = 1
                """,
                (status, job_id, message, now, result_json),
            )
