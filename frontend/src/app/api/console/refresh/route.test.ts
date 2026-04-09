import { beforeEach, describe, expect, it, vi } from "vitest";

const { proxyToBackend } = vi.hoisted(() => ({
  proxyToBackend: vi.fn(),
}));

vi.mock("@/lib/server/backend-proxy", () => ({
  proxyToBackend,
}));

import { POST } from "./route";

describe("refresh route", () => {
  beforeEach(() => {
    proxyToBackend.mockReset();
  });

  it("rejects analyst viewers on admin routes", async () => {
    const request = new Request("http://localhost/api/console/refresh", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "X-Auth-Request-User": "analyst-1",
        "X-Auth-Request-Email": "analyst@example.com",
        "X-Auth-Request-Role": "analyst",
      },
      body: JSON.stringify({ hours: 1, clicks: true, conversions: true, detect: true }),
    });

    const response = await POST(request);

    expect(response.status).toBe(403);
    await expect(response.json()).resolves.toEqual({
      detail: "Forbidden",
    });
    expect(proxyToBackend).not.toHaveBeenCalled();
  });

  it("allows admin viewers and forwards the refresh payload", async () => {
    proxyToBackend.mockResolvedValue(
      new Response(JSON.stringify({ success: true }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    const body = JSON.stringify({ hours: 2, clicks: true, conversions: false, detect: false });
    const request = new Request("http://localhost/api/console/refresh", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "X-Auth-Request-User": "admin-1",
        "X-Auth-Request-Email": "admin@example.com",
        "X-Auth-Request-Role": "admin",
      },
      body,
    });

    const response = await POST(request);

    expect(response.status).toBe(200);
    expect(proxyToBackend).toHaveBeenCalledTimes(1);
    expect(proxyToBackend).toHaveBeenCalledWith(
      expect.objectContaining({
        path: "/api/console/admin/refresh",
        method: "POST",
        body,
        viewer: expect.objectContaining({
          userId: "admin-1",
          email: "admin@example.com",
          role: "admin",
        }),
      }),
    );
  });
});
