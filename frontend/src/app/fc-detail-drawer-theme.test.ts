import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const dir = dirname(fileURLToPath(import.meta.url));
const globalsCss = readFileSync(join(dir, "globals.css"), "utf8");

describe("fc-detail-drawer テーマ反転（globals.css）", () => {
  it("data-theme=dark のルールでパネル背景が白 (#ffffff)", () => {
    expect(globalsCss).toContain('html[data-theme="dark"] .fc-detail-drawer-panel');
    expect(globalsCss).toContain("background-color: #ffffff");
    const darkIdx = globalsCss.indexOf('html[data-theme="dark"] .fc-detail-drawer-panel');
    const lightIdx = globalsCss.indexOf('html[data-theme="light"] .fc-detail-drawer-panel');
    expect(darkIdx).toBeGreaterThan(-1);
    expect(lightIdx).toBeGreaterThan(darkIdx);
    const darkBlock = globalsCss.slice(darkIdx, lightIdx);
    expect(darkBlock).toContain("background-color: #ffffff");
  });

  it("data-theme=light のルールでパネル背景が黒 (#0a0a0a)", () => {
    expect(globalsCss).toContain('html[data-theme="light"] .fc-detail-drawer-panel');
    const lightIdx = globalsCss.indexOf('html[data-theme="light"] .fc-detail-drawer-panel');
    const nextSection = globalsCss.indexOf("::selection", lightIdx);
    const lightBlock = globalsCss.slice(lightIdx, nextSection > lightIdx ? nextSection : undefined);
    expect(lightBlock).toContain("background-color: #0a0a0a");
  });
});
