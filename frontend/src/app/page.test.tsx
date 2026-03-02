import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import DashboardPage from "@/app/page";
import { API_BASE_URL } from "@/lib/api";
import { buildSummaryResponse } from "@/test/msw/handlers";
import { server } from "@/test/msw/server";

describe("ダッシュボード画面", () => {
  it("主要指標と遷移カードを表示できる", async () => {
    render(<DashboardPage />);

    await screen.findByRole("heading", { name: "Dashboard" });
    await screen.findByText("Reporting date: 2026-01-21");

    expect(screen.getByText("Total Clicks")).toBeInTheDocument();
    expect(screen.getByText("Total Conversions")).toBeInTheDocument();
    expect(screen.getByText("Suspicious Clicks")).toBeInTheDocument();
    expect(screen.getByText("Suspicious Conversions")).toBeInTheDocument();
  });

  it("取得失敗後にRetryで再取得できる", async () => {
    let attemptCount = 0;
    server.use(
      http.get(`${API_BASE_URL}/api/summary`, ({ request }) => {
        attemptCount += 1;
        if (attemptCount <= 3) {
          return HttpResponse.json(
            { detail: "summary failed on purpose" },
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

    await screen.findByRole("heading", { name: "Error" }, { timeout: 4000 });
    expect(screen.getByText("summary failed on purpose")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Retry" }));

    await screen.findByRole("heading", { name: "Dashboard" });
    await waitFor(() => {
      expect(
        screen.queryByText("summary failed on purpose")
      ).not.toBeInTheDocument();
    });
    expect(attemptCount).toBeGreaterThanOrEqual(2);
  });

  it("日付選択で表示対象日を切り替えられる", async () => {
    const user = userEvent.setup();
    render(<DashboardPage />);

    await screen.findByRole("heading", { name: "Dashboard" });
    await screen.findByText("Reporting date: 2026-01-21");

    await user.selectOptions(screen.getByLabelText("Select date"), "2026-01-20");

    await waitFor(() => {
      expect(screen.getByText("Reporting date: 2026-01-20")).toBeInTheDocument();
    });
  });
});
