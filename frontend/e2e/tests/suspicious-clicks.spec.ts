import { expect, test } from "@playwright/test";

import { prepareBaselineData } from "../helpers/test-data";

test.describe("suspicious clicks e2e", () => {
  test.beforeEach(async ({ request }) => {
    await prepareBaselineData(request);
  });

  test("shows list rows and expandable details", async ({ page }) => {
    await page.goto("/suspicious/clicks");

    await expect(page.getByRole("heading", { name: "不審クリック" })).toBeVisible();
    await expect(page.getByLabel("結果範囲", { exact: true })).toHaveText("1-50件 / 全55件");

    await page.getByRole("searchbox", { name: "一覧を検索" }).fill("Media Alpha");
    await expect(page.getByLabel("結果範囲", { exact: true })).toHaveText("1-1件 / 全1件");
    await page.getByRole("button", { name: "詳細" }).first().click();
    await expect(page.getByText("概要")).toBeVisible();
    await expect(page.getByRole("cell", { name: "Media Alpha", exact: true })).toBeVisible();
    await expect(page.getByRole("cell", { name: "Affiliate Alpha", exact: true })).toBeVisible();
  });

  test("filters by media name and supports pagination", async ({ page }) => {
    await page.goto("/suspicious/clicks");
    await expect(page.getByLabel("結果範囲", { exact: true })).toHaveText("1-50件 / 全55件");

    const searchInput = page.getByRole("searchbox", { name: "一覧を検索" });
    await searchInput.fill("Media Alpha");
    await expect(page.getByLabel("結果範囲", { exact: true })).toHaveText("1-1件 / 全1件");

    await searchInput.fill("");
    await expect(page.getByLabel("結果範囲", { exact: true })).toHaveText("1-50件 / 全55件");

    await page.getByRole("button", { name: "次へ" }).click();
    await expect(page.getByLabel("結果範囲", { exact: true })).toHaveText("51-55件 / 全55件");
  });

  test("restores deep link search state from the URL", async ({ page }) => {
    await page.goto("/suspicious/clicks?date=2026-01-21&search=Media%20Alpha");

    await expect(page.getByRole("searchbox", { name: "一覧を検索" })).toHaveValue("Media Alpha");
    await expect(page.getByLabel("結果範囲", { exact: true })).toHaveText("1-1件 / 全1件");
  });
});
