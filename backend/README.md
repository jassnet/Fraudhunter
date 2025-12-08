# Backend (FastAPI + CLI)

Fraud Checker backend ingests ACS click/conversion logs, aggregates IP/UA stats, and exposes both a FastAPI service and a CLI.

## Layout
- `pyproject.toml` – package + dev dependencies.
- `src/fraud_checker/` – application code (API, CLI, ingestion, rules, repository).
- `tests/` – pytest suites.
- `examples/` – sample scripts and flows.
- `Docs/` – design notes.

## Environment
Set these in `.env` (repo root or `backend/.env`):
- `FRAUD_DB_PATH` – SQLite path (absolute recommended).
- `ACS_BASE_URL` – e.g. `https://acs.example.com/api`.
- `ACS_ACCESS_KEY` / `ACS_SECRET_KEY` or `ACS_TOKEN` (`access:secret`).
- Optional overrides: `FRAUD_PAGE_SIZE`, `FRAUD_STORE_RAW`, `FRAUD_CLICK_THRESHOLD`, `FRAUD_MEDIA_THRESHOLD`, `FRAUD_PROGRAM_THRESHOLD`, `FRAUD_BURST_CLICK_THRESHOLD`, `FRAUD_BURST_WINDOW_SECONDS`, `FRAUD_CONVERSION_THRESHOLD`, `FRAUD_CONV_MEDIA_THRESHOLD`, `FRAUD_CONV_PROGRAM_THRESHOLD`, `FRAUD_BURST_CONVERSION_THRESHOLD`, `FRAUD_BURST_CONVERSION_WINDOW_SECONDS`, `FRAUD_BROWSER_ONLY`, `FRAUD_EXCLUDE_DATACENTER_IP`, `ACS_LOG_ENDPOINT`.
- Click-to-conversion timing: `FRAUD_MIN_CLICK_TO_CONV_SECONDS`, `FRAUD_MAX_CLICK_TO_CONV_SECONDS`.

## Install
```
cd backend
python -m pip install -e ".[dev]"
```

## Run API only
```
cd backend
python -m uvicorn fraud_checker.api:app --reload --app-dir ./src --port 8000
```
Docs: http://localhost:8000/docs

## CLI examples
```
python -m fraud_checker.cli ingest --date 2024-01-01
python -m fraud_checker.cli suspicious --date 2024-01-01
python -m fraud_checker.cli ingest-conversions --date 2024-01-01
python -m fraud_checker.cli suspicious-conversions --date 2024-01-01
python -m fraud_checker.cli daily --days-ago 1
python -m fraud_checker.cli daily-full --days-ago 1
python -m fraud_checker.cli refresh --hours 12 --detect
```

## Tests
```
python -m pytest
```
