/*
 * shapes.js: turns the shape records in a character file into path strings, and gives skins the tools they need:
 * a path parser, seeded jitter, bounds, a point transform, colour mixing and the lip-sync mouth drawings.
 * Paths use absolute M, L, C, Q and Z only, so a skin can move every point (line boil, paper wobble) without
 * a full SVG parser.
 */
(function (g) {
  'use strict';
  if (typeof require === 'function' && !(g.B2M && g.B2M.hash)) { require('./poses.js'); require('./rig.js'); }
  const B = (g.B2M = g.B2M || {});
  const K = 0.5523;
  const fmt = (v) => String(Math.round(v * 100) / 100);
  const pt = (x, y) => fmt(x) + ' ' + fmt(y);

  function ellipsePath(cx, cy, rx, ry, rot) {
    const c = Math.cos(B.rad(rot || 0)), s = Math.sin(B.rad(rot || 0));
    const P = (x, y) => pt(cx + x * c - y * s, cy + x * s + y * c);
    return 'M' + P(rx, 0) + 'C' + P(rx, ry * K) + ' ' + P(rx * K, ry) + ' ' + P(0, ry) + 'C' + P(-rx * K, ry) + ' ' + P(-rx, ry * K) + ' ' + P(-rx, 0)
      + 'C' + P(-rx, -ry * K) + ' ' + P(-rx * K, -ry) + ' ' + P(0, -ry) + 'C' + P(rx * K, -ry) + ' ' + P(rx, -ry * K) + ' ' + P(rx, 0) + 'Z';
  }

  function capsulePath(a, b, ra, rb) {
    const dx = b[0] - a[0], dy = b[1] - a[1], len = Math.hypot(dx, dy) || 1, ux = dx / len, uy = dy / len, nx = -uy, ny = ux;
    const A1 = [a[0] + nx * ra, a[1] + ny * ra], A2 = [a[0] - nx * ra, a[1] - ny * ra];
    const B1 = [b[0] + nx * rb, b[1] + ny * rb], B2 = [b[0] - nx * rb, b[1] - ny * rb];
    const cap = (p, q, r, dirx, diry) => pt(p[0] + dirx * r * 1.333, p[1] + diry * r * 1.333) + ' ' + pt(q[0] + dirx * r * 1.333, q[1] + diry * r * 1.333) + ' ' + pt(q[0], q[1]);
    return 'M' + pt(A1[0], A1[1]) + 'L' + pt(B1[0], B1[1]) + 'C' + cap(B1, B2, rb, ux, uy) + 'L' + pt(A2[0], A2[1]) + 'C' + cap(A2, A1, ra, -ux, -uy) + 'Z';
  }

  function rectPath(x, y, w, h, r) {
    const q = Math.min(r || 0, w / 2, h / 2);
    if (!q) return 'M' + pt(x, y) + 'L' + pt(x + w, y) + 'L' + pt(x + w, y + h) + 'L' + pt(x, y + h) + 'Z';
    return 'M' + pt(x + q, y) + 'L' + pt(x + w - q, y) + 'Q' + pt(x + w, y) + ' ' + pt(x + w, y + q) + 'L' + pt(x + w, y + h - q) + 'Q' + pt(x + w, y + h) + ' ' + pt(x + w - q, y + h)
      + 'L' + pt(x + q, y + h) + 'Q' + pt(x, y + h) + ' ' + pt(x, y + h - q) + 'L' + pt(x, y + q) + 'Q' + pt(x, y) + ' ' + pt(x + q, y) + 'Z';
  }

  // Straight corners, or a smooth curve through the points (Catmull-Rom turned into cubic curves).
  function polyPath(pts, smooth, closed) {
    const n = pts.length, isClosed = closed !== false;
    if (!smooth) return 'M' + pt(pts[0][0], pts[0][1]) + pts.slice(1).map((p) => 'L' + pt(p[0], p[1])).join('') + (isClosed ? 'Z' : '');
    const at = (i) => (isClosed ? pts[((i % n) + n) % n] : pts[Math.min(n - 1, Math.max(0, i))]);
    let d = 'M' + pt(pts[0][0], pts[0][1]);
    const segs = isClosed ? n : n - 1;
    for (let i = 0; i < segs; i++) {
      const p0 = at(i - 1), p1 = at(i), p2 = at(i + 1), p3 = at(i + 2);
      d += 'C' + pt(p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6) + ' ' + pt(p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6) + ' ' + pt(p2[0], p2[1]);
    }
    return d + (isClosed ? 'Z' : '');
  }

  // A cache that forgets the least recently used entry, so a long film never grows without bound.
  function lru(max) {
    const m = new Map();
    return {
      get(k) { const v = m.get(k); if (v !== undefined) { m.delete(k); m.set(k, v); } return v; },
      set(k, v) { m.set(k, v); if (m.size > max) m.delete(m.keys().next().value); },
      get size() { return m.size; },
    };
  }

  const PATH_CACHE = lru(800);
  function shapePath(s) {
    if (s.type === 'path') return s.d;
    const key = JSON.stringify(s, ['type', 'c', 'r', 'rot', 'a', 'b', 'ra', 'rb', 'x', 'y', 'w', 'h', 'pts', 'smooth', 'closed']);
    let d = PATH_CACHE.get(key);
    if (d) return d;
    if (s.type === 'circle') d = ellipsePath(s.c[0], s.c[1], s.r, s.r, 0);
    else if (s.type === 'ellipse') d = ellipsePath(s.c[0], s.c[1], s.r[0], s.r[1], s.rot);
    else if (s.type === 'capsule') d = capsulePath(s.a, s.b, s.ra, s.rb === undefined ? s.ra : s.rb);
    else if (s.type === 'rect') d = rectPath(s.x, s.y, s.w, s.h, s.r);
    else if (s.type === 'poly') d = polyPath(s.pts, s.smooth, s.closed);
    else throw new Error('unknown shape type "' + s.type + '"');
    PATH_CACHE.set(key, d);
    return d;
  }

  const ARGS = { M: 2, L: 2, C: 6, Q: 4, Z: 0 };
  const PARSED = lru(600);
  function parsePath(d) {
    let out = PARSED.get(d);
    if (out) return out;
    out = [];
    const re = /([MLCQZ])([^MLCQZ]*)/g;
    let m;
    while ((m = re.exec(d))) {
      const nums = (m[2].match(/-?\d*\.?\d+(?:e[-+]?\d+)?/gi) || []).map(Number);
      const pts = [];
      for (let i = 0; i + 1 < nums.length; i += 2) pts.push([nums[i], nums[i + 1]]);
      out.push({ c: m[1], pts });
    }
    PARSED.set(d, out);
    return out;
  }

  function mapPoints(d, fn) {
    let i = 0;
    return parsePath(d).map((seg) => seg.c + seg.pts.map((p) => { const q = fn(p[0], p[1], i++); return pt(q[0], q[1]); }).join(' ')).join('');
  }

  // Move every point by a seeded amount: the same (key, frame) always gives the same wobble.
  function jitterPath(d, key, frame, amount) {
    return mapPoints(d, (x, y, i) => [x + (B.hash(key + 'x', frame * 131 + i) - 0.5) * 2 * amount, y + (B.hash(key + 'y', frame * 131 + i) - 0.5) * 2 * amount]);
  }

  function pathBounds(d) {
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    parsePath(d).forEach((s) => s.pts.forEach((p) => { x0 = Math.min(x0, p[0]); y0 = Math.min(y0, p[1]); x1 = Math.max(x1, p[0]); y1 = Math.max(y1, p[1]); }));
    return { x0, y0, x1, y1, w: x1 - x0, h: y1 - y0, cx: (x0 + x1) / 2, cy: (y0 + y1) / 2 };
  }

  // ---- colour ----
  const channel = (v) => { const u = v / 255; return u <= 0.03928 ? u / 12.92 : Math.pow((u + 0.055) / 1.055, 2.4); };
  // Relative luminance (WCAG) of '#rrggbb' or [r, g, b], and the contrast ratio between two colours: 1 (the same) to 21.
  const luminance = (c) => { const r = typeof c === 'string' ? toRgb(c) : c; return 0.2126 * channel(r[0]) + 0.7152 * channel(r[1]) + 0.0722 * channel(r[2]); };
  const contrast = (a, b) => { const x = luminance(a), y = luminance(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
  const toRgb = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
  const toHex = (rgb) => '#' + rgb.map((v) => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, '0')).join('');
  const mix = (a, b, k) => { const p = toRgb(a), q = toRgb(b); return toHex(p.map((v, i) => v + (q[i] - v) * k)); };

  const DEFAULT_PALETTE = { ink: '#1d1a22', mouth: '#5b1f26', teeth: '#fff8ee', tongue: '#d8606a', lip: '#d9605b', white: '#fffaf0' };
  const colorOf = (character, key) => (key ? character.palette[key] || DEFAULT_PALETTE[key] || '#ff00ff' : null);

  // ---- the mouth: nine drawings from one table ----
  function lipShapes(cfg, pivot, viseme, smile) {
    const P = B.VISEME_SHAPE[viseme] || B.VISEME_SHAPE.rest, size = cfg.size || 1;
    const cx = pivot[0], cy = pivot[1], w = 10 * size * P.w, h = 9 * size * P.open, s = smile || 0;
    const cornerY = cy - s * 3 * size * (1 - P.round * 0.6), ctrl = cy + s * 4 * size;
    if (h < 0.5) {
      if (P.press) {   // lips pressed together: a flat pink pad with a seam
        return [{ type: 'ellipse', c: [cx, cy], r: [w * 0.92, 2.6 * size], fill: 'lip', stroke: 'ink', sw: 1.1 * size, role: 'mouth' },
          { type: 'path', d: 'M' + pt(cx - w * 0.8, cy) + 'L' + pt(cx + w * 0.8, cy), fill: null, stroke: 'ink', sw: 1.2 * size, role: 'line' }];
      }
      const d = 'M' + pt(cx - w, cornerY) + 'Q' + pt(cx, ctrl) + ' ' + pt(cx + w, cornerY);
      return [{ type: 'path', d, fill: null, stroke: 'ink', sw: 1.5 * size, role: 'line' }];
    }
    const top = cy - h * 0.35, bot = cy + h * 0.65;
    const open = P.round > 0.5 ? { type: 'ellipse', c: [cx, cy + h * 0.1], r: [w * 0.85, h * 0.55] }
      : { type: 'path', d: 'M' + pt(cx - w, cornerY) + 'Q' + pt(cx, top - h * 0.25) + ' ' + pt(cx + w, cornerY) + 'C' + pt(cx + w * 0.8, bot + h * 0.3) + ' ' + pt(cx - w * 0.8, bot + h * 0.3) + ' ' + pt(cx - w, cornerY) + 'Z' };
    const out = [Object.assign(open, { fill: 'mouth', stroke: 'ink', sw: 1.2 * size, role: 'mouth' })];
    const th = h * 0.42 * P.teeth;
    if (P.teeth && P.round < 0.5) {
      const y = P.lip ? bot - h * 0.55 : top + h * 0.1;
      out.push({ type: 'rect', x: cx - w * 0.62, y, w: w * 1.24, h: Math.max(1.6, th), r: 1, fill: 'teeth', stroke: null, role: 'mouth' });
    }
    if (P.tongue && h > 4) {
      const ty = P.tongueUp ? top + h * 0.1 + th + h * 0.16 : bot - h * 0.2;
      out.push({ type: 'ellipse', c: [cx, ty], r: [w * 0.46, h * 0.2], fill: 'tongue', stroke: null, role: 'mouth' });
    }
    if (P.lip) out.push({ type: 'ellipse', c: [cx, bot - h * 0.04], r: [w * 0.8, h * 0.22], fill: 'lip', stroke: 'ink', sw: 0.9 * size, role: 'mouth' });
    return out;
  }

  Object.assign(B, { cacheStats: () => ({ parsed: PARSED.size, shapes: PATH_CACHE.size }), luminance, contrast, shapePath, parsePath, mapPoints, jitterPath, pathBounds, ellipsePath, polyPath, rectPath, capsulePath, mix, toRgb, toHex, colorOf, DEFAULT_PALETTE, lipShapes, fmt });
  if (typeof module !== 'undefined' && module.exports) module.exports = B;
})(globalThis);
