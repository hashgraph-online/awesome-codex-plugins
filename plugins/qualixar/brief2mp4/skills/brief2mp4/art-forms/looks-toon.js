// brief2mp4 art forms: looks-toon.js, batch 3 (anime, cartoon and craft). MIT. Same rules as looks.js: every look is a
// pure function of time, no clock, all roughness from hash(). All characters here are generic shapes made for this file.
import { TAU, clamp, lerp, prog, easeOut, easeInOut, hash, frameOf, held, jit, blob, strokePart, circlePts, bg, FONT } from './looks.js';
import { rgba, mix, spline, bounds, poly, speckle } from './looks-painted.js';
import { closed, rot, leaf, lines, dots, scales, disc, ribbon, ellipseLine, halftone, scaleAbout, centroid } from './looks-folk.js';

const overshootK = (k) => 1 + 2.70158 * (k - 1) ** 3 + 1.70158 * (k - 1) ** 2;
const BLACK = '#000', WHITE = '#fff', OUT = '#16121c';
export const path = (g, pts, close = true) => { g.beginPath(); pts.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); if (close) g.closePath(); };
export const polyFill = (g, pts, col, line = 0, lw = 4) => { path(g, pts); g.fillStyle = col; g.fill(); if (line) { g.strokeStyle = line; g.lineWidth = lw; g.lineJoin = 'round'; g.stroke(); } };
export const ell = (g, x, y, rx, ry, col, line = 0, lw = 4, a = 0) => { g.beginPath(); g.ellipse(x, y, Math.max(0.01, rx), Math.max(0.01, ry), a, 0, TAU); g.fillStyle = col; g.fill(); if (line) { g.strokeStyle = line; g.lineWidth = lw; g.stroke(); } };
export const star = (x, y, ro, ri, n, a0 = 0, wob = 0, seed = 0) => Array.from({ length: n * 2 }, (_, i) => { const a = a0 + (i / (n * 2)) * TAU, r = (i % 2 ? ri : ro) * (1 + (wob ? (hash(i, seed) - 0.5) * wob : 0)); return [x + Math.cos(a) * r, y + Math.sin(a) * r]; });

// manga helpers: only black and white. A speed-line burst, a screentone, and a fighter drawn from local coordinates
const speedLines = (g, cx, cy, r0, r1, n, f, w = 2) => { g.fillStyle = BLACK; for (let i = 0; i < n; i++) { const a = (i / n) * TAU + jit(f, i, 0.02), a2 = a + 0.012 + hash(i, 2) * 0.012, r = r1 * (0.8 + hash(i, f % 4, 3) * 0.4), q = r0 * (0.8 + hash(i, 4) * 0.5); path(g, [[cx + Math.cos(a) * q, cy + Math.sin(a) * q], [cx + Math.cos(a) * r, cy + Math.sin(a) * r], [cx + Math.cos(a2) * r, cy + Math.sin(a2) * r]]); g.fill(); } };
const tone = (g, bb, pitch, val, ang = 0.78) => { g.fillStyle = BLACK; halftone(g, bb, pitch, ang, val); };
function fighter(g, x, y, s, dir, clothes, f) {
  g.save(); g.translate(x, y); g.scale(s * dir, s); g.lineJoin = 'round'; g.lineCap = 'round'; g.strokeStyle = BLACK;
  const limb = (pts, w) => { g.lineWidth = w + 6; g.strokeStyle = BLACK; path(g, pts, false); g.stroke(); g.lineWidth = w; g.strokeStyle = clothes === 'tone' ? WHITE : BLACK; path(g, pts, false); g.stroke(); };
  limb([[-8, -6], [-60, 20], [-92, 90]], 18); limb([[10, -6], [62, 28], [52, 92]], 18); limb([[-8, -68], [-44, -42], [-52, -16]], 14);
  polyFill(g, [[-24, -4], [24, -10], [32, -72], [-12, -82]], clothes === 'tone' ? WHITE : BLACK, BLACK, 4);
  if (clothes === 'tone') { g.save(); path(g, [[-24, -4], [24, -10], [32, -72], [-12, -82]]); g.clip(); tone(g, [-40, -90, 40, 0], 5, () => 0.6); g.restore(); } else { g.fillStyle = WHITE; g.fillRect(-10, -76, 5, 70); }
  g.lineWidth = 20; g.strokeStyle = BLACK; path(g, [[24, -66], [70, -76], [112, -80]], false); g.stroke(); g.lineWidth = 11; g.strokeStyle = clothes === 'tone' ? WHITE : BLACK; g.stroke();   // the punching arm
  disc(g, 120, -80, 17, WHITE); g.lineWidth = 5; g.strokeStyle = BLACK; g.beginPath(); g.arc(120, -80, 17, 0, TAU); g.stroke();
  disc(g, 22, -100, 21, WHITE); g.lineWidth = 4.5; g.stroke(); g.beginPath(); g.arc(22, -100, 21, 0, TAU); g.stroke();
  polyFill(g, [[0, -112], [8, -142], [20, -118], [32, -146], [40, -116], [54, -134], [48, -104], [38, -118], [10, -112]], BLACK);   // spiked hair
  g.lineWidth = 3.4; g.beginPath(); g.moveTo(24, -108); g.lineTo(42, -102); g.stroke(); disc(g, 34, -97, 3, BLACK); g.beginPath(); g.moveTo(26, -84); g.lineTo(40, -86); g.stroke();   // an angry brow, an eye, a gritted mouth
  g.restore();
}

export const shadeHex = (hex, k) => { const n = parseInt(hex.slice(1), 16); return `rgb(${Math.round(((n >> 16) & 255) * k)},${Math.round(((n >> 8) & 255) * k)},${Math.round((n & 255) * k)})`; };
const curlPts = (x, y, r, turns = 2, dir = 1) => Array.from({ length: 28 }, (_, i) => { const a = (i / 27) * turns * TAU * dir, rr = r * (1 - i / 34); return [x + Math.cos(a) * rr, y + Math.sin(a) * rr]; });
// an isometric brick world: x runs down to the right, y down to the left, z up
const ISO = { cx: 480, cy: 136, cw: 33, ch: 16.5, bh: 24 };
const iso = (x, y, z) => [ISO.cx + (x - y) * ISO.cw, ISO.cy + (x + y) * ISO.ch - z * ISO.bh];
function stud(g, x, y, z, col, r = 0.55) {
  const [sx, sy] = iso(x, y, z), rx = ISO.cw * r, ry = ISO.ch * r;
  ell(g, sx, sy, rx, ry, shadeHex(col, 0.8)); g.fillStyle = shadeHex(col, 0.85); g.fillRect(sx - rx, sy - 6, 2 * rx, 6); ell(g, sx, sy - 6, rx, ry, col, 'rgba(0,0,0,.25)', 1);
  g.strokeStyle = 'rgba(255,255,255,.6)'; g.lineWidth = 1.8; g.beginPath(); g.arc(sx, sy - 6, rx * 0.55, Math.PI * 1.05, Math.PI * 1.55); g.stroke();
}
function brick(g, gx, gy, gz, w, d, col) {
  const L = [iso(gx, gy + d, gz + 1), iso(gx + w, gy + d, gz + 1), iso(gx + w, gy + d, gz), iso(gx, gy + d, gz)], R = [iso(gx + w, gy, gz + 1), iso(gx + w, gy + d, gz + 1), iso(gx + w, gy + d, gz), iso(gx + w, gy, gz)], T = [iso(gx, gy, gz + 1), iso(gx + w, gy, gz + 1), iso(gx + w, gy + d, gz + 1), iso(gx, gy + d, gz + 1)];
  polyFill(g, L, shadeHex(col, 0.8), 'rgba(0,0,0,.35)', 1.2); polyFill(g, R, shadeHex(col, 0.6), 'rgba(0,0,0,.35)', 1.2); polyFill(g, T, col, 'rgba(0,0,0,.35)', 1.2);
  g.strokeStyle = 'rgba(255,255,255,.5)'; g.lineWidth = 2; path(g, [T[3], T[0], T[1]], false); g.stroke();
  for (let i = 0; i < w; i++) for (let j = 0; j < d; j++) stud(g, gx + i + 0.5, gy + j + 0.5, gz + 1, col);
}
// a puppet from Rajasthan: a big painted head, a bright costume, and arms and legs that swing on strings from a bar above
function puppet(g, x, headY, kind, ph, ts, barY) {
  const dx = Math.sin(ts * 2 + ph) * 16, hx = x + dx, a1 = Math.sin(ts * 3 + ph) * 0.7, a2 = Math.sin(ts * 3 + ph + 2) * 0.7, hand = (s, a) => [hx + s * (34 + Math.sin(a) * 34), headY + 46 + Math.cos(a) * 44], foot = (s, a) => [hx + s * 14 + Math.sin(a) * 26, headY + 176 - Math.abs(Math.cos(a)) * 8];
  g.strokeStyle = 'rgba(40,24,10,.75)'; g.lineWidth = 1.4; const targets = [[hx, headY - 30, x], hand(-1, a1).concat([x - 34]), hand(1, a2).concat([x + 34]), foot(-1, a2).concat([x - 18]), foot(1, a1).concat([x + 18])];
  targets.forEach(([tx, ty, ax]) => { g.beginPath(); g.moveTo(ax, barY + 8); g.lineTo(tx, ty); g.stroke(); });
  const skin = '#e0a070', trim = '#f5c542';
  if (kind === 'king') { for (const [s, a] of [[-1, a2], [1, a1]]) { const f = foot(s, a); polyFill(g, [[hx + s * 4, headY + 96], [hx + s * 22, headY + 96], [f[0] + s * 4, f[1]], [f[0] - 4, f[1]]], '#fff3d2', OUT, 2); polyFill(g, [[f[0] - 8, f[1]], [f[0] + s * 18, f[1] - 4], [f[0] + s * 20, f[1] + 7], [f[0] - 8, f[1] + 8]], '#c0392b', OUT, 2); } }
  else { const sw = Math.sin(ts * 3 + ph) * 12; polyFill(g, [[hx - 22, headY + 92], [hx + 22, headY + 92], [hx + 62 + sw, headY + 172], [hx - 62 + sw, headY + 172]], '#e8438a', OUT, 2); polyFill(g, [[hx - 44 + sw * 0.6, headY + 136], [hx + 44 + sw * 0.6, headY + 136], [hx + 62 + sw, headY + 172], [hx - 62 + sw, headY + 172]], '#f08a24', OUT, 2); g.fillStyle = trim; g.fillRect(hx - 63 + sw, headY + 166, 126, 6); for (let i = 0; i < 7; i++) disc(g, hx - 54 + sw + i * 18, headY + 150, 3, '#fff6d8'); }
  polyFill(g, [[hx - 30, headY + 40], [hx + 30, headY + 40], [hx + 26, headY + 98], [hx - 26, headY + 98]], kind === 'king' ? '#e8a21a' : '#2e9b4f', OUT, 2); g.fillStyle = kind === 'king' ? '#2e9b4f' : trim; g.fillRect(hx - 27, headY + 82, 54, 9);
  for (const [s, a] of [[-1, a1], [1, a2]]) { const h = hand(s, a); g.strokeStyle = OUT; g.lineWidth = 13; g.lineCap = 'round'; path(g, [[hx + s * 28, headY + 46], h], false); g.stroke(); g.strokeStyle = kind === 'king' ? '#e8a21a' : '#2e9b4f'; g.lineWidth = 8; g.stroke(); disc(g, h[0], h[1], 6, skin); }
  g.fillStyle = skin; g.fillRect(hx - 8, headY + 22, 16, 22); ell(g, hx, headY, 25, 30, skin, OUT, 2.4);
  for (const d of [-1, 1]) { ell(g, hx + d * 10, headY - 4, 8, 6, '#fff', OUT, 1.6); disc(g, hx + d * 10 + 1, headY - 4, 3, OUT); }
  g.strokeStyle = OUT; g.lineWidth = 3; path(g, [[hx - 18, headY - 12], [hx - 4, headY - 14]], false); g.stroke(); path(g, [[hx + 4, headY - 14], [hx + 18, headY - 12]], false); g.stroke(); disc(g, hx, headY - 14, 2.6, '#c0392b');
  if (kind === 'king') { g.lineWidth = 3.4; path(g, [[hx - 18, headY + 12], [hx - 8, headY + 8], [hx, headY + 11], [hx + 8, headY + 8], [hx + 18, headY + 12]], false); g.stroke(); ell(g, hx, headY - 34, 29, 18, '#d6342a', OUT, 2.4); ell(g, hx, headY - 46, 18, 22, '#d6342a', OUT, 2.4); g.fillStyle = trim; g.fillRect(hx - 28, headY - 32, 56, 7); disc(g, hx, headY - 28, 5, '#2e9b4f', OUT, 1.4); g.strokeStyle = '#f5c542'; g.lineWidth = 3; path(g, [[hx, headY - 64], [hx + 6, headY - 78]], false); g.stroke(); }
  else { ell(g, hx, headY + 12, 6, 3.4, '#c0392b'); path(g, [[hx - 34, headY - 20], [hx - 28, headY + 36], [hx + 28, headY + 36], [hx + 34, headY - 20], [hx, headY - 40]]); g.fillStyle = 'rgba(240,138,36,.92)'; g.fill(); g.strokeStyle = OUT; g.lineWidth = 2.4; g.stroke(); ell(g, hx, headY - 2, 20, 26, skin, OUT, 2); for (const d of [-1, 1]) { ell(g, hx + d * 9, headY - 4, 7, 5, '#fff', OUT, 1.4); disc(g, hx + d * 9 + 1, headY - 4, 2.8, OUT); } disc(g, hx + 1, headY - 12, 2.4, '#c0392b'); ell(g, hx, headY + 14, 6, 3, '#c0392b'); disc(g, hx + 5, headY + 6, 2.4, trim); g.strokeStyle = trim; g.lineWidth = 3; path(g, [[hx - 33, headY - 20], [hx, headY - 40], [hx + 33, headY - 20]], false); g.stroke(); }
}

// lace-cut paper: a ring of cut-out shapes (leaf, round, drop) round a centre; every hole is a closed polyline, scaled about its own middle so it can open
function laceRing(cx, cy, r0, len, wid, n, kind, a0 = 0, a1 = TAU, k = 1) {
  const out = []; for (let i = 0; i < n; i++) {
    const a = a0 + ((i + 0.5) / n) * (a1 - a0), x = cx + Math.cos(a) * r0, y = cy + Math.sin(a) * r0;
    const pts = kind === 'leaf' ? leaf(x, y, len, wid, a) : kind === 'drop' ? closed(rot([[0, 0], [0.5, -0.55], [1, 0], [0.5, 0.55]], x, y, a, len, wid * 1.3), 4).map(([px, py]) => [px, py]) : circlePts(cx + Math.cos(a) * (r0 + len / 2), cy + Math.sin(a) * (r0 + len / 2), wid, 14);
    out.push(scaleAbout(pts, Math.max(0.01, k)));
  }
  return out;
}
const holesPath = (outer, holes) => { const p = new Path2D(); const add = (pts) => pts.forEach(([x, y], i) => (i ? p.lineTo(x, y) : p.moveTo(x, y))); add(outer); p.closePath(); for (const h of holes) { add(h); p.closePath(); } return p; };

// one part of a cel-shaded figure: a flat base colour, one hard shadow shape on the left (away from the sun), a thin rim of sunset light on the right edge, and a fine dark outline
function celPart(g, pts, base, shade, rim = '#ffb36b', frac = 0.5) {
  const bb = bounds(pts); g.fillStyle = rim; path(g, pts); g.fill();
  g.save(); g.clip(poly(pts)); g.translate(-3, 0); g.fillStyle = base; path(g, pts); g.fill(); g.clip(poly(pts)); g.fillStyle = shade; g.fillRect(bb[0] - 10, bb[1] - 10, (bb[2] - bb[0]) * frac + 10, bb[3] - bb[1] + 20); g.restore();
  g.strokeStyle = '#0c0c24'; g.lineWidth = 2; g.lineJoin = 'round'; path(g, pts); g.stroke();
}
const taper = (pts, w0, w1) => ribbon(pts, w0, w1);   // a limb or a scarf tail: a band that narrows along its length

export const LOOKS = {
  /* ------------------------------------------------ anime, cartoon and craft ------------------------------------------------ */
  'retro-anime': { kind: '2d', fps: 8, draw(g, t, W, H) {
    // an 80s or 90s cel look: hard two-tone shading, banded sunset sky and a striped sun, a lit skyline, a figure from behind with hair and scarf in the wind, film grain and a soft bloom
    const ts = held(t, 8), f = frameOf(t, 8), sunY = lerp(440, 255, easeOut(prog(ts, 0, 3.2)));
    bg(g, W, H, '#ffe9a0');   // every pixel is repainted each frame, so the same time always gives the same picture
    ['#1d0b3d', '#3b1366', '#6a1b8a', '#b3237f', '#e8505b', '#ff8a3d', '#ffc15a', '#ffe9a0'].forEach((c, i) => { g.fillStyle = c; g.fillRect(0, i * 54, W, 56); });
    for (let i = 0; i < 26; i++) if ((f + i) % 5) { const x = hash(i, 1) * W, y = hash(i, 2) * 160, r = 1.5 + hash(i, 3) * 2; g.fillStyle = '#fff6d8'; g.fillRect(x - r, y - 0.5, 2 * r, 1); g.fillRect(x - 0.5, y - r, 1, 2 * r); }
    g.save(); g.beginPath(); g.arc(480, sunY, 140, 0, TAU); g.clip(); g.fillStyle = '#ffe27a'; g.fillRect(0, 0, W, H); g.fillStyle = '#ffb347'; g.fillRect(0, sunY + 12, W, H);   // the sun: a hard shadow tone below
    for (let k = 0; k < 7; k++) { g.fillStyle = '#ff8a3d'; g.fillRect(0, sunY + 24 + k * 19, W, 2.5 + k * 2.4); } g.restore();   // slits of sky cut across it
    const city = (base, minH, maxH, col, win, seed, step) => { for (let x = -10, i = 0; x < W; x += step * (0.7 + hash(i, seed) * 0.8), i++) { const w = 34 + hash(i, seed + 1) * 52, h = minH + hash(i, seed + 2) * (maxH - minH); g.fillStyle = col; g.fillRect(x, base - h, w, h + 60); if (hash(i, seed + 3) > 0.6) g.fillRect(x + w / 2 - 1, base - h - 26, 2, 26); if (win) for (let wy = base - h + 10; wy < base - 8; wy += 15) for (let wx = x + 7; wx < x + w - 8; wx += 12) if (hash(wx | 0, wy | 0, seed) > 0.5 && (f + wx) % 13 !== 0) { g.fillStyle = '#ffd35a'; g.fillRect(wx, wy, 5, 7); g.fillStyle = col; } } };
    city(430, 40, 120, '#4a1a6e', true, 11, 58); city(470, 28, 78, '#1b0b2e', true, 21, 70);
    g.fillStyle = '#0f0620'; g.fillRect(0, 462, W, 80); g.fillStyle = '#ff8a3d'; g.fillRect(0, 462, W, 3);   // the rooftop, with a rim of sunset light
    const bloom = g.createRadialGradient(480, sunY, 20, 480, sunY, 330); bloom.addColorStop(0, 'rgba(255,220,130,.5)'); bloom.addColorStop(1, 'rgba(255,160,90,0)'); g.save(); g.globalCompositeOperation = 'lighter'; g.fillStyle = bloom; g.fillRect(0, 0, W, H); g.restore();
    const sway = Math.sin(ts * 3.2) * 5, wave = (i, k) => Math.sin(ts * 4.5 + i * 0.8 + k) ;
    g.save(); g.translate(330, 472); g.scale(1.0, 1.0);   // a figure from behind in a jacket, standing on the roof edge: about 45% of the frame's height
    for (const [d, ax, ay] of [[-1, -22, -100], [1, 22, -100]]) { const kx = d * 24; celPart(g, [[ax - 15, ay], [ax + 15, ay], [kx + 12, -4], [kx - 12, -4]], '#2a3068', '#171b40', '#ff9a63', 0.55); celPart(g, [[kx - 16, -6], [kx + 16, -6], [kx + 22 * d, 8], [kx - 14 * d, 8]], '#12122e', '#0a0a1c', '#ff9a63', 0.5); }   // legs and shoes
    celPart(g, [[-50, -178], [50, -178], [42, -98], [46, -88], [-46, -88], [-42, -98]], '#2f4bb5', '#1d2d78', '#ffb36b', 0.52);   // the jacket, wider at the shoulders and flared at the hem
    celPart(g, [[-28, -178], [-18, -204], [18, -204], [28, -178], [0, -170]], '#27408f', '#17265a', '#ffb36b', 0.5);   // a raised collar
    celPart(g, taper([[-46, -172], [-62, -132], [-40, -98]], 12, 10), '#2f4bb5', '#1d2d78', '#ffb36b', 0.55); celPart(g, [[-48, -106], [-34, -92], [-30, -104], [-44, -114]], '#e2a381', '#a8704f', '#ffb36b', 0.5);   // the left arm, hand in a pocket
    celPart(g, taper([[48, -172], [66, -132], [60, -92]], 12, 10), '#2f4bb5', '#1d2d78', '#ffb36b', 0.3); disc(g, 60, -86, 9, '#e2a381');   // the right arm hanging, a fist
    celPart(g, [[-10, -204], [10, -204], [12, -190], [-12, -190]], '#e2a381', '#a8704f', '#ffb36b', 0.5);   // the neck
    for (let i = 0; i < 2; i++) {   // the scarf: a wrap at the collar and two tails streaming to the right
      const tail = Array.from({ length: 9 }, (_, j) => [14 + j * 21, -192 + i * 8 + wave(j, i * 1.4) * (4 + j * 1.6) + j * 1.5]);
      celPart(g, taper(tail, 9 - i * 2, 3), i ? '#c92b36' : '#e8363f', '#8f1c28', '#ffc08a', 0.0);
    }
    celPart(g, [[-30, -196], [30, -196], [28, -182], [-28, -182]], '#e8363f', '#a8202e', '#ffc08a', 0.5);
    const head = ellipseLine(0, -224, 29, 31); celPart(g, head, '#1b1b3a', '#0e0e24', '#ffb36b', 0.5);
    for (let i = 0; i < 8; i++) {   // spiky hair streaming to the right, each lock a tapering blade that waves on twos
      const a = -2.5 + i * 0.36, bx = Math.cos(a) * 24, by = -224 + Math.sin(a) * 26, len = 44 + (i % 3) * 14, w = wave(i, 0) * 11;
      celPart(g, [[bx - 9, by + 6], [bx + len * 0.6 + sway, by - 8 + w - i * 1.5], [bx + len + sway * 1.4, by + 6 + w * 1.4 + i * 2], [bx + 9, by + 13]], '#1b1b3a', '#0e0e24', '#ffb36b', 0.35 + (i % 2) * 0.1);
    }
    g.fillStyle = '#4a56a0'; g.beginPath(); g.arc(0, -224, 30, Math.PI * 1.22, Math.PI * 1.7); g.arc(0, -214, 22, Math.PI * 1.7, Math.PI * 1.22, true); g.fill();   // a hard highlight band on the hair
    celPart(g, [[22, -222], [30, -214], [26, -204], [20, -210]], '#e2a381', '#a8704f', '#ffb36b', 0.4);   // an ear
    g.restore();
    speckle(g, W, H, 40 + (f % 6), 55, [255, 240, 220]);
  } },
  manga: { kind: '2d', fps: 8, draw(g, t, W, H) {
    // black and white only: three inked panels, screentone dots, speed lines, and one dramatic moment, two fighters meeting in a burst
    const ts = held(t, 8), f = frameOf(t, 8); bg(g, W, H, WHITE);
    const panel = (x, y, w, h, start, body) => {
      const k = easeOut(prog(ts, start, 0.25)); if (k <= 0) return; g.save(); g.translate(x + w / 2, y + h / 2); g.scale(lerp(1.12, 1, k), lerp(1.12, 1, k)); g.globalAlpha = k; g.translate(-x - w / 2, -y - h / 2);
      g.beginPath(); g.rect(x, y, w, h); g.fillStyle = WHITE; g.fill(); g.save(); g.clip(); body(); g.restore(); g.strokeStyle = BLACK; g.lineWidth = 6; g.strokeRect(x, y, w, h); g.restore();
    };
    panel(24, 24, 912, 300, 0.1, () => {
      speedLines(g, 480, 120, 70, 760, 110, f);
      fighter(g, 330, 214, 1.25, 1, 'black', f); fighter(g, 630, 214, 1.25, -1, 'tone', f);
      if (prog(ts, 0.8, 0.2) > 0) { const b = star(480, 118, 84 + (f % 2) * 8, 44, 14, 0.1, 0.5, f % 3); polyFill(g, b, WHITE, BLACK, 6); polyFill(g, star(480, 118, 40, 20, 9, 0.4, 0.3, 7), BLACK); }
    });
    panel(24, 340, 448, 176, 1.4, () => {
      tone(g, [24, 340, 472, 516], 6, (x, y) => (y - 340) / 176 * 0.9 + 0.08);
      g.save(); g.beginPath(); g.ellipse(248, 430, 150, 62, -0.08, 0, TAU); g.clip(); g.fillStyle = WHITE; g.fillRect(90, 360, 320, 140); g.restore();   // a huge eye
      g.beginPath(); g.ellipse(248, 430, 150, 62, -0.08, 0, TAU); g.lineWidth = 8; g.strokeStyle = BLACK; g.stroke(); disc(g, 260, 432, 52, BLACK); disc(g, 240, 412, 15, WHITE); disc(g, 276, 450, 7, WHITE);
      polyFill(g, [[96, 410], [250, 352], [412, 396], [404, 372], [250, 330], [90, 386]], BLACK); for (let i = 0; i < 4; i++) { g.lineWidth = 2.4; g.strokeStyle = BLACK; path(g, [[150 + i * 36, 496], [160 + i * 36, 480]], false); g.stroke(); }
      polyFill(g, [[400, 392], [412, 420], [400, 432], [388, 420]], WHITE, BLACK, 3);
    });
    panel(488, 340, 448, 176, 2.2, () => {
      for (let i = 0; i < 28; i++) { const y = 340 + hash(i, 1) * 176, x0 = 488 + hash(i, f % 3, 2) * 120; g.fillStyle = BLACK; path(g, [[x0, y], [936, y - 1.5 - hash(i, 3) * 2], [936, y + 1.5 + hash(i, 3) * 2]]); g.fill(); }
      const cx = 740 + (f % 2) * 4; polyFill(g, star(cx, 430, 74, 40, 12, 0.2, 0.5, 5), WHITE, BLACK, 6); g.save(); g.translate(cx, 430); g.rotate(-0.5); disc(g, 0, -22, 14, WHITE); g.lineWidth = 4; g.strokeStyle = BLACK; g.beginPath(); g.arc(0, -22, 14, 0, TAU); g.stroke(); g.lineWidth = 12; g.beginPath(); g.moveTo(0, -8); g.lineTo(0, 24); g.moveTo(0, 0); g.lineTo(-24, 14); g.moveTo(0, 0); g.lineTo(24, -4); g.moveTo(0, 24); g.lineTo(-14, 52); g.moveTo(0, 24); g.lineTo(18, 50); g.stroke(); g.restore();   // a figure thrown clear
    });
  } },
  chibi: { kind: '2d', fps: 12, draw(g, t, W, H) {
    // two heads tall: a huge head, a tiny body, big shiny eyes, and a bouncing squash and stretch with a soft landing
    const ts = held(t, 12), u = (ts * 1.1) % 1, air = 4 * u * (1 - u), land = u < 0.14 ? (0.14 - u) / 0.14 : u > 0.86 ? (u - 0.86) / 0.14 : 0, sq = land * 0.28 - air * 0.07, blink = (ts % 2.4) < 0.12;
    const sky = g.createLinearGradient(0, 0, 0, H); sky.addColorStop(0, '#ffe3f1'); sky.addColorStop(1, '#e4ecff'); g.fillStyle = sky; g.fillRect(0, 0, W, H);
    for (let i = 0; i < 16; i++) { const x = hash(i, 1) * W, y = (hash(i, 2) * H + ts * 14 * (1 + hash(i, 3))) % H, r = 6 + hash(i, 4) * 9; polyFill(g, star(x, y, r, r * 0.45, 4, 0.78), i % 2 ? '#fff6b0' : '#ffffff'); }
    g.fillStyle = '#f2d4ea'; g.fillRect(0, 470, W, 70); ell(g, 480, 472, 120 - air * 40, 16 - air * 5, 'rgba(120,70,110,.3)');
    g.save(); g.translate(480, 470 - air * 90); g.scale(1 + sq, 1 - sq); g.lineJoin = 'round'; g.lineCap = 'round';
    const tail = Math.sin(ts * 7) * 0.22 * (0.3 + air); for (const d of [-1, 1]) { g.save(); g.translate(d * 120, -250); g.rotate(d * (0.35 + tail)); ell(g, 0, 70, 36, 92, '#ff8fb8', '#a8446f', 5); g.restore(); }
    for (const d of [-1, 1]) { ell(g, d * 18, -16, 20, 14 + air * 4, '#f6f0ff', '#6b4b8a', 5); ell(g, d * 24 + d * 24 * (air), -30, 11, 26, '#b69cff', '#6b4b8a', 5, d * (0.2 + air * 0.3)); }
    polyFill(g, [[-34, -58], [34, -58], [44, -112], [-44, -112]], '#b69cff', '#6b4b8a', 5); polyFill(g, [[-14, -112], [14, -112], [0, -92]], '#ff4f6d', '#6b4b8a', 3);
    for (const d of [-1, 1]) { g.lineWidth = 14; g.strokeStyle = '#6b4b8a'; path(g, [[d * 40, -100], [d * (66 + air * 20), -78 - air * 40]], false); g.stroke(); g.lineWidth = 8; g.strokeStyle = '#ffe3d0'; g.stroke(); }
    ell(g, 0, -214, 112, 104, '#ffe3d0', '#6b4b8a', 5);   // the huge head
    path(g, [[-114, -214], [-96, -300], [0, -330], [96, -300], [114, -214], [86, -262], [66, -226], [40, -270], [14, -224], [-12, -272], [-38, -228], [-62, -268], [-86, -222]]); g.fillStyle = '#ff8fb8'; g.fill(); g.strokeStyle = '#a8446f'; g.lineWidth = 5; g.stroke();
    for (const d of [-1, 1]) {
      const ex = d * 44, ey = -200;
      if (blink) { g.lineWidth = 6; g.strokeStyle = '#4b2f6b'; g.beginPath(); g.arc(ex, ey, 22, 0.15 * Math.PI, 0.85 * Math.PI); g.stroke(); continue; }
      ell(g, ex, ey, 28, 36, '#fff', '#4b2f6b', 5); const iris = g.createRadialGradient(ex, ey + 8, 4, ex, ey + 4, 28); iris.addColorStop(0, '#9fd4ff'); iris.addColorStop(1, '#2a56c8'); g.fillStyle = iris; g.beginPath(); g.ellipse(ex + 2, ey + 4, 21, 28, 0, 0, TAU); g.fill(); ell(g, ex + 2, ey + 6, 10, 14, '#1b1b44'); disc(g, ex - 7, ey - 10, 8, WHITE); disc(g, ex + 9, ey + 14, 4, WHITE);
      g.lineWidth = 7; g.strokeStyle = '#4b2f6b'; g.beginPath(); g.arc(ex, ey + 4, 31, Math.PI * 1.08, Math.PI * 1.92); g.stroke();
    }
    ell(g, -66, -162, 20, 11, 'rgba(255,110,150,.55)'); ell(g, 66, -162, 20, 11, 'rgba(255,110,150,.55)');
    if (air > 0.35) ell(g, 0, -150, 9, 12 + air * 6, '#c2415a', '#6b4b8a', 3); else { g.lineWidth = 4; g.strokeStyle = '#6b4b8a'; g.beginPath(); g.arc(-6, -156, 6, 0.1, Math.PI - 0.1); g.arc(6, -156, 6, 0.1, Math.PI - 0.1); g.stroke(); }
    polyFill(g, star(-70, -284, 20, 9, 5, -1.57), '#fff6b0', '#d9a21f', 3);
    g.restore();
  } },
  'ukiyo-e': { kind: '2d', fps: 8, draw(g, t, W, H) {
    // a woodblock print: flat colour areas and fine ink outlines, a great curling wave of Prussian blue with claw-like fingers of foam, a pale banded sky, a small mountain, and a red seal
    const ts = held(t, 8), INKB = '#14203a', BLUE = '#1f4a86', DEEP = '#16345f'; bg(g, W, H, '#efe3c6');
    ['#d8c79c', '#e3d3ab'].forEach((c, i) => { g.fillStyle = c; g.fillRect(0, i * 34, W, 34 + (i ? 0 : 1)); });
    for (const [cx, cy, w] of [[700, 120, 230], [860, 196, 190], [300, 70, 180]]) { g.fillStyle = '#e8dcc0'; g.beginPath(); g.roundRect(cx - w / 2, cy - 10, w, 20, 10); g.fill(); }
    const mk = easeOut(prog(ts, 0.2, 0.6)); polyFill(g, [[600, 456], [690, 346], [718, 330], [742, 346], [870, 456]], '#3c6aa3', INKB, 2); polyFill(g, [[690, 346], [718, 330], [742, 346], [724, 356], [716, 346], [706, 362], [696, 352]], '#f4efe0', INKB, 1.6);
    const sea = Array.from({ length: 30 }, (_, i) => [i * 34, 466 + Math.sin(i * 0.9 + ts * 1.6) * 7]); polyFill(g, [...sea, [W, H], [0, H]], BLUE, INKB, 2);
    for (let r = 0; r < 5; r++) { g.strokeStyle = 'rgba(240,235,210,.55)'; g.lineWidth = 1.6; path(g, Array.from({ length: 24 }, (_, i) => [40 + i * 40 + r * 14, 484 + r * 11 + Math.sin(i + r + ts * 1.6) * 3]), false); g.stroke(); }
    const ctrl = [[-30, 560], [-30, 330], [40, 250], [130, 170], [240, 112], [350, 92], [440, 108], [500, 150], [512, 205], [478, 225], [446, 200], [418, 178], [392, 198], [410, 246], [470, 310], [560, 388], [660, 450], [760, 500], [800, 560]];
    const wk = prog(ts, 0.1, 1.2), wave = closed(ctrl, 8); g.save(); g.translate(0, (1 - easeOut(wk)) * 120);
    polyFill(g, wave, BLUE, INKB, 3);
    g.save(); path(g, wave); g.clip(); for (let i = 1; i <= 7; i++) { g.strokeStyle = i % 2 ? DEEP : '#2b5c9e'; g.lineWidth = 2.4; path(g, scaleAbout(wave, 1 - i * 0.07).map(([x, y]) => [x + i * 7, y + i * 5]), false); g.stroke(); } g.restore();
    const crest = spline([[170, 150], [240, 112], [350, 92], [440, 108], [500, 150], [512, 205]], 12), n = 10;
    for (let i = 0; i < n; i++) {   // foam fingers: curved, tapering claws that reach out and down from the crest
      const k = easeOut(prog(ts, 0.8 + i * 0.1, 0.5)); if (k <= 0) continue; const [bx, by] = crest[Math.floor((i / n) * (crest.length - 4)) + 2], L = 24 + 6 * Math.sin(i * 1.7);
      polyFill(g, ribbon([[bx, by], [bx + L * 0.7 * k, by - 8 * k], [bx + L * 1.3 * k, by + 8 * k], [bx + L * 1.5 * k, by + 30 * k]], 8, 1.2), '#f6f2e4', INKB, 1.6);
    }
    for (let i = 0; i < 46; i++) { const k = prog(ts, 1.2 + hash(i, 1) * 1.6, 0.3); if (k > 0) disc(g, 250 + hash(i, 2) * 300 + k * 12, 90 + hash(i, 3) * 130 + (i % 3) * 8, 1.6 + hash(i, 4) * 3, '#f6f2e4'); }
    g.restore();
    for (const [bx, ph] of [[640, 0], [790, 2]]) { const by = 492 + Math.sin(ts * 2 + ph) * 4; polyFill(g, [[bx - 50, by], [bx + 50, by], [bx + 36, by + 9], [bx - 38, by + 9]], '#8a5a2b', INKB, 1.6); for (let i = 0; i < 4; i++) disc(g, bx - 24 + i * 16, by - 4, 3.4, '#e9d9b0'); }
    g.strokeStyle = INKB; g.lineWidth = 3; g.strokeRect(14, 14, W - 28, H - 28); g.fillStyle = '#c8322a'; g.fillRect(878, 30, 40, 58); g.fillStyle = '#efe3c6'; g.fillRect(886, 40, 24, 5); g.fillRect(886, 52, 24, 5); g.fillRect(896, 62, 5, 18);
    speckle(g, W, H, 3, 50, [110, 80, 40]);
  } },
  'tv-cartoon': { kind: '2d', fps: 12, draw(g, t, W, H) {
    // a modern TV cartoon: thick even outlines, flat bright colour, simple geometric characters, drawn on twos with a squash and a blink
    const ts = held(t, 12), f = frameOf(t, 12), O = OUT; g.lineJoin = 'round'; g.lineCap = 'round';
    bg(g, W, H, '#8fd0ff'); ell(g, 780, 110, 54, 54, '#ffe14d', O, 8); for (let i = 0; i < 8; i++) { const a = (i / 8) * TAU + ts * 0.5; g.lineWidth = 8; g.strokeStyle = O; path(g, [[780 + Math.cos(a) * 72, 110 + Math.sin(a) * 72], [780 + Math.cos(a) * 92, 110 + Math.sin(a) * 92]], false); g.stroke(); }
    for (const [cx, cy, s] of [[200, 100, 1], [520, 70, 0.8]]) { const dx = Math.sin(ts * 0.5 + cx) * 14; g.beginPath(); g.arc(cx + dx - 40 * s, cy, 34 * s, Math.PI * 0.5, Math.PI * 1.5); g.arc(cx + dx, cy - 22 * s, 40 * s, Math.PI, 0); g.arc(cx + dx + 44 * s, cy, 34 * s, Math.PI * 1.5, Math.PI * 0.5); g.closePath(); g.fillStyle = '#fff'; g.fill(); g.strokeStyle = O; g.lineWidth = 8; g.stroke(); }
    polyFill(g, [[0, 410], [180, 350], [380, 400], [560, 340], [760, 400], [960, 360], [960, 540], [0, 540]], '#5fcf62', O, 8);
    ell(g, 860, 330, 54, 54, '#3fb34f', O, 8); g.fillStyle = '#b5782f'; g.strokeStyle = O; g.lineWidth = 8; g.fillRect(846, 370, 28, 60); g.strokeRect(846, 370, 28, 60);
    const hop = (ph) => { const u = (ts * 1.4 + ph) % 1, air = 4 * u * (1 - u), land = u < 0.12 ? (0.12 - u) / 0.12 : 0; return [air * 80, 1 + land * 0.2 - air * 0.06]; };
    const [h1, s1] = hop(0), blink = (ts % 2.2) < 0.15;   // the square one
    g.save(); g.translate(300, 470 - h1); g.scale(1 / s1, s1);
    for (const d of [-1, 1]) { g.lineWidth = 14; g.strokeStyle = O; path(g, [[d * 30, -10], [d * 34, 24 - h1 * 0.1]], false); g.stroke(); ell(g, d * 36, 26 - h1 * 0.1, 22, 12, '#e8433a', O, 8); }
    for (const d of [-1, 1]) { g.lineWidth = 14; g.strokeStyle = O; path(g, [[d * 62, -86], [d * (96 + h1 * 0.3), -120 - h1 * 0.4]], false); g.stroke(); ell(g, d * (100 + h1 * 0.3), -124 - h1 * 0.4, 14, 14, '#fff', O, 7); }
    g.beginPath(); g.roundRect(-64, -150, 128, 140, 26); g.fillStyle = '#ffcc19'; g.fill(); g.strokeStyle = O; g.lineWidth = 8; g.stroke();
    for (const d of [-1, 1]) { if (blink) { g.lineWidth = 7; path(g, [[d * 28 - 16, -100], [d * 28 + 16, -100]], false); g.stroke(); } else { ell(g, d * 28, -102, 18, 22, '#fff', O, 7); disc(g, d * 28 + 5, -98, 8, O); } }
    g.beginPath(); g.moveTo(-30, -66); g.quadraticCurveTo(0, -30, 30, -66); g.closePath(); g.fillStyle = '#7a1f2b'; g.fill(); g.stroke(); g.fillStyle = '#fff'; g.fillRect(-10, -66, 20, 10); g.restore();
    const [h2] = hop(0.5); g.save(); g.translate(600, 470 - h2);   // the round one
    for (const d of [-1, 1]) { g.lineWidth = 14; g.strokeStyle = O; path(g, [[d * 22, -6], [d * 26, 22]], false); g.stroke(); ell(g, d * 30, 24, 20, 11, '#3c67e0', O, 8); }
    ell(g, 0, -80, 74, 74, '#ff8bc2', O, 8); path(g, [[-48, -140], [-62, -190], [-20, -150]]); g.fillStyle = '#ff8bc2'; g.fill(); g.stroke(); path(g, [[48, -140], [62, -190], [20, -150]]); g.fill(); g.stroke();
    ell(g, 0, -92, 28, 32, '#fff', O, 7); disc(g, 6 + Math.sin(ts * 2) * 4, -90, 12, O); g.beginPath(); g.arc(0, -52, 24, 0.15, Math.PI - 0.15); g.lineWidth = 7; g.stroke();
    g.lineWidth = 14; path(g, [[-68, -70], [-110, -110 + Math.sin(ts * 9) * 14]], false); g.stroke(); g.restore();
    if (prog(ts % 0.7143, 0, 0.1) > 0 && ((ts * 1.4) % 1) < 0.1) for (let i = 0; i < 6; i++) polyFill(g, star(300 + Math.cos(i) * 90, 440 + Math.sin(i * 2) * 20, 12, 5, 4, 0.78), '#fff', O, 4);
  } },
  'gothic-cartoon': { kind: '2d', fps: 8, draw(g, t, W, H) {
    // purple and black: a pale moon, crooked houses with lit windows, curly trees, and spindly, hollow-eyed figures that sway; everything leans a little and nothing is straight
    const ts = held(t, 8), f = frameOf(t, 8), O = '#0d0716'; g.lineJoin = 'round'; g.lineCap = 'round'; bg(g, W, H, '#2b1646');
    for (let i = 0; i < 40; i++) { const tw = (f + i) % 6; disc(g, hash(i, 1) * W, hash(i, 2) * 300, tw ? 1.6 : 2.6, '#d9cfee'); }
    ell(g, 700, 150, 92, 92, '#ece6cc', O, 6); for (const [x, y, r] of [[670, 120, 16], [725, 178, 12], [738, 112, 8]]) ell(g, x, y, r, r * 0.8, '#d3cba8'); g.strokeStyle = '#c4bb96'; g.lineWidth = 3; path(g, curlPts(700, 150, 40, 1.6), false); g.stroke();
    polyFill(g, [[0, 430], [200, 400], [420, 440], [640, 400], [960, 430], [960, 540], [0, 540]], '#1a0d2b', O, 6); for (let i = 0; i < 14; i++) { g.strokeStyle = '#5b3394'; g.lineWidth = 5; path(g, [[i * 74, 470 + (i % 2) * 20], [i * 74 + 50, 500 + (i % 2) * 20]], false); g.stroke(); }
    const house = (x, base, w, h, ph) => { const lean = Math.sin(ts * 1.4 + ph) * 0.03 + (ph % 2 ? 0.07 : -0.06); g.save(); g.translate(x, base); g.transform(1, 0, lean, 1, 0, 0); polyFill(g, [[-w / 2, 0], [w / 2 + 6, 0], [w / 2 - 8, -h], [-w / 2 + 10, -h - 6]], '#17102a', O, 6); polyFill(g, [[-w / 2 - 14, -h - 2], [w / 2 + 6, -h + 4], [4, -h - w * 1.3]], '#2a1646', O, 6); for (const [wx, wy] of [[-w / 4, -h * 0.62], [w / 5, -h * 0.35]]) { g.save(); g.translate(wx, wy); g.rotate(wx * 0.004 + 0.1); polyFill(g, [[-12, -16], [12, -14], [10, 16], [-10, 18]], (f + ph) % 9 ? '#f2e08a' : '#8a7a3a', O, 4); g.restore(); } g.restore(); };
    house(140, 450, 100, 190, 1); house(330, 446, 84, 140, 2); house(840, 450, 110, 210, 3);
    const tree = (x, base, h, ph) => { const sway = Math.sin(ts * 1.6 + ph) * 8; g.strokeStyle = O; g.lineWidth = 12; path(g, [[x, base], [x + 8 + sway * 0.3, base - h * 0.5], [x - 10 + sway, base - h]], false); g.stroke(); g.lineWidth = 5; for (const d of [-1, 1]) { path(g, curlPts(x + d * 34 + sway, base - h * 0.78 - 10, 30, 2.1, d), false); g.stroke(); path(g, [[x + 4, base - h * 0.55], [x + d * 24 + sway * 0.5, base - h * 0.66]], false); g.stroke(); } path(g, curlPts(x - 10 + sway, base - h - 22, 24, 2.2), false); g.stroke(); };
    tree(250, 450, 190, 0); tree(640, 440, 220, 2); tree(940, 460, 160, 4);
    const figure = (x, base, sc, ph) => {
      const sw = Math.sin(ts * 3 + ph) * 0.5; g.save(); g.translate(x, base); g.scale(sc, sc); g.lineWidth = 10; g.strokeStyle = O;
      for (const d of [-1, 1]) { path(g, [[d * 8, -120], [d * 8 + Math.sin(sw * d) * 26, -60], [d * 12 + Math.sin(sw * d) * 40, -4]], false); g.stroke(); ell(g, d * 12 + Math.sin(sw * d) * 52, 0, 22, 8, O); }
      polyFill(g, [[-20, -230], [20, -230], [14, -118], [-14, -118]], '#17102a', O, 6); for (let i = 0; i < 4; i++) { g.fillStyle = '#6b3fa0'; g.fillRect(-18 + i * 2, -218 + i * 24, 36 - i * 4, 8); }
      for (const d of [-1, 1]) { path(g, [[d * 18, -218], [d * (38 + Math.sin(sw + d) * 16), -156], [d * (30 + Math.sin(sw + d) * 22), -100]], false); g.stroke(); disc(g, d * (30 + Math.sin(sw + d) * 22), -96, 8, '#e8e2c8', O, 3); }
      g.lineWidth = 6; path(g, [[0, -230], [0, -258]], false); g.stroke(); ell(g, 0, -290, 32, 38, '#e8e2c8', O, 6); ell(g, -12, -294, 8, 13, O); ell(g, 12, -294, 8, 13, O); path(g, [[-10, -268], [-4, -272], [2, -266], [8, -272], [12, -268]], false); g.stroke(); polyFill(g, [[-30, -300], [-24, -346], [-10, -312], [0, -354], [10, -314], [26, -348], [30, -300]], O); g.restore();
    };
    figure(520, 460, 1, 0); figure(430, 470, 0.7, 2);
    for (let i = 0; i < 4; i++) { const bx = 120 + ((ts * 60 + i * 240) % 840), by = 90 + i * 30 + Math.sin(ts * 3 + i) * 12, fl = Math.sin(ts * 12 + i) * 10; polyFill(g, [[bx, by], [bx - 18, by - 12 - fl], [bx - 28, by + 2], [bx - 10, by + 4], [bx, by + 10], [bx + 10, by + 4], [bx + 28, by + 2], [bx + 18, by - 12 - fl]], O); }
    const fog = g.createLinearGradient(0, 400, 0, 540); fog.addColorStop(0, 'rgba(120,90,170,0)'); fog.addColorStop(1, 'rgba(120,90,170,.35)'); g.fillStyle = fog; g.fillRect(0, 400, W, 140);
  } },
  'pop-up-book': { kind: '2d', fps: null, draw(g, t, W, H) {
    // an open book seen at an angle: the right page swings open, then layered card pieces stand up off the pages, each with a fold shadow, a card edge and a shadow on the page
    const open = easeInOut(prog(t, 0, 1.2)), X0 = 480, FW = 400, BW = 340;
    const P = (side, u, v, ox = 1) => [X0 + side * u * (FW - (FW - BW) * v) * ox, 472 - v * 270];
    g.fillStyle = '#cdb48a'; g.fillRect(0, 0, W, H); const wood = g.createLinearGradient(0, 0, 0, H); wood.addColorStop(0, 'rgba(255,255,255,.18)'); wood.addColorStop(1, 'rgba(90,60,20,.2)'); g.fillStyle = wood; g.fillRect(0, 0, W, H);
    ell(g, 480, 490, 470, 36, 'rgba(60,35,10,.3)');
    polyFill(g, [[X0 - FW - 16, 484], [X0 + FW + 16, 484], [X0 + BW + 20, 188], [X0 - BW - 20, 188]], '#7a1f2b', '#4a1019', 3);
    const rx = Math.cos(Math.PI * (1 - open)), page = (side, ox) => polyFill(g, [P(side, 1, 0, ox), P(side, 0, 0), P(side, 0, 1), P(side, 1, 1, ox)], '#f6efdc', '#b8a97f', 2);
    page(-1, 1); page(1, rx);
    const sp = g.createLinearGradient(X0 - 50, 0, X0 + 50, 0); sp.addColorStop(0, 'rgba(60,40,20,0)'); sp.addColorStop(0.5, 'rgba(60,40,20,.38)'); sp.addColorStop(1, 'rgba(60,40,20,0)'); g.fillStyle = sp; g.fillRect(X0 - 50, 200, 100, 276);
    const pieces = [
      [1, 0.5, 0.96, 330, 150, 1.0, (w, h) => { polyFill(g, [[-w / 2, 0], [-w / 2, -h * 0.55], [-w * 0.25, -h * 0.9], [0, -h * 0.7], [w * 0.25, -h], [w / 2, -h * 0.6], [w / 2, 0]], '#7cc576', '#3f7a45', 3); }],
      [-1, 0.5, 0.96, 120, 190, 1.1, (w, h) => { ell(g, 0, -h * 0.6, w / 2, w / 2, '#ffd23f', '#c99a0f', 3); g.strokeStyle = '#c99a0f'; g.lineWidth = 3; path(g, [[0, -h * 0.1], [0, 0]], false); g.stroke(); }],
      [1, 0.45, 0.62, 160, 150, 1.5, (w, h) => { polyFill(g, [[-w / 2, 0], [-w / 2, -h * 0.7], [w / 2, -h * 0.7], [w / 2, 0]], '#e8a0a0', '#9a5a5a', 3); for (const d of [-1, 1]) { polyFill(g, [[d * w * 0.5 - 22, -h * 0.7], [d * w * 0.5 - 22, -h], [d * w * 0.5 + 22, -h], [d * w * 0.5 + 22, -h * 0.7]], '#d98a8a', '#9a5a5a', 3); polyFill(g, [[d * w * 0.5 - 28, -h], [d * w * 0.5, -h * 1.28], [d * w * 0.5 + 28, -h]], '#4a5fb5', '#26346d', 3); } for (let i = -3; i <= 3; i++) g.fillRect(i * 18 - 6, -h * 0.7 - 9, 12, 9); polyFill(g, [[-18, 0], [-18, -h * 0.38], [0, -h * 0.5], [18, -h * 0.38], [18, 0]], '#5a2f1a', '#2a140a', 3); }],
      [-1, 0.5, 0.5, 130, 120, 1.8, (w, h) => { polyFill(g, [[-w / 2, 0], [-w / 2, -h * 0.6], [w / 2, -h * 0.6], [w / 2, 0]], '#f4e3b0', '#a89458', 3); polyFill(g, [[-w * 0.62, -h * 0.6], [0, -h * 1.05], [w * 0.62, -h * 0.6]], '#c0392b', '#7a1f18', 3); polyFill(g, [[-10, 0], [-10, -h * 0.34], [10, -h * 0.34], [10, 0]], '#5a2f1a'); }],
      [1, 0.8, 0.34, 70, 130, 2.1, (w, h) => { g.fillStyle = '#8a5a2b'; g.fillRect(-7, -h * 0.5, 14, h * 0.5); ell(g, 0, -h * 0.72, w * 0.55, h * 0.3, '#2e9b4f', '#1b6b32', 3); }],
      [-1, 0.25, 0.12, 60, 80, 2.4, (w, h) => { g.strokeStyle = '#2e9b4f'; g.lineWidth = 4; path(g, [[0, 0], [0, -h * 0.7]], false); g.stroke(); ell(g, 0, -h * 0.8, 16, 16, '#ff6b8a', '#a8334f', 2); }],
      [1, 0.3, 0.1, 60, 90, 2.6, (w, h) => { g.strokeStyle = '#2e9b4f'; g.lineWidth = 4; path(g, [[0, 0], [0, -h * 0.7]], false); g.stroke(); ell(g, 0, -h * 0.8, 16, 16, '#ffd23f', '#a87f0f', 2); }],
    ];
    pieces.sort((a, b) => b[2] - a[2]).forEach(([side, u, v, w, h, st, draw]) => {
      const k = clamp(overshootK(prog(t, st, 0.55))); if (k <= 0.001 || open < 0.6) return;
      const [px, py] = P(side, u, v), sc = 1 - 0.15 * v; g.save(); g.translate(px, py);
      ell(g, 8 * k, 2, w * 0.5 * sc, 7 * k * sc, 'rgba(50,30,10,.28)'); g.save(); g.scale(sc, sc * k); g.translate(5, 0); g.globalAlpha = 0.5; g.fillStyle = '#000'; draw(w, h); g.restore();   // the card edge, offset to one side
      g.save(); g.scale(sc, sc * k); draw(w, h); g.restore();
      const fold = g.createLinearGradient(0, 0, 0, -14); fold.addColorStop(0, 'rgba(40,20,0,.35)'); fold.addColorStop(1, 'rgba(40,20,0,0)'); g.fillStyle = fold; g.fillRect(-w * 0.5 * sc, -14 * k, w * sc, 14 * k); g.restore();
    });
  } },
  papercut: { kind: '2d', fps: 8, draw(g, t, W, H) {
    // one colour of lace-cut paper, red on cream: a scalloped medallion and four corner pieces, symmetrical cut patterns that open ring by ring, a drop shadow under the paper
    const ts = held(t, 8), f = frameOf(t, 8), RED = '#c8281f', cx = 480, cy = 270; bg(g, W, H, '#f2e8d2'); speckle(g, W, H, 2, 34, [150, 120, 70]);
    const kk = (i) => easeOut(prog(ts, 0.2 + i * 0.45, 0.6)), sway = jit(f, 1, 0.004);
    const rings = [[16, 46, 12, 8, 'leaf'], [76, 40, 9, 16, 'leaf'], [124, 20, 9, 16, 'dot'], [150, 34, 8, 24, 'drop'], [190, 22, 3.6, 48, 'dot'], [208, 16, 5, 36, 'drop']];
    const outer = Array.from({ length: 360 }, (_, i) => { const a = (i / 360) * TAU, r = 240 + 8 * Math.abs(Math.cos(a * 18)); return [cx + Math.cos(a) * r, cy + Math.sin(a) * r]; });
    const holes = rings.flatMap(([r0, len, wid, n, kind], i) => laceRing(cx, cy, r0, len, wid, n, kind, 0, TAU, kk(i)));
    holes.push(...laceRing(cx, cy, 0, 0, 8 * kk(0), 1, 'dot'));
    g.save(); g.translate(cx, cy); g.rotate(sway); g.translate(-cx, -cy); g.shadowColor = 'rgba(70,20,10,.45)'; g.shadowBlur = 9; g.shadowOffsetX = 4 + jit(f, 2, 1); g.shadowOffsetY = 6; g.fillStyle = RED; g.fill(holesPath(outer, holes), 'evenodd'); g.restore();
    for (const [sx, sy] of [[1, 1], [-1, 1], [1, -1], [-1, -1]]) {   // corner lace, mirrored four ways
      const q = []; for (let i = 0; i <= 40; i++) { const a = (i / 40) * Math.PI / 2, r = 150 + 6 * Math.abs(Math.cos(a * 16)); q.push([Math.cos(a) * r, Math.sin(a) * r]); }
      const ch = [[0, 34, 9, 6, 'leaf'], [66, 26, 7, 9, 'drop'], [112, 14, 4.6, 14, 'dot']].flatMap(([r0, len, wid, n, kind], i) => laceRing(0, 0, r0, len, wid, n, kind, 0.12, Math.PI / 2 - 0.12, kk(i + 1)));
      g.save(); g.translate(sx > 0 ? 0 : W, sy > 0 ? 0 : H); g.scale(sx, sy); g.shadowColor = 'rgba(70,20,10,.45)'; g.shadowBlur = 8; g.shadowOffsetX = 3; g.shadowOffsetY = 5; g.fillStyle = RED; g.fill(holesPath([[0, 0], ...q], ch.map((h) => h)), 'evenodd'); g.restore();
    }
  } },
  'brick-toy': { kind: '2d', fps: 12, draw(g, t, W, H) {
    // everything built from studded plastic bricks on a baseplate: bricks drop in one at a time, each with its studs, a bright edge and a glossy highlight, drawn on twos
    const ts = held(t, 12), sky = g.createLinearGradient(0, 0, 0, H); sky.addColorStop(0, '#dbe9fb'); sky.addColorStop(1, '#f6f9ff'); g.fillStyle = sky; g.fillRect(0, 0, W, H); g.lineJoin = 'round';
    const base = [iso(0, 0, 0), iso(12, 0, 0), iso(12, 10, 0), iso(0, 10, 0)];
    polyFill(g, [iso(0, 10, 0), iso(12, 10, 0), iso(12, 10, -0.35), iso(0, 10, -0.35)], '#1f7a3c', 'rgba(0,0,0,.35)', 1.2); polyFill(g, [iso(12, 0, 0), iso(12, 10, 0), iso(12, 10, -0.35), iso(12, 0, -0.35)], '#17602f', 'rgba(0,0,0,.35)', 1.2); polyFill(g, base, '#2e9b4f', 'rgba(0,0,0,.35)', 1.2);
    for (let i = 0; i < 12; i++) for (let j = 0; j < 10; j++) stud(g, i + 0.5, j + 0.5, 0, '#2e9b4f', 0.4);
    const WH = '#f4f1ea', CR = '#f2d9a0', RD = '#d6342a', BL = '#2f6fdf', YL = '#f5c518', BR = '#7a4a22', GR = '#2e9b4f', DK = '#2a2a33', list = [];
    for (let z = 0; z < 4; z++) { const c = z % 2 ? CR : WH; for (const x of [2, 4, 6]) { list.push([x, 6, z, 2, 1, z < 3 && x === 4 ? BR : (z === 1 || z === 2) && x === 6 ? BL : c]); list.push([x, 3, z, 2, 1, c]); } list.push([2, 4, z, 1, 2, c], [7, 4, z, 1, 2, c]); }
    for (const x of [2, 4, 6]) list.push([x, 3, 4, 2, 4, RD]); for (const x of [3, 5]) list.push([x, 3, 5, 2, 4, RD]); list.push([4, 3, 6, 2, 4, RD], [6, 3, 5, 1, 1, YL], [6, 3, 6, 1, 1, YL]);
    for (let z = 0; z < 3; z++) list.push([10, 1, z, 1, 1, BR]); list.push([9, 0, 3, 3, 3, GR], [9, 1, 4, 2, 2, GR], [9, 1, 5, 1, 1, GR]);
    list.push([1, 8, 0, 1, 1, YL], [1, 8, 1, 1, 1, RD], [1, 8, 2, 1, 1, YL], [1, 8, 3, 1, 1, DK], [3, 8, 0, 2, 1, BL], [3, 8, 1, 1, 1, YL]);
    list.map((b, i) => ({ b, i, st: 0.1 + i * 0.075 })).sort((a, b) => (a.b[0] + a.b[3] + a.b[1] + a.b[4]) - (b.b[0] + b.b[3] + b.b[1] + b.b[4]) || a.b[2] - b.b[2]).forEach(({ b, st }) => {
      const k = prog(ts, st, 0.4); if (k <= 0) return; const drop = (1 - easeOut(k)) * 6, [gx, gy, gz, w, d, col] = b;
      g.save(); g.translate(0, -drop * ISO.bh); g.globalAlpha = clamp(k * 3); brick(g, gx, gy, gz, w, d, col); g.restore();
    });
  } },
  'string-puppet': { kind: '2d', fps: 8, draw(g, t, W, H) {
    // kathputli marionettes in bright Rajasthani dress: a king and a dancer hang from a control bar by strings and swing jerkily, in a small theatre with red curtains and a gold valance
    const ts = held(t, 8), barY = 54, tilt = Math.sin(ts * 1.3) * 0.05; bg(g, W, H, '#e8b53a');
    g.fillStyle = '#d99a22'; for (let i = 0; i < 20; i++) g.fillRect(i * 50, 0, 25, H); polyFill(g, [[300, 470], [300, 200], [480, 100], [660, 200], [660, 470]], '#c0392b', '#7a1f18', 6); polyFill(g, [[330, 470], [330, 210], [480, 128], [630, 210], [630, 470]], '#f3d77a', '#c99a0f', 4);
    for (let i = 0; i < 12; i++) disc(g, 340 + i * 25, 470 - 8, 4, '#c0392b'); g.fillStyle = '#6b3b1f'; g.fillRect(0, 440, W, 100); g.fillStyle = '#8a4e28'; for (let i = 0; i < 8; i++) g.fillRect(i * 125, 440, 3, 100);
    g.save(); g.translate(480, barY); g.rotate(tilt); g.fillStyle = '#5b3a1e'; g.fillRect(-190, -7, 380, 14); disc(g, -190, 0, 9, '#8a5a2b'); disc(g, 190, 0, 9, '#8a5a2b'); g.restore();
    for (const [x, hy, kind, ph] of [[410, 172, 'king', 0], [570, 176, 'dancer', 2]]) { g.save(); g.translate(x, barY); g.scale(1.3, 1.3); g.translate(-x, -barY); puppet(g, x, hy, kind, ph, ts, barY); g.restore(); }
    for (const side of [-1, 1]) { g.save(); g.translate(side > 0 ? W : 0, 0); g.scale(side, 1); for (let i = 0; i < 6; i++) { polyFill(g, [[i * 40, 0], [i * 40 + 40, 0], [i * 40 + 34 - (5 - i) * 4, 480], [i * 40 + 4 - (5 - i) * 4, 480]], i % 2 ? '#8a1722' : '#a8222c'); } g.fillStyle = '#f5c542'; g.fillRect(0, 470, 240, 10); for (let i = 0; i < 24; i++) g.fillRect(i * 10 + 2, 480, 3, 14); g.restore(); }
    g.fillStyle = '#a8222c'; g.fillRect(0, 0, W, 34); for (let i = 0; i < 20; i++) { g.beginPath(); g.arc(i * 50 + 25, 34, 25, 0, Math.PI); g.fill(); g.strokeStyle = '#f5c542'; g.lineWidth = 4; g.stroke(); }
    g.fillStyle = '#f5c542'; g.fillRect(0, 28, W, 6);
  } },
};
export const IDS = Object.keys(LOOKS);
