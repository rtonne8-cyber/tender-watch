import { copyFileSync, mkdirSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, "..", "..");
const destDir = join(__dirname, "..", "public", "data");

mkdirSync(destDir, { recursive: true });

for (const name of ["tenders.json", "signals.json"]) {
  const src = join(repoRoot, "data", name);
  if (!existsSync(src)) {
    console.error(`copy-data: source not found at ${src} — run "python run.py" / "python run_signals.py" first`);
    process.exit(1);
  }
  const dest = join(destDir, name);
  copyFileSync(src, dest);
  console.log(`copy-data: copied ${src} -> ${dest}`);
}
