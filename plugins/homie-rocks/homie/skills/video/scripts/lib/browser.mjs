/**
 * A headless Chrome on the GPU, driven with puppeteer-core from the studio's own
 * node_modules (it comes with @homie-rocks/studio). A software renderer runs a
 * WebGL game at about one frame a second and makes it look stuck, so the GPU
 * flags are not optional.
 *
 * On Linux with no GPU (a cloud session, CI) Chrome draws WebGL with SwiftShader (it needs
 * --enable-unsafe-swiftshader since Chrome 137), and a Chrome for Testing on an Ubuntu that restricts unprivileged
 * user namespaces (23.10 and later), or a Chrome run as root, starts only without its sandbox: the same rules as
 * @homie-rocks/studio's own checks (lib/chrome.mjs). Pages are opened in throwaway profiles.
 */
import { existsSync, mkdtempSync, readFileSync, readdirSync, rmSync } from 'node:fs';
import { createRequire } from 'node:module';
import { homedir, tmpdir } from 'node:os';
import { join } from 'node:path';

export const CHROMES = [
  process.env.CHROME_PATH,
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/Applications/Chromium.app/Contents/MacOS/Chromium',
  '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser', '/opt/google/chrome/chrome',
].filter(Boolean);

function noSandboxNeeded() {
  if (process.platform !== 'linux') return false;
  if (typeof process.getuid === 'function' && process.getuid() === 0) return true;
  try { return readFileSync('/proc/sys/kernel/apparmor_restrict_unprivileged_userns', 'utf8').trim() === '1'; } catch { return false; }
}

export const GPU_FLAGS = process.platform === 'darwin'
  ? ['--use-angle=metal', '--enable-gpu-rasterization', '--ignore-gpu-blocklist']
  : ['--enable-gpu-rasterization', '--ignore-gpu-blocklist', '--use-gl=angle', '--enable-unsafe-swiftshader', '--disable-dev-shm-usage', ...(noSandboxNeeded() ? ['--no-sandbox'] : [])];

/** The newest build in a Chrome for Testing cache (`homie-studio chrome install` keeps one in .cache/homie-studio in the home folder). */
function newestIn(dir, rel) {
  if (!existsSync(dir)) return null;
  const builds = readdirSync(dir, { withFileTypes: true }).filter((d) => d.isDirectory()).map((d) => d.name).sort((a, b) => b.localeCompare(a, 'en', { numeric: true }));
  for (const b of builds) for (const r of rel) { const path = join(dir, b, ...r); if (existsSync(path)) return path; }
  return null;
}

export function chromePath() {
  return CHROMES.find((p) => existsSync(p))
    ?? newestIn(join(homedir(), '.cache', 'homie-studio', 'chrome', 'chrome'), [['chrome-linux64', 'chrome'], ['chrome-mac-arm64', 'Google Chrome for Testing.app', 'Contents', 'MacOS', 'Google Chrome for Testing'], ['chrome-mac-x64', 'Google Chrome for Testing.app', 'Contents', 'MacOS', 'Google Chrome for Testing']])
    ?? null;
}

export function loadPuppeteer(root) {
  const tries = [root ? join(root, 'package.json') : null, join(process.cwd(), 'package.json')].filter(Boolean);
  for (const from of tries) {
    try { const m = createRequire(from)('puppeteer-core'); return m.default ?? m; } catch { /* next */ }
  }
  return null;
}

/** Launch; returns { browser, close } where close() also deletes the throwaway profile. */
export async function launch(root, { width = 1920, height = 1080, extra = [] } = {}) {
  const exe = chromePath();
  if (!exe) throw new Error('no Chrome found (set CHROME_PATH to a Chrome or Chromium; on Linux, `npx --no-install homie-studio chrome install` in a studio fetches Chrome for Testing)');
  const puppeteer = loadPuppeteer(root);
  if (!puppeteer) throw new Error('puppeteer-core is not installed (it comes with @homie-rocks/studio: run npm install in the studio)');
  const profile = mkdtempSync(join(tmpdir(), 'homie-video-'));
  // 150 s for Chrome to start: on a loaded computer a cold start has taken over a minute.
  const browser = await puppeteer.launch({
    executablePath: exe, headless: true, userDataDir: profile, timeout: 150_000, protocolTimeout: 180_000,
    args: [...GPU_FLAGS, `--window-size=${width},${height}`, '--hide-scrollbars', '--no-first-run', '--no-default-browser-check', '--disable-background-timer-throttling', '--disable-renderer-backgrounding', '--force-color-profile=srgb', ...extra],
  });
  const close = async () => {
    try { await Promise.race([browser.close(), new Promise((r) => setTimeout(r, 8000))]); } catch { /* */ }
    try { browser.process()?.kill('SIGKILL'); } catch { /* */ }
    rmSync(profile, { recursive: true, force: true });
  };
  return { browser, close, pid: browser.process()?.pid ?? null };
}

/** Render HTML to a PNG at an exact size (cards, contact sheets): text comes out right with no font setup. */
export async function htmlToPng(root, html, out, { width, height }) {
  const { browser, close } = await launch(root, { width, height });
  try {
    const page = await browser.newPage();
    await page.setViewport({ width, height, deviceScaleFactor: 1 });
    await page.setContent(html, { waitUntil: 'load' });
    await page.evaluate(() => document.fonts?.ready);
    await page.screenshot({ path: out, clip: { x: 0, y: 0, width, height } });
  } finally { await close(); }
  return out;
}
