import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { server } from "@/test/msw/server";

import { AlertsScreen } from "./alerts-screen";

const replaceMock = vi.fn();

vi.mock("next/navigation", () => ({
  usePathname: () => "/alerts",
  useRouter: () => ({
    replace: replaceMock,
  }),
}));

describe("AlertsScreen", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  beforeEach(() => {
    replaceMock.mockReset();
  });

  it("loads case-centric alerts and sends review reason with case keys", async () => {
    let fetchCount = 0;
    let reviewRequestBody: unknown = null;

    server.use(
      http.get("/api/console/alerts", () => {
        fetchCount += 1;
        if (fetchCount > 1) {
          return HttpResponse.json({
            available_dates: ["2026-04-05"],
            applied_filters: {
              status: "unhandled",
              risk_level: null,
              start_date: "2026-04-05",
              end_date: "2026-04-05",
              search: "alpha",
              sort: "risk_desc",
            },
            status_counts: {
              unhandled: 0,
              investigating: 1,
              confirmed_fraud: 0,
              white: 0,
            },
            items: [],
            total: 0,
            page: 1,
            page_size: 50,
            has_next: false,
          });
        }

        return HttpResponse.json({
          available_dates: ["2026-04-05"],
          applied_filters: {
            status: "unhandled",
            risk_level: null,
            start_date: "2026-04-05",
            end_date: "2026-04-05",
            search: "alpha",
            sort: "risk_desc",
          },
          status_counts: {
            unhandled: 2,
            investigating: 1,
            confirmed_fraud: 0,
            white: 0,
          },
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
              risk_level: "critical",
              primary_reason: "shared-ip-pattern",
              reasons: ["shared-ip-pattern"],
              status: "unhandled",
              reward_amount: 52000,
              reward_amount_source: "fallback_default",
              reward_amount_is_estimated: true,
              transaction_count: 11,
              latest_detected_at: "2026-04-05T09:28:00+09:00",
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
            },
          ],
          total: 2,
          page: 1,
          page_size: 50,
          has_next: false,
        });
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
    render(
      <AlertsScreen
        searchParams={{
          search: "alpha",
        }}
        viewerRole="admin"
      />,
    );

    expect(await screen.findByRole("heading", { name: "アラート一覧" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "CSVエクスポート" })).toHaveAttribute(
      "href",
      "/api/console/alerts/export?status=unhandled&sort=risk_desc&start_date=2026-04-05&end_date=2026-04-05&search=alpha",
    );
    expect(screen.getByText("alpha-media +1")).toBeInTheDocument();
    expect(screen.getByText("203.0.113.10")).toBeInTheDocument();
    expect(screen.getByText("推定")).toBeInTheDocument();

    await user.click(screen.getByLabelText("Select alpha-media +1"));
    await user.click(screen.getByLabelText("Select gamma-traffic"));
    await user.click(screen.getByRole("button", { name: "不正確定" }));

    expect(screen.getByRole("dialog", { name: "レビュー理由" })).toBeInTheDocument();
    await user.type(screen.getByLabelText("理由"), "bulk review reason");
    await user.click(screen.getByRole("button", { name: "不正として確定" }));

    await waitFor(() => {
      expect(reviewRequestBody).toEqual({
        case_keys: ["case-002", "case-001"],
        status: "confirmed_fraud",
        reason: "bulk review reason",
      });
    });

    expect(await screen.findByText("条件に一致するアラートはありません。")).toBeInTheDocument();
  });

  it("applies filters only when the apply button is clicked", async () => {
    const requestedSearches: Array<string | null> = [];
    const requestedRiskLevels: Array<string | null> = [];

    server.use(
      http.get("/api/console/alerts", ({ request }) => {
        const url = new URL(request.url);
        requestedSearches.push(url.searchParams.get("search"));
        requestedRiskLevels.push(url.searchParams.get("risk_level"));

        return HttpResponse.json({
          available_dates: ["2026-04-05"],
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
          items: [],
          total: 0,
          page: 1,
          page_size: 50,
          has_next: false,
        });
      }),
    );

    const user = userEvent.setup();
    render(<AlertsScreen viewerRole="admin" />);

    expect(await screen.findByRole("heading", { name: "アラート一覧" })).toBeInTheDocument();
    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith(
        "/alerts?status=unhandled&sort=risk_desc&page=1&page_size=50&start_date=2026-04-05&end_date=2026-04-05",
        { scroll: false },
      );
    });
    replaceMock.mockClear();

    await user.type(screen.getByLabelText("検索"), "risky");
    await user.selectOptions(screen.getByLabelText("リスクレベル"), "critical");

    expect(replaceMock).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "適用" }));

    expect(replaceMock).toHaveBeenCalledWith(
      "/alerts?status=unhandled&sort=risk_desc&page=1&page_size=50&risk_level=critical&search=risky",
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
          return HttpResponse.json({
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
              },
            ],
            total: 51,
            page: 2,
            page_size: 50,
            has_next: false,
          });
        }

        return HttpResponse.json({
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
              risk_level: "critical",
              primary_reason: "page-one-pattern",
              reasons: ["page-one-pattern"],
              status: "unhandled",
              reward_amount: 52000,
              reward_amount_source: "observed_transactions",
              reward_amount_is_estimated: false,
              transaction_count: 11,
              latest_detected_at: "2026-04-05T09:28:00+09:00",
            },
          ],
          total: 51,
          page: 1,
          page_size: 50,
          has_next: true,
        });
      }),
    );

    const user = userEvent.setup();
    render(<AlertsScreen viewerRole="admin" />);

    expect(await screen.findByText("page-one-affiliate")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "次へ" }));

    expect(replaceMock).toHaveBeenLastCalledWith(
      "/alerts?status=unhandled&sort=risk_desc&page=2&page_size=50&start_date=2026-04-05&end_date=2026-04-05",
      { scroll: false },
    );
    expect(requestedPages[0]).toBe("1");
  });
});
