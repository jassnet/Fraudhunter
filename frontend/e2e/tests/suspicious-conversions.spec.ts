import { expect, test } from "@playwright/test";
import { suspiciousCopy } from "../../src/features/suspicious-list/copy";
import { prepareBaselineData } from "../helpers/test-data";

test.describe("suspicious conversions e2e", () => {
  test.beforeEach(async ({ request }) => {
    await prepareBaselineData(request);
  });

  test("shows the conversion list and details", async ({ page }) => {
    await page.goto("/suspicious/conversions");

    await expect(page.getByRole("heading", { name: suspiciousCopy.conversionsTitle })).toBeVisible();
    await expect(
      page.getByRole("columnheader", { name: suspiciousCopy.countLabelConversions })
    ).toBeVisible();
    await expect(page.getByLabel(suspiciousCopy.labels.resultRange, { exact: true })).toHaveText(
      "1-1 of 1"
    );

    await page.getByRole("button", { name: suspiciousCopy.labels.detail }).first().click();
    await expect(page.getByText(suspiciousCopy.labels.clickToCvGap)).toBeVisible();
    await expect(page.getByRole("cell", { name: "Program Alpha", exact: true })).toBeVisible();
  });
});
