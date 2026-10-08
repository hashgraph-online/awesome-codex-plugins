#!/usr/bin/env node
/**
 * record-page.mjs — record any web page while a script drives it: clicks, taps, keys, typing, scrolls and waits for
 * a selector, a text or a state, in REAL TIME, off a headless GPU Chrome, into an mp4 whose every frame is one the
 * page drew. For product demos, site walkthroughs, tutorials, and a studio's own game page: land, press Play, play.
 *
 *   node record-page.mjs --steps <steps.json> --out <folder> [--url <site>] [--device computer|phone]
 *        [--fps 30] [--width 1920] [--height 1080] [--scale 1] [--seconds 120] [--no-cursor] [--min-fps 0]
 *        [--min-free-gb 10]
 *
 * The steps file (references/RECORD.md has every step; references/examples/ has tested ones):
 *
 *   { "path": "/gem-rush/", "device": "computer", "tail": 2,
 *     "steps": [
 *       { "wait": 1500, "caption": "Gem Rush, on the studio's own site" },
 *       { "click": "a[data-play]", "caption": "Press Play" },
 *       { "waitFor": { "frame": "game", "selector": "canvas" } },
 *       { "key": "ArrowRight", "hold": 900, "frame": "game" },
 *       { "keys": ["ArrowUp", "ArrowLeft"], "hold": 400, "gap": 150, "frame": "game" }
 *     ] }
 *
 * "url" (absolute) or "path" (joined to --url, the local `dev` site or the live one) is where it starts. The page is
 * opened and settled first, then the recording starts and the steps run one after another at the speed they take:
 * nothing is sped up, nothing is cut. The recording ends `tail` seconds after the last step (or at --seconds).
 *
 * Picture: the compositor's own frames (CDP screencast) with the time each was presented, laid onto --fps by
 *          holding the newest frame (lib/frames.mjs): a frame the page did not paint is held and counted, never
 *          interpolated. The page's real frame rate (requestAnimationFrame, in the page and in a game's frame) and
 *          the GPU renderer are measured and reported; under 20 frames a second, or on a software renderer, the
 *          result says so, because the recording then shows a slow computer, not the page.
 * Cursor:  a small arrow and a press ring drawn over the page (in the page, so it is in the frames) to show where the
 *          script pointed; a tap shows a ring. --no-cursor leaves them out.
 * Sound:   what a studio game's frame (/<id>/__game/) sends to its speaker through WebAudio (tap.js), on the same
 *          clock; the browser is muted. Other pages record silent: add a bed or a voice-over in the edit.
 * Out:     <out>/recording.mp4, <out>/recording.json (every step with the second it ran, frame rates, held
 *          frames, renderer, notes), <out>/captions.vtt when steps have captions. Raw frames are deleted once
 *          encoded. Only small JSON with paths goes to stdout.
 */
import { mkdirSync, readFileSync, rmSync, statfsSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { launch } from './lib/browser.mjs';
import { TapReader, constantRate, encodeMp4, fitAudio, startScreencast, writeConcat } from './lib/frames.mjs';
import { findStudio } from '../../music/scripts/lib/studio.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const has = (n) => argv.includes(`--${n}`);
const opt = (n, d = null) => { const i = argv.indexOf(`--${n}`); return i >= 0 && i + 1 < argv.length ? argv[i + 1] : d; };
const fail = (m, code = 2) => { process.stderr.write(`record-page: ${m}\n`); process.exit(code); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const log = (k, v = {}) => process.stderr.write(`${JSON.stringify({ t: +(process.uptime()).toFixed(1), k, ...v })}\n`);

if (!opt('steps')) fail('--steps <steps.json> (references/RECORD.md)');
if (!opt('out')) fail('--out <folder>');
let spec;
try { spec = JSON.parse(readFileSync(resolve(String(opt('steps'))), 'utf8')); } catch (error) { fail(`--steps: ${error.message}`); }
if (!spec || !Array.isArray(spec.steps)) fail('the steps file needs "steps": [ ... ]');
const OUT = resolve(String(opt('out')));
const DEVICE = String(opt('device', spec.device ?? 'computer'));
if (!['computer', 'phone'].includes(DEVICE)) fail('--device computer|phone');
const PHONE = DEVICE === 'phone';
const FPS = Number(opt('fps', spec.fps ?? 30));
// The film's size: 16:9 for a computer, 9:16 for a phone (a 360x640 page at 3x).
const W = Number(opt('width', spec.width ?? (PHONE ? 1080 : 1920)));
const H = Number(opt('height', spec.height ?? (PHONE ? 1920 : 1080)));
const SCALE = Number(opt('scale', spec.scale ?? 1));
const SECONDS = Number(opt('seconds', spec.seconds ?? 120));
const TAIL = Number(spec.tail ?? 2);
const CURSOR = !has('no-cursor') && spec.cursor !== false;
const MIN_FPS = Number(opt('min-fps', spec.minFps ?? 0));
const MIN_FREE_GB = Number(opt('min-free-gb', 10));
if (!(FPS >= 1 && FPS <= 60)) fail('--fps 1..60');
if (!(SCALE >= 0.25 && SCALE <= 1)) fail('--scale 0.25..1');
if (!(SECONDS >= 2 && SECONDS <= 600)) fail('--seconds 2..600');
const base = String(opt('url', spec.base ?? '')).replace(/\/+$/, '');
const START = spec.url ?? (spec.path != null ? `${base}${String(spec.path).startsWith('/') ? '' : '/'}${spec.path}` : base);
if (!/^https?:\/\//.test(START)) fail('where to start: "url" in the steps file, or "path" with --url <site> (http://127.0.0.1:8787 from npm run dev, or the live site)');
// The page's own size (CSS pixels) and its pixel ratio: the frames come out at W x H (x SCALE), even sizes.
const DSF = PHONE ? 3 * SCALE : SCALE;
const VW = PHONE ? Math.round(W / 3) : W; const VH = PHONE ? Math.round(H / 3) : H;
const RW = Math.max(2, Math.round((VW * DSF) / 2) * 2); const RH = Math.max(2, Math.round((VH * DSF) / 2) * 2);

mkdirSync(OUT, { recursive: true });
const freeGB = () => { try { const f = statfsSync(OUT); return (f.bavail * f.bsize) / 1e9; } catch { return 99; } };
if (freeGB() < MIN_FREE_GB + 2) fail(`only ${freeGB().toFixed(1)} GB free; a recording needs room (stopping below ${MIN_FREE_GB} GB)`);

/* ---------------------------------------------------------------- what is injected into every page */

const TAP = readFileSync(join(HERE, 'tap.js'), 'utf8');
// A requestAnimationFrame counter in every frame: the page's real frame rate, measured where it runs. It draws nothing.
// And what input each frame actually received (passive listeners that change nothing): delivered, not judged.
const RAF = `(() => { if (window.__homieRaf) return; const s = { id: Math.random(), n: 0, t0: performance.now(), keys: 0, pointers: 0, touches: 0 }; window.__homieRaf = s;
  const tick = () => { s.n++; requestAnimationFrame(tick); }; requestAnimationFrame(tick);
  addEventListener('keydown', (e) => { if (!e.repeat) s.keys++; }, { capture: true, passive: true });
  addEventListener('pointerdown', () => { s.pointers++; }, { capture: true, passive: true });
  addEventListener('touchstart', () => { s.touches++; }, { capture: true, passive: true }); })();`;
// The cursor and the press ring, top document only, above everything and never in the way of a click.
const CURSOR_JS = `(() => { if (window.top !== window || window.__homieCursor) return;
  const make = () => {
    if (document.getElementById('__homie-cursor')) return;
    const c = document.createElement('div'); c.id = '__homie-cursor';
    c.style.cssText = 'position:fixed;left:0;top:0;width:26px;height:26px;z-index:2147483647;pointer-events:none;transform:translate(-200px,-200px);will-change:transform';
    c.innerHTML = '<svg width="26" height="26" viewBox="0 0 26 26"><path d="M3 2 L3 21 L8.2 16.4 L11.6 24 L15 22.5 L11.7 15 L19 15 Z" fill="#fff" stroke="#111" stroke-width="1.6" stroke-linejoin="round"/></svg>';
    const r = document.createElement('div'); r.id = '__homie-ring';
    r.style.cssText = 'position:fixed;left:0;top:0;width:44px;height:44px;margin:-22px 0 0 -22px;border-radius:50%;border:3px solid rgba(255,255,255,.95);box-shadow:0 0 0 2px rgba(0,0,0,.35);z-index:2147483646;pointer-events:none;opacity:0';
    (document.body || document.documentElement).append(r, c);
  };
  const S = { x: -200, y: -200, anim: null };
  const place = () => { make(); const c = document.getElementById('__homie-cursor'); if (c) c.style.transform = 'translate(' + (S.x - 3) + 'px,' + (S.y - 2) + 'px)'; };
  window.__homieCursor = {
    at(x, y) { S.x = x; S.y = y; place(); },
    glide(x, y, ms) { return new Promise((done) => { const x0 = S.x < -100 ? x - 140 : S.x; const y0 = S.y < -100 ? y + 90 : S.y; const t0 = performance.now();
      const step = (t) => { const k = Math.min(1, (t - t0) / Math.max(1, ms)); const e = k < .5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
        S.x = x0 + (x - x0) * e; S.y = y0 + (y - y0) * e; place(); if (k < 1) requestAnimationFrame(step); else done(); };
      requestAnimationFrame(step); }); },
    ring(x, y) { make(); const r = document.getElementById('__homie-ring'); if (!r) return;
      r.style.left = x + 'px'; r.style.top = y + 'px';
      r.animate([{ opacity: 1, transform: 'scale(.45)' }, { opacity: 0, transform: 'scale(1.25)' }], { duration: 420, easing: 'ease-out' }); },
    hide() { S.x = -200; S.y = -200; place(); },
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', place); else place();
})();`;

/* ---------------------------------------------------------------- steps */

const KINDS = ['goto', 'wait', 'waitFor', 'click', 'tap', 'hover', 'move', 'drag', 'key', 'keys', 'type', 'scroll', 'focus', 'caption'];
/** `{ "click": "a" }` is `{ "do": "click", "selector": "a" }`; every shorthand to one shape. */
function normal(raw, i) {
  if (!raw || typeof raw !== 'object') throw new Error(`step ${i + 1} is not an object`);
  const kind = raw.do ?? KINDS.find((k) => k in raw);
  if (!KINDS.includes(kind)) throw new Error(`step ${i + 1}: say what to do (${KINDS.join(', ')})`);
  const s = { ...raw, do: kind };
  const v = raw.do ? undefined : raw[kind];
  if (kind === 'wait' && v !== undefined) s.ms = Number(v);
  if (kind === 'waitFor' && v !== undefined) Object.assign(s, typeof v === 'string' ? { selector: v } : v);
  if (['click', 'tap', 'hover', 'move'].includes(kind) && v !== undefined) Object.assign(s, typeof v === 'string' ? { selector: v } : Array.isArray(v) ? { at: v } : v);
  if (kind === 'goto' && v !== undefined) s.url = v;
  if (kind === 'key' && v !== undefined) s.key = v;
  if (kind === 'keys' && v !== undefined) s.keys = v;
  if (kind === 'type' && v !== undefined) s.text = v;
  if (kind === 'scroll' && v !== undefined) Object.assign(s, typeof v === 'number' ? { by: v } : typeof v === 'string' ? { to: v } : v);
  if (kind === 'focus' && v !== undefined) Object.assign(s, typeof v === 'string' ? { frame: v } : v);
  if (kind === 'drag' && v !== undefined) Object.assign(s, v);
  if (kind === 'caption' && v !== undefined) s.caption = v;
  return s;
}
let steps;
try { steps = spec.steps.map(normal); } catch (error) { fail(error.message); }

const root = findStudio(OUT) ?? findStudio();
const report = {
  ran: new Date().toISOString(), start: START, device: DEVICE, fps: FPS, size: [W, H], page: [VW, VH], ...(SCALE !== 1 ? { scale: SCALE, rendered: [RW, RH] } : {}),
  steps: [], notes: [],
};

const { browser, close, pid } = await launch(root, { width: VW, height: VH, extra: ['--autoplay-policy=no-user-gesture-required', '--mute-audio'] });
log('browser', { pid });
const frameDir = join(OUT, 'frames');
rmSync(frameDir, { recursive: true, force: true });
mkdirSync(frameDir, { recursive: true });
const pcmFile = join(OUT, 'page-audio.s16le');
const tap = new TapReader(pcmFile);
let frames = [];
let videoT0 = null; // epoch seconds of the recording's start (the first frame's presentation time)
let stopAt = null;
let tapFrame = null;
const stop = async (why) => { log('stop', { why }); tap.close(); await close(); process.exit(3); };
process.on('SIGINT', () => stop('SIGINT'));
process.on('SIGTERM', () => stop('SIGTERM'));

let page;
/** A frame by name: "game" (a studio game's /<id>/__game/ frame), a piece of its address, or the page itself. */
function frameOf(name) {
  if (!name || name === 'top' || name === 'page') return page.mainFrame();
  const want = name === 'game' ? /\/__game\//i : null;
  return page.frames().find((f) => !f.isDetached() && (want ? want.test(f.url()) : f.url().includes(String(name)))) ?? null;
}
async function frameNamed(name, timeout) {
  const until = Date.now() + timeout;
  for (;;) {
    const f = frameOf(name);
    if (f) return f;
    if (Date.now() > until) throw new Error(`no frame "${name}" within ${timeout} ms`);
    await sleep(100);
  }
}
/** A point in the page: a selector's centre (in any frame), or [x, y] in CSS pixels, or fractions of the page (0..1). */
async function pointOf(s, timeout) {
  if (Array.isArray(s.at)) {
    const [x, y] = s.at.map(Number);
    return x <= 1 && y <= 1 && x >= 0 && y >= 0 ? { x: x * VW, y: y * VH } : { x, y };
  }
  if (!s.selector) throw new Error('give "selector" or "at": [x, y]');
  const frame = await frameNamed(s.frame, timeout);
  const el = await frame.waitForSelector(s.selector, { visible: true, timeout });
  // Scrolled to only when it is out of view, and smoothly, as a person would; never a jump.
  if (!(await el.isIntersectingViewport({ threshold: 1 }).catch(() => true))) {
    await el.evaluate((e) => e.scrollIntoView({ block: 'center', inline: 'nearest', behavior: 'smooth' }));
    await sleep(700);
  }
  const box = await el.boundingBox();
  if (!box) throw new Error(`"${s.selector}" has no box on the page`);
  return { x: box.x + box.width * (s.offset?.[0] ?? 0.5), y: box.y + box.height * (s.offset?.[1] ?? 0.5), el };
}
const cursor = (fn, ...args) => (CURSOR ? page.evaluate(fn, ...args).catch(() => {}) : Promise.resolve());
let pointer = null;
async function glide(p, ms = 450) {
  // The visible cursor glides in the page; the real mouse follows in steps, so hover styles answer as for a person.
  const moves = PHONE ? Promise.resolve() : page.mouse.move(p.x, p.y, { steps: Math.max(2, Math.round(ms / 25)) });
  await Promise.all([cursor((x, y, t) => window.__homieCursor?.glide(x, y, t), p.x, p.y, ms), moves, sleep(ms)]);
  pointer = p;
}
const secondsNow = () => (videoT0 === null ? 0 : Math.max(0, Date.now() / 1000 - videoT0));
/** The input a frame's document has received so far (keys, pointer presses, touches), with which document it is. */
const inputsOf = (f) => (f ? f.evaluate(() => (window.__homieRaf ? { id: window.__homieRaf.id, keys: window.__homieRaf.keys, pointers: window.__homieRaf.pointers, touches: window.__homieRaf.touches } : null)).catch(() => null) : Promise.resolve(null));
const INPUT_STEPS = new Set(['click', 'tap', 'drag', 'key', 'keys', 'type']);
const captions = [];

async function runStep(s) {
  const timeout = Number(s.timeout ?? 20_000);
  switch (s.do) {
    case 'goto': await page.goto(/^https?:/.test(s.url) ? s.url : `${base}${s.url}`, { waitUntil: 'domcontentloaded', timeout: 60_000 }); if (pointer) await cursor((x, y) => window.__homieCursor?.at(x, y), pointer.x, pointer.y); break;
    case 'wait': await sleep(Number(s.ms ?? 1000)); break;
    case 'caption': await sleep(Number(s.ms ?? 0)); break;
    case 'waitFor': {
      if (s.selector) { const f = await frameNamed(s.frame, timeout); await f.waitForSelector(s.selector, { visible: s.visible !== false, timeout }); }
      else if (s.text) { const f = await frameNamed(s.frame, timeout); await f.waitForFunction((t) => document.body && document.body.innerText.includes(t), { timeout, polling: 100 }, String(s.text)); }
      else if (s.js) { const f = await frameNamed(s.frame, timeout); await f.waitForFunction(String(s.js), { timeout, polling: 100 }); }
      else if (s.frame) await frameNamed(s.frame, timeout);
      else throw new Error('waitFor needs "selector", "text", "js" or "frame"');
      break;
    }
    case 'hover': case 'move': { const p = await pointOf(s, timeout); await glide(p, Number(s.ms ?? 450)); break; }
    case 'click': {
      const p = await pointOf(s, timeout);
      if (!PHONE) await glide(p, Number(s.ms ?? 450));
      if (PHONE) { await cursor((x, y) => window.__homieCursor?.ring(x, y), p.x, p.y); await page.touchscreen.tap(p.x, p.y); }
      else { await cursor((x, y) => window.__homieCursor?.ring(x, y), p.x, p.y); await page.mouse.click(p.x, p.y, { delay: 60 }); }
      break;
    }
    case 'tap': {
      const p = await pointOf(s, timeout);
      await cursor((x, y) => window.__homieCursor?.ring(x, y), p.x, p.y);
      await page.touchscreen.tap(p.x, p.y);
      break;
    }
    case 'drag': {
      // A held press that moves: a virtual stick on a phone, a drag on a computer. "to" is [dx, dy] in CSS pixels.
      const from = await pointOf({ ...s, at: s.from ?? s.at }, timeout);
      const [dx, dy] = (s.to ?? s.by ?? [0, 0]).map(Number);
      const ms = Number(s.ms ?? 800); const n = Math.max(4, Math.round(ms / 30));
      if (PHONE) {
        await cursor((x, y) => window.__homieCursor?.ring(x, y), from.x, from.y);
        await page.touchscreen.touchStart(from.x, from.y);
        for (let k = 1; k <= n; k++) { await page.touchscreen.touchMove(from.x + (dx * k) / n, from.y + (dy * k) / n); await sleep(ms / n); }
        await sleep(Number(s.hold ?? 0));
        await page.touchscreen.touchEnd();
      } else {
        await glide(from, 350);
        await page.mouse.down();
        for (let k = 1; k <= n; k++) { const q = { x: from.x + (dx * k) / n, y: from.y + (dy * k) / n }; await Promise.all([page.mouse.move(q.x, q.y), cursor((x, y) => window.__homieCursor?.at(x, y), q.x, q.y)]); await sleep(ms / n); pointer = q; }
        await sleep(Number(s.hold ?? 0));
        await page.mouse.up();
      }
      break;
    }
    case 'focus': {
      const f = await frameNamed(s.frame ?? 'game', timeout);
      if (f !== page.mainFrame()) { const el = await f.frameElement(); await el?.focus(); await f.evaluate(() => window.focus()); }
      if (s.selector) await (await f.waitForSelector(s.selector, { timeout })).focus();
      break;
    }
    case 'key': case 'keys': {
      if (s.frame) { const f = await frameNamed(s.frame, timeout); if (f !== page.mainFrame()) { const el = await f.frameElement(); await el?.focus().catch(() => {}); } }
      const list = s.do === 'key' ? [s.key] : (Array.isArray(s.keys) ? s.keys : [s.keys]);
      const times = Number(s.times ?? 1);
      for (let t = 0; t < times; t++) {
        for (const k of list) {
          // A chord: "Shift+ArrowUp" holds every key together.
          const chord = String(k).split('+');
          for (const c of chord) await page.keyboard.down(c);
          await sleep(Number(s.hold ?? 120));
          for (const c of [...chord].reverse()) await page.keyboard.up(c);
          await sleep(Number(s.gap ?? 120));
        }
      }
      break;
    }
    case 'type': {
      if (s.into || s.selector) {
        const p = await pointOf({ ...s, selector: s.into ?? s.selector }, timeout);
        if (!PHONE) await glide(p, 400);
        await cursor((x, y) => window.__homieCursor?.ring(x, y), p.x, p.y);
        if (PHONE) await page.touchscreen.tap(p.x, p.y); else await page.mouse.click(p.x, p.y);
      }
      await page.keyboard.type(String(s.text ?? ''), { delay: Number(s.delay ?? 70) });
      break;
    }
    case 'scroll': {
      // Real wheel (or touch-free) scrolling over time: never a jump.
      let by = Number(s.by ?? 0);
      if (s.to) {
        const f = await frameNamed(s.frame, timeout);
        const el = await f.waitForSelector(s.to, { timeout });
        const box = await el.boundingBox();
        by = box ? box.y - VH * Number(s.align ?? 0.25) : 0;
      }
      const ms = Number(s.ms ?? Math.min(2400, Math.max(500, Math.abs(by) * 1.6)));
      const n = Math.max(4, Math.round(ms / 33));
      if (pointer === null && !PHONE) await page.mouse.move(VW / 2, VH / 2);
      for (let k = 0; k < n; k++) {
        if (PHONE) await page.evaluate((d) => window.scrollBy(0, d), by / n);
        else await page.mouse.wheel({ deltaY: by / n });
        await sleep(ms / n);
      }
      break;
    }
    default: throw new Error(`unknown step "${s.do}"`);
  }
}

/** Every frame's rAF count (frames drawn per second, where it was measured) and the input it received. */
async function rafRates(inputs = null) {
  const out = {};
  for (const [name, f] of [['page', page.mainFrame()], ['game', frameOf('game')]]) {
    if (!f) continue;
    try {
      const r = await f.evaluate(() => (window.__homieRaf ? { n: window.__homieRaf.n, ms: performance.now() - window.__homieRaf.t0, keys: window.__homieRaf.keys, pointers: window.__homieRaf.pointers, touches: window.__homieRaf.touches } : null));
      if (r && r.ms > 500) out[name] = +((r.n * 1000) / r.ms).toFixed(1);
      if (r && inputs) inputs[name] = { keys: r.keys, pointers: r.pointers, touches: r.touches };
    } catch { /* gone */ }
  }
  return out;
}

let failed = null;
try {
  page = await browser.newPage();
  await page.setViewport({ width: VW, height: VH, deviceScaleFactor: DSF, isMobile: PHONE, hasTouch: PHONE });
  // A phone reads as one; and a studio's own site counts the recorder as its QA, never as a visitor or a player.
  const ua0 = await browser.userAgent();
  const ua = PHONE ? ua0.replace(/\([^)]*\)/, '(Linux; Android 14; Pixel 8)').replace('HeadlessChrome', 'Chrome').replace(/Safari\/([\d.]+)$/, 'Mobile Safari/$1') : ua0;
  await page.setUserAgent(`${ua} homie-studio-check video-record`);
  await page.evaluateOnNewDocument(RAF);
  await page.evaluateOnNewDocument(TAP);
  if (CURSOR) await page.evaluateOnNewDocument(CURSOR_JS);
  const errors = [];
  page.on('pageerror', (e) => { if (errors.length < 30) errors.push(String(e.message).slice(0, 200)); });
  // A click that opens another page (Play): the cursor is drawn again where it was.
  page.on('domcontentloaded', () => { if (pointer) cursor((x, y) => window.__homieCursor?.at(x, y), pointer.x, pointer.y); });
  await page.goto(START, { waitUntil: 'load', timeout: 60_000 });
  await sleep(Number(spec.settle ?? 1.5) * 1000);
  // The renderer and the frame rate before anything is recorded: a software renderer makes a game look stuck.
  report.renderer = await page.evaluate(() => {
    try { const gl = document.createElement('canvas').getContext('webgl'); const x = gl && gl.getExtension('WEBGL_debug_renderer_info'); return gl ? String(x ? gl.getParameter(x.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER)) : 'no WebGL'; } catch { return 'unknown'; }
  });
  report.software = /swiftshader|llvmpipe|software|basic render/i.test(report.renderer);
  const before = await rafRates();
  report.pageFpsBefore = before.page ?? null;
  if (CURSOR && !PHONE) { pointer = { x: VW * 0.55, y: VH * 0.62 }; await cursor((x, y) => window.__homieCursor?.at(x, y), pointer.x, pointer.y); await page.mouse.move(pointer.x, pointer.y); }

  const cast = await startScreencast(page, { dir: frameDir, width: RW, height: RH, quality: 90 });
  frames = cast.frames;
  for (let i = 0; i < 100 && !frames.length; i++) await sleep(20);
  videoT0 = frames[0]?.t ?? Date.now() / 1000;
  const deadline = Date.now() + SECONDS * 1000;
  // The game's sound, once a game frame exists: polled beside the steps, on the same clock.
  let polling = true;
  const poller = (async () => {
    while (polling) {
      try {
        if (!tapFrame || tapFrame.isDetached()) {
          tapFrame = frameOf('game');
          if (tapFrame) await tapFrame.evaluate(() => window.__homieTap?.start?.() ?? null).catch(() => null);
        }
        if (tapFrame) await tap.poll(tapFrame);
      } catch (error) { if (report.notes.length < 20) report.notes.push(`sound: ${String(error.message).slice(0, 120)}`); }
      if (freeGB() < MIN_FREE_GB) { report.notes.push('stopped early: disk low'); break; }
      await sleep(250);
    }
  })();

  for (const [i, s] of steps.entries()) {
    if (Date.now() > deadline) { report.notes.push(`stopped at --seconds ${SECONDS} before step ${i + 1}`); break; }
    const at = secondsNow();
    if (s.caption) captions.push({ from: at, to: at + Number(s.captionSeconds ?? 3), text: String(s.caption) });
    const t = Date.now();
    try {
      // What the step's own frame received while it ran: delivered, not judged (a click that opens a page says so).
      const target = INPUT_STEPS.has(s.do) ? (frameOf(s.frame) ?? null) : null;
      const before = target ? await inputsOf(target) : null;
      await runStep(s);
      let received;
      if (target) {
        await sleep(30);
        const after = await inputsOf(target);
        received = !after || !before || after.id !== before.id ? 'another page opened' : { keys: after.keys - before.keys, pointers: after.pointers - before.pointers, touches: after.touches - before.touches };
      }
      report.steps.push({ i: i + 1, do: s.do, at: +at.toFixed(3), took: +((Date.now() - t) / 1000).toFixed(3), ...(s.selector ? { selector: s.selector } : {}), ...(s.key ? { key: s.key } : {}), ...(received ? { received } : {}) });
      log('step', { i: i + 1, do: s.do, at: +at.toFixed(2) });
    } catch (error) {
      const why = String(error.message ?? error).split('\n')[0].slice(0, 300);
      report.steps.push({ i: i + 1, do: s.do, at: +at.toFixed(3), failed: why });
      if (s.optional) continue;
      failed = { step: i + 1, do: s.do, why };
      break;
    }
  }
  const tailUntil = Math.min(deadline, Date.now() + TAIL * 1000);
  while (Date.now() < tailUntil) await sleep(50);
  report.inputs = {};
  report.pageFps = await rafRates(report.inputs);
  stopAt = Date.now() / 1000;
  polling = false;
  await poller;
  await cast.stop();
  await sleep(200);
  report.errors = errors;
} catch (error) {
  report.crashed = String(error.stack ?? error).split('\n').slice(0, 3).join(' ');
} finally {
  tap.close();
  await close();
}

// A still page sends one frame and nothing more until it changes: one is enough (it is held for as long as it showed).
if (report.crashed || frames.length < 1) {
  writeFileSync(join(OUT, 'recording.json'), `${JSON.stringify({ ...report, frames: frames.length }, null, 1)}\n`);
  rmSync(frameDir, { recursive: true, force: true });
  rmSync(pcmFile, { force: true });
  fail(report.crashed ? `the recording failed: ${report.crashed}` : 'the page sent no frame at all', 1);
}

/* ---- picture: held, never interpolated, to the moment the recording stopped (a still page lasts as long as it did) */
const cfr = constantRate(frames, FPS, { until: stopAt });
const concat = writeConcat(join(OUT, 'frames.txt'), cfr.list, FPS);
const audio = fitAudio(tap, { t0: cfr.t0, total: cfr.total, fps: FPS, out: join(OUT, 'page-audio.raw') });
rmSync(pcmFile, { force: true });
const mp4 = join(OUT, 'recording.mp4');
const seconds = cfr.total / FPS;
const enc = encodeMp4({ concat, audio, fps: FPS, width: W, height: H, seconds, out: mp4, crf: 18 });
rmSync(frameDir, { recursive: true, force: true });
rmSync(concat, { force: true });
if (audio) delete audio.raw;
if (!enc.ok) fail(`encode failed: ${enc.why}`, 1);

// The steps' seconds are against the first frame, which is the video's first frame.
const shift = videoT0 !== null ? videoT0 - cfr.t0 : 0;
for (const s of report.steps) s.at = +(s.at + shift).toFixed(3);
const vtt = (x) => { const h = Math.floor(x / 3600); const m = Math.floor((x % 3600) / 60); const sec = (x % 60).toFixed(3).padStart(6, '0'); return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${sec}`; };
if (captions.length) {
  const cues = captions.map((c, i) => ({ from: c.from + shift, to: Math.min(seconds, captions[i + 1] ? Math.min(c.to, captions[i + 1].from) : c.to) + shift, text: c.text })).filter((c) => c.to > c.from);
  writeFileSync(join(OUT, 'captions.vtt'), `WEBVTT\n\n${cues.map((c) => `${vtt(c.from)} --> ${vtt(c.to)}\n${c.text}`).join('\n\n')}\n`);
}

const span = cfr.frames.at(-1).t - cfr.t0;
const painted = +(cfr.frames.length / Math.max(0.001, span)).toFixed(1);
const slow = Object.entries(report.pageFps ?? {}).filter(([, v]) => v < 20);
const warnings = [];
if (report.software) warnings.push(`Chrome drew this page on a software renderer (${report.renderer}): a WebGL page runs far slower here than on a computer with a GPU, and the recording shows that slowness. Record on a computer with a GPU.`);
if (slow.length) warnings.push(`the ${slow.map(([k, v]) => `${k} ran at ${v}`).join(' and the ')} frames a second here (under 20): the recording shows a slow page, not a stuck one. Try --scale 0.67, fewer programs running, or a computer with a GPU.`);
const result = {
  ...report, file: 'recording.mp4', seconds: +seconds.toFixed(3), outputFrames: cfr.total, paintedFrames: cfr.frames.length, paintedFps: painted,
  distinctFramesUsed: cfr.distinct, heldFrames: cfr.held, audio, ...(captions.length ? { captions: 'captions.vtt' } : {}), ...(warnings.length ? { warnings } : {}),
  ...(failed ? { failed } : {}),
  honesty: `Recorded in real time from Chrome (${report.renderer}) as the steps ran; every frame is one the page drew, and a moment it did not repaint is held (${cfr.held} of ${cfr.total} frames), never invented.${CURSOR ? ' The cursor and the press rings are drawn by the recorder to show where the script pointed and pressed.' : ''}`,
};
writeFileSync(join(OUT, 'recording.json'), `${JSON.stringify(result, null, 1)}\n`);
const minFpsMiss = MIN_FPS > 0 && Object.values(report.pageFps ?? {}).some((v) => v < MIN_FPS);
const ok = !failed && !minFpsMiss;
process.stdout.write(`${JSON.stringify({
  ok, file: mp4, json: join(OUT, 'recording.json'), ...(captions.length ? { captions: join(OUT, 'captions.vtt') } : {}), seconds: result.seconds,
  pageFps: report.pageFps, inputs: report.inputs, paintedFps: painted, heldFrames: cfr.held, steps: report.steps.length, ...(failed ? { failed } : {}), ...(warnings.length ? { warnings } : {}),
  ...(minFpsMiss ? { why: `the page ran under --min-fps ${MIN_FPS}` } : {}),
})}\n`);
process.exit(ok ? 0 : 1);
