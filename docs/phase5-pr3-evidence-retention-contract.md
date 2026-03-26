# PR3: Evidence Retention Contract

## Decision

This phase adopts the 90-day investigation contract.

- raw evidence retention remains 90 days
- findings retention remains 365 days
- findings older than the raw evidence window remain listable
- detail access for those old findings is downgraded to summary-only with `evidence_status = expired`

## Why

This is the smallest safe step that matches the current monolith shape.

It avoids:

- extending raw retention without an explicit product decision
- storing large evidence snapshots inside findings rows
- adding a second evidence store

## API Behavior

### List endpoints

List responses now include evidence availability fields:

- `evidence_status`
- `evidence_available`
- `evidence_expired`
- `evidence_retention_days`
- `evidence_expires_on`

Lists remain masked by default.

### Detail endpoints

For findings still inside the evidence window:

- full detail remains available
- unmasked access is returned
- audit logging still records access

For findings outside the evidence window:

- the response is summary-only
- supporting detail rows are omitted
- IP / UA stay masked
- `evidence_status = expired`

## Frontend Behavior

The detail panel now shows whether evidence is still available.

- available: detail can be used for investigation
- expired: only summary metadata is shown

## Rollback

This phase is application-only. No schema migration is required.

Rollback is just a deploy rollback.
