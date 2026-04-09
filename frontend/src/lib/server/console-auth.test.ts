import { afterEach, describe, expect, it, vi } from "vitest";

import { requireConsoleViewer } from "./console-auth";

const ORIGINAL_ENV = { ...process.env };

afterEach(() => {
  process.env = { ...ORIGINAL_ENV };
  vi.restoreAllMocks();
});

describe("requireConsoleViewer", () => {
  it("accepts trusted gateway headers", () => {
    const request = new Request("http://localhost/api/console/dashboard", {
      headers: {
        "X-Auth-Request-User": "analyst-1",
        "X-Auth-Request-Email": "analyst@example.com",
        "X-Auth-Request-Role": "analyst",
      },
    });

    const viewer = requireConsoleViewer(request, "analyst");

    expect(viewer.userId).toBe("analyst-1");
    expect(viewer.email).toBe("analyst@example.com");
    expect(viewer.role).toBe("analyst");
  });

  it("falls back to local dev viewer identity only in dev", () => {
    process.env.FC_ENV = "dev";
    process.env.FC_DEV_CONSOLE_USER = "local-admin";
    process.env.FC_DEV_CONSOLE_EMAIL = "local-admin@example.com";
    process.env.FC_DEV_CONSOLE_ROLE = "admin";

    const request = new Request("http://localhost/api/console/dashboard");
    const viewer = requireConsoleViewer(request, "analyst");

    expect(viewer.userId).toBe("local-admin");
    expect(viewer.email).toBe("local-admin@example.com");
    expect(viewer.role).toBe("admin");
  });

  it("rejects missing identity outside dev", () => {
    process.env.FC_ENV = "production";

    const request = new Request("http://localhost/api/console/dashboard");

    expect(() => requireConsoleViewer(request, "analyst")).toThrowError("Console gateway identity is required.");
  });
});
