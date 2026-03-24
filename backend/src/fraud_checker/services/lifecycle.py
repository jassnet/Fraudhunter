from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from typing import Any

from ..job_status_pg import JobStatusStorePG
from ..service_protocols import LifecycleRepository
from ..time_utils import now_local

DEFAULT_RAW_RETENTION_DAYS = 90
DEFAULT_AGGREGATE_RETENTION_DAYS = 365
DEFAULT_FINDINGS_RETENTION_DAYS = 365
DEFAULT_JOB_RUN_RETENTION_DAYS = 30


@dataclass
class RetentionPolicy:
    raw_days: int | None = DEFAULT_RAW_RETENTION_DAYS
    aggregate_days: int | None = DEFAULT_AGGREGATE_RETENTION_DAYS
    findings_days: int | None = DEFAULT_FINDINGS_RETENTION_DAYS
    job_run_days: int | None = DEFAULT_JOB_RUN_RETENTION_DAYS


def resolve_retention_policy(
    *,
    raw_days: int | None = None,
    aggregate_days: int | None = None,
    findings_days: int | None = None,
    job_run_days: int | None = None,
) -> RetentionPolicy:
    return RetentionPolicy(
        raw_days=_resolve_days("FC_RETENTION_RAW_DAYS", DEFAULT_RAW_RETENTION_DAYS, raw_days),
        aggregate_days=_resolve_days(
            "FC_RETENTION_AGGREGATE_DAYS",
            DEFAULT_AGGREGATE_RETENTION_DAYS,
            aggregate_days,
        ),
        findings_days=_resolve_days(
            "FC_RETENTION_FINDINGS_DAYS",
            DEFAULT_FINDINGS_RETENTION_DAYS,
            findings_days,
        ),
        job_run_days=_resolve_days(
            "FC_RETENTION_JOB_RUN_DAYS",
            DEFAULT_JOB_RUN_RETENTION_DAYS,
            job_run_days,
        ),
    )


def purge_old_data(
    repo: LifecycleRepository,
    job_store: JobStatusStorePG,
    *,
    policy: RetentionPolicy | None = None,
    execute: bool = False,
    reference_time: datetime | None = None,
) -> dict[str, Any]:
    effective_policy = policy or resolve_retention_policy()
    now = reference_time or now_local()

    raw_cutoff = _cutoff_datetime(now, effective_policy.raw_days)
    aggregate_cutoff = _cutoff_date(now, effective_policy.aggregate_days)
    findings_cutoff = _cutoff_date(now, effective_policy.findings_days)
    job_run_cutoff = _cutoff_datetime(now, effective_policy.job_run_days)

    counts = {
        "raw": repo.purge_raw_before(raw_cutoff, execute=execute) if raw_cutoff else {},
        "aggregates": (
            repo.purge_aggregates_before(aggregate_cutoff, execute=execute)
            if aggregate_cutoff
            else {}
        ),
        "findings": repo.purge_findings_before(findings_cutoff, execute=execute) if findings_cutoff else {},
        "job_runs": (
            {"job_runs": job_store.purge_finished_runs_before(job_run_cutoff, execute=execute)}
            if job_run_cutoff
            else {}
        ),
    }

    return {
        "success": True,
        "execute": execute,
        "reference_time": now.isoformat(),
        "policy": asdict(effective_policy),
        "cutoffs": {
            "raw_before": raw_cutoff.isoformat() if raw_cutoff else None,
            "aggregates_before": aggregate_cutoff.isoformat() if aggregate_cutoff else None,
            "findings_before": findings_cutoff.isoformat() if findings_cutoff else None,
            "job_runs_before": job_run_cutoff.isoformat() if job_run_cutoff else None,
        },
        "counts": counts,
    }


def _resolve_days(name: str, default: int, explicit: int | None) -> int | None:
    if explicit is not None:
        return _normalize_days(explicit)
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return _normalize_days(int(raw))


def _normalize_days(value: int) -> int | None:
    return None if value <= 0 else int(value)


def _cutoff_datetime(reference_time: datetime, days: int | None) -> datetime | None:
    if days is None:
        return None
    return reference_time - timedelta(days=days)


def _cutoff_date(reference_time: datetime, days: int | None) -> date | None:
    if days is None:
        return None
    return (reference_time - timedelta(days=days)).date()
