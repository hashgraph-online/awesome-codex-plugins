/*
 * look.js — the look of the film. A starting point, meant to be changed for every
 * video: a two-ink print (paper, ink, and an accent) where the generated clip is the
 * motion underneath and the drawing is what you see, plus kinetic lyric type.
 *
 * drawBase(ctx, img, env): the picture. env: { t, songT, W, H, mode, shot, palette, beatPhase, words, rand }.
 * drawType(ctx, env): the words. Big and present for shots marked "big", quiet for "quiet", none for "none".
 */
const SCREEN = 9; // halftone cell, px
let small = null;

export function drawBase(ctx, img, env) {
  const { W, H, palette, shot, rand } = env;
  ctx.globalCompositeOperation = 'source-over';
  ctx.fillStyle = palette.paper;
  ctx.fillRect(0, 0, W, H);
  if (!img) return;
  // Cover the frame, keeping the subject (shot.focus, 0..1) in view; a small push on each beat.
  const bump = 1 + 0.018 * Math.max(0, 1 - env.beatPhase * 4);
  const s = Math.max(W / img.width, H / img.height) * bump;
  const [fx, fy] = shot.focus ?? [0.5, 0.5];
  const dw = img.width * s; const dh = img.height * s;
  const dx = Math.min(0, Math.max(W - dw, W / 2 - fx * dw));
  const dy = Math.min(0, Math.max(H - dh, H / 2 - fy * dh));
  // The hand: the plate shifts a little, twelve times a second (the "boil").
  const tick = Math.floor(env.t * 12);
  const jx = (rand(tick) - 0.5) * 3; const jy = (rand(tick + 99) - 0.5) * 3;
  // Line work: the base in grey, multiplied onto the paper.
  ctx.save();
  ctx.filter = 'grayscale(1) contrast(1.6) brightness(1.08)';
  ctx.globalAlpha = 0.5;
  ctx.globalCompositeOperation = 'multiply';
  ctx.drawImage(img, dx + jx, dy + jy, dw, dh);
  ctx.restore();
  // Ink: halftone dots sized by how dark each cell is.
  const cw = Math.ceil(W / SCREEN); const chh = Math.ceil(H / SCREEN);
  if (!small || small.width !== cw) { small = document.createElement('canvas'); small.width = cw; small.height = chh; }
  const sc = small.getContext('2d', { willReadFrequently: true });
  sc.filter = 'contrast(1.3)';
  sc.drawImage(img, dx / SCREEN, dy / SCREEN, dw / SCREEN, dh / SCREEN);
  const px = sc.getImageData(0, 0, cw, chh).data;
  // Two screens: the ink prints the dark, the accent prints warm light (red well above blue),
  // on a grid offset by half a cell and misregistered a little from the ink, like a second pass.
  const plate = (colour, amount, ox0, oy0) => {
    ctx.fillStyle = colour;
    ctx.beginPath();
    for (let y = 0; y < chh; y++) {
      for (let x = 0; x < cw; x++) {
        const r = amount(px, (y * cw + x) * 4) * SCREEN * 0.62;
        if (r < 0.6) continue;
        const cx = x * SCREEN + (y % 2) * SCREEN * 0.5 + ox0; const cy = y * SCREEN + SCREEN / 2 + oy0;
        ctx.moveTo(cx + r, cy);
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
      }
    }
    ctx.fill();
  };
  ctx.globalCompositeOperation = 'multiply';
  plate(palette.ink, (p, i) => 1 - (0.3 * p[i] + 0.59 * p[i + 1] + 0.11 * p[i + 2]) / 255, jx, jy);
  const mx = (rand(tick + 5) - 0.5) * 3 + SCREEN / 3; const my = (rand(tick + 17) - 0.5) * 3 + SCREEN / 3;
  plate(palette.accent, (p, i) => Math.max(0, Math.min(1, (p[i] - p[i + 2] - 40) / 140)), mx, my);
  ctx.globalCompositeOperation = 'source-over';
  // Paper tooth: fixed to the card, not to time.
  ctx.fillStyle = 'rgba(0,0,0,0.035)';
  for (let i = 0; i < 1400; i++) ctx.fillRect(rand(i) * W, rand(i + 7) * H, 1 + rand(i + 3) * 2, 1);
}

/** The line being sung at songT, and its words up to now. */
function lineAt(words, songT) {
  if (!words.length) return null;
  let i = words.findIndex((w) => w.s > songT);
  if (i < 0) i = words.length;
  const past = words.slice(0, i);
  if (!past.length) return null;
  const last = past[past.length - 1];
  if (songT - last.e > 1.2) return null;
  // A line: the words since the last pause of 0.45 s or more.
  let k = past.length - 1;
  while (k > 0 && past[k].s - past[k - 1].e < 0.45) k--;
  return past.slice(k);
}

export function drawType(ctx, env) {
  const { W, H, palette, shot, songT, words, font } = env;
  if (shot.type === 'none') return;
  const line = lineAt(words, songT);
  if (!line) return;
  const big = shot.type === 'big';
  const size = big ? (env.mode === 'v' ? 150 : 170) : (env.mode === 'v' ? 64 : 58);
  const left = shot.side !== 'right';
  const x0 = env.mode === 'v' ? W * 0.08 : (left ? W * 0.06 : W * 0.56);
  const maxW = env.mode === 'v' ? W * 0.84 : W * 0.38;
  ctx.save();
  ctx.font = font.replace('1px', `${size}px`);
  ctx.textBaseline = 'alphabetic';
  let x = x0; let y = env.mode === 'v' ? H * 0.2 : (big ? H * 0.28 : H * 0.8);
  for (const w of line) {
    const word = big ? w.w.toUpperCase() : w.w;
    const wWidth = ctx.measureText(`${word} `).width;
    if (x + wWidth > x0 + maxW && x > x0) { x = x0; y += size * 0.95; }
    const age = songT - w.s;
    const pop = big ? 1 + 0.35 * Math.max(0, 1 - age / 0.12) : 1;
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(pop, pop);
    // The newest word in the accent ink, the rest in ink, all knocked out of a paper box so they read over any picture.
    const newest = w === line[line.length - 1];
    if (big) { ctx.fillStyle = palette.paper; ctx.fillRect(-6, -size * 0.82, wWidth - size * 0.18, size * 0.98); }
    ctx.fillStyle = newest ? palette.accent : palette.ink;
    ctx.fillText(word, 0, 0);
    ctx.restore();
    x += wWidth;
  }
  ctx.restore();
}
