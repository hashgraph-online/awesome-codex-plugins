/*
 * film.js — every frame is a pure function of time: renderAt(t) draws the frame at
 * t seconds and returns it as a JPEG data URL, so `video.mjs film render` can shoot
 * it frame-exactly in a headless browser, and any frame can be re-rendered alone.
 *
 * Inputs (served from the video's folder):
 *   film/shots.json  the shot list on the song's bar grid (at, dur, base frames, where the subject is, the type)
 *   grid.json        the song's beats, bars and sung words (video.mjs grid)
 *   work/frames/<id>/f00001.jpg …  a generated clip's frames at 24 fps (video.mjs film frames)
 * The look itself is look.js: change it, not this file.
 */
import { drawBase, drawType } from './look.js';

const params = new URLSearchParams(location.search);
const MODE = params.get('mode') === 'v' ? 'v' : 'h';
const W = MODE === 'v' ? 1080 : 1920;
const H = MODE === 'v' ? 1920 : 1080;
const canvas = document.getElementById('c');
canvas.width = W; canvas.height = H;
const ctx = canvas.getContext('2d', { willReadFrequently: true });
let SHOTS = null; let GRID = null;
const cache = new Map();

function image(src) {
  if (cache.has(src)) return cache.get(src);
  const p = new Promise((ok) => { const i = new Image(); i.onload = () => ok(i); i.onerror = () => ok(null); i.src = src; });
  cache.set(src, p);
  if (cache.size > 96) cache.delete(cache.keys().next().value);
  return p;
}

export async function boot() {
  SHOTS = await (await fetch('./shots.json', { cache: 'no-store' })).json();
  GRID = await (await fetch('../grid.json', { cache: 'no-store' })).json().catch(() => ({ beats: [], words: [] }));
  await document.fonts?.ready;
}

/** Deterministic noise: the same t and seed always give the same number. */
export const rand = (seed) => { const x = Math.sin(seed * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };

window.renderAt = async (t) => {
  const shot = SHOTS.shots.find((s) => t >= s.at && t < s.at + s.dur) ?? SHOTS.shots[SHOTS.shots.length - 1];
  const local = t - shot.at + (shot.baseStart ?? 0);
  let img = null;
  if (shot.base) {
    const n = Math.max(1, Math.floor(local * 24 + 1e-6) + 1);
    img = await image(`../${shot.base}/f${String(n).padStart(5, '0')}.jpg`);
    for (let k = n - 1; !img && k >= 1 && k > n - 48; k--) img = await image(`../${shot.base}/f${String(k).padStart(5, '0')}.jpg`); // past the clip's end: hold its last frame
  }
  const songT = t + (SHOTS.songStart ?? 0);
  const beats = GRID.beats ?? [];
  let beatPhase = 1;
  for (let i = beats.length - 1; i >= 0; i--) if (beats[i] <= songT) { beatPhase = Math.min(1, (songT - beats[i]) / (GRID.beat || 0.5)); break; }
  const env = { t, songT, W, H, mode: MODE, shot, palette: SHOTS.palette, font: SHOTS.font, beatPhase, words: GRID.words ?? [], rand };
  drawBase(ctx, img, env);
  drawType(ctx, env);
  return canvas.toDataURL('image/jpeg', 0.92);
};
