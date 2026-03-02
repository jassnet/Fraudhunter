import fs from "node:fs";
import path from "node:path";

const rootDir = process.cwd();
const summaryPath = path.join(rootDir, "coverage", "coverage-summary.json");
const focusFiles = [
  "src/app/page.tsx",
  "src/components/suspicious-list-page.tsx",
  "src/lib/api.ts",
];

const toKey = (value) => value.replaceAll("\\", "/").toLowerCase();

if (!fs.existsSync(summaryPath)) {
  console.log("[coverage-check] coverage-summary.json がありません。先に `npm run test:coverage` を実行してください。");
  process.exit(0);
}

const summary = JSON.parse(fs.readFileSync(summaryPath, "utf8"));
const entries = Object.entries(summary).filter(([key]) => key !== "total");

function findEntry(targetFile) {
  const normalizedTarget = toKey(targetFile);
  return entries.find(([key]) => {
    const normalizedKey = toKey(key);
    return normalizedKey.endsWith(normalizedTarget);
  });
}

const total = summary.total;
console.log("[coverage-check] 全体カバレッジ");
console.log(
  `- lines: ${total.lines.pct}% | statements: ${total.statements.pct}% | functions: ${total.functions.pct}% | branches: ${total.branches.pct}%`
);

console.log("[coverage-check] 重点ファイル");
for (const file of focusFiles) {
  const entry = findEntry(file);
  if (!entry) {
    console.log(`- ${file}: 対象外 (計測結果なし)`);
    continue;
  }

  const [, metrics] = entry;
  console.log(
    `- ${file}: lines ${metrics.lines.pct}% / functions ${metrics.functions.pct}% / branches ${metrics.branches.pct}%`
  );
}

console.log("[coverage-check] 第1段階はレポートのみ（閾値failなし）です。");
