import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";

import { server } from "@/test/msw/server";

import { DashboardScreen } from "./dashboard-screen";

describe("DashboardScreen", () => {
  it("renders KPI summary, freshness, and queue", async () => {
    server.use(
      http.get("/api/console/dashboard", () =>
        HttpResponse.json({
          date: "2026-04-05",
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
          case_ranking: [],
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
            queue: { queued: 2, running: 1, failed: 0 },
          },
        }),
      ),
    );

    render(<DashboardScreen viewerRole="analyst" />);

    expect(await screen.findByRole("heading", { name: "検知件数推移" })).toBeInTheDocument();
    expect(screen.getByText("12.4%")).toBeInTheDocument();
    expect(screen.getByText("未対応アラート件数")).toBeInTheDocument();
    expect(screen.getByText("¥428,000")).toBeInTheDocument();
    expect(screen.getByText(/検知結果が最新ではありません/)).toBeInTheDocument();
    expect(screen.getByText(/待機 2 \/ 実行中 1 \/ 失敗 0/)).toBeInTheDocument();
  });

  it("starts refresh and loads job status for admin actions", async () => {
    let dashboardFetchCount = 0;
    let refreshRequestBody: unknown = null;

    server.use(
      http.get("/api/console/dashboard", () => {
        dashboardFetchCount += 1;
        return HttpResponse.json({
          date: "2026-04-05",
          available_dates: ["2026-04-05"],
          kpis: {
            fraud_rate: { value: 12.4, unit: "%" },
            unhandled_alerts: { value: 19, unit: "items" },
            estimated_damage: { value: 428000, unit: "JPY" },
          },
          trend: [{ date: "2026-04-05", alerts: 14 }],
          case_ranking: [],
          quality: {
            findings: {
              stale: false,
              stale_reasons: [],
            },
          },
          job_status_summary: {
            status: "idle",
            message: "idle",
            queue: { queued: 0, running: 0, failed: 0 },
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
          queue: { queued: 1, running: 1, failed: 0 },
        }),
      ),
    );

    const user = userEvent.setup();
    render(<DashboardScreen viewerRole="admin" />);

    expect(await screen.findByText("不正率")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "更新" }));

    await waitFor(() => {
      expect(refreshRequestBody).toEqual({
        hours: 1,
        clicks: true,
        conversions: true,
        detect: true,
      });
    });
    expect(await screen.findByText(/job: run-refresh-1/)).toBeInTheDocument();
    expect(dashboardFetchCount).toBe(1);
  });

  it("starts master sync from the admin action area", async () => {
    let masterSyncCalls = 0;

    server.use(
      http.get("/api/console/dashboard", () =>
        HttpResponse.json({
          date: "2026-04-05",
          available_dates: ["2026-04-05"],
          kpis: {
            fraud_rate: { value: 12.4, unit: "%" },
            unhandled_alerts: { value: 19, unit: "items" },
            estimated_damage: { value: 428000, unit: "JPY" },
          },
          trend: [{ date: "2026-04-05", alerts: 14 }],
          case_ranking: [],
          quality: {
            findings: {
              stale: false,
              stale_reasons: [],
            },
          },
          job_status_summary: {
            status: "idle",
            message: "idle",
            queue: { queued: 0, running: 0, failed: 0 },
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
          queue: { queued: 1, running: 0, failed: 0 },
        }),
      ),
    );

    const user = userEvent.setup();
    render(<DashboardScreen viewerRole="admin" />);

    expect(await screen.findByText("不正率")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "マスター同期" }));

    await waitFor(() => {
      expect(masterSyncCalls).toBe(1);
    });
    expect(await screen.findByText(/マスター同期を開始しました。job: master-sync-1/)).toBeInTheDocument();
    expect(screen.getByText("master-sync-1 (queued)")).toBeInTheDocument();
  });
});
