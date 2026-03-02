import { expect, test } from "@playwright/test";

import { prepareBaselineData } from "../helpers/test-data";

test.describe("dashboard e2e", () => {
  test.beforeEach(async ({ request }) => {
    await prepareBaselineData(request);
  });

  test("shows seeded summary metrics for the latest date", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
    await expect(page.getByText("Reporting date: 2026-01-21")).toBeVisible();
    await expect(page.getByText("3,300")).toBeVisible();
    await expect(page.getByText("6")).toBeVisible();

    const suspiciousClicksCard = page.getByRole("link", { name: /Suspicious Clicks/i });
    const suspiciousConversionsCard = page.getByRole("link", { name: /Suspicious Conversions/i });
    await expect(suspiciousClicksCard).toContainText("55");
    await expect(suspiciousConversionsCard).toContainText("1");
  });

  test("switches dashboard date using the date selector", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Reporting date: 2026-01-21")).toBeVisible();

    await page.getByLabel("Select date").selectOption("2026-01-20");

    await expect(page.getByText("Reporting date: 2026-01-20")).toBeVisible();
    await expect(page.getByText("22")).toBeVisible();
    await expect(page.getByRole("link", { name: /Suspicious Clicks/i })).toContainText("0");
  });
});
