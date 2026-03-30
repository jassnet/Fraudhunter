from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


JOB_RUN_STATUSES = {"queued", "running", "succeeded", "failed", "cancelled"}
JOB_RUN_ACTIVE_STATUSES = {"queued", "running"}
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_PRIORITY = 100
DEFAULT_RETRY_BASE_SECONDS = 30
MAX_RETRY_BACKOFF_SECONDS = 900

IDLE_JOB_STATUS_MESSAGE = "まだジョブは実行されていません"
QUEUED_JOB_STATUS_MESSAGE = "ジョブを実行待ちキューに登録しました"


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
