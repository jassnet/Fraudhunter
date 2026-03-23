import { expect, test } from "@playwright/test";

import { prepareBaselineData } from "../helpers/test-data";

test.describe("dashboard e2e", () => {
  test.beforeEach(async ({ request }) => {
    await prepareBaselineData(request);
  });

  test("shows seeded summary metrics for the latest date", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("heading", { name: "ダッシュボード" })).toBeVisible();
    await expect(page.getByText("基準日: 2026-01-21")).toBeVisible();
    await expect(
      page.locator("div").filter({ has: page.getByText("総クリック数") }).first()
    ).toContainText("3,300");
    await expect(
      page.locator("div").filter({ has: page.getByText("総コンバージョン数") }).first()
    ).toContainText("6");

    const suspiciousClicksCard = page.getByRole("link", {
      name: /不審クリック 55件の一覧を確認/i,
    });
    const suspiciousConversionsCard = page.getByRole("link", {
      name: /不審コンバージョン 1件の一覧を確認/i,
    });
    await expect(suspiciousClicksCard).toContainText("55");
    await expect(suspiciousConversionsCard).toContainText("1");
  });

  test("switches dashboard date using the date selector", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("基準日: 2026-01-21")).toBeVisible();

    await page.getByLabel("対象日を選択").selectOption("2026-01-20");

    await expect(page.getByText("基準日: 2026-01-20")).toBeVisible();
    await expect(
      page.locator("div").filter({ has: page.getByText("総クリック数") }).first()
    ).toContainText("22");
    await expect(
      page.getByRole("link", { name: /不審クリック 0件の一覧を確認/i })
    ).toContainText("0");
  });
});
