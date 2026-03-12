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

describe("API helper", () => {
  it("ApiError.detail があれば fallback より優先して返す", () => {
    const error = new ApiError("fallback");
    error.detail = "詳細なエラーメッセージ";

    expect(getErrorMessage(error, "代替メッセージ")).toBe(
      "詳細なエラーメッセージ"
    );
  });

  it("一時的な summary 失敗は再試行後の成功 payload を返す", async () => {
    let attemptCount = 0;
    server.use(
      http.get(`${API_BASE_URL}/api/summary`, ({ request }) => {
        attemptCount += 1;
        if (attemptCount < 3) {
          return HttpResponse.json(
            { detail: "一時的なエラーです" },
            { status: 500 }
          );
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

  it("不正クリック API の 400 detail を利用者向けエラーへ載せる", async () => {
    server.use(
      http.get(`${API_BASE_URL}/api/suspicious/clicks`, () => {
        return HttpResponse.json(
          { detail: "無効な検索条件です" },
          { status: 400 }
        );
      })
    );

    await expect(fetchSuspiciousClicks("2026-01-21")).rejects.toMatchObject({
      status: 400,
      detail: "無効な検索条件です",
      message: "無効な検索条件です",
    });
  });
});