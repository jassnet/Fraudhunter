# Backend

FastAPI + CLI for Fraud Checker.

Install:
  cd backend
  python -m pip install -e ".[dev]"

Requires:
  DATABASE_URL (PostgreSQL)
  ACS_BASE_URL, ACS_ACCESS_KEY, ACS_SECRET_KEY (or ACS_TOKEN)
  FC_ADMIN_API_KEY (required for admin endpoints: /api/health, /api/ingest/*, /api/refresh)

Run API:
  python -m uvicorn fraud_checker.api:app --reload --app-dir ./src --port 8001

CLI:
  python -m fraud_checker.cli --help
  python -m fraud_checker.cli refresh --hours 12 --detect

Tests:
  set FRAUD_TEST_DATABASE_URL to a disposable Postgres database
  py -3 -m pytest
