from __future__ import annotations

from .job_status_models import (
    IDLE_JOB_STATUS_MESSAGE,
    QUEUED_JOB_STATUS_MESSAGE,
    JobStatus,
)


class JobStatusSummaryMixin:
    def get(self) -> JobStatus:
        run = self._fetch_latest_run()
        queue = self._serialize_queue_metrics(self.get_queue_metrics())
        if not run:
            return JobStatus(
                status="idle",
                job_id=None,
                message=IDLE_JOB_STATUS_MESSAGE,
                started_at=None,
                completed_at=None,
                result=None,
                queue=queue,
            )

        if run.status == "queued":
            return JobStatus(
                status="queued",
                job_id=run.id,
                message=run.message or QUEUED_JOB_STATUS_MESSAGE,
                started_at=run.started_at,
                completed_at=run.finished_at,
                result=run.result,
                queue=queue,
            )

        status = "completed" if run.status == "succeeded" else run.status
        return JobStatus(
            status=status,
            job_id=run.id,
            message=run.message,
            started_at=run.started_at,
            completed_at=run.finished_at,
            result=run.result,
            queue=queue,
        )
