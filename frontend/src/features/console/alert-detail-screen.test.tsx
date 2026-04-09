import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";

import { server } from "@/test/msw/server";

import { AlertDetailScreen } from "./alert-detail-screen";

describe("AlertDetailScreen", () => {
  it("shows evidence, transactions, reward source, and review actions", async () => {
    let reviewRequestBody: unknown = null;

    server.use(
      http.get("/api/console/alerts/fk-001", () =>
        HttpResponse.json({
          finding_key: "fk-001",
          affiliate_id: "AFF-145",
          affiliate_name: "beta-traffic",
          risk_score: 96,
          risk_level: "critical",
          status: "unhandled",
          reward_amount: 36000,
          reward_amount_source: "fallback_default",
          reward_amount_is_estimated: true,
          detected_at: "2026-04-05T08:55:00+09:00",
          outcome_type: "Program B",
          program_name: "クレジットカード",
          reasons: [
            "同一IPから24時間で47件のCV",
            "CV間隔が極端に短い",
            "同日中に複数端末から発生",
          ],
          transactions: [
            {
              transaction_id: "tx-981",
              occurred_at: "2026-04-05T08:52:03+09:00",
              outcome_type: "Program B",
              reward_amount: 6000,
              state: "approved",
            },
            {
              transaction_id: "tx-977",
              occurred_at: "2026-04-05T08:49:38+09:00",
              outcome_type: "Program B",
              reward_amount: 6000,
              state: "pending",
            },
          ],
          actions: ["confirmed_fraud", "white", "investigating"],
        }),
      ),
      http.post("/api/console/alerts/review", async ({ request }) => {
        reviewRequestBody = await request.json();
        return HttpResponse.json({ updated_count: 1, status: "investigating" });
      }),
    );

    const user = userEvent.setup();
    render(<AlertDetailScreen findingKey="fk-001" viewerRole="admin" />);

    expect(await screen.findByRole("heading", { name: "アラート詳細" })).toBeInTheDocument();
    expect(screen.getByText("beta-traffic")).toBeInTheDocument();
    expect(screen.getByText("ID: AFF-145")).toBeInTheDocument();
    expect(screen.getByText("96")).toBeInTheDocument();
    expect(screen.getByText("未対応")).toBeInTheDocument();
    expect(screen.getAllByText("既定単価から推定")).toHaveLength(2);
    expect(screen.getByText("同一IPから24時間で47件のCV")).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "関連取引" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "調査中にする" }));

    await waitFor(() => {
      expect(reviewRequestBody).toEqual({
        finding_keys: ["fk-001"],
        status: "investigating",
      });
    });

    expect(await screen.findByText("判定状態を更新しました。")).toBeInTheDocument();
    expect(await screen.findByText("調査中")).toBeInTheDocument();
  });
});
