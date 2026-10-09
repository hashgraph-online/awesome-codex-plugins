#!/usr/bin/env node
/**
 * art.mjs: a game's cover, painted backdrops and textures, made at build time and never while
 * anyone plays. Real frames come from the running game for free; generated images come from fal
 * through the creator's own account, priced first, capped by a budget, receipted the moment fal
 * accepts them.
 *
 *   check                                   ffmpeg, Chrome, the studio, the fal key (a free check)
 *   frame <game> --url <site> [--view tv|play] [--seconds 12] [--slug <art job>]
 *                                           real frames of the game playing, the busiest one picked
 *   cover <game> --from <image> [--focus x,y]
 *                                           the game's cover: 16:9, 1600x900 JPEG, into the game, named in game.json
 *   budget <slug> --cap <usd>               what the person agreed to spend on this art job
 *   price --model <fal model> --input <input.json>
 *   gen <slug> --model <fal model> --input <input.json> --out <file> [--dry-run | --yes]
 *                                           one paid image (or a few), inside the cap, resumable, receipted
 *   tile <image>                            does a texture tile without a seam? numbers and a 2x2 preview
 *   fit <image> --out <file> [--width 1024] [--max-kb 300]
 *                                           a texture or backdrop at a size a phone can download
 *   sheet <folder>                          a labelled contact sheet of every image in a folder
 *
 * Every command takes --json. Run it from inside the studio (the folder with studio.json).
 */
import { spawnSync } from 'node:child_process';
import { appendFileSync, existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
import { dirname, extname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { experienceDir, experienceJson, SLUG, checkBudget, findStudio, readBudget, readJson, setBudget, writeJson } from '../../music/scripts/lib/studio.mjs';
import { GPU_FLAGS, chromePath, htmlToPng, loadPuppeteer } from '../../video/scripts/lib/browser.mjs';
import { checkKey, falKey, priceOf, run as falRun } from '../../video/scripts/lib/fal.mjs';
import { decode, stats } from '../../playtest/scripts/lib/pixels.mjs';

const argv = process.argv.slice(2);
const flags = new Map();
const pos = [];
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a.startsWith('--')) { const k = a.slice(2); const v = argv[i + 1]; if (v === undefined || v.startsWith('--')) flags.set(k, true); else { flags.set(k, v); i++; } } else pos.push(a);
}
const JSON_OUT = flags.has('json');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const rel = (root, f) => relative(root, f).split('\\').join('/');
const ffmpeg = (args) => { const r = spawnSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', ...args], { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 }); if (r.status !== 0) throw new Error(`ffmpeg: ${String(r.stderr).trim().split('\n').pop()}`); return r; };
const size = (file) => { const r = spawnSync('ffprobe', ['-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', file], { encoding: 'utf8' }); const [w, h] = String(r.stdout).trim().split(',').map(Number); return { w, h }; };

function studioRoot() {
  const root = findStudio();
  if (!root) throw new Error('not inside a Homie studio (no studio.json here or above). The studio-setup skill makes one.');
  return root;
}
function artDir(root, slug) {
  if (!SLUG.test(String(slug ?? ''))) throw new Error('name the art job with a slug: lowercase letters, digits and hyphens (e.g. "cover" or "skyline")');
  const d = join(root, 'art', slug);
  mkdirSync(d, { recursive: true });
  return d;
}
function gameDir(root, game) {
  const d = experienceDir(root, String(game ?? ''));
  if (!game || !existsSync(experienceJson(d))) throw new Error('a game in this studio: games/<id>/game.json');
  return d;
}

/** A receipt line: the job's budget (running total), art/receipts.jsonl, and HOMIE_SPEND_LEDGER when set. */
function receipt(root, dir, line) {
  const at = new Date().toISOString();
  const b = readBudget(dir);
  if (b) {
    b.spent = +(b.spent + (Number(line.cost) || 0)).toFixed(6);
    b.calls.push({ at, provider: line.provider, model: line.model, cost: line.cost, unit: line.unit, requestId: line.requestId ?? null, artifact: line.artifact ?? null });
    writeJson(join(dir, 'budget.json'), b);
  }
  mkdirSync(join(root, 'art'), { recursive: true });
  appendFileSync(join(root, 'art', 'receipts.jsonl'), `${JSON.stringify({ schema: 'homie.media-receipt/1', at, ...line })}\n`);
  const ledger = process.env.HOMIE_SPEND_LEDGER;
  if (ledger) {
    try { appendFileSync(ledger, `${JSON.stringify({ schema: 'homie.brand-spend/1', at, provider: line.provider, model: line.model, jobId: line.requestId ?? null, units: line.units ?? null, unit: line.unitName ?? line.unit, usd: line.cost, credits: null, unpriced: null, brand: process.env.HOMIE_SPEND_BRAND ?? null, attribution: process.env.HOMIE_SPEND_ATTRIBUTION ?? null, artifact: line.artifact ?? null })}\n`); } catch (e) { process.stderr.write(`could not write the ledger: ${e.message}\n`); }
  }
}

/* ---------------------------------------------------------------- check */

async function check() {
  const ff = spawnSync('ffmpeg', ['-version']).status === 0;
  const root = findStudio();
  const key = falKey() ? await checkKey() : { ok: false, why: 'FAL_KEY is not set (only generated images need it; frames, covers, tiles and fitting are free)' };
  return { ok: ff, command: 'check', ffmpeg: ff, chrome: chromePath(), puppeteer: Boolean(loadPuppeteer(root)), studio: root, fal: key.ok ? 'the key works (checked free)' : key.why };
}

/* ---------------------------------------------------------------- frame */

async function frame(root) {
  const game = pos[1];
  gameDir(root, game);
  const url = String(flags.get('url') ?? '').replace(/\/+$/, '');
  if (!/^https?:\/\//.test(url)) throw new Error('--url <the studio site: http://127.0.0.1:8787 from npm run dev, or the live site>');
  const view = flags.get('view') === 'play' ? 'play' : 'tv';
  const seconds = Math.max(4, Math.min(60, Number(flags.get('seconds') ?? 12)));
  const dir = artDir(root, String(flags.get('slug') ?? 'frames'));
  const puppeteer = loadPuppeteer(root); const exe = chromePath();
  if (!puppeteer || !exe) throw new Error(!exe ? 'no Chrome found (set CHROME_PATH)' : 'puppeteer-core is missing (npm install in the studio)');
  const browser = await puppeteer.launch({ executablePath: exe, headless: true, timeout: 150_000, args: [...GPU_FLAGS, '--mute-audio', '--window-size=1920,1080', '--hide-scrollbars', '--force-color-profile=srgb', '--no-first-run'] });
  const shots = [];
  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
    await page.setUserAgent(`${await browser.userAgent()} homie-art`);
    await page.goto(`${url}/${game}/${view}`, { waitUntil: 'domcontentloaded', timeout: 60_000 });
    // The platform's own furniture never goes into art: the join card, the QR, the status chip, result cards.
    await page.addStyleTag({ content: '.join,.chip,.card,[data-join],[data-chip],[data-results],[data-screen],[data-room-ui],[data-toast]{display:none!important}' }).catch(() => {});
    await sleep(4000);
    for (let t = 0; t < seconds; t += 2) {
      const png = await page.screenshot({ type: 'png', captureBeyondViewport: false });
      const st = stats(decode(png, 480));
      const f = join(dir, `frame-${String(shots.length + 1).padStart(2, '0')}.png`);
      writeFileSync(f, png);
      shots.push({ file: rel(root, f), ...st });
      await sleep(2000);
    }
  } finally { await browser.close().catch(() => {}); }
  const usable = shots.filter((s) => !s.black && !s.flat);
  const best = (usable.length ? usable : shots).slice().sort((a, b) => b.edges - a.edges)[0];
  return { ok: Boolean(usable.length), command: 'frame', view, frames: shots.map((s) => `${s.file}: detail ${(s.edges * 100).toFixed(1)}%, brightness ${s.mean}`), best: best?.file, why: usable.length ? undefined : 'every frame was black or one colour: is the game drawing?', next: `look at ${best?.file}; a cover from it: art.mjs cover ${game} --from ${best?.file}` };
}

/* ---------------------------------------------------------------- cover */

function cover(root) {
  const game = pos[1];
  const gdir = gameDir(root, game);
  const from = resolve(String(flags.get('from') ?? ''));
  if (!existsSync(from)) throw new Error('--from <image>: a frame from `frame`, a painted image from `gen`, or the person\'s own art');
  const g = readJson(experienceJson(gdir), {});
  const pub = g.build?.mode === 'static' ? gdir : join(gdir, 'public');
  mkdirSync(pub, { recursive: true });
  const { w, h } = size(from);
  if (!w || !h) throw new Error(`could not read ${from} as an image`);
  // Crop to 16:9 around the focus (fractions; the middle by default), then 1600x900.
  const [fx, fy] = String(flags.get('focus') ?? '0.5,0.5').split(',').map(Number);
  const cw = Math.min(w, Math.round(h * 16 / 9)); const ch = Math.min(h, Math.round(w * 9 / 16));
  const x = Math.max(0, Math.min(w - cw, Math.round(fx * w - cw / 2))); const y = Math.max(0, Math.min(h - ch, Math.round(fy * h - ch / 2)));
  const out = join(pub, 'cover.jpg');
  let q = 3;
  for (;;) {
    ffmpeg(['-i', from, '-vf', `crop=${cw}:${ch}:${x}:${y},scale=1600:900:flags=lanczos`, '-q:v', String(q), out]);
    if (statSync(out).size <= 400 * 1024 || q >= 10) break;
    q += 1;
  }
  g.cover = 'cover.jpg';
  writeFileSync(experienceJson(gdir), `${JSON.stringify(g, null, 2)}\n`);
  const st = stats(decode(out, 480));
  const warn = [];
  if (w < 1200) warn.push(`the source is ${w} px wide: upscaled covers look soft; capture or generate at 1600 px or more`);
  if (st.mean < 35) warn.push(`dark (brightness ${st.mean} of 255): a card on a page reads as a black box`);
  if (st.edges < 0.03) warn.push('little visible detail: a cover sells the game; a busier moment or a painted version reads better');
  return { ok: true, command: 'cover', game, cover: rel(root, out), kb: Math.round(statSync(out).size / 1024), from: `${w}x${h}`, crop: `${cw}x${ch} at ${x},${y}`, gameJson: 'cover: "cover.jpg"', warnings: warn, look: 'open it: no QR code, no share panel, no debug text, not a waiting screen, and nothing the game does not contain' };
}

/* ---------------------------------------------------------------- money */

function budget(root) {
  const dir = artDir(root, pos[1]);
  const cap = Number(flags.get('cap'));
  if (!(cap > 0 && cap <= 1000)) throw new Error('--cap <US dollars the person agreed to>');
  const b = setBudget(dir, { provider: 'fal', unit: 'usd', cap });
  return { ok: true, command: 'budget', slug: pos[1], cap: b.cap, spent: b.spent };
}

function inputOf(file) {
  const j = readJson(resolve(String(file ?? '')), null);
  if (!j) throw new Error('--input <file.json>: the model\'s input (its schema is on the model\'s fal page, or the fal MCP get_model_schema)');
  return j;
}

async function price() {
  const model = String(flags.get('model') ?? '');
  if (!model) throw new Error('--model <fal model id, e.g. fal-ai/flux/dev>');
  const p = await priceOf(model, inputOf(flags.get('input')));
  return { ok: true, command: 'price', ...p };
}

async function gen(root) {
  const slug = pos[1];
  const dir = artDir(root, slug);
  const model = String(flags.get('model') ?? '');
  if (!model) throw new Error('--model <fal model id>');
  if (!flags.get('out')) throw new Error('--out <file in this art job, e.g. cover-painted.png>');
  const input = inputOf(flags.get('input'));
  const out = resolve(dir, String(flags.get('out')));
  if (!out.startsWith(`${dir}/`)) throw new Error('--out must stay inside the art job\'s folder');
  if (existsSync(out)) return { ok: true, command: 'gen', slug, already: rel(root, out) };
  const p = await priceOf(model, input);
  if (flags.has('dry-run')) return { ok: true, command: 'gen', dryRun: true, slug, price: p };
  const resuming = existsSync(`${out}.request`);
  if (!resuming) {
    const b = checkBudget(dir, p.usd, { provider: 'fal', unit: 'usd' });
    if (!flags.has('yes')) return { ok: false, command: 'gen', needs: 'approval', slug, price: p, budget: { cap: b.cap, spent: b.spent }, why: `This call costs about US$${p.usd.toFixed(3)} (${p.basis}); US$${b.spent.toFixed(2)} of US$${b.cap.toFixed(2)} spent so far. Run it with --yes once that is fine.` };
  }
  const r = await falRun(model, input, {
    out, base: dir, uploads: join(dir, 'uploads.json'), price: p, log: (m) => { if (!JSON_OUT) process.stderr.write(`${m}\n`); },
    onAccepted: async (q) => { receipt(root, dir, { provider: 'fal', model, requestId: q.request_id, cost: p.usd, unit: 'usd', units: p.units, unitName: p.unit, basis: p.basis, artifact: rel(root, out) }); },
  });
  return { ok: true, command: 'gen', slug, files: r.files.map((f) => rel(root, f)), requestId: r.requestId, usd: p.usd, spent: readJson(join(dir, 'budget.json'), {}).spent, next: 'look at it before anything else; a second call only with a changed prompt, never a loop' };
}

/* ---------------------------------------------------------------- tile / fit / sheet */

function tile() {
  const file = resolve(String(pos[1] ?? ''));
  if (!existsSync(file)) throw new Error('usage: tile <image>');
  const img = decode(file, 512);
  const { w, h, rgb } = img;
  const px = (x, y, c) => rgb[(y * w + x) * 3 + c];
  const colDiff = (a, b) => { let s = 0; for (let y = 0; y < h; y++) for (let c = 0; c < 3; c++) s += Math.abs(px(a, y, c) - px(b, y, c)); return s / (h * 3); };
  const rowDiff = (a, b) => { let s = 0; for (let x = 0; x < w; x++) for (let c = 0; c < 3; c++) s += Math.abs(px(x, a, c) - px(x, b, c)); return s / (w * 3); };
  // The wrap (last column against the first) against the texture's own neighbour steps inside it.
  let inX = 0; let nX = 0; for (let x = 1; x < w; x += 7) { inX += colDiff(x - 1, x); nX++; }
  let inY = 0; let nY = 0; for (let y = 1; y < h; y += 7) { inY += rowDiff(y - 1, y); nY++; }
  const seamX = +(colDiff(w - 1, 0) / Math.max(0.5, inX / nX)).toFixed(2);
  const seamY = +(rowDiff(h - 1, 0) / Math.max(0.5, inY / nY)).toFixed(2);
  const preview = file.replace(/(\.[a-z0-9]+)$/i, '-tiled.png');
  ffmpeg(['-i', file, '-filter_complex', '[0]scale=512:-2,split=4[a][b][c][d];[a][b]hstack[t];[c][d]hstack[u];[t][u]vstack', preview]);
  const ok = seamX <= 2 && seamY <= 2;
  return { ok: true, command: 'tile', file, seamX, seamY, tiles: ok, why: ok ? 'the edges meet like the inside does (2 or less)' : `a visible seam ${seamX > 2 ? 'left to right' : ''}${seamX > 2 && seamY > 2 ? ' and ' : ''}${seamY > 2 ? 'top to bottom' : ''}: image models are bad at tiling; mirror-blend the edges or ask for a texture and make it tile yourself`, preview };
}

function fit() {
  const file = resolve(String(pos[1] ?? ''));
  if (!existsSync(file)) throw new Error('usage: fit <image> --out <file.jpg|.webp|.png> [--width 1024] [--max-kb 300]');
  let out = resolve(String(flags.get('out') ?? file.replace(/(\.[a-z0-9]+)$/i, '-fit.jpg')));
  const encoders = spawnSync('ffmpeg', ['-hide_banner', '-encoders'], { encoding: 'utf8' }).stdout ?? '';
  let note;
  if (extname(out).toLowerCase() === '.webp' && !/libwebp/.test(encoders)) { out = out.replace(/\.webp$/i, '.jpg'); note = 'this ffmpeg has no WebP encoder, so it wrote a JPEG (brew install ffmpeg with libwebp, or keep JPEG: every browser reads it)'; }
  const width = Math.max(16, Math.min(8192, Number(flags.get('width') ?? 1024)));
  const maxKb = Number(flags.get('max-kb') ?? 300);
  const ext = extname(out).toLowerCase();
  mkdirSync(dirname(out), { recursive: true });
  let q = ext === '.webp' ? 82 : 3;
  for (let pass = 0; pass < 8; pass++) {
    const enc = ext === '.webp' ? ['-c:v', 'libwebp', '-quality', String(q)] : ext === '.png' ? ['-compression_level', '9'] : ['-q:v', String(q)];
    ffmpeg(['-i', file, '-vf', `scale=${width}:-2:flags=lanczos`, ...enc, out]);
    if (statSync(out).size <= maxKb * 1024 || ext === '.png') break;
    q = ext === '.webp' ? q - 10 : q + 2;
  }
  const kb = Math.round(statSync(out).size / 1024);
  const { w, h } = size(out);
  return { ok: kb <= maxKb || ext !== '.png', command: 'fit', out, size: `${w}x${h}`, kb, note, ...(kb > maxKb ? { why: `still ${kb} KB: a smaller width, or JPEG/WebP instead of PNG` } : {}), next: 'load it in the game, play it, and check the load time did not grow (the playtest\'s first row)' };
}

async function sheet(root) {
  const dir = resolve(String(pos[1] ?? ''));
  if (!existsSync(dir)) throw new Error('usage: sheet <folder of images>');
  const files = readdirSync(dir).filter((f) => /\.(png|jpe?g|webp)$/i.test(f) && !f.startsWith('sheet')).sort();
  if (!files.length) throw new Error('no images in that folder');
  const cells = files.map((f) => {
    const small = spawnSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-i', join(dir, f), '-vf', 'scale=480:-2', '-f', 'image2', '-c:v', 'mjpeg', '-q:v', '4', '-'], { maxBuffer: 32 * 1024 * 1024 }).stdout;
    return `<figure><img src="data:image/jpeg;base64,${Buffer.from(small).toString('base64')}"><figcaption>${f.replace(/</g, '&lt;')}</figcaption></figure>`;
  });
  const cols = Math.min(4, files.length); const rowsN = Math.ceil(files.length / cols);
  const html = `<!doctype html><meta charset="utf-8"><style>body{margin:0;background:#111;color:#ddd;font:14px system-ui,sans-serif}main{display:grid;grid-template-columns:repeat(${cols},480px);gap:12px;padding:12px}figure{margin:0}img{width:480px;height:270px;object-fit:contain;background:#000;display:block}figcaption{padding-top:4px}</style><main>${cells.join('')}</main>`;
  const out = join(dir, 'sheet.png');
  await htmlToPng(root, html, out, { width: cols * 492 + 12, height: rowsN * 306 + 12 });
  return { ok: true, command: 'sheet', images: files.length, sheet: out };
}

/* ---------------------------------------------------------------- main */

async function main() {
  const cmd = pos[0];
  if (!cmd || cmd === 'help' || flags.has('help')) {
    const head = readFileSync(fileURLToPath(import.meta.url), 'utf8').split('*/')[0];
    return { ok: true, command: 'help', usage: head.replace(/^#!.*\n\/\*\*?/, '').replace(/^ \* ?/gm, '').trim() };
  }
  if (cmd === 'check') return check();
  if (cmd === 'price') return price();
  if (cmd === 'tile') return tile();
  if (cmd === 'fit') return fit();
  const root = studioRoot();
  if (cmd === 'frame') return frame(root);
  if (cmd === 'cover') return cover(root);
  if (cmd === 'budget') return budget(root);
  if (cmd === 'gen') return gen(root);
  if (cmd === 'sheet') return sheet(root);
  return { ok: false, command: cmd, why: `unknown command "${cmd}" (art.mjs help)` };
}

const print = (o) => {
  if (JSON_OUT) { process.stdout.write(`${JSON.stringify(o, null, 2)}\n`); return; }
  if (o.ok === false && o.why) { process.stdout.write(`art: ${o.why}\n`); return; }
  for (const [k, v] of Object.entries(o)) if (k !== 'ok' && k !== 'command' && v !== undefined) process.stdout.write(`${k}: ${Array.isArray(v) ? `\n  ${v.join('\n  ')}` : typeof v === 'object' ? JSON.stringify(v) : v}\n`);
};

try {
  const r = await main();
  if (r) { print(r); if (r.ok === false) process.exitCode = 1; }
} catch (error) {
  print({ ok: false, why: error instanceof Error ? error.message : String(error) });
  process.exitCode = 1;
}
