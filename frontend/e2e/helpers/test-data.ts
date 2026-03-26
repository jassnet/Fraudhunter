import { APIRequestContext, expect } from "@playwright/test";

const backendPort = process.env.PLAYWRIGHT_BACKEND_PORT || "8001";
const API_BASE_URL =
  process.env.E2E_API_URL || `http://127.0.0.1:${backendPort}`;
const E2E_TEST_KEY = process.env.E2E_TEST_KEY || "fraudchecker-e2e-key";

async function postAndAssertOk(request: APIRequestContext, path: string) {
  const response = await request.post(`${API_BASE_URL}${path}`, {
    headers: {
      "X-Test-Key": E2E_TEST_KEY,
    },
  });

  expect(response.ok()).toBeTruthy();
  const payload = await response.json();
  expect(payload.success).toBeTruthy();
  return payload;
}

export async function resetTestData(request: APIRequestContext) {
  return postAndAssertOk(request, "/api/test/reset");
}

export async function seedBaselineData(request: APIRequestContext) {
  return postAndAssertOk(request, "/api/test/seed/baseline");
}

export async function prepareBaselineData(request: APIRequestContext) {
  await resetTestData(request);
  await seedBaselineData(request);
}
