# Phase 5 PR1: Read Access Hardening

## Goal

Separate read endpoints by sensitivity instead of treating every read as the same class of access.

The three tiers introduced in this PR are:

- public minimal
- analyst-auth
- admin-only

## Endpoint Tiering

### Public minimal

- `GET /`
- `GET /api/health/public`

Purpose:

- liveness
- service discovery
- minimal runtime posture visibility

### Analyst-auth

- `GET /api/summary`
- `GET /api/stats/daily`
- `GET /api/dates`
- `GET /api/suspicious/clicks`
- `GET /api/suspicious/conversions`
- `GET /api/suspicious/clicks/{finding_key}`
- `GET /api/suspicious/conversions/{finding_key}`
- `GET /api/masters/status`
- `GET /api/job/status`

Purpose:

- analyst monitoring
- masked list views
- unmasked detail with audit logging
- sanitized operations summary

### Admin-only

- `GET /api/health`
- `GET /api/settings`
- `POST /api/settings`
- `POST /api/refresh`
- `POST /api/sync/masters`
- `POST /api/ingest/*`
- `GET /api/job/status/admin`

## Backward Compatibility

- `GET /api/health` is preserved and remains the ops-health endpoint
- `GET /api/job/status` is preserved, but now returns a sanitized summary
- full admin job status moved to:
  - `GET /api/job/status/admin`

## Audit Logging

Unmasked suspicious detail access now emits a structured audit-like event to application logs.

Event name:

- `sensitive_detail_access`

Fields:

- `finding_key`
- `finding_type`
- `access_level`
- `token_source`
- `include_names`
- `include_details`

This PR intentionally keeps audit logging in structured app logs. It does not add a dedicated audit table.

## Env / Operations

- analyst-auth uses existing `FC_REQUIRE_READ_AUTH=true` and `FC_READ_API_KEY`
- admin-only uses `FC_ADMIN_API_KEY`
- production still must declare its read posture explicitly

## Next PR Hooks

This PR only separates access tiers.

It does not yet solve:

- immutable settings history
- findings generations
- stronger explainability / replay metadata
