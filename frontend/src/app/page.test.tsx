import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import DashboardPage from "@/app/page";
import { API_BASE_URL } from "@/lib/api";
import { buildSummaryResponse } from "@/test/msw/handlers";
import { server } from "@/test/msw/server";

describe("ダッシュボード画面", () => {
  it("最新の対象日と KPI 帯を表示する", async () => {
    render(<DashboardPage />);

    await screen.findByRole("heading", { name: "ダッシュボード" });
    await screen.findByText("対象日 2026-01-21");

    expect(screen.getByText("総クリック")).toBeInTheDocument();
    expect(screen.getByText("総CV")).toBeInTheDocument();
    expect(screen.getAllByText("不審クリック").length).toBeGreaterThan(0);
    expect(screen.getByText("不審コンバージョン")).toBeInTheDocument();
    expect(screen.getByText("診断情報")).toBeInTheDocument();
  });

  it("一時的な取得失敗のあと再読込で通常表示に戻る", async () => {
    let attemptCount = 0;
    server.use(
      http.get(`${API_BASE_URL}/api/summary`, ({ request }) => {
        attemptCount += 1;
        if (attemptCount <= 3) {
          return HttpResponse.json(
            { detail: "一時的に取得に失敗しました" },
            { status: 500 }
          );
        }
        const url = new URL(request.url);
        const targetDate = url.searchParams.get("target_date") || "2026-01-21";
        return HttpResponse.json(buildSummaryResponse(targetDate));
      })
    );

    const user = userEvent.setup();
    render(<DashboardPage />);

    await screen.findByRole("heading", { name: "一時的な取得エラー" }, { timeout: 4000 });
    expect(screen.getByText("一時的に取得に失敗しました")).toBeInTheDocument();

    await user.click(screen.getAllByRole("button", { name: "再読込" }).at(-1)!);

    await screen.findByRole("heading", { name: "ダッシュボード" });
    await waitFor(() => {
      expect(screen.queryByText("一時的に取得に失敗しました")).not.toBeInTheDocument();
    });
  });

  it("対象日を切り替えると表示を更新する", async () => {
    const user = userEvent.setup();
    render(<DashboardPage />);

    await screen.findByRole("heading", { name: "ダッシュボード" });
    await screen.findByText("対象日 2026-01-21");

    await user.selectOptions(screen.getByLabelText("対象日"), "2026-01-20");

    await waitFor(() => {
      expect(screen.getByText("対象日 2026-01-20")).toBeInTheDocument();
    });
  });

  it("findings stale をヘッダーで表示する", async () => {
    server.use(
      http.get(`${API_BASE_URL}/api/summary`, ({ request }) => {
        const url = new URL(request.url);
        const targetDate = url.searchParams.get("target_date") || "2026-01-21";
        return HttpResponse.json({
          ...buildSummaryResponse(targetDate),
          quality: {
            findings: {
              stale: true,
              findings_last_computed_at: "2026-01-21T09:00:00Z",
              stale_reasons: ["findings lagging behind raw ingest"],
            },
          },
        });
      })
    );

    render(<DashboardPage />);

    await screen.findByRole("heading", { name: "ダッシュボード" });
    expect(screen.getByText("findings の再計算が遅れています")).toBeInTheDocument();
  });
});
