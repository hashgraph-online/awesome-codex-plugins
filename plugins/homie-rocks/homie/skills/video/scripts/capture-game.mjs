#!/usr/bin/env node
/**
 * capture-game.mjs — real gameplay from a studio's own game, for a trailer: the
 * game's big-screen view (/<id>/tv: a spectator in a live public room) recorded
 * off a headless GPU Chrome, picture and the game's own
 * sound on one clock.
 * A server rules room needs a player to keep ticking; use --view play when
 * filming an otherwise empty room. A spectator alone does not wake it.
 *
 *   node capture-game.mjs --url <site> --game <id> --seconds 60 --out <dir>
 *        [--view tv|play] [--fps 30] [--width 1920] [--height 1080] [--scale 1] [--settle 4] [--min-free-gb 10]
 *
 * Size and speed: --width/--height is the film's size, --fps its frame rate. --scale renders the page smaller
 * (0.25 to 1: 0.67 is a 1280x720 page for a 1920x1080 film) and scales the frames up to the film's size when it
 * encodes. A heavy game paints far more frames at a smaller size (measured: 8 frames a second at 1080p, 39 at
 * 720p), and a frame the page did not paint in time is a held frame. The result says the page's own frame rate;
 * when it is well under --fps it names a --scale that would paint enough.
 *
 * Picture: the compositor's own frame stream (CDP Page.startScreencast), every
 *          frame kept with the time Chrome presented it, then laid onto a constant
 *          frame rate (a frame the page did not paint in time is held, and counted).
 * Sound:   tap.js copies what the game sends to its speaker (WebAudio), stamped
 *          with the audio clock, which is fitted to the page clock; the browser is
 *          muted, so nothing plays out loud on this computer.
 * Out:     <dir>/capture.mp4 (H.264 + AAC when the game made sound), <dir>/capture.json
 *          (what was captured, frame rates, held frames, the room, the sound). The raw
 *          frames are deleted once encoded.
 *
 * It never presses anything in the game: what it records is the game as it plays.
 */
import { mkdirSync, readFileSync, rmSync, statfsSync, writeFileSync } from 'node:fs';
import { cpus, loadavg } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { launch } from './lib/browser.mjs';
import { TapReader, constantRate, encodeMp4, fitAudio, startScreencast, writeConcat } from './lib/frames.mjs';
import { findStudio } from '../../music/scripts/lib/studio.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const opt = (n, d = null) => { const i = argv.indexOf(`--${n}`); return i >= 0 && i + 1 < argv.length ? argv[i + 1] : d; };
const URL_ = String(opt('url', '')).replace(/\/+$/, '');
const GAME = opt('game');
const SECONDS = Number(opt('seconds', 60));
const OUT = resolve(String(opt('out', '')));
const VIEW = opt('view', 'tv');
const FPS = Number(opt('fps', 30));
const W = Number(opt('width', 1920)); const H = Number(opt('height', 1080));
const SCALE = Number(opt('scale', 1));
// The page's own size: even numbers (the encoder's rule), scaled up to W x H when the film is made.
const RW = Math.max(2, Math.round((W * SCALE) / 2) * 2); const RH = Math.max(2, Math.round((H * SCALE) / 2) * 2);
const SETTLE = Number(opt('settle', 4));
const MIN_FREE_GB = Number(opt('min-free-gb', 10));
const fail = (m) => { process.stderr.write(`capture-game: ${m}\n`); process.exit(2); };
if (!/^https?:\/\//.test(URL_)) fail('--url <the studio site: http://127.0.0.1:8787 from npm run dev, or the live site>');
if (!/^[a-z0-9][a-z0-9-]{0,39}$/.test(String(GAME ?? ''))) fail('--game <id>');
if (!(SECONDS >= 3 && SECONDS <= 600)) fail('--seconds 3..600');
if (!(SCALE >= 0.25 && SCALE <= 1)) fail('--scale 0.25..1 (the page renders at that part of --width x --height, and the film is scaled up to it)');
if (!(FPS >= 1 && FPS <= 60)) fail('--fps 1..60');
if (!opt('out')) fail('--out <folder> (the video job\'s work/capture folder)');
const freeGB = () => { try { const f = statfsSync(OUT); return (f.bavail * f.bsize) / 1e9; } catch { return 99; } };
mkdirSync(OUT, { recursive: true });
if (freeGB() < MIN_FREE_GB + 2) fail(`only ${freeGB().toFixed(1)} GB free; a capture needs room (stopping below ${MIN_FREE_GB} GB)`);

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const log = (k, v = {}) => process.stderr.write(`${JSON.stringify({ t: +(process.uptime()).toFixed(1), k, ...v })}\n`);
const TAP = readFileSync(join(HERE, 'tap.js'), 'utf8');
const root = findStudio(OUT) ?? findStudio();

const frameDir = join(OUT, 'frames');
rmSync(frameDir, { recursive: true, force: true });
mkdirSync(frameDir, { recursive: true });
let frames = []; // { file, t } t = presentation time (epoch seconds)
const pcmFile = join(OUT, 'game-audio.s16le');
const tap = new TapReader(pcmFile);
const report = { ran: new Date().toISOString(), url: `${URL_}/${GAME}/${VIEW}`, seconds: SECONDS, fps: FPS, size: [W, H], ...(SCALE !== 1 ? { scale: SCALE, rendered: [RW, RH] } : {}), notes: [] };

const { browser, close, pid } = await launch(root, { width: RW, height: RH, extra: ['--autoplay-policy=no-user-gesture-required', '--mute-audio'] });
log('browser', { pid });
const stop = async (why) => { log('stop', { why }); tap.close(); await close(); process.exit(3); };
process.on('SIGINT', () => stop('SIGINT'));
process.on('SIGTERM', () => stop('SIGTERM'));

try {
  const page = await browser.newPage();
  await page.setViewport({ width: RW, height: RH, deviceScaleFactor: 1 });
  await page.evaluateOnNewDocument(TAP);
  const errors = [];
  page.on('pageerror', (e) => { if (errors.length < 30) errors.push(String(e.message).slice(0, 200)); });
  const target = VIEW === 'play' ? `${URL_}/${GAME}/play?hand=desk&name=Camera` : `${URL_}/${GAME}/tv`;
  await page.goto(target, { waitUntil: 'domcontentloaded', timeout: 60_000 });
  // The shell's own furniture (status chip, join card, results card) is not the game.
  await page.addStyleTag({ content: '[data-chip],[data-join],[data-screen],[data-results],[data-room-ui],[data-toast]{display:none!important} *{cursor:none!important}' });
  let game = null;
  for (let i = 0; i < 200 && !game; i++) {
    for (const f of page.frames()) if (/\/__game\//.test(f.url()) && !f.isDetached()) game = f;
    if (!game) await sleep(150);
  }
  if (!game) throw new Error('the game frame never loaded');
  // A static/older imported game need not publish a netplay probe. Its module
  // still finishes loading before complete; rules games publish their probe there.
  await game.waitForFunction(() => document.readyState === 'complete', { timeout: 30000 });
  report.room = await page.evaluate(() => window.__shell?.room ?? null).catch(() => null);
  const rulesBefore = await game.evaluate(() => { const p = window.__homieNet?.probe; return typeof p?.hosted === 'function' ? { hosted: p.hosted(), tick: p.tick?.() } : null; }).catch(() => null);
  await sleep(SETTLE * 1000);
  if (VIEW === 'tv' && rulesBefore?.hosted === 'server') {
    const tick = await game.evaluate(() => window.__homieNet?.probe?.tick?.()).catch(() => null);
    if (!(tick > rulesBefore.tick)) throw new Error('The server room is paused: a TV is not a participant. Keep a real player open in this same room, or capture with --view play, then record again.');
  }
  await page.keyboard.press('Shift').catch(() => {}); // a first gesture, for games that start their sound on one
  const tapStart = await game.evaluate(() => window.__homieTap?.start?.() ?? null).catch(() => null);
  report.tap = tapStart;
  log('ready', { room: report.room, tap: tapStart });

  const cast = await startScreencast(page, { dir: frameDir, width: RW, height: RH });
  frames = cast.frames;
  const until = Date.now() + SECONDS * 1000 + 600;
  let lastLog = 0;
  while (Date.now() < until) {
    try { await tap.poll(game); } catch (error) { report.notes.push(`poll: ${String(error.message).slice(0, 120)}`); }
    if (Date.now() - lastLog > 10_000) { lastLog = Date.now(); log('recording', { frames: frames.length, audioS: tap.rate ? +(tap.frames / tap.rate).toFixed(1) : 0, freeGB: +freeGB().toFixed(1) }); }
    if (freeGB() < MIN_FREE_GB) { report.notes.push('stopped early: disk low'); break; }
    await sleep(250);
  }
  await cast.stop();
  await sleep(300);
  report.errors = errors;
} catch (error) {
  report.failed = String(error.stack ?? error);
} finally {
  tap.close();
  await close();
}

if (report.failed || frames.length < 10) {
  writeFileSync(join(OUT, 'capture.json'), JSON.stringify({ ...report, frames: frames.length }, null, 1));
  rmSync(frameDir, { recursive: true, force: true });
  fail(report.failed ? `capture failed: ${report.failed.split('\n')[0]}` : `the page painted only ${frames.length} frames`);
}

/* ---- picture onto a constant frame rate: output frame k shows the newest frame presented by t0 + k/fps (lib/frames.mjs) */
const cfr = constantRate(frames, FPS);
const { t0, total, list, held, distinct } = cfr;
const concat = writeConcat(join(OUT, 'frames.txt'), list, FPS);

/* ---- sound onto the same clock: fit epoch(ms) = a + b * contextTime from the output timestamps */
const audio = fitAudio(tap, { t0, total, fps: FPS, out: join(OUT, 'game-audio.raw') });
if (audio && !audio.peakDb) audio.note = 'the game made no sound while it was recorded';
rmSync(pcmFile, { force: true });

const mp4 = join(OUT, 'capture.mp4');
const enc = encodeMp4({ concat, audio, fps: FPS, width: W, height: H, seconds: total / FPS, out: mp4 });
rmSync(frameDir, { recursive: true, force: true });
rmSync(concat, { force: true });
if (audio) delete audio.raw;
if (!enc.ok) fail(`encode failed: ${enc.why}`);
const spanS = cfr.frames.at(-1).t - t0;
const sourceFps = +(frames.length / spanS).toFixed(1);
// Too few frames from the page: a smaller page paints more (the frame count grows about with the pixels saved).
let advice = null;
if (sourceFps < FPS * 0.75) {
  // Below half size a film is too soft to scale up, and a page that slow is a busy computer as much as a heavy game.
  const want = Math.max(0.5, Math.min(1, +(SCALE * Math.sqrt(Math.max(0.05, sourceFps / FPS))).toFixed(2)));
  const load = +(loadavg()[0] / Math.max(1, cpus().length)).toFixed(1);
  advice = `the page painted ${sourceFps} frames a second for a ${FPS} fps film (${held} frames held)${load > 1.5 ? `, on a busy computer (load ${load} a core)` : ''}: `
    + (want < SCALE ? `capture again with --scale ${want} (a ${Math.round(W * want)}x${Math.round(H * want)} page, scaled up)${load > 1.5 ? ' when it is quieter' : ''}, or a lower --fps` : `capture with a lower --fps${load > 1.5 ? ', or when the computer is quieter' : ''}`);
}
const result = {
  ...report, mode: 'live', file: 'capture.mp4', seconds: +(total / FPS).toFixed(3), outputFrames: total, sourceFrames: frames.length,
  sourceFps, distinctFramesUsed: distinct, heldFrames: held, audio, ...(advice ? { advice } : {}),
  honesty: 'Recorded from the game in a live public room, with no scripted gameplay or drawn overlay. Any bots shown are the game\'s own bots.',
};
writeFileSync(join(OUT, 'capture.json'), `${JSON.stringify(result, null, 1)}\n`);
process.stdout.write(`${JSON.stringify({ ok: true, file: mp4, seconds: result.seconds, sourceFps: result.sourceFps, heldFrames: held, ...(advice ? { advice } : {}), audio: audio ? { seconds: audio.seconds, peakDb: audio.peakDb, covered: audio.covered } : null })}\n`);
process.exit(0);
