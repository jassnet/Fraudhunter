# Backend

FastAPI + CLI for Fraud Checker.

Install:
  cd backend
  python -m pip install -e ".[dev]"

Requires:
  DATABASE_URL (PostgreSQL)

Run API:
  python -m uvicorn fraud_checker.api:app --reload --app-dir ./src --port 8001

CLI:
  python -m fraud_checker.cli --help

Tests:
  set FRAUD_TEST_DATABASE_URL to a disposable Postgres database
  py -3 -m pytest
