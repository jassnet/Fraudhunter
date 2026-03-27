import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, resolve, extname } from "node:path";

const root = resolve(process.cwd(), "..");
const targets = [
  join(root, ".editorconfig"),
  join(root, ".gitattributes"),
  join(root, "frontend", "src"),
  join(root, "frontend", "e2e"),
  join(root, "docs"),
];

const extensions = new Set([".ts", ".tsx", ".css", ".md", ".json", ".yml", ".yaml"]);
let hasFailure = false;

function visit(path) {
  const stat = statSync(path);
  if (stat.isDirectory()) {
    for (const entry of readdirSync(path)) {
      visit(join(path, entry));
    }
    return;
  }

  if (!extensions.has(extname(path)) && !path.endsWith(".editorconfig") && !path.endsWith(".gitattributes")) {
    return;
  }

  const buffer = readFileSync(path);
  if (buffer[0] === 0xef && buffer[1] === 0xbb && buffer[2] === 0xbf) {
    console.error(`UTF-8 BOM detected: ${path}`);
    hasFailure = true;
  }

  const text = buffer.toString("utf8");
  if (text.includes("\uFFFD")) {
    console.error(`Replacement character detected: ${path}`);
    hasFailure = true;
  }
}

for (const target of targets) {
  visit(target);
}

if (hasFailure) {
  process.exit(1);
}

console.log("UTF-8 check passed");
