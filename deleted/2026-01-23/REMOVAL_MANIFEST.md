# Removal manifest (2026-01-23)

All items below were moved here to reduce repo volume, remove duplicates, and
avoid committing secrets or data. Paths are relative to repo root.

## Security-sensitive or generated
- .env (contained real credentials)
- fraud_checker.db (data file)
- backend/src/fraud_checker.db (data file)
- backend/fraud_checker.db-wal
- backend/fraud_checker.db-shm
- backend/src/fraud_checker.db-wal
- backend/src/fraud_checker.db-shm
- backend.err.log, backend.out.log, frontend.err.log, frontend.out.log
- uvicorn_err.log, uvicorn_out.log

## Documentation cleanup (duplicates / outdated)
- docs/
- backend/Docs/
- frontend/README.md
- refactor_plan.md
- refactor_report.md
- backend/README.md (replaced with a minimal ASCII version)

## Examples / samples (non-production)
- backend/examples/
- backend/src/fraud_checker/examples/

## Unused frontend assets
- frontend/public/next.svg
- frontend/public/vercel.svg
- frontend/public/globe.svg
- frontend/public/window.svg
- frontend/public/file.svg
- frontend/components.json

## Frontend feature trims (admin + advanced UI)
- frontend/src/app/settings/page.tsx
- frontend/src/components/refresh-dialog.tsx
- frontend/src/lib/use-job-runner.ts
- frontend/src/components/job-status-indicator.tsx
- frontend/src/components/job-status-notifier.tsx
- frontend/src/components/notification-center.tsx
- frontend/src/hooks/use-job-status.ts
- frontend/src/components/setup-warning.tsx
- frontend/src/hooks/use-health-status.ts
- frontend/src/app/api/admin/[...path]/route.ts
- frontend/src/components/ui/switch.tsx
- frontend/src/components/ui/tabs.tsx
- frontend/src/components/breadcrumbs.tsx
- frontend/src/components/ui/dialog.tsx
- frontend/src/components/ui/label.tsx
- frontend/src/components/ui/tooltip.tsx
- frontend/src/components/mode-toggle.tsx
- frontend/src/components/theme-provider.tsx
- frontend/src/components/ui/dropdown-menu.tsx
- frontend/src/components/ui/select.tsx
- frontend/src/components/ui/sheet.tsx

## Build artifacts
- backend/tests/__pycache__
- backend/src/fraud_checker/__pycache__
- backend/src/fraud_checker/db/__pycache__
- backend/src/fraud_checker/services/__pycache__
- frontend/.next

## Backend SQLite removal (Postgres-only)
- backend/src/fraud_checker/repository.py
- backend/src/fraud_checker/job_status.py
- backend/src/fraud_checker/db/migrate_sqlite_to_postgres.py
- backend/tests/test_cli.py
- backend/tests/test_ingestion.py
- backend/tests/test_repository.py
- backend/tests/test_suspicious.py

## Config / local tooling cleanup
- .vscode/
- .claude/
- .github/workflows/refresh.yml
- .github/workflows/sync-masters.yml
- frontend/.env.example
- start.bat

If any item needs to be restored, move it back to the original path.
