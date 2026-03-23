import { expect, test } from "@playwright/test";
import { prepareBaselineData } from "../helpers/test-data";

test.describe("dashboard e2e", () => {
  test.beforeEach(async ({ request }) => {
    await prepareBaselineData(request);
  });

  test("shows seeded summary metrics for the latest date", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("heading", { name: "ダッシュボード" })).toBeVisible();
    await expect(page.getByText("対象日 2026-01-21")).toBeVisible();
    await expect(page.locator("section").filter({ has: page.getByText("クリック") }).first()).toContainText("3,300");
    await expect(page.locator("section").filter({ has: page.getByText("CV") }).first()).toContainText("6");

    const suspiciousClicksBlock = page.getByRole("link", {
      name: /不審クリック 55件を開く/i,
    });
    const suspiciousConversionsBlock = page.getByRole("link", {
      name: /不審コンバージョン 1件を開く/i,
    });
    await expect(suspiciousClicksBlock).toContainText("55");
    await expect(suspiciousConversionsBlock).toContainText("1");
  });

  test("switches dashboard date using the date selector", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("対象日 2026-01-21")).toBeVisible();

    await page.getByLabel("対象日").selectOption("2026-01-20");

    await expect(page.getByText("対象日 2026-01-20")).toBeVisible();
    await expect(page.locator("section").filter({ has: page.getByText("クリック") }).first()).toContainText("22");
    await expect(page.getByRole("link", { name: /不審クリック 0件を開く/i })).toContainText("0");
  });
});
