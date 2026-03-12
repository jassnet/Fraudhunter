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
      reasons_formatted: ["IP からのアクセス頻度が高すぎます"],
      risk_level: "high",
      risk_score: 80,
      risk_label: "高リスク",
      media_names: [`メディア ${index}`],
      program_names: [`案件 ${index}`],
      affiliate_names: [`提携先 ${index}`],
      details: [
        {
          media_id: `M-${index}`,
          program_id: `P-${index}`,
          media_name: `メディア ${index}`,
          program_name: `案件 ${index}`,
          affiliate_name: `提携先 ${index}`,
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
              row.useragent.toLowerCase().includes(query)
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
      title="不正クリック一覧"
      description="クリックベースのルールで検知した IP と User Agent を確認する。"
      countLabel="クリック数"
      fetcher={fetcher}
      metricKey="total_clicks"
    />
  );
}

describe("不正一覧画面", () => {
  it("初期表示で 1 ページ目の結果件数と代表行を表示する", async () => {
    const fetcher = createFetcher();
    renderPage(fetcher);

    await screen.findByRole("heading", { name: "不正クリック一覧" });
    await screen.findByText("Showing 1-50 of 120");

    expect(screen.getByText("10.0.0.1")).toBeInTheDocument();
    expect(screen.getAllByText("高リスク").length).toBeGreaterThan(0);
  });

  it("検索キーワードに合う行だけへ絞り込み、件数表示も更新する", async () => {
    const fetcher = createFetcher();
    const user = userEvent.setup();
    renderPage(fetcher);

    await screen.findByText("Showing 1-50 of 120");
    const input = screen.getByRole("searchbox", {
      name: "Search suspicious list",
    });

    await user.type(input, "10.0.0.120");

    await waitFor(() => {
      expect(screen.getByText("Showing 1-1 of 1")).toBeInTheDocument();
    });
    expect(screen.getByText("10.0.0.120")).toBeInTheDocument();
    expect(screen.queryByText("10.0.0.1")).not.toBeInTheDocument();
  });

  it("ページ移動後に詳細を開閉できる", async () => {
    const fetcher = createFetcher();
    const user = userEvent.setup();
    renderPage(fetcher);

    await screen.findByText("Showing 1-50 of 120");
    await user.click(screen.getByRole("button", { name: "Next" }));
    await screen.findByText("Showing 51-100 of 120");

    const detailButton = screen.getAllByRole("button", { name: "Details" })[0];
    await user.click(detailButton);
    await screen.findByText("First seen");

    await user.click(screen.getByRole("button", { name: "Hide" }));
    await waitFor(() => {
      expect(screen.queryByText("First seen")).not.toBeInTheDocument();
    });
  });

  it("一覧取得に失敗したときは画面上にエラーを表示する", async () => {
    const fetcher = vi.fn(async (): Promise<SuspiciousResponse> => {
      throw new Error("不正一覧の取得に失敗しました");
    });
    renderPage(fetcher);

    await screen.findByText("不正一覧の取得に失敗しました");
  });
});