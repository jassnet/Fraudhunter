import { expect, test } from "@playwright/test";

import { prepareBaselineData } from "../helpers/test-data";

test.describe("suspicious conversions e2e", () => {
  test.beforeEach(async ({ request }) => {
    await prepareBaselineData(request);
  });

  test("shows conversion list and details", async ({ page }) => {
    await page.goto("/suspicious/conversions");

    await expect(page.getByRole("heading", { name: "不審コンバージョン" })).toBeVisible();
    await expect(page.getByRole("columnheader", { name: "CV 数" })).toBeVisible();
    await expect(page.getByText("1-1件目 / 全1件", { exact: true })).toBeVisible();

    await page.getByRole("button", { name: "詳細" }).first().click();
    await expect(page.getByText("クリックから CV まで")).toBeVisible();
    await expect(page.getByRole("cell", { name: "Program Alpha", exact: true })).toBeVisible();
  });
});
