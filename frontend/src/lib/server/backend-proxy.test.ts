import { afterEach, describe, expect, it, vi } from "vitest";

import { proxyToBackend } from "./backend-proxy";

const ORIGINAL_ENV = { ...process.env };

afterEach(() => {
  vi.restoreAllMocks();
  process.env = { ...ORIGINAL_ENV };
});

describe("proxyToBackend", () => {
  const viewer = {
    userId: "user-1",
    email: "viewer@example.com",
    role: "analyst" as const,
    requestId: "req-1",
  };

  it("forwards signed console viewer headers", async () => {
    process.env.FC_BACKEND_URL = "https://backend.example";
    process.env.FC_INTERNAL_PROXY_SECRET = "proxy-secret";

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
      viewer,
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0]?.[0]).toBe("https://backend.example/api/console/dashboard");

    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    const headers = init.headers as Headers;
    expect(headers.get("X-Console-User-Id")).toBe("user-1");
    expect(headers.get("X-Console-User-Email")).toBe("viewer@example.com");
    expect(headers.get("X-Console-User-Role")).toBe("analyst");
    expect(headers.get("X-Console-Request-Id")).toBe("req-1");
    expect(headers.get("X-Console-User-Signature")).toBeTruthy();
    expect(response.status).toBe(200);
  });

  it("returns 502 when the internal proxy secret is missing", async () => {
    process.env.FC_BACKEND_URL = "https://backend.example";
    delete process.env.FC_INTERNAL_PROXY_SECRET;

    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const response = await proxyToBackend({
      path: "/api/console/dashboard",
      viewer,
    });

    expect(fetchMock).not.toHaveBeenCalled();
    expect(response.status).toBe(502);
    await expect(response.json()).resolves.toEqual({
      detail: "FC_INTERNAL_PROXY_SECRET is not configured.",
    });
  });
});
