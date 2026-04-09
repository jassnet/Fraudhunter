# Business Test Scenarios

## Backend

### SC-04 Alerts list honors filters, pagination, and scoped status counts

- Goal: keep triage counts aligned with the rows the operator is currently looking at.
- Input: call the alerts list API with `status`, `risk`, `start_date`, `end_date`, `search`, `page`, and `page_size`.
- Expected: the response returns case-centric rows, pagination metadata, and `status_counts` computed for the same filter scope except for the selected status.
- Primary layer: backend API.
- Covered by: `backend/tests/test_console_api_behavior.py`

### SC-05 Review requires admin role, case keys, and a reason

- Goal: restrict triage mutations to admin users and preserve an auditable reason.
- Input: send a review request with `case_keys`, `status`, and `reason`.
- Expected: analyst users are rejected, admin users receive `requested_count`, `matched_current_count`, `updated_count`, `missing_keys`, and the applied `status`.
- Primary layer: backend API.
- Covered by: `backend/tests/test_console_api_behavior.py`

### SC-06 Refresh only enqueues findings recompute when detection is requested

- Goal: keep ingest-only refresh runs from creating unnecessary findings work.
- Input: execute refresh with and without `detect=true`.
- Expected: only affected dates are enqueued, and `detect=false` performs ingestion without creating findings recompute jobs.
- Primary layer: backend API and backend service.
- Covered by: `backend/tests/test_jobs_behavior.py`, `backend/tests/test_refresh_detect.py`

### SC-07 Console read and write permissions are split by role

- Goal: enforce analyst/admin boundaries on the console surface itself.
- Input: call console endpoints with anonymous, analyst, and admin viewer headers.
- Expected: analysts can read console data, while review, refresh, and master sync mutations remain admin-only.
- Primary layer: backend API.
- Covered by: `backend/tests/test_console_api_behavior.py`

## Frontend

### FC-01 Dashboard shows KPI, freshness, queue summary, and case ranking

- Goal: let operators distinguish stale data from active background processing.
- Input: render the dashboard from the console dashboard payload.
- Expected: KPI cards, freshness timestamps, stale warning state, queue summary, and case ranking are visible.
- Primary layer: frontend component.
- Covered by: `frontend/src/features/console/dashboard-screen.test.tsx`

### FC-02 Dashboard admin actions surface job progress

- Goal: make refresh and master sync actions observable after the click.
- Input: trigger refresh or master sync from the dashboard as an admin user.
- Expected: the UI stores the returned `job_id`, polls job status, and shows queued or running progress until completion.
- Primary layer: frontend component.
- Covered by: `frontend/src/features/console/dashboard-screen.test.tsx`

### FC-03 Alerts list is case-centric and bulk review requires a reason

- Goal: remove client-side grouping accidents and force explicit review context.
- Input: render alerts rows that contain `case_key`, environment data, and affected entity counts, then execute bulk review.
- Expected: each row represents one environment case and bulk review requires a non-empty reason before submission.
- Primary layer: frontend component.
- Covered by: `frontend/src/features/console/alerts-screen.test.tsx`

### FC-04 Alerts filters and pagination stay synchronized with the URL

- Goal: preserve sharable triage links and back/forward navigation.
- Input: change filters and page controls in the alerts view.
- Expected: the URL reflects the active filters, and a reload restores the same query state.
- Primary layer: frontend component.
- Covered by: `frontend/src/features/console/alerts-screen.test.tsx`

### FC-05 Alert detail shows environment, evidence, and review history

- Goal: ensure the detail screen presents the actual suspicious evidence for the selected case.
- Input: open a detail page by `caseKey`.
- Expected: the page shows environment conditions, affected affiliates and programs, evidence transactions, optional affiliate recent transactions, and review history.
- Primary layer: frontend component.
- Covered by: `frontend/src/features/console/alert-detail-screen.test.tsx`

### FC-06 Frontend proxy forwards signed console viewer identity

- Goal: preserve trusted gateway identity from the Next.js server to the backend.
- Input: proxy a console request through the frontend server.
- Expected: the backend request includes signed viewer headers, and missing internal proxy configuration fails closed.
- Primary layer: frontend server unit.
- Covered by: `frontend/src/lib/server/backend-proxy.test.ts`

## Scenario Mapping

| Scenario ID | Primary layer | Coverage |
| --- | --- | --- |
| SC-04 | backend API | `backend/tests/test_console_api_behavior.py` |
| SC-05 | backend API | `backend/tests/test_console_api_behavior.py` |
| SC-06 | backend API / service | `backend/tests/test_jobs_behavior.py`, `backend/tests/test_refresh_detect.py` |
| SC-07 | backend API | `backend/tests/test_console_api_behavior.py` |
| FC-01 | frontend component | `frontend/src/features/console/dashboard-screen.test.tsx` |
| FC-02 | frontend component | `frontend/src/features/console/dashboard-screen.test.tsx` |
| FC-03 | frontend component | `frontend/src/features/console/alerts-screen.test.tsx` |
| FC-04 | frontend component | `frontend/src/features/console/alerts-screen.test.tsx` |
| FC-05 | frontend component | `frontend/src/features/console/alert-detail-screen.test.tsx` |
| FC-06 | frontend server unit | `frontend/src/lib/server/backend-proxy.test.ts` |
