import { NextRequest } from "next/server";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { proxyToBackend } = vi.hoisted(() => ({
  proxyToBackend: vi.fn(),
}));

vi.mock("@/lib/server/backend-proxy", () => ({
  proxyToBackend,
}));

import { GET } from "./route";

describe("dashboard route", () => {
  beforeEach(() => {
    proxyToBackend.mockReset();
  });

  it("allows trusted viewer headers on dashboard routes", async () => {
    proxyToBackend.mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    const request = new NextRequest("http://localhost/api/console/dashboard?status=unhandled", {
      headers: {
        "X-Auth-Request-User": "analyst-1",
        "X-Auth-Request-Email": "analyst@example.com",
      },
    });

    const response = await GET(request);

    expect(response.status).toBe(200);
    expect(proxyToBackend).toHaveBeenCalledTimes(1);
    expect(proxyToBackend).toHaveBeenCalledWith(
      expect.objectContaining({
        path: "/api/console/dashboard",
        search: "?status=unhandled",
        viewer: expect.objectContaining({
          userId: "analyst-1",
          email: "analyst@example.com",
        }),
      }),
    );
  });

  it("rejects missing gateway headers", async () => {
    const request = new NextRequest("http://localhost/api/console/dashboard");

    const response = await GET(request);

    expect(response.status).toBe(403);
    await expect(response.json()).resolves.toEqual({
      detail: "Console gateway identity is required.",
    });
    expect(proxyToBackend).not.toHaveBeenCalled();
  });
});
