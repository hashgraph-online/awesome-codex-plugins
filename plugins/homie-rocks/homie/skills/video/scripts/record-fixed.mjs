#!/usr/bin/env node
/**
 * record-fixed.mjs — a page rendered FRAME BY FRAME on a virtual clock, with its sound rebuilt offline: for
 * a trailer of a game too heavy to draw every frame in real time, and for any film that must not hold a frame.
 *
 *   node record-fixed.mjs --url <page> --out <folder> [--seconds 30] [--fps 30] [--width 1920] [--height 1080]
 *        [--scale 1] [--settle 2] [--wait-for "<js that turns true>"] [--steps <steps.json>] [--css "<css>"]
 *        [--frame game] [--no-pace] [--min-free-gb 10]
 *
 * How it differs from capture-game.mjs and record-page.mjs (which film the page in real time and HOLD a frame
 * the page did not paint in time): here the page's clock is ours (clock.js). Each film frame, the page's
 * requestAnimationFrame, performance.now, Date.now, setTimeout, setInterval and its CSS and Web animations all
 * move on by exactly 1/fps, the page draws, and the frame is copied. A frame that takes half a second to draw
 * is still one frame of film, so there are no held frames, at any size, on any computer.
 *
 * Sound: a page on a virtual clock has no speaker worth recording (its audio clock runs at the wall's speed).
 *        The recorder sets window.__homieSoundCapture before the page's scripts, the sound player logs every
 *        sound it schedules (sound.js says exactly what), the files it names are fetched from the page's own
 *        origin, and lib/remix.mjs mixes them again on the film's clock. A game that does not use sound.js
 *        and does not push the same events records silent, and the result says so.
 *
 * Steps (optional): the same file as record-page.mjs, on the virtual clock, with these steps only:
 *        wait, waitFor (selector | text | js | frame), click, tap, key, keys, type, focus, caption.
 *        No cursor is drawn, and there is no hover, drag or scroll here: use record-page.mjs for those.
 *
 * What stays on the wall's clock, and so is NOT covered (clock.js lists them): the audio clock, <video> and
 * <audio> elements, Web Workers, and the network. A page fed by a live server (a room on a relay) sees that
 * server run fast when frames take longer than 1/fps to render: the result gives the speed (film seconds per
 * real second) and warns when a page with an open WebSocket ran well under 1. Rendering is never run faster
 * than real time (--no-pace lifts that, for a page with no server).
 *
 * Out: <out>/capture.mp4 (H.264 limited-range BT.709, + AAC when the log held sound), <out>/capture.json,
 *      <out>/events.json (the sound log on the film's clock), <out>/sound.wav, sfx.wav and music.wav (the mix
 *      and its two buses), <out>/captions.vtt when steps have captions. Raw frames are deleted once encoded.
 */
import { mkdirSync, readFileSync, rmSync, statfsSync, writeFileSync } from 'node:fs';
import { basename, dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { launch } from './lib/browser.mjs';
import { encodeMp4, writeConcat } from './lib/frames.mjs';
import { remix } from './lib/remix.mjs';
import { findStudio } from '../../music/scripts/lib/studio.mjs';
import { wavBytes } from '../../sound/scripts/lib/synth.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const has = (n) => argv.includes(`--${n}`);
const opt = (n, d = null) => { const i = argv.indexOf(`--${n}`); return i >= 0 && i + 1 < argv.length ? argv[i + 1] : d; };
const fail = (m, code = 2) => { process.stderr.write(`record-fixed: ${m}\n`); process.exit(code); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const log = (k, v = {}) => process.stderr.write(`${JSON.stringify({ t: +(process.uptime()).toFixed(1), k, ...v })}\n`);

let spec = { steps: [] };
if (opt('steps')) { try { spec = JSON.parse(readFileSync(resolve(String(opt('steps'))), 'utf8')); } catch (error) { fail(`--steps: ${error.message}`); } }
if (!Array.isArray(spec.steps)) fail('the steps file needs "steps": [ ... ]');
if (!opt('out')) fail('--out <folder>');
const OUT = resolve(String(opt('out')));
const base = String(opt('url', spec.base ?? '')).replace(/\/+$/, '');
const START = spec.url ?? (spec.path != null ? `${base}${String(spec.path).startsWith('/') ? '' : '/'}${spec.path}` : String(opt('url', '')));
if (!/^https?:\/\//.test(START)) fail('--url <the page to film> (or "url" / "path" in the steps file)');
const FPS = Number(opt('fps', spec.fps ?? 30));
const W = Number(opt('width', spec.width ?? 1920)); const H = Number(opt('height', spec.height ?? 1080));
const SCALE = Number(opt('scale', spec.scale ?? 1));
const SECONDS = Number(opt('seconds', spec.seconds ?? 30));
const SETTLE = Number(opt('settle', spec.settle ?? 2));
const TAIL = Number(spec.tail ?? 2);
const WAIT_FOR = opt('wait-for', spec.waitFor ?? null);
const WAIT_FRAME = opt('frame', spec.frame ?? null);
const CSS = opt('css', spec.css ?? null);
const PACE = !has('no-pace');
const MIN_FREE_GB = Number(opt('min-free-gb', 10));
if (!(Number.isInteger(FPS) && FPS >= 1 && FPS <= 60)) fail('--fps 1..60, a whole number');
if (!(SCALE >= 0.25 && SCALE <= 1)) fail('--scale 0.25..1');
if (!(SECONDS >= 1 && SECONDS <= 600)) fail('--seconds 1..600');
const RW = Math.max(2, Math.round((W * SCALE) / 2) * 2); const RH = Math.max(2, Math.round((H * SCALE) / 2) * 2);
const DT = 1000 / FPS;

mkdirSync(OUT, { recursive: true });
const freeGB = () => { try { const f = statfsSync(OUT); return (f.bavail * f.bsize) / 1e9; } catch { return 99; } };
if (freeGB() < MIN_FREE_GB + 2) fail(`only ${freeGB().toFixed(1)} GB free; a recording needs room (stopping below ${MIN_FREE_GB} GB)`);

const CLOCK = readFileSync(join(HERE, 'clock.js'), 'utf8');
// The sound log is asked for in every frame, before the page's own scripts: see sound.js.
const ASK = '(() => { if (!window.__homieSoundCapture) window.__homieSoundCapture = { events: [] }; })();';

/* ---------------------------------------------------------------- steps, on the virtual clock */

const KINDS = ['wait', 'waitFor', 'click', 'tap', 'key', 'keys', 'type', 'focus', 'caption'];
const NOT_HERE = ['goto', 'hover', 'move', 'drag', 'scroll'];
function normal(raw, i) {
  if (!raw || typeof raw !== 'object') throw new Error(`step ${i + 1} is not an object`);
  const other = NOT_HERE.find((k) => raw.do === k || k in raw);
  if (other) throw new Error(`step ${i + 1}: "${other}" is not a step of the frame-by-frame recorder (it has ${KINDS.join(', ')}); record-page.mjs has it, in real time`);
  const kind = raw.do ?? KINDS.find((k) => k in raw);
  if (!KINDS.includes(kind)) throw new Error(`step ${i + 1}: say what to do (${KINDS.join(', ')})`);
  const s = { ...raw, do: kind };
  const v = raw.do ? undefined : raw[kind];
  if (kind === 'wait' && v !== undefined) s.ms = Number(v);
  if (kind === 'waitFor' && v !== undefined) Object.assign(s, typeof v === 'string' ? { selector: v } : v);
  if (['click', 'tap'].includes(kind) && v !== undefined) Object.assign(s, typeof v === 'string' ? { selector: v } : Array.isArray(v) ? { at: v } : v);
  if (kind === 'key' && v !== undefined) s.key = v;
  if (kind === 'keys' && v !== undefined) s.keys = v;
  if (kind === 'type' && v !== undefined) s.text = v;
  if (kind === 'focus' && v !== undefined) Object.assign(s, typeof v === 'string' ? { frame: v } : v);
  if (kind === 'caption' && v !== undefined) s.caption = v;
  return s;
}
let steps;
try { steps = spec.steps.map(normal); } catch (error) { fail(error.message); }

const root = findStudio(OUT) ?? findStudio();
const report = { ran: new Date().toISOString(), start: START, fps: FPS, size: [W, H], ...(SCALE !== 1 ? { scale: SCALE, rendered: [RW, RH] } : {}), steps: [], notes: [] };
const { browser, close, pid } = await launch(root, { width: RW, height: RH, extra: ['--autoplay-policy=no-user-gesture-required', '--mute-audio'] });
log('browser', { pid });
const frameDir = join(OUT, 'frames');
rmSync(frameDir, { recursive: true, force: true });
mkdirSync(frameDir, { recursive: true });
const stop = async (why) => { log('stop', { why }); await close(); process.exit(3); };
process.on('SIGINT', () => stop('SIGINT'));
process.on('SIGTERM', () => stop('SIGTERM'));

let page;
let vt = 0; // the master clock, virtual ms since the page was opened
let vt0 = null; // the master clock when the film's first frame was copied
const events = []; // the sound log, t in seconds on the film's clock (negative: before the first frame)
const clockSeen = { timers: 0, animations: 0, frames: 0, errors: [] };
const captions = [];
const files = [];
let failed = null;
let sockets = 0;

function frameOf(name) {
  if (!name || name === 'top' || name === 'page') return page.mainFrame();
  const want = name === 'game' ? /\/__game\//i : null;
  return page.frames().find((f) => !f.isDetached() && (want ? want.test(f.url()) : f.url().includes(String(name)))) ?? null;
}

/** One film frame of time in every frame of the page, together; the sound each one logged comes back with it. */
async function stepAll(ms) {
  const before = vt;
  vt += ms;
  await Promise.all(page.frames().filter((f) => !f.isDetached()).map(async (f) => {
    let r = null;
    try {
      r = await f.evaluate((d) => (window.__homieClock ? window.__homieClock.step(d).then((x) => ({ ...x, events: window.__homieSoundCapture ? window.__homieSoundCapture.events.splice(0) : [] })) : null), ms);
    } catch { /* a frame that went away mid-step */ }
    if (!r) return;
    clockSeen.timers = Math.max(clockSeen.timers, r.timers); clockSeen.animations = Math.max(clockSeen.animations, r.animations); clockSeen.frames = Math.max(clockSeen.frames, r.frames);
    for (const e of r.errors ?? []) if (clockSeen.errors.length < 20) clockSeen.errors.push(e);
    // A frame's own clock began at 0 when its document did: its events are moved onto the master clock.
    const offset = before + ms - r.now;
    for (const e of r.events) events.push({ ...e, t: e.t + offset });
  }));
}

/* ---- the steps run as one script that sleeps on the virtual clock; the frame loop wakes it between frames */
const sleepers = [];
let parkResolve = () => {};
let scriptDone = steps.length === 0;
let scriptEndedAt = steps.length === 0 ? 0 : null;
const vsleep = (ms) => new Promise((res) => { sleepers.push({ at: vt + Math.max(0, ms), res }); parkResolve(); });
async function wake() {
  const due = sleepers.filter((s) => s.at <= vt + 1e-6);
  if (!due.length || scriptDone) return;
  const parked = new Promise((r) => { parkResolve = r; });
  for (const s of due) { sleepers.splice(sleepers.indexOf(s), 1); s.res(); }
  await parked;
}
const filmNow = () => (vt0 === null ? 0 : (vt - vt0) / 1000);
async function until(test, timeout, what) {
  const end = vt + timeout;
  for (;;) {
    if (await test().catch(() => false)) return;
    if (vt > end) throw new Error(`${what} did not happen within ${timeout} ms of the film`);
    await vsleep(DT);
  }
}
async function pointOf(s, timeout) {
  if (Array.isArray(s.at)) { const [x, y] = s.at.map(Number); return x <= 1 && y <= 1 && x >= 0 && y >= 0 ? { x: x * RW, y: y * RH } : { x, y }; }
  if (!s.selector) throw new Error('give "selector" or "at": [x, y]');
  let box = null;
  await until(async () => { const f = frameOf(s.frame); const el = f ? await f.$(s.selector) : null; box = el ? await el.boundingBox() : null; return Boolean(box); }, timeout, `"${s.selector}"`);
  return { x: box.x + box.width * (s.offset?.[0] ?? 0.5), y: box.y + box.height * (s.offset?.[1] ?? 0.5) };
}
async function runStep(s) {
  const timeout = Number(s.timeout ?? 20_000);
  switch (s.do) {
    case 'wait': await vsleep(Number(s.ms ?? 1000)); break;
    case 'caption': await vsleep(Number(s.ms ?? 0)); break;
    case 'waitFor': {
      if (s.selector) await until(async () => Boolean(await frameOf(s.frame)?.$(s.selector)), timeout, `"${s.selector}"`);
      else if (s.text) await until(() => frameOf(s.frame).evaluate((t) => Boolean(document.body && document.body.innerText.includes(t)), String(s.text)), timeout, `the text "${s.text}"`);
      else if (s.js) await until(() => frameOf(s.frame).evaluate(String(s.js)).then(Boolean), timeout, 'the "js" condition');
      else if (s.frame) await until(async () => Boolean(frameOf(s.frame)), timeout, `the frame "${s.frame}"`);
      else throw new Error('waitFor needs "selector", "text", "js" or "frame"');
      break;
    }
    case 'click': { const p = await pointOf(s, timeout); await page.mouse.move(p.x, p.y); await page.mouse.down(); await vsleep(Number(s.hold ?? 60)); await page.mouse.up(); break; }
    case 'tap': { const p = await pointOf(s, timeout); await page.touchscreen.touchStart(p.x, p.y); await vsleep(Number(s.hold ?? 60)); await page.touchscreen.touchEnd(); break; }
    case 'focus': {
      await until(async () => Boolean(frameOf(s.frame ?? 'game')), timeout, `the frame "${s.frame ?? 'game'}"`);
      const f = frameOf(s.frame ?? 'game');
      if (f !== page.mainFrame()) { const el = await f.frameElement(); await el?.focus(); await f.evaluate(() => window.focus()); }
      if (s.selector) await (await f.$(s.selector))?.focus();
      break;
    }
    case 'key': case 'keys': {
      if (s.frame) { const f = frameOf(s.frame); if (f && f !== page.mainFrame()) { const el = await f.frameElement(); await el?.focus().catch(() => {}); } }
      const list = s.do === 'key' ? [s.key] : (Array.isArray(s.keys) ? s.keys : [s.keys]);
      for (let t = 0; t < Number(s.times ?? 1); t++) {
        for (const k of list) {
          const chord = String(k).split('+');
          for (const c of chord) await page.keyboard.down(c);
          await vsleep(Number(s.hold ?? 120));
          for (const c of [...chord].reverse()) await page.keyboard.up(c);
          await vsleep(Number(s.gap ?? 120));
        }
      }
      break;
    }
    case 'type': {
      if (s.into || s.selector) { const p = await pointOf({ ...s, selector: s.into ?? s.selector }, timeout); await page.mouse.click(p.x, p.y); }
      for (const ch of String(s.text ?? '')) { await page.keyboard.type(ch); await vsleep(Number(s.delay ?? 70)); }
      break;
    }
    default: throw new Error(`unknown step "${s.do}"`);
  }
}
async function script() {
  try {
    for (const [i, s] of steps.entries()) {
      const at = filmNow();
      if (s.caption) captions.push({ from: at, to: at + Number(s.captionSeconds ?? 3), text: String(s.caption) });
      try {
        await runStep(s);
        report.steps.push({ i: i + 1, do: s.do, at: +at.toFixed(3), took: +(filmNow() - at).toFixed(3), ...(s.selector ? { selector: s.selector } : {}), ...(s.key ? { key: s.key } : {}) });
      } catch (error) {
        const why = String(error.message ?? error).split('\n')[0].slice(0, 300);
        report.steps.push({ i: i + 1, do: s.do, at: +at.toFixed(3), failed: why });
        if (s.optional) continue;
        failed = { step: i + 1, do: s.do, why };
        break;
      }
    }
  } finally { scriptDone = true; scriptEndedAt = filmNow(); parkResolve(); }
}

/* ---------------------------------------------------------------- the film */

const realStart = Date.now();
let realRecordStart = null;
try {
  page = await browser.newPage();
  await page.setViewport({ width: RW, height: RH, deviceScaleFactor: 1 });
  const ua0 = await browser.userAgent();
  await page.setUserAgent(`${ua0} homie-studio-check video-record`);
  await page.evaluateOnNewDocument(ASK);
  await page.evaluateOnNewDocument(CLOCK);
  const errors = [];
  page.on('pageerror', (e) => { if (errors.length < 30) errors.push(String(e.message).slice(0, 200)); });
  const cdp = await page.createCDPSession();
  await cdp.send('Network.enable').catch(() => {});
  cdp.on('Network.webSocketCreated', () => { sockets++; });
  let loaded = false;
  page.once('load', () => { loaded = true; });
  // The page cannot finish loading with its clock stopped (a loader on a timer, a fade-in), so the clock is run at
  // the wall's speed until the page is ready: loaded, settled, and whatever --wait-for asks for.
  const nav = page.goto(START, { waitUntil: 'domcontentloaded', timeout: 60_000 });
  nav.catch(() => {});
  await nav;
  if (CSS) await page.addStyleTag({ content: String(CSS) }).catch(() => {});
  const ready = async () => {
    if (!loaded || vt < SETTLE * 1000) return false;
    if (WAIT_FRAME && !frameOf(WAIT_FRAME)) return false;
    if (!WAIT_FOR) return true;
    return Boolean(await (frameOf(WAIT_FRAME) ?? page.mainFrame()).evaluate(String(WAIT_FOR)).catch(() => false));
  };
  const giveUp = Date.now() + 90_000;
  for (;;) {
    const t = Date.now();
    await stepAll(DT);
    if (await ready()) break;
    if (Date.now() > giveUp) throw new Error(`the page was not ready within 90 s${WAIT_FOR ? ` (--wait-for ${WAIT_FOR})` : ''}${WAIT_FRAME ? ` (--frame ${WAIT_FRAME})` : ''}`);
    const left = DT - (Date.now() - t);
    if (left > 0) await sleep(left);
  }
  await page.keyboard.press('Shift').catch(() => {}); // a first gesture, for a game that starts its sound on one
  report.renderer = await page.evaluate(() => {
    try { const gl = document.createElement('canvas').getContext('webgl'); const x = gl && gl.getExtension('WEBGL_debug_renderer_info'); return gl ? String(x ? gl.getParameter(x.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER)) : 'no WebGL'; } catch { return 'unknown'; }
  }).catch(() => 'unknown');
  log('ready', { settledAt: +(vt / 1000).toFixed(2), renderer: report.renderer });

  vt0 = vt;
  realRecordStart = Date.now();
  const maxFrames = Math.round(SECONDS * FPS);
  if (steps.length) { const parked = new Promise((r) => { parkResolve = r; }); script(); await parked; }
  let lastLog = Date.now();
  for (let k = 0; k < maxFrames; k++) {
    const shot = await cdp.send('Page.captureScreenshot', { format: 'jpeg', quality: 92, optimizeForSpeed: true });
    const file = join(frameDir, `${String(k).padStart(6, '0')}.jpg`);
    writeFileSync(file, Buffer.from(shot.data, 'base64'));
    files.push(file);
    // With steps, the film ends `tail` seconds after the last one (or at --seconds); without, at --seconds.
    if (steps.length && scriptDone && filmNow() >= scriptEndedAt + TAIL) break;
    if (failed) break;
    if (freeGB() < MIN_FREE_GB) { report.notes.push('stopped early: disk low'); break; }
    await wake();
    await stepAll(DT);
    if (PACE) { const ahead = (vt - vt0) - (Date.now() - realRecordStart); if (ahead > 0) await sleep(ahead); }
    if (Date.now() - lastLog > 10_000) { lastLog = Date.now(); log('rendering', { frame: k + 1, of: maxFrames, filmS: +filmNow().toFixed(1), realS: +((Date.now() - realRecordStart) / 1000).toFixed(1) }); }
  }
  if (steps.length && !scriptDone) report.notes.push(`stopped at --seconds ${SECONDS} before the steps finished`);
  report.errors = errors;
} catch (error) {
  report.crashed = String(error.stack ?? error).split('\n').slice(0, 3).join(' ');
}
const realSeconds = realRecordStart ? (Date.now() - realRecordStart) / 1000 : 0;

/* ---- the game's own sound files, from the page's own origin and nowhere else */
const origin = new URL(START).origin;
const soundDir = join(OUT, 'sounds');
const local = new Map();
const notFetched = [];
const filmEvents = events.map((e) => ({ ...e, t: +((e.t - (vt0 ?? 0)) / 1000).toFixed(4) })).sort((a, b) => a.t - b.t);
if (!report.crashed && files.length) {
  rmSync(soundDir, { recursive: true, force: true });
  const urls = [...new Set(filmEvents.filter((e) => e.type === 'start' && e.url).map((e) => e.url))];
  if (urls.length) mkdirSync(soundDir, { recursive: true });
  for (const [i, u] of urls.entries()) {
    let ok = false;
    try {
      if (new URL(u).origin !== origin) throw new Error('another origin');
      const r = await fetch(u);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const f = join(soundDir, `${String(i).padStart(3, '0')}-${basename(new URL(u).pathname).replace(/[^A-Za-z0-9._-]/g, '_')}`);
      writeFileSync(f, Buffer.from(await r.arrayBuffer()));
      local.set(u, f); ok = true;
    } catch (error) { notFetched.push({ url: u, why: String(error.message ?? error).slice(0, 120) }); }
    if (!ok) local.set(u, null);
  }
}
await close();

if (report.crashed || files.length < 1) {
  writeFileSync(join(OUT, 'capture.json'), `${JSON.stringify({ ...report, frames: files.length }, null, 1)}\n`);
  rmSync(frameDir, { recursive: true, force: true });
  fail(report.crashed ? `the recording failed: ${report.crashed}` : 'no frame was rendered', 1);
}

const total = files.length;
const seconds = total / FPS;
/* ---- sound: the log mixed again on the film's clock */
let audio = null;
const starts = filmEvents.filter((e) => e.type === 'start');
if (starts.length) {
  const m = remix(filmEvents, { seconds, fileFor: (u) => local.get(u) ?? null });
  for (const [name, buf] of [['sound', m.mix], ['sfx', m.sfx], ['music', m.music]]) writeFileSync(join(OUT, `${name}.wav`), wavBytes(buf, { bits: 16 }));
  const raw = join(OUT, 'sound.raw');
  const pcm = Buffer.alloc(m.mix.L.length * 4);
  for (let i = 0; i < m.mix.L.length; i++) { pcm.writeInt16LE(Math.round(Math.max(-1, Math.min(1, m.mix.L[i])) * 32767), i * 4); pcm.writeInt16LE(Math.round(Math.max(-1, Math.min(1, m.mix.R[i])) * 32767), i * 4 + 2); }
  writeFileSync(raw, pcm);
  audio = { rebuilt: true, rate: 48000, seconds: +m.report.seconds.toFixed(3), peakDb: m.report.peakDb, placed: m.report.placed, dropped: m.report.dropped, files: m.report.files, limited: m.report.limited, missing: m.report.missing, stems: { mix: 'sound.wav', sfx: 'sfx.wav', music: 'music.wav' }, raw, note: m.report.note };
} else for (const f of ['sound.wav', 'sfx.wav', 'music.wav']) rmSync(join(OUT, f), { force: true });
writeFileSync(join(OUT, 'events.json'), `${JSON.stringify({ fps: FPS, frames: total, seconds: +seconds.toFixed(4), origin, events: filmEvents }, null, 1)}\n`);

const concat = writeConcat(join(OUT, 'frames.txt'), files, FPS);
const mp4 = join(OUT, 'capture.mp4');
const enc = encodeMp4({ concat, audio, fps: FPS, width: W, height: H, seconds, out: mp4, crf: 16 });
rmSync(frameDir, { recursive: true, force: true });
rmSync(concat, { force: true });
rmSync(soundDir, { recursive: true, force: true });
if (audio) delete audio.raw;
if (!enc.ok) fail(`encode failed: ${enc.why}`, 1);

const vtt = (x) => { const h = Math.floor(x / 3600); const m = Math.floor((x % 3600) / 60); const sec = (x % 60).toFixed(3).padStart(6, '0'); return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${sec}`; };
if (captions.length) {
  const cues = captions.map((c, i) => ({ from: c.from, to: Math.min(seconds, captions[i + 1] ? Math.min(c.to, captions[i + 1].from) : c.to), text: c.text })).filter((c) => c.to > c.from);
  writeFileSync(join(OUT, 'captions.vtt'), `WEBVTT\n\n${cues.map((c) => `${vtt(c.from)} --> ${vtt(c.to)}\n${c.text}`).join('\n\n')}\n`);
}

const speed = realSeconds > 0 ? +(seconds / realSeconds).toFixed(2) : null;
const warnings = [];
if (/swiftshader|llvmpipe|software|basic render/i.test(String(report.renderer))) report.notes.push(`drawn on a software renderer (${report.renderer}): slow to render, and the film is unaffected, each frame is still one frame`);
if (sockets > 0 && speed !== null && speed < 0.8) warnings.push(`the page holds ${sockets} live connection(s) and the film was rendered at ${speed} of real time: a server on the other end kept real time, so what it sent arrived ${(1 / speed).toFixed(1)} times too fast for the film. For a room on a relay, film it in real time (capture), or render smaller (--scale) until the speed is near 1.`);
if (!starts.length) warnings.push('the page logged no sound: the film is silent. The sound player made by the sound skill logs when asked (sound.js); a game with its own audio code has to push the same events (window.__homieSoundCapture.events).');
if (audio?.missing?.length || notFetched.length) warnings.push(`${new Set([...(audio?.missing ?? []), ...notFetched.map((x) => x.url)]).size} sound file(s) named in the log could not be read (${notFetched.slice(0, 2).map((x) => `${x.url}: ${x.why}`).join('; ') || 'not decodable'}): those sounds are missing from the mix`);
if (clockSeen.errors.length) report.notes.push(`callbacks threw while the clock ran them: ${clockSeen.errors.slice(0, 3).join(' | ')}`);
const result = {
  ...report, file: 'capture.mp4', seconds: +seconds.toFixed(3), outputFrames: total, sourceFps: FPS, heldFrames: 0, distinctFramesUsed: total,
  realSeconds: +realSeconds.toFixed(1), speed, settled: +((vt0 ?? 0) / 1000).toFixed(2), webSockets: sockets,
  clock: { virtual: ['requestAnimationFrame', 'performance.now', 'Date', 'setTimeout', 'setInterval', 'CSS animations', 'CSS transitions', 'Web Animations'], notVirtual: ['AudioContext.currentTime', 'video and audio elements', 'Web Workers', 'the network'], mostTimers: clockSeen.timers, mostAnimations: clockSeen.animations },
  audio, events: 'events.json', soundEvents: filmEvents.length, ...(captions.length ? { captions: 'captions.vtt' } : {}), ...(warnings.length ? { warnings } : {}), ...(failed ? { failed } : {}),
  honesty: `Rendered frame by frame from the page on a virtual clock at ${FPS} frames a second: every frame is one the page drew, none is held or invented, and the page's own clocks moved 1/${FPS} s a frame however long it took to draw. ${starts.length ? 'The sound is mixed again offline from the game\'s own sound files and its log of what it played; it is not a recording of a speaker.' : 'It has no sound.'}`,
};
writeFileSync(join(OUT, 'capture.json'), `${JSON.stringify(result, null, 1)}\n`);
const ok = !failed;
process.stdout.write(`${JSON.stringify({
  ok, file: mp4, json: join(OUT, 'capture.json'), events: join(OUT, 'events.json'), ...(captions.length ? { captions: join(OUT, 'captions.vtt') } : {}),
  seconds: result.seconds, frames: total, heldFrames: 0, realSeconds: result.realSeconds, speed, soundEvents: filmEvents.length,
  audio: audio ? { seconds: audio.seconds, peakDb: audio.peakDb, placed: audio.placed, missing: audio.missing.length } : null, steps: report.steps.length,
  ...(failed ? { failed } : {}), ...(warnings.length ? { warnings } : {}),
})}\n`);
process.exit(ok ? 0 : 1);
