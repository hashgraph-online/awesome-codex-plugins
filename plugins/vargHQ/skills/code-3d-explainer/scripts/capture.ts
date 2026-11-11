#!/usr/bin/env bun
// capture.ts: deterministic frame capture of a seekable HTML film -> MP4 / PNG stills / label boxes.
// No npm: drives system Chrome over the DevTools protocol (Bun WebSocket) and pipes frames into ffmpeg.
//
// The page must publish  window.__film = { ready: Promise, fps, duration, width, height, render(t), labels?() }
// (examples/animal-cell/index.html does). Frame i shows exactly t = i / fps. Labels and text are HTML
// over the WebGL canvas, so each frame is a screenshot of the composited page, not a canvas readback.
//
// Usage:
//   bun scripts/capture.ts <project-dir | url> [options]
//   bun scripts/capture.ts examples/animal-cell --out examples/animal-cell/renders/master.mp4 --labels examples/animal-cell/qa/labels.json
//   bun scripts/capture.ts examples/animal-cell --stills 0.5,4.6,12.9,19.5 --still-dir examples/animal-cell/qa/stills
//   bun scripts/capture.ts examples/animal-cell --fps 10 --out /tmp/draft.mp4        # fast draft, 1/3 of the frames
//   bun scripts/capture.ts examples/animal-cell --check 12                          # determinism: 12 times, 2 orders, compare pixels
// Options:
//   --out <file.mp4>       video output (default <dir>/renders/master.mp4)
//   --fps <n>              sample rate (default: the film's fps). --from/--to <s> render a time range
//   --workers <n>          parallel tabs (default 4). Frames are independent, so tabs render out of order
//   --gl auto|gpu|swiftshader   auto = GPU on macOS, SwiftShader elsewhere (software, slower, CI-safe)
//   --format png|jpeg      screenshot format piped to ffmpeg (png = lossless, default; jpeg is faster)
//   --crf <n> --preset <p> x264 settings (default 16, medium). --audio <file> muxes a track (aac)
//   --stills <t,t,...>     write PNG stills instead of a video (--still-dir, default <dir>/qa/stills)
//   --labels <file.json>   also dump every visible label/text box per frame (for scripts/check_labels.ts)
//   --check <n>            determinism test: render n spread-out times forward and in reverse, compare
//   --eval "<js>"          print the JSON value of an expression after load (e.g. "__film.anchors()")
//   --chrome <path>        Chrome/Chromium binary (or env CHROME_PATH)
//   --timeout <s>          deadline for each DevTools call (default 90): a stuck page fails instead of hanging
import { mkdtemp, rm, mkdir, readFile, stat } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, dirname, resolve, extname } from 'node:path';
import { existsSync } from 'node:fs';
import { createHash } from 'node:crypto';

// ---------- args ----------
const argv = Bun.argv.slice(2);
const opt: Record<string, string | boolean> = {}; const pos: string[] = [];
for (let i = 0; i < argv.length; i++) { const a = argv[i]; if (a.startsWith('--')) { const k = a.slice(2); const nx = argv[i + 1]; if (nx === undefined || nx.startsWith('--')) opt[k] = true; else { opt[k] = nx; i++; } } else pos.push(a); }
if (!pos[0] || opt.help) { console.log((await readFile(import.meta.path, 'utf8')).split('\n').filter(l => l.startsWith('//')).map(l => l.slice(3)).join('\n')); process.exit(pos[0] ? 0 : 1); }
const target = pos[0];
const isUrl = /^https?:\/\//.test(target);
const root = isUrl ? '' : resolve(target);
const workers = Number(opt.workers ?? 4);
const fmt = String(opt.format ?? 'png') as 'png' | 'jpeg';
const glMode = String(opt.gl ?? 'auto') === 'auto' ? (process.platform === 'darwin' ? 'gpu' : 'swiftshader') : String(opt.gl);

// ---------- static server (for a project directory) ----------
const TYPES: Record<string, string> = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.css': 'text/css', '.woff2': 'font/woff2', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.glb': 'model/gltf-binary', '.pdb': 'text/plain', '.cif': 'text/plain' };
let server: ReturnType<typeof Bun.serve> | null = null;
let url = target;
if (!isUrl) {
  server = Bun.serve({ port: 0, async fetch(req) {
    let p = decodeURIComponent(new URL(req.url).pathname); if (p.endsWith('/')) p += 'index.html';
    const f = join(root, p); if (!f.startsWith(root) || !existsSync(f)) return new Response('not found', { status: 404 });
    return new Response(Bun.file(f), { headers: { 'content-type': TYPES[extname(f)] || 'application/octet-stream', 'cache-control': 'no-store' } });
  } });
  url = `http://127.0.0.1:${server.port}/index.html`;
}

// ---------- Chrome over CDP ----------
function chromePath() {
  const c = [opt.chrome, process.env.CHROME_PATH, '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Chromium.app/Contents/MacOS/Chromium', '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser'].filter(Boolean) as string[];
  const hit = c.find(p => existsSync(p)); if (!hit) throw new Error('Chrome not found: pass --chrome <path> or set CHROME_PATH'); return hit;
}
const profile = await mkdtemp(join(tmpdir(), 'c3d-chrome-'));
const glFlags = glMode === 'swiftshader' ? ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] : ['--enable-gpu', '--ignore-gpu-blocklist', '--enable-gpu-rasterization'];
const chrome = Bun.spawn([chromePath(), '--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`, '--no-first-run', '--no-default-browser-check', '--hide-scrollbars', '--mute-audio',
  '--disable-background-timer-throttling', '--disable-renderer-backgrounding', '--disable-backgrounding-occluded-windows', '--force-device-scale-factor=1', '--force-color-profile=srgb', ...glFlags, 'about:blank'], { stdout: 'ignore', stderr: 'ignore' });
let wsUrl = '';
for (let i = 0; i < 300 && !wsUrl; i++) { try { const [port, path] = (await readFile(join(profile, 'DevToolsActivePort'), 'utf8')).trim().split('\n'); if (port && path) wsUrl = `ws://127.0.0.1:${port}${path}`; } catch {} if (!wsUrl) await Bun.sleep(50); }
if (!wsUrl) throw new Error('Chrome did not open a DevTools port');
const ws = new WebSocket(wsUrl);
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
let nextId = 1; const pending = new Map<number, { res: (v: any) => void; rej: (e: any) => void }>();
const errors: string[] = [];
ws.onmessage = (ev) => {
  const m = JSON.parse(String(ev.data));
  if (m.id && pending.has(m.id)) { const p = pending.get(m.id)!; pending.delete(m.id); m.error ? p.rej(new Error(`${m.error.message} ${m.error.data || ''}`)) : p.res(m.result); return; }
  if (m.method === 'Runtime.exceptionThrown') errors.push(m.params.exceptionDetails?.exception?.description || m.params.exceptionDetails?.text);
  if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') errors.push(m.params.args.map((a: any) => a.value ?? a.description).join(' '));
};
// every DevTools call has a deadline: a page whose CDN import never arrives must fail, not hang for hours
const TIMEOUT = Number(opt.timeout ?? 90) * 1000;
const send = (method: string, params: any = {}, sessionId?: string) => new Promise<any>((res, rej) => {
  const id = nextId++;
  const timer = setTimeout(() => { pending.delete(id); rej(new Error(`DevTools ${method} timed out after ${TIMEOUT / 1000} s. A stuck page is usually a CDN import (three.js) that never loaded: run scripts/vendor_three.sh <project> to serve it locally, or raise --timeout`)); }, TIMEOUT);
  pending.set(id, { res: (v) => { clearTimeout(timer); res(v); }, rej: (e) => { clearTimeout(timer); rej(e); } });
  ws.send(JSON.stringify({ id, method, params, sessionId }));
});

async function openTab() {
  const { targetId } = await send('Target.createTarget', { url: 'about:blank' });
  const { sessionId } = await send('Target.attachToTarget', { targetId, flatten: true });
  const s = (m: string, p: any = {}) => send(m, p, sessionId);
  await s('Page.enable'); await s('Runtime.enable');
  const evaluate = async (expr: string) => { const r = await s('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true }); if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text); return r.result.value; };
  return { s, evaluate };
}
type Tab = Awaited<ReturnType<typeof openTab>>;

async function load(tab: Tab, w: number, h: number) {
  await tab.s('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 1, mobile: false });
  await tab.s('Page.navigate', { url });
  return tab.evaluate(`(async () => { for (let i = 0; i < 600 && !(window.__film && window.__film.ready); i++) await new Promise(r => setTimeout(r, 50));
    if (!window.__film) throw new Error('page has no window.__film after 30 s: a module import failed or is still downloading (check the import map / network, or run scripts/vendor_three.sh)'); await window.__film.ready;
    const f = window.__film; return { fps: f.fps, duration: f.duration, width: f.width, height: f.height }; })()`);
}
async function frame(tab: Tab, t: number, withLabels: boolean, format = fmt) {
  const labels = await tab.evaluate(`(() => { window.__film.render(${t}); return ${withLabels ? 'window.__film.labels ? window.__film.labels() : []' : 'null'}; })()`);
  const shot = await tab.s('Page.captureScreenshot', { format, quality: format === 'jpeg' ? Number(opt.quality ?? 95) : undefined, optimizeForSpeed: true, captureBeyondViewport: false, fromSurface: true });
  return { buf: Buffer.from(shot.data, 'base64'), labels };
}

const t0 = performance.now();
let exitCode = 0;
try {
  // probe the film size, then open the worker tabs at that size
  const probe = await openTab();
  const film = await load(probe, 1920, 1080);
  const tabs: Tab[] = [probe];
  if (film.width !== 1920 || film.height !== 1080) await load(probe, film.width, film.height);
  const nTabs = opt.eval ? 1 : opt.stills || opt.check ? Math.min(2, workers) : workers;
  await Promise.all(Array.from({ length: nTabs - 1 }, async () => { const t = await openTab(); await load(t, film.width, film.height); tabs.push(t); }));
  const tLoad = performance.now();
  console.log(`loaded ${url} in ${((tLoad - t0) / 1000).toFixed(1)} s: ${film.width}x${film.height}, ${film.duration} s @ ${film.fps} fps, ${tabs.length} tab(s), gl=${glMode}`);
  const fps = Number(opt.fps ?? film.fps);

  if (opt.eval) {
    console.log(JSON.stringify(await tabs[0].evaluate(String(opt.eval)), null, 1));
  } else if (opt.check) {
    const n = Number(opt.check), times = Array.from({ length: n }, (_, i) => +((film.duration * (i + 0.5)) / n).toFixed(4));
    const hashA = new Map<number, string>(), hashB = new Map<number, string>(); const bufA = new Map<number, Buffer>(), bufB = new Map<number, Buffer>();
    for (const t of times) { const { buf } = await frame(tabs[0], t, false, 'png'); hashA.set(t, createHash('sha1').update(buf).digest('hex')); bufA.set(t, buf); }
    const other = tabs[1] || tabs[0];
    for (const t of [...times].reverse()) { const { buf } = await frame(other, t, false, 'png'); hashB.set(t, createHash('sha1').update(buf).digest('hex')); bufB.set(t, buf); }
    let bad = 0; const dir = await mkdtemp(join(tmpdir(), 'c3d-check-'));
    for (const t of times) {
      if (hashA.get(t) === hashB.get(t)) continue;
      const a = join(dir, `a_${t}.png`), b = join(dir, `b_${t}.png`); await Bun.write(a, bufA.get(t)!); await Bun.write(b, bufB.get(t)!);
      const p = Bun.spawnSync(['magick', 'compare', '-metric', 'AE', '-fuzz', '2%', a, b, 'null:']); const ae = Number(String(p.stderr).trim().split(' ')[0]) || 0;
      if (ae > film.width * film.height * 0.0005) { bad++; console.log(`  t=${t}: ${ae} pixels differ beyond 2% fuzz`); } else console.log(`  t=${t}: bytes differ, ${ae} px beyond 2% fuzz (GPU rounding, ok)`);
    }
    await rm(dir, { recursive: true, force: true });
    console.log(bad ? `determinism: FAIL (${bad}/${n} times differ between render orders)` : `determinism: PASS (${n} times, forward vs reverse order, ${tabs.length > 1 ? 'two tabs' : 'one tab'})`);
    if (bad) exitCode = 2;
  } else if (opt.stills) {
    const times = String(opt.stills).split(',').map(Number);
    const dir = resolve(String(opt['still-dir'] ?? join(root || '.', 'qa/stills'))); await mkdir(dir, { recursive: true });
    for (const t of times) { const { buf } = await frame(tabs[0], t, false, 'png'); const f = join(dir, `t${t.toFixed(2).padStart(5, '0')}.png`); await Bun.write(f, buf); console.log(f); }
  } else {
    const from = Number(opt.from ?? 0), to = Number(opt.to ?? film.duration);
    const n = Math.round((to - from) * fps), times = Array.from({ length: n }, (_, i) => +(from + i / fps).toFixed(6));
    const out = resolve(String(opt.out ?? join(root || '.', 'renders/master.mp4'))); await mkdir(dirname(out), { recursive: true });
    const audio = opt.audio ? ['-i', String(opt.audio)] : [];
    const ff = Bun.spawn(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', fmt === 'png' ? 'png' : 'mjpeg', '-i', '-', ...audio,
      '-c:v', 'libx264', '-preset', String(opt.preset ?? 'medium'), '-crf', String(opt.crf ?? 16), '-pix_fmt', 'yuv420p', '-movflags', '+faststart', ...(opt.audio ? ['-c:a', 'aac', '-b:a', '192k', '-shortest'] : []), out], { stdin: 'pipe' });
    const done = new Map<number, Buffer>(); const labelsOut: any[] = new Array(n);
    let next = 0, written = 0; const wantLabels = !!opt.labels; let tick = performance.now();
    const flush = async () => { while (done.has(written)) { ff.stdin.write(done.get(written)!); done.delete(written); written++; if (written % fps === 0) { await ff.stdin.flush(); const now = performance.now(); process.stdout.write(`\r${written}/${n} frames  ${(fps / ((now - tick) / 1000)).toFixed(1)} fps   `); tick = now; } } };
    await Promise.all(tabs.map(async (tab) => { while (next < n) { const i = next++; const { buf, labels } = await frame(tab, times[i], wantLabels); done.set(i, buf); if (wantLabels) labelsOut[i] = { t: times[i], items: labels }; await flush(); } }));
    await flush(); ff.stdin.end();
    if (await ff.exited) throw new Error('ffmpeg failed');
    const tEnd = performance.now(), secs = (tEnd - tLoad) / 1000;
    if (wantLabels) { const lf = resolve(String(opt.labels)); await mkdir(dirname(lf), { recursive: true }); await Bun.write(lf, JSON.stringify({ fps, width: film.width, height: film.height, frames: labelsOut })); console.log(`\nlabel boxes -> ${lf}`); }
    const size = (await stat(out)).size;
    console.log(`\n${n} frames (${(n / fps).toFixed(2)} s of film) -> ${out} (${(size / 1e6).toFixed(1)} MB)`);
    console.log(`render: ${secs.toFixed(1)} s = ${(n / secs).toFixed(1)} frames/s = ${((secs * 1000) / n).toFixed(0)} ms/frame with ${tabs.length} tabs; total incl. load ${((tEnd - t0) / 1000).toFixed(1)} s; realtime factor ${((n / fps) / secs).toFixed(2)}x`);
  }
  if (errors.length) { console.warn(`page errors:\n  ${[...new Set(errors)].join('\n  ')}`); }
} catch (e) {
  console.error(String((e as any)?.stack || e)); if (errors.length) console.error(`page errors:\n  ${[...new Set(errors)].join('\n  ')}`); exitCode = 1;
} finally {
  try { ws.close(); } catch {}
  chrome.kill(); server?.stop(true);
  await rm(profile, { recursive: true, force: true }).catch(() => {});
}
process.exit(exitCode);
