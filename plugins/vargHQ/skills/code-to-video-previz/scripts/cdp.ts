// A minimal Chrome DevTools Protocol client for Bun: no npm packages, no browser-automation library.
// Launches headless Chrome with software WebGL (SwiftShader), so it works on machines without a GPU
// and gives the same pixels on every run.
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

export function findChrome(): string {
  const paths = [
    process.env.CHROME,
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser',
  ].filter(Boolean) as string[];
  for (const p of paths) if (existsSync(p)) return p;
  for (const n of ['google-chrome', 'chromium', 'chromium-browser', 'chrome-headless-shell', 'chrome']) {
    const w = Bun.which(n);
    if (w) return w;
  }
  throw new Error('Chrome not found: set CHROME=/path/to/chrome');
}

export async function launch({ width = 1280, height = 800 } = {}) {
  const dir = await mkdtemp(join(tmpdir(), 'animatic-chrome-'));
  const proc = Bun.spawn([
    findChrome(), '--headless=new', `--user-data-dir=${dir}`, '--remote-debugging-port=0',
    '--no-first-run', '--no-default-browser-check', '--hide-scrollbars', '--mute-audio',
    '--use-angle=swiftshader', '--enable-unsafe-swiftshader', `--window-size=${width},${height}`, 'about:blank',
  ], { stdout: 'ignore', stderr: 'ignore' });

  let port = 0; // Chrome writes its debugging port into DevToolsActivePort
  for (let i = 0; i < 150 && !port; i++) {
    try { port = Number((await readFile(join(dir, 'DevToolsActivePort'), 'utf8')).split('\n')[0]); } catch { /* not yet */ }
    if (!port) await Bun.sleep(100);
  }
  if (!port) { proc.kill(); throw new Error('Chrome did not start'); }
  let page: any;
  for (let i = 0; i < 50 && !page; i++) {
    page = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find((t: any) => t.type === 'page');
    if (!page) await Bun.sleep(100);
  }
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });

  let seq = 0;
  const pending = new Map<number, { res: (v: any) => void; rej: (e: Error) => void }>();
  const errors: string[] = [], warnings: string[] = [];
  ws.onmessage = ev => {
    const m = JSON.parse(String(ev.data));
    if (m.id && pending.has(m.id)) {
      const p = pending.get(m.id)!; pending.delete(m.id);
      m.error ? p.rej(new Error(m.error.message)) : p.res(m.result);
      return;
    }
    if (m.method === 'Runtime.exceptionThrown') {
      const d = m.params.exceptionDetails;
      errors.push(`exception: ${d.exception?.description || d.text}`);
    } else if (m.method === 'Runtime.consoleAPICalled' && ['error', 'warning', 'assert'].includes(m.params.type)) {
      const text = m.params.args.map((a: any) => a.value ?? a.description ?? '').join(' ');
      (m.params.type === 'warning' ? warnings : errors).push(`console.${m.params.type}: ${text}`);
    } else if (m.method === 'Log.entryAdded' && m.params.entry.level === 'error') {
      errors.push(`log: ${m.params.entry.text} ${m.params.entry.url || ''}`.trim());
    }
  };
  const send = (method: string, params: object = {}) => new Promise<any>((res, rej) => {
    const id = ++seq;
    pending.set(id, { res, rej });
    ws.send(JSON.stringify({ id, method, params }));
  });
  await send('Runtime.enable'); await send('Page.enable'); await send('Log.enable');
  await send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: false });

  async function evaluate(expression: string) {
    const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
    return r.result.value;
  }
  // Waits for the page's ready flag; three.js comes from a CDN, so allow for the first download.
  async function goto(url: string, ready = 'window.__ready === true', timeoutMs = 60000) {
    await send('Page.navigate', { url });
    const t0 = Date.now();
    while (Date.now() - t0 < timeoutMs) {
      try { if (await evaluate(ready)) return; } catch { /* navigating */ }
      await Bun.sleep(100);
    }
    throw new Error(`not ready after ${timeoutMs / 1000} s: ${url}\n${errors.join('\n')}`);
  }
  async function screenshot(path: string) {
    const r = await send('Page.captureScreenshot', { format: 'png' });
    await Bun.write(path, Buffer.from(r.data, 'base64'));
  }
  // Renders one moment through the page's __frame hook and returns PNG bytes.
  async function frame(expr: string): Promise<Buffer> {
    const url: string = await evaluate(expr);
    return Buffer.from(url.slice(url.indexOf(',') + 1), 'base64');
  }
  async function close() {
    try { ws.close(); } catch { /* closed */ }
    proc.kill();
    await proc.exited;
    await rm(dir, { recursive: true, force: true });
  }
  return { send, evaluate, goto, screenshot, frame, close, errors, warnings };
}

export function args(defaults: Record<string, string | boolean>) {
  const out: Record<string, string | boolean> = { ...defaults };
  const a = process.argv.slice(2);
  for (let i = 0; i < a.length; i++) {
    if (!a[i].startsWith('--')) continue;
    const k = a[i].slice(2), next = a[i + 1];
    if (next === undefined || next.startsWith('--')) out[k] = true;
    else { out[k] = next; i++; }
  }
  return out;
}
