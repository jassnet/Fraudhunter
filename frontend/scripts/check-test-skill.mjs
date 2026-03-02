import fs from "node:fs";
import path from "node:path";

const rootDir = process.cwd();
const srcDir = path.join(rootDir, "src");
const japanesePattern = /[\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Han}]/u;
const titlePattern = /\b(?:describe|it|test)\s*\(\s*(['"`])((?:\\.|(?!\1).)*)\1/g;
const fireEventPattern = /\bfireEvent\b/g;
const internalMockPattern =
  /\b(?:vi|jest)\.mock\(\s*['"`](?:@\/|\.{1,2}\/)[^'"`]*(?:use-[^'"`/]*|context)[^'"`]*['"`]/gi;

function findTestFiles(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const files = [];

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...findTestFiles(fullPath));
      continue;
    }
    if (entry.isFile() && /\.test\.tsx?$/.test(entry.name)) {
      files.push(fullPath);
    }
  }
  return files;
}

function relative(filePath) {
  return path.relative(rootDir, filePath).replaceAll("\\", "/");
}

const errors = [];
const testFiles = fs.existsSync(srcDir) ? findTestFiles(srcDir) : [];

if (testFiles.length === 0) {
  errors.push("テストファイルが見つかりませんでした（src/**/*.test.ts(x)）。");
}

for (const filePath of testFiles) {
  const content = fs.readFileSync(filePath, "utf8");
  const fileLabel = relative(filePath);

  if (fireEventPattern.test(content)) {
    errors.push(`${fileLabel}: fireEvent の使用は禁止です。userEvent を使用してください。`);
  }

  if (internalMockPattern.test(content)) {
    errors.push(
      `${fileLabel}: hooks/context の直接 mock が検出されました。実コンテキスト + MSW で検証してください。`
    );
  }

  let titleMatch;
  while ((titleMatch = titlePattern.exec(content)) !== null) {
    const [, , rawTitle] = titleMatch;
    if (!japanesePattern.test(rawTitle)) {
      errors.push(`${fileLabel}: テストタイトルは日本語で記述してください -> "${rawTitle}"`);
    }
  }
}

if (errors.length > 0) {
  console.error("[frontend-react-test] 規約違反を検出しました:");
  for (const message of errors) {
    console.error(`- ${message}`);
  }
  process.exit(1);
}

console.log(
  `[frontend-react-test] 規約チェック完了: ${testFiles.length} files, 違反 0 件`
);
