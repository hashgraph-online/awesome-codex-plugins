// brief2mp4 art forms: looks-painted.js, batch 1 (painting and drawing). MIT. Its helpers (rgba, mix, poly, spline, at, bounds, tooth, speckle, flatShape, ...) are exported for the later looks files. Same rules as looks.js:
// every look is a pure function of time, nothing is read from a clock, and all roughness comes from hash().
// The helpers at the top are shared by the nine looks; the nine looks are registered in LOOKS below.
import { TAU, clamp, lerp, prog, easeOut, easeInOut, hash, frameOf, held, jit, grain, blob, cut, strokePart, circlePts, fill, bg, paper, FONT } from './looks.js';

export const rgba = (c, a = 1, j = 0) => `rgba(${clamp(c[0] + j, 0, 255) | 0},${clamp(c[1] + j, 0, 255) | 0},${clamp(c[2] + j, 0, 255) | 0},${a})`;
export const mix = (a, b, k) => [lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k)];
export const poly = (pts) => { const p = new Path2D(); pts.forEach(([x, y], i) => (i ? p.lineTo(x, y) : p.moveTo(x, y))); p.closePath(); return p; };
export const outside = (W, H, shape) => { const p = new Path2D(); p.rect(0, 0, W, H); p.addPath(shape); return p; };   // clip it with 'evenodd' to keep everything but the shape
export const ellipsePath = (x, y, rx, ry, rot = 0) => { const p = new Path2D(); p.ellipse(x, y, rx, ry, rot, 0, TAU); return p; };
// paper tooth: coarse specks keyed by (x, y) with no row or column pattern; scale 2 makes the grains two pixels wide
const teeth = new Map();
export function tooth(w, h, seed, strength, tint, scale = 1) {
  const key = `${w}x${h}:${seed}:${strength}:${tint}:${scale}`; if (teeth.has(key)) return teeth.get(key);
  const sw = Math.ceil(w / scale), sh = Math.ceil(h / scale), c = new OffscreenCanvas(sw, sh), im = c.getContext('2d').createImageData(sw, sh);
  for (let y = 0; y < sh; y++) for (let x = 0; x < sw; x++) { const i = (y * sw + x) * 4; im.data[i] = tint[0]; im.data[i + 1] = tint[1]; im.data[i + 2] = tint[2]; im.data[i + 3] = (hash(x, y, seed) * 0.6 + hash(x >> 1, y >> 1, seed + 1) * 0.4) * strength; }
  c.getContext('2d').putImageData(im, 0, 0); teeth.set(key, c); return c;
}
export const speckle = (g, W, H, seed, strength, tint, scale = 1) => { g.save(); g.imageSmoothingEnabled = false; g.drawImage(tooth(W, H, seed, strength, tint, scale), 0, 0, W, H); g.restore(); };
// smooth value noise in 0..1 from a position: a wandering field for colour and direction
export function vnoise(x, y, seed = 0) {
  const xi = Math.floor(x), yi = Math.floor(y), u = (x - xi) ** 2 * (3 - 2 * (x - xi)), v = (y - yi) ** 2 * (3 - 2 * (y - yi));
  return lerp(lerp(hash(xi, yi, seed), hash(xi + 1, yi, seed), u), lerp(hash(xi, yi + 1, seed), hash(xi + 1, yi + 1, seed), u), v);
}
// a Catmull-Rom spline through the points, as a dense polyline: a smooth line that passes through every point
export function spline(pts, per = 8) {
  const out = [];
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)];
    for (let s = 0; s < per; s++) { const u = s / per; out.push([0, 1].map((d) => 0.5 * (2 * p1[d] + (p2[d] - p0[d]) * u + (2 * p0[d] - 5 * p1[d] + 4 * p2[d] - p3[d]) * u * u + (3 * p1[d] - p0[d] - 3 * p2[d] + p3[d]) * u ** 3))); }
  }
  out.push(pts[pts.length - 1]); return out;
}
export const at = (pts, k) => { const u = clamp(k) * (pts.length - 1), i = Math.min(Math.floor(u), pts.length - 2); return [lerp(pts[i][0], pts[i + 1][0], u - i), lerp(pts[i][1], pts[i + 1][1], u - i), Math.atan2(pts[i + 1][1] - pts[i][1], pts[i + 1][0] - pts[i][0])]; };
export const bounds = (pts) => [Math.min(...pts.map((p) => p[0])), Math.min(...pts.map((p) => p[1])), Math.max(...pts.map((p) => p[0])), Math.max(...pts.map((p) => p[1]))];
// a row of soft, uneven dabs along a line: charcoal, pastel, rubbed graphite. k (0..1) is how much of the line is laid
function dabs(g, x0, y0, x1, y1, w, a, seed, k = 1, col = [24, 23, 26]) {
  if (k <= 0) return;
  const n = Math.max(2, Math.floor(Math.hypot(x1 - x0, y1 - y0) / (w * (w > 30 ? 0.35 : 0.2)))), m = Math.floor(n * clamp(k));
  for (let i = 0; i <= m; i++) {
    const e = i / n, r = w * (0.55 + 0.6 * hash(i, seed)), x = lerp(x0, x1, e) + (hash(i, seed, 1) - 0.5) * w * 0.7, y = lerp(y0, y1, e) + (hash(i, seed, 2) - 0.5) * w * 0.7, al = a * (0.5 + hash(i, seed, 3)) * (w > 30 ? 1 : 0.6);
    if (w > 30) { const rg = g.createRadialGradient(x, y, 0, x, y, r); rg.addColorStop(0, rgba(col, al)); rg.addColorStop(1, rgba(col, 0)); g.fillStyle = rg; }   // a big dab is soft: it was rubbed
    else g.fillStyle = rgba(col, al);
    g.beginPath(); g.arc(x, y, r, 0, TAU); g.fill();
  }
}
// parallel pencil lines inside a clip, laid one after another; o: { cx, cy, ang, sp, L, start, gap, a, w }
function hatch(g, clips, o, ts, f) {
  const d = [Math.cos(o.ang), Math.sin(o.ang)], nr = [-d[1], d[0]], n = Math.ceil((2 * o.L) / o.sp);
  g.save(); clips.forEach(([p, rule]) => g.clip(p, rule)); g.lineWidth = o.w; g.strokeStyle = `rgba(48,50,58,${o.a})`;
  for (let i = 0; i < n; i++) {
    const k = clamp((ts - o.start - i * o.gap) / 0.16); if (k <= 0) break;
    const c = -o.L + i * o.sp + jit(f, i, 1.5), x = o.cx + nr[0] * c + jit(f, i + 40, 1.4), y = o.cy + nr[1] * c;
    g.beginPath(); g.moveTo(x - d[0] * o.L, y - d[1] * o.L); g.lineTo(x + d[0] * o.L * (2 * k - 1), y + d[1] * o.L * (2 * k - 1)); g.stroke();
  }
  g.restore();
}
const cloudPts = (x, y, k) => [...Array.from({ length: 37 }, (_, i) => { const u = i / 36; return [x + (-72 + 144 * u) * k, y + (30 - (26 + 26 * Math.abs(Math.sin(u * 3 * Math.PI)) ** 0.5) * Math.sin(u * Math.PI) ** 0.35) * k]; }), [x + 72 * k, y + 30 * k], [x - 72 * k, y + 30 * k]];   // a flat-bottomed cloud with three puffs
const applePts = (cx, cy, R, n = 72) => Array.from({ length: n + 1 }, (_, i) => {
  const a = (i / n) * TAU - Math.PI / 2, c = Math.cos(a), s = Math.sin(a);   // wider at the shoulders, a dimple at the top and a small one below
  return [cx + R * c * (1.06 - 0.1 * s), cy + R * 0.94 * s + (s < 0 ? -0.22 * R * s * Math.exp(-c * c * 14) : -0.07 * R * s * Math.exp(-c * c * 14))];
});
// a thick daub of oil paint: a shadow side, the colour, bristle streaks and a light ridge, along one direction
function brush(g, x, y, a, len, w, col, k, ridge) {
  const ux = Math.cos(a) * len * 0.5 * k, uy = Math.sin(a) * len * 0.5 * k, px = -Math.sin(a) * w * 0.16, py = Math.cos(a) * w * 0.16;
  const line = (ox, oy, lw, style) => { g.lineWidth = lw; g.strokeStyle = style; g.beginPath(); g.moveTo(x - ux + ox, y - uy + oy); g.lineTo(x + ux + ox, y + uy + oy); g.stroke(); };
  line(1.8, 2.2, w, rgba(col.map((v) => v * 0.5), 0.6)); line(0, 0, w, rgba(col));
  line(px, py, 1.2, rgba(col.map((v) => v * 0.75), 0.4)); line(-px, -py, 1.2, rgba(col.map((v) => v * 0.75), 0.4));
  line(-w * 0.2, -w * 0.26, w * 0.26, rgba(col.map((v) => v + 50), ridge));
}
function oilColour(x, y, W, H) {
  const sx = W * 0.64, sy = H * 0.4, hz = H * 0.64, d = Math.hypot(x - sx, (y - sy) * 1.1), n = vnoise(x / 42, y / 42, 5);
  if (y > hz) {
    if (Math.abs(x - sx) < 40 + (y - hz) * 0.3) return mix([250, 196, 70], [226, 112, 42], n);
    if (x < W * 0.34 && y < hz + 90 * (1 - x / (W * 0.34))) return mix([46, 58, 44], [76, 54, 96], n);
    return mix([28, 44, 118], [66, 84, 158], n);
  }
  const u = clamp(y / hz) ** 1.4, sky = u < 0.55 ? mix([30, 40, 118], [112, 70, 152], u / 0.55) : mix([112, 70, 152], [244, 150, 72], (u - 0.55) / 0.45);
  const halo = mix(sky, [240, 138, 46], clamp(1 - (d - 62) / 150) * 0.92);
  return d < 66 ? mix([255, 232, 138], [255, 250, 205], n) : halo;
}
function oilAngle(x, y, W, H) {
  const sx = W * 0.64, sy = H * 0.4, hz = H * 0.64;
  if (y > hz) return Math.abs(x - sx) < 60 + (y - hz) * 0.3 ? Math.PI / 2 + 0.1 * Math.sin(y / 30) : (x < W * 0.34 ? -0.6 : 0.05 * Math.sin(x / 50));
  const d = Math.hypot(x - sx, y - sy), w = clamp(1 - d / 330), tangent = Math.atan2(y - sy, x - sx) + Math.PI / 2, flat = 0.14 * Math.sin(x / 90);
  return Math.atan2(w * Math.sin(tangent) + (1 - w) * Math.sin(flat), w * Math.cos(tangent) + (1 - w) * Math.cos(flat));
}
// a flat opaque shape with a hand-cut edge and faint brush streaks inside; path() builds it, bb is its bounding box
export function flatShape(g, path, col, seed, bb) {
  path(); fill(g, col); g.save(); g.clip(); g.lineCap = 'round';
  for (let j = 0; j < 26; j++) {
    const y = lerp(bb[1], bb[3], hash(j, seed)), x = lerp(bb[0] - 40, bb[2], hash(j, seed, 1));
    g.strokeStyle = hash(j, seed, 2) > 0.5 ? 'rgba(255,255,255,.07)' : 'rgba(0,0,0,.07)'; g.lineWidth = 5 + hash(j, seed, 3) * 6;
    g.beginPath(); g.moveTo(x, y); g.lineTo(x + 60 + hash(j, seed, 4) * 120, y + jit(j, seed, 3)); g.stroke();
  }
  g.restore();
}
// a back-and-forth crayon scribble over a box, slanted and uneven like a hand; each pass has its own pressure, so the strokes show. k (0..1) sweeps through the passes. Clip it to keep it inside a shape
function scribble(g, bb, col, k, f, seed, w = 9) {
  const cx = (bb[0] + bb[2]) / 2, cy = (bb[1] + bb[3]) / 2, D = Math.hypot(bb[2] - bb[0], bb[3] - bb[1]) / 2 + 90, ys = [];
  for (let y = -D, i = 0; y <= D; y += w * (0.4 + 0.45 * hash(i, seed)), i++) ys.push(y);
  g.save(); g.translate(cx, cy); g.rotate(-0.55 + (seed % 5) * 0.08); g.lineCap = 'round';
  ys.forEach((y, j) => {
    const e = clamp(k * ys.length - j), a = j % 2 ? D : -D; if (e <= 0) return;
    g.strokeStyle = rgba(col, 0.55 + 0.4 * hash(j, seed, 5), (hash(j, seed, 7) - 0.5) * 26); g.lineWidth = w * (0.85 + 0.3 * hash(j, seed, 6));
    g.beginPath(); g.moveTo(a + jit(seed, j, 9), y + jit(f + seed, j, 1.4)); g.lineTo(lerp(a, -a, e) + jit(seed, j + 30, 9), y + jit(f + seed, j + 60, 1.4) + jit(seed, j, w * 0.3)); g.stroke();
  });
  g.strokeStyle = rgba(col, 0.3, 30); g.lineWidth = w * 0.35; g.setLineDash([18, 5, 9, 7]); g.rotate(0.35);   // a second, lighter pass across the first: the wax catches the paper differently
  ys.forEach((y, j) => { if (j % 3 === 0 && k * ys.length - j > 0) { g.beginPath(); g.moveTo(-D * 0.7, y * 0.9); g.lineTo(D * 0.7 * clamp(k * ys.length - j), y * 0.9 + jit(f + seed, j, 2)); g.stroke(); } });
  g.setLineDash([]); g.restore();
}
// chalk: three thin dusty passes and a soft halo; a stub of chalk sits at the tip while the line is still being drawn
function chalk(g, pts, k, f, col = '#f1eee4', w = 4) {
  g.lineCap = 'round'; g.lineJoin = 'round'; g.strokeStyle = col;
  [[w, 0.55, [22, 2]], [w * 0.7, 0.45, [9, 5, 16, 4]], [w * 2.2, 0.1, []]].forEach(([lw, a, dash], p) => { g.globalAlpha = a; g.lineWidth = lw; g.setLineDash(dash); g.lineDashOffset = p * 7; strokePart(g, pts.map(([x, y]) => [x + p - 1, y + (p - 1) * 1.2]), k, f + p * 31, 1.2); });
  g.setLineDash([]); g.globalAlpha = 1;
  if (k > 0 && k < 1) { const [x, y, a] = at(pts, k); g.save(); g.translate(x, y); g.rotate(a + 0.5); g.fillStyle = '#f6f3ea'; g.beginPath(); g.roundRect(0, -5, 34, 10, 3); g.fill(); g.restore(); }
}
// one daub of translucent paint on lit glass: the colour, a deeper rim where it is thick, and finger streaks dragged behind it
function daub(g, build, col, box, f, seed, a = 0.8) {
  g.save(); build(); g.fillStyle = rgba(col, a); g.fill(); g.lineWidth = 7; g.strokeStyle = rgba(col.map((v) => v * 0.5), 0.5); g.stroke(); g.restore();
  g.lineCap = 'round';
  for (let j = 0; j < 12; j++) {
    const x = lerp(box[0], box[2], hash(j, seed)), y = lerp(box[1], box[3], hash(j, seed, 1)), len = 50 + hash(j, seed, 2) * 110 + jit(f, j + seed, 10), bend = jit(f, j + seed + 50, 6);
    const gr = g.createLinearGradient(x, y, x - len, y + bend); gr.addColorStop(0, rgba(col, 0.32)); gr.addColorStop(1, rgba(col, 0));
    g.strokeStyle = gr; g.lineWidth = 3 + hash(j, seed, 3) * 8; g.beginPath(); g.moveTo(x, y); g.quadraticCurveTo(x - len / 2, y + bend * 1.6, x - len, y + bend); g.stroke();
  }
}
// the sand figure as ten soft ellipses [x, y, rx, ry, angle] in units of R: a sun (a disc and eight rays), a flower (a core and eight petals) or a bird in flight.
// Every figure has ten, so any two can be blended number by number: that is how one shape is pushed into the next
const radial = (a, r, rx, ry) => [Math.cos(a) * r, Math.sin(a) * r, rx, ry, a];
const SAND_SUN = [[0, 0, 0.55, 0.55, 0], ...Array.from({ length: 8 }, (_, i) => radial((i * TAU) / 8, 1.05, 0.42, 0.09)), [0, 0, 0.01, 0.01, 0]];
const SAND_FLOWER = [[0, 0, 0.3, 0.3, 0], ...Array.from({ length: 8 }, (_, i) => radial((i * TAU) / 8, 0.74, 0.44, 0.27)), [0, 0, 0.01, 0.01, 0]];
const SAND_BIRD = [[0, 0.05, 0.72, 0.3, 0.12], [-0.78, -0.12, 0.2, 0.17, 0], [-1.0, -0.1, 0.17, 0.045, 0.1], [0.95, 0.12, 0.4, 0.1, 0.3], [0.92, 0.22, 0.36, 0.09, 0.55], [0.5, -0.7, 0.8, 0.2, -0.9], [-0.5, -0.7, 0.8, 0.2, -2.25], [0.98, -1.0, 0.42, 0.11, -0.6], [-0.92, -1.0, 0.4, 0.11, -2.5], [0.05, 0.15, 0.5, 0.25, 0]];
const blendShapes = (a, b, k) => a.map((e, i) => e.map((v, j) => lerp(v, b[i][j], k)));
// sand as a mass: a wide, pale halo where it is thin, then the dark sepia body with a soft edge
function sandMass(g, shapes, R) {
  const pass = (scale, blur, style) => { g.filter = `blur(${blur}px)`; g.fillStyle = style; shapes.forEach(([x, y, rx, ry, a]) => { g.beginPath(); g.ellipse(x * R, y * R, Math.max(0.01, rx * R * scale), Math.max(0.01, ry * R * scale), a, 0, TAU); g.fill(); }); };
  pass(1.3, 16, 'rgba(120,58,12,.32)'); pass(1.1, 8, 'rgba(60,28,6,.6)'); pass(1, 4, 'rgba(26,11,3,.95)'); g.filter = 'none';
}
// the one line of the swan, as points evenly spaced along its length so the pen moves at a steady speed
function swanLine() {
  const C = spline([[430, 360], [398, 322], [376, 282], [372, 240], [386, 200], [392, 164], [380, 134]], 8), n = C.length - 1;
  const side = (sign) => C.map(([x, y], i) => { const p = C[Math.max(0, i - 1)], q = C[Math.min(n, i + 1)], a = Math.atan2(q[1] - p[1], q[0] - p[0]), hw = lerp(25, 11, easeOut(i / n)) * sign; return [x + Math.sin(a) * hw, y - Math.cos(a) * hw]; });
  const front = side(1), back = side(-1).reverse();
  const raw = [...spline([[104, 462], [186, 448], [258, 462], [332, 448], [388, 428], [404, 400]], 10), ...front, ...spline([[front[n][0], front[n][1]], [352, 112], [338, 114], [316, 132], [296, 144], [322, 150], [346, 142], [376, 140], [back[0][0], back[0][1]]], 8), ...back,
    ...spline([[back[n][0], back[n][1]], [500, 316], [566, 296], [636, 290], [696, 300], [740, 298], [776, 270], [748, 322], [716, 360], [662, 392], [592, 412], [520, 416], [456, 404], [416, 386], [466, 384], [530, 364], [600, 350], [666, 346], [716, 334], [686, 366], [628, 388], [566, 400], [510, 410], [504, 436], [580, 448], [680, 438], [780, 448], [868, 438]], 10)];
  const len = [0]; raw.forEach((p, i) => i && len.push(len[i - 1] + Math.hypot(p[0] - raw[i - 1][0], p[1] - raw[i - 1][1])));
  return Array.from({ length: 360 }, (_, j) => { const d = (len[len.length - 1] * j) / 359; let i = 1; while (i < len.length - 1 && len[i] < d) i++; const e = (d - len[i - 1]) / Math.max(1e-6, len[i] - len[i - 1]); return [lerp(raw[i - 1][0], raw[i][0], e), lerp(raw[i - 1][1], raw[i][1], e)]; });
}

export const LOOKS = {
  /* ------------------------------------------------ painting and drawing ------------------------------------------------ */
  'pencil-sketch': { kind: '2d', fps: 8, draw(g, t, W, H) {
    // an apple in graphite: a faint construction circle, a doubled outline, three layers of hatching that thicken toward the shadow, a rubbed smudge, and paper tooth over it all
    const f = frameOf(t, 8), ts = held(t, 8), cx = W * 0.47, cy = H * 0.5, R = 150, body = poly(applePts(cx, cy, R));
    bg(g, W, H, '#eee8da'); g.lineCap = 'round'; g.lineJoin = 'round';
    g.strokeStyle = 'rgba(70,72,80,.22)'; g.lineWidth = 1; strokePart(g, circlePts(cx, cy, R * 1.12, 48), prog(ts, 0, 0.5), f, 2);
    const clips = (...extra) => [[body, 'nonzero'], ...extra];
    hatch(g, clips([outside(W, H, ellipsePath(cx - 0.42 * R, cy - 0.45 * R, 0.3 * R, 0.2 * R, -0.6)), 'evenodd']), { cx, cy, ang: -0.9, sp: 9, L: 260, start: 0.9, gap: 0.02, a: 0.5, w: 1.5 }, ts, f);
    hatch(g, clips([outside(W, H, ellipsePath(cx - 0.3 * R, cy - 0.35 * R, 1.05 * R, 1.05 * R)), 'evenodd']), { cx, cy, ang: 0.8, sp: 8, L: 260, start: 1.7, gap: 0.02, a: 0.46, w: 1.4 }, ts, f);
    hatch(g, clips([outside(W, H, ellipsePath(cx - 0.12 * R, cy - 0.16 * R, 1.22 * R, 1.22 * R)), 'evenodd']), { cx, cy, ang: -0.45, sp: 5, L: 260, start: 2.5, gap: 0.015, a: 0.5, w: 1.4 }, ts, f);
    hatch(g, [[ellipsePath(cx + 0.1 * R, cy + 0.93 * R, 1.15 * R, 0.17 * R), 'nonzero'], [outside(W, H, body), 'evenodd']], { cx, cy: cy + 0.93 * R, ang: 0.1, sp: 5, L: 220, start: 2.6, gap: 0.02, a: 0.45, w: 1.5 }, ts, f);
    g.strokeStyle = 'rgba(46,48,56,.5)'; g.lineWidth = 1.5; strokePart(g, applePts(cx, cy, R * 1.01), prog(ts, 0.1, 0.9), f, 2.2);
    g.strokeStyle = 'rgba(40,42,50,.75)'; g.lineWidth = 2; strokePart(g, applePts(cx + 1, cy - 1, R), prog(ts, 0.3, 0.9), f + 17, 1.2);
    g.strokeStyle = 'rgba(40,42,50,.85)'; g.lineWidth = 4.5; strokePart(g, spline([[cx, cy - 0.7 * R], [cx + 5, cy - 0.88 * R], [cx + 16, cy - 1.06 * R]], 6), prog(ts, 1.0, 0.3), f, 0.8);
    g.lineWidth = 1.8; g.strokeStyle = 'rgba(40,42,50,.8)'; strokePart(g, spline([[cx + 8, cy - 0.98 * R], [cx + 48, cy - 1.22 * R], [cx + 105, cy - 1.2 * R], [cx + 70, cy - 1.0 * R], [cx + 8, cy - 0.98 * R]], 6), prog(ts, 1.2, 0.5), f, 1);
    strokePart(g, [[cx + 14, cy - 1.0 * R], [cx + 60, cy - 1.1 * R], [cx + 92, cy - 1.17 * R]], prog(ts, 1.6, 0.3), f, 0.8);
    const k = prog(ts, 3.0, 0.8); g.save(); g.globalCompositeOperation = 'multiply'; g.translate(cx + 0.5 * R, cy + 0.55 * R); g.rotate(-0.6); g.scale(1, 0.4);   // a thumb rubbed through the shadow
    const sm = g.createRadialGradient(0, 0, 4, 0, 0, 0.9 * R); sm.addColorStop(0, `rgba(80,82,92,${0.3 * k})`); sm.addColorStop(1, 'rgba(80,82,92,0)'); g.fillStyle = sm; g.fillRect(-R, -R, 2 * R, 2 * R); g.restore();
    paper(g, W, H, 3, 24); g.drawImage(grain(W, H, 9, 80, [250, 246, 236]), 0, 0);   // the tooth of the paper breaks every line
  } },
  charcoal: { kind: '2d', fps: 8, draw(g, t, W, H) {
    // a lone tree on a hill under a low sun: soft smears, rough dabbed edges, a sun and highlights rubbed out with an eraser
    const ts = held(t, 8), P = [222, 216, 204], bx = W * 0.3, by = H * 0.8;
    bg(g, W, H, rgba(P));
    for (let i = 0; i < 6; i++) for (let j = 0; j < 12; j++) {   // the sky is rubbed in long, uneven sweeps of the side of a stick
      const y = 10 + i * 56 + hash(i, j, 1) * 60, k = prog(ts, 0.1 + i * 0.1, 0.6), x0 = -30 + hash(i, j, 2) * 300, x1 = x0 + 260 + hash(i, j, 3) * 700;
      g.strokeStyle = rgba([58, 56, 60], (0.22 - i * 0.025) * (0.4 + hash(i, j, 4))); g.lineWidth = 3 + hash(i, j, 5) * 16; g.lineCap = 'round'; strokePart(g, [[x0, y], [(x0 + x1) / 2, y + jit(i, j, 14)], [x1, y + jit(i, j + 9, 14)]], k);
    }
    const sun = g.createRadialGradient(W * 0.66, H * 0.34, 10, W * 0.66, H * 0.34, 150); sun.addColorStop(0, rgba(P, 1)); sun.addColorStop(0.45, rgba(P, 0.7)); sun.addColorStop(1, rgba(P, 0));
    g.fillStyle = sun; g.globalAlpha = easeOut(prog(ts, 0.3, 0.6)); g.fillRect(W * 0.4, 0, W * 0.6, H * 0.7);
    g.fillStyle = rgba(P, 0.95); blob(g, W * 0.66, H * 0.34, 50, 77, 0.07); g.fill(); g.globalAlpha = 1;   // the sun: a clean disc lifted out with a kneaded eraser
    for (let pass = 0; pass < 2; pass++) for (let c = 0; c <= 40; c++) {
      const x = (c * W) / 40, top = H * 0.78 + Math.sin(c * 0.33) * 22 + Math.sin(c * 0.11) * 18 + hash(c, 4) * 8;
      if (c / 40 < prog(ts, pass * 0.4, 0.7)) dabs(g, x, top, x + jit(c, 1, 8), H + 20, 48, 0.17, 100 + c + pass * 50, 1, [20, 19, 22]);
    }
    const limb = (x, y, a, len, w, depth, seed, start) => {
      const x1 = x + Math.cos(a) * len, y1 = y + Math.sin(a) * len; dabs(g, x, y, x1, y1, w, 0.55, seed, easeOut(prog(ts, start, 0.3)), [18, 17, 20]);
      if (!depth) return;
      for (let c = 0; c < 2 + (hash(seed, depth) > 0.5 ? 1 : 0); c++) limb(x1, y1, a + (c === 2 ? jit(seed, c, 0.25) : (c ? 1 : -1) * (0.34 + 0.34 * hash(seed, c, depth))), len * (0.7 + 0.1 * hash(seed, c)), w * 0.62, depth - 1, seed * 7 + c + 1, start + 0.2);
    };
    limb(bx, by + 6, -Math.PI / 2 + 0.1, 110, 24, 4, 3, 0);
    g.strokeStyle = rgba(P, 0.5); g.lineWidth = 5; g.lineCap = 'round'; strokePart(g, [[bx - 9, by - 2], [bx - 5, by - 50], [bx - 3, by - 96]], easeOut(prog(ts, 1.4, 0.4)), 0, 0.8);   // a highlight lifted off the trunk
    dabs(g, W * 0.52, H * 0.2, W * 0.92, H * 0.12, 11, 0.13, 22, prog(ts, 1.8, 0.5), P);
    for (let i = 0; i < 3; i++) { g.strokeStyle = 'rgba(30,29,32,.8)'; g.lineWidth = 3; g.lineCap = 'round'; strokePart(g, [[W * 0.74 + i * 34, H * 0.2 + i * 9], [W * 0.755 + i * 34, H * 0.2 + i * 9 - 8], [W * 0.77 + i * 34, H * 0.2 + i * 9]], prog(ts, 2.8 + i * 0.12, 0.2)); }
    dabs(g, bx, by + 14, bx + 150, by + 34, 28, 0.06, 23, prog(ts, 2.2, 0.6), [20, 19, 22]);
    speckle(g, W, H, 31, 150, P, 2);
    const v = g.createRadialGradient(W / 2, H / 2, H * 0.4, W / 2, H / 2, H * 0.95); v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(30,26,20,.32)'); g.fillStyle = v; g.fillRect(0, 0, W, H);
  } },
  'oil-painting': { kind: '2d', fps: 12, draw(g, t, W, H) {
    // a sun over a bay in directional daubs: each carries a shadow side, a bristle streak and a light ridge; thick cream daubs sit on top as impasto
    const ts = held(t, 12), cell = 21, hz = H * 0.64; g.lineCap = 'round';
    bg(g, W, H, '#22204a');
    g.filter = 'blur(20px)';
    for (let y = -54; y < H + 54; y += 54) for (let x = -54; x < W + 54; x += 54) { g.fillStyle = rgba(oilColour(x + 27, y + 27, W, H).map((v) => v * 0.78), easeOut(prog(ts, 0, 0.7))); g.fillRect(x, y, 55, 55); }   // the first wash blocks the colours in
    g.filter = 'none';
    for (let j = -1; j <= H / cell; j++) for (let i = -1; i <= W / cell; i++) {
      const x = (i + 0.5 + (hash(i, j, 1) - 0.5) * 0.8) * cell, y = (j + 0.5 + (hash(i, j, 2) - 0.5) * 0.8) * cell, k = easeOut(prog(ts, hash(i, j, 3) * 2.3 + (y / H) * 0.4, 0.35));
      if (k <= 0) continue;
      const col = oilColour(x, y, W, H).map((v, c) => v + (hash(i, j, 4 + c) - 0.5) * 34), a = oilAngle(x, y, W, H) + (hash(i, j, 8) - 0.5) * 0.5;
      brush(g, x, y, a, 44, 13, col, k, y > hz ? 0.3 : 0.38);
    }
    for (let i = 0; i < 60; i++) {   // impasto: thick, light daubs around the sun and along the reflection
      const onSun = i < 34, a = hash(i, 5) * TAU, r = hash(i, 6) * 96, x = onSun ? W * 0.64 + Math.cos(a) * r : W * 0.64 + (hash(i, 7) - 0.5) * 80, y = onSun ? H * 0.4 + Math.sin(a) * r * 0.9 : hz + 14 + hash(i, 8) * (H - hz - 30);
      const k = easeOut(prog(ts, 1.6 + hash(i, 9) * 1.4, 0.3)); if (k > 0) brush(g, x, y, onSun ? a + Math.PI / 2 : Math.PI / 2, 28, 15, onSun ? [255, 246, 190] : [255, 214, 120], k, 0.85);
    }
  } },
  gouache: { kind: '2d', fps: 8, draw(g, t, W, H) {
    // a storybook night in flat, matte, opaque layers: each colour laid in turn with a hand-cut edge, faint brush streaks, no gradients
    const ts = held(t, 8), f = frameOf(t, 8);
    const layer = (start, dir, body) => { const k = easeOut(prog(ts, start, 0.5)); if (k <= 0) return; g.save(); g.beginPath(); if (dir === 'up') g.rect(0, H * (1 - k), W, H * k); else g.rect(0, 0, W * k, H); g.clip(); body(); g.restore(); };
    const shape = (pts, col, seed) => flatShape(g, () => cut(g, pts, seed, 2.2), col, seed, bounds(pts));
    const pine = (x, base, h, seed) => { shape([[x - 10, base + 4], [x + 10, base + 4], [x + 10, base - h * 0.2], [x - 10, base - h * 0.2]], '#4b2f24', seed); for (let i = 0; i < 3; i++) { const w = (60 - i * 14) * (h / 170), yb = base - h * 0.14 - i * h * 0.27; shape([[x - w, yb], [x + w, yb], [x, yb - h * 0.42]], '#2b5a35', seed + i + 1); } };
    layer(0, 'up', () => { bg(g, W, H, '#273672'); shape([[0, 240], [960, 220], [960, 420], [0, 440]], '#2f4284', 3); });
    layer(0.25, 'right', () => { flatShape(g, () => blob(g, 700, 150, 70, 5, 0.02), '#f3e5a4', 5, [630, 80, 770, 220]); [[675, 130, 17], [722, 172, 12], [706, 118, 8]].forEach(([x, y, r], i) => flatShape(g, () => blob(g, x, y, r, 6 + i, 0.05), '#e3cf88', 6 + i, [x - r, y - r, x + r, y + r])); });
    for (let i = 0; i < 26; i++) { const x = hash(i, 1) * W, y = hash(i, 2) * 230; if (Math.hypot(x - 700, y - 150) > 96 && prog(ts, 2.8 + hash(i, 3) * 0.8, 0.1) > 0) { g.fillStyle = (f + i) % 7 === 0 ? 'rgba(243,229,164,.45)' : '#f3e5a4'; g.beginPath(); g.arc(x, y, 1.6 + hash(i, 4) * 1.8, 0, TAU); g.fill(); } }
    layer(0.6, 'up', () => shape([[0, 380], [140, 322], [300, 362], [470, 306], [640, 354], [800, 316], [960, 350], [960, 540], [0, 540]], '#40509a', 11));
    layer(1.0, 'up', () => { shape([[0, 440], [200, 392], [420, 424], [640, 384], [960, 430], [960, 540], [0, 540]], '#3f7440', 12); shape([[322, 408], [354, 408], [430, 470], [520, 540], [290, 540], [350, 470]], '#e8d29c', 13); });
    layer(1.5, 'right', () => { shape([[250, 336], [430, 336], [430, 414], [250, 414]], '#e9b676', 14); shape([[392, 270], [416, 270], [416, 320], [392, 320]], '#8f3c32', 15); });
    layer(1.9, 'right', () => shape([[226, 340], [340, 262], [454, 340]], '#b8463a', 16));
    layer(2.3, 'right', () => { flatShape(g, () => blob(g, 284, 368, 36, 19, 0.04), '#f3cc78', 19, [248, 332, 320, 404]); shape([[318, 366], [356, 366], [356, 414], [318, 414]], '#6a3b2b', 17); shape([[266, 350], [302, 350], [302, 386], [266, 386]], '#ffd45e', 18); g.strokeStyle = '#a0622f'; g.lineWidth = 3; g.beginPath(); g.moveTo(284, 350); g.lineTo(284, 386); g.moveTo(266, 368); g.lineTo(302, 368); g.stroke(); });
    [[560, 428, 150], [640, 436, 196], [738, 422, 142], [868, 436, 176]].forEach(([x, b, h], i) => layer(2.4 + i * 0.22, 'up', () => pine(x, b, h, 30 + i * 5)));
    for (let i = 0; i < 3; i++) { const s = prog(ts, 2.9, 1.2), y = 262 - ((s * 3 + i * 0.9) % 2.6) * 34; if (s > 0) { g.fillStyle = 'rgba(232,226,208,.8)'; g.beginPath(); g.arc(404 + Math.sin(f * 0.7 + i) * 4 + i * 4, y, 7 + i * 3, 0, TAU); g.fill(); } }
    paper(g, W, H, 4, 16);
  } },
  crayon: { kind: '2d', fps: 8, draw(g, t, W, H) {
    // a child's picture in wax: scribbled fills laid from the top down, fat outlines past the edges, and paper tooth showing through every stroke
    const ts = held(t, 8), f = frameOf(t, 8); bg(g, W, H, '#f6f0e0'); g.lineCap = 'round';
    const fillIn = (clip, bb, col, start, dur, seed, w) => { g.save(); g.clip(clip); scribble(g, bb, col, prog(ts, start, dur), f, seed, w); g.restore(); };
    const outline = (pts, col, start, dur) => { g.strokeStyle = rgba(col, 0.9); g.lineWidth = 6; g.lineJoin = 'round'; strokePart(g, pts, prog(ts, start, dur), f + 5, 1.8); };
    fillIn(poly([[0, 0], [W, 0], [W, 392], [0, 392]]), [0, 0, W, 392], [120, 190, 235], 0, 0.9, 1, 14);
    [[470, 96, 1], [760, 70, 0.8]].forEach(([x, y, k], i) => { const c = cloudPts(x, y, k); fillIn(poly(c), [x - 90 * k, y - 60 * k, x + 90 * k, y + 40 * k], [252, 252, 250], 0.9 + i * 0.2, 0.4, 40 + i, 11); outline(c, [110, 160, 215], 1.0 + i * 0.2, 0.4); });   // clouds: puffed outlines scribbled white
    const sun = circlePts(170, 130, 62, 28); fillIn(poly(sun), [100, 60, 240, 200], [250, 205, 40], 0.6, 0.5, 2, 10); outline(sun, [235, 150, 30], 0.7, 0.4);
    for (let i = 0; i < 10; i++) { const a = (i / 10) * TAU; g.strokeStyle = rgba([240, 140, 30], 0.9); g.lineWidth = 7; strokePart(g, [[170 + Math.cos(a) * 80, 130 + Math.sin(a) * 80], [170 + Math.cos(a) * 112, 130 + Math.sin(a) * 112]], prog(ts, 1.1 + i * 0.03, 0.15), f, 1.5); }
    fillIn(poly([[0, 372], [W, 372], [W, H], [0, H]]), [0, 372, W, H], [70, 170, 60], 1.3, 0.7, 3, 11);
    const walls = [[360, 270], [600, 270], [600, 420], [360, 420]]; fillIn(poly(walls), [360, 270, 600, 420], [225, 130, 55], 1.9, 0.5, 4, 10); outline([...walls, walls[0]], [150, 80, 30], 2.0, 0.5);
    const roof = [[335, 276], [480, 168], [625, 276]]; fillIn(poly(roof), [335, 168, 625, 276], [214, 56, 46], 2.5, 0.4, 5, 10); outline([...roof, roof[0]], [140, 30, 30], 2.6, 0.35);
    fillIn(poly([[455, 330], [505, 330], [505, 420], [455, 420]]), [455, 330, 505, 420], [46, 95, 181], 2.9, 0.3, 6, 9);
    fillIn(poly([[385, 300], [430, 300], [430, 345], [385, 345]]), [385, 300, 430, 345], [252, 215, 60], 3.0, 0.2, 7, 9);
    g.strokeStyle = rgba([140, 80, 30], 0.9); g.lineWidth = 4; strokePart(g, [[407, 300], [407, 345]], prog(ts, 3.2, 0.1), f, 1); strokePart(g, [[385, 322], [430, 322]], prog(ts, 3.25, 0.1), f, 1);
    fillIn(poly([[722, 300], [752, 300], [752, 420], [722, 420]]), [722, 300, 752, 420], [125, 76, 40], 3.2, 0.3, 8, 9);
    const crown = circlePts(737, 250, 78, 28); fillIn(poly(crown), [655, 170, 820, 330], [60, 150, 58], 3.4, 0.5, 9, 10); outline(crown, [30, 100, 40], 3.5, 0.5);
    for (let i = 0; i < 9; i++) { const x = 40 + hash(i, 1) * 880, y = 430 + hash(i, 2) * 90, k = prog(ts, 3.8 + i * 0.06, 0.15); g.strokeStyle = rgba([40, 120, 40], 0.9); g.lineWidth = 4; strokePart(g, [[x, y + 26], [x + 2, y]], k, f, 1); g.fillStyle = rgba(i % 2 ? [225, 60, 110] : [255, 235, 70], 0.95); if (k > 0.9) { g.beginPath(); g.arc(x + 2, y - 4, 9, 0, TAU); g.fill(); } }
    speckle(g, W, H, 21, 190, [248, 243, 230], 2); paper(g, W, H, 22, 12);   // the tooth: paper-coloured specks over wax
  } },
  chalkboard: { kind: '2d', fps: 10, draw(g, t, W, H) {
    // a green-black board with old eraser swipes, a ledge, and a right triangle drawn in dusty chalk with the chalk stub at the tip of each stroke
    const f = frameOf(t, 10), ts = held(t, 10);
    bg(g, W, H, '#1c2b25'); const lit = g.createRadialGradient(W * 0.45, H * 0.4, 40, W * 0.45, H * 0.45, W * 0.7); lit.addColorStop(0, 'rgba(70,98,84,.4)'); lit.addColorStop(1, 'rgba(70,98,84,0)'); g.fillStyle = lit; g.fillRect(0, 0, W, H);
    g.drawImage(grain(W, H, 12, 44, [205, 222, 212]), 0, 0);
    for (let i = 0; i < 6; i++) { g.save(); g.translate(120 + i * 150, 120 + hash(i, 1) * 260); g.rotate(-0.5 + hash(i, 2) * 0.5); g.fillStyle = `rgba(200,214,205,${0.045 + hash(i, 3) * 0.03})`; g.beginPath(); g.ellipse(0, 0, 120 + hash(i, 4) * 90, 26 + hash(i, 5) * 16, 0, 0, TAU); g.fill(); g.restore(); }
    g.fillStyle = '#5e4128'; g.fillRect(0, H - 40, W, 40); g.fillStyle = '#7a5833'; g.fillRect(0, H - 40, W, 7); g.fillStyle = 'rgba(235,238,230,.18)'; g.fillRect(0, H - 47, W, 7);   // the ledge, with a line of fallen dust
    const A = [150, 420], B = [500, 420], C = [500, 150];
    chalk(g, [A, B], prog(ts, 0.2, 0.55), f); chalk(g, [B, C], prog(ts, 0.8, 0.5), f); chalk(g, [C, A], prog(ts, 1.35, 0.6), f);
    chalk(g, [[472, 420], [472, 392], [500, 392]], prog(ts, 2.0, 0.2), f, '#f1eee4', 3);
    g.fillStyle = 'rgba(245,242,230,.92)'; g.font = `600 44px "Chalkduster", "Marker Felt", "Comic Sans MS", ${FONT}`;
    [['b', 316, 462, 2.1], ['a', 528, 296, 2.3], ['c', 290, 268, 2.5]].forEach(([s, x, y, st]) => { g.globalAlpha = prog(ts, st, 0.2); g.fillText(s, x, y); }); g.globalAlpha = 1;
    const k = prog(ts, 2.7, 0.9); g.save(); g.beginPath(); g.rect(556, 150, 400 * k, 140); g.clip(); g.fillStyle = 'rgba(255,224,120,.94)'; g.font = `600 52px "Chalkduster", "Marker Felt", "Comic Sans MS", ${FONT}`; g.fillText('a² + b² = c²', 566, 236); g.restore();
    chalk(g, [[566, 258], [740, 255], [900, 260]], prog(ts, 3.5, 0.3), f, '#ffe078', 3);
    const sunPts = circlePts(760, 360, 34, 20); chalk(g, sunPts, prog(ts, 3.4, 0.4), f, '#f6a9c4', 3);
    for (let i = 0; i < 8; i++) { const a = (i / 8) * TAU; chalk(g, [[760 + Math.cos(a) * 46, 360 + Math.sin(a) * 46], [760 + Math.cos(a) * 64, 360 + Math.sin(a) * 64]], prog(ts, 3.7 + i * 0.03, 0.12), f, '#f6a9c4', 3); }
    g.drawImage(grain(W, H, 17, 130, [28, 43, 37]), 0, 0);   // board-coloured specks eat into the chalk, so every line breaks up
  } },
  'one-line': { kind: '2d', fps: null, draw(g, t, W, H) {
    // a swan drawn by a single line that never lifts: a ripple, up the breast and neck, round the head and beak, down the back to the tail, back along the belly, a wing, and out as a ripple
    bg(g, W, H, '#f2c14e');
    const path = swanLine(), k = easeInOut(prog(t, 0.15, 3.3));
    g.strokeStyle = '#17233f'; g.lineWidth = 4.6; g.lineCap = 'round'; g.lineJoin = 'round'; strokePart(g, path, k);
    if (k > 0 && k < 1) { const [x, y] = at(path, k); g.fillStyle = '#17233f'; g.beginPath(); g.arc(x, y, 7, 0, TAU); g.fill(); }
    g.fillStyle = '#17233f'; g.beginPath(); g.arc(352, 122, 4.8 * prog(t, 1.9, 0.2), 0, TAU); g.fill();
  } },
  'paint-on-glass': { kind: '2d', fps: 12, draw(g, t, W, H) {
    // oil paint smeared on a lit sheet of glass: colour that glows against the lamp, deeper at the rims, finger streaks dragged behind, a fish that melts into a bird
    const ts = held(t, 12), f = frameOf(t, 12), m = easeInOut(prog(ts, 1.2, 2.2)), x = lerp(W * 0.38, W * 0.58, easeInOut(prog(ts, 0, 4.5))), y = H * 0.56 - m * 70 + Math.sin(ts * 3) * 7;
    bg(g, W, H, '#2a1a10'); const lamp = g.createRadialGradient(W / 2, H / 2, 40, W / 2, H / 2, W * 0.62); lamp.addColorStop(0, '#fff6d6'); lamp.addColorStop(0.62, '#f6c96c'); lamp.addColorStop(1, '#7a4514'); g.fillStyle = lamp; g.fillRect(0, 0, W, H);
    g.globalCompositeOperation = 'multiply';
    [[W * 0.25, H * 0.95, 380, [40, 80, 190]], [W * 0.85, H * 0.1, 330, [215, 70, 120]]].forEach(([wx, wy, r, c]) => { const wash = g.createRadialGradient(wx, wy, 10, wx, wy, r); wash.addColorStop(0, rgba(c, 0.5)); wash.addColorStop(1, rgba(c, 0)); g.fillStyle = wash; g.fillRect(0, 0, W, H); });
    for (let j = 0; j < 7; j++) { const ly = 60 + j * 70 + jit(f, j, 4); g.strokeStyle = rgba([60, 90, 200], 0.07); g.lineWidth = 12 + hash(j, 2) * 14; g.beginPath(); g.moveTo(-20, ly); g.quadraticCurveTo(W / 2, ly + jit(f, j + 9, 14) + 24, W + 20, ly - 20); g.stroke(); }
    g.translate(x, y); g.rotate(-m * 0.28);
    daub(g, () => { g.beginPath(); for (const s of [-1, 1]) g.ellipse(168, s * 36 * (1 - m * 0.55), 66, 25, s * (0.75 - 0.4 * m), 0, TAU); }, [214, 50, 112], [120, -60, 230, 60], f, 5, 0.72);   // tail: a fork that folds into a fan
    daub(g, () => { g.beginPath(); g.ellipse(0, 0, 132, 58, 0, 0, TAU); }, mix([238, 128, 28], [44, 92, 214], m), [-120, -50, 110, 50], f, 3);
    daub(g, () => { g.beginPath(); g.ellipse(14 + m * 20, -50 - m * 40, 62 + m * 46, 22 + m * 12, lerp(-0.25, -0.9, m) + Math.sin(ts * 8) * 0.28 * m, 0, TAU); }, mix([246, 200, 42], [130, 60, 208], m), [-50, -130, 90, -40], f, 7, 0.7);   // fin, then a flapping wing
    daub(g, () => { g.beginPath(); g.ellipse(-8, 44, 40, 14, 0.5, 0, TAU); }, [224, 70, 120], [-50, 30, 30, 60], f, 9, 0.6);
    if (m > 0.05) daub(g, () => { g.beginPath(); g.moveTo(-126, -14); g.lineTo(-126 - 58 * m, 2); g.lineTo(-126, 18); g.closePath(); }, [240, 150, 30], [-190, -10, -126, 14], f, 11, 0.85);   // a beak grows
    g.globalCompositeOperation = 'source-over'; g.fillStyle = 'rgba(30,14,6,.9)'; g.beginPath(); g.arc(-100, -14, 8, 0, TAU); g.fill(); g.fillStyle = 'rgba(255,248,225,.9)'; g.beginPath(); g.arc(-97, -17, 2.6, 0, TAU); g.fill();
    g.save(); g.beginPath(); g.ellipse(0, 0, 130, 56, 0, 0, TAU); g.clip(); g.strokeStyle = 'rgba(255,244,205,.8)'; g.lineWidth = 2.2; g.lineCap = 'round';   // lines scratched through the paint: scales, then feathers
    for (let i = 0; i < 8; i++) { const x0 = -92 + i * 28, k = prog(ts, 0.5 + i * 0.1, 0.3); if (k > 0) { g.beginPath(); g.moveTo(x0, -54); g.quadraticCurveTo(x0 + 20 + m * 16, -4, x0 + 4 + m * 30, 56 * k); g.stroke(); } }
    g.strokeStyle = 'rgba(255,255,255,.38)'; g.lineWidth = 8; g.beginPath(); g.ellipse(0, 0, 112, 40, 0, Math.PI * 1.12, Math.PI * 1.55); g.stroke(); g.restore();
    g.setTransform(1, 0, 0, 1, 0, 0); g.strokeStyle = 'rgba(255,245,210,.7)'; g.lineWidth = 2.5;
    for (let i = 0; i < 4; i++) { const bx = x - 180 - i * 46 + Math.sin(ts * 2 + i) * 6, by = y - 40 - ((ts * 28 + i * 40) % 160) * (1 - m * 0.4); g.beginPath(); g.arc(bx, by, 7 + i * 3, 0, TAU); g.stroke(); }
  } },
  'sand-art': { kind: '2d', fps: 12, draw(g, t, W, H) {
    // a light table seen from above: a warm backlight, sand as dark sepia masses with soft graded edges, light coming through where it is thin. A sun is pushed into a flower, then the flower into a bird
    const ts = held(t, 12), f = frameOf(t, 12), m1 = easeInOut(prog(ts, 1.0, 1.3)), m2 = easeInOut(prog(ts, 2.6, 1.3)), R = 104 * easeOut(prog(ts, 0.05, 0.8)), cx = W / 2, cy = H * 0.44;
    bg(g, W, H, '#fff0c4'); const lamp = g.createRadialGradient(W / 2, H * 0.45, 30, W / 2, H * 0.45, W * 0.62); lamp.addColorStop(0, '#fff6d2'); lamp.addColorStop(0.6, '#f6c25e'); lamp.addColorStop(1, '#b8661c'); g.fillStyle = lamp; g.fillRect(0, 0, W, H);
    const gy = lerp(H * 1.06, H * 0.86, easeOut(prog(ts, 0.05, 1)));   // a bank of sand along the bottom
    for (const [blur, style, dy] of [[22, 'rgba(120,58,12,.3)', -14], [10, 'rgba(60,28,6,.6)', -4], [4, 'rgba(26,11,3,.95)', 0]]) { g.filter = `blur(${blur}px)`; g.fillStyle = style; g.beginPath(); g.moveTo(-40, H + 40); g.lineTo(-40, gy + dy); g.bezierCurveTo(W * 0.25, gy + dy - 26, W * 0.4, gy + dy + 14, W * 0.55, gy + dy - 6); g.bezierCurveTo(W * 0.72, gy + dy - 24, W * 0.88, gy + dy + 10, W + 40, gy + dy - 8); g.lineTo(W + 40, H + 40); g.fill(); }
    g.filter = 'none';
    g.save(); g.translate(cx, cy);
    sandMass(g, blendShapes(blendShapes(SAND_SUN, SAND_FLOWER, m1), SAND_BIRD, m2), R);
    const stem = easeOut(prog(m1, 0.2, 0.8)) * (1 - m2), top = R * 0.95, bottom = gy - cy + 20;   // the stem and leaves grow with the flower and are swept away for the bird
    if (stem > 0.01) { g.filter = 'blur(4px)'; g.strokeStyle = 'rgba(26,11,3,.95)'; g.lineWidth = 13; g.lineCap = 'round'; g.beginPath(); g.moveTo(0, top); g.quadraticCurveTo(-8, lerp(top, bottom, 0.5), 3, lerp(top, bottom, stem)); g.stroke(); g.fillStyle = 'rgba(26,11,3,.95)'; for (const s of [-1, 1]) { g.beginPath(); g.ellipse(s * 52 * stem, lerp(top, bottom, 0.55) - 18 * stem, 52 * stem, 15 * stem, -s * 0.5, 0, TAU); g.fill(); } g.filter = 'none'; }
    const eye = m1 * (1 - m2); if (eye > 0.02) { g.filter = 'blur(3px)'; g.fillStyle = `rgba(255,236,170,${0.9 * eye})`; g.beginPath(); g.arc(0, 0, 0.2 * R, 0, TAU); g.fill(); g.filter = 'none'; }   // the flower's core is thin sand: light shows through
    const push = 4 * (m1 * (1 - m1) + m2 * (1 - m2));   // grains heaped along the edge while the sand is being swept
    for (let i = 0; i < 46 * push; i++) { const a = hash(i, f) * TAU, r = R * (0.9 + hash(i, f, 1) * 0.6); g.fillStyle = `rgba(30,13,4,${0.4 + hash(i, 2) * 0.5})`; g.beginPath(); g.arc(Math.cos(a) * r, Math.sin(a) * r * 0.85, 1.4 + hash(i, f, 3) * 2.4, 0, TAU); g.fill(); }
    g.restore();
    speckle(g, W, H, 41, 70, [50, 24, 6]); speckle(g, W, H, 42, 90, [255, 226, 150]);   // loose grains: dark on the light, bright pinholes in the dark
    g.save(); g.globalCompositeOperation = 'multiply'; const v = g.createRadialGradient(W / 2, H / 2, H * 0.32, W / 2, H / 2, H * 0.98); v.addColorStop(0, 'rgba(255,255,255,0)'); v.addColorStop(1, 'rgba(70,32,0,.5)'); g.fillStyle = v; g.fillRect(0, 0, W, H); g.restore();
  } },
};
export const IDS = Object.keys(LOOKS);
