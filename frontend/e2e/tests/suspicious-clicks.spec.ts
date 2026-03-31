import { expect, test } from "@playwright/test";

import { prepareBaselineData } from "../helpers/test-data";

test.describe("legacy suspicious clicks route", () => {
  test.beforeEach(async ({ request }) => {
    await prepareBaselineData(request);
  });

  test("redirects to suspicious conversions", async ({ page }) => {
    await page.goto("/suspicious/clicks");

    await expect(page).toHaveURL(/\/suspicious\/conversions$/);
    await expect(page.getByRole("heading", { name: "不審コンバージョン" })).toBeVisible();
  });
});
