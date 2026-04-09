import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { afterEach, describe, expect, it, vi } from "vitest";

import { server } from "@/test/msw/server";

import { AlertDetailScreen } from "./alert-detail-screen";

describe("AlertDetailScreen", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows evidence transactions, review history, and review actions", async () => {
    let reviewRequestBody: unknown = null;

    server.use(
      http.get("/api/console/alerts/case-001", () =>
        HttpResponse.json({
          case_key: "case-001",
          finding_key: "fk-001",
          environment: {
            date: "2026-04-05",
            ipaddress: "203.0.113.10",
            useragent: "Mozilla/5.0 Chrome/123.0",
          },
          affected_affiliate_count: 2,
          affected_affiliates: [
            { id: "AFF-145", name: "beta-traffic" },
            { id: "AFF-146", name: "gamma-traffic" },
          ],
          affected_program_count: 1,
          affected_programs: [{ id: "PRG-2", name: "Program B" }],
          risk_score: 96,
          risk_level: "critical",
          status: "unhandled",
          reward_amount: 36000,
          reward_amount_source: "fallback_default",
          reward_amount_is_estimated: true,
          latest_detected_at: "2026-04-05T08:55:00+09:00",
          primary_reason: "shared-ip-pattern",
          reasons: ["shared-ip-pattern", "burst-conversion-pattern"],
          evidence_transactions: [
            {
              transaction_id: "tx-981",
              occurred_at: "2026-04-05T08:52:03+09:00",
              outcome_type: "Program B",
              program_name: "Program B",
              reward_amount: 6000,
              state: "approved",
              affiliate_id: "AFF-145",
              affiliate_name: "beta-traffic",
            },
          ],
          affiliate_recent_transactions: [
            {
              transaction_id: "tx-977",
              occurred_at: "2026-04-05T08:49:38+09:00",
              outcome_type: "Program B",
              program_name: "Program B",
              reward_amount: 6000,
              state: "pending",
              affiliate_id: "AFF-145",
              affiliate_name: "beta-traffic",
            },
          ],
          review_history: [
            {
              status: "investigating",
              reason: "initial review",
              reviewed_by: "admin-user",
              reviewed_role: "admin",
              source_surface: "console",
              request_id: "req-1",
              reviewed_at: "2026-04-05T09:10:00+09:00",
            },
          ],
          actions: ["confirmed_fraud", "white", "investigating"],
        }),
      ),
      http.post("/api/console/alerts/review", async ({ request }) => {
        reviewRequestBody = await request.json();
        return HttpResponse.json({
          requested_count: 1,
          matched_current_count: 1,
          updated_count: 1,
          missing_keys: [],
          status: "investigating",
        });
      }),
    );

    const user = userEvent.setup();
    render(<AlertDetailScreen caseKey="case-001" viewerRole="admin" />);

    expect(await screen.findByRole("heading", { name: "Alert detail" })).toBeInTheDocument();
    expect(screen.getByText("203.0.113.10")).toBeInTheDocument();
    expect(screen.getByText("beta-traffic (AFF-145)")).toBeInTheDocument();
    expect(screen.getByText("96")).toBeInTheDocument();
    expect(screen.getAllByText("Estimated from default")).toHaveLength(2);
    expect(screen.getByRole("table", { name: "evidence transactions" })).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "review history" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Mark investigating" }));
    const dialog = screen.getByRole("dialog", { name: "Review reason" });
    expect(dialog).toBeInTheDocument();
    await user.type(screen.getByLabelText("Reason"), "detail review reason");
    await user.click(within(dialog).getByRole("button", { name: "Mark investigating" }));

    await waitFor(() => {
      expect(reviewRequestBody).toEqual({
        case_keys: ["case-001"],
        status: "investigating",
        reason: "detail review reason",
      });
    });

    expect(await screen.findByText("Updated 1 case.")).toBeInTheDocument();
  });
});
