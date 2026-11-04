#!/usr/bin/env node
// Clean 2x screenshots of web pages at one laptop-sized viewport, so every screen in the reel has
// the same size and scale. Works for your real store, your tool's pages, or assets/demo-app.html.
//
//   npx -y playwright@1.48.2 install chromium      # once
//   node screenshot.mjs out/ "name|https://your-store.com/products/x" "home|file:///…/demo-app.html?screen=home" …
//
// Log in first in a normal browser if a page needs it, then use that page's public or preview URL;
// this script does not reuse your browser session. Runs with node 18+ or bun + the playwright package.
import { mkdirSync } from "node:fs";
import { join } from "node:path";
import { chromium } from "playwright";

const [outDir, ...jobs] = process.argv.slice(2);
if (!outDir || !jobs.length) {
  console.error('usage: node screenshot.mjs out/ "name|url" ["name|url" …]');
  process.exit(1);
}
mkdirSync(outDir, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });
for (const job of jobs) {
  const cut = job.indexOf("|");
  const [name, url] = [job.slice(0, cut), job.slice(cut + 1)];
  await page.goto(url, { waitUntil: "networkidle" });
  await page.screenshot({ path: join(outDir, `${name}.png`) });
  console.log(join(outDir, `${name}.png`));
}
await browser.close();
