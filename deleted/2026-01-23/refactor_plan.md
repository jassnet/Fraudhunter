# Refactor Plan

## Goals
- Clarify API responsibilities by moving reporting and settings logic into service modules.
- Reduce duplicated SQL and helper code in API endpoints.
- Remove unused backend methods and unused frontend UI components and deps.

## TODO (completed)
- [x] Add repository query helpers and reporting/settings service modules.
- [x] Simplify summary, daily stats, and dates endpoints to use reporting helpers.
- [x] Consolidate suspicious search and name caching logic.
- [x] Remove unused repository methods.
- [x] Remove unused UI components and Radix dependencies.
- [x] Update lockfile after dependency cleanup.

## Validation
- Backend tests: `py -m pytest`
