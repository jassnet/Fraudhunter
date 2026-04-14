import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ConsoleDisplayModeProvider } from "@/components/console-display-mode";
import { server } from "@/test/msw/server";

import { DashboardScreen } from "./dashboard-screen";

const replaceMock = vi.fn();

vi.mock("next/navigation", () => ({
  usePathname: () => "/dashboard",
  useRouter: () => ({
    replace: replaceMock,
  }),
}));

describe("DashboardScreen", () => {
  function renderWithDisplayMode(showAdvanced = false) {
    render(
      <ConsoleDisplayModeProvider initialShowAdvanced={showAdvanced}>
        <DashboardScreen />
      </ConsoleDisplayModeProvider>,
    );
  }

  beforeEach(() => {
    replaceMock.mockReset();
  });

  it("renders KPI summary, date selector, review outcomes, and failed jobs", async () => {
    server.use(
      http.get("/api/console/dashboard", () =>
        HttpResponse.json({
          target_date: "2026-04-05",
          available_dates: ["2026-04-05", "2026-04-04"],
          kpis: {
            fraud_rate: { value: 12.4, unit: "%" },
            unhandled_alerts: { value: 19, unit: "items" },
            estimated_damage: { value: 428000, unit: "JPY" },
          },
          trend: [
            { date: "2026-04-03", alerts: 9 },
            { date: "2026-04-04", alerts: 12 },
            { date: "2026-04-05", alerts: 14 },
          ],
          review_outcomes: {
            confirmed_fraud: 5,
            white: 2,
            investigating: 3,
            reviewed_total: 7,
            confirmed_ratio: 71.4,
          },
          operations: {
            oldest_unhandled_days: 4,
            stale_unhandled_count: 2,
            failed_jobs: [
              {
                job_id: "job-failed-1",
                job_type: "refresh_findings",
                message: "failed",
                error_message: "database timeout",
                finished_at: "2026-04-05T07:40:00+09:00",
              },
            ],
            schedules: [
              {
                key: "refresh_latest",
                label: "最新データ再取得",
                description: "毎時実行",
                next_run_at: "2026-04-05T10:00:00+09:00",
              },
            ],
          },
          quality: {
            last_successful_ingest_at: "2026-04-05T09:05:00+09:00",
            findings: {
              findings_last_computed_at: "2026-04-05T09:10:00+09:00",
              stale: true,
              stale_reasons: ["conversion_source_advanced"],
            },
            master_sync: {
              last_synced_at: "2026-04-05T08:00:00+09:00",
            },
          },
          job_status_summary: {
            status: "running",
            job_id: "job-123",
            message: "processing",
            queue: { queued: 2, retry_scheduled: 1, running: 1, failed: 0 },
          },
        }),
      ),
    );

    renderWithDisplayMode();

    expect(await screen.findByRole("heading", { name: "ダッシュボード" })).toBeInTheDocument();
    expect(screen.getByLabelText("日付")).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "2026/04/05" })).toBeInTheDocument();
    expect(screen.getByText("12.4%")).toBeInTheDocument();
    expect(screen.getByText("未対応アラート件数")).toBeInTheDocument();
    expect(screen.getByText("¥428,000")).toBeInTheDocument();
    expect(screen.getByText(/検知結果が最新ではありません/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "判定結果の内訳" })).toBeInTheDocument();
    expect(screen.getByText("71.4%")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "優先的に確認すべきケース" })).not.toBeInTheDocument();
  });

  it("updates the URL when a target date is selected", async () => {
    server.use(
      http.get("/api/console/dashboard", () =>
        HttpResponse.json({
          target_date: "2026-04-05",
          available_dates: ["2026-04-05", "2026-04-04"],
          kpis: {
            fraud_rate: { value: 10.1, unit: "%" },
            unhandled_alerts: { value: 3, unit: "items" },
            estimated_damage: { value: 12000, unit: "JPY" },
          },
          trend: [{ date: "2026-04-05", alerts: 3 }],
          review_outcomes: {
            confirmed_fraud: 1,
            white: 0,
            investigating: 1,
            reviewed_total: 1,
            confirmed_ratio: 100,
          },
          operations: {
            oldest_unhandled_days: 1,
            stale_unhandled_count: 0,
            failed_jobs: [],
            schedules: [],
          },
          quality: {
            findings: {
              stale: false,
              stale_reasons: [],
            },
          },
          job_status_summary: {
            status: "idle",
            message: "idle",
            queue: { queued: 0, retry_scheduled: 0, running: 0, failed: 0 },
          },
        }),
      ),
    );

    const user = userEvent.setup();
    renderWithDisplayMode();

    expect(await screen.findByRole("heading", { name: "ダッシュボード" })).toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText("日付"), "2026-04-04");

    expect(replaceMock).toHaveBeenCalledWith("/dashboard?target_date=2026-04-04", { scroll: false });
  });

  it("starts refresh and loads job status for admin actions", async () => {
    let dashboardFetchCount = 0;
    let refreshRequestBody: unknown = null;

    server.use(
      http.get("/api/console/dashboard", () => {
        dashboardFetchCount += 1;
        return HttpResponse.json({
          target_date: "2026-04-05",
          available_dates: ["2026-04-05"],
          kpis: {
            fraud_rate: { value: 12.4, unit: "%" },
            unhandled_alerts: { value: 19, unit: "items" },
            estimated_damage: { value: 428000, unit: "JPY" },
          },
          trend: [{ date: "2026-04-05", alerts: 14 }],
          review_outcomes: {
            confirmed_fraud: 1,
            white: 0,
            investigating: 2,
            reviewed_total: 1,
            confirmed_ratio: 100,
          },
          operations: {
            oldest_unhandled_days: 1,
            stale_unhandled_count: 0,
            failed_jobs: [],
            schedules: [],
          },
          quality: {
            findings: {
              stale: false,
              stale_reasons: [],
            },
          },
          job_status_summary: {
            status: "idle",
            message: "idle",
            queue: { queued: 0, retry_scheduled: 0, running: 0, failed: 0 },
          },
        });
      }),
      http.post("/api/console/refresh", async ({ request }) => {
        refreshRequestBody = await request.json();
        return HttpResponse.json({
          success: true,
          message: "started",
          details: { job_id: "run-refresh-1", hours: 1, clicks: true, conversions: true },
        });
      }),
      http.get("/api/console/job-status/run-refresh-1", () =>
        HttpResponse.json({
          status: "running",
          job_id: "run-refresh-1",
          message: "processing",
          queue: { queued: 1, retry_scheduled: 0, running: 1, failed: 0 },
        }),
      ),
    );

    const user = userEvent.setup();
    renderWithDisplayMode(true);

    expect(await screen.findByText("データ再取得")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "データ再取得" }));

    await waitFor(() => {
      expect(refreshRequestBody).toEqual({
        hours: 1,
        clicks: true,
        conversions: true,
        detect: true,
      });
    });
    expect(await screen.findByText(/最新データの反映を開始しました/)).toBeInTheDocument();
    expect(dashboardFetchCount).toBe(1);
  });

  it("starts master sync from the action area", async () => {
    let masterSyncCalls = 0;

    server.use(
      http.get("/api/console/dashboard", () =>
        HttpResponse.json({
          target_date: "2026-04-05",
          available_dates: ["2026-04-05"],
          kpis: {
            fraud_rate: { value: 12.4, unit: "%" },
            unhandled_alerts: { value: 19, unit: "items" },
            estimated_damage: { value: 428000, unit: "JPY" },
          },
          trend: [{ date: "2026-04-05", alerts: 14 }],
          review_outcomes: {
            confirmed_fraud: 1,
            white: 0,
            investigating: 2,
            reviewed_total: 1,
            confirmed_ratio: 100,
          },
          operations: {
            oldest_unhandled_days: 1,
            stale_unhandled_count: 0,
            failed_jobs: [],
            schedules: [],
          },
          quality: {
            findings: {
              stale: false,
              stale_reasons: [],
            },
          },
          job_status_summary: {
            status: "idle",
            message: "idle",
            queue: { queued: 0, retry_scheduled: 0, running: 0, failed: 0 },
          },
        }),
      ),
      http.post("/api/console/sync/masters", () => {
        masterSyncCalls += 1;
        return HttpResponse.json({
          success: true,
          message: "started",
          details: { job_id: "master-sync-1" },
        });
      }),
      http.get("/api/console/job-status/master-sync-1", () =>
        HttpResponse.json({
          status: "queued",
          job_id: "master-sync-1",
          message: "queued",
          queue: { queued: 1, retry_scheduled: 0, running: 0, failed: 0 },
        }),
      ),
    );

    const user = userEvent.setup();
    renderWithDisplayMode(true);

    expect(await screen.findByText("基本データ同期")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "基本データ同期" }));

    await waitFor(() => {
      expect(masterSyncCalls).toBe(1);
    });
    expect(await screen.findByText(/基本データの同期を開始しました/)).toBeInTheDocument();
    expect(screen.getByText("master-sync-1（queued）")).toBeInTheDocument();
  });
});
