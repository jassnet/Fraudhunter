# Render Deployment

This repo includes `render.yaml` for a two-service setup (backend + frontend) and a managed Postgres database.

## Required environment variables

Backend (service: `fraudchecker-backend`):
- `ACS_BASE_URL`
- `ACS_ACCESS_KEY` / `ACS_SECRET_KEY` (or `ACS_TOKEN`)
- `FC_ADMIN_API_KEY` (must match frontend)
- `FC_CORS_ORIGINS` (set to the frontend URL)

Frontend (service: `fraudchecker-frontend`):
- `NEXT_PUBLIC_API_URL` (backend URL)
- `API_BASE_URL` (backend URL)
- `FC_ADMIN_API_KEY` (same value as backend)

Cron jobs (if enabled in `render.yaml`):
- `ACS_BASE_URL`
- `ACS_ACCESS_KEY` / `ACS_SECRET_KEY` (or `ACS_TOKEN`)
- `DATABASE_URL` (wired in `render.yaml`)

## Scheduled ingestion

`render.yaml` includes two cron jobs (UTC):
- `fraudchecker-refresh-hourly`: runs `python -m fraud_checker.cli refresh --hours 1 --detect` every hour.
- `fraudchecker-sync-masters-daily`: runs `python -m fraud_checker.cli sync-masters` daily at 03:30 UTC.

If your Render plan does not support cron jobs, use GitHub Actions instead (see below).

## GitHub Actions (alternative)

Two workflows are provided:
- `.github/workflows/refresh.yml` (hourly refresh)
- `.github/workflows/sync-masters.yml` (daily master sync)

Required GitHub Secrets:
- `BACKEND_BASE_URL` (e.g. `https://fraudchecker-backend.onrender.com`)
- `FC_ADMIN_API_KEY` (same as backend)

## Notes
- `DATABASE_URL` is wired from Render Postgres in `render.yaml`.
- `preDeployCommand: alembic upgrade head` runs migrations on deploy (requires a paid Render plan for predeploy commands).
