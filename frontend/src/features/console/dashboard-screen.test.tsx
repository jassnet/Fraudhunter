import { render, screen } from "@testing-library/react";
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

    render(<DashboardScreen />);

    expect(screen.getByText("読み込み中...")).toBeInTheDocument();
    expect(await screen.findByText("全体フラウド率")).toBeInTheDocument();
    expect(screen.getByText("12.4%")).toBeInTheDocument();
    expect(screen.getByText("未対応アラート件数")).toBeInTheDocument();
    expect(screen.getByText("19件")).toBeInTheDocument();
    expect(screen.getByText("被害推定額")).toBeInTheDocument();
    expect(screen.getByText("¥428,000")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "検知件数推移" })).toBeInTheDocument();
    expect(
      screen.getByRole("table", { name: "フラウド率ランキング" }),
    ).toBeInTheDocument();
    expect(screen.getByText("alpha-media")).toBeInTheDocument();
    expect(screen.getByText("36.7%")).toBeInTheDocument();
  });
});
