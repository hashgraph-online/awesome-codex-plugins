// Screenshot engine used by pl.mjs. Zero dependencies: drives the installed Chrome/Edge/Chromium
// over the DevTools protocol (Node 22+). Older Node falls back to plain viewport shots.
import { execFile, spawn, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const sleep = ms => new Promise(r => setTimeout(r, ms));
const KEYS = { Enter: [13, '\r'], Escape: [27], Tab: [9], ArrowDown: [40], ArrowUp: [38], ArrowLeft: [37], ArrowRight: [39], Backspace: [8], ' ': [32, ' '] };

// jobs: [{ file, url, w, h, scale?, scheme?, fullPage?, selector?, padding?, wait?, actions? }]
// → same order: [{ ok, scale } | { ok: false, error }]
export async function capture(jobs) {
  const browser = findBrowser();
  if (!browser) throw new Error('NO_BROWSER: no Chrome, Edge or Chromium found. Set PREVIEW_LAB_CHROME, or capture with your own tools and pass "shots".');
  if (typeof WebSocket === 'undefined') return legacy(browser, jobs);
  const c = await launch(browser);
  try {
    const results = new Array(jobs.length), queue = jobs.map((j, i) => [j, i]);
    await Promise.all(Array.from({ length: Math.min(4, jobs.length) }, async () => {
      while (queue.length) { const [j, i] = queue.shift(); results[i] = await shoot(c, j).catch(e => ({ ok: false, error: e.message })); }
    }));
    return results;
  } finally { await c.close(); }
}

async function launch(browser) {
  const profile = fs.mkdtempSync(join(tmpdir(), 'pl-chrome-'));
  const proc = spawn(browser, ['--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`, '--no-first-run',
    '--no-default-browser-check', '--hide-scrollbars', '--mute-audio', '--disable-gpu', 'about:blank'], { stdio: ['ignore', 'ignore', 'pipe'] });
  const wsUrl = await new Promise((res, rej) => {
    let buf = '';
    const t = setTimeout(() => rej(new Error('the browser did not start in 20s')), 20000);
    proc.stderr.on('data', d => { buf += d; const m = buf.match(/DevTools listening on (ws:\/\/\S+)/); if (m) { clearTimeout(t); res(m[1]); } });
    proc.on('error', e => { clearTimeout(t); rej(e); });
    proc.on('exit', code => { clearTimeout(t); rej(new Error(`the browser exited (${code}) before it was ready`)); });
  });
  const ws = new WebSocket(wsUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = () => rej(new Error('could not connect to the browser')); });
  let id = 0;
  const pending = new Map(), listeners = new Set();
  ws.onmessage = e => {
    const m = JSON.parse(e.data);
    if (!m.id) return listeners.forEach(l => l(m));
    const p = pending.get(m.id); pending.delete(m.id);
    if (p) m.error ? p.rej(new Error(m.error.message)) : p.res(m.result);
  };
  return {
    send: (method, params = {}, sessionId) => new Promise((res, rej) => { pending.set(++id, { res, rej }); ws.send(JSON.stringify({ id, method, params, sessionId })); }),
    once: (sessionId, method, ms) => new Promise((res, rej) => {
      const l = m => { if (m.sessionId === sessionId && m.method === method) { clearTimeout(t); listeners.delete(l); res(m.params); } };
      const t = setTimeout(() => { listeners.delete(l); rej(new Error(`timed out waiting for the page (${method})`)); }, ms);
      listeners.add(l);
    }),
    async close() {
      try { ws.close(); } catch {}
      proc.kill();
      await new Promise(r => (proc.exitCode !== null ? r() : proc.once('exit', r)));
      fs.rmSync(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 100 });
    },
  };
}

async function shoot(c, j) {
  // Own window per shot, sized to the viewport: a background tab paints onto a stale surface and comes out tiled.
  const { targetId } = await c.send('Target.createTarget', { url: 'about:blank', newWindow: true, width: j.w, height: j.h });
  const { sessionId: s } = await c.send('Target.attachToTarget', { targetId, flatten: true });
  const cmd = (m, p) => c.send(m, p, s);
  const evaluate = async expression => {
    const r = await cmd('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    if (r.exceptionDetails) throw new Error((r.exceptionDetails.exception?.description || 'page script error').split('\n')[0]);
    return r.result.value;
  };
  // Scrolls the element into view and returns its box in viewport (x, y) and document (dx, dy) coordinates.
  const box = async sel => {
    const r = await evaluate(`(() => { const e = document.querySelector(${JSON.stringify(sel)}); if (!e) return null;
      e.scrollIntoView({ block: 'center', inline: 'center' }); const r = e.getBoundingClientRect();
      return { x: r.x, y: r.y, w: r.width, h: r.height, dx: r.x + scrollX, dy: r.y + scrollY }; })()`);
    if (!r) throw new Error(`selector not found: ${sel}`);
    return r;
  };
  const waitFor = async w => {
    if (typeof w !== 'string') return sleep(w);
    for (let t = 0; t < 10000; t += 100) { if (await evaluate(`!!document.querySelector(${JSON.stringify(w)})`)) return; await sleep(100); }
    throw new Error(`timed out waiting for selector: ${w}`);
  };
  const mouse = (type, b, extra) => cmd('Input.dispatchMouseEvent', { type, x: b.x + b.w / 2, y: b.y + b.h / 2, ...extra });
  const click = async sel => { const b = await box(sel); await mouse('mouseMoved', b); await mouse('mousePressed', b, { button: 'left', clickCount: 1 }); await mouse('mouseReleased', b, { button: 'left', clickCount: 1 }); };
  try {
    const scale = j.scale || (j.w < 768 ? 2 : 1);
    await cmd('Page.enable');
    await cmd('Emulation.setDeviceMetricsOverride', { width: j.w, height: j.h, deviceScaleFactor: scale, mobile: j.w < 768 });
    await cmd('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: j.scheme === 'dark' ? 'dark' : 'light' }] });
    const loaded = c.once(s, 'Page.loadEventFired', 30000);
    loaded.catch(() => {});
    const nav = await cmd('Page.navigate', { url: j.url });
    if (nav.errorText) throw new Error(`${nav.errorText} (${j.url})`);
    await loaded;
    await waitFor(j.wait ?? 500);
    for (const a of j.actions || []) {
      if (a.click) await click(a.click);
      else if (a.hover) await mouse('mouseMoved', await box(a.hover));
      else if (a.type) { const [sel, text] = a.type; await click(sel); await cmd('Input.insertText', { text: String(text) }); }
      else if (a.press) { const [code, text] = KEYS[a.press] || []; if (!code) throw new Error(`unknown key: ${a.press}`);
        await cmd('Input.dispatchKeyEvent', { type: 'keyDown', key: a.press, windowsVirtualKeyCode: code, ...(text ? { text } : {}) });
        await cmd('Input.dispatchKeyEvent', { type: 'keyUp', key: a.press, windowsVirtualKeyCode: code }); }
      else if (a.scroll !== undefined) typeof a.scroll === 'number' ? await evaluate(`scrollTo(0, ${a.scroll})`) : await box(a.scroll);
      else if (a.wait !== undefined) await waitFor(a.wait);
      else throw new Error(`unknown action: ${JSON.stringify(a)}`);
      if (a.wait === undefined) await sleep(150);
    }
    let clip;
    if (j.selector) { const b = await box(j.selector), p = j.padding || 0; const x = Math.max(0, b.dx - p), y = Math.max(0, b.dy - p); clip = { x, y, width: b.dx + b.w + p - x, height: b.dy + b.h + p - y, scale: 1 }; }
    else if (j.fullPage) { const { cssContentSize: z } = await cmd('Page.getLayoutMetrics'); clip = { x: 0, y: 0, width: z.width, height: Math.min(z.height, 16000), scale: 1 }; }
    const { data } = await cmd('Page.captureScreenshot', { format: 'png', ...(clip ? { clip, captureBeyondViewport: true } : {}) });
    fs.writeFileSync(j.file, Buffer.from(data, 'base64'));
    return { ok: true, scale };
  } finally { await c.send('Target.closeTarget', { targetId }).catch(() => {}); }
}

// Node < 22 has no WebSocket: one Chrome process per shot, viewport only.
function legacy(browser, jobs) {
  return Promise.all(jobs.map(j => new Promise(done => {
    if (j.fullPage || j.selector || j.actions?.length) return done({ ok: false, error: 'fullPage, selector and actions need Node 22+' });
    const profile = fs.mkdtempSync(join(tmpdir(), 'pl-chrome-')), scale = j.scale || (j.w < 768 ? 2 : 1);
    execFile(browser, ['--headless', '--disable-gpu', '--hide-scrollbars', '--no-first-run', '--no-default-browser-check', '--mute-audio',
      `--user-data-dir=${profile}`, `--window-size=${j.w},${j.h}`, `--force-device-scale-factor=${scale}`,
      `--virtual-time-budget=${typeof j.wait === 'number' ? j.wait + 2000 : 2500}`, `--screenshot=${j.file}`,
      `--blink-settings=preferredColorScheme=${j.scheme === 'dark' ? 0 : 1}`, j.url], { timeout: 60000 }, err => {
      fs.rmSync(profile, { recursive: true, force: true });
      done(fs.existsSync(j.file) ? { ok: true, scale } : { ok: false, error: String(err?.message || 'no screenshot produced').slice(0, 200) });
    });
  })));
}

export function findBrowser() {
  if (process.env.PREVIEW_LAB_CHROME) return process.env.PREVIEW_LAB_CHROME;
  const abs = {
    darwin: ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Chromium.app/Contents/MacOS/Chromium',
      '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge', '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'],
    win32: [process.env.PROGRAMFILES, process.env['PROGRAMFILES(X86)'], process.env.LOCALAPPDATA].filter(Boolean).flatMap(p => [
      join(p, 'Google/Chrome/Application/chrome.exe'), join(p, 'Microsoft/Edge/Application/msedge.exe')]),
  }[process.platform] || [];
  const hit = abs.find(p => fs.existsSync(p));
  if (hit) return hit;
  for (const name of ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser', 'microsoft-edge', 'brave-browser']) {
    const r = spawnSync(process.platform === 'win32' ? 'where' : 'which', [name], { encoding: 'utf8' });
    if (r.status === 0) return r.stdout.split('\n')[0].trim();
  }
}
