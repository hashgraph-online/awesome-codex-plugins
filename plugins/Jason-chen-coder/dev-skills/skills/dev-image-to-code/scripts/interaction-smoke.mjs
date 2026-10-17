#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

function usage() {
  console.error([
    'Usage: node interaction-smoke.mjs --url <url> --spec <spec.json> --width <px> --height <px> --out <report.json>',
    '',
    'Spec format:',
    '{',
    '  "checks": [',
    '    {"name":"Select focus","selector":"select","action":"focus"},',
    '    {"name":"Tab click","selector":"[role=tab]:has-text(\\"台面\\")","action":"click","expectAttribute":{"name":"aria-selected","value":"true"}}',
    '  ]',
    '}',
  ].join('\n'));
}

function parseArgs(argv) {
  const args = { wait: 100 };
  for (let i = 0; i < argv.length; i += 1) {
    const key = argv[i];
    if (key.startsWith('--')) {
      args[key.slice(2)] = argv[++i];
    } else {
      throw new Error(`Unknown argument: ${key}`);
    }
  }
  for (const required of ['url', 'spec', 'width', 'height', 'out']) {
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
    throw new Error(`Playwright is required for interaction smoke tests. ${error.message}`);
  }
}

function browserLaunchOptions() {
  const candidates = [
    process.env.CHROME_PATH,
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
  ].filter(Boolean);
  for (const executablePath of candidates) {
    if (fs.existsSync(executablePath)) return { executablePath };
  }
  return {};
}

async function runCheck(page, check) {
  const locator = page.locator(check.selector).first();
  const count = await locator.count();
  if (count === 0) {
    return { ...check, ok: false, error: `Selector not found: ${check.selector}` };
  }

  if (check.action === 'focus') {
    await locator.focus();
  } else if (check.action === 'click') {
    await locator.click();
  } else if (check.action === 'fill') {
    await locator.fill(check.value ?? '');
  } else if (check.action === 'select') {
    await locator.selectOption(check.value);
  } else {
    return { ...check, ok: false, error: `Unknown action: ${check.action}` };
  }

  const assertions = {};
  if (check.expectFocused) {
    assertions.focused = await locator.evaluate((element) => document.activeElement === element);
  }
  if (check.expectValue !== undefined) {
    assertions.value = await locator.inputValue();
  }
  if (check.expectAttribute) {
    assertions.attribute = await locator.getAttribute(check.expectAttribute.name);
  }

  let ok = true;
  if (check.expectFocused) ok = ok && assertions.focused === true;
  if (check.expectValue !== undefined) ok = ok && assertions.value === check.expectValue;
  if (check.expectAttribute) ok = ok && assertions.attribute === check.expectAttribute.value;

  return { ...check, ok, assertions };
}

const args = parseArgs(process.argv.slice(2));
const spec = JSON.parse(fs.readFileSync(args.spec, 'utf8'));
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
const results = [];
try {
  const response = await page.goto(args.url, { waitUntil: 'networkidle' });
  status = response ? response.status() : null;
  if (args.wait > 0) await page.waitForTimeout(args.wait);
  for (const check of spec.checks ?? []) {
    results.push(await runCheck(page, check));
  }
} finally {
  await browser.close();
}

const report = {
  url: args.url,
  viewport: { width: args.width, height: args.height },
  status,
  ok: results.every((result) => result.ok) && pageErrors.length === 0,
  results,
  consoleMessages,
  pageErrors,
};

fs.mkdirSync(path.dirname(path.resolve(args.out)), { recursive: true });
fs.writeFileSync(args.out, `${JSON.stringify(report, null, 2)}\n`);
process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
