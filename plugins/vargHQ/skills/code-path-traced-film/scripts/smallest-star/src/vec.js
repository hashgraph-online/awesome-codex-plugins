// tiny vector and easing helpers
export const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
export const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
export const mul = (a, s) => [a[0] * s, a[1] * s, a[2] * s];
export const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
export const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
export const len = (a) => Math.hypot(a[0], a[1], a[2]);
export const norm = (a) => { const l = len(a) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
export const lerp = (a, b, t) => a + (b - a) * t;
export const lerp3 = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const sstep = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
export const ease = (t) => { t = clamp(t); return t * t * t * (t * (6 * t - 15) + 10); };
export const easeOut = (t) => { t = clamp(t); return 1 - (1 - t) * (1 - t) * (1 - t); };
export const easeIn = (t) => { t = clamp(t); return t * t * t; };
export const remap = (x, a, b) => clamp((x - a) / (b - a));

// Catmull-Rom through points, u in 0..1
export function spline(pts, u) {
  const n = pts.length - 1; const x = clamp(u) * n; const i = Math.min(n - 1, Math.floor(x)); const t = x - i;
  const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(n, i + 2)];
  const out = [0, 0, 0];
  for (let k = 0; k < 3; k++) {
    out[k] = 0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t * t + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t * t * t);
  }
  return out;
}

// local frame as mat3 columns: x = forward, y = up, z = side
export function frame(fwd, upHint = [0, 1, 0]) {
  const f = norm(fwd);
  let s = cross(f, upHint);
  if (len(s) < 1e-4) s = cross(f, [1, 0, 0]);
  s = norm(s);
  const u = cross(s, f);
  return [f[0], f[1], f[2], u[0], u[1], u[2], s[0], s[1], s[2]];
}
export const mat3mul = (m, v) => [m[0] * v[0] + m[3] * v[1] + m[6] * v[2], m[1] * v[0] + m[4] * v[1] + m[7] * v[2], m[2] * v[0] + m[5] * v[1] + m[8] * v[2]];

// smooth deterministic noise for hand-held drift and flight wobble
export function wob(t, seed) {
  return Math.sin(t * 1.31 + seed * 12.9) * 0.5 + Math.sin(t * 2.27 + seed * 7.1) * 0.3 + Math.sin(t * 3.71 + seed * 3.3) * 0.2;
}
