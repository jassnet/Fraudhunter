from __future__ import annotations

from .db import Base
from .job_status_models import (
    DEFAULT_MAX_ATTEMPTS,
    DEFAULT_PRIORITY,
    DEFAULT_RETRY_BASE_SECONDS,
    IDLE_JOB_STATUS_MESSAGE,
    JOB_RUN_ACTIVE_STATUSES,
    JOB_RUN_STATUSES,
    MAX_RETRY_BACKOFF_SECONDS,
    QUEUED_JOB_STATUS_MESSAGE,
    JobRun,
    JobStatus,
)
from .job_status_queue import IntegrityError, now_local, uuid
from .job_status_queue import JobStatusQueueStore as _JobStatusQueueStore
from .job_status_summary import JobStatusSummaryMixin


class JobStatusStorePG(JobStatusSummaryMixin, _JobStatusQueueStore):
    """Backward-compatible facade over queue persistence and status summarization."""


__all__ = [
    "Base",
    "DEFAULT_MAX_ATTEMPTS",
    "DEFAULT_PRIORITY",
    "DEFAULT_RETRY_BASE_SECONDS",
    "IDLE_JOB_STATUS_MESSAGE",
    "IntegrityError",
    "JOB_RUN_ACTIVE_STATUSES",
    "JOB_RUN_STATUSES",
    "JobRun",
    "JobStatus",
    "JobStatusStorePG",
    "MAX_RETRY_BACKOFF_SECONDS",
    "QUEUED_JOB_STATUS_MESSAGE",
    "now_local",
    "uuid",
]
