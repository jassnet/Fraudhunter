import { defineConfig } from "@playwright/test";

const FRONTEND_PORT = Number(process.env.PLAYWRIGHT_FRONTEND_PORT || 3000);
const BACKEND_PORT = Number(process.env.PLAYWRIGHT_BACKEND_PORT || 8001);
const FRONTEND_URL = `http://127.0.0.1:${FRONTEND_PORT}`;
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`;
const E2E_TEST_KEY = process.env.E2E_TEST_KEY || "fraudchecker-e2e-key";
const databaseUrl = process.env.FRAUD_TEST_DATABASE_URL || process.env.DATABASE_URL;
const CORS_ORIGINS = [
  FRONTEND_URL,
  `http://localhost:${FRONTEND_PORT}`,
  BACKEND_URL,
  `http://localhost:${BACKEND_PORT}`,
].join(",");

if (!databaseUrl) {
  throw new Error("Set FRAUD_TEST_DATABASE_URL (or DATABASE_URL) before running Playwright E2E tests.");
}

export default defineConfig({
  testDir: "./e2e/tests",
  timeout: 45_000,
  expect: {
    timeout: 10_000,
  },
  workers: 1,
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  use: {
    baseURL: FRONTEND_URL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  webServer: [
    {
      command: `python -m fraud_checker.migrations && python -m uvicorn fraud_checker.api:app --host 127.0.0.1 --port ${BACKEND_PORT} --app-dir ./src`,
      cwd: "../backend",
      url: `${BACKEND_URL}/`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        ...process.env,
        DATABASE_URL: databaseUrl,
        FC_ENV: "test",
        FC_E2E_TEST_KEY: E2E_TEST_KEY,
        FC_ADMIN_API_KEY: E2E_TEST_KEY,
        FC_ALLOW_INSECURE_ADMIN: "true",
        FC_CORS_ORIGINS: CORS_ORIGINS,
        PYTHONPATH: "./src",
      },
    },
    {
      command: `npm run dev -- --hostname 127.0.0.1 --port ${FRONTEND_PORT}`,
      cwd: ".",
      url: `${FRONTEND_URL}/`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        ...process.env,
        NEXT_PUBLIC_API_URL: BACKEND_URL,
        NEXT_DIST_DIR: ".next-playwright",
        FC_ADMIN_API_KEY: E2E_TEST_KEY,
      },
    },
  ],
});
