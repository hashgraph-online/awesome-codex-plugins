// design-helper verification: computed style, DOM counts and a screenshot of the sheet.
//
//   node check.cjs <url> <shot.png> [--section r1-2] [--sel '.spec .target'] [--props borderRadius,boxShadow] [--width 1600]
//
// Run it from the project root so the project's own Playwright is found first.
// Prints one JSON report. Prints NO_PLAYWRIGHT and exits 0 when no Playwright or browser
// can be launched, so the caller can skip the step silently.
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execSync } = require('child_process');

const argv = process.argv.slice(2);
const opt = (k, d) => { const i = argv.indexOf(k); return i < 0 ? d : argv.splice(i, 2)[1]; };
const section = opt('--section');
const sel = opt('--sel');
const props = (opt('--props', '') || '').split(',').filter(Boolean);
const width = +opt('--width', 1600);
const [url, shot] = argv;
if (!url || !shot) {
  console.error('usage: node check.cjs <url> <shot.png> [--section id] [--sel css] [--props a,b] [--width n]');
  process.exit(2);
}

const ver = d => { try { return require(path.join(d, 'package.json')).version.split('.').map(Number); } catch { return [0]; } };
const newer = (a, b) => { for (let i = 0; i < 3; i++) if ((b[i] || 0) !== (a[i] || 0)) return (b[i] || 0) - (a[i] || 0); return 0; };
const dirs = p => { try { return fs.readdirSync(p).map(f => path.join(p, f)); } catch { return []; } };

// Playwright modules: the project's, then global, then the npx cache (newest first).
function modules() {
  const out = [];
  for (const name of ['playwright', 'playwright-core', '@playwright/test']) {
    try { out.push(path.dirname(require.resolve(name + '/package.json', { paths: [process.cwd()] }))); } catch {}
  }
  try {
    const g = execSync('npm root -g', { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
    for (const name of ['playwright', 'playwright-core']) if (fs.existsSync(path.join(g, name))) out.push(path.join(g, name));
  } catch {}
  const npx = dirs(path.join(os.homedir(), '.npm', '_npx'))
    .flatMap(d => ['playwright', 'playwright-core'].map(n => path.join(d, 'node_modules', n)))
    .filter(d => fs.existsSync(d))
    .sort((a, b) => newer(ver(a), ver(b)));
  return [...new Set([...out, ...npx])];
}

// Browsers Playwright has downloaded, for when a module's own revision is missing.
function browsers() {
  const roots = [process.env.PLAYWRIGHT_BROWSERS_PATH,
    path.join(os.homedir(), 'Library', 'Caches', 'ms-playwright'),
    path.join(os.homedir(), '.cache', 'ms-playwright'),
    process.env.LOCALAPPDATA && path.join(process.env.LOCALAPPDATA, 'ms-playwright')].filter(Boolean);
  const names = new Set(['Chromium', 'Google Chrome for Testing', 'chrome', 'chrome.exe',
    'chrome-headless-shell', 'chrome-headless-shell.exe']);
  const found = [];
  const walk = (d, depth) => {
    for (const p of dirs(d)) {
      let st; try { st = fs.statSync(p); } catch { continue; }
      if (st.isDirectory() && depth > 0) walk(p, depth - 1);
      else if (st.isFile() && names.has(path.basename(p))) found.push(p);
    }
  };
  for (const r of roots) for (const d of dirs(r)) if (/chromium/.test(path.basename(d))) walk(d, 5);
  const rev = p => +(p.match(/chromium[^/\\]*-(\d+)/) || [0, 0])[1];
  return found.sort((a, b) => rev(b) - rev(a));
}

async function launch() {
  const exes = browsers();
  for (const m of modules()) {
    let chromium;
    try { ({ chromium } = require(m)); } catch { continue; }
    if (!chromium) continue;
    for (const o of [{}, ...exes.map(e => ({ executablePath: e })), { channel: 'chrome' }]) {
      try { return await chromium.launch(o); } catch {}
    }
  }
  return null;
}

(async () => {
  const b = await launch();
  if (!b) { console.log('NO_PLAYWRIGHT'); return; }
  try {
    const p = await b.newPage({ viewport: { width, height: 1000 } });
    await p.goto(url, { waitUntil: 'load' });
    await p.evaluate(() => document.fonts && document.fonts.ready);
    await p.waitForTimeout(300);

    const report = await p.evaluate(({ sel, props, section }) => {
      const root = section ? document.getElementById(section) : document;
      const r = {
        sections: [...document.querySelectorAll('section')].map(s => ({
          id: s.id, specs: s.querySelectorAll('.spec').length,
          overflowX: [...s.querySelectorAll('.grid')].some(g => g.scrollWidth > g.clientWidth + 1),
        })),
        pageOverflowX: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
      };
      if (section && !root) r.missingSection = section;
      if (sel && root) {
        const els = [...root.querySelectorAll(sel)];
        r.matched = els.length;
        r.values = els.map(e => { const c = getComputedStyle(e); return props.map(k => c[k]).join(' | '); });
        r.distinct = new Set(r.values).size;
      }
      return r;
    }, { sel, props, section });

    const el = section && await p.$('#' + section);
    if (el) await el.screenshot({ path: shot });
    else await p.screenshot({ path: shot, fullPage: true });
    report.shot = shot;
    console.log(JSON.stringify(report, null, 1));
  } finally {
    await b.close();
  }
})().catch(e => { console.error(String(e && e.message || e)); process.exit(1); });
