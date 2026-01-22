# Refactor Report

## What Changed
- backend/src/fraud_checker/services/reporting.py: centralized summary/daily/date reporting queries.
- backend/src/fraud_checker/services/settings.py: moved settings cache and persistence out of API module.
- backend/src/fraud_checker/repository.py: added fetch_one/fetch_all helpers and removed unused master name helpers and unused suspicious report methods.
- backend/src/fraud_checker/api.py: endpoints now delegate to reporting/settings helpers and share suspicious search/cache helpers.
- frontend/src/components/ui/*.tsx: removed unused UI components.
- frontend/package.json and frontend/package-lock.json: removed unused Radix dependencies.
- frontend/src/hooks/use-job-status.ts and frontend/src/hooks/use-health-status.ts: added polling stores via useSyncExternalStore.

## Impact
- Dependencies: Next updated to 16.1.4 to address audit findings.
- Clarity: API endpoints are thinner and delegate to focused service modules.
- Maintainability: shared query helpers replace ad-hoc sqlite calls.
- Reduction: removed unused UI components and 5 unused Radix packages.
- Security surface: fewer unused dependencies reduce exposure to unused CVEs.
- UI stability: polling moved to external stores to avoid setState-in-effect lint violations.

## Behavior Notes
- API routes and response shapes are preserved; changes are internal refactors.
- Backend tests: `py -m pytest` (passed).
