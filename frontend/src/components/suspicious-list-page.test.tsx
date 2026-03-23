import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import SuspiciousListPage from "@/components/suspicious-list-page";
import { SuspiciousItem, SuspiciousQueryOptions, SuspiciousResponse } from "@/lib/api";

function buildRows(count = 120): SuspiciousItem[] {
  return Array.from({ length: count }, (_, i) => {
    const index = i + 1;
    const riskLevel =
      index % 3 === 0 ? "medium" : index % 5 === 0 ? "low" : "high";

    return {
      finding_key: `finding-${index}`,
      date: "2026-01-21",
      ipaddress: `10.0.0.${index}`,
      useragent: `Mozilla/TestAgent-${index}`,
      total_clicks: 200 - i,
      media_count: (index % 4) + 1,
      program_count: (index % 3) + 1,
      first_time: `2026-01-21T00:00:${String(index % 60).padStart(2, "0")}Z`,
      last_time: `2026-01-21T01:00:${String(index % 60).padStart(2, "0")}Z`,
      reasons: ["total_clicks >= 50"],
      reasons_formatted: ["クリック数が閾値以上です（50件以上）"],
      risk_level: riskLevel,
      risk_score: riskLevel === "high" ? 90 : riskLevel === "medium" ? 60 : 20,
      risk_label:
        riskLevel === "high" ? "高リスク" : riskLevel === "medium" ? "中リスク" : "低リスク",
      media_names: [`Media ${index}`],
      program_names: [`Program ${index}`],
      affiliate_names: [`Affiliate ${index}`],
    };
  });
}

function createFetcher(rows = buildRows()) {
  return vi.fn(
    async (
      date?: string,
      limit = 50,
      offset = 0,
      options?: SuspiciousQueryOptions
    ): Promise<SuspiciousResponse> => {
      const query = (options?.search || "").trim().toLowerCase();
      let filtered = query
        ? rows.filter(
            (row) =>
              row.ipaddress.toLowerCase().includes(query) ||
              row.useragent.toLowerCase().includes(query) ||
              (row.media_names || []).some((media) => media.toLowerCase().includes(query))
          )
        : rows;

      if (options?.riskLevel) {
        filtered = filtered.filter((row) => row.risk_level === options.riskLevel);
      }

      return {
        date: date || "2026-01-21",
        data: filtered.slice(offset, offset + limit),
        total: filtered.length,
        limit,
        offset,
      };
    }
  );
}

function createDetailFetcher() {
  return vi.fn(async (findingKey: string) => ({
    finding_key: findingKey,
    date: "2026-01-21",
    ipaddress: "10.0.0.1",
    useragent: "Mozilla/TestAgent-1",
    total_clicks: 200,
    media_count: 2,
    program_count: 1,
    first_time: "2026-01-21T00:00:01Z",
    last_time: "2026-01-21T01:00:01Z",
    reasons: ["total_clicks >= 50"],
    reasons_formatted: ["クリック数が閾値以上です（50件以上）"],
    risk_level: "high",
    risk_score: 90,
    risk_label: "高リスク",
    media_names: ["Media 1"],
    program_names: ["Program 1"],
    affiliate_names: ["Affiliate 1"],
    details: [
      {
        media_id: "M-1",
        program_id: "P-1",
        media_name: "Media 1",
        program_name: "Program 1",
        affiliate_name: "Affiliate 1",
        click_count: 61,
        conversion_count: 4,
      },
    ],
  }));
}

function renderPage(
  fetcher: ReturnType<typeof createFetcher>,
  detailFetcher = createDetailFetcher()
) {
  return render(
    <SuspiciousListPage
      title="不審クリック"
      countLabel="クリック数"
      fetcher={fetcher}
      fetchDetail={detailFetcher}
      metricKey="total_clicks"
    />
  );
}

describe("不審一覧画面", () => {
  it("初期表示で件数と一覧を表示する", async () => {
    const fetcher = createFetcher();
    renderPage(fetcher);

    await screen.findByRole("heading", { name: "不審クリック" });
    await screen.findByText("1-50件目 / 全120件");

    expect(screen.getByText("10.0.0.1")).toBeInTheDocument();
    expect(screen.getAllByText("高リスク").length).toBeGreaterThan(0);
  });

  it("検索条件を server-side query として渡す", async () => {
    const fetcher = createFetcher();
    const user = userEvent.setup();
    renderPage(fetcher);

    await screen.findByText("1-50件目 / 全120件");
    const input = screen.getByRole("searchbox", { name: "一覧を検索" });

    await user.type(input, "10.0.0.120");

    await waitFor(() => {
      expect(screen.getByText("1-1件目 / 全1件")).toBeInTheDocument();
    });
    expect(fetcher).toHaveBeenLastCalledWith(
      "2026-01-21",
      50,
      0,
      expect.objectContaining({ search: "10.0.0.120", includeDetails: false })
    );
  });

  it("詳細展開時に lazy detail fetch を呼ぶ", async () => {
    const fetcher = createFetcher();
    const detailFetcher = createDetailFetcher();
    const user = userEvent.setup();
    renderPage(fetcher, detailFetcher);

    await screen.findByText("1-50件目 / 全120件");
    await user.click(screen.getAllByRole("button", { name: "詳細" })[0]);

    await screen.findByText("詳細内訳");
    expect(detailFetcher).toHaveBeenCalledWith("finding-1");

    await user.click(screen.getByRole("button", { name: "閉じる" }));
    await waitFor(() => {
      expect(screen.queryByText("詳細内訳")).not.toBeInTheDocument();
    });
  });

  it("リスク絞り込みを server-side に渡す", async () => {
    const fetcher = createFetcher();
    const user = userEvent.setup();
    renderPage(fetcher);

    await screen.findByRole("searchbox", { name: "一覧を検索" });
    await user.click(screen.getByRole("button", { name: "高" }));

    await waitFor(() => {
      expect(fetcher).toHaveBeenLastCalledWith(
        "2026-01-21",
        50,
        0,
        expect.objectContaining({ riskLevel: "high", includeDetails: false })
      );
    });
  });
});
