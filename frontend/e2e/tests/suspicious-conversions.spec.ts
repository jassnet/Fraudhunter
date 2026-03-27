import { expect, test } from "@playwright/test";

import { prepareBaselineData } from "../helpers/test-data";

test.describe("suspicious conversions e2e", () => {
  test.beforeEach(async ({ request }) => {
    await prepareBaselineData(request);
  });

  test("shows conversion list and details", async ({ page }) => {
    await page.goto("/suspicious/conversions");

    await expect(page.getByRole("heading", { name: "不審コンバージョン" })).toBeVisible();
    await expect(page.getByRole("columnheader", { name: "CV数" })).toBeVisible();
    await expect(page.getByLabel("結果範囲", { exact: true })).toHaveText("1-1件 / 全1件");

    await page.getByRole("button", { name: "詳細" }).first().click();
    await expect(page.getByText("Click→CV間隔")).toBeVisible();
    await expect(page.getByRole("cell", { name: "Program Alpha", exact: true })).toBeVisible();
  });
});
