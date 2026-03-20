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
    await expect(
      page.locator("div").filter({ has: page.getByText("Total Clicks") }).first()
    ).toContainText("3,300");
    await expect(
      page.locator("div").filter({ has: page.getByText("Total Conversions") }).first()
    ).toContainText("6");

    const suspiciousClicksCard = page.getByRole("link", {
      name: /Suspicious Clicks\s+\d+\s+Review/i,
    });
    const suspiciousConversionsCard = page.getByRole("link", {
      name: /Suspicious Conversions\s+\d+\s+Review/i,
    });
    await expect(suspiciousClicksCard).toContainText("55");
    await expect(suspiciousConversionsCard).toContainText("1");
  });

  test("switches dashboard date using the date selector", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Reporting date: 2026-01-21")).toBeVisible();

    await page.getByLabel("Select date").selectOption("2026-01-20");

    await expect(page.getByText("Reporting date: 2026-01-20")).toBeVisible();
    await expect(
      page.locator("div").filter({ has: page.getByText("Total Clicks") }).first()
    ).toContainText("22");
    await expect(
      page.getByRole("link", { name: /Suspicious Clicks\s+\d+\s+Review/i })
    ).toContainText("0");
  });
});
