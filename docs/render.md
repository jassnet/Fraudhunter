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

## Notes
- `DATABASE_URL` is wired from Render Postgres in `render.yaml`.
- `preDeployCommand: alembic upgrade head` runs migrations on deploy (requires a paid Render plan for predeploy commands).
