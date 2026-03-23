# Phase 1 Operations

## Summary

Phase 1 introduces a durable `job_runs` table, lease-based job execution, production runtime guards, and additive data-quality metrics on the reporting and health surfaces.

The system remains a single Render + PostgreSQL monolith. Jobs are still triggered from the API, but durability now comes from PostgreSQL rather than in-process `BackgroundTasks` state.

## Migration

Apply Alembic before deploying application code:

```bash
cd backend
alembic upgrade head
```

New migration:

- `backend/alembic/versions/0003_add_job_runs.py`

## Runtime Model

- API write endpoints enqueue rows into `job_runs`.
- API may still kick a local worker via `BackgroundTasks`, but durability no longer depends on that task surviving process restarts.
- A worker can safely process queued jobs with:

```bash
cd backend
python -m fraud_checker.cli run-worker --max-jobs 1
```

- Lease-based execution fields:
  - `status`
  - `heartbeat_at`
  - `locked_until`
  - `worker_id`
- Stale running jobs are re-queued when their lease expires.

## Recommended Render Operation

- Keep the existing web service for the API.
- Add a cron or worker invocation that runs `python -m fraud_checker.cli run-worker --max-jobs 1`.
- Continue using PostgreSQL as the only shared coordination mechanism.

## Production Guards

The app now fails fast in production when either of these are enabled:

- `FC_ALLOW_INSECURE_ADMIN=true`
- `ACS_ALLOW_INSECURE=true`

API docs are disabled by default in production. Override only if intentionally needed:

- `FC_ENABLE_API_DOCS=true`

## Additive API Changes

### `GET /api/summary`

Adds:

- `quality.last_successful_ingest_at`
- `quality.click_ip_ua_coverage`
- `quality.conversion_click_enrichment`
- `quality.master_sync.last_synced_at`

### `GET /api/health`

Adds:

- `metrics.latest_data_date`
- `metrics.last_successful_ingest_at`
- `metrics.click_ip_ua_coverage`
- `metrics.conversion_click_enrichment`
- `metrics.master_sync`

Also removes legacy SQLite-oriented health hints and uses `DATABASE_URL` wording.

### `POST /api/refresh`
### `POST /api/ingest/clicks`
### `POST /api/ingest/conversions`
### `POST /api/sync/masters`

These endpoints now return durable `job_id` values from `job_runs`.

## Logging

Structured JSON logs are emitted for:

- API startup
- HTTP request timing
- job enqueue/start/finish/failure
- ingest and sync execution timing

## Rollback

If rollback is required:

1. Deploy the previous application version.
2. Leave the `job_runs` table in place. The old code will simply ignore it.
3. If needed, disable the worker/cron path that runs `fraud_checker.cli run-worker`.
4. Do not drop `job_runs` until the old version is confirmed stable and no queued jobs need inspection.
