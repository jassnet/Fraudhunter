# Phase 5 PR4: Queue Correctness Hardening

## Goal

Reduce duplicate findings recompute work and make queue behavior observable from the console.

## Dedupe model

- Findings recompute jobs are deduplicated by target date.
- Dedupe key:
  - `recompute_findings_date:{target_date}`
- `generation_id`, `trigger`, and `source_job_id` remain in job params for lineage, but they do not create separate active recompute jobs for the same date.

## Refresh behavior

- Refresh ingests a sliding time window.
- Only dates actually touched by click or conversion ingestion are enqueued for findings recompute.
- `detect=false` performs ingestion only and does not enqueue findings recompute jobs.

## Master sync and settings fan-out

- Master sync still fans out recompute work for available dates, but active duplicates coalesce by date.
- Settings-driven recompute follows the same date-level dedupe contract.

## Console visibility

- The dashboard includes freshness and queue summary.
- Admin actions return `job_id`.
- `GET /api/console/job-status/{job_id}` exposes:
  - queued
  - running
  - completed
  - failed

## Verification

- backend job tests verify date-level dedupe and detect behavior
- frontend dashboard tests verify job polling and stale visibility
