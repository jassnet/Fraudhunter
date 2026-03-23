import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import DashboardPage from "@/app/page";
import { API_BASE_URL } from "@/lib/api";
import { buildSummaryResponse } from "@/test/msw/handlers";
import { server } from "@/test/msw/server";

describe("ダッシュボード画面", () => {
  it("最新の基準日と主要カードを表示する", async () => {
    render(<DashboardPage />);

    await screen.findByRole("heading", { name: "ダッシュボード" });
    await screen.findByText("基準日: 2026-01-21");

    expect(screen.getByText("総クリック数")).toBeInTheDocument();
    expect(screen.getByText("総コンバージョン数")).toBeInTheDocument();
    expect(screen.getByText("不審クリック")).toBeInTheDocument();
    expect(screen.getByText("不審コンバージョン")).toBeInTheDocument();
  });

  it("一時的な取得失敗のあと再試行で通常表示に戻る", async () => {
    let attemptCount = 0;
    server.use(
      http.get(`${API_BASE_URL}/api/summary`, ({ request }) => {
        attemptCount += 1;
        if (attemptCount <= 3) {
          return HttpResponse.json(
            { detail: "一時的に取得に失敗しました" },
            { status: 400 }
          );
        }
        const url = new URL(request.url);
        const targetDate = url.searchParams.get("target_date") || "2026-01-21";
        return HttpResponse.json(buildSummaryResponse(targetDate));
      })
    );

    const user = userEvent.setup();
    render(<DashboardPage />);

    await screen.findByRole("heading", { name: "取得エラー" }, { timeout: 4000 });
    expect(screen.getByText("一時的に取得に失敗しました")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "再試行" }));

    await screen.findByRole("heading", { name: "ダッシュボード" });
    await waitFor(() => {
      expect(screen.queryByText("一時的に取得に失敗しました")).not.toBeInTheDocument();
    });
  });

  it("日付を切り替えると別日の集計表示へ更新される", async () => {
    const user = userEvent.setup();
    render(<DashboardPage />);

    await screen.findByRole("heading", { name: "ダッシュボード" });
    await screen.findByText("基準日: 2026-01-21");

    await user.selectOptions(screen.getByLabelText("対象日を選択"), "2026-01-20");

    await waitFor(() => {
      expect(screen.getByText("基準日: 2026-01-20")).toBeInTheDocument();
    });
  });
});
