import { expect, test } from "@playwright/test";

import { prepareBaselineData } from "../helpers/test-data";

test.describe("suspicious clicks e2e", () => {
  test.beforeEach(async ({ request }) => {
    await prepareBaselineData(request);
  });

  test("shows list rows and expandable details", async ({ page }) => {
    await page.goto("/suspicious/clicks");

    await expect(page.getByRole("heading", { name: "Suspicious Clicks" })).toBeVisible();
    await expect(page.getByText("Showing 1-50 of 55")).toBeVisible();

    await page.getByRole("button", { name: "Details" }).first().click();
    await expect(page.getByText("Breakdown")).toBeVisible();
    await expect(page.getByText("Media Alpha")).toBeVisible();
    await expect(page.getByText("Affiliate Alpha")).toBeVisible();
  });

  test("filters by media name and supports pagination", async ({ page }) => {
    await page.goto("/suspicious/clicks");
    await expect(page.getByText("Showing 1-50 of 55")).toBeVisible();

    const searchInput = page.getByRole("searchbox", { name: "Search suspicious list" });
    await searchInput.fill("Media Alpha");
    await expect(page.getByText("Showing 1-1 of 1")).toBeVisible();

    await searchInput.fill("");
    await expect(page.getByText("Showing 1-50 of 55")).toBeVisible();

    await page.getByRole("button", { name: "Next" }).click();
    await expect(page.getByText("Showing 51-55 of 55")).toBeVisible();
  });
});
