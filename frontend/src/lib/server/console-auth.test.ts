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
      },
    });

    const viewer = requireConsoleViewer(request);

    expect(viewer.userId).toBe("analyst-1");
    expect(viewer.email).toBe("analyst@example.com");
  });

  it("falls back to local dev viewer identity only in dev", () => {
    process.env.FC_ENV = "dev";
    process.env.FC_DEV_CONSOLE_USER = "local-admin";
    process.env.FC_DEV_CONSOLE_EMAIL = "local-admin@example.com";

    const request = new Request("http://localhost/api/console/dashboard");
    const viewer = requireConsoleViewer(request);

    expect(viewer.userId).toBe("local-admin");
    expect(viewer.email).toBe("local-admin@example.com");
  });

  it("rejects missing identity outside dev", () => {
    process.env.FC_ENV = "production";

    const request = new Request("http://localhost/api/console/dashboard");

    expect(() => requireConsoleViewer(request)).toThrowError("Console gateway identity is required.");
  });
});
