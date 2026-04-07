import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";

import { server } from "@/test/msw/server";

import { AlertsScreen } from "./alerts-screen";

describe("AlertsScreen", () => {
  it("defaults to unhandled alerts, shows bulk triage actions, and refreshes after review", async () => {
    let fetchCount = 0;
    let requestedStatus: string | null = null;
    let requestedSort: string | null = null;
    let reviewRequestBody: unknown = null;

    server.use(
      http.get("/api/console/alerts", ({ request }) => {
        fetchCount += 1;
        const url = new URL(request.url);
        requestedStatus = url.searchParams.get("status");
        requestedSort = url.searchParams.get("sort");

        if (fetchCount > 1) {
          return HttpResponse.json({
            available_dates: ["2026-04-05"],
            applied_filters: {
              status: "unhandled",
              start_date: "2026-04-05",
              end_date: "2026-04-05",
              sort: "risk_desc",
            },
            status_counts: {
              unhandled: 0,
              investigating: 1,
              confirmed_fraud: 2,
              white: 0,
            },
            items: [],
            total: 0,
          });
        }

        return HttpResponse.json({
          available_dates: ["2026-04-05", "2026-04-04"],
          applied_filters: {
            status: "unhandled",
            start_date: "2026-04-05",
            end_date: "2026-04-05",
            sort: "risk_desc",
          },
          status_counts: {
            unhandled: 2,
            investigating: 1,
            confirmed_fraud: 4,
            white: 8,
          },
          items: [
            {
              finding_key: "fk-002",
              detected_at: "2026-04-05T09:28:00+09:00",
              affiliate_id: "AFF-200",
              affiliate_name: "alpha-media",
              outcome_type: "口座開設",
              risk_score: 98,
              risk_level: "critical",
              pattern: "同一端末から短時間に大量CV",
              status: "unhandled",
              reward_amount: 52000,
              transaction_count: 11,
            },
            {
              finding_key: "fk-001",
              detected_at: "2026-04-05T08:55:00+09:00",
              affiliate_id: "AFF-145",
              affiliate_name: "beta-traffic",
              outcome_type: "カード申込",
              risk_score: 87,
              risk_level: "high",
              pattern: "CV間隔が平均2.3秒",
              status: "unhandled",
              reward_amount: 36000,
              transaction_count: 7,
            },
          ],
          total: 2,
        });
      }),
      http.post("/api/console/alerts/review", async ({ request }) => {
        reviewRequestBody = await request.json();
        return HttpResponse.json({ updated_count: 2, status: "confirmed_fraud" });
      }),
    );

    const user = userEvent.setup();
    render(<AlertsScreen />);

    expect(await screen.findByRole("heading", { name: "アラート一覧" })).toBeInTheDocument();
    await waitFor(() => {
      expect(requestedStatus).toBe("unhandled");
      expect(requestedSort).toBe("risk_desc");
    });

    expect(screen.getByLabelText("ステータス")).toHaveValue("unhandled");
    expect(screen.getByLabelText("開始日")).toHaveValue("2026-04-05");
    expect(screen.getByLabelText("終了日")).toHaveValue("2026-04-05");

    const rows = screen.getAllByRole("row").slice(1);
    expect(within(rows[0]).getByText("98")).toBeInTheDocument();
    expect(within(rows[0]).getByText("alpha-media")).toBeInTheDocument();
    expect(within(rows[0]).getByText("AFF-200")).toBeInTheDocument();
    expect(within(rows[0]).getByText("¥52,000")).toBeInTheDocument();
    expect(within(rows[1]).getByText("87")).toBeInTheDocument();

    const checkboxes = screen.getAllByRole("checkbox");
    await user.click(checkboxes[1]);
    await user.click(checkboxes[2]);
    await user.click(screen.getByRole("button", { name: "確定不正" }));

    await waitFor(() => {
      expect(reviewRequestBody).toEqual({
        finding_keys: ["fk-002", "fk-001"],
        status: "confirmed_fraud",
      });
    });

    expect(await screen.findByText("対象のアラートはありません。")).toBeInTheDocument();
  });

  it("groups alerts for the same affiliate and detected time behind a collapsible row", async () => {
    server.use(
      http.get("/api/console/alerts", () =>
        HttpResponse.json({
          available_dates: ["2026-04-05"],
          applied_filters: {
            status: "unhandled",
            start_date: "2026-04-05",
            end_date: "2026-04-05",
            sort: "risk_desc",
          },
          status_counts: {
            unhandled: 3,
            investigating: 0,
            confirmed_fraud: 0,
            white: 0,
          },
          items: [
            {
              finding_key: "fk-201",
              detected_at: "2026-04-05T09:28:00+09:00",
              affiliate_id: "AFF-200",
              affiliate_name: "alpha-media",
              outcome_type: "口座開設",
              risk_score: 98,
              risk_level: "critical",
              pattern: "同一端末から短時間に大量CV",
              status: "unhandled",
              reward_amount: 52000,
              transaction_count: 11,
            },
            {
              finding_key: "fk-202",
              detected_at: "2026-04-05T09:28:00+09:00",
              affiliate_id: "AFF-200",
              affiliate_name: "alpha-media",
              outcome_type: "カード申込",
              risk_score: 92,
              risk_level: "critical",
              pattern: "CV間隔が平均2.3秒",
              status: "unhandled",
              reward_amount: 36000,
              transaction_count: 7,
            },
            {
              finding_key: "fk-203",
              detected_at: "2026-04-05T08:55:00+09:00",
              affiliate_id: "AFF-145",
              affiliate_name: "beta-traffic",
              outcome_type: "カード申込",
              risk_score: 87,
              risk_level: "high",
              pattern: "直近7日平均の6.2倍の急増",
              status: "unhandled",
              reward_amount: 12000,
              transaction_count: 3,
            },
          ],
          total: 3,
        }),
      ),
    );

    const user = userEvent.setup();
    render(<AlertsScreen />);

    expect(await screen.findByText("alpha-media")).toBeInTheDocument();
    expect(screen.getByText("同時刻に 2 件のアラート")).toBeInTheDocument();
    expect(screen.getByText("¥88,000")).toBeInTheDocument();
    expect(screen.queryByText("CV間隔が平均2.3秒")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "2件を展開" }));

    expect(await screen.findByText("CV間隔が平均2.3秒")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /alpha-media/i })).toHaveLength(2);
  });
});
