# PR2: Immutable Provenance

## Summary

PR2 adds durable provenance for settings and findings generations without changing the monolith shape.

The goal is to keep explainability after:

- `job_runs` retention removes old queue records
- raw evidence retention removes old source rows
- settings are updated multiple times

## Added Tables

### `settings_versions`

Append-only snapshot table for effective application settings.

Columns:

- `id`
- `fingerprint`
- `snapshot_json`
- `created_at`

`app_settings` remains the mutable current-state table.
`settings_versions` is the provenance table used by findings generations.

### `findings_generations`

Current-pointer table for recompute generations by finding type and target date.

Columns:

- `id`
- `generation_id`
- `finding_type`
- `target_date`
- `computed_by_job_id`
- `settings_version_id`
- `settings_fingerprint`
- `detector_code_version`
- `source_click_watermark`
- `source_conversion_watermark`
- `row_count`
- `is_current`
- `created_at`

## Read Path

Current findings reads now prefer `findings_generations` as the source of lineage truth.

- list/detail still read finding rows
- current generation selection is constrained by `findings_generations.is_current = TRUE`
- summary freshness reads lineage from `findings_generations`
- legacy row-level `settings_updated_at_snapshot` remains as backward-compatible fallback

## Why This Design

This keeps the implementation additive and safe:

- no detector rewrite
- no dual storage service
- no queue redesign
- no breaking API change

The tradeoff is that findings rows still carry some duplicated lineage fields.
That duplication is acceptable for now because it preserves backward compatibility and keeps rollback simple.

## Rollback

Rollback is application-first.

1. Deploy the previous app version.
2. Leave `settings_versions` and `findings_generations` in place.
3. Old code ignores those tables.

Schema downgrade is possible but not recommended unless the application rollback is insufficient.

## Operational Notes

- `settings_versions` is the long-lived provenance source for settings snapshots.
- `findings_generations` is the long-lived provenance source for recompute runs.
- `job_runs` may expire earlier than findings. Provenance still remains explainable through generation metadata.
- If a database is behind and has no `findings_generations`, the read path falls back to legacy current-row lineage until migrations are applied.
