import { expect, test } from "@playwright/test";
import { dashboardCopy } from "../../src/features/dashboard/copy";
import { prepareBaselineData } from "../helpers/test-data";

test.describe("dashboard e2e", () => {
  test.beforeEach(async ({ request }) => {
    await prepareBaselineData(request);
  });

  test("shows seeded summary metrics for the latest date", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("heading", { name: dashboardCopy.title })).toBeVisible();
    await expect(page.getByText(dashboardCopy.targetDateLabel("2026-01-21"))).toBeVisible();
    await expect(
      page.locator("section").filter({ has: page.getByText(dashboardCopy.labels.clicks) }).first()
    ).toContainText("3,300");
    await expect(
      page.locator("section").filter({ has: page.getByText(dashboardCopy.labels.conversions) }).first()
    ).toContainText("6");

    const suspiciousConversionsBlock = page
      .locator("section")
      .filter({ has: page.getByText(dashboardCopy.labels.suspiciousConversions) })
      .first();
    await expect(suspiciousConversionsBlock).toContainText("1");
  });

  test("switches dashboard date using the date selector", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText(dashboardCopy.targetDateLabel("2026-01-21"))).toBeVisible();

    await page.getByLabel("Target date").selectOption("2026-01-20");

    await expect(page.getByText(dashboardCopy.targetDateLabel("2026-01-20"))).toBeVisible();
    await expect(
      page.locator("section").filter({ has: page.getByText(dashboardCopy.labels.clicks) }).first()
    ).toContainText("22");
    await expect(
      page.locator("section").filter({ has: page.getByText(dashboardCopy.labels.suspiciousConversions) }).first()
    ).toContainText("0");
  });

  test("shows admin actions in the dashboard header", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("button", { name: dashboardCopy.admin.actions.refresh })).toBeVisible();
    await expect(page.getByRole("button", { name: dashboardCopy.admin.actions.masterSync })).toBeVisible();
  });
});
