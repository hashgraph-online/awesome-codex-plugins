// Render driver: serves the film page, launches headless Chrome on the real GPU, receives raw frames, writes PNGs.
//   bun render.ts --out DIR [--w 960 --h 540 --spp 16 --quality draft|final]
//     stills:  --t 12.5,29.5            (global film times)   or  --dev dev_mouse:0.2,dev_mouse:0.6
//     ranges:  --frames 0-1439 [--step 1]   (film frame numbers, 24 fps; existing files are skipped)
//     --set key=value (repeatable, e.g. --set post.exposure=4)   --mode 0..4   --denoise N   --name prefix
import { deflateSync, crc32 } from 'node:zlib';
import { mkdirSync, existsSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const args = process.argv.slice(2);
const opt: Record<string, string[]> = {};
for (let i = 0; i < args.length; i++) {
  if (args[i].startsWith('--')) { const k = args[i].slice(2); const v = args[i + 1] && !args[i + 1].startsWith('--') ? args[++i] : 'true'; (opt[k] ||= []).push(v); }
}
const one = (k: string, d: string) => (opt[k] ? opt[k][opt[k].length - 1] : d);
const ROOT = import.meta.dir;
const out = one('out', '');
if (!out) { console.error('need --out DIR'); process.exit(1); }
mkdirSync(out, { recursive: true });
const w = +one('w', '960'), h = +one('h', '540'), spp = +one('spp', '16'), fps = 24;
const prefix = one('name', 'f');
const set: Record<string, any> = {};
for (const s of opt.set || []) { const i = s.indexOf('='); const k = s.slice(0, i); const v = s.slice(i + 1); set[k] = v.startsWith('[') ? JSON.parse(v) : +v; }

type Frame = { name: string; t?: number; shot?: string; k?: number; mode?: number };
let frames: Frame[] = [];
if (opt.t) for (const s of one('t', '').split(',')) frames.push({ name: `${prefix}_t${(+s).toFixed(2).padStart(6, '0')}.png`, t: +s });
if (opt.dev) for (const s of one('dev', '').split(',')) { const [shot, k] = s.split(':'); frames.push({ name: `${prefix}_${shot}_${(+(k || 0)).toFixed(2)}.png`, shot, k: +(k || 0) }); }
if (opt.frames) {
  const [a, b] = one('frames', '').split('-').map(Number); const step = +one('step', '1');
  for (let f = a; f <= (b ?? a); f += step) frames.push({ name: `${prefix}_${String(f).padStart(5, '0')}.png`, t: (f + 0.5) / fps });
}
const total = frames.length;
const modes = opt.modes ? one('modes', '').split(',').map(Number) : null;
frames = frames.filter(f => !existsSync(join(out, modes ? f.name.replace('.png', `_m${modes[modes.length - 1]}.png`) : f.name)));
if (!frames.length) { console.log(`nothing to do (${total} frames exist)`); process.exit(0); }

const job = { w, h, spp, modes, flatSpp: !!opt.flatspp, quality: one('quality', 'final'), frames, set, mode: +one('mode', '0'), denoise: opt.denoise ? +one('denoise', '4') : undefined, shutter: opt.shutter ? +one('shutter', '0.0208') : undefined };

function png(rgba: Uint8Array, w: number, h: number): Uint8Array {
  const raw = new Uint8Array(h * (1 + w * 3));
  let o = 0, i = 0;
  for (let y = 0; y < h; y++) { raw[o++] = 0; for (let x = 0; x < w; x++) { raw[o++] = rgba[i]; raw[o++] = rgba[i + 1]; raw[o++] = rgba[i + 2]; i += 4; } }
  const z = deflateSync(raw, { level: 2 });
  const chunk = (type: string, data: Uint8Array) => {
    const b = new Uint8Array(12 + data.length); const dv = new DataView(b.buffer);
    dv.setUint32(0, data.length); b.set(new TextEncoder().encode(type), 4); b.set(data, 8);
    dv.setUint32(8 + data.length, crc32(b.subarray(4, 8 + data.length)) >>> 0);
    return b;
  };
  const ihdr = new Uint8Array(13); const dv = new DataView(ihdr.buffer); dv.setUint32(0, w); dv.setUint32(4, h); ihdr[8] = 8; ihdr[9] = 2;
  const sig = new Uint8Array([137, 80, 78, 71, 13, 10, 26, 10]);
  return Buffer.concat([sig, chunk('IHDR', ihdr), chunk('IDAT', z), chunk('IEND', new Uint8Array(0))]);
}

let done = 0; const t0 = Date.now(); let chrome: any; let failed = false;
const finish = (code: number) => { try { chrome?.kill(); } catch {} setTimeout(() => process.exit(code), 150); };
const server = Bun.serve({
  port: 0,
  maxRequestBodySize: 1024 * 1024 * 256,
  async fetch(req) {
    const u = new URL(req.url);
    if (req.method === 'GET') {
      if (u.pathname === '/job') return Response.json(job);
      const rel = u.pathname === '/timeline.json' ? 'timeline.json' : join('src', u.pathname);
      const f = Bun.file(join(ROOT, rel));
      if (await f.exists()) return new Response(f, { headers: { 'cache-control': 'no-store' } });
      return new Response('not found', { status: 404 });
    }
    if (u.pathname === '/log') { console.log('[page]', await req.text()); return new Response('ok'); }
    if (u.pathname === '/fail') { console.error('[page error]', await req.text()); failed = true; finish(2); return new Response('ok'); }
    if (u.pathname === '/frame') {
      const name = u.searchParams.get('name')!; const ms = +u.searchParams.get('ms')!;
      const buf = new Uint8Array(await req.arrayBuffer());
      writeFileSync(join(out, name), png(buf, w, h));
      if (u.searchParams.get('last') === '0') return new Response('ok');
      done++;
      const el = (Date.now() - t0) / 1000; const eta = el / done * (frames.length - done);
      if (frames.length <= 40 || done % 10 === 0 || done === frames.length) console.log(`frame ${done}/${frames.length} ${name} ${(ms / 1000).toFixed(2)}s  elapsed ${el.toFixed(0)}s eta ${eta.toFixed(0)}s`);
      return new Response('ok');
    }
    if (u.pathname === '/done') { console.log(`done ${done} frames in ${((Date.now() - t0) / 1000).toFixed(1)}s`); finish(0); return new Response('ok'); }
    return new Response('?', { status: 404 });
  },
});

const profile = join(process.env.TMPDIR || '/tmp', `smallest-star-chrome-${process.pid}`);
chrome = Bun.spawn(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '--headless=new', '--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist', '--disable-gpu-watchdog', '--disable-gpu-process-crash-limit',
  '--no-first-run', '--no-default-browser-check', '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
  '--disable-backgrounding-occluded-windows', '--disable-extensions', '--mute-audio', `--user-data-dir=${profile}`, `--window-size=${Math.min(w, 1280)},${Math.min(h, 800)}`,
  `http://localhost:${server.port}/film.html`], { stdout: 'ignore', stderr: 'ignore' });
chrome.exited.then((c: number) => { if (!failed && done < frames.length) { console.error(`chrome exited (${c}) after ${done}/${frames.length} frames`); process.exit(3); } });
console.log(`rendering ${frames.length} frame(s) ${w}x${h} spp=${spp} q=${job.quality} -> ${out}`);
