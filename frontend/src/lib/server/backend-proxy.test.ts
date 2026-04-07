import { afterEach, describe, expect, it, vi } from "vitest";

import { proxyToBackend } from "./backend-proxy";

const ORIGINAL_ENV = { ...process.env };

afterEach(() => {
  vi.restoreAllMocks();
  process.env = { ...ORIGINAL_ENV };
});

describe("proxyToBackend", () => {
  it("uses the read api key for read-auth requests", async () => {
    process.env.FC_BACKEND_URL = "https://backend.example";
    process.env.FC_READ_API_KEY = "read-secret";

    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const response = await proxyToBackend({
      path: "/api/console/dashboard",
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0]?.[0]).toBe("https://backend.example/api/console/dashboard");

    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    const headers = init.headers as Headers;
    expect(headers.get("X-Read-API-Key")).toBe("read-secret");
    expect(headers.get("X-API-Key")).toBeNull();
    expect(response.status).toBe(200);
  });

  it("returns 502 when the read api key is missing", async () => {
    process.env.FC_BACKEND_URL = "https://backend.example";
    delete process.env.FC_READ_API_KEY;
    process.env.FC_ADMIN_API_KEY = "admin-secret";

    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const response = await proxyToBackend({
      path: "/api/console/dashboard",
      auth: "read",
    });

    expect(fetchMock).not.toHaveBeenCalled();
    expect(response.status).toBe(502);
    await expect(response.json()).resolves.toEqual({
      detail: "FC_READ_API_KEY is not configured.",
    });
  });
});
