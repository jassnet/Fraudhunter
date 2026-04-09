import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";

import { server } from "@/test/msw/server";

import { DashboardScreen } from "./dashboard-screen";

describe("DashboardScreen", () => {
  it("renders the KPI summary, trend chart, and affiliate ranking", async () => {
    server.use(
      http.get("/api/console/dashboard", () =>
        HttpResponse.json({
          date: "2026-04-05",
          available_dates: ["2026-04-05", "2026-04-04"],
          kpis: {
            fraud_rate: { value: 12.4, unit: "%" },
            unhandled_alerts: { value: 19, unit: "件" },
            estimated_damage: { value: 428000, unit: "円" },
          },
          trend: [
            { date: "2026-03-30", alerts: 3 },
            { date: "2026-03-31", alerts: 4 },
            { date: "2026-04-01", alerts: 8 },
            { date: "2026-04-02", alerts: 10 },
            { date: "2026-04-03", alerts: 9 },
            { date: "2026-04-04", alerts: 12 },
            { date: "2026-04-05", alerts: 14 },
          ],
          ranking: [
            {
              affiliate_id: "AFF-2001",
              affiliate_name: "alpha-media",
              fraud_rate: 36.7,
              alert_count: 5,
              total_conversions: 49,
              estimated_damage: 162000,
            },
            {
              affiliate_id: "AFF-1188",
              affiliate_name: "beta-traffic",
              fraud_rate: 28.1,
              alert_count: 4,
              total_conversions: 48,
              estimated_damage: 94000,
            },
          ],
        }),
      ),
    );

    render(<DashboardScreen viewerRole="analyst" />);
    expect(screen.getByRole("link", { name: "アラート一覧" })).toHaveAttribute("href", "/alerts");

    expect(screen.getByText("読み込み中...")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "検知件数推移" })).toBeInTheDocument();
    expect(screen.getByText("12.4%")).toBeInTheDocument();
    expect(screen.getByText("未対応アラート数")).toBeInTheDocument();
    expect(screen.getByText("19件")).toBeInTheDocument();
    expect(screen.getAllByText("想定被害額")).toHaveLength(2);
    expect(screen.getByText("¥428,000")).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "不正率ランキング" })).toBeInTheDocument();
    expect(screen.getByText("alpha-media")).toBeInTheDocument();
    expect(screen.getByText("36.7%")).toBeInTheDocument();
  });

  it("runs the latest-data refresh when the admin update button is pressed", async () => {
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
            unhandled_alerts: { value: 19, unit: "件" },
            estimated_damage: { value: 428000, unit: "円" },
          },
          trend: [{ date: "2026-04-05", alerts: 14 }],
          ranking: [],
        });
      }),
      http.post("/api/console/refresh", async ({ request }) => {
        refreshRequestBody = await request.json();
        return HttpResponse.json({
          success: true,
          message: "最新データの取り込みジョブを起動しました",
          details: { job_id: "run-refresh-1", hours: 1, clicks: true, conversions: true },
        });
      }),
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
    await waitFor(() => {
      expect(dashboardFetchCount).toBe(2);
    });
    expect(await screen.findByText("最新データの取り込みを開始しました。反映まで少々お待ちください。")).toBeInTheDocument();
  });

  it("runs master sync from the admin action area", async () => {
    let masterSyncCalls = 0;

    server.use(
      http.get("/api/console/dashboard", () =>
        HttpResponse.json({
          date: "2026-04-05",
          available_dates: ["2026-04-05"],
          kpis: {
            fraud_rate: { value: 12.4, unit: "%" },
            unhandled_alerts: { value: 19, unit: "件" },
            estimated_damage: { value: 428000, unit: "円" },
          },
          trend: [{ date: "2026-04-05", alerts: 14 }],
          ranking: [],
        }),
      ),
      http.post("/api/console/sync/masters", () => {
        masterSyncCalls += 1;
        return HttpResponse.json({
          success: true,
          message: "マスターデータ同期ジョブを起動しました",
          details: { job_id: "master-sync-1" },
        });
      }),
    );

    const user = userEvent.setup();
    render(<DashboardScreen viewerRole="admin" />);

    expect(await screen.findByText("不正率")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "広告主・案件データを更新" }));

    await waitFor(() => {
      expect(masterSyncCalls).toBe(1);
    });
    expect(await screen.findByText("広告主・案件データの更新を開始しました。反映まで数分待ってから確認してください。")).toBeInTheDocument();
  });
});
