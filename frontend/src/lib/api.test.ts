import { describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import {
  API_BASE_URL,
  ApiError,
  fetchSummary,
  fetchSuspiciousClicks,
  getErrorMessage,
} from "@/lib/api";
import { buildSummaryResponse } from "@/test/msw/handlers";
import { server } from "@/test/msw/server";

describe("APIユーティリティ", () => {
  it("ApiErrorのdetailを優先してエラーメッセージ化する", () => {
    const error = new ApiError("fallback");
    error.detail = "詳細メッセージ";

    expect(getErrorMessage(error, "代替メッセージ")).toBe("詳細メッセージ");
  });

  it("一時的なサーバーエラー時は再試行して成功できる", async () => {
    let attemptCount = 0;
    server.use(
      http.get(`${API_BASE_URL}/api/summary`, ({ request }) => {
        attemptCount += 1;
        if (attemptCount < 3) {
          return HttpResponse.json({ detail: "temporary error" }, { status: 500 });
        }
        const url = new URL(request.url);
        const targetDate = url.searchParams.get("target_date") || "2026-01-21";
        return HttpResponse.json(buildSummaryResponse(targetDate));
      })
    );

    const result = await fetchSummary("2026-01-21");

    expect(result.date).toBe("2026-01-21");
    expect(attemptCount).toBe(3);
  });

  it("400エラー時は詳細メッセージ付きで失敗する", async () => {
    server.use(
      http.get(`${API_BASE_URL}/api/suspicious/clicks`, () => {
        return HttpResponse.json({ detail: "不正なパラメータです" }, { status: 400 });
      })
    );

    await expect(fetchSuspiciousClicks("2026-01-21")).rejects.toMatchObject({
      status: 400,
      detail: "不正なパラメータです",
      message: "不正なパラメータです",
    });
  });
});
