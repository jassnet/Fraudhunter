# FraudChecker Operations Runbook

## Scope

This runbook covers the incidents and recovery steps called out in the April 8, 2026 review:

- stalled or delayed background jobs
- ACS API degradation
- database migration rollback
- console alert export checks

## Quick Checks

Run these first when the system looks unhealthy.

### Backend health

1. Call `GET /api/health/public`.
2. Confirm `status=ok`.
3. Confirm `read_access_mode` matches the expected deployment mode.

For admin-only diagnostics, call `GET /api/health` with `X-API-Key`.

Check these fields:

- `metrics.jobs.queued_jobs_count`
- `metrics.jobs.running_jobs_count`
- `metrics.jobs.failed_jobs_count`
- `metrics.acs_api.ok`
- `metrics.findings.stale`

### Console smoke check

1. Open the alerts screen.
2. Apply a narrow date range and a search term.
3. Confirm the list loads.
4. Trigger `CSVエクスポート`.
5. Confirm the response includes a CSV attachment and rows match the visible filters.

## Incident: Background Job Is Stuck

Symptoms:

- refresh job never completes
- queued jobs keep growing
- `metrics.jobs.oldest_queued_age_seconds` keeps increasing

Steps:

1. Call `GET /api/job/status`.
2. If the job is still `running`, compare `started_at` with the expected job duration.
3. Check application logs for the current `job_id`.
4. Check `GET /api/health` and confirm whether ACS or database access is degraded.
5. If a worker is wedged, restart the backend process.
6. Re-run the intended operation from the console or the corresponding admin endpoint.

Recovery criteria:

- `queued_jobs_count` trends back to zero
- a new refresh job finishes successfully
- `findings.stale` becomes `false`

## Incident: ACS API Degradation

Symptoms:

- `metrics.acs_api.ok=false`
- ingestion jobs fail repeatedly
- latency spikes or ACS responses time out

Steps:

1. Call `GET /api/health` and inspect `metrics.acs_api`.
2. Check recent backend logs for `ACS request failed` or non-200 ACS responses.
3. Verify `ACS_BASE_URL` and credentials are still correct in the deployment environment.
4. Retry a lightweight ACS call through the normal health endpoint rather than ad hoc scripts.
5. If ACS is down, pause manual re-runs until the upstream service recovers.
6. After recovery, trigger a bounded refresh first, then a full refresh if needed.

Notes:

- the client now retries transient ACS failures automatically
- health checks surface ACS reachability directly

## Incident: Database Migration Rollback

Use this only when a recent schema change caused a production regression.

Steps:

1. Identify the migration that was applied most recently.
2. Stop write-heavy operational activity if possible.
3. Take a fresh database backup or snapshot before any rollback.
4. Roll back exactly one migration step using the project migration tool.
5. Restart the backend.
6. Run `GET /api/health` and verify database access, queue metrics, and findings status.
7. Re-test console alerts, dashboard, and refresh flow.

Do not:

- run destructive manual SQL unless the rollback path is unavailable
- skip the pre-rollback backup

## Incident: Console Export Looks Wrong

Symptoms:

- CSV download fails
- exported rows do not match UI filters
- reward amounts look inconsistent

Checks:

1. Re-run the same filters in the alerts UI.
2. Download the CSV again.
3. Confirm the request query contains the same `status`, `start_date`, `end_date`, and `search`.
4. Confirm the response has `Content-Disposition` and `Content-Type: text/csv`.
5. Spot check `reward_amount_source` and `reward_amount_is_estimated`.

If the export is wrong:

1. Compare API response from `/api/console/alerts` and `/api/console/alerts/export` using the same filters.
2. Check backend logs for console query failures.
3. If only fallback reward estimation is affected, inspect recent conversion data completeness.

## Escalation Notes

Escalate beyond the application team when:

- ACS is unavailable or returning invalid payloads for an extended period
- the database cannot be rolled back cleanly
- queued jobs keep growing after a clean restart
- alert exports differ from API payloads under identical filters
