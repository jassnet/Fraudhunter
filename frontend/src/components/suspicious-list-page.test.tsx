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
      reasons_formatted: ["IP頻度が高い"],
      risk_level: "high",
      risk_score: 80,
      risk_label: "High Risk",
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
      title="Suspicious Clicks"
      description="IPs and user agents flagged by click-based rules."
      countLabel="Clicks"
      fetcher={fetcher}
      metricKey="total_clicks"
    />
  );
}

describe("不正一覧コンポーネント", () => {
  it("初期表示で一覧と件数レンジを表示できる", async () => {
    const fetcher = createFetcher();
    renderPage(fetcher);

    await screen.findByRole("heading", { name: "Suspicious Clicks" });
    await screen.findByText("Showing 1-50 of 120");

    expect(fetcher).toHaveBeenCalled();
    expect(screen.getByText("10.0.0.1")).toBeInTheDocument();
  });

  it("検索入力後にデバウンスして再取得する", async () => {
    const fetcher = createFetcher();
    const user = userEvent.setup();
    renderPage(fetcher);

    await screen.findByText("Showing 1-50 of 120");
    const input = screen.getByRole("searchbox", {
      name: "Search suspicious list",
    });

    await user.type(input, "10.0.0.12");

    await waitFor(() => {
      const lastCall = fetcher.mock.lastCall;
      expect(lastCall?.[3]).toBe("10.0.0.12");
    });
  });

  it("ページングと詳細表示の開閉ができる", async () => {
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

  it("取得失敗時にエラーメッセージを表示する", async () => {
    const fetcher = vi.fn(
      async (): Promise<SuspiciousResponse> => {
        throw new Error("一覧取得に失敗しました");
      }
    );
    renderPage(fetcher);

    await screen.findByText("一覧取得に失敗しました");
  });
});
