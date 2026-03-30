import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import DashboardPage from "@/app/page";
import { dashboardCopy } from "@/copy/dashboard";
import { API_BASE_URL } from "@/lib/api";
import { ADMIN_REFRESH_LOOKBACK_HOURS } from "@/lib/api/admin-client";
import { buildSummaryResponse } from "@/test/msw/handlers";
import { server } from "@/test/msw/server";

describe("ダッシュボード画面", () => {
  it("最新の対象日と KPI を表示する", async () => {
    render(<DashboardPage />);

    await screen.findByRole("heading", { name: dashboardCopy.title });
    await screen.findByText("対象日 2026-01-21");

    expect(screen.getByText(dashboardCopy.labels.clicks)).toBeInTheDocument();
    expect(screen.getByText(dashboardCopy.labels.conversions)).toBeInTheDocument();
    expect(screen.getAllByText(dashboardCopy.labels.suspiciousClicks).length).toBeGreaterThan(0);
    expect(screen.getByText(dashboardCopy.labels.suspiciousConversions)).toBeInTheDocument();
    expect(screen.getByText(dashboardCopy.labels.diagnostics)).toBeInTheDocument();
  });

  it("admin 権限がないと操作帯を表示しない", async () => {
    render(<DashboardPage />);

    await screen.findByRole("heading", { name: dashboardCopy.title });

    expect(
      screen.queryByRole("button", { name: dashboardCopy.admin.actions.refresh })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: dashboardCopy.admin.actions.masterSync })
    ).not.toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/FC_ADMIN_API_KEY/)).toBeInTheDocument();
    });
  });

  it("admin 権限があると再取得を enqueue して成功後に再読込する", async () => {
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

  it("admin 権限があるとマスタ同期を enqueue できる", async () => {
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

  it("一時的なエラー時に再読込で通常表示へ戻る", async () => {
    let attemptCount = 0;
    server.use(
      http.get(`${API_BASE_URL}/api/summary`, () => {
        attemptCount += 1;
        if (attemptCount <= 3) {
          return HttpResponse.json(
            { detail: "一時的な取得に失敗しました" },
            { status: 500 }
          );
        }
        return HttpResponse.json(buildSummaryResponse("2026-01-21"));
      })
    );

    const user = userEvent.setup();
    render(<DashboardPage />);

    await screen.findByRole("heading", { name: dashboardCopy.states.transientTitle }, { timeout: 4000 });
    expect(screen.getByText("一時的な取得に失敗しました")).toBeInTheDocument();

    await user.click(screen.getAllByRole("button", { name: dashboardCopy.states.retry }).at(-1)!);

    await screen.findByRole("heading", { name: dashboardCopy.title });
    await waitFor(() => {
      expect(screen.queryByText("一時的な取得に失敗しました")).not.toBeInTheDocument();
    });
  });

  it("対象日を切り替えると表示を更新する", async () => {
    const user = userEvent.setup();
    render(<DashboardPage />);

    await screen.findByRole("heading", { name: dashboardCopy.title });
    await screen.findByText("対象日 2026-01-21");

    await user.selectOptions(screen.getByLabelText("対象日"), "2026-01-20");

    await waitFor(() => {
      expect(screen.getByText("対象日 2026-01-20")).toBeInTheDocument();
    });
  });

  it("findings stale をヘッダーに表示する", async () => {
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
});
