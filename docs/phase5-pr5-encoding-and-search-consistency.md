# Phase 5 PR5: Encoding + Search Consistency

## Summary
- findings list search uses `search_text` built from persisted finding fields
- `search_text` currently includes mutable master-derived names
- master sync now re-enqueues findings recompute so the persisted search surface catches up
- repository text files are treated as UTF-8 and guarded in tests

## Changes
### 1. UTF-8 hygiene
- Added [`.editorconfig`](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/.editorconfig)
- Added [`.gitattributes`](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/.gitattributes)
- Added [test_utf8_guard_behavior.py](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/backend/tests/test_utf8_guard_behavior.py)
- Removed the mojibake-heavy pytest display-name map and fell back to original test names in [conftest.py](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/backend/tests/conftest.py)

### 2. Search performance
- Added PostgreSQL `pg_trgm` GIN indexes for current click/conversion findings search text
- Migration: [0009_add_findings_search_indexes.py](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/backend/alembic/versions/0009_add_findings_search_indexes.py)
- Scope is limited to `is_current = TRUE` because the list hot path only reads current generations

### 3. Master rename consistency
- `run_master_sync()` now enqueues findings recompute jobs for all available dates after master upsert completes
- This keeps persisted `search_text` aligned when media/program/user names change
- The design remains simple:
  - no dual-write search material
  - no trigger-based rewrite
  - no separate search projection store

## Tradeoffs
- Recomputing all available dates after master sync is more expensive than a targeted rename diff.
- That cost is acceptable here because master sync is low-frequency and already runs off the durable queue.
- We intentionally avoid a more complex immutable search projection until master rename churn becomes a proven bottleneck.

## Rollback
1. Deploy the previous app version.
2. Leave migration `0009_findings_search_idx` in place.
3. If needed, drop trigram indexes:
   - `DROP INDEX IF EXISTS idx_scf_search_text_trgm`
   - `DROP INDEX IF EXISTS idx_scof_search_text_trgm`
4. If master-sync-triggered recompute causes operational load, revert the app change while keeping the indexes.

## Operational Notes
- Production remains `enqueue-only`.
- Master sync still runs as a durable job.
- Findings recompute caused by master sync is visible in the parent job result under `findings_recompute`.
- If search feels stale after a rename, check:
  - latest successful `master_sync`
  - queued/running `recompute_findings_date` jobs
  - findings generation timestamps for affected dates
