# PR4: Queue Correctness Hardening

## Summary

This phase tightens correctness around durable jobs without changing the monolith shape.

Key changes:

- `job_runs` now has `concurrency_key`
- active duplicate protection moves from app-only best effort to DB-backed enforcement
- broad refresh no longer recomputes findings inline across many dates
- settings update no longer recomputes findings inline in the request path
- legacy `job_status` remains a compatibility artifact, but the runtime now treats `job_runs` as the only source of truth

## Schema

Migration: `0008_job_run_concurrency`

- add `job_runs.concurrency_key`
- add `idx_job_runs_concurrency_status`
- add PostgreSQL partial unique index:
  - `ux_job_runs_active_dedupe_key`
  - unique on `dedupe_key`
  - only when `status IN ('queued', 'running')`

## Execution Model

### Active dedupe

The application still checks for an existing queued/running duplicate before insert.

The new partial unique index is the race-safe backstop.

If two enqueue requests race:

- one insert wins
- the loser catches the integrity error
- the service looks up the existing active run
- the existing `job_id` is returned

### Concurrency control

Jobs that write findings for the same date now share a `concurrency_key`.

Current date-scoped key:

- `date-write:YYYY-MM-DD`

Used by:

- click ingestion jobs
- conversion ingestion jobs
- recompute findings date jobs

Execution uses PostgreSQL advisory locks.

If a worker acquires a job but the date lock is busy:

- the job is put back to `queued`
- `attempt_count` is not consumed
- `next_retry_at` is advanced by a short delay

This prevents overlapping writes without dropping work.

## Fan-out changes

### Refresh

`refresh` still ingests the requested sliding time window.

What changed is the findings recompute stage:

- before: recompute all affected dates inline in the same job
- now: enqueue one `recompute_findings_date` job per affected date

This keeps the refresh job bounded and makes date-level serialization explicit.

### Settings update

`POST /api/settings` now:

- persists the settings snapshot
- enqueues one findings recompute job per available date
- returns enqueue metadata instead of doing broad recompute inline

Returned fields now include:

- `findings_recompute_enqueued`
- `recompute_job_ids`
- `recompute_target_dates`
- `generation_id`

`findings_recomputed` is only `true` when there were no target dates to enqueue.

## Legacy `job_status`

`job_status` is no longer part of runtime coordination.

Current stance:

- source of truth: `job_runs`
- API status endpoints are derived from `job_runs`
- seed/reset flows no longer depend on `job_status`

The table may still exist in older databases, but it is treated as retired residue.

## Rollback

This phase is additive.

Safe rollback order:

1. roll application code back
2. leave migration `0008` in place
3. keep `concurrency_key` and indexes; old code ignores the extra column

No destructive schema rollback is required for a normal deploy rollback.

## Verification

- `pytest backend/tests -q`
