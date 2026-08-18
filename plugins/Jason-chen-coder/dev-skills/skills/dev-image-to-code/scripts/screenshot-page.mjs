#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

function usage() {
  console.error([
    'Usage: node screenshot-page.mjs --url <url> --out <image.png> --width <px> --height <px>',
    'Options: --wait <ms> --full-page --json <report.json>',
  ].join('\n'));
}

function parseArgs(argv) {
  const args = { wait: 500, fullPage: false, json: null };
  for (let i = 0; i < argv.length; i += 1) {
    const key = argv[i];
    if (key === '--full-page') {
      args.fullPage = true;
    } else if (key.startsWith('--')) {
      const name = key.slice(2);
      args[name] = argv[++i];
    } else {
      throw new Error(`Unknown argument: ${key}`);
    }
  }
  for (const required of ['url', 'out', 'width', 'height']) {
    if (!args[required]) {
      usage();
      process.exit(2);
    }
  }
  args.width = Number(args.width);
  args.height = Number(args.height);
  args.wait = Number(args.wait);
  if (!Number.isFinite(args.width) || !Number.isFinite(args.height)) {
    throw new Error('--width and --height must be numbers.');
  }
  return args;
}

async function loadPlaywright() {
  const require = createRequire(import.meta.url);
  const bundledNodeModules = process.env.HOME
    ? path.join(process.env.HOME, '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules')
    : null;
  const candidates = [
    process.env.CODEX_NODE_MODULES,
    bundledNodeModules,
  ].filter(Boolean);
  try {
    return await import('playwright');
  } catch (error) {
    for (const modulesDir of candidates) {
      try {
        return require(path.join(modulesDir, 'playwright'));
      } catch {
        // Try the next known module location.
      }
    }
    throw new Error(`Playwright is required for screenshots. Install it in the target project, set CODEX_NODE_MODULES, or run where it is available. ${error.message}`);
  }
}

function browserLaunchOptions() {
  const candidates = [
    process.env.CHROME_PATH,
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
  ].filter(Boolean);
  for (const executablePath of candidates) {
    if (fs.existsSync(executablePath)) {
      return { executablePath };
    }
  }
  return {};
}

const args = parseArgs(process.argv.slice(2));
const { chromium } = await loadPlaywright();
let browser;
try {
  browser = await chromium.launch();
} catch (error) {
  const fallback = browserLaunchOptions();
  if (!fallback.executablePath) throw error;
  browser = await chromium.launch(fallback);
}
const page = await browser.newPage({
  viewport: { width: args.width, height: args.height },
  deviceScaleFactor: 1,
});

const consoleMessages = [];
const pageErrors = [];
page.on('console', (message) => {
  consoleMessages.push({ type: message.type(), text: message.text() });
});
page.on('pageerror', (error) => {
  pageErrors.push({ message: error.message, stack: error.stack });
});

let status = null;
try {
  const response = await page.goto(args.url, { waitUntil: 'networkidle' });
  status = response ? response.status() : null;
  if (args.wait > 0) {
    await page.waitForTimeout(args.wait);
  }
  fs.mkdirSync(path.dirname(path.resolve(args.out)), { recursive: true });
  await page.screenshot({ path: args.out, fullPage: args.fullPage });
} finally {
  await browser.close();
}

const report = {
  url: args.url,
  output: path.resolve(args.out),
  viewport: { width: args.width, height: args.height },
  fullPage: args.fullPage,
  status,
  consoleMessages,
  pageErrors,
};

const reportPath = args.json || `${args.out}.json`;
fs.writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`);
process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
