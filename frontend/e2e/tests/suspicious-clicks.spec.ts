import { expect, test } from "@playwright/test";

import { prepareBaselineData } from "../helpers/test-data";

test.describe("suspicious clicks e2e", () => {
  test.beforeEach(async ({ request }) => {
    await prepareBaselineData(request);
  });

  test("shows list rows and expandable details", async ({ page }) => {
    await page.goto("/suspicious/clicks");

    await expect(page.getByRole("heading", { name: "不審クリック" })).toBeVisible();
    await expect(page.getByText("1-50件目 / 全55件", { exact: true })).toBeVisible();

    await page.getByRole("searchbox", { name: "一覧を検索" }).fill("Media Alpha");
    await expect(page.getByText("1-1件目 / 全1件", { exact: true })).toBeVisible();
    await page.getByRole("button", { name: "詳細" }).first().click();
    await expect(page.getByText("詳細内訳")).toBeVisible();
    await expect(page.getByRole("cell", { name: "Media Alpha", exact: true })).toBeVisible();
    await expect(page.getByRole("cell", { name: "Affiliate Alpha", exact: true })).toBeVisible();
  });

  test("filters by media name and supports pagination", async ({ page }) => {
    await page.goto("/suspicious/clicks");
    await expect(page.getByText("1-50件目 / 全55件", { exact: true })).toBeVisible();

    const searchInput = page.getByRole("searchbox", { name: "一覧を検索" });
    await searchInput.fill("Media Alpha");
    await expect(page.getByText("1-1件目 / 全1件", { exact: true })).toBeVisible();

    await searchInput.fill("");
    await expect(page.getByText("1-50件目 / 全55件", { exact: true })).toBeVisible();

    await page.getByRole("button", { name: "次へ" }).click();
    await expect(page.getByText("51-55件目 / 全55件", { exact: true })).toBeVisible();
  });
});
