import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { SuspiciousItem, SuspiciousResponse } from "@/lib/api";
import SuspiciousListPage from "@/components/suspicious-list-page";

function buildRows(count = 120): SuspiciousItem[] {
  return Array.from({ length: count }, (_, i) => {
    const index = i + 1;
    return {
      date: "2026-01-21",
      ipaddress: `10.0.0.${index}`,
      useragent: `Mozilla/TestAgent-${index}`,
      total_clicks: 200 - i,
      media_count: (index % 4) + 1,
      program_count: (index % 3) + 1,
      first_time: `2026-01-21T00:00:${String(index % 60).padStart(2, "0")}Z`,
      last_time: `2026-01-21T01:00:${String(index % 60).padStart(2, "0")}Z`,
      reasons: ["ip_frequency_high"],
      reasons_formatted: ["IP access threshold exceeded"],
      risk_level: "high",
      risk_score: 80,
      risk_label: "HIGH",
      media_names: [`Media ${index}`],
      program_names: [`Program ${index}`],
      affiliate_names: [`Affiliate ${index}`],
      details: [
        {
          media_id: `M-${index}`,
          program_id: `P-${index}`,
          media_name: `Media ${index}`,
          program_name: `Program ${index}`,
          affiliate_name: `Affiliate ${index}`,
          click_count: 10 + index,
          conversion_count: 3 + (index % 5),
        },
      ],
    };
  });
}

function createFetcher(rows = buildRows()) {
  return vi.fn(
    async (
      date?: string,
      limit = 50,
      offset = 0,
      search?: string
    ): Promise<SuspiciousResponse> => {
      const query = (search || "").trim().toLowerCase();
      const filtered = query
        ? rows.filter(
            (row) =>
              row.ipaddress.toLowerCase().includes(query) ||
              row.useragent.toLowerCase().includes(query) ||
              (row.media_names || []).some((media) => media.toLowerCase().includes(query))
          )
        : rows;

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

function renderPage(fetcher: ReturnType<typeof createFetcher>) {
  return render(
    <SuspiciousListPage
      title="不審クリック"
      countLabel="クリック数"
      fetcher={fetcher}
      metricKey="total_clicks"
    />
  );
}

describe("不審一覧画面", () => {
  it("初期表示で結果件数と先頭行を表示する", async () => {
    const fetcher = createFetcher();
    renderPage(fetcher);

    await screen.findByRole("heading", { name: "不審クリック" });
    await screen.findByText("1-50件目 / 全120件");

    expect(screen.getByText("10.0.0.1")).toBeInTheDocument();
    expect(screen.getAllByText("HIGH").length).toBeGreaterThan(0);
  });

  it("検索で行を絞り込み、件数表示も更新する", async () => {
    const fetcher = createFetcher();
    const user = userEvent.setup();
    renderPage(fetcher);

    await screen.findByText("1-50件目 / 全120件");
    const input = screen.getByRole("searchbox", { name: "一覧を検索" });

    await user.type(input, "10.0.0.120");

    await waitFor(() => {
      expect(screen.getByText("1-1件目 / 全1件")).toBeInTheDocument();
    });
    expect(screen.getByText("10.0.0.120")).toBeInTheDocument();
    expect(screen.queryByText("10.0.0.1")).not.toBeInTheDocument();
  });

  it("ページ移動後に詳細を開閉できる", async () => {
    const fetcher = createFetcher();
    const user = userEvent.setup();
    renderPage(fetcher);

    await screen.findByText("1-50件目 / 全120件");
    await user.click(screen.getByRole("button", { name: "次へ" }));
    await screen.findByText("51-100件目 / 全120件");

    await user.click(screen.getAllByRole("button", { name: "詳細" })[0]);
    await screen.findByText("初回検知");

    await user.click(screen.getByRole("button", { name: "閉じる" }));
    await waitFor(() => {
      expect(screen.queryByText("初回検知")).not.toBeInTheDocument();
    });
  });

  it("制御帯とリスク表示を描画する", async () => {
    const fetcher = createFetcher();
    renderPage(fetcher);

    await screen.findByRole("searchbox", { name: "一覧を検索" });
    await screen.findByText("1-50件目 / 全120件");
    expect(screen.getByRole("button", { name: "全件" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "高" })).toBeInTheDocument();
    expect(screen.getAllByText("HIGH").length).toBeGreaterThan(0);
  });
});
