# Phase 5 PR1: Console Access Hardening

## Goal

Stop treating server-side secrets as a substitute for human authorization.

This phase moves console authorization to trusted viewer identity and enforces role boundaries on the console surface itself.

## Viewer model

### Trusted gateway into Next.js

- `X-Auth-Request-User`
- `X-Auth-Request-Email`
- `X-Auth-Request-Role`

Accepted roles:

- `analyst`
- `admin`

### Internal headers into backend

- `X-Console-User-Id`
- `X-Console-User-Email`
- `X-Console-User-Role`
- `X-Console-Request-Id`
- `X-Console-User-Signature`

The backend verifies the signature with `FC_INTERNAL_PROXY_SECRET`.

## Access policy

### Analyst read

- `GET /api/console/dashboard`
- `GET /api/console/alerts`
- `GET /api/console/alerts/{case_key}`
- `GET /api/console/alerts/export`
- `GET /api/console/job-status/{job_id}`

### Admin mutation

- `POST /api/console/alerts/review`
- `POST /api/console/admin/refresh`
- `POST /api/console/admin/master-sync`

## Frontend behavior

- Next.js proxy routes fail closed when gateway identity is missing.
- Read routes require at least analyst role.
- Mutation routes require admin role.
- Review and admin action controls are hidden for analyst viewers.

## Verification

- frontend proxy unit tests verify signed viewer forwarding
- route tests verify analyst read access and admin-only mutations
- backend API tests verify anonymous, analyst, and admin behavior
