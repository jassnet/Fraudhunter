import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { vi } from "vitest";

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
  beforeEach(() => {
    replaceMock.mockReset();
  });

  it("loads unhandled alerts, supports bulk review, and refreshes the list", async () => {
    let fetchCount = 0;
    let requestedStatus: string | null = null;
    let requestedRiskLevel: string | null = null;
    let requestedSearch: string | null = null;
    let reviewRequestBody: unknown = null;

    server.use(
      http.get("/api/console/alerts", ({ request }) => {
        fetchCount += 1;
        const url = new URL(request.url);
        requestedStatus = url.searchParams.get("status");
        requestedRiskLevel = url.searchParams.get("risk_level");
        requestedSearch = url.searchParams.get("search");

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
              confirmed_fraud: 2,
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
          available_dates: ["2026-04-05", "2026-04-04"],
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
            confirmed_fraud: 4,
            white: 8,
          },
          items: [
            {
              finding_key: "fk-002",
              detected_at: "2026-04-05T09:28:00+09:00",
              affiliate_id: "AFF-200",
              affiliate_name: "alpha-media",
              outcome_type: "Program A",
              risk_score: 98,
              risk_level: "critical",
              pattern: "短時間に高額CVが集中",
              status: "unhandled",
              reward_amount: 52000,
              reward_amount_source: "fallback_default",
              reward_amount_is_estimated: true,
              transaction_count: 11,
            },
            {
              finding_key: "fk-001",
              detected_at: "2026-04-05T08:55:00+09:00",
              affiliate_id: "AFF-145",
              affiliate_name: "beta-traffic",
              outcome_type: "Program B",
              risk_score: 87,
              risk_level: "high",
              pattern: "CV間隔が極端に短い",
              status: "unhandled",
              reward_amount: 36000,
              reward_amount_source: "observed_transactions",
              reward_amount_is_estimated: false,
              transaction_count: 7,
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
        return HttpResponse.json({ updated_count: 2, status: "confirmed_fraud" });
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
    await waitFor(() => {
      expect(requestedStatus).toBe("unhandled");
      expect(requestedRiskLevel).toBe(null);
      expect(requestedSearch).toBe("alpha");
    });

    expect(screen.getByLabelText("判定状態")).toHaveValue("unhandled");
    expect(screen.getByLabelText("リスクレベル")).toHaveValue("all");
    expect(screen.getByLabelText("検索")).toHaveValue("alpha");
    expect(screen.getByRole("link", { name: "CSV出力" })).toHaveAttribute(
      "href",
      "/api/console/alerts/export?status=unhandled&sort=risk_desc&start_date=2026-04-05&end_date=2026-04-05&search=alpha",
    );

    const rows = screen.getAllByRole("row").slice(1);
    expect(within(rows[0]).getByText("98")).toBeInTheDocument();
    expect(within(rows[0]).getByText("alpha-media")).toBeInTheDocument();
    expect(within(rows[0]).getByText("推定")).toBeInTheDocument();
    expect(within(rows[1]).getByText("実測")).toBeInTheDocument();

    const checkboxes = screen.getAllByRole("checkbox");
    await user.click(checkboxes[1]);
    await user.click(checkboxes[2]);
    await user.click(screen.getByRole("button", { name: "不正にする" }));

    await waitFor(() => {
      expect(reviewRequestBody).toEqual({
        finding_keys: ["fk-002", "fk-001"],
        status: "confirmed_fraud",
      });
    });

    expect(await screen.findByText("条件に一致するアラートはありません。")).toBeInTheDocument();
  });

  it("groups matching alerts behind a collapsible row", async () => {
    server.use(
      http.get("/api/console/alerts", () =>
        HttpResponse.json({
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
              outcome_type: "Program A",
              risk_score: 98,
              risk_level: "critical",
              pattern: "短時間に高額CVが集中",
              status: "unhandled",
              reward_amount: 52000,
              reward_amount_source: "fallback_default",
              reward_amount_is_estimated: true,
              transaction_count: 11,
            },
            {
              finding_key: "fk-202",
              detected_at: "2026-04-05T09:28:00+09:00",
              affiliate_id: "AFF-200",
              affiliate_name: "alpha-media",
              outcome_type: "Program B",
              risk_score: 92,
              risk_level: "critical",
              pattern: "CV間隔が極端に短い",
              status: "unhandled",
              reward_amount: 36000,
              reward_amount_source: "observed_transactions",
              reward_amount_is_estimated: false,
              transaction_count: 7,
            },
            {
              finding_key: "fk-203",
              detected_at: "2026-04-05T08:55:00+09:00",
              affiliate_id: "AFF-145",
              affiliate_name: "beta-traffic",
              outcome_type: "Program C",
              risk_score: 87,
              risk_level: "high",
              pattern: "同一IPから連続CV",
              status: "unhandled",
              reward_amount: 12000,
              reward_amount_source: "observed_transactions",
              reward_amount_is_estimated: false,
              transaction_count: 3,
            },
          ],
          total: 3,
          page: 1,
          page_size: 50,
          has_next: false,
        }),
      ),
    );

    const user = userEvent.setup();
    render(<AlertsScreen viewerRole="admin" />);

    expect(await screen.findByText("alpha-media")).toBeInTheDocument();
    expect(screen.getByText("2件のアラートをまとめて表示")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "2件を表示" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "詳細を見る" })).toHaveAttribute("href", "/alerts/fk-201");
    expect(screen.queryByText("CV間隔が極端に短い")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "2件を表示" }));

    expect(await screen.findByText("CV間隔が極端に短い")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /alpha-media/i })).toHaveLength(2);
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

    await user.click(screen.getByRole("button", { name: "絞り込む" }));

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
                finding_key: "fk-051",
                detected_at: "2026-04-05T10:45:00+09:00",
                affiliate_id: "AFF-500",
                affiliate_name: "page-two-affiliate",
                outcome_type: "Program Z",
                risk_score: 72,
                risk_level: "medium",
                pattern: "page-two-pattern",
                status: "unhandled",
                reward_amount: 8000,
                reward_amount_source: "observed_transactions",
                reward_amount_is_estimated: false,
                transaction_count: 1,
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
              finding_key: "fk-001",
              detected_at: "2026-04-05T09:28:00+09:00",
              affiliate_id: "AFF-200",
              affiliate_name: "page-one-affiliate",
              outcome_type: "Program A",
              risk_score: 98,
              risk_level: "critical",
              pattern: "page-one-pattern",
              status: "unhandled",
              reward_amount: 52000,
              reward_amount_source: "observed_transactions",
              reward_amount_is_estimated: false,
              transaction_count: 11,
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
    expect(requestedPages).toEqual(["1"]);
  });
});
