import { copyFileSync, mkdirSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, "..", "..");
const src = join(repoRoot, "data", "tenders.json");
const destDir = join(__dirname, "..", "public", "data");
const dest = join(destDir, "tenders.json");

if (!existsSync(src)) {
  console.error(`copy-data: source not found at ${src} — run "python run.py" first`);
  process.exit(1);
}

mkdirSync(destDir, { recursive: true });
copyFileSync(src, dest);
console.log(`copy-data: copied ${src} -> ${dest}`);
