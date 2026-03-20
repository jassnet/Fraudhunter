import { expect, test } from "@playwright/test";

import { prepareBaselineData } from "../helpers/test-data";

test.describe("suspicious conversions e2e", () => {
  test.beforeEach(async ({ request }) => {
    await prepareBaselineData(request);
  });

  test("shows conversion list and details", async ({ page }) => {
    await page.goto("/suspicious/conversions");

    await expect(page.getByRole("heading", { name: "Suspicious Conversions" })).toBeVisible();
    await expect(page.getByRole("columnheader", { name: "Conversions" })).toBeVisible();
    await expect(page.getByText("Showing 1-1 of 1")).toBeVisible();

    await page.getByRole("button", { name: "Details" }).first().click();
    await expect(page.getByText("Click to conversion")).toBeVisible();
    await expect(page.getByRole("cell", { name: "Program Alpha", exact: true })).toBeVisible();
  });
});
