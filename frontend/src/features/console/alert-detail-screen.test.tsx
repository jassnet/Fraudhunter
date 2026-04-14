import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ConsoleDisplayModeProvider } from "@/components/console-display-mode";
import { server } from "@/test/msw/server";

import { AlertDetailScreen } from "./alert-detail-screen";

describe("AlertDetailScreen", () => {
  function renderWithDisplayMode(showAdvanced = false, returnTo?: string) {
    render(
      <ConsoleDisplayModeProvider initialShowAdvanced={showAdvanced}>
        <AlertDetailScreen caseKey="case-001" viewerUserId="admin-user" returnTo={returnTo} />
      </ConsoleDisplayModeProvider>,
    );
  }

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows evidence transactions, related cases, review history, and review actions", async () => {
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
          risk_level: "high",
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
              state: "承認 (1)",
              state_raw: "1",
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
              state: "保留 (0)",
              state_raw: "0",
              affiliate_id: "AFF-145",
              affiliate_name: "beta-traffic",
            },
          ],
          affiliate_recent_scope: {
            id: "AFF-145",
            name: "beta-traffic",
          },
          review_history: [
            {
              status: "investigating",
              reason: "initial review",
              reviewed_by: "admin-user",
              source_surface: "console",
              request_id: "req-1",
              reviewed_at: "2026-04-05T09:10:00+09:00",
            },
          ],
          assignee: {
            user_id: "admin-user",
            assigned_at: "2026-04-05T09:00:00+09:00",
          },
          follow_up_tasks: [
            {
              id: "task-1",
              task_type: "payout_hold",
              label: "支払保留を実施",
              status: "open",
              created_by: "admin-user",
              created_at: "2026-04-05T09:05:00+09:00",
              due_at: "2026-04-05T10:05:00+09:00",
              is_overdue: false,
            },
          ],
          related_cases: [
            {
              case_key: "case-older",
              display_label: "beta-traffic / Program B / shared-ip-pattern",
              secondary_label: "2026-04-04 / shared-ip-pattern",
              status: "investigating",
              risk_score: 78,
              risk_level: "high",
              latest_detected_at: "2026-04-04T08:55:00+09:00",
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
      http.post("/api/console/alerts/assign", () =>
        HttpResponse.json({
          updated_count: 1,
          action: "claim",
        }),
      ),
      http.post("/api/console/alerts/follow-up", () =>
        HttpResponse.json({
          id: "task-1",
          task_type: "payout_hold",
          label: "支払保留を実施",
          status: "completed",
          created_by: "admin-user",
          created_at: "2026-04-05T09:05:00+09:00",
          due_at: "2026-04-05T10:05:00+09:00",
          is_overdue: false,
          completed_by: "admin-user",
          completed_at: "2026-04-05T09:30:00+09:00",
        }),
      ),
    );

    const user = userEvent.setup();
    renderWithDisplayMode(true, "/alerts?status=investigating&page=2");

    expect(await screen.findByRole("heading", { name: "アラート詳細" })).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "アラート一覧に戻る" })[0]).toHaveAttribute(
      "href",
      "/alerts?status=investigating&page=2",
    );
    expect(screen.getAllByText(/203\.0\.113\.10/).length).toBeGreaterThan(0);
    const affiliateBlock = screen.getByRole("heading", { name: "対象アフィリエイト" }).parentElement;
    expect(affiliateBlock).not.toBeNull();
    expect(within(affiliateBlock!).getByRole("link", { name: "beta-traffic" })).toBeInTheDocument();
    expect(within(affiliateBlock!).getByText("AFF-145")).toBeInTheDocument();
    expect(screen.getByText("承認 (1)")).toBeInTheDocument();
    expect(screen.getByText("保留 (0)")).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "根拠となる成果データ" })).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "判定履歴" })).toBeInTheDocument();
    expect(screen.getByText("支払保留を実施")).toBeInTheDocument();
    expect(screen.getByText("過去30日の関連ケース")).toBeInTheDocument();
    expect(screen.getByText(/期限：2026\/04\/05 10:05/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /beta-traffic \/ Program B \/ shared-ip-pattern/ })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /beta-traffic \/ Program B \/ shared-ip-pattern/ })).toHaveAttribute(
      "href",
      "/alerts/case-older?returnTo=%2Falerts%3Fstatus%3Dinvestigating%26page%3D2",
    );

    await user.click(screen.getByRole("button", { name: "調査中へ変更" }));
    const dialog = screen.getByRole("dialog", { name: "判定理由の入力" });
    expect(dialog).toBeInTheDocument();
    await user.type(screen.getByLabelText("理由"), "detail review reason");
    await user.click(within(dialog).getByRole("button", { name: "この内容で調査中に変更" }));

    await waitFor(() => {
      expect(reviewRequestBody).toEqual({
        case_keys: ["case-001"],
        status: "investigating",
        reason: "detail review reason",
      });
    });

    expect(await screen.findByText("1件のケースを更新しました。")).toBeInTheDocument();
  });

  it("opens the review dialog from keyboard shortcuts", async () => {
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
          affected_affiliate_count: 1,
          affected_affiliates: [{ id: "AFF-145", name: "beta-traffic" }],
          affected_program_count: 1,
          affected_programs: [{ id: "PRG-2", name: "Program B" }],
          risk_score: 88,
          risk_level: "high",
          status: "unhandled",
          reward_amount: 36000,
          reward_amount_source: "fallback_default",
          reward_amount_is_estimated: true,
          latest_detected_at: "2026-04-05T08:55:00+09:00",
          primary_reason: "shared-ip-pattern",
          reasons: ["shared-ip-pattern"],
          evidence_transactions: [],
          affiliate_recent_transactions: [],
          affiliate_recent_scope: null,
          review_history: [],
          assignee: null,
          follow_up_tasks: [],
          related_cases: [],
          actions: ["confirmed_fraud", "white", "investigating"],
        }),
      ),
    );

    const user = userEvent.setup();
    renderWithDisplayMode();

    expect(await screen.findByRole("heading", { name: "アラート詳細" })).toBeInTheDocument();
    await user.keyboard("f");

    expect(screen.getByRole("dialog", { name: "判定理由の入力" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "この内容で不正確定" })).toBeInTheDocument();
  });
});
