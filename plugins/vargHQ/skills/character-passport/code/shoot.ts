// Serve this folder and screenshot a page once it sets window.__done = true.
// Usage: bun shoot.ts <page.html> <out.png> [width] [height]
import { chromium } from "playwright-core";
import { existsSync } from "fs";
import { homedir } from "os";

const [page = "blockout_turnaround.html", out = "out.png", w = "1600", h = "600"] = Bun.argv.slice(2);
const dir = import.meta.dir;
const server = Bun.serve({
  port: 0,
  fetch(req) {
    const p = decodeURIComponent(new URL(req.url).pathname);
    const f = Bun.file(dir + (p === "/" ? "/index.html" : p));
    return new Response(f, { headers: { "Access-Control-Allow-Origin": "*" } });
  },
});

// Playwright's headless shell if present, else system Chrome.
const shell = `${homedir()}/Library/Caches/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-mac-arm64/chrome-headless-shell`;
const executablePath = existsSync(shell) ? shell : "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const browser = await chromium.launch({ executablePath, args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const tab = await browser.newPage({ viewport: { width: +w, height: +h } });
tab.on("console", (m) => (m.type() === "error" || m.text().startsWith("expressions")) && console.log("page:", m.text()));
tab.on("pageerror", (e) => console.error("pageerror:", e.message));
await tab.goto(`http://localhost:${server.port}/${page}`);
await tab.waitForFunction(() => (window as any).__done === true, null, { timeout: 90_000 });
await tab.screenshot({ path: out });
console.log("wrote", out);
await browser.close();
server.stop();
