# Fraud Console Hardening Notes

## Auth boundary

- Console routes now require trusted gateway identity on the frontend edge:
  - `X-Auth-Request-User`
  - `X-Auth-Request-Email`
  - `X-Auth-Request-Role`
- Accepted roles are `analyst` and `admin`.
- The Next.js proxy forwards signed internal headers to the backend:
  - `X-Console-User-Id`
  - `X-Console-User-Email`
  - `X-Console-User-Role`
  - `X-Console-Request-Id`
  - `X-Console-User-Signature`
- Console read routes require at least analyst access. Console review, refresh, and master sync routes require admin access.

## Stable case identity

- Triage is now centered on `case_key`.
- `case_key` is derived from the environment identity:
  - `"conversion_case|date|ipaddress|useragent"`
- `finding_key` remains an internal lineage key tied to a specific recompute generation and rule version.
- List rows, detail lookups, and review state joins now use `case_key`.

## Review model

- Reviews are stored in two layers:
  - `fraud_alert_review_events` for append-only audit history
  - `fraud_alert_review_states` for the latest state per case
- Review mutations require:
  - `case_keys`
  - `status`
  - `reason`
- Review responses return:
  - `requested_count`
  - `matched_current_count`
  - `updated_count`
  - `missing_keys`
  - `status`

## Detail evidence semantics

- Alert detail now separates:
  - `evidence_transactions`
  - `affiliate_recent_transactions`
- The primary evidence table always uses the suspicious environment itself:
  - same `date`
  - same `ipaddress`
  - same `useragent`
- Affiliate recent transactions are optional secondary context and are not used as the primary evidence view.

## Dashboard and job visibility

- The console dashboard now exposes:
  - `quality`
  - `job_status_summary`
  - `case_ranking`
- Freshness payload includes:
  - `quality.findings.stale`
  - `findings_last_computed_at`
  - `last_successful_ingest_at`
  - `master_sync.last_synced_at`
- Admin actions surface `job_id` and can be followed through `GET /api/console/job-status/{job_id}`.

## Queue and refresh behavior

- Findings recompute jobs are deduplicated by target date using:
  - `recompute_findings_date:{target_date}`
- Refresh only enqueues dates actually touched by ingestion.
- `detect=false` performs ingestion without creating findings recompute jobs.
