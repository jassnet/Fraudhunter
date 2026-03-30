import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import DashboardPage from "@/app/page";
import { API_BASE_URL } from "@/lib/api";
import { buildSummaryResponse } from "@/test/msw/handlers";
import { server } from "@/test/msw/server";

describe("ダッシュボード画面", () => {
  it("最新の対象日と KPI を表示する", async () => {
    render(<DashboardPage />);

    await screen.findByRole("heading", { name: "ダッシュボード" });
    await screen.findByText("対象日 2026-01-21");

    expect(screen.getByText("総クリック")).toBeInTheDocument();
    expect(screen.getByText("総CV")).toBeInTheDocument();
    expect(screen.getAllByText("不審クリック").length).toBeGreaterThan(0);
    expect(screen.getByText("不審コンバージョン")).toBeInTheDocument();
    expect(screen.getByText("診断指標")).toBeInTheDocument();
  });

  it("admin 権限がないと操作帯を表示しない", async () => {
    render(<DashboardPage />);

    await screen.findByRole("heading", { name: "ダッシュボード" });

    expect(
      screen.queryByRole("button", { name: "最新1時間を再取得" })
    ).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "マスタ同期" })).not.toBeInTheDocument();
  });

  it("admin 権限があると再取得を enqueue して完了後に再読込する", async () => {
    let summaryCalls = 0;
    let statusCalls = 0;
    let refreshPayload: Record<string, unknown> | null = null;

    server.use(
      http.get("*/api/admin/job-status", () => {
        statusCalls += 1;
        if (statusCalls === 1) {
          return HttpResponse.json({
            status: "idle",
            message: "idle",
            job_id: null,
            result: null,
          });
        }
        if (statusCalls === 2) {
          return HttpResponse.json({
            status: "running",
            message: "running",
            job_id: "job-refresh-1",
            result: null,
          });
        }
        return HttpResponse.json({
          status: "completed",
          message: "completed",
          job_id: "job-refresh-1",
          result: { success: true },
        });
      }),
      http.post("*/api/admin/refresh", async ({ request }) => {
        refreshPayload = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({
          success: true,
          details: {
            job_id: "job-refresh-1",
          },
        });
      }),
      http.get(`${API_BASE_URL}/api/summary`, ({ request }) => {
        summaryCalls += 1;
        const url = new URL(request.url);
        const targetDate = url.searchParams.get("target_date") || "2026-01-21";
        return HttpResponse.json(buildSummaryResponse(targetDate));
      })
    );

    const user = userEvent.setup();
    render(<DashboardPage />);

    await screen.findByRole("button", { name: "最新1時間を再取得" });
    await user.click(screen.getByRole("button", { name: "最新1時間を再取得" }));

    await screen.findByText("再取得 / キュー登録済み");
    await waitFor(() => {
      expect(screen.getByText("再取得 / 実行中")).toBeInTheDocument();
    }, { timeout: 4000 });
    await waitFor(() => {
      expect(screen.getByText("再取得 / 完了")).toBeInTheDocument();
    }, { timeout: 4000 });

    expect(refreshPayload).toEqual({
      hours: 1,
      clicks: true,
      conversions: true,
      detect: true,
    });

    await waitFor(() => {
      expect(summaryCalls).toBe(2);
    });
  });

  it("admin 権限があるとマスタ同期を enqueue できる", async () => {
    let statusCalls = 0;
    let masterSyncCalls = 0;

    server.use(
      http.get("*/api/admin/job-status", () => {
        statusCalls += 1;
        if (statusCalls === 1) {
          return HttpResponse.json({
            status: "idle",
            message: "idle",
            job_id: null,
            result: null,
          });
        }
        return HttpResponse.json({
          status: "completed",
          message: "completed",
          job_id: "job-master-sync-1",
          result: { success: true },
        });
      }),
      http.post("*/api/admin/master-sync", () => {
        masterSyncCalls += 1;
        return HttpResponse.json({
          success: true,
          details: {
            job_id: "job-master-sync-1",
          },
        });
      })
    );

    const user = userEvent.setup();
    render(<DashboardPage />);

    await screen.findByRole("button", { name: "マスタ同期" });
    await user.click(screen.getByRole("button", { name: "マスタ同期" }));

    await screen.findByText("マスタ同期 / キュー登録済み");
    await waitFor(() => {
      expect(screen.getByText("マスタ同期 / 完了")).toBeInTheDocument();
    }, { timeout: 4000 });
    expect(masterSyncCalls).toBe(1);
  });

  it("一時的なエラー時に再読込で通常表示へ戻る", async () => {
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
    expect(screen.getByText("Findings の更新が遅れています")).toBeInTheDocument();
  });
});
