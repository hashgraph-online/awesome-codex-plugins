// brief2mp4 art forms: looks-folk.js, batch 2 (Indian folk and print traditions). MIT. Same rules as looks.js:
// every look is a pure function of time, no clock, all roughness from hash(). These are code studies of each
// tradition's visual rules, not the craft itself: living artists make the real thing.
import { TAU, clamp, lerp, prog, easeOut, easeInOut, hash, frameOf, held, jit, grain, blob, strokePart, circlePts, bg, FONT } from './looks.js';
import { rgba, mix, spline, bounds, tooth, speckle } from './looks-painted.js';

const INK = '#15100d';
export const centroid = (pts) => [pts.reduce((a, p) => a + p[0], 0) / pts.length, pts.reduce((a, p) => a + p[1], 0) / pts.length];
export const scaleAbout = (pts, k) => { const [cx, cy] = centroid(pts); return pts.map(([x, y]) => [cx + (x - cx) * k, cy + (y - cy) * k]); };
export const closed = (pts, per = 8) => { const n = pts.length; return spline([pts[n - 1], ...pts, pts[0], pts[1]], per).slice(per, per * (n + 1) + 1); };   // a smooth closed curve through the points
export const rot = (pts, x, y, a, sx = 1, sy = sx) => pts.map(([u, v]) => [x + (u * sx) * Math.cos(a) - (v * sy) * Math.sin(a), y + (u * sx) * Math.sin(a) + (v * sy) * Math.cos(a)]);
export const leaf = (x, y, len, wid, ang) => closed(rot([[0, 0], [0.3, -0.5], [0.72, -0.4], [1, 0], [0.72, 0.4], [0.3, 0.5]], x, y, ang, len, wid * 2), 4);   // a pointed leaf or petal, root at (x, y)
export const fish = (cx, cy, L, H, dir = 1, a = 0) => closed(rot([[1, 0], [0.55, -0.42], [-0.1, -0.5], [-0.55, -0.22], [-0.7, -0.06], [-1.0, -0.42], [-0.92, 0], [-1.0, 0.42], [-0.7, 0.06], [-0.55, 0.22], [-0.1, 0.5], [0.55, 0.42]].map(([x, y]) => [x * dir, y]), cx, cy, a, L, H), 6);
// parallel lines over a box, at an angle
export function lines(g, bb, ang, sp, w, col, from = 0) {
  const cx = (bb[0] + bb[2]) / 2, cy = (bb[1] + bb[3]) / 2, D = Math.hypot(bb[2] - bb[0], bb[3] - bb[1]) / 2 + 2, dx = Math.cos(ang), dy = Math.sin(ang);
  g.strokeStyle = col; g.lineWidth = w; g.beginPath();
  for (let c = -D + from; c <= D; c += sp) { const x = cx - dy * c, y = cy + dx * c; g.moveTo(x - dx * D, y - dy * D); g.lineTo(x + dx * D, y + dy * D); }
  g.stroke();
}
export function dots(g, bb, sp, r, col) { g.fillStyle = col; g.beginPath(); for (let y = bb[1], j = 0; y <= bb[3]; y += sp, j++) for (let x = bb[0] + (j % 2) * sp / 2; x <= bb[2]; x += sp) { g.moveTo(x + r, y); g.arc(x, y, r, 0, TAU); } g.fill(); }
export function scales(g, bb, r, col, w = 2) { g.strokeStyle = col; g.lineWidth = w; g.beginPath(); for (let y = bb[1], j = 0; y <= bb[3] + r; y += r * 0.8, j++) for (let x = bb[0] - r + (j % 2) * r; x <= bb[2] + r; x += r * 2) { g.moveTo(x + r, y); g.arc(x, y, r, 0, Math.PI); } g.stroke(); }
// a shape that is drawn on in stages: the outline travels round it, the fill comes in, a pattern fills it, and a second inner line follows.
// o: { start, dur, fill, line, lw, inner, pattern(g, bb) }; pts must be a closed polyline
export function folkShape(g, pts, o, ts) {
  const k = prog(ts, o.start, o.dur); if (k <= 0) return;
  if (k > 0.5 && o.fill) {
    g.save(); g.globalAlpha = clamp((k - 0.5) / 0.3); g.fillStyle = o.fill; g.beginPath(); pts.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.closePath(); g.fill();
    if (o.pattern) { g.clip(); o.pattern(g, bounds(pts)); } g.restore();
  }
  g.strokeStyle = o.line || INK; g.lineWidth = o.lw || 4; g.lineJoin = 'round'; g.lineCap = 'round'; strokePart(g, pts, clamp(k / 0.6));
  if (o.inner && k > 0.7) { g.lineWidth = Math.max(1.4, (o.lw || 4) * 0.45); strokePart(g, scaleAbout(pts, o.inner), clamp((k - 0.7) / 0.3)); }
}
// a band of triangles round the four sides of the frame: base on the outer edge, apex pointing in, colours cycling
function borderTriangles(g, W, H, cols, shown) {
  let i = 0;
  for (const [x0, y0, ux, uy, n] of [[78, 28, 0, 1, (W - 156) / 26], [78, H - 28, 0, -1, (W - 156) / 26], [28, 78, 1, 0, (H - 156) / 26], [W - 28, 78, -1, 0, (H - 156) / 26]]) {
    for (let j = 0; j < n; j++, i++) {
      if (!shown(i)) continue;
      const x = x0 + (uy ? j * 26 + 13 : 0), y = y0 + (ux ? j * 26 + 13 : 0);
      g.fillStyle = cols[j % cols.length]; g.beginPath(); g.moveTo(x - uy * 12, y + ux * 12); g.lineTo(x + uy * 12, y - ux * 12); g.lineTo(x + ux * 30, y + uy * 30); g.closePath(); g.fill();
    }
  }
}
export const disc = (g, x, y, r, col, line = 0) => { g.fillStyle = col; g.beginPath(); g.arc(x, y, Math.max(0, r), 0, TAU); g.fill(); if (line) { g.strokeStyle = INK; g.lineWidth = line; g.stroke(); } };
// a flower seen from the front: round petals round a centre
export function rosette(g, x, y, r, n, col, col2, seed = 0) {
  g.fillStyle = col; for (let i = 0; i < n; i++) { const a = (i / n) * TAU + seed; g.beginPath(); g.ellipse(x + Math.cos(a) * r * 0.55, y + Math.sin(a) * r * 0.55, r * 0.46, r * 0.26, a, 0, TAU); g.fill(); }
  disc(g, x, y, r * 0.3, col2); disc(g, x, y, r * 0.12, INK);
}

const WHITE = '#f6efe0';
// a Warli figure: a circle head and two triangles that meet at their tips, with stick arms and legs; step 0 or 1 swaps the pose
function warliFigure(g, x, y, s, ang, step, reach) {
  g.save(); g.translate(x, y); g.rotate(ang); g.fillStyle = g.strokeStyle = WHITE; g.lineWidth = Math.max(1.7, s * 0.14); g.lineCap = 'round';
  g.beginPath(); g.moveTo(-0.55 * s, -s); g.lineTo(0.55 * s, -s); g.lineTo(0, 0); g.closePath(); g.moveTo(0, 0); g.lineTo(-0.55 * s, s); g.lineTo(0.55 * s, s); g.closePath(); g.fill();
  g.beginPath(); g.arc(0, -1.45 * s, 0.3 * s, 0, TAU); g.fill();
  g.beginPath(); for (const d of [-1, 1]) { g.moveTo(d * 0.5 * s, -0.9 * s); g.lineTo(d * (0.5 * s + reach), -0.9 * s + (step ? -0.4 : 0.3) * s); g.moveTo(d * 0.42 * s, s); g.lineTo(d * (0.3 + 0.35 * step) * s, 2.05 * s); }
  g.stroke(); g.restore();
}
// a Warli tree: a trunk, branches in pairs that shorten toward the top, and a small round leaf at each tip
function warliTree(g, x, y, sc, k) {
  g.strokeStyle = g.fillStyle = WHITE; g.lineWidth = 3; g.lineCap = 'round';
  strokePart(g, [[x, y], [x, y - 150 * sc]], clamp(k * 1.4));
  for (let l = 1; l <= 5; l++) for (const d of [-1, 1]) { const e = clamp(k * 2 - l * 0.18); if (e <= 0) continue; const bx = x, by = y - l * 26 * sc, len = (120 - l * 18) * sc; strokePart(g, [[bx, by], [bx + d * len * 0.55, by - len * 0.3], [bx + d * len, by - len * 0.55]], e); if (e > 0.95) { g.beginPath(); g.arc(bx + d * len, by - len * 0.55, 5 * sc, 0, TAU); g.fill(); } }
}
// a curl of vine: an Archimedean spiral that winds out from (x, y)
const curl = (x, y, r, turns = 2.2, dir = 1) => Array.from({ length: 30 }, (_, i) => { const a = (i / 29) * turns * TAU * dir, rr = r * (1 - i / 36); return [x + Math.cos(a) * rr, y + Math.sin(a) * rr]; });

export const ellipseLine = (x, y, rx, ry, a = 0) => rot(circlePts(0, 0, 1, 28), x, y, a, rx, ry);
// Gond bands: each band is a solid base colour with fine marks of one contrasting colour: dots, dashes, parallel lines or fish-scale arcs
const GOND = [['#b3182a', '#f7c948'], ['#f2a81d', '#15100d'], ['#1f4fa8', '#f6f0dc'], ['#2d8a3e', '#f7c948'], ['#15100d', '#f2a81d'], ['#b3182a', '#f6f0dc'], ['#f2a81d', '#b3182a'], ['#1f4fa8', '#f2a81d']];
function gondBands(g, bb, ang, seed = 0) {
  const cx = (bb[0] + bb[2]) / 2, cy = (bb[1] + bb[3]) / 2, D = Math.hypot(bb[2] - bb[0], bb[3] - bb[1]) / 2 + 6;
  g.save(); g.translate(cx, cy); g.rotate(ang); g.lineCap = 'round';
  for (let r = 0, y = -D; y <= D; y += 14, r++) {
    const [base, mark] = GOND[(r * 3 + seed) % GOND.length], kind = (r + seed) % 4;
    g.fillStyle = base; g.fillRect(-D, y, 2 * D, 14.5); g.fillStyle = g.strokeStyle = mark; g.lineWidth = 1.8;
    if (kind === 0) { g.beginPath(); for (let x = -D; x < D; x += 8) { g.moveTo(x + 2.4, y + 7); g.arc(x, y + 7, 2.4, 0, TAU); } g.fill(); }
    else if (kind === 1) { g.lineWidth = 2.4; g.beginPath(); for (let x = -D; x < D; x += 7) { g.moveTo(x, y + 3.5); g.lineTo(x, y + 10.5); } g.stroke(); }
    else if (kind === 2) { g.beginPath(); for (const o of [4, 7, 10]) { g.moveTo(-D, y + o); g.lineTo(D, y + o); } g.stroke(); }
    else { g.beginPath(); for (let x = -D; x < D; x += 10) { g.moveTo(x + 5, y + 4); g.arc(x, y + 4, 5, 0, Math.PI); } g.stroke(); }
  }
  g.restore();
}
// a tapering band along a curve: used for tree trunks and branches
export function ribbon(ctrl, w0, w1) {
  const pts = spline(ctrl, 8), n = pts.length, L = [], R = [];
  pts.forEach(([x, y], i) => { const p = pts[Math.max(0, i - 1)], q = pts[Math.min(n - 1, i + 1)], a = Math.atan2(q[1] - p[1], q[0] - p[0]), w = lerp(w0, w1, i / (n - 1)); L.push([x + Math.sin(a) * w, y - Math.cos(a) * w]); R.push([x - Math.sin(a) * w, y + Math.cos(a) * w]); });
  return [...L, ...R.reverse(), L[0]];
}
export function halftone(g, bb, pitch, ang, val) {
  const cx = (bb[0] + bb[2]) / 2, cy = (bb[1] + bb[3]) / 2, n = Math.ceil(Math.hypot(bb[2] - bb[0], bb[3] - bb[1]) / 2 / pitch), c = Math.cos(ang), s = Math.sin(ang);
  g.beginPath();
  for (let j = -n; j <= n; j++) for (let i = -n; i <= n; i++) { const x = cx + (i * c - j * s) * pitch, y = cy + (i * s + j * c) * pitch; if (x < bb[0] || x > bb[2] || y < bb[1] || y > bb[3]) continue; const r = pitch * 0.72 * Math.sqrt(clamp(val(x, y))); if (r > 0.4) { g.moveTo(x + r, y); g.arc(x, y, r, 0, TAU); } }
  g.fill();
}
// one ink of a screen print: it slides into register, overprints (multiply) and sits a little off, differently on each drawing
function inkLayer(g, col, start, ts, f, off, draw) {
  const k = easeOut(prog(ts, start, 0.7)); if (k <= 0) return;
  g.save(); g.globalCompositeOperation = 'multiply'; g.globalAlpha = k; g.translate(off[0] + (1 - k) * off[2] + jit(f, start * 10, 1.4), off[1] + (1 - k) * off[3] + jit(f, start * 10 + 1, 1.4)); g.fillStyle = col; draw(); g.restore();
}
const polyFill = (g, pts) => { g.beginPath(); pts.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.closePath(); g.fill(); };
// an engraved sphere: a point on it, turned by tilt, as screen position and a brightness from a light at upper left
function spherePoint(phi, lam, R, cx, cy, tilt) {
  const X = Math.cos(phi) * Math.sin(lam), Y = Math.sin(phi), Z = Math.cos(phi) * Math.cos(lam), Yp = Y * Math.cos(tilt) - Z * Math.sin(tilt), Zp = Y * Math.sin(tilt) + Z * Math.cos(tilt);
  return { x: cx + R * X, y: cy - R * Yp, vis: Zp > 0.02, shade: Math.max(0, X * -0.55 + Yp * 0.55 + Zp * 0.63) };
}

export const LOOKS = {
  /* ------------------------------------------------ folk and print traditions ------------------------------------------------ */
  madhubani: { kind: '2d', fps: 8, draw(g, t, W, H) {
    // fish, a peacock and a lotus in double black outlines, every gap filled with dots, hatching and small motifs, inside a decorated border: no empty paper
    const ts = held(t, 8), f = frameOf(t, 8), RED = '#c8312b', YEL = '#f0b429', GRN = '#2e8b57', IND = '#2b3a8c';
    bg(g, W, H, '#f3e2bd'); g.lineCap = 'round'; g.lineJoin = 'round';
    const k0 = easeOut(prog(ts, 0, 0.7));
    g.strokeStyle = INK; for (const [ins, w] of [[14, 5], [21, 2], [64, 2], [71, 5]]) { g.lineWidth = w; strokePart(g, [[ins, ins], [W - ins, ins], [W - ins, H - ins], [ins, H - ins], [ins, ins]], k0); }
    borderTriangles(g, W, H, [RED, YEL, IND], (i) => prog(ts, 0.1 + hash(i, 1) * 0.6, 0.1) > 0);
    for (const [x, y] of [[43, 43], [W - 43, 43], [43, H - 43], [W - 43, H - 43]]) if (k0 > 0.6) rosette(g, x, y, 15, 8, RED, YEL);
    g.save(); g.globalAlpha = k0; g.beginPath(); g.rect(72, 72, W - 144, H - 144); g.clip(); lines(g, [72, 72, W - 72, H - 72], 0.75, 9, 1, 'rgba(150,100,40,.28)'); g.restore();   // even the paper is hatched
    for (let y = 86, r = 0; y < H - 76; y += 27, r++) for (let x = 86 + (r % 2) * 14; x < W - 76; x += 28) {   // the ground: a small motif in every gap, chosen and placed by a hash
      const c = Math.floor(x / 28) + r * 40, k = prog(ts, 0.3 + hash(c, 2) * 2.4, 0.1), kind = Math.floor(hash(c, 3) * 4); if (k <= 0) continue;
      const jx = x + jit(c, 4, 4), jy = y + jit(c, 5, 4); g.strokeStyle = INK; g.lineWidth = 1.6;
      if (kind === 0) rosette(g, jx, jy, 12, 4, hash(c, 6) > 0.5 ? RED : IND, YEL, hash(c, 7));
      else if (kind === 1) { g.fillStyle = GRN; for (const s of [-1, 1]) { g.beginPath(); g.ellipse(jx + s * 6, jy, 9, 3.6, s * 0.7, 0, TAU); g.fill(); } }
      else if (kind === 2) { for (let d = 0; d < 3; d++) disc(g, jx - 8 + d * 8, jy + (d % 2) * 4, 2.4, d === 1 ? RED : INK); }
      else { g.beginPath(); g.moveTo(jx - 9, jy + 4); g.lineTo(jx - 3, jy - 4); g.lineTo(jx + 3, jy + 4); g.lineTo(jx + 9, jy - 4); g.stroke(); }
    }
    for (let i = 0; i < 11; i++) {   // the peacock's tail: eleven feathers, each with an eye
      const a = -Math.PI * (0.96 - i * 0.092), col = [GRN, IND, RED][i % 3], L = 168, p = leaf(480, 266, L, 30, a);
      folkShape(g, p, { start: 0.7 + i * 0.07, dur: 0.5, fill: col, lw: 3.4, inner: 0.9, pattern: (c, bb) => lines(c, bb, a + 0.5, 6, 1.4, 'rgba(250,235,190,.7)') }, ts);
      if (prog(ts, 1.2 + i * 0.07, 0.2) > 0.5) { const ex = 480 + Math.cos(a) * L * 0.72, ey = 266 + Math.sin(a) * L * 0.72; disc(g, ex, ey, 16, YEL, 2); disc(g, ex, ey, 10, RED); disc(g, ex, ey, 5, IND); }
    }
    folkShape(g, leaf(480, 266, 140, 30, -Math.PI / 2), { start: 1.5, dur: 0.5, fill: IND, lw: 3.6, inner: 0.9, pattern: (c, bb) => dots(c, bb, 9, 1.8, YEL) }, ts);
    if (prog(ts, 1.9, 0.3) > 0.3) { disc(g, 480, 118, 18, IND, 3); g.strokeStyle = INK; g.lineWidth = 2.4; for (const s of [-1, 0, 1]) { g.beginPath(); g.moveTo(480 + s * 5, 101); g.lineTo(480 + s * 13, 84); g.stroke(); disc(g, 480 + s * 13, 82, 3.4, RED); } disc(g, 472, 116, 3.4, '#fff'); }
    for (const [i, L, col, st] of [[0, 150, RED, 2.0], [1, 114, YEL, 2.25], [2, 76, GRN, 2.5]]) {   // the lotus: three rings of petals
      const n = 7 - i * 2; for (let j = 0; j < n; j++) { const a = -Math.PI * (0.94 - (j + 0.5 * (i % 2)) * (0.88 / (n - 1 + (i % 2) * 0.01))); folkShape(g, leaf(480, 464, L, 26 - i * 4, a), { start: st + j * 0.05, dur: 0.45, fill: col, lw: 3.4, inner: 0.88, pattern: (c, bb) => lines(c, bb, a, 5, 1.4, i === 1 ? RED : INK) }, ts); }
    }
    for (const [cx, dir, col, col2, st] of [[232, 1, RED, YEL, 2.6], [728, -1, YEL, RED, 2.9]]) {
      folkShape(g, leaf(cx - 40 * dir, 318, 70, 16, dir > 0 ? -1.0 : -2.14), { start: st, dur: 0.4, fill: GRN, lw: 3, pattern: (c, bb) => lines(c, bb, 0.9, 5, 1.2, INK) }, ts);
      for (let w = 0; w < 3; w++) { g.strokeStyle = IND; g.lineWidth = 3; strokePart(g, Array.from({ length: 20 }, (_, i) => [cx - 150 + i * 15.8, 418 + w * 14 + Math.sin(i * 1.2 + w) * 4]), prog(ts, st + 0.4, 0.5), 0, 0); }   // water under the fish
      folkShape(g, fish(cx, 348, 140, 76, dir), { start: st, dur: 0.7, fill: col, lw: 4.4, inner: 0.9, pattern: (c, bb) => { scales(c, bb, 11, col2, 2.4); dots(c, bb, 16, 1.6, INK); } }, ts);
      if (prog(ts, st + 0.6, 0.3) > 0.4) { disc(g, cx + 76 * dir, 340, 14, '#fff', 3); disc(g, cx + 76 * dir, 340, 6.5, INK); }
    }
    for (const [x, c1, st] of [[170, RED, 3.2], [790, IND, 3.4]]) {   // two big flowers on stems, with leaves, fill the upper corners
      if (prog(ts, st, 0.3) > 0) { g.strokeStyle = INK; g.lineWidth = 3; strokePart(g, [[x, 232], [x + 4, 270], [x - 2, 310]], 1); for (const s of [-1, 1]) folkShape(g, leaf(x, 262, 60, 13, s > 0 ? 0.5 : Math.PI - 0.5), { start: st, dur: 0.3, fill: GRN, lw: 3, pattern: (c, bb) => lines(c, bb, 0, 5, 1.2, INK) }, ts); rosette(g, x, 175, 56, 8, c1, YEL, 0.2); }
    }
    speckle(g, W, H, 9, 40, [120, 80, 40]);
  } },
  warli: { kind: '2d', fps: 8, draw(g, t, W, H) {
    // white on a mud-wall red: a spiral of stick-limbed figures dancing hand in hand round a tarpa player, a sun, trees, and a chain of diamonds along the edge
    const ts = held(t, 8), step = frameOf(t, 4) % 2, spin = ts * 0.3, cx = 480, cy = 288;
    bg(g, W, H, '#9b4a2d');
    for (let i = 0; i < 16; i++) { const b = g.createRadialGradient(hash(i, 1) * W, hash(i, 2) * H, 10, hash(i, 1) * W, hash(i, 2) * H, 120 + hash(i, 3) * 160); b.addColorStop(0, i % 2 ? 'rgba(190,100,60,.28)' : 'rgba(70,24,12,.3)'); b.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = b; g.fillRect(0, 0, W, H); }   // a daubed mud wall
    speckle(g, W, H, 5, 60, [235, 190, 150]);
    g.strokeStyle = WHITE; g.lineWidth = 2.4; g.lineJoin = 'round';
    for (const y of [26, H - 26]) { const n = 36, k = prog(ts, 0, 1); for (let i = 0; i < n * k; i++) { const x = 30 + i * ((W - 60) / n); g.beginPath(); g.moveTo(x, y); g.lineTo(x + 13, y - 10); g.lineTo(x + 26, y); g.lineTo(x + 13, y + 10); g.closePath(); g.stroke(); } }
    g.beginPath(); for (const y of [48, H - 48]) { g.moveTo(30, y); g.lineTo(W - 30, y); } g.stroke();
    const sun = prog(ts, 0.1, 0.8); g.lineWidth = 3; strokePart(g, circlePts(140, 120, 30, 28), sun); for (let i = 0; i < 14 * sun; i++) { const a = (i / 14) * TAU; g.beginPath(); g.moveTo(140 + Math.cos(a) * 40, 120 + Math.sin(a) * 40); g.lineTo(140 + Math.cos(a) * 56, 120 + Math.sin(a) * 56); g.stroke(); }
    warliTree(g, 860, 440, 1.2, prog(ts, 1.8, 1.2)); warliTree(g, 100, 440, 0.9, prog(ts, 2.4, 1.2));
    for (const [hx, st] of [[230, 3.0], [730, 3.3]]) { const k = prog(ts, st, 0.6); if (k > 0) { g.lineWidth = 3; strokePart(g, [[hx - 34, 440], [hx - 34, 400], [hx, 372], [hx + 34, 400], [hx + 34, 440], [hx - 34, 440]], k); strokePart(g, [[hx - 8, 440], [hx - 8, 414], [hx + 8, 414], [hx + 8, 440]], k); } }   // two huts
    for (let i = 0; i < 22; i++) {   // the dance: one spiral, eleven figures to a turn, heads outward, hands joined
      if (prog(ts, 0.3 + i * 0.07, 0.1) <= 0) continue;
      const a = (i * TAU) / 11 + spin, r = 78 + i * 4.2, s = 9 + r * 0.06;
      warliFigure(g, cx + Math.cos(a) * r, cy + Math.sin(a) * r, s, a + Math.PI / 2, (step + i) % 2, s * 1.45);
    }
    if (prog(ts, 0.1, 0.4) > 0) { warliFigure(g, cx, cy + 6, 14, 0, step, 14); g.beginPath(); g.moveTo(cx + 30, cy - 6); g.lineTo(cx + 78, cy - 30); g.lineTo(cx + 78, cy + 14); g.closePath(); g.stroke(); g.beginPath(); g.arc(cx + 82, cy - 8, 4, 0, TAU); g.fill(); }   // the tarpa: a gourd horn
  } },
  pattachitra: { kind: '2d', fps: 8, draw(g, t, W, H) {
    // a flat ochre ground, a thick ornamental border, bold black outlines, a fish with an almond eye in profile, and flowers and tendrils packed in round it
    const ts = held(t, 8), f = frameOf(t, 8), RED = '#a8281f', CRM = '#f7e8c6', GRN = '#2f7d3b', k0 = easeOut(prog(ts, 0, 0.8));
    bg(g, W, H, '#e8ad44'); g.lineCap = 'round'; g.lineJoin = 'round';
    for (let y = 90, r = 0; y < H - 80; y += 62, r++) for (let x = 96 + (r % 2) * 40; x < W - 80; x += 80) {   // the ground: rosettes, leaf pairs and tendrils on a grid, offset every other row
      const c = r * 20 + Math.floor(x / 80), k = prog(ts, 0.4 + hash(c, 1) * 2.4, 0.15); if (k <= 0) continue; g.strokeStyle = INK; g.lineWidth = 2.4;
      if (hash(c, 2) > 0.45) { rosette(g, x, y, 26, 6, hash(c, 3) > 0.5 ? RED : CRM, '#f6d160', hash(c, 4)); g.beginPath(); g.arc(x, y, 26 * 0.9, 0, TAU); g.stroke(); }
      else { strokePart(g, curl(x, y, 22, 2.2, hash(c, 5) > 0.5 ? 1 : -1), 1); for (const d of [-1, 1]) { g.fillStyle = GRN; g.beginPath(); g.ellipse(x + d * 26, y + 18, 16, 6, d * -0.5, 0, TAU); g.fill(); g.stroke(); } }
    }
    g.fillStyle = RED; g.beginPath(); g.rect(0, 0, W, H); g.rect(46, 46, W - 92, H - 92); g.globalAlpha = k0; g.fill('evenodd'); g.globalAlpha = 1;   // the thick red border
    g.fillStyle = '#f6d160'; g.beginPath(); g.rect(46, 46, W - 92, H - 92); g.rect(68, 68, W - 136, H - 136); g.globalAlpha = k0; g.fill('evenodd'); g.globalAlpha = 1;
    g.strokeStyle = INK; for (const [ins, w] of [[3, 3], [46, 5], [68, 5]]) { g.lineWidth = w; g.strokeRect(ins, ins, W - 2 * ins, H - 2 * ins); }
    for (let i = 0; i < 80 * k0; i++) { const per = 2 * (W - 40) + 2 * (H - 40), d = (i / 80) * per, side = d < W - 40 ? 0 : d < W - 40 + H - 40 ? 1 : d < 2 * (W - 40) + H - 40 ? 2 : 3; let x, y; if (side === 0) { x = 20 + d; y = 24; } else if (side === 1) { x = W - 24; y = 20 + d - (W - 40); } else if (side === 2) { x = W - 20 - (d - (W - 40) - (H - 40)); y = H - 24; } else { x = 24; y = H - 20 - (d - 2 * (W - 40) - (H - 40)); } disc(g, x, y, 6, CRM, 2); }
    g.strokeStyle = INK; g.lineWidth = 2.4; for (let i = 0; i < 60 * k0; i++) { const x = 90 + i * ((W - 180) / 60); strokePart(g, [[x, 52], [x + 7, 62], [x + 14, 52]], 1); strokePart(g, [[x, H - 52], [x + 7, H - 62], [x + 14, H - 52]], 1); }
    const A = -0.1, cx = 480, cy = 282, fp = fish(cx, cy, 238, 120, 1, A);
    folkShape(g, closed([[-0.6, 0.08], [-0.45, -0.5], [-0.05, -0.95], [0.4, -0.75], [0.72, -0.3], [0.7, 0.1]], 6).map(([x, y]) => [cx + x * 120 - 20, cy - 52 + y * 105]), { start: 1.5, dur: 0.5, fill: RED, lw: 6, pattern: (c, bb) => lines(c, bb, Math.PI / 2 + 0.3, 8, 2.4, INK) }, ts);   // dorsal fin
    folkShape(g, closed([[0, 0], [-0.35, 0.65], [0.3, 1], [0.7, 0.35]], 6).map(([x, y]) => [cx - 10 + x * 90, cy + 40 + y * 80]), { start: 1.7, dur: 0.4, fill: GRN, lw: 6, pattern: (c, bb) => lines(c, bb, 1.2, 8, 2.4, INK) }, ts);   // pectoral fin
    folkShape(g, fp, { start: 0.9, dur: 1.2, fill: CRM, lw: 8, pattern: (c, bb) => { scales(c, bb, 20, RED, 3.6); lines(c, [bb[0], bb[1], bb[0] + 100, bb[3]], Math.PI / 2, 10, 4, RED); dots(c, [bb[0] + 110, cy - 34, bb[2] - 40, cy + 34], 14, 2.6, INK); } }, ts);
    if (prog(ts, 2.4, 0.4) > 0.4) {
      const ex = cx + 140, ey = cy - 18, eye = closed([[-1, 0], [0, -0.6], [1, 0], [0, 0.6]], 6).map(([x, y]) => [ex + x * 38, ey + y * 24]);
      g.fillStyle = '#fff'; g.beginPath(); eye.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.fill(); g.strokeStyle = INK; g.lineWidth = 5; g.stroke(); disc(g, ex + 4, ey, 11, INK);
      g.lineWidth = 4; strokePart(g, spline([[cx + 70, cy - 70], [cx + 95, cy], [cx + 70, cy + 70]], 8), 1); strokePart(g, spline([[cx + 40, cy - 66], [cx + 62, cy], [cx + 40, cy + 66]], 8), 1);   // the gill lines
    }
    speckle(g, W, H, 6, 45, [110, 70, 20]);
  } },
  gond: { kind: '2d', fps: 8, draw(g, t, W, H) {
    // a bold bird and a tree on a plain light ground: every part is solid colour in bands, each band carrying one colour of fine marks, the tree's branches curling in toward the bird
    const ts = held(t, 8); bg(g, W, H, '#f6ecd0'); g.lineCap = 'round'; g.lineJoin = 'round';
    const k0 = prog(ts, 0, 0.8); g.strokeStyle = INK; g.lineWidth = 3; strokePart(g, [[16, 16], [W - 16, 16], [W - 16, H - 16], [16, H - 16], [16, 16]], k0); g.lineWidth = 1.6; strokePart(g, [[24, 24], [W - 24, 24], [W - 24, H - 24], [24, H - 24], [24, 24]], k0);
    g.fillStyle = INK; for (let i = 0; i < 60 * k0; i++) { const x = 40 + i * ((W - 80) / 60); for (const y of [34, H - 34]) { g.beginPath(); g.arc(x, y, 2.4, 0, TAU); g.fill(); } }
    const shape = (pts, st, ang, seed, lw = 3.4) => folkShape(g, pts, { start: st, dur: 0.6, fill: INK, lw, pattern: (c, bb) => gondBands(c, bb, ang, seed) }, ts);
    for (let i = 0; i < 3; i++) shape(leaf(470, 305, 200, 36, -0.4 + i * 0.4), 1.0 + i * 0.12, -0.4 + i * 0.4, i + 1);   // tail
    shape(ellipseLine(340, 308, 170, 98, -0.1), 0.2, -0.1, 0);   // body
    shape(leaf(250, 292, 130, 38, -2.45), 0.7, -2.45, 2);   // neck
    shape(ellipseLine(205, 205, 42, 38), 0.9, 0.4, 5);   // head
    for (let i = 0; i < 5; i++) { const a = -1.57 + (i - 2) * 0.34; shape(leaf(205 + (i - 2) * 6, 172, 58 - Math.abs(i - 2) * 6, 11, a), 1.4 + i * 0.05, a, i + 1, 3); }   // a bold crest
    shape(closed([[0, 0], [1, 0.25], [0, 0.5]], 4).map(([x, y]) => [172 - x * 64, 200 + y * 24]), 1.4, 0, 3, 3);   // beak
    if (prog(ts, 1.6, 0.2) > 0.5) { disc(g, 208, 198, 13, '#f6f0dc', 2.6); disc(g, 208, 198, 9, '#b3182a', 1.6); disc(g, 208, 198, 4.4, INK); g.fillStyle = INK; for (let i = 0; i < 10; i++) { const a = (i / 10) * TAU; g.beginPath(); g.arc(208 + Math.cos(a) * 18, 198 + Math.sin(a) * 18, 1.8, 0, TAU); g.fill(); } }   // a decorated eye
    for (const [x, st] of [[300, 1.8], [372, 1.9]]) { g.strokeStyle = INK; g.lineWidth = 5; strokePart(g, [[x, 395], [x - 8, 440], [x - 24, 478]], prog(ts, st, 0.4)); g.fillStyle = '#b3182a'; for (let i = 0; i < 6 * prog(ts, st + 0.2, 0.4); i++) { g.beginPath(); g.arc(x + 10 - i * 4.4, 414 + i * 11, 2.6, 0, TAU); g.fill(); } }
    shape(ribbon([[822, 492], [812, 410], [826, 310], [812, 215]], 24, 9), 1.9, -1.57, 6);   // the trunk
    shape(ribbon([[816, 340], [750, 318], [690, 282], [640, 262], [600, 268], [588, 292], [608, 306], [626, 292]], 13, 4), 2.3, -0.5, 1);   // a branch that curls in over the tail
    shape(ribbon([[820, 425], [750, 424], [680, 408], [630, 392], [596, 404], [596, 428], [618, 430]], 12, 4), 2.5, -0.2, 4);   // and one that curls in under it
    for (const [x, y, a, st] of [[820, 250, -2.3, 2.7], [820, 250, -0.8, 2.75], [815, 330, -2.2, 2.8], [822, 380, -0.9, 2.85], [800, 215, -1.57, 2.9]]) shape(leaf(x, y, 80, 16, a), st, a, (x + y) % 5, 3);
    const sun = prog(ts, 0.1, 0.8); shape(ellipseLine(112, 100, 40, 40), 0.1, 0.3, 3);
    g.fillStyle = INK; for (const r of [54, 64]) for (let i = 0; i < 16 * sun; i++) { const a = (i / 16) * TAU + (r > 58 ? 0.2 : 0); g.beginPath(); g.arc(112 + Math.cos(a) * r, 100 + Math.sin(a) * r, 2.8, 0, TAU); g.fill(); }
    speckle(g, W, H, 8, 40, [140, 100, 60]);
  } },
  'indian-miniature': { kind: '2d', fps: 8, draw(g, t, W, H) {
    // a palace terrace in flat colour and jewel tones: a gold border with a floral margin, a pavilion with domes, a garden and a channel seen from above, two figures in profile on a rug
    const ts = held(t, 8), RUBY = '#a81f35', EMER = '#1f6a4a', LAP = '#27408b', GOLD = '#d6a21f', PINK = '#e7a79c', CREAM = '#f4e4c1';
    bg(g, W, H, GOLD); const k0 = easeOut(prog(ts, 0, 0.6)); g.lineJoin = 'round'; g.lineCap = 'round';
    g.fillStyle = RUBY; g.fillRect(24, 24, W - 48, H - 48); g.strokeStyle = INK; g.lineWidth = 1.6; g.strokeRect(24, 24, W - 48, H - 48); g.strokeRect(58, 58, W - 116, H - 116);
    for (let i = 0; i < 36 * k0; i++) { const x = 40 + i * ((W - 80) / 35); for (const y of [41, H - 41]) { rosette(g, x, y, 11, 5, GOLD, CREAM, i); g.fillStyle = EMER; g.beginPath(); g.ellipse(x + 13, y, 6, 2.6, 0, 0, TAU); g.fill(); } }
    for (let i = 0; i < 18 * k0; i++) { const y = 70 + i * ((H - 140) / 17); for (const x of [41, W - 41]) rosette(g, x, y, 11, 5, GOLD, CREAM, i); }
    g.save(); g.beginPath(); g.rect(62, 62, W - 124, H - 124); g.clip(); g.fillStyle = CREAM; g.fillRect(62, 62, W - 124, H - 124);
    const sk = g.createLinearGradient(0, 62, 0, 210); sk.addColorStop(0, '#f2c98a'); sk.addColorStop(1, '#fbecd0'); g.fillStyle = sk; g.fillRect(62, 62, W - 124, 150);
    for (let i = 0; i < 3; i++) { g.strokeStyle = i % 2 ? GOLD : '#fff'; g.lineWidth = 4; strokePart(g, Array.from({ length: 30 }, (_, j) => [62 + j * 31, 90 + i * 34 + Math.sin(j * 0.7 + i * 2 + ts * 0.8) * 7]), prog(ts, 0.4 + i * 0.1, 0.5)); }   // gold cloud ribbons, drifting
    disc(g, 150, 126, 24, GOLD, 1.6); for (let i = 0; i < 12; i++) { const a = (i / 12) * TAU; g.strokeStyle = GOLD; g.lineWidth = 3; g.beginPath(); g.moveTo(150 + Math.cos(a) * 32, 126 + Math.sin(a) * 32); g.lineTo(150 + Math.cos(a) * 44, 126 + Math.sin(a) * 44); g.stroke(); }
    const pk = prog(ts, 0.8, 1.0);
    if (pk > 0) {
      g.fillStyle = PINK; g.fillRect(62, 205, W - 124, 98); g.fillStyle = '#d9867c'; for (let x = 62; x < W - 62; x += 22) g.fillRect(x, 193, 12, 13);
      g.fillStyle = LAP; for (let x = 80; x < W - 80; x += 56) { g.beginPath(); g.moveTo(x - 12, 280); g.lineTo(x - 12, 244); g.arc(x, 244, 12, Math.PI, 0); g.lineTo(x + 12, 280); g.fill(); }
      g.fillStyle = '#e0a090'; g.fillRect(330, 150, 300, 154); g.strokeStyle = GOLD; g.lineWidth = 4; g.strokeRect(330, 150, 300, 154);
      for (const x of [400, 480, 560]) { g.fillStyle = LAP; g.beginPath(); g.moveTo(x - 30, 300); g.lineTo(x - 30, 215); g.arc(x, 215, 30, Math.PI, 0); g.lineTo(x + 30, 300); g.fill(); g.stroke(); g.fillStyle = RUBY; g.fillRect(x - 12, 262, 24, 38); }
      for (const [dx, dy, rx, ry, st] of [[480, 148, 76, 58, 1.0], [250, 152, 40, 32, 1.3], [710, 152, 40, 32, 1.3]]) { if (prog(ts, st, 0.5) <= 0) continue; g.fillStyle = GOLD; g.beginPath(); g.ellipse(dx, dy, rx, ry, 0, Math.PI, TAU); g.fill(); g.strokeStyle = INK; g.lineWidth = 1.6; g.stroke(); g.beginPath(); for (let i = -2; i <= 2; i++) { g.moveTo(dx, dy - ry); g.quadraticCurveTo(dx + i * rx * 0.55, dy - ry * 0.6, dx + i * rx * 0.45, dy); } g.stroke(); g.beginPath(); g.moveTo(dx, dy - ry); g.lineTo(dx, dy - ry - 22); g.stroke(); disc(g, dx, dy - ry - 22, 4, RUBY, 1.4); }
      for (const x of [250, 710]) { g.fillStyle = GOLD; g.fillRect(x - 40, 183, 80, 10); g.strokeStyle = INK; g.lineWidth = 3; g.beginPath(); for (const dx of [-30, -10, 10, 30]) { g.moveTo(x + dx, 183); g.lineTo(x + dx, 152); } g.stroke(); }
    }
    const gk = prog(ts, 1.8, 0.8);
    if (gk > 0) {
      g.fillStyle = EMER; g.fillRect(62, 303, W - 124, H - 365); g.strokeStyle = GOLD; g.lineWidth = 3; g.strokeRect(62, 303, W - 124, 4);
      for (let r = 0; r < 4; r++) for (let c = 0; c < 6; c++) { const x = 90 + c * 64 + (c > 2 ? 360 : 0), y = 320 + r * 36; if (c > 2 && r < 1) continue; g.fillStyle = '#2f8a5a'; g.fillRect(x, y, 54, 28); g.strokeStyle = GOLD; g.lineWidth = 1.4; g.strokeRect(x, y, 54, 28); for (let i = 0; i < 5; i++) disc(g, x + 8 + i * 9.5, y + 14 + (i % 2) * 5 - 2, 2.6, [RUBY, '#f0b429', '#f4e4c1'][(i + r + c) % 3]); }
    }
    if (prog(ts, 2.4, 0.6) > 0) { g.fillStyle = LAP; polyFill(g, [[440, 304], [520, 304], [570, H - 62], [390, H - 62]]); g.strokeStyle = '#fff'; g.lineWidth = 1.6; for (let i = 0; i < 6; i++) strokePart(g, Array.from({ length: 12 }, (_, j) => [412 + j * 12 + i * 4, 320 + i * 26 + Math.sin(j * 1.3 + ts * 2) * 3]), 1); for (let i = 0; i < 9; i++) disc(g, 480 + Math.sin(i * 2) * 8, 400 - ((ts * 40 + i * 14) % 90), 2, '#dff0ff'); }   // the channel, with a fountain
    for (const [x, y, st] of [[120, 380, 2.6], [190, 395, 2.7], [860, 385, 2.8]]) { if (prog(ts, st, 0.4) <= 0) continue; g.fillStyle = '#14472f'; g.beginPath(); g.moveTo(x, y - 110); g.quadraticCurveTo(x + 30, y - 30, x + 20, y); g.lineTo(x - 20, y); g.quadraticCurveTo(x - 30, y - 30, x, y - 110); g.fill(); dots(g, [x - 14, y - 90, x + 14, y - 4], 11, 1.6, GOLD); g.fillStyle = '#5b3a1e'; g.fillRect(x - 3, y, 6, 14); }
    if (prog(ts, 3.0, 0.5) > 0) {
      g.fillStyle = RUBY; g.fillRect(600, 384, 240, 66); g.strokeStyle = GOLD; g.lineWidth = 4; g.strokeRect(604, 388, 232, 58); dots(g, [612, 396, 828, 440], 18, 2.2, GOLD);
      const seated = (x, y, dir, robe, turb) => { g.fillStyle = robe; polyFill(g, [[x - 34, y], [x + 34, y], [x + 26, y - 30], [x + 14, y - 62], [x - 14, y - 62], [x - 26, y - 30]]); g.strokeStyle = INK; g.lineWidth = 1.6; g.stroke(); g.fillStyle = GOLD; g.fillRect(x - 24, y - 34, 48, 5); disc(g, x + dir * 4, y - 78, 13, '#e8b98a', 1.6); polyFill(g, [[x + dir * 16, y - 80], [x + dir * 24, y - 75], [x + dir * 16, y - 72]]); g.fillStyle = turb; g.beginPath(); g.ellipse(x + dir * 2, y - 92, 18, 10, 0, 0, TAU); g.fill(); g.stroke(); disc(g, x + dir * 9, y - 80, 2.2, INK); g.strokeStyle = INK; g.lineWidth = 3; strokePart(g, [[x + dir * 8, y - 56], [x + dir * 34, y - 44]], 1); disc(g, x + dir * 38, y - 44, 5, GOLD, 1.4); };
      seated(680, 424, 1, EMER, '#f0b429'); seated(770, 424, -1, LAP, RUBY);
    }
    for (let i = 0; i < 3; i++) { const x = 90 + ((ts * 38 + i * 260) % (W - 200)), y = 96 + i * 26 + Math.sin(ts * 2 + i) * 6; g.strokeStyle = INK; g.lineWidth = 2.2; strokePart(g, [[x - 10, y - 5], [x, y], [x + 10, y - 5]], prog(ts, 3.4, 0.3)); }
    g.restore(); speckle(g, W, H, 3, 34, [110, 70, 30]);
  } },
  engraving: { kind: '2d', fps: null, draw(g, t, W, H) {
    // a banknote-style engraving: a sphere cut in fine lines that follow its form and swell in the shadow, cross-hatched where it is darkest, in a vignette of waves inside a woven guilloche frame; two inks on cream
    const PAPER = '#f1ead6', I1 = '#20170e', I2 = '#7d1d2c', cx = 480, cy = 276, R = 120, tilt = 0.38; bg(g, W, H, PAPER); g.lineCap = 'butt'; g.lineJoin = 'round';
    g.save(); g.beginPath(); g.ellipse(cx, cy, 332, 208, 0, 0, TAU); g.clip(); g.strokeStyle = I2;
    for (let y = cy - 212, i = 0; y < cy + 212; y += 4.4, i++) { const e = (y - cy) / 208; g.lineWidth = 0.5 + 1.9 * e * e; strokePart(g, Array.from({ length: 58 }, (_, j) => [cx - 340 + j * 12, y + 2.6 * Math.sin(j * 0.26 + y / 23)]), prog(t, i * 0.005, 0.7)); }
    g.restore();
    g.strokeStyle = I1; g.lineWidth = 0.8; g.save(); g.beginPath(); g.ellipse(cx + 40, cy + R * 0.96, 150, 20, 0, 0, TAU); g.clip(); for (let y = cy + R * 0.7; y < cy + R * 1.3; y += 3) { g.beginPath(); g.moveTo(cx - 140, y); g.lineTo(cx + 230, y); g.stroke(); } g.restore();   // the cast shadow, ruled
    g.fillStyle = PAPER; g.beginPath(); g.arc(cx, cy, R + 4, 0, TAU); g.fill();
    const N = 30, M = 48;
    for (let i = 0; i < N; i++) {   // lines of latitude, drawn one after another; each segment is wider the darker the sphere is there
      const phi = -Math.PI / 2 + ((i + 0.5) / N) * Math.PI, shown = Math.floor(M * prog(t, 0.25 + i * 0.045, 0.5));
      for (let j = 0; j < shown; j++) { const a = spherePoint(phi, -Math.PI / 2 + (j / M) * Math.PI, R, cx, cy, tilt), b = spherePoint(phi, -Math.PI / 2 + ((j + 1) / M) * Math.PI, R, cx, cy, tilt); if (!a.vis || !b.vis) continue; g.lineWidth = 0.35 + 3.3 * (1 - (a.shade + b.shade) / 2) ** 1.7; g.beginPath(); g.moveTo(a.x, a.y); g.lineTo(b.x, b.y); g.stroke(); }
    }
    g.globalAlpha = prog(t, 2.6, 1); g.lineWidth = 0.7;
    for (let j = 0; j < 28; j++) { const lam = -Math.PI / 2 + ((j + 0.5) / 28) * Math.PI; for (let i = 0; i < 40; i++) { const a = spherePoint(-Math.PI / 2 + (i / 40) * Math.PI, lam, R, cx, cy, tilt), b = spherePoint(-Math.PI / 2 + ((i + 1) / 40) * Math.PI, lam, R, cx, cy, tilt); if (a.vis && b.vis && a.shade < 0.4 && b.shade < 0.4) { g.beginPath(); g.moveTo(a.x, a.y); g.lineTo(b.x, b.y); g.stroke(); } } }   // cross-hatching in the deepest shade
    g.globalAlpha = 1; g.lineCap = 'round';
    const kf = prog(t, 0.2, 1.4); g.strokeStyle = I2; for (const [ins, w] of [[12, 2.6], [18, 0.8], [54, 0.8], [60, 2.6]]) { g.lineWidth = w; strokePart(g, [[ins, ins], [W - ins, ins], [W - ins, H - ins], [ins, H - ins], [ins, ins]], kf); }
    g.lineWidth = 0.9;
    for (let p = 0; p < 6; p++) { const ph = (p * TAU) / 6; strokePart(g, Array.from({ length: 150 }, (_, i) => [74 + i * ((W - 148) / 149), 36 + 9 * Math.sin(i * 0.3 + ph)]), kf); strokePart(g, Array.from({ length: 150 }, (_, i) => [74 + i * ((W - 148) / 149), H - 36 + 9 * Math.sin(i * 0.3 + ph)]), kf); strokePart(g, Array.from({ length: 80 }, (_, i) => [36 + 9 * Math.sin(i * 0.3 + ph), 74 + i * ((H - 148) / 79)]), kf); strokePart(g, Array.from({ length: 80 }, (_, i) => [W - 36 + 9 * Math.sin(i * 0.3 + ph), 74 + i * ((H - 148) / 79)]), kf); }
    for (const [x, y] of [[36, 36], [W - 36, 36], [36, H - 36], [W - 36, H - 36]]) for (let c = 0; c < 4; c++) { g.strokeStyle = c % 2 ? I1 : I2; strokePart(g, Array.from({ length: 80 }, (_, i) => { const a = (i / 79) * TAU, r = 21 * (0.55 + 0.45 * Math.cos(7 * a + c * 0.45)); return [x + Math.cos(a + c * 0.2) * r, y + Math.sin(a + c * 0.2) * r]; }), kf); }
  } },
  silkscreen: { kind: '2d', fps: 8, draw(g, t, W, H) {
    // a poster in three flat inks that overprint: yellow, red and blue, each a little out of register, with halftone dots for the sky and the glow
    const ts = held(t, 8), f = frameOf(t, 8); bg(g, W, H, '#f3ecd9');
    inkLayer(g, '#f7c600', 0.2, ts, f, [0, 0, 0, -40], () => { g.beginPath(); g.arc(480, 250, 132, 0, TAU); g.fill(); halftone(g, [0, 0, W, 300], 9, 0.26, (x, y) => (y / 300) * 0.95); });
    inkLayer(g, '#e5314f', 1.2, ts, f, [4, -3, -40, 0], () => { halftone(g, [250, 70, 710, 430], 8, 0.78, (x, y) => { const d = Math.hypot(x - 480, y - 250); return d < 140 ? 0 : 1 - (d - 140) / 70; }); polyFill(g, [[0, 440], [0, 250], [150, 170], [310, 340], [400, 440]]); g.fillRect(0, H - 58, W, 16); });
    inkLayer(g, '#1d3b8f', 2.2, ts, f, [-3, 4, 40, 0], () => {
      polyFill(g, [[300, H], [560, 300], [700, 236], [960, 372], [960, H]]); for (const [x, y, w] of [[50, 60, 210], [50, 86, 140], [50, 112, 180]]) g.fillRect(x, y, w, 15);
      g.lineWidth = 7; g.lineCap = 'round'; g.strokeStyle = '#1d3b8f'; for (const [bx, by, sc] of [[700, 120, 1], [770, 90, 0.6], [640, 70, 0.5]]) { g.beginPath(); g.moveTo(bx - 40 * sc, by + 14 * sc); g.quadraticCurveTo(bx - 18 * sc, by - 18 * sc, bx, by + 4 * sc); g.quadraticCurveTo(bx + 18 * sc, by - 18 * sc, bx + 40 * sc, by + 14 * sc); g.stroke(); }
    });
    speckle(g, W, H, 7, 70, [90, 70, 40]);
  } },
  'art-deco': { kind: '2d', fps: null, draw(g, t, W, H) {
    // symmetric and stepped: a gold sunburst over burgundy wedges, fan arcs, a stepped tower with a spire, and zigzag borders, on a deep navy ground
    const GOLD = '#d9ad4f', LIGHT = '#f3dc92', WINE = '#5e1426', NAVY = '#0b1226', cx = 480, cy = 530; bg(g, W, H, NAVY); g.lineCap = 'round'; g.lineJoin = 'miter';
    const n = 28; for (let i = 0; i < n; i++) {   // the sunburst: wedges alternate burgundy and navy, each edge a gold line that grows out from the centre
      const a0 = Math.PI + (i * Math.PI) / n, a1 = a0 + Math.PI / n, r = 900 * easeOut(prog(t, 0.1 + i * 0.03, 0.9));
      if (i % 2) { g.fillStyle = WINE; g.beginPath(); g.moveTo(cx, cy); g.arc(cx, cy, r, a0, a1); g.closePath(); g.fill(); }
      g.strokeStyle = GOLD; g.lineWidth = 2.2; g.beginPath(); g.moveTo(cx, cy); g.lineTo(cx + Math.cos(a0) * r, cy + Math.sin(a0) * r); g.stroke();
    }
    for (const [r, w] of [[130, 4], [200, 2.4], [280, 2.4], [360, 4], [440, 2.4]]) { g.strokeStyle = r === 130 || r === 360 ? LIGHT : GOLD; g.lineWidth = w; g.beginPath(); g.arc(cx, cy, r, Math.PI, Math.PI + Math.PI * easeInOut(prog(t, 0.5 + r / 500, 1.2))); g.stroke(); }
    g.strokeStyle = GOLD; g.lineWidth = 1.6; for (let ring = 0; ring < 3; ring++) for (let i = 0; i < 9 - ring; i++) { const r = 165 + ring * 40, a = Math.PI + ((i + 0.5) / (9 - ring)) * Math.PI; if (prog(t, 1.4 + ring * 0.2, 0.8) > i / 9) { g.beginPath(); g.arc(cx + Math.cos(a) * r, cy + Math.sin(a) * r, 18, a - 1.57, a + 1.57); g.stroke(); } }   // fan scallops
    const tk = easeOut(prog(t, 1.2, 1.3));   // the tower rises in steps, symmetric about the middle
    const steps = [[84, 520], [66, 440], [48, 370], [32, 310], [16, 250], [5, 196]]; g.fillStyle = NAVY; g.strokeStyle = LIGHT; g.lineWidth = 3;
    steps.forEach(([hw, top], i) => { const y = lerp(H, top, tk); g.fillRect(cx - hw, y, hw * 2, H - y); g.strokeRect(cx - hw, y, hw * 2, H - y); });
    g.strokeStyle = GOLD; g.lineWidth = 1.6; for (const dx of [-60, -36, -12, 12, 36, 60]) { g.beginPath(); g.moveTo(cx + dx, H); g.lineTo(cx + dx, lerp(H, 470, tk)); g.stroke(); }
    for (const side of [-1, 1]) { g.save(); g.translate(cx, 0); g.scale(side, 1); const k = prog(t, 0.3, 1.5);   // zigzag borders and stepped side frames, mirrored
      g.strokeStyle = GOLD; g.lineWidth = 2.4; strokePart(g, Array.from({ length: 24 }, (_, i) => [i * 20, 24 + (i % 2) * 18]), k); strokePart(g, Array.from({ length: 24 }, (_, i) => [i * 20, H - 24 - (i % 2) * 18]), k);
      for (let i = 0; i < 4; i++) strokePart(g, [[400 - i * 26, H], [400 - i * 26, 120 + i * 40], [374 - i * 26, 120 + i * 40]], prog(t, 0.6 + i * 0.2, 0.8));
      g.restore(); }
    for (let i = 0; i < 6; i++) { const x = 60 + i * 168 + (i % 2) * 20, y = 90 + (i % 3) * 40, k = (Math.sin(t * 2.4 + i * 1.7) + 1) / 2, r = 5 + 8 * k; g.fillStyle = LIGHT; g.beginPath(); g.moveTo(x, y - r); g.lineTo(x + r * 0.28, y - r * 0.28); g.lineTo(x + r, y); g.lineTo(x + r * 0.28, y + r * 0.28); g.lineTo(x, y + r); g.lineTo(x - r * 0.28, y + r * 0.28); g.lineTo(x - r, y); g.lineTo(x - r * 0.28, y - r * 0.28); g.closePath(); g.fill(); }
  } },
  'stained-glass': { kind: '2d', fps: null, draw(g, t, W, H) {
    // a pointed window of coloured panes between thick lead lines, a rose at the top and a diamond lattice below, with light coming through and a slow beam of sun across the glass
    const COLS = ['#b3122b', '#1b3fa8', '#0a6a38', '#e8a317', '#6a2a9a', '#d9467a', '#e2641b'], x0 = 260, x1 = 700, yb = 512, ys = 250, cx = 480, cy = 236;
    bg(g, W, H, '#2a2622'); g.strokeStyle = 'rgba(0,0,0,.35)'; g.lineWidth = 2; g.beginPath(); for (let y = 20; y < H; y += 46) { g.moveTo(0, y); g.lineTo(W, y); for (let x = ((y / 46) % 2) * 40; x < W; x += 80) { g.moveTo(x, y); g.lineTo(x, y + 46); } } g.stroke();   // the stone wall
    const arch = () => { g.beginPath(); g.moveTo(x0, yb); g.lineTo(x0, ys); g.quadraticCurveTo(x0, 110, cx, 36); g.quadraticCurveTo(x1, 110, x1, ys); g.lineTo(x1, yb); g.closePath(); };
    const glow = g.createRadialGradient(cx, 260, 40, cx, 260, 360); glow.addColorStop(0, 'rgba(255,230,160,.35)'); glow.addColorStop(1, 'rgba(255,230,160,0)'); g.fillStyle = glow; g.fillRect(0, 0, W, H);
    g.save(); arch(); g.fillStyle = '#fff2c8'; g.fill(); g.clip();
    const panes = []; for (let row = -1; row < 7; row++) for (let c = -1; c < 7; c++) { const x = x0 + c * 74 + (row % 2 ? 37 : 0), y = 70 + row * 70; panes.push({ pts: [[x, y - 70], [x + 37, y], [x, y + 70], [x - 37, y]], x, y, col: COLS[Math.floor(hash(row + 9, c + 9, 1) * 7)] }); }
    const ring = (r0, r1, n, off, seed) => { for (let i = 0; i < n; i++) { const a0 = off + (i / n) * TAU, a1 = off + ((i + 1) / n) * TAU, am = (a0 + a1) / 2, pts = [[cx + Math.cos(a0) * r0, cy + Math.sin(a0) * r0], [cx + Math.cos(a0) * r1, cy + Math.sin(a0) * r1], [cx + Math.cos(am) * (r1 + 2), cy + Math.sin(am) * (r1 + 2)], [cx + Math.cos(a1) * r1, cy + Math.sin(a1) * r1], [cx + Math.cos(a1) * r0, cy + Math.sin(a1) * r0]]; panes.push({ pts, x: cx + Math.cos(am) * (r0 + r1) / 2, y: cy + Math.sin(am) * (r0 + r1) / 2, col: COLS[(i * 2 + seed + (i % 3)) % 7], round: true }); } };
    panes.push({ pts: circlePts(cx, cy, 134, 48), x: cx, y: cy, col: '#1a1620' }); ring(96, 134, 24, 0.1, 1); ring(62, 96, 16, 0, 3); ring(32, 62, 8, 0.2, 5); panes.push({ pts: circlePts(cx, cy, 32, 24), x: cx, y: cy, col: '#f5c518' });
    panes.forEach((p, i) => {
      const lit = prog(t, 0.1 + Math.hypot(p.x - cx, p.y - cy) / 900, 0.5); g.beginPath(); p.pts.forEach(([x, y], j) => (j ? g.lineTo(x, y) : g.moveTo(x, y))); g.closePath();
      g.fillStyle = lit < 1 ? '#1c1a22' : p.col; g.globalAlpha = 1; g.fill();
      if (lit > 0) { g.save(); g.clip(); g.globalAlpha = lit; g.fillStyle = p.col; g.fillRect(0, 0, W, H); const gl = g.createRadialGradient(p.x, p.y, 2, p.x, p.y, 52); gl.addColorStop(0, 'rgba(255,255,255,.1)'); gl.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gl; g.globalCompositeOperation = 'lighter'; g.fillRect(p.x - 60, p.y - 60, 120, 120); g.restore(); }
    });
    g.lineJoin = 'round'; g.strokeStyle = '#15131a'; g.lineWidth = 6; panes.forEach((p) => { g.beginPath(); p.pts.forEach(([x, y], j) => (j ? g.lineTo(x, y) : g.moveTo(x, y))); g.closePath(); g.stroke(); });
    const bx = lerp(x0 - 200, x1 + 200, (t * 0.18) % 1), bm = g.createLinearGradient(bx - 80, 0, bx + 80, 160); bm.addColorStop(0, 'rgba(255,240,190,0)'); bm.addColorStop(0.5, 'rgba(255,240,190,.38)'); bm.addColorStop(1, 'rgba(255,240,190,0)'); g.globalCompositeOperation = 'lighter'; g.fillStyle = bm; g.fillRect(x0, 0, x1 - x0, H); g.globalCompositeOperation = 'source-over';
    g.restore(); arch(); g.strokeStyle = '#3a342e'; g.lineWidth = 16; g.stroke(); g.strokeStyle = '#15131a'; g.lineWidth = 5; g.stroke();
  } },
};
export const IDS = Object.keys(LOOKS);
