import { describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";

import {
  API_BASE_URL,
  ApiError,
  fetchSummary,
  fetchSuspiciousClickDetail,
  fetchSuspiciousClicks,
  getErrorMessage,
} from "@/lib/api";
import { buildSummaryResponse } from "@/test/msw/handlers";
import { server } from "@/test/msw/server";

describe("API helper", () => {
  it("ApiError.detail があれば fallback より優先して返す", () => {
    const error = new ApiError("fallback");
    error.detail = "詳細なエラーメッセージ";

    expect(getErrorMessage(error, "元のメッセージ")).toBe("詳細なエラーメッセージ");
  });

  it("一時的な summary 失敗は再試行後に payload を返す", async () => {
    let attemptCount = 0;
    server.use(
      http.get(`${API_BASE_URL}/api/summary`, ({ request }) => {
        attemptCount += 1;
        if (attemptCount < 3) {
          return HttpResponse.json({ detail: "一時的なエラーです" }, { status: 500 });
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

  it("不審クリック API に filter/sort query を付けて取得する", async () => {
    server.use(
      http.get(`${API_BASE_URL}/api/suspicious/clicks`, ({ request }) => {
        const url = new URL(request.url);
        expect(url.searchParams.get("date")).toBe("2026-01-21");
        expect(url.searchParams.get("search")).toBe("Media Alpha");
        expect(url.searchParams.get("risk_level")).toBe("high");
        expect(url.searchParams.get("sort_by")).toBe("risk");
        expect(url.searchParams.get("sort_order")).toBe("asc");
        expect(url.searchParams.get("include_details")).toBe("false");
        return HttpResponse.json({
          date: "2026-01-21",
          data: [],
          total: 0,
          limit: 50,
          offset: 0,
        });
      })
    );

    const result = await fetchSuspiciousClicks("2026-01-21", 50, 0, {
      search: "Media Alpha",
      riskLevel: "high",
      sortBy: "risk",
      sortOrder: "asc",
      includeDetails: false,
    });

    expect(result.total).toBe(0);
  });

  it("不審クリック detail API の 400 detail をそのまま返す", async () => {
    server.use(
      http.get(`${API_BASE_URL}/api/suspicious/clicks/:findingKey`, () =>
        HttpResponse.json({ detail: "不正な finding_key です" }, { status: 400 })
      )
    );

    await expect(fetchSuspiciousClickDetail("broken-key")).rejects.toMatchObject({
      status: 400,
      detail: "不正な finding_key です",
      message: "不正な finding_key です",
    });
  });
});
