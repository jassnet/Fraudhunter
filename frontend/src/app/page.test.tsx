import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import DashboardPage from "@/app/page";
import { dashboardCopy } from "@/features/dashboard/copy";
import { API_BASE_URL } from "@/lib/api";
import { ADMIN_REFRESH_LOOKBACK_HOURS } from "@/lib/api/admin-client";
import { buildSummaryResponse } from "@/test/msw/handlers";
import { server } from "@/test/msw/server";

describe("Dashboard page", () => {
  it("shows the latest target date and KPIs", async () => {
    render(<DashboardPage />);

    await screen.findByRole("heading", { name: dashboardCopy.title });
    await screen.findByText(dashboardCopy.targetDateLabel("2026-01-21"));

    expect(screen.getAllByText(dashboardCopy.labels.clicks)[0]).toBeInTheDocument();
    expect(screen.getAllByText(dashboardCopy.labels.conversions)[0]).toBeInTheDocument();
    expect(screen.getAllByText(dashboardCopy.labels.suspiciousConversions)[0]).toBeInTheDocument();
    expect(screen.getByText(dashboardCopy.labels.chart)).toBeInTheDocument();
  });

  it("preserves the selected date in the fraud findings link", async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      expect(document.querySelector('a[href="/suspicious/fraud?date=2026-01-21"]')).not.toBeNull();
    });
  });

  it("hides admin actions when admin access is unavailable", async () => {
    render(<DashboardPage />);

    await screen.findByRole("heading", { name: dashboardCopy.title });

    expect(
      screen.queryByRole("button", { name: dashboardCopy.admin.actions.refresh })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: dashboardCopy.admin.actions.masterSync })
    ).not.toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(dashboardCopy.admin.unavailableShortHint)).toBeInTheDocument();
    });
  });

  it("enqueues refresh for admin users and reloads the summary after success", async () => {
    let summaryCalls = 0;
    let statusCalls = 0;
    let refreshPayload: Record<string, unknown> | null = null;

    server.use(
      http.get("*/api/admin/job-status", () => {
        statusCalls += 1;
        if (statusCalls === 1) {
          return HttpResponse.json({
            status: "idle",
            message: "idle",
            job_id: null,
            result: null,
          });
        }

        if (statusCalls === 2) {
          return HttpResponse.json({
            status: "running",
            message: "running",
            job_id: "job-refresh-1",
            result: null,
          });
        }

        return HttpResponse.json({
          status: "completed",
          message: "completed",
          job_id: "job-refresh-1",
          result: { success: true },
        });
      }),
      http.post("*/api/admin/refresh", async ({ request }) => {
        refreshPayload = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({
          success: true,
          details: {
            job_id: "job-refresh-1",
          },
        });
      }),
      http.get(`${API_BASE_URL}/api/summary`, ({ request }) => {
        summaryCalls += 1;
        const url = new URL(request.url);
        const targetDate = url.searchParams.get("target_date") || "2026-01-21";
        return HttpResponse.json(buildSummaryResponse(targetDate));
      })
    );

    const user = userEvent.setup();
    render(<DashboardPage />);

    await screen.findByRole("button", { name: dashboardCopy.admin.actions.refresh });
    await user.click(screen.getByRole("button", { name: dashboardCopy.admin.actions.refresh }));

    await screen.findByText(dashboardCopy.admin.feedback.refresh.queued);
    await waitFor(() => {
      expect(screen.getByText(dashboardCopy.admin.feedback.refresh.running)).toBeInTheDocument();
    }, { timeout: 4000 });
    await waitFor(() => {
      expect(screen.getByText(dashboardCopy.admin.feedback.refresh.succeeded)).toBeInTheDocument();
    }, { timeout: 4000 });

    expect(refreshPayload).toEqual({
      hours: ADMIN_REFRESH_LOOKBACK_HOURS,
      clicks: true,
      conversions: true,
      detect: true,
    });

    await waitFor(() => {
      expect(summaryCalls).toBe(2);
    });
  });

  it("enqueues master sync for admin users", async () => {
    let statusCalls = 0;
    let masterSyncCalls = 0;

    server.use(
      http.get("*/api/admin/job-status", () => {
        statusCalls += 1;
        if (statusCalls === 1) {
          return HttpResponse.json({
            status: "idle",
            message: "idle",
            job_id: null,
            result: null,
          });
        }

        return HttpResponse.json({
          status: "completed",
          message: "completed",
          job_id: "job-master-sync-1",
          result: { success: true },
        });
      }),
      http.post("*/api/admin/master-sync", () => {
        masterSyncCalls += 1;
        return HttpResponse.json({
          success: true,
          details: {
            job_id: "job-master-sync-1",
          },
        });
      })
    );

    const user = userEvent.setup();
    render(<DashboardPage />);

    await screen.findByRole("button", { name: dashboardCopy.admin.actions.masterSync });
    await user.click(screen.getByRole("button", { name: dashboardCopy.admin.actions.masterSync }));

    await screen.findByText(dashboardCopy.admin.feedback.masterSync.queued);
    await waitFor(() => {
      expect(screen.getByText(dashboardCopy.admin.feedback.masterSync.succeeded)).toBeInTheDocument();
    }, { timeout: 4000 });
    expect(masterSyncCalls).toBe(1);
  });

  it("returns to the normal view after a transient error and manual retry", async () => {
    let attemptCount = 0;
    const transientMessage = "temporary summary failure";

    server.use(
      http.get(`${API_BASE_URL}/api/summary`, () => {
        attemptCount += 1;
        if (attemptCount <= 3) {
          return HttpResponse.json({ detail: transientMessage }, { status: 500 });
        }

        return HttpResponse.json(buildSummaryResponse("2026-01-21"));
      })
    );

    const user = userEvent.setup();
    render(<DashboardPage />);

    await screen.findByRole("heading", { name: dashboardCopy.states.transientTitle }, { timeout: 4000 });
    expect(screen.getByText(transientMessage)).toBeInTheDocument();

    await user.click(screen.getAllByRole("button", { name: dashboardCopy.states.retry }).at(-1)!);

    await screen.findByRole("heading", { name: dashboardCopy.title });
    await waitFor(() => {
      expect(screen.queryByText(transientMessage)).not.toBeInTheDocument();
    });
  });

  it("updates the dashboard when the target date changes", async () => {
    const user = userEvent.setup();
    render(<DashboardPage />);

    await screen.findByRole("heading", { name: dashboardCopy.title });
    await screen.findByText(dashboardCopy.targetDateLabel("2026-01-21"));

    await user.selectOptions(screen.getByLabelText("対象日"), "2026-01-20");

    await waitFor(() => {
      expect(screen.getByText(dashboardCopy.targetDateLabel("2026-01-20"))).toBeInTheDocument();
    });
  });

  it("shows the stale findings warning in the header", async () => {
    server.use(
      http.get(`${API_BASE_URL}/api/summary`, ({ request }) => {
        const url = new URL(request.url);
        const targetDate = url.searchParams.get("target_date") || "2026-01-21";
        return HttpResponse.json({
          ...buildSummaryResponse(targetDate),
          quality: {
            findings: {
              stale: true,
              findings_last_computed_at: "2026-01-21T09:00:00Z",
              stale_reasons: ["findings lagging behind raw ingest"],
            },
          },
        });
      })
    );

    render(<DashboardPage />);

    await screen.findByRole("heading", { name: dashboardCopy.title });
    expect(screen.getByText(dashboardCopy.states.staleTitle)).toBeInTheDocument();
  });

  it("uses the backend-resolved target date on the initial load", async () => {
    server.use(
      http.get(`${API_BASE_URL}/api/dates`, () => {
        return HttpResponse.json({ dates: ["2026-01-22", "2026-01-21", "2026-01-20"] });
      }),
      http.get(`${API_BASE_URL}/api/summary`, ({ request }) => {
        const url = new URL(request.url);
        const targetDate = url.searchParams.get("target_date");
        if (targetDate) {
          return HttpResponse.json(buildSummaryResponse(targetDate));
        }
        return HttpResponse.json(buildSummaryResponse("2026-01-21"));
      }),
      http.get(`${API_BASE_URL}/api/stats/daily`, ({ request }) => {
        const url = new URL(request.url);
        return HttpResponse.json({
          data: [
            {
              date: url.searchParams.get("target_date") || "missing",
              clicks: 1,
              conversions: 1,
              suspicious_conversions: 0,
              fraud_findings: 0,
            },
          ],
        });
      })
    );

    render(<DashboardPage />);

    await screen.findByText(dashboardCopy.targetDateLabel("2026-01-21"));
    await waitFor(() => {
      expect(screen.getByDisplayValue("2026-01-21")).toBeInTheDocument();
    });
  });
});
