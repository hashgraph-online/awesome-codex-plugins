#!/usr/bin/env node
/**
 * playtest.mjs: play a studio's game in real browsers and come back with numbers about it:
 * how fast a stranger is in and moving, what the screen looks like on a computer and on a phone held
 * both ways, how much of it the UI covers, what the game really sounds like, and how a round goes when
 * one person plays hard and another does nothing. Then the owner tests and the two-stranger round from
 * @homie-rocks/studio. It writes pictures and a report, and a brief for a blind reviewer.
 *
 *   run <game> --url <site> [--only first,look,ui,sound,play,controls,round] [--seconds 20] [--out <dir>]
 *   review <run folder> [--to "<who reviews>"] [--local]
 *                            write REVIEW.md: the brief a fresh reviewer (a subagent that never saw the code) scores from,
 *                            and say exactly which files the review step hands over, as one question to approve once.
 *                            --local writes REVIEW-LOCAL.md instead: the same rubric for this session to score the
 *                            pictures itself when nothing may leave it (labelled NOT independent).
 *   reviewed <run folder> --kind independent|local|none [--by "<who>"] [--reason "<why>"] [--score <0-100>]
 *                            record which review ran (or that none did, and why) in the run's report
 *   report <run folder>      print a finished run's report again
 *
 * Headless Chrome on the GPU through puppeteer-core from the studio's node_modules (it comes with
 * @homie-rocks/studio). At most two browsers at a time. The browsers are muted: nothing plays out loud.
 * Rows say PASS, FAIL, WARN, BLOCKED or N/A. BLOCKED means it could not be measured (a software renderer, a stuck
 * decoder, a round that was on its results screen for the whole wait), which is never the same as "fine". N/A means
 * the row did not apply to what was on screen (a results card is not judged against the active-play UI bar).
 *
 * What the game's state is at each press and each picture (round phase, time left, whether the body is the player's
 * to steer, control mode) comes from the port probe and the play page's shell: lib/judge.mjs lists every name read.
 * game.json may declare the game's primary action ("playtest": { "primary": ... }) and "scoring": "together".
 */
import { spawn } from 'node:child_process';
import { appendFileSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, statSync, statfsSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { experienceDir, experienceJson, findStudio, readJson } from '../../music/scripts/lib/studio.mjs';
import { measure, sheetPng, warnings } from '../../sound/scripts/lib/measure.mjs';
import { wavBytes } from '../../sound/scripts/lib/synth.mjs';
import { GPU_FLAGS, chromePath, loadPuppeteer } from '../../video/scripts/lib/browser.mjs';
import { finish, within } from './lib/exit.mjs';
import { actionProfile, activePlay, connectionNote, contextOf, describeActions, describeState, judgeFirst, judgeMove, judgeScores, judgeUi, oppositeOf, shellOverlaps, EXTRA_NAMES, readPort, UI_CAVEAT, pairMismatch, readinessOf, renderCost, reportMd, reviewLine, stateOf, weakest, REVIEW_KINDS } from './lib/judge.mjs';
import { decode, motion, stats, uiCover } from './lib/pixels.mjs';
import { preflight } from './lib/preflight.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const TAP = readFileSync(join(HERE, '..', '..', 'video', 'scripts', 'tap.js'), 'utf8');
const argv = process.argv.slice(2);
const flags = new Map();
const pos = [];
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a.startsWith('--')) { const k = a.slice(2); const v = argv[i + 1]; if (v === undefined || v.startsWith('--')) flags.set(k, true); else { flags.set(k, v); i++; } } else pos.push(a);
}
const JSON_OUT = flags.has('json');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const log = (m) => { if (!JSON_OUT) process.stderr.write(`${m}\n`); };
// A bounded wait whose losing timer is cleared (lib/exit.mjs): a race that leaves its timer behind keeps Node alive.
const T = (p, ms, v = null) => within(p, ms, v);

const DEVICES = {
  desk: { width: 1280, height: 800, isMobile: false, hasTouch: false, deviceScaleFactor: 1 },
  phone: { width: 390, height: 844, isMobile: true, hasTouch: true, deviceScaleFactor: 2 },
  'phone-landscape': { width: 844, height: 390, isMobile: true, hasTouch: true, deviceScaleFactor: 2 },
};
const PHONE_UA = 'Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36';

/* ---------------------------------------------------------------- browsers */

let puppeteer = null;
let EXE = null;
const open = [];

/** Open one muted headless GPU Chrome on the game's play page (or /tv). */
async function launch(device, url, { tap = false, autoplay = false } = {}) {
  const vp = DEVICES[device];
  const profile = mkdtempSync(join(tmpdir(), 'homie-playtest-'));
  const browser = await puppeteer.launch({
    executablePath: EXE, headless: true, userDataDir: profile, timeout: 150_000, protocolTimeout: 120_000, // 150 s to start on a loaded computer
    args: [...GPU_FLAGS, '--mute-audio', `--window-size=${vp.width},${vp.height}`, '--no-first-run', '--no-default-browser-check', '--disable-background-timer-throttling', '--disable-renderer-backgrounding', '--disable-backgrounding-occluded-windows', '--force-color-profile=srgb', ...(autoplay ? ['--autoplay-policy=no-user-gesture-required'] : [])],
  });
  const page = await browser.newPage();
  await page.setViewport(vp);
  const ua = vp.isMobile ? PHONE_UA : await browser.userAgent();
  await page.setUserAgent(`${ua} homie-playtest`);
  const h = { device, vp, browser, page, profile, errors: [], bad: [], t0: 0 };
  page.on('pageerror', (e) => h.errors.push(String(e?.message ?? e).slice(0, 300)));
  page.on('console', (m) => { if (m.type() === 'error') h.errors.push(`console: ${m.text().slice(0, 300)}`); });
  page.on('response', (r) => { if (r.status() >= 400) h.bad.push(`${r.status()} ${r.url().replace(/^https?:\/\/[^/]+/, '')}`); });
  if (tap) await page.evaluateOnNewDocument(TAP);
  // A frame counter in every frame: rAF ticks, so a software renderer's 1-2 fps is seen before it is judged.
  await page.evaluateOnNewDocument(() => { let n = 0; const tick = () => { n++; requestAnimationFrame(tick); }; requestAnimationFrame(tick); window.__ptFrames = () => n; });
  open.push(h);
  h.t0 = Date.now();
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60_000 });
  return h;
}

async function close(h) {
  const i = open.indexOf(h);
  if (i >= 0) open.splice(i, 1);
  try { await T(h.browser.close(), 8000); } catch { /* */ }
  try { h.browser.process()?.kill('SIGKILL'); } catch { /* */ }
  rmSync(h.profile, { recursive: true, force: true });
}

const gameFrame = (h) => h.page.frames().find((f) => /\/__game\//.test(f.url())) ?? null;
async function waitFrame(h, ms = 30_000) {
  const until = Date.now() + ms;
  while (Date.now() < until) { const f = gameFrame(h); if (f) return f; await sleep(200); }
  return null;
}
const shell = (h) => T(h.page.evaluate(() => { const s = window.__shell; return s ? { room: s.room, seat: s.seat, role: s.stats?.role ?? null, round: s.round, results: s.results } : null; }), 5000);
const inFrame = async (h, fn, arg) => { const f = gameFrame(h); return f ? T(f.evaluate(fn, arg), 8000) : null; };
const probeInfo = (h) => inFrame(h, () => { const p = window.__homiePort; if (!p) return null; const i = p.info(); return { view: p.view, size: p.size, keys: p.keys, thumb: p.thumb, world: p.world, info: i, now: p.now() }; });
const selfAt = (h, since) => inFrame(h, (s) => { const p = window.__homiePort; if (!p) return null; const rows = p.rows(s); return rows.length ? rows[rows.length - 1] : null; }, since);
const frameNow = (h) => inFrame(h, () => performance.now());

/**
 * The game's visible DOM HUD, as rectangles in the frame's CSS pixels (run inside the game's frame): every element
 * that shows something of its own (text, a picture, a control) and is not the world (a canvas, a video, the game's
 * declared world element) nor the helper's own "Reconnecting" line. At most 150, the outermost of each. A HUD drawn
 * inside the canvas has no element and is not here.
 */
const HUD_ELEMENTS = (worldSel) => {
  const out = [];
  const world = worldSel ? [...document.querySelectorAll(worldSel)] : [];
  const press = (el) => /^(BUTTON|A|INPUT|SELECT|TEXTAREA)$/.test(el.tagName) || el.getAttribute('role') === 'button' || el.hasAttribute('data-action');
  const own = (el) => press(el) || /^(IMG|SVG|svg)$/.test(el.tagName) || [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
  const walk = (el) => {
    if (out.length >= 150) return;
    if (/^(CANVAS|VIDEO|SCRIPT|STYLE|IFRAME)$/.test(el.tagName) || world.includes(el) || el.hasAttribute('data-homie-link')) return;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || Number(cs.opacity) < 0.05) return;
    if (own(el)) {
      const b = el.getBoundingClientRect();
      if (b.width > 0 && b.height > 0 && b.right > 0 && b.bottom > 0 && b.left < innerWidth && b.top < innerHeight) {
        const name = `${el.tagName.toLowerCase()}${el.id ? `#${el.id}` : el.classList[0] ? `.${el.classList[0]}` : ''}`;
        const text = (el.textContent || el.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim().slice(0, 24);
        out.push({ label: text ? `${name} "${text}"` : name, x: Math.round(b.left), y: Math.round(b.top), w: Math.round(b.width), h: Math.round(b.height), interactive: press(el) });
        return; // the outermost element that shows something stands for what is inside it
      }
    }
    for (const c of el.children) walk(c);
  };
  if (document.body) walk(document.body);
  return out;
};

/**
 * The game's state right now, from what it exposes (lib/judge.mjs says which names): the round and time left, whether
 * the body is the player's to steer, where it is, the control mode and loadout, and the page's loading cover.
 * Anything the game does not expose stays null; nothing here changes the game.
 */
async function readState(h) {
  const [port, sh, net] = await Promise.all([
    inFrame(h, readPort, EXTRA_NAMES),
    T(h.page.evaluate(() => { const s = window.__shell; if (!s) return null; const a = s.arrival; const r = s.round; return { seat: s.seat, round: r ? { n: r.n, phase: r.phase, endsAt: r.endsAt } : null, arrival: a ? { phase: a.phase, liftedMs: a.liftedMs, by: a.by } : null, link: s.link && typeof s.link === 'object' ? { state: s.link.state } : null, stale: s.stale ? { ver: s.stale.ver ?? null } : null }; }), 5000),
    // The helper's own word on its link (revision 9), in the game's frame: a browser cut off from its room is labelled, not judged as play.
    inFrame(h, () => { const n = window.__homieNet; return n ? { link: typeof n.link === 'string' ? n.link : null, reconnects: Number.isFinite(n.reconnects) ? n.reconnects : null, stale: typeof n.stale === 'string' ? n.stale : null } : null; }),
  ]);
  const st = stateOf({ at: Date.now(), port, shell: sh, net });
  // Not part of the game's state, kept beside it: the renderer's counters at this moment (measured runtime cost).
  Object.defineProperty(st, 'render', { enumerable: false, value: port?.extra ? { drawCalls: port.extra.drawCalls, triangles: port.extra.triangles } : null });
  return st;
}

/** Wait (at most `ms`) for a moment that can be judged as active play: a live round, a free body, the cover gone. */
async function waitActive(h, ms) {
  const t0 = Date.now(); let state = null;
  while (Date.now() - t0 < ms) {
    state = await readState(h);
    // true: active play. null: the game does not say, so there is nothing to wait for (the row says "unknown").
    if (activePlay(state) !== false) return { ok: true, ms: Date.now() - t0, state };
    await sleep(300);
  }
  return { ok: false, ms: Date.now() - t0, state };
}

/** The game's own frame counter (the probe's, else requestAnimationFrame in the game's frame): its render heartbeat. */
const heartbeat = (h) => inFrame(h, () => { let n = null; try { n = window.__homiePort?.info?.().frames ?? null; } catch { /* */ } return n ?? window.__ptFrames?.() ?? null; });

async function screenshot(h) { return T(h.page.screenshot({ type: 'png', captureBeyondViewport: false }), 15_000); }

/** What a session's script really pressed: counted as it goes, so a score conclusion can say what was exercised. */
const newActions = (profile) => ({ moves: 0, primary: { declared: profile.declared, how: profile.how, pressed: 0, missed: 0 } });

/**
 * Press the game's primary action once, the way game.json declares it (lib/judge.mjs actionProfile): a key, a mouse
 * button, the game's own touch control found by its selector, or a declared region. False when a declared control
 * was not on screen (hidden between rounds, another loadout): counted as missed, never as pressed.
 */
async function pressPrimary(h, profile) {
  try {
    if (profile.kind === 'key') { await h.page.keyboard.press(profile.key); return true; }
    if (profile.kind === 'mouse') { await h.page.mouse.click(Math.round(h.vp.width * profile.at[0]), Math.round(h.vp.height * profile.at[1]), { button: profile.button }); return true; }
    if (profile.kind === 'selector') {
      const f = gameFrame(h);
      const el = f ? await T(f.$(profile.selector), 3000) : null;
      // An element in the game's frame: puppeteer gives its box in the page's own coordinates.
      const box = el ? await T(el.boundingBox(), 3000) : null;
      try { await el?.dispose(); } catch { /* */ }
      if (!box || box.width < 2 || box.height < 2) return false;
      await h.page.touchscreen.tap(Math.round(box.x + box.width / 2), Math.round(box.y + box.height / 2));
      return true;
    }
    const [x, y, w, hh] = profile.region;
    await h.page.touchscreen.tap(Math.round(h.vp.width * (x + w / 2)), Math.round(h.vp.height * (y + hh / 2)));
    return true;
  } catch { return false; }
}

/** Hold one direction for `ms`: a key on a computer, a thumb on the game's stick on a phone. */
async function hold(h, dir, ms, probe) {
  const keys = probe?.keys ?? { up: 'ArrowUp', down: 'ArrowDown', left: 'ArrowLeft', right: 'ArrowRight' };
  if (h.vp.hasTouch) await drag(h, dir, ms, probe);
  else { await h.page.keyboard.down(keys[dir]).catch(() => {}); await sleep(ms); await h.page.keyboard.up(keys[dir]).catch(() => {}); }
}

/** Play like a person: hold a direction for most of a second, now and then press the primary action, change your mind. */
async function playFor(h, seconds, probe, { rng = Math.random, profile = actionProfile(null, h.device), actions = newActions(profile) } = {}) {
  const until = Date.now() + seconds * 1000;
  const dirs = ['up', 'right', 'down', 'left'];
  let presses = 0;
  const times = [];
  while (Date.now() < until) {
    const d = dirs[Math.floor(rng() * 4)];
    const ms = 500 + Math.floor(rng() * 900);
    times.push(Date.now());
    await hold(h, d, ms, probe);
    presses++; actions.moves++;
    if (rng() < 0.3) {
      times.push(Date.now());
      if (await pressPrimary(h, profile)) { actions.primary.pressed++; presses++; } else actions.primary.missed++;
    }
    await sleep(80 + Math.floor(rng() * 200));
  }
  return { presses, times, actions };
}

/** A thumb lands where the game's stick lives, slides 70 px the pressed way in small steps, holds, lifts. */
async function drag(h, dir, hold, probe) {
  const [fx, fy] = probe?.thumb ?? [0.24, 0.74];
  const x = Math.round(h.vp.width * fx); const y = Math.round(h.vp.height * fy);
  const v = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] }[dir];
  const ts = h.page.touchscreen;
  try {
    await ts.touchStart(x, y);
    for (let k = 1; k <= 6; k++) { await ts.touchMove(x + v[0] * 12 * k, y + v[1] * 12 * k); await sleep(16); }
    const until = Date.now() + hold;
    let w = 0;
    while (Date.now() < until) { w++; await ts.touchMove(x + v[0] * 72 + (w % 2), y + v[1] * 72); await sleep(60); }
    await ts.touchEnd();
  } catch { /* a closed page */ }
}

/* ---------------------------------------------------------------- rows */

const rows = [];
const row = (name, verdict, detail = {}) => { rows.push({ name, verdict, ...detail }); log(`${verdict.padEnd(7)} ${name}${detail.why ? `: ${detail.why}` : ''}`); };

/**
 * One device, one browser: the first seconds (seated, first paint, the loading cover gone, the first picture of the
 * game itself), the first move, the look during play, and how much of the screen the UI covers. Every press and
 * every picture is taken with the game's state beside it (readState), and a row that needs active play waits for it.
 */
async function deviceSession(device, base, game, out, seconds, only, gameJson) {
  const h = await launch(device, `${base}/${game}/play`);
  const profile = actionProfile(gameJson, device);
  const actions = newActions(profile);
  const save = async (name, png) => { if (!png) return null; const f = join(out, `${device}-${name}.png`); writeFileSync(f, png); return f; };
  try {
    // First seconds. Four separate times (lib/judge.mjs readinessOf): a seat; the page's first paint, which is the
    // loading card and not the game; the cover gone; and the first picture with the cover gone and the game's own
    // frames advancing. A non-black loading screen at 35 ms is not "the first picture of the game".
    const samples = []; let paintPng = null; let gamePng = null; let lastBeat = null; let beatFrom = null;
    const marks = [1000, 3000, 5000, 10000];
    const firstShots = [];
    const until = h.t0 + 30_000;
    while (Date.now() < until && (marks.length || !samples.some((x) => x.seated) || !gamePng)) {
      const s = await shell(h);
      const seated = Boolean(s?.room && s.seat !== null && s.seat !== undefined && s.role);
      const st = await readState(h);
      const beat = await heartbeat(h);
      const moved = Number.isFinite(beat) && Number.isFinite(lastBeat) && beat > lastBeat;
      if (Number.isFinite(beat)) { lastBeat = beat; beatFrom ??= st.source === 'probe' ? 'the port probe\'s frame counter' : 'requestAnimationFrame in the game\'s frame'; }
      const el = Date.now() - h.t0;
      let picture = false;
      if (!gamePng || (marks.length && el >= marks[0])) {
        const png = await screenshot(h);
        if (png) {
          const ps = stats(decode(png, 320));
          picture = !ps.black && !ps.flat;
          if (picture && !paintPng) paintPng = png;
          if (picture && moved && st.cover !== 'up' && !gamePng) gamePng = png;
          if (marks.length && el >= marks[0]) { const m = marks.shift(); firstShots.push({ at: m, file: await save(`first-${m / 1000}s`, png), state: describeState(st), ...ps }); }
        }
      }
      samples.push({ ms: el, seated, picture, cover: st.cover, heartbeat: moved });
      await sleep(250);
    }
    const ready = readinessOf(samples);
    const frame = await waitFrame(h, 5000);
    const probe = await probeInfo(h);
    const fps = frame ? await T(frame.evaluate(() => new Promise((r) => { const a = window.__ptFrames?.() ?? 0; setTimeout(() => r(((window.__ptFrames?.() ?? 0) - a) / 2), 2000); })), 6000) : null;
    const renderer = frame ? await T(frame.evaluate(() => { try { const c = document.createElement('canvas'); const g = c.getContext('webgl2') || c.getContext('webgl'); if (!g) return null; const e = g.getExtension('WEBGL_debug_renderer_info'); return e ? g.getParameter(e.UNMASKED_RENDERER_WEBGL) : g.getParameter(g.RENDERER); } catch { return null; } }), 5000) : null;
    const slow = fps !== null && fps < 20;
    const soft = /swiftshader|llvmpipe|software/i.test(String(renderer ?? ''));
    const softWhy = `this browser renders at ${fps} fps on "${renderer}": a software renderer makes any game look stuck, so nothing here is judged (run on a computer with a GPU)`;
    if (only.has('first')) {
      const j = judgeFirst(ready);
      row(`first ${device}`, slow || soft ? 'BLOCKED' : j.verdict, { why: slow || soft ? softWhy : j.why, note: j.note, ...ready, heartbeatFrom: beatFrom, fps, renderer, shots: firstShots.map((x) => rel(out, x.file)), frames: firstShots.map((x) => ({ at: x.at, state: x.state })) });
      // First move, a row of its own: it needs a live round and a body that is the player's, and says so when it
      // had neither. A press into a wall, a press on the results screen and a press as a spectator are not "the
      // controls do not answer".
      const HOLD_MS = 3000;
      if (slow || soft) row(`move ${device}`, 'BLOCKED', { why: softWhy });
      else if (!probe) row(`move ${device}`, 'BLOCKED', { why: 'the game has no port probe (exposePort), so the script cannot see its body: first-move latency was not measured (the controls row needs the probe too)' });
      else if (probe.view === 'board') row(`move ${device}`, 'N/A', { why: 'a board game has no body to move: the controls row checks that a press is applied' });
      else {
        const tryMove = async (dir) => {
          const before = await readState(h);
          const t0 = await frameNow(h);
          const from = await selfAt(h, t0 - 500);
          const started = Date.now();
          const press = hold(h, dir, 1600, probe);
          let ms = null;
          while (Date.now() - started < HOLD_MS) {
            const now = await selfAt(h, t0);
            if (from && now && Number.isFinite(from[1]) && Number.isFinite(now[1]) && Math.hypot(now[1] - from[1], now[2] - from[2]) > (probe.size || 10) * 0.5) { ms = Date.now() - started; break; }
            await sleep(40);
          }
          await press;
          actions.moves++;
          return { dir, moved: ms !== null, ms, before, after: await readState(h) };
        };
        const waited = await waitActive(h, 25_000);
        const attempts = [];
        if (waited.ok) {
          attempts.push(await tryMove('right'));
          // Nothing moved: a wall on that side looks exactly like this. Press the other way before saying anything.
          if (!attempts[0].moved) { await waitActive(h, 10_000); attempts.push(await tryMove(oppositeOf('right'))); }
        }
        const j = judgeMove(attempts, { waited, holdMs: HOLD_MS });
        const png = await screenshot(h);
        row(`move ${device}`, j.verdict, { why: j.why, controlMs: j.controlMs, waitedForPlayMs: waited.ms, attempts: j.attempts, shot: rel(out, await save('move', png)) });
      }
    }
    if (paintPng) await save('first-paint', paintPng);
    if (gamePng) await save('first-frame', gamePng);
    // The look, while playing like a person.
    if (only.has('look')) {
      const lookShots = [];
      const cost = [];
      const playing = playFor(h, seconds, probe, { profile, actions });
      const every = Math.max(2500, (seconds * 1000) / 6);
      let prev = null;
      for (let t = 0; t < seconds * 1000 - 500; t += every) {
        await sleep(t === 0 ? 1500 : every);
        const st = await readState(h);
        const png = await screenshot(h);
        if (!png) continue;
        const img = decode(png, 480);
        const ps = stats(img);
        const mv = prev ? motion(prev, img) : null;
        prev = img;
        if (st.render) cost.push(st.render);
        lookShots.push({ file: rel(out, await save(`look-${lookShots.length + 1}`, png)), motion: mv, state: describeState(st), screen: contextOf(st).kind, ...ps });
      }
      const { presses } = await playing;
      const black = lookShots.filter((x) => x.black || x.flat).length;
      const dead = lookShots.filter((x) => x.flatBlackShare > 0.05).length;
      const plain = lookShots.filter((x) => x.flatDarkShare > 0.3).length;
      const still = lookShots.filter((x) => x.motion !== null && x.motion < 0.002).length;
      const avg = (k) => +(lookShots.reduce((a, x) => a + x[k], 0) / Math.max(1, lookShots.length)).toFixed(3);
      const notes = [];
      if (avg('mean') < 40) notes.push(`dark: mean brightness ${avg('mean')} of 255`);
      if (avg('sd') < 22) notes.push(`low contrast: luma spread ${avg('sd')}`);
      if (avg('edges') < 0.03) notes.push(`little visible detail (${(avg('edges') * 100).toFixed(1)}% edge pixels): flat shapes read as unfinished`);
      if (plain >= 2) notes.push(`over 30% of the screen is one flat dark colour in ${plain} shots: an empty backdrop reads as unfinished; give the floor texture, light or props`);
      if (still >= 2) notes.push(`${still} pairs of shots barely changed while playing: is anything moving?`);
      const offPlay = lookShots.filter((x) => !['live', 'unknown'].includes(x.screen));
      const why = black ? `${black} of ${lookShots.length} shots were black or one colour while playing` : dead >= 2 ? `${dead} shots have pure-black holes over 5% of the screen: nothing drew there (a failed shader, a world that never loaded, the clear colour)` : undefined;
      // Measured runtime cost, when the game exposes its renderer's counters; "not exposed" is said, never a zero.
      const rc = renderCost(cost);
      row(`look ${device}`, slow || soft ? 'BLOCKED' : why ? 'FAIL' : notes.length ? 'WARN' : 'PASS', {
        why: why ?? (notes.length ? notes.join('; ') : undefined), presses, mean: avg('mean'), contrast: avg('sd'), saturation: avg('saturation'), edges: avg('edges'),
        qualifier: offPlay.length ? `${offPlay.length} of ${lookShots.length} shots were not active play (${[...new Set(offPlay.map((x) => x.screen))].join(', ')}): each shot carries its state` : undefined,
        render: rc ? `draw calls median ${rc.drawCalls?.median ?? '?'} (max ${rc.drawCalls?.max ?? '?'}), triangles median ${rc.triangles?.median ?? '?'} (max ${rc.triangles?.max ?? '?'}) over ${rc.samples} samples` : 'not exposed by the game (exposePort extra: drawCalls, triangles): runtime scene cost was not measured here',
        renderCost: rc, shots: lookShots,
      });
    }
    // UI cover: the world hidden, the page's background black and then white; what stays is the UI.
    if (only.has('ui') && h.vp.isMobile) {
      const world = probe?.world ?? null;
      const paint = async (bg) => {
        await T(h.page.evaluate((c) => { let s = document.getElementById('__pt_ui'); if (!s) { s = document.createElement('style'); s.id = '__pt_ui'; document.head.appendChild(s); } s.textContent = c ? `html,body,iframe.game{background:${c}!important}` : ''; }, bg), 5000);
        await inFrame(h, ([c, sel]) => { let s = document.getElementById('__pt_ui'); if (!s) { s = document.createElement('style'); s.id = '__pt_ui'; (document.head || document.documentElement).appendChild(s); } s.textContent = c ? `canvas,video${sel ? `,${sel}` : ''}{visibility:hidden!important} html,body{background:${c}!important;background-image:none!important}` : ''; }, [bg, world]);
        await sleep(350);
      };
      await playFor(h, 1.2, probe, { profile, actions });
      // Self-check (PLAYTEST_UI_SELFCHECK=1): a known opaque panel, a third of the width square, in the middle of the game.
      if (process.env.PLAYTEST_UI_SELFCHECK) await inFrame(h, () => { const d = document.createElement('div'); d.style.cssText = 'position:fixed;left:33.4%;top:40%;width:33.2vw;height:33.2vw;background:#345;z-index:99999'; document.body.appendChild(d); });
      // Active play is what the 12% bar is about: wait for a live round and a free body. If the wait runs out, the
      // screen that IS there (a results card, a spectator view) is measured and labelled, and not judged by that bar.
      const waited = await waitActive(h, 25_000);
      let pair = null;
      for (let k = 0; k < 3; k++) {
        // The thumb stays down on the stick for both frames: a held stick is part of what a player sees in play.
        const [fx, fy] = probe?.thumb ?? [0.24, 0.74];
        const tx = Math.round(h.vp.width * fx); const ty = Math.round(h.vp.height * fy);
        let thumb = 'up';
        try { await h.page.touchscreen.touchStart(tx, ty); for (let m = 1; m <= 6; m++) { await h.page.touchscreen.touchMove(tx + 12 * m, ty); await sleep(16); } thumb = 'held'; } catch { /* a closed page */ }
        const before = await readState(h);
        // The page's own controls and the game's DOM HUD, in the same pixels, at the same moment (lib/judge.mjs shellOverlaps).
        const layout = await T(h.page.evaluate(() => { const r = window.__shell?.rects; return r ? { width: r.width, height: r.height, rects: r.rects } : null; }), 5000);
        const hud = await inFrame(h, HUD_ELEMENTS, world);
        await paint('#000'); const a = await screenshot(h);
        await paint('#fff'); const b = await screenshot(h);
        const after = await readState(h);
        await paint(null);
        try { await h.page.touchscreen.touchEnd(); } catch { /* */ }
        pair = { a, b, before, after, thumb, tries: k + 1, layout, hud };
        // A round that ended between the two frames makes them two different screens: take the pair again.
        if (!a || !b || !pairMismatch(before, after)) break;
        await waitActive(h, 15_000);
      }
      if (pair.a && pair.b) {
        // Both frames are kept, with the state each was taken in: the pair can be checked by eye.
        await save('ui-on-black', pair.a); await save('ui-on-white', pair.b);
        const kept = { shot: `${device}-ui-on-black.png`, shotWhite: `${device}-ui-on-white.png`, stateBlack: describeState(pair.before), stateWhite: describeState(pair.after), thumb: pair.thumb, pairTries: pair.tries, waitedForPlayMs: waited.ms };
        const mismatch = pairMismatch(pair.before, pair.after);
        const cov = mismatch ? null : uiCover(decode(pair.a, 390), decode(pair.b, 390));
        const overlaps = shellOverlaps(pair.layout, pair.hud);
        const j = judgeUi(cov ?? { cover: 0, opaque: 0, centreOpaque: 0 }, { before: pair.before, after: pair.after, thumb: pair.thumb, overlaps });
        row(`ui ${device}`, j.verdict, { why: j.why, ...(cov ?? {}), screen: j.screen, state: j.state, qualifier: j.qualifier, note: UI_CAVEAT, ...kept, hudUnderShell: overlaps.known ? overlaps.overlaps.length : 'not checked', shellOverlaps: overlaps.overlaps });
      } else row(`ui ${device}`, 'BLOCKED', { why: 'no screenshot' });
    }
    return { errors: h.errors, bad: h.bad, probe: Boolean(probe), actions };
  } finally { await close(h); }
}

/** What the game really sounds like: its own Web Audio output copied off the graph for `seconds` of play. */
async function soundSession(base, game, out, seconds, gameJson) {
  const h = await launch('desk', `${base}/${game}/play`, { tap: true });
  const profile = actionProfile(gameJson, 'desk');
  try {
    const frame = await waitFrame(h, 30_000);
    if (!frame) { row('sound', 'BLOCKED', { why: 'the game frame never opened' }); return; }
    await sleep(2500);
    const probe = await probeInfo(h);
    const pre = await inFrame(h, () => window.__homieTap?.clock?.() ?? null);
    // The first gesture: a click in the middle of the game, then keys.
    const gestureWall = Date.now();
    await h.page.mouse.click(Math.round(h.vp.width / 2), Math.round(h.vp.height / 2)).catch(() => {});
    let runningMs = null;
    for (let k = 0; k < 30; k++) { const c = await inFrame(h, () => window.__homieTap?.clock?.() ?? null); if (c?.state === 'running') { runningMs = Date.now() - gestureWall; break; } await sleep(100); }
    await inFrame(h, () => window.__homieTap?.start?.());
    const gestureClock = await inFrame(h, () => window.__homieTap?.clock?.() ?? null);
    const runs = [];
    const presses = [];
    const pull = async () => { const r = await inFrame(h, () => window.__homieTap?.take?.() ?? []); if (Array.isArray(r)) runs.push(...r); };
    const until = Date.now() + seconds * 1000;
    const keys = probe?.keys ?? { up: 'ArrowUp', down: 'ArrowDown', left: 'ArrowLeft', right: 'ArrowRight' };
    const seq = ['right', 'up', 'left', 'down'];
    let i = 0;
    while (Date.now() < until) {
      const c = await inFrame(h, () => window.__homieTap?.clock?.() ?? null);
      // Every fifth press is the game's primary action (game.json playtest.primary, else the space bar), taken with
      // the round's state: a game that ignores the action between rounds owes it no sound there.
      if (i % 5 === 4) {
        const st = await readState(h);
        if (await pressPrimary(h, profile)) { if (c?.now !== undefined) presses.push({ ctx: c.now, action: true, play: activePlay(st), state: describeState(st) }); }
        await sleep(90);
      } else {
        const k = keys[seq[i % 4]];
        if (c?.now !== undefined) presses.push({ ctx: c.now, action: false });
        await h.page.keyboard.down(k).catch(() => {}); await sleep(700); await h.page.keyboard.up(k).catch(() => {});
      }
      i++;
      await sleep(250);
      if (i % 3 === 0) await pull();
    }
    await pull();
    const post = await inFrame(h, () => ({ clock: window.__homieTap?.clock?.() ?? null, sound: window.__homieSound?.stats ?? null }));
    const ctxs = post?.clock?.ctxs ?? 0;
    const rate = post?.clock?.rate ?? 48000;
    if (!ctxs) { row('sound', 'FAIL', { why: 'the game made no Web Audio context: it is silent (or plays only <audio> elements, which this capture cannot hear)', runningMs }); return; }
    if (!runs.length) { row('sound', 'FAIL', { why: `the game's audio never ran after the first click and keys (context ${post?.clock?.state ?? '?'})`, runningMs }); return; }
    // Lay the captured runs onto one timeline by their context frames; gaps stay silent.
    const f0 = Math.min(...runs.map((r) => r.f));
    const f1 = Math.max(...runs.map((r) => r.f + r.frames));
    const L = new Float32Array(f1 - f0); const R = new Float32Array(f1 - f0);
    for (const r of runs) {
      const b = Buffer.from(r.b64, 'base64');
      const s = new Int16Array(b.buffer, b.byteOffset, b.byteLength / 2);
      for (let k = 0; k < r.frames; k++) { L[r.f - f0 + k] = s[2 * k] / 32768; R[r.f - f0 + k] = s[2 * k + 1] / 32768; }
    }
    const wav = join(out, 'sound-capture.wav');
    writeFileSync(wav, wavBytes({ L, R }, { bits: 16, rate }));
    const m = measure(wav, { rate: 48000 });
    let sheet = null; try { sheet = rel(out, sheetPng(wav, join(out, 'sound-capture.png'))); } catch { /* */ }
    // Did presses answer with sound? An onset (10 ms energy 6 dB over the 300 ms before) within 250 ms of a press.
    const env = [];
    const w = Math.round(rate * 0.01);
    for (let k = 0; k + w <= L.length; k += w) { let e = 0; for (let j = k; j < k + w; j++) e += L[j] * L[j] + R[j] * R[j]; env.push(e / w); }
    const t0 = f0 / rate;
    // Movement holds owe no sound; an action (a button, the space bar) does.
    const judge = (list) => {
      let yes = 0; let n = 0;
      for (const p of list) {
        const at = Math.round((p.ctx - t0) / 0.01);
        if (at < 30 || at + 25 >= env.length) continue;
        n++;
        const before = env.slice(at - 30, at).reduce((a, v) => a + v, 0) / 30;
        const after = Math.max(...env.slice(at, at + 25));
        if (after > before * 4 && after > 1e-7) yes++;
      }
      return { yes, n };
    };
    // Only action presses made in active play (or where the game does not say) are owed a sound; the ones that
    // landed on a results screen or a dead body are counted apart, with the state they landed in.
    const act = judge(presses.filter((p) => p.action && p.play !== false));
    const offPlay = presses.filter((p) => p.action && p.play === false);
    const mov = judge(presses.filter((p) => !p.action));
    const answered = act.yes; const judged = act.n;
    const firstLoud = (() => { const floor = 10 ** (-50 / 20); for (let k = 0; k < L.length; k++) if (Math.abs(L[k]) > floor || Math.abs(R[k]) > floor) return k; return -1; })();
    const firstSoundMs = firstLoud < 0 || !gestureClock ? null : Math.max(0, Math.round(((f0 + firstLoud) / rate - (gestureClock.now ?? 0)) * 1000));
    const warn = warnings(m, 'capture');
    const answerShare = judged ? +(answered / judged).toFixed(2) : null;
    if (answerShare !== null && answerShare < 0.5) warn.push(`only ${answered} of ${judged} presses of ${profile.how} made in active play were followed by a sound within 250 ms: give every action a sound`);
    if (m.loudness.lufs !== null && m.loudness.lufs < -32) warn.push(`very quiet: ${m.loudness.lufs} LUFS while playing (a phone at half volume will hear almost nothing)`);
    if (m.silentShare > 0.5) warn.push(`${Math.round(m.silentShare * 100)}% of the time was silent while someone played: no music bed?`);
    const verdict = m.samplePeakDb !== null && m.samplePeakDb < -60 ? 'FAIL' : m.clippedSamples > 0 ? 'FAIL' : warn.length ? 'WARN' : 'PASS';
    row('sound', verdict, {
      why: verdict === 'FAIL' ? (m.clippedSamples > 0 ? `${m.clippedSamples} clipped samples: it distorts` : 'the capture is silent after the first click') : warn.join('; ') || undefined,
      contexts: ctxs, before: pre?.state ?? null, runningAfterGestureMs: runningMs, firstSoundMs, seconds: m.seconds, actionPresses: judged, answered, answerShare, action: profile.how, actionDeclared: profile.declared, actionPressesOutsidePlay: offPlay.length,
      qualifier: [offPlay.length ? `${offPlay.length} action press(es) landed outside active play (${[...new Set(offPlay.map((p) => p.state))].slice(0, 2).join(' | ')}) and were not judged for sound` : null, !judged ? 'no action press was judged for sound in this capture' : null, profile.declared ? null : 'the action pressed was a guess (game.json declares no playtest.primary): a game whose action is another input was not asked for its sound'].filter(Boolean).join('; ') || undefined,
      movesWithSound: `${mov.yes} of ${mov.n}`,
      loudness: m.loudness, samplePeakDb: m.samplePeakDb, clippedSamples: m.clippedSamples, silentShare: m.silentShare, gaps: m.gaps.slice(0, 5), bands: m.bands, under300Share: m.under300Share, onsetsPerSecond: m.onsetsPerSecond,
      soundJs: post?.sound ? { plays: post.sound.plays?.length ?? 0, names: [...new Set((post.sound.plays ?? []).map((p) => p.name))], missing: post.sound.missing, music: post.sound.music, errors: post.sound.errors } : null,
      capture: rel(out, wav), sheet,
    });
  } finally { await close(h); }
}

/** A round with one person playing hard (a computer) and one doing nothing (a phone), both strangers in the public room. */
async function playSession(base, game, out, roundSeconds, gameJson) {
  const profile = actionProfile(gameJson, 'desk');
  const actions = newActions(profile);
  const active = await launch('desk', `${base}/${game}/play`);
  const idle = await launch('phone', `${base}/${game}/play`);
  try {
    const seat = async (h) => { const until = Date.now() + 45_000; while (Date.now() < until) { const s = await shell(h); if (s?.room && s.seat !== null && s.seat !== undefined && s.role) return s; await sleep(300); } return null; };
    const [sa, si] = await Promise.all([seat(active), seat(idle)]);
    if (!sa || !si) { row('play', 'FAIL', { why: 'a browser never got a seat in 45 s' }); return; }
    if (sa.room !== si.room) { row('play', 'FAIL', { why: `the two browsers landed in different rooms (${sa.room}, ${si.room}): two strangers who press Play must meet` }); return; }
    const since = Date.now();
    // Only a round that STARTS after both are seated counts: a newcomer takes a bot's place mid-round and inherits
    // its body and score, so the round already running says nothing about how these two played.
    let at0 = null;
    for (let k = 0; k < 40 && !at0; k++) { at0 = (await shell(active))?.round ?? null; if (!at0) await sleep(250); }
    const minN = (at0?.n ?? 0) + 1;
    const probe = await probeInfo(active);
    const scores = [];
    let lastLive = null; let liveSeenAt = null; let overAt = null; let result = null;
    const budget = (roundSeconds * 2 + 60) * 1000;
    const playing = (async () => { while (!result && Date.now() - since < budget) await playFor(active, 4, probe, { profile, actions }); })();
    while (!result && Date.now() - since < budget) {
      const [a, b] = await Promise.all([shell(active), shell(idle)]);
      const pa = await inFrame(active, () => window.__homiePort?.info?.().score ?? null);
      const pi = await inFrame(idle, () => window.__homiePort?.info?.().score ?? null);
      if ((a?.round?.n ?? 0) >= minN) scores.push({ t: Math.round((Date.now() - since) / 1000), active: pa, idle: pi });
      const r = a?.round;
      if (r?.phase === 'live' && r.n >= minN) { if (!lastLive || lastLive.n !== r.n) liveSeenAt = Date.now(); lastLive = r; }
      const hit = (a?.results ?? []).find((x) => x.at > since && x.n >= minN && x.results.some((row0) => row0.seat === sa.seat) && x.results.some((row0) => row0.seat === si.seat));
      if (hit) { result = hit; overAt = Date.now(); }
      void b;
      await sleep(1000);
    }
    await playing.catch(() => {});
    const shot = await screenshot(active);
    if (shot) writeFileSync(join(out, 'play-round-over.png'), shot);
    if (!result) { row('play', 'FAIL', { why: `no round finished with both of them in its results within ${Math.round(budget / 1000)} s`, scores: scores.slice(-10) }); return; }
    const rowsR = result.results;
    const me = rowsR.find((x) => x.seat === sa.seat); const them = rowsR.find((x) => x.seat === si.seat);
    const planned = lastLive ? Math.round((lastLive.endsAt - lastLive.startedAt) / 1000) : null;
    const watched = liveSeenAt && overAt ? Math.round((overAt - liveSeenAt) / 1000) : null;
    let changes = 0; let lead = null;
    for (const s of scores) { if (s.active === null || s.idle === null) continue; const l = s.active > s.idle ? 'active' : s.idle > s.active ? 'idle' : lead; if (lead && l !== lead) changes++; lead = l; }
    // What the scores of this one round say, and no more (lib/judge.mjs judgeScores): a cooperative game's shared
    // total is not a ranking, a bot's win is a measured gap, and a conclusion says which inputs the script used.
    const j = judgeScores({ me, them, rows: rowsR, scoring: gameJson?.scoring ?? null, planned, roundSeconds: gameJson?.roundSeconds ?? null, actions });
    const notes = j.notes;
    row('play', notes.length ? 'WARN' : 'PASS', {
      why: notes.join('; ') || undefined, room: sa.room, round: result.n, plannedSeconds: planned, watchedSeconds: watched, players: rowsR.length, bots: rowsR.filter((x) => x.bot).length,
      scoring: j.scoring, comparison: j.comparison, actions: describeActions(actions), primaryDeclared: profile.declared, primaryPresses: actions.primary.pressed, primaryMissed: actions.primary.missed, directionHolds: actions.moves,
      active: me ? { place: me.place, score: me.score } : null, idle: them ? { place: them.place, score: them.score } : null, leadChanges: changes,
      results: rowsR.map((x) => ({ place: x.place, score: x.score, bot: x.bot, who: x.seat === sa.seat ? 'the active player' : x.seat === si.seat ? 'the idle player' : x.bot ? 'a bot' : 'another person' })),
      scoreSamples: scores.filter((_, k) => k % 5 === 0).slice(0, 40), shot: 'play-round-over.png',
    });
  } finally { await close(active); await close(idle); }
}

/** The studio's own checks, run as the creator would: the owner tests (port check) and the two-stranger round. */
function studioCheck(root, args, name, timeoutMs) {
  return new Promise((ok) => {
    const bin = join(root, 'node_modules', '.bin', 'homie-studio');
    if (!existsSync(bin)) { row(name, 'BLOCKED', { why: '@homie-rocks/studio is not installed in this studio (npm install)' }); ok(null); return; }
    const child = spawn(bin, [...args, '--json'], { cwd: root, stdio: ['ignore', 'pipe', 'pipe'] });
    let outText = '';
    child.stdout.on('data', (d) => { outText += d; });
    child.stderr.on('data', () => {});
    // Bounded all the way down: asked to stop at the timeout, killed 5 s later, and answered 5 s after that even if
    // `close` never comes (a helper that inherited the child's pipes keeps them open after the child is gone).
    let settled = false; let timedOut = false;
    const timers = [];
    const done = () => {
      if (settled) return; settled = true;
      for (const t of timers) clearTimeout(t);
      let j = null; try { j = JSON.parse(outText); } catch { /* */ }
      if (!j) { row(name, 'BLOCKED', { why: timedOut ? `homie-studio ${args.join(' ')} did not finish in ${Math.round(timeoutMs / 1000)} s and was stopped: nothing was measured` : `homie-studio ${args.join(' ')} gave no result`, instrument: timedOut }); ok(null); return; }
      ok(j);
    };
    timers.push(setTimeout(() => { timedOut = true; try { child.kill('SIGTERM'); } catch { /* */ } }, timeoutMs));
    timers.push(setTimeout(() => { try { child.kill('SIGKILL'); } catch { /* */ } }, timeoutMs + 5000));
    timers.push(setTimeout(() => { try { child.stdout.destroy(); child.stderr.destroy(); } catch { /* */ } done(); }, timeoutMs + 10_000));
    child.on('close', done);
  });
}

/* ---------------------------------------------------------------- run */

async function run() {
  const game = pos[1];
  const url = String(flags.get('url') ?? '').replace(/\/+$/, '');
  if (!game || !/^https?:\/\//.test(url)) throw new Error('usage: run <game> --url <site> (http://127.0.0.1:8787 from npm run dev, or the live site)');
  const root = findStudio();
  const only = new Set(String(flags.get('only') ?? 'first,look,ui,sound,play,controls,round').split(',').map((s) => s.trim()));
  const seconds = Math.max(8, Math.min(120, Number(flags.get('seconds') ?? 20)));
  const stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\..*/, '');
  const out = resolve(String(flags.get('out') ?? (root ? join(root, '.playtest', game, stamp) : join(process.cwd(), '.playtest', game, stamp))));
  // First of all, before a folder is made or the disk is looked at: can this process reach the site at all? A name Node cannot resolve (while a browser can) is a network preflight
  // failure of the instrument, BLOCKED, never a game failure (lib/preflight.mjs).
  const pre = await preflight(`${url}/${game}/play`);
  if (!pre.ok) { const e = new Error(pre.why); e.verdict = pre.verdict; e.kind = pre.kind; throw e; }
  mkdirSync(out, { recursive: true });
  if (root) {
    const gi = join(root, '.gitignore');
    const text = existsSync(gi) ? readFileSync(gi, 'utf8') : '';
    if (!/^\.playtest\/?$/m.test(text)) appendFileSync(gi, `${text.endsWith('\n') || !text ? '' : '\n'}.playtest/\n`);
  }
  try { const f = statfsSync(out); if ((f.bavail * f.bsize) / 1e9 < 10) throw new Error('under 10 GB free on this disk: free some space before a playtest'); } catch (e) { if (/GB free/.test(e.message)) throw e; }
  EXE = chromePath();
  puppeteer = loadPuppeteer(root);
  if (!EXE || !puppeteer) throw new Error(!EXE ? 'no Chrome found (set CHROME_PATH to a Chrome or Chromium)' : 'puppeteer-core is not installed (it comes with @homie-rocks/studio: npm install in the studio)');
  const gameJson = root ? readJson(experienceJson(experienceDir(root, game)), {}) : {};
  const isApp = root && experienceJson(experienceDir(root, game)).endsWith('/app.json');
  const started = Date.now();
  const errors = [];
  const bad = [];
  let probed = false;
  const instrumentFaults = [];
  for (const device of ['desk', 'phone', 'phone-landscape']) {
    if (!['first', 'look', 'ui'].some((k) => only.has(k))) break;
    log(`… ${device}: first seconds, the look while playing, the UI`);
    let r;
    try { r = await deviceSession(device, url, game, out, seconds, only, gameJson); } catch (e) {
      // The instrument could not read its own pictures (a stuck or missing decoder). The browser is closed already
      // (deviceSession's finally); every row of this device that was not written yet is BLOCKED, never failed, and
      // the run ends non-zero because it did not measure what it was asked to.
      if (!e?.blocked) throw e;
      instrumentFaults.push(`${device}: ${e.message}`);
      for (const kind of ['first', 'move', 'look', 'ui']) {
        const wanted = kind === 'move' ? only.has('first') : kind === 'ui' ? only.has('ui') && DEVICES[device].isMobile : only.has(kind);
        if (wanted && !rows.some((x) => x.name === `${kind} ${device}`)) row(`${kind} ${device}`, 'BLOCKED', { why: e.message, instrument: true });
      }
      continue;
    }
    errors.push(...r.errors.map((e) => `${device}: ${e}`)); bad.push(...r.bad.map((e) => `${device}: ${e}`)); probed ||= r.probe;
  }
  if (only.has('sound')) { log('… sound: the game\'s own audio while someone plays'); await soundSession(url, game, out, Math.max(15, seconds), gameJson); }
  if (only.has('play') && !isApp) { log('… play: a round with one person playing hard and one doing nothing'); await playSession(url, game, out, Number(gameJson.roundSeconds ?? 90), gameJson); }
  if (only.has('controls') && root && !isApp) {
    log('… controls: the owner tests (homie-studio port check)');
    const pc = await studioCheck(root, ['port', 'check', game, '--url', url, '--only', 'owner-desk,owner-phone,owner-iphone,ui-cover,life,tv,audio,errors', '--shots', join(out, 'port-check')], 'controls', 9 * 60_000);
    if (pc) {
      const failed = (pc.rows ?? []).filter((x) => x.ok === false);
      // A skipped row (no WebKit for the iPhone, say) was not tested: that is never a pass.
      const skipped = (pc.rows ?? []).filter((x) => x.ok === null || x.ok === undefined);
      const verdict = failed.length ? 'FAIL' : !pc.rows?.length ? 'BLOCKED' : skipped.length ? 'WARN' : 'PASS';
      const why = failed.length ? failed.map((x) => `${x.name}: ${x.why ?? 'failed'}`).join('; ') : !pc.rows?.length ? pc.why : skipped.length ? `not tested: ${skipped.map((x) => `${x.name} (${x.why ?? 'skipped'})`).join('; ')}` : undefined;
      // What a row did not check rides with it (the big screen's join QR on a loopback preview is not applicable, and
      // a pass there says nothing about the live QR).
      const unchecked = (pc.rows ?? []).filter((x) => x.qrNote).map((x) => `${x.name}: ${x.qrNote}`);
      row('controls', verdict, { why, qualifier: unchecked.join('; ') || undefined, rows: (pc.rows ?? []).map((x) => ({ name: x.name, ok: x.ok, why: x.why ?? null, ...(x.qrNote ? { note: x.qrNote } : {}) })), receipt: 'port-check/receipt.json' });
    }
  }
  if ((only.has('round') || (isApp && only.has('play'))) && root) {
    log(isApp ? '… sync: a wall and two phones share an action and reconnect' : '… round: two fresh browsers press Play and finish a round together (homie-studio check)');
    const ck = await studioCheck(root, ['check', game, '--url', url, '--shots', join(out, 'round')], 'round', 5 * 60_000);
    if (ck) {
      // A round that finished is not a connection that held: reconnects are said beside completion, and a round
      // completed across a reconnect is WARN (measured, worth a look), not a quiet pass.
      const conn = connectionNote(ck.connection);
      if (isApp) row('sync', ck.ok ? 'PASS' : 'FAIL', { why: ck.why, room: ck.room, surfaces: ck.surfaces, reconnect: ck.reconnect });
      else row('round', !ck.ok ? 'FAIL' : conn.uninterrupted === false ? 'WARN' : 'PASS', { why: !ck.ok ? ck.why : conn.uninterrupted === false ? conn.note : undefined, completed: Boolean(ck.ok), reconnects: conn.reconnects ?? 'not reported', uninterrupted: conn.uninterrupted ?? 'unknown', connection: conn.note, readiness: ck.readiness ?? null, room: ck.room, seats: ck.seats, round: ck.round ? { n: ck.round.n, humans: ck.round.humans, bots: ck.round.bots } : null, seconds: ck.totalMs ? Math.round(ck.totalMs / 1000) : null });
    }
  }
  const uniq = (xs) => [...new Set(xs)].slice(0, 30);
  row('errors', errors.length ? 'FAIL' : bad.length ? 'WARN' : 'PASS', { why: errors.length ? `${errors.length} uncaught error(s) or console errors, first: ${errors[0]}` : bad.length ? `${bad.length} failed request(s), first: ${bad[0]}` : undefined, errors: uniq(errors), requests: uniq(bad) });
  const report = { v: 1, game, url, at: new Date().toISOString(), seconds: Math.round((Date.now() - started) / 1000), probe: probed, rows, weak: weakest(rows) };
  writeFileSync(join(out, 'report.json'), `${JSON.stringify(report, null, 1)}\n`);
  writeFileSync(join(out, 'REPORT.md'), reportMd(report, readJson(join(out, 'review.json'), null)));
  await sheets(out, root);
  return { ok: !rows.some((r) => r.verdict === 'FAIL') && !instrumentFaults.length, ...(instrumentFaults.length ? { blocked: instrumentFaults } : {}), command: 'run', game, out, report: join(out, 'REPORT.md'), seconds: report.seconds, rows: rows.map((r) => `${r.verdict.padEnd(7)} ${r.name}${r.why ? `: ${r.why}` : ''}`), weak: report.weak, review: reviewLine(null).line, next: `node playtest.mjs review ${relative(process.cwd(), out) || '.'} (then hand REVIEW.md to a fresh reviewer)` };
}

/** Contact sheets of a run's pictures, labelled (drawn in Chrome, so no font setup). */
async function sheets(out, root) {
  const { htmlToPng } = await import('../../video/scripts/lib/browser.mjs');
  const rep = readJson(join(out, 'report.json'), { rows: [] });
  const groups = [];
  for (const device of ['desk', 'phone', 'phone-landscape']) {
    const first = rep.rows.find((r) => r.name === `first ${device}`);
    const look = rep.rows.find((r) => r.name === `look ${device}`);
    const cells = [...(first?.shots ?? []).map((f, i) => ({ file: f, label: `${device} · ${[1, 3, 5, 10][i]} s after opening` })), ...(look?.shots ?? []).map((s, i) => ({ file: s.file, label: `${device} · playing, shot ${i + 1} · brightness ${s.mean} · contrast ${s.sd} · detail ${(s.edges * 100).toFixed(1)}%` }))];
    if (cells.length) groups.push({ name: device, cells, wide: DEVICES[device].width > DEVICES[device].height });
  }
  for (const g of groups) {
    const cols = g.wide ? 3 : 5;
    const cw = g.wide ? 560 : 300;
    const ch = g.wide ? Math.round(cw * (g.name === 'desk' ? 800 / 1280 : 390 / 844)) : Math.round(cw * 844 / 390);
    const imgs = g.cells.filter((c) => c.file && existsSync(join(out, c.file))).map((c) => `<figure><img src="data:image/png;base64,${readFileSync(join(out, c.file)).toString('base64')}"><figcaption>${c.label.replace(/</g, '&lt;')}</figcaption></figure>`);
    if (!imgs.length) continue;
    const rowsN = Math.ceil(imgs.length / cols);
    const W = cols * (cw + 12) + 12; const H = rowsN * (ch + 40) + 12;
    const html = `<!doctype html><meta charset="utf-8"><style>body{margin:0;background:#111;color:#ddd;font:13px/1.3 system-ui,sans-serif}main{display:grid;grid-template-columns:repeat(${cols},${cw}px);gap:12px;padding:12px}figure{margin:0}img{width:${cw}px;height:${ch}px;object-fit:contain;background:#000;display:block}figcaption{padding-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}</style><main>${imgs.join('')}</main>`;
    try { await htmlToPng(root, html, join(out, `sheet-${g.name}.png`), { width: W, height: H }); } catch (e) { log(`sheet ${g.name}: ${e.message}`); }
  }
}

/* ---------------------------------------------------------------- review */

/** The pictures a review is given, in the order a reviewer should open them. */
const REVIEW_PICTURES = ['sheet-desk.png', 'sheet-phone.png', 'sheet-phone-landscape.png', 'desk-first-frame.png', 'phone-ui-on-black.png', 'phone-ui-on-white.png', 'phone-landscape-ui-on-black.png', 'phone-landscape-ui-on-white.png', 'sound-capture.png', 'play-round-over.png'];

/**
 * THE REVIEW STEP, AND WHAT IT HANDS OVER. A blind review means giving a game's screenshots to a reviewer outside
 * this session, and a host that reviews what an agent sends (an approval reviewer in front of a second coding agent's
 * command line, say) may refuse that transfer; Homie cannot and must not get round it. So this command says, before
 * anything is sent, exactly which files go and to whom, as ONE question a person answers once per report folder
 * (review-request.json keeps the same list, so an approval can be tied to that exact payload and destination). When
 * the answer is no, or the host refuses anyway, `review --local` is the fallback that sends nothing, and `reviewed`
 * records which review ran, or that none did: a missing review is BLOCKED in the report, never a quiet pass.
 */
function review() {
  const out = resolve(String(pos[1] ?? ''));
  const rep = readJson(join(out, 'report.json'), null);
  if (!rep) throw new Error('usage: review <run folder> (the folder a run wrote, with report.json)');
  const brief = readFileSync(join(HERE, '..', 'references', 'REVIEWER.md'), 'utf8');
  const pics = REVIEW_PICTURES.filter((f) => existsSync(join(out, f)));
  const numbers = rep.rows.map((r) => `- ${r.verdict} ${r.name}${r.why ? `: ${r.why}` : ''}`).join('\n');
  const text = brief
    .replaceAll('{{GAME}}', rep.game)
    .replaceAll('{{URL}}', `${rep.url}/${rep.game}/play`)
    .replaceAll('{{FOLDER}}', out)
    .replaceAll('{{PICTURES}}', pics.map((p) => `- \`${join(out, p)}\``).join('\n') || '- (none: the run made no pictures)')
    .replaceAll('{{NUMBERS}}', numbers);
  if (flags.has('local')) {
    // The fallback that sends nothing anywhere: this session scores the same pictures with the same rubric. It is
    // the builder grading its own build, and every line of it says so.
    const rubric = text.slice(text.indexOf('## Look at these yourself'));
    const local = [`# Local review (NOT independent): ${rep.game}`, '',
      'This is the fallback for when the blind review could not run: the reviewer could not be reached, or the person or the host did not approve handing the screenshots to one. Nothing leaves this session.',
      '',
      'You are the session that made this game, so this is NOT a blind review and must never be reported as one. Score only what the pictures and the numbers below show, not what you know the code does or meant to do. Where you catch yourself explaining a weakness away, write the weakness down instead.',
      '',
      `The game: ${rep.url}/${rep.game}/play. The run folder: \`${out}\`.`, '',
      rubric.trimEnd(), '',
      'Add `"review": "local"` to the JSON, save it as VERDICT.json in the run folder, then record it:', '',
      `    node playtest.mjs reviewed ${relative(process.cwd(), out) || '.'} --kind local --reason "<why no independent review ran>" --score <overall>`, '',
      'When you report to the person, say in the first sentence that this was a local review and not an independent one, and offer the independent review again.', ''].join('\n');
    writeFileSync(join(out, 'REVIEW-LOCAL.md'), local);
    return { ok: true, command: 'review', kind: 'local', brief: join(out, 'REVIEW-LOCAL.md'), pictures: pics.length, sends: 'nothing: the pictures stay in this session', how: 'Read REVIEW-LOCAL.md and every picture it lists yourself, score with its rubric, save VERDICT.json (with "review": "local"), then run `reviewed <run folder> --kind local --reason "<why>" --score <n>`. This is NOT independent: say so wherever you report it.' };
  }
  writeFileSync(join(out, 'REVIEW.md'), text);
  // Exactly what the review step hands over: the brief, the numbers and these pictures, all from this one folder.
  const files = ['REVIEW.md', 'report.json', ...pics].filter((f) => existsSync(join(out, f))).map((f) => ({ file: f, bytes: statSync(join(out, f)).size }));
  const to = typeof flags.get('to') === 'string' ? flags.get('to') : 'a fresh reviewer that has not seen the code (say which: a subagent inside this session, or an external command such as a second coding agent)';
  const question = [
    `Approve the blind review of "${rep.game}" from the report folder ${out}?`,
    `It hands ${files.length} files from that folder to ${to}:`,
    ...files.map((f) => `  - ${f.file} (${Math.max(1, Math.round(f.bytes / 1024))} KB)`),
    'They are screenshots of the game (private while it is unreleased), the instruments\' numbers and the review brief. The reviewer is told the folder and may open the other screenshots in it; nothing outside that folder is sent, and the reviewer also plays the game at the address in the brief.',
    'One yes covers this report folder and this reviewer. Another folder or another reviewer is a new question.',
    'Say "local" instead and nothing leaves this session: the session scores the same pictures itself with the same rubric, and the report says that review was not independent.',
  ].join('\n');
  writeFileSync(join(out, 'review-request.json'), `${JSON.stringify({ v: 1, game: rep.game, folder: out, destination: to, files, question, at: new Date().toISOString() }, null, 1)}\n`);
  return {
    ok: true, command: 'review', brief: join(out, 'REVIEW.md'), pictures: pics.length,
    sends: files.map((f) => f.file), folder: out, destination: to,
    approval: question,
    how: 'FIRST ask the person the approval question above, once, word for word (it names every file and the destination; pass --to "<the reviewer>" to name it). After a yes: give the WHOLE TEXT of REVIEW.md, as it is, to a FRESH reviewer that has not seen the code, the plan or your summary (Claude Code: the Agent tool, with the file\'s full contents as the prompt, not its path or a summary of it; Codex: a new session). Add nothing about the code or what you changed. It plays the game itself and saves VERDICT.json in the run folder; then run `reviewed <run folder> --kind independent --by "<the reviewer>"`.',
    ifRefused: 'If the person says no, or the host refuses the transfer (an approval reviewer rejecting the command is the host\'s decision: do not retry it in other words, and do not send the pictures another way): run `review <run folder> --local` for a review that sends nothing, or record that none ran with `reviewed <run folder> --kind none --reason "<why>"`. Either way the report then says which review this run had.',
  };
}

/** `reviewed <run folder> --kind ...`: write review.json and put the review's line into REPORT.md. */
function reviewed() {
  const out = resolve(String(pos[1] ?? ''));
  const rep = readJson(join(out, 'report.json'), null);
  const kind = String(flags.get('kind') ?? '');
  if (!rep || !REVIEW_KINDS.includes(kind)) throw new Error(`usage: reviewed <run folder> --kind ${REVIEW_KINDS.join('|')} [--by "<who>"] [--reason "<why>"] [--score <0-100>]`);
  const text = (k) => (typeof flags.get(k) === 'string' ? flags.get(k).slice(0, 300) : null);
  if (kind !== 'independent' && !text('reason')) throw new Error(`--reason "<why>" is needed with --kind ${kind}: a report that says no independent review ran must say why`);
  const verdict = readJson(join(out, 'VERDICT.json'), null);
  if (kind !== 'none' && !verdict) throw new Error(`no VERDICT.json in ${out}: a review that ran saves its verdict there first (for a review that did not run: --kind none --reason "<why>")`);
  const score = Number.isFinite(Number(flags.get('score'))) && flags.get('score') !== true ? Number(flags.get('score')) : Number.isFinite(verdict?.score) ? verdict.score : null;
  const record = { v: 1, kind, by: text('by'), reason: text('reason'), score: kind === 'none' ? null : score, at: new Date().toISOString() };
  writeFileSync(join(out, 'review.json'), `${JSON.stringify(record, null, 1)}\n`);
  writeFileSync(join(out, 'REPORT.md'), reportMd(rep, record));
  const line = reviewLine(record);
  return { ok: true, command: 'reviewed', kind, review: line.line, report: join(out, 'REPORT.md') };
}

function showReport() {
  const out = resolve(String(pos[1] ?? ''));
  const rep = readJson(join(out, 'report.json'), null);
  if (!rep) throw new Error('usage: report <run folder>');
  // The review is part of what a report says: which kind ran, or BLOCKED when none did.
  const line = reviewLine(readJson(join(out, 'review.json'), null));
  return { ok: !rep.rows.some((r) => r.verdict === 'FAIL'), command: 'report', game: rep.game, rows: rep.rows.map((r) => `${r.verdict.padEnd(7)} ${r.name}${r.why ? `: ${r.why}` : ''}`), weak: rep.weak, review: line.line, reviewKind: line.kind, report: join(out, 'REPORT.md') };
}

const rel = (out, f) => (f ? relative(out, f) : null);

async function main() {
  const cmd = pos[0];
  if (!cmd || cmd === 'help' || flags.has('help')) {
    const head = readFileSync(fileURLToPath(import.meta.url), 'utf8').split('*/')[0];
    return { ok: true, command: 'help', usage: head.replace(/^#!.*\n\/\*\*?/, '').replace(/^ \* ?/gm, '').trim() };
  }
  if (cmd === 'run') return run();
  if (cmd === 'review') return review();
  if (cmd === 'reviewed') return reviewed();
  if (cmd === 'report') return showReport();
  return { ok: false, command: cmd, why: `unknown command "${cmd}" (playtest.mjs help)` };
}

const print = (o) => {
  if (JSON_OUT) { process.stdout.write(`${JSON.stringify(o, null, 2)}\n`); return; }
  if (o.ok === false && o.why) { process.stdout.write(`playtest: ${o.why}\n`); return; }
  const lines = [];
  for (const [k, v] of Object.entries(o)) if (k !== 'ok' && k !== 'command') lines.push(Array.isArray(v) ? `${k}:\n  ${v.join('\n  ')}` : `${k}: ${typeof v === 'object' ? JSON.stringify(v) : v}`);
  process.stdout.write(`${lines.join('\n')}\n`);
};

try {
  const r = await main();
  if (r) { print(r); if (r.ok === false) process.exitCode = 1; }
} catch (error) {
  const msg = error instanceof Error ? error.message : String(error);
  // A preflight that could not reach the site measured nothing: BLOCKED, said as such, and still a non-zero exit.
  const blocked = error?.verdict === 'BLOCKED';
  print({ ok: false, ...(blocked ? { verdict: 'BLOCKED', kind: error.kind } : {}), why: /ERR_CONNECTION_REFUSED|ECONNREFUSED/.test(msg) && !error?.verdict ? `the site stopped answering during the playtest (${msg}): is the dev server still running? Restart it as a background task (a rebuild while \`npm run dev\` runs can kill it) and run again` : `${blocked ? 'BLOCKED ' : ''}${msg}` });
  process.exitCode = 1;
}
// The report is written and printed: close whatever browser is still open (bounded), then leave. A controller once
// stayed alive after its report with every browser and decoder it owned already gone; whatever handle held it was
// never isolated, so the end does not wait for the event loop to empty (lib/exit.mjs). The exit code set above stays.
await finish({ cleanup: async () => { for (const h of [...open]) await close(h); } });
