# Fraud Checker v2

FastAPI + Next.js stack for click/conversion ingestion and fraud detection.

## Structure
- backend/   Python package (API, CLI, ingestion, rules, repository)
- frontend/  Next.js dashboard
- dev.py     run backend + frontend together

## Quick start
### Backend
cd backend
python -m pip install -e ".[dev]"

### Frontend
cd frontend
npm install

### Environment
Copy `.env.example` and set real values:
- DATABASE_URL (PostgreSQL)
- ACS_BASE_URL, ACS_ACCESS_KEY, ACS_SECRET_KEY (or ACS_TOKEN)
- FC_ADMIN_API_KEY (required for admin endpoints like /api/health, /api/ingest/*, /api/refresh)
- NEXT_PUBLIC_API_URL (frontend -> backend)

### Run
python dev.py
- Backend: http://localhost:8001 (docs at /docs)
- Frontend: http://localhost:3000

## Security
Admin endpoints require FC_ADMIN_API_KEY. For local dev only, you can set
FC_ENV=dev or FC_ALLOW_INSECURE_ADMIN=true to bypass the check.

## Operations
The dashboard is read-only. Ingestion/refresh tasks run via CLI or cron jobs.
`refresh --detect` uses the same thresholds as the API (DB settings override env defaults).

## CLI (examples)
cd backend
python -m fraud_checker.cli refresh --hours 12 --detect
python -m fraud_checker.cli sync-masters

## Deployment
render.yaml defines backend, frontend, and cron jobs using PostgreSQL.
Secrets like FC_ADMIN_API_KEY and ACS_* should be set in Render (envVars use sync: false).
