import type { ReactElement } from "react";

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ConsoleDisplayModeProvider } from "@/components/console-display-mode";
import { server } from "@/test/msw/server";

import { AlertsScreen } from "./alerts-screen";

const replaceMock = vi.fn();

vi.mock("next/navigation", () => ({
  usePathname: () => "/alerts",
  useRouter: () => ({
    replace: replaceMock,
  }),
}));

function buildAlertsResponse(overrides: Record<string, unknown> = {}) {
  return {
    available_dates: ["2026-04-05"],
    applied_filters: {
      status: "unhandled",
      risk_level: null,
      start_date: "2026-04-05",
      end_date: "2026-04-05",
      search: null,
      sort: "risk_desc",
    },
    status_counts: {
      unhandled: 2,
      investigating: 1,
      confirmed_fraud: 0,
      white: 0,
    },
    items: [],
    total: 0,
    page: 1,
    page_size: 50,
    has_next: false,
    ...overrides,
  };
}

describe("AlertsScreen", () => {
  function renderWithDisplayMode(
    ui: ReactElement,
    showAdvanced = false,
  ) {
    render(
      <ConsoleDisplayModeProvider initialShowAdvanced={showAdvanced}>
        {ui}
      </ConsoleDisplayModeProvider>,
    );
  }

  afterEach(() => {
    vi.restoreAllMocks();
  });

  beforeEach(() => {
    replaceMock.mockReset();
  });

  it("loads case-centric alerts and sends review reason with selected case keys", async () => {
    let fetchCount = 0;
    let reviewRequestBody: unknown = null;

    server.use(
      http.get("/api/console/alerts", () => {
        fetchCount += 1;
        if (fetchCount > 1) {
          return HttpResponse.json(
            buildAlertsResponse({
              items: [],
              total: 0,
              status_counts: {
                unhandled: 0,
                investigating: 1,
                confirmed_fraud: 0,
                white: 0,
              },
              applied_filters: {
                status: "unhandled",
                risk_level: null,
                start_date: "2026-04-05",
                end_date: "2026-04-05",
                search: "alpha",
                sort: "risk_desc",
              },
            }),
          );
        }

        return HttpResponse.json(
          buildAlertsResponse({
            total: 2,
            items: [
              {
                case_key: "case-002",
                finding_key: "fk-002",
                environment: {
                  date: "2026-04-05",
                  ipaddress: "203.0.113.10",
                  useragent: "Mozilla/5.0 Chrome/123.0",
                },
                affected_affiliate_count: 2,
                affected_affiliates: [
                  { id: "AFF-200", name: "alpha-media" },
                  { id: "AFF-201", name: "beta-media" },
                ],
                affected_program_count: 1,
                affected_programs: [{ id: "PRG-1", name: "Program A" }],
                risk_score: 98,
                risk_level: "high",
                primary_reason: "shared-ip-pattern",
                reasons: ["shared-ip-pattern"],
                status: "unhandled",
                reward_amount: 52000,
                reward_amount_source: "fallback_default",
                reward_amount_is_estimated: true,
                transaction_count: 11,
                latest_detected_at: "2026-04-05T09:28:00+09:00",
                display_label: "alpha-media +1",
                secondary_label: "shared-ip-pattern",
                assignee: null,
                follow_up_open_count: 0,
              },
              {
                case_key: "case-001",
                finding_key: "fk-001",
                environment: {
                  date: "2026-04-05",
                  ipaddress: "203.0.113.11",
                  useragent: "Mozilla/5.0 Safari/17.0",
                },
                affected_affiliate_count: 1,
                affected_affiliates: [{ id: "AFF-145", name: "gamma-traffic" }],
                affected_program_count: 1,
                affected_programs: [{ id: "PRG-2", name: "Program B" }],
                risk_score: 87,
                risk_level: "high",
                primary_reason: "burst-conversion-pattern",
                reasons: ["burst-conversion-pattern"],
                status: "unhandled",
                reward_amount: 36000,
                reward_amount_source: "observed_transactions",
                reward_amount_is_estimated: false,
                transaction_count: 7,
                latest_detected_at: "2026-04-05T08:55:00+09:00",
                display_label: "gamma-traffic",
                secondary_label: "burst-conversion-pattern",
                assignee: null,
                follow_up_open_count: 0,
              },
            ],
            applied_filters: {
              status: "unhandled",
              risk_level: null,
              start_date: "2026-04-05",
              end_date: "2026-04-05",
              search: "alpha",
              sort: "risk_desc",
            },
          }),
        );
      }),
      http.post("/api/console/alerts/review", async ({ request }) => {
        reviewRequestBody = await request.json();
        return HttpResponse.json({
          requested_count: 2,
          matched_current_count: 2,
          updated_count: 2,
          missing_keys: [],
          status: "confirmed_fraud",
        });
      }),
    );

    const user = userEvent.setup();
    renderWithDisplayMode(
      <AlertsScreen
        searchParams={{
          search: "alpha",
        }}
      />,
    );

    expect(await screen.findByRole("heading", { name: "アラート一覧" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "CSV形式でダウンロード" })).not.toBeInTheDocument();
    expect(screen.getByText("alpha-media +1")).toBeInTheDocument();
    expect(screen.getByText("alpha-media +1").closest("a")).toHaveAttribute(
      "href",
      "/alerts/case-002?returnTo=%2Falerts%3Fstatus%3Dunhandled%26sort%3Drisk_desc%26page%3D1%26page_size%3D50%26start_date%3D2026-04-05%26end_date%3D2026-04-05%26search%3Dalpha",
    );
    expect(screen.queryByText("203.0.113.10")).not.toBeInTheDocument();
    expect(screen.getByText("推定の金額")).toBeInTheDocument();

    await user.click(screen.getByLabelText("alpha-media 他1件を選択"));
    await user.click(screen.getByLabelText("gamma-trafficを選択"));
    await user.click(screen.getByRole("button", { name: "不正と確定" }));

    expect(screen.getByRole("dialog", { name: "判定理由の入力" })).toBeInTheDocument();
    await user.type(screen.getByLabelText("理由"), "bulk review reason");
    await user.click(screen.getByRole("button", { name: "この内容で不正確定" }));

    await waitFor(() => {
      expect(reviewRequestBody).toEqual({
        case_keys: ["case-002", "case-001"],
        status: "confirmed_fraud",
        reason: "bulk review reason",
      });
    });

    expect(await screen.findByText("2件のケースを更新しました。")).toBeInTheDocument();
  });

  it("can apply bulk review to the entire filtered result set", async () => {
    let filteredReviewBody: unknown = null;

    server.use(
      http.get("/api/console/alerts", () =>
        HttpResponse.json(
          buildAlertsResponse({
            total: 120,
            items: [
              {
                case_key: "case-002",
                finding_key: "fk-002",
                environment: {
                  date: "2026-04-05",
                  ipaddress: "203.0.113.10",
                  useragent: "Mozilla/5.0 Chrome/123.0",
                },
                affected_affiliate_count: 1,
                affected_affiliates: [{ id: "AFF-200", name: "alpha-media" }],
                affected_program_count: 1,
                affected_programs: [{ id: "PRG-1", name: "Program A" }],
                risk_score: 82,
                risk_level: "high",
                primary_reason: "shared-ip-pattern",
                reasons: ["shared-ip-pattern"],
                status: "unhandled",
                reward_amount: 52000,
                reward_amount_source: "fallback_default",
                reward_amount_is_estimated: true,
                transaction_count: 11,
                latest_detected_at: "2026-04-05T09:28:00+09:00",
                display_label: "alpha-media",
                secondary_label: "shared-ip-pattern",
                assignee: null,
                follow_up_open_count: 0,
              },
            ],
          }),
        ),
      ),
      http.post("/api/console/alerts/review", async ({ request }) => {
        filteredReviewBody = await request.json();
        return HttpResponse.json({
          requested_count: 120,
          matched_current_count: 120,
          updated_count: 120,
          missing_keys: [],
          status: "white",
        });
      }),
    );

    const user = userEvent.setup();
    renderWithDisplayMode(<AlertsScreen />, true);

    expect(await screen.findByRole("heading", { name: "アラート一覧" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "絞り込み全件を対象にする" }));
    await user.click(screen.getByRole("button", { name: "正常（ホワイト）と確定" }));
    await user.type(screen.getByLabelText("理由"), "bulk white review");
    await user.click(screen.getByRole("button", { name: "この内容で正常確定" }));

    await waitFor(() => {
      expect(filteredReviewBody).toEqual({
        case_keys: [],
        status: "white",
        reason: "bulk white review",
        filters: {
          status: "unhandled",
          start_date: "2026-04-05",
          end_date: "2026-04-05",
          search: "",
          sort: "risk_desc",
        },
      });
    });

    expect(await screen.findByText("絞り込み条件に合う120件のケースを更新しました。")).toBeInTheDocument();
  });

  it("applies filters only when the apply button is clicked", async () => {
    const requestedSearches: Array<string | null> = [];
    const requestedRiskLevels: Array<string | null> = [];

    server.use(
      http.get("/api/console/alerts", ({ request }) => {
        const url = new URL(request.url);
        requestedSearches.push(url.searchParams.get("search"));
        requestedRiskLevels.push(url.searchParams.get("risk_level"));

        return HttpResponse.json(
          buildAlertsResponse({
            applied_filters: {
              status: url.searchParams.get("status") ?? "unhandled",
              risk_level: url.searchParams.get("risk_level"),
              start_date: "2026-04-05",
              end_date: "2026-04-05",
              search: url.searchParams.get("search"),
              sort: "risk_desc",
            },
            status_counts: {
              unhandled: 1,
              investigating: 0,
              confirmed_fraud: 0,
              white: 0,
            },
          }),
        );
      }),
    );

    const user = userEvent.setup();
    renderWithDisplayMode(<AlertsScreen />);

    expect(await screen.findByRole("heading", { name: "アラート一覧" })).toBeInTheDocument();
    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith(
        "/alerts?status=unhandled&sort=risk_desc&page=1&page_size=50&start_date=2026-04-05&end_date=2026-04-05",
        { scroll: false },
      );
    });
    replaceMock.mockClear();

    await user.type(screen.getByLabelText("検索"), "risky");
    await user.selectOptions(screen.getByLabelText("リスクレベル"), "high");

    expect(replaceMock).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "この条件で絞り込む" }));

    expect(replaceMock).toHaveBeenCalledWith(
      "/alerts?status=unhandled&sort=risk_desc&page=1&page_size=50&risk_level=high&search=risky",
      { scroll: false },
    );
    expect(requestedSearches[0]).toBe(null);
    expect(requestedRiskLevels[0]).toBe(null);
  });

  it("requests the next page when pagination is used", async () => {
    const requestedPages: string[] = [];

    server.use(
      http.get("/api/console/alerts", ({ request }) => {
        const url = new URL(request.url);
        const page = url.searchParams.get("page") ?? "1";
        requestedPages.push(page);

        if (page === "2") {
          return HttpResponse.json(
            buildAlertsResponse({
              total: 51,
              page: 2,
              has_next: false,
              status_counts: {
                unhandled: 51,
                investigating: 0,
                confirmed_fraud: 0,
                white: 0,
              },
              items: [
                {
                  case_key: "case-051",
                  finding_key: "fk-051",
                  environment: {
                    date: "2026-04-05",
                    ipaddress: "203.0.113.51",
                    useragent: "Mozilla/5.0 Edge/123.0",
                  },
                  affected_affiliate_count: 1,
                  affected_affiliates: [{ id: "AFF-500", name: "page-two-affiliate" }],
                  affected_program_count: 1,
                  affected_programs: [{ id: "PRG-Z", name: "Program Z" }],
                  risk_score: 72,
                  risk_level: "medium",
                  primary_reason: "page-two-pattern",
                  reasons: ["page-two-pattern"],
                  status: "unhandled",
                  reward_amount: 8000,
                  reward_amount_source: "observed_transactions",
                  reward_amount_is_estimated: false,
                  transaction_count: 1,
                  latest_detected_at: "2026-04-05T10:45:00+09:00",
                  display_label: "page-two-affiliate",
                  secondary_label: "page-two-pattern",
                  assignee: null,
                  follow_up_open_count: 0,
                },
              ],
            }),
          );
        }

        return HttpResponse.json(
          buildAlertsResponse({
            total: 51,
            has_next: true,
            status_counts: {
              unhandled: 51,
              investigating: 0,
              confirmed_fraud: 0,
              white: 0,
            },
            items: [
              {
                case_key: "case-001",
                finding_key: "fk-001",
                environment: {
                  date: "2026-04-05",
                  ipaddress: "203.0.113.1",
                  useragent: "Mozilla/5.0 Chrome/123.0",
                },
                affected_affiliate_count: 1,
                affected_affiliates: [{ id: "AFF-200", name: "page-one-affiliate" }],
                affected_program_count: 1,
                affected_programs: [{ id: "PRG-A", name: "Program A" }],
                risk_score: 98,
                risk_level: "high",
                primary_reason: "page-one-pattern",
                reasons: ["page-one-pattern"],
                status: "unhandled",
                reward_amount: 52000,
                reward_amount_source: "observed_transactions",
                reward_amount_is_estimated: false,
                transaction_count: 11,
                latest_detected_at: "2026-04-05T09:28:00+09:00",
                display_label: "page-one-affiliate",
                secondary_label: "page-one-pattern",
                assignee: null,
                follow_up_open_count: 0,
              },
            ],
          }),
        );
      }),
    );

    const user = userEvent.setup();
    renderWithDisplayMode(<AlertsScreen />);

    expect(await screen.findByText("page-one-affiliate")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "次へ" }));

    expect(replaceMock).toHaveBeenLastCalledWith(
      "/alerts?status=unhandled&sort=risk_desc&page=2&page_size=50&start_date=2026-04-05&end_date=2026-04-05",
      { scroll: false },
    );
    expect(requestedPages).toContain("1");
  });
});
