import { describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import {
  API_BASE_URL,
  ApiError,
  enqueueMasterSyncJob,
  enqueueRefreshJob,
  fetchSummary,
  getErrorMessage,
} from "@/lib/api";
import { buildSummaryResponse } from "@/test/msw/handlers";
import { server } from "@/test/msw/server";

describe("API helpers", () => {
  it("prefers ApiError.detail over the fallback message", () => {
    const error = new ApiError("fallback");
    error.detail = "Detailed error message";

    expect(getErrorMessage(error, "Fallback message")).toBe("Detailed error message");
  });

  it("retries transient summary failures before succeeding", async () => {
    let attemptCount = 0;
    server.use(
      http.get(`${API_BASE_URL}/api/summary`, ({ request }) => {
        attemptCount += 1;
        if (attemptCount < 3) {
          return HttpResponse.json({ detail: "Temporary failure" }, { status: 500 });
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

  it("returns the conflict job id for refresh enqueue", async () => {
    server.use(
      http.post("*/api/admin/refresh", () =>
        HttpResponse.json(
          {
            detail: "duplicate",
            details: { job_id: "run-refresh-existing" },
          },
          { status: 409 }
        )
      )
    );

    await expect(enqueueRefreshJob()).resolves.toEqual({
      jobId: "run-refresh-existing",
    });
  });

  it("returns the conflict job id for master sync enqueue", async () => {
    server.use(
      http.post("*/api/admin/master-sync", () =>
        HttpResponse.json(
          {
            detail: "duplicate",
            details: { job_id: "run-master-existing" },
          },
          { status: 409 }
        )
      )
    );

    await expect(enqueueMasterSyncJob()).resolves.toEqual({
      jobId: "run-master-existing",
    });
  });
});
