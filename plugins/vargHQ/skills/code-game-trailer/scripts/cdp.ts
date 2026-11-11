// cdp.ts: a tiny Chrome DevTools Protocol client for Bun (no npm packages).
// Used by capture.ts. Launches the system Google Chrome headless, injects scripts before page
// scripts, sends real keyboard and mouse events, and takes screenshots.
//
//   import { launch } from './cdp.ts';
//   const c = await launch({ width: 1920, height: 1080, gl: 'gpu' });
//   await c.addInitScript(source); await c.goto('http://localhost:8080/');
//   await c.key('keyDown', 'ArrowLeft'); const jpg = await c.screenshot('jpeg', 92);
//
// Chrome is found at $CHROME, then the usual macOS / Linux paths.
// gl: 'gpu' (default, the machine's GPU through ANGLE) or 'swiftshader' (software WebGL: no GPU
// needed, identical pixels on every machine, several times slower at 1080p).
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
  for (const n of ['google-chrome', 'chromium', 'chromium-browser', 'chrome']) {
    const w = Bun.which(n);
    if (w) return w;
  }
  throw new Error('Chrome not found: set CHROME=/path/to/chrome');
}

// key name -> [key, code, keyCode, text]
const KEYS: Record<string, [string, string, number, string?]> = {
  ArrowLeft: ['ArrowLeft', 'ArrowLeft', 37], ArrowUp: ['ArrowUp', 'ArrowUp', 38],
  ArrowRight: ['ArrowRight', 'ArrowRight', 39], ArrowDown: ['ArrowDown', 'ArrowDown', 40],
  Space: [' ', 'Space', 32, ' '], Enter: ['Enter', 'Enter', 13, '\r'], Escape: ['Escape', 'Escape', 27],
  Shift: ['Shift', 'ShiftLeft', 16], Control: ['Control', 'ControlLeft', 17], Alt: ['Alt', 'AltLeft', 18],
  Tab: ['Tab', 'Tab', 9], Backspace: ['Backspace', 'Backspace', 8],
};
export function keyInfo(name: string): [string, string, number, string?] {
  if (KEYS[name]) return KEYS[name];
  if (/^[a-zA-Z]$/.test(name)) return [name.toLowerCase(), `Key${name.toUpperCase()}`, name.toUpperCase().charCodeAt(0), name.toLowerCase()];
  if (/^[0-9]$/.test(name)) return [name, `Digit${name}`, name.charCodeAt(0), name];
  throw new Error(`unknown key "${name}" (use ArrowLeft, Space, Shift, Enter, a-z, 0-9 ...)`);
}

export async function launch({ width = 1920, height = 1080, gl = 'gpu', chrome = '' } = {}) {
  const dir = await mkdtemp(join(tmpdir(), 'game-trailer-chrome-'));
  const glFlags = gl === 'swiftshader'
    ? ['--use-angle=swiftshader', '--enable-unsafe-swiftshader']
    : ['--enable-gpu', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader'];
  const proc = Bun.spawn([
    chrome || findChrome(), '--headless=new', `--user-data-dir=${dir}`, '--remote-debugging-port=0',
    '--no-first-run', '--no-default-browser-check', '--hide-scrollbars', '--mute-audio',
    '--disable-background-timer-throttling', '--disable-renderer-backgrounding', '--disable-backgrounding-occluded-windows',
    '--autoplay-policy=no-user-gesture-required', '--force-color-profile=srgb',
    ...glFlags, `--window-size=${width},${height}`, 'about:blank',
  ], { stdout: 'ignore', stderr: 'ignore' });

  let port = 0; // Chrome writes its debugging port into DevToolsActivePort
  for (let i = 0; i < 150 && !port; i++) {
    try { port = Number((await readFile(join(dir, 'DevToolsActivePort'), 'utf8')).split('\n')[0]); } catch { /* not yet */ }
    if (!port) await Bun.sleep(100);
  }
  if (!port) { proc.kill(); throw new Error('Chrome did not start'); }
  let target: any;
  for (let i = 0; i < 50 && !target; i++) {
    target = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find((t: any) => t.type === 'page');
    if (!target) await Bun.sleep(100);
  }
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });

  let seq = 0;
  const pending = new Map<number, { res: (v: any) => void; rej: (e: Error) => void }>();
  const listeners = new Map<string, ((p: any) => void)[]>();
  const errors: string[] = [], logs: string[] = [];
  ws.onmessage = (ev) => {
    const m = JSON.parse(String(ev.data));
    if (m.id && pending.has(m.id)) {
      const p = pending.get(m.id)!; pending.delete(m.id);
      m.error ? p.rej(new Error(`${m.error.message} ${m.error.data || ''}`.trim())) : p.res(m.result);
      return;
    }
    for (const fn of listeners.get(m.method) || []) fn(m.params);
    if (m.method === 'Runtime.exceptionThrown') {
      const d = m.params.exceptionDetails;
      errors.push(`exception: ${d.exception?.description || d.text}`);
    } else if (m.method === 'Runtime.consoleAPICalled') {
      const text = m.params.args.map((a: any) => a.value ?? a.description ?? '').join(' ');
      (m.params.type === 'error' || m.params.type === 'assert' ? errors : logs).push(`console.${m.params.type}: ${text}`);
    } else if (m.method === 'Log.entryAdded' && m.params.entry.level === 'error') {
      errors.push(`log: ${m.params.entry.text} ${m.params.entry.url || ''}`.trim());
    }
  };
  const send = (method: string, params: object = {}) => new Promise<any>((res, rej) => {
    const id = ++seq;
    pending.set(id, { res, rej });
    ws.send(JSON.stringify({ id, method, params }));
  });
  const once = (method: string) => new Promise<any>((res) => {
    const arr = listeners.get(method) || [];
    const fn = (p: any) => { listeners.set(method, (listeners.get(method) || []).filter((f) => f !== fn)); res(p); };
    arr.push(fn); listeners.set(method, arr);
  });
  await send('Runtime.enable'); await send('Page.enable'); await send('Log.enable');
  await send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: false });

  async function evaluate(expression: string) {
    const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
    return r.result.value;
  }
  const initIds: string[] = [];
  return {
    send, evaluate, errors, logs, port,
    async addInitScript(source: string) { initIds.push((await send('Page.addScriptToEvaluateOnNewDocument', { source })).identifier); },
    async clearInitScripts() { for (const identifier of initIds.splice(0)) await send('Page.removeScriptToEvaluateOnNewDocument', { identifier }); },
    async goto(url: string, timeoutMs = 60000) {
      const loaded = once('Page.loadEventFired');
      const r = await send('Page.navigate', { url });
      if (r.errorText) throw new Error(`navigate ${url}: ${r.errorText}`);
      // a cleared timer, not Bun.sleep: a pending sleep keeps the process alive for the whole timeout
      let timer: any;
      try { await Promise.race([loaded, new Promise((_, rej) => { timer = setTimeout(() => rej(new Error(`load timeout ${url}`)), timeoutMs); })]); }
      finally { clearTimeout(timer); }
    },
    async key(type: 'keyDown' | 'keyUp', name: string) {
      const [key, code, keyCode, text] = keyInfo(name);
      await send('Input.dispatchKeyEvent', {
        type: type === 'keyDown' && text ? 'keyDown' : type === 'keyDown' ? 'rawKeyDown' : 'keyUp',
        key, code, windowsVirtualKeyCode: keyCode, nativeVirtualKeyCode: keyCode, ...(type === 'keyDown' && text ? { text } : {}),
      });
    },
    async mouse(type: 'mouseMoved' | 'mousePressed' | 'mouseReleased' | 'mouseWheel', x: number, y: number, extra: any = {}) {
      await send('Input.dispatchMouseEvent', { type, x, y, button: type === 'mouseMoved' ? 'none' : 'left', clickCount: 1, ...extra });
    },
    async screenshot(format: 'jpeg' | 'png' = 'jpeg', quality = 92): Promise<Uint8Array> {
      const r = await send('Page.captureScreenshot', { format, ...(format === 'jpeg' ? { quality } : {}), optimizeForSpeed: true, captureBeyondViewport: false });
      return Uint8Array.from(atob(r.data), (ch) => ch.charCodeAt(0));
    },
    async close() {
      // Chrome may drop the socket before it answers Browser.close: never wait more than a second
      let timer: any;
      await Promise.race([send('Browser.close').catch(() => {}), new Promise((r) => { timer = setTimeout(r, 1000); })]);
      clearTimeout(timer);
      try { ws.close(); } catch { /* closed */ }
      proc.kill();
      await rm(dir, { recursive: true, force: true }).catch(() => {});
    },
  };
}

export type Chrome = Awaited<ReturnType<typeof launch>>;
