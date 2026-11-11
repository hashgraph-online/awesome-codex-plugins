// capture.ts: record a browser game frame by frame from a director JSON (shot list + inputs + cameras).
//
//   bun scripts/capture.ts director.json                     every shot -> capture/<shot>/00000.jpg ... + capture/manifest.json
//   bun scripts/capture.ts director.json --stills            first, middle and last frame of each shot only (fast look)
//   bun scripts/capture.ts director.json --only s2,s4        re-record some shots (the manifest keeps the others)
//   bun scripts/capture.ts director.json --verify            record the first shot twice as PNG, compare every frame
//
// Options: --out capture  --fps 30  --size 1920x1080  --format jpeg|png  --quality 92  --gl gpu|swiftshader
//          --chrome /path/to/chrome (or $CHROME)
// Local paths in the director ("url", "card") are relative to the director file and served over
// http://127.0.0.1 for the run (ES modules and CDN imports need http, not file://).
// The page gets scripts/virtual-clock.js and scripts/director-runtime.js before its own scripts, so
// frame k of a shot is exactly k / fps seconds of shot time, however slow the machine is.
import { mkdir, rm, readFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, resolve, join, basename } from 'node:path';
import { createHash } from 'node:crypto';
import { launch, type Chrome } from './cdp.ts';

const argv = process.argv.slice(2);
const flag = (n: string) => argv.includes(`--${n}`);
const opt = (n: string, d: string) => { const i = argv.indexOf(`--${n}`); return i >= 0 && argv[i + 1] ? argv[i + 1] : d; };
const directorPath = argv.find((a) => a.endsWith('.json'));
if (!directorPath) { console.error('usage: bun scripts/capture.ts director.json [--stills] [--only id,id] [--verify] [--out dir]'); process.exit(1); }
const D = JSON.parse(await readFile(directorPath, 'utf8'));
const base = dirname(resolve(directorPath));
const fps = Number(opt('fps', String(D.fps ?? 30)));
const [W, H] = opt('size', `${D.width ?? 1920}x${D.height ?? 1080}`).split('x').map(Number);
const format = opt('format', D.format ?? 'jpeg') as 'jpeg' | 'png';
const quality = Number(opt('quality', '92'));
const outDir = resolve(opt('out', D.out ? resolve(base, D.out) : join(base, 'capture')));
const only = opt('only', '').split(',').filter(Boolean);
const stills = flag('stills'), verify = flag('verify');
const here = dirname(new URL(import.meta.url).pathname);
const clockSrc = await readFile(join(here, 'virtual-clock.js'), 'utf8');
const runtimeSrc = await readFile(join(here, 'director-runtime.js'), 'utf8');

// ---------- shot timing: seconds, or beats at the director's bpm ----------
const bpm = D.music?.bpm ?? D.bpm;
const shots = (D.shots as any[]).map((s) => {
  const duration = s.duration ?? (s.beats != null && bpm ? (s.beats * 60) / bpm : null);
  if (!duration) throw new Error(`shot ${s.id}: set "duration" (s) or "beats" (+ "bpm" in the director)`);
  return { ...s, duration };
});
const todo = only.length ? shots.filter((s) => only.includes(s.id)) : shots;
if (only.length && todo.length !== only.length) throw new Error(`unknown shot in --only; shots: ${shots.map((s) => s.id).join(' ')}`);

// ---------- static server for local pages ----------
const mounts: string[] = [];
const server = Bun.serve({
  port: 0, hostname: '127.0.0.1',
  async fetch(req) {
    const u = new URL(req.url), m = u.pathname.match(/^\/m(\d+)\/(.*)$/);
    if (!m || !mounts[+m[1]]) return new Response('not found', { status: 404 });
    const file = resolve(mounts[+m[1]], decodeURIComponent(m[2]) || 'index.html');
    if (!file.startsWith(mounts[+m[1]])) return new Response('forbidden', { status: 403 });
    const f = Bun.file(file);
    return (await f.exists()) ? new Response(f) : new Response('not found', { status: 404 });
  },
});
function pageUrl(ref: string): string {
  if (/^https?:\/\//.test(ref)) return ref;
  const [p, q] = ref.split('?');
  const abs = resolve(base, p), dir = existsSync(abs) && !abs.endsWith('.html') ? abs : dirname(abs);
  const file = abs === dir ? 'index.html' : basename(abs);
  let i = mounts.indexOf(dir); if (i < 0) { mounts.push(dir); i = mounts.length - 1; }
  return `http://127.0.0.1:${server.port}/m${i}/${file}${q ? `?${q}` : ''}`;
}

// ---------- one shot ----------
async function load(c: Chrome, s: any) {
  const seed = s.seed ?? D.seed ?? 1;
  await c.clearInitScripts();
  await c.addInitScript(`window.__VC_CONFIG = ${JSON.stringify({ seed })};\n${clockSrc}\n${runtimeSrc}`);
  await c.goto(pageUrl(s.card ?? s.url ?? D.url));
  // 1) real time: wait until the page's scripts ran (CDN modules load over the network). No virtual time passes.
  const ready = s.card ? 'true' : (s.ready ?? D.ready ?? 'true');
  const t0 = Date.now();
  while (!(await c.evaluate(`document.readyState === 'complete' && (window.__vc.pending().raf > 0 || !!(${ready}))`))) {
    await c.evaluate('window.__vc.flush()');
    if (c.errors.some((e) => e.startsWith('exception: SyntaxError'))) throw new Error(`shot ${s.id}: the page has a syntax error:\n${c.errors.join('\n')}`);
    if (Date.now() - t0 > 60000) throw new Error(`shot ${s.id}: page never queued a frame (ready: ${ready}); errors:\n${c.errors.join('\n')}`);
    await Bun.sleep(50);
  }
  // 2) virtual time: step frames until the ready expression holds (deterministic: same count every run)
  for (let k = 0; !(await c.evaluate(`!!(${ready})`)); k++) {
    if (k > 600) throw new Error(`shot ${s.id}: not ready after 600 frames: ${ready}; page errors:\n${[...new Set(c.errors)].slice(0, 8).join('\n')}`);
    await c.evaluate(`window.__vc.step(${1000 / fps})`);
  }
}

async function recordShot(c: Chrome, s: any, mode: { write: boolean; stillsOnly?: boolean; maxFrames?: number; fmt?: 'jpeg' | 'png' }) {
  await load(c, s);
  if (s.setup) await c.evaluate(s.setup);
  const dt = 1000 / fps;
  for (let k = 0; k < Math.round((s.warmup ?? 0) * fps); k++) await c.evaluate(`window.__vc.step(${dt})`);
  await c.evaluate(`window.__trailer.begin(${JSON.stringify(s)}, ${JSON.stringify(D.hooks || {})})`);
  const n = Math.min(Math.round(s.duration * fps), mode.maxFrames ?? Infinity);
  const speed = s.speed ?? 1;
  const dir = join(outDir, s.id);
  if (mode.write && !mode.stillsOnly) { await rm(dir, { recursive: true, force: true }); await mkdir(dir, { recursive: true }); }
  // inputs -> a timeline of actions at frame indices
  const acts: { f: number; run: () => Promise<any> }[] = [];
  const held = new Set<string>();
  for (const i of s.inputs ?? []) {
    const f0 = Math.max(0, Math.round(i.at * fps));
    if (i.key) {
      acts.push({ f: f0, run: () => { held.add(i.key); return c.key('keyDown', i.key); } });
      acts.push({ f: f0 + Math.max(1, Math.round((i.hold ?? 0) * fps)), run: () => { held.delete(i.key); return c.key('keyUp', i.key); } });
    }
    if (i.eval) acts.push({ f: f0, run: () => c.evaluate(i.eval) });
    if (i.mouse) {
      const [x, y] = i.mouse; const px = x <= 1 ? x * W : x, py = y <= 1 ? y * H : y;
      acts.push({ f: f0, run: async () => { await c.mouse('mouseMoved', px, py); if (i.click) { await c.mouse('mousePressed', px, py); await c.mouse('mouseReleased', px, py); } } });
    }
  }
  acts.sort((a, b) => a.f - b.f);
  const keep = new Set(mode.stillsOnly ? [0, Math.floor(n / 2), n - 1] : []);
  const events: { frame: number; type: string }[] = [], hashes: string[] = [];
  let text = '', probe: any = null, shotMs = 0, writes: Promise<any>[] = [];
  const t0 = performance.now();
  for (let k = 0, a = 0; k < n; k++) {
    while (a < acts.length && acts[a].f <= k) await acts[a++].run();
    for (const e of await c.evaluate(`window.__trailer.tick(${k / fps}, ${dt * speed})`)) events.push({ frame: k, type: e });
    if (k === Math.floor(n / 2)) {
      text = await c.evaluate('window.__trailer.text()');
      if (s.probe ?? (s.card ? null : D.probe)) probe = await c.evaluate(s.probe ?? D.probe);
    }
    if (mode.stillsOnly && !keep.has(k)) continue;
    const img = await c.screenshot(mode.fmt ?? format, quality);
    if (!mode.write) { hashes.push(createHash('md5').update(img).digest('hex')); continue; }
    const name = mode.stillsOnly ? `${s.id}_${k === 0 ? 'a' : k === n - 1 ? 'c' : 'b'}.${format === 'png' ? 'png' : 'jpg'}` : `${String(k).padStart(5, '0')}.${format === 'png' ? 'png' : 'jpg'}`;
    writes.push(Bun.write(join(mode.stillsOnly ? join(outDir, 'stills') : dir, name), img));
    if (writes.length > 16) { await Promise.all(writes); writes = []; }
  }
  await Promise.all(writes);
  shotMs = performance.now() - t0;
  for (const key of held) await c.key('keyUp', key);
  const end = s.probe ?? (s.card ? null : D.probe) ? await c.evaluate(s.probe ?? D.probe) : null;
  await c.evaluate('window.__trailer.end()');
  return { id: s.id, dir: s.id, frames: n, duration: n / fps, speed, events, text: text.trim(), probe_mid: probe, probe_end: end,
    ms_per_frame: +(shotMs / n).toFixed(1), hashes };
}

// ---------- run ----------
const c = await launch({ width: W, height: H, gl: opt('gl', 'gpu'), chrome: opt('chrome', '') });
const started = performance.now();
try {
  if (verify) {
    const s = todo[0], max = Math.min(Math.round(s.duration * fps), 45);
    const a = await recordShot(c, s, { write: false, maxFrames: max, fmt: 'png' });
    const b = await recordShot(c, s, { write: false, maxFrames: max, fmt: 'png' });
    const same = a.hashes.filter((h, i) => h === b.hashes[i]).length;
    console.log(`verify ${s.id}: ${same}/${a.hashes.length} frames identical across two loads (PNG md5)`);
    if (same !== a.hashes.length) console.log(`first difference at frame ${a.hashes.findIndex((h, i) => h !== b.hashes[i])}: a clock, Math.random or load timing leaks in`);
  } else {
    await mkdir(stills ? join(outDir, 'stills') : outDir, { recursive: true });
    const manPath = join(outDir, 'manifest.json');
    const old = !stills && only.length && existsSync(manPath) ? JSON.parse(await readFile(manPath, 'utf8')) : null;
    const results: any[] = [];
    for (const s of todo) {
      const r = await recordShot(c, s, { write: true, stillsOnly: stills });
      delete (r as any).hashes;
      results.push(r);
      console.log(`${s.id}: ${stills ? '3 stills' : `${r.frames} frames`}  ${r.ms_per_frame} ms/frame  events ${r.events.length}  probe ${JSON.stringify(r.probe_end)}`);
    }
    const total = (performance.now() - started) / 1000, frames = results.reduce((n, r) => n + (stills ? 3 : r.frames), 0);
    console.log(`${frames} frames in ${total.toFixed(1)} s (${(total / frames).toFixed(3)} s/frame incl. page loads) -> ${stills ? join(outDir, 'stills') : outDir}`);
    if (!stills) {
      const merged = old ? shots.map((s) => results.find((r) => r.id === s.id) || old.shots.find((r: any) => r.id === s.id)).filter(Boolean) : results;
      await Bun.write(manPath, JSON.stringify({ director: resolve(directorPath), fps, width: W, height: H, format,
        captured: new Date().toISOString(), seconds: +total.toFixed(1), s_per_frame: +(total / frames).toFixed(3), shots: merged }, null, 1));
      console.log(`manifest -> ${manPath}`);
    }
  }
  if (c.errors.length) console.warn(`page errors (${c.errors.length}):\n${[...new Set(c.errors)].slice(0, 12).join('\n')}`);
} finally {
  await c.close();
  server.stop(true);
}
