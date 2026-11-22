// brief2mp4 art forms: looks-abstract.js, batch 6 (information and abstract). MIT. Same rules as looks.js: every look is
// a pure function of time, no clock, all randomness from hash(); the particle and field looks recompute every point from t.
import { TAU, clamp, lerp, prog, easeOut, easeInOut, overshoot, hash, frameOf, held, jit, circlePts, FONT } from './looks.js';
import { rgba, mix, speckle, vnoise } from './looks-painted.js';
import { path, polyFill, ell, star } from './looks-toon.js';

const BLK = '#14101a', BAUD = '"Arial Black", Impact, "Helvetica Neue", sans-serif';
const word = (g, s, x, y, size, col, alpha = 1) => { g.globalAlpha = alpha; g.fillStyle = col; g.font = `italic ${size}px "Times New Roman", Georgia, serif`; g.fillText(s, x, y); g.globalAlpha = 1; return g.measureText(s).width; };
const sampled = new Map();
// the points of a word, found once by drawing it small on a hidden canvas and keeping the pixels that are lit
function wordPoints(text, W, H, size) {
  const key = `${text}:${W}:${H}:${size}`; if (sampled.has(key)) return sampled.get(key);
  const c = new OffscreenCanvas(W, H), x = c.getContext('2d'); x.fillStyle = '#000'; x.fillRect(0, 0, W, H); x.fillStyle = '#fff'; x.font = `900 ${size}px ${BAUD}`; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(text, W / 2, H / 2);
  const d = x.getImageData(0, 0, W, H).data, pts = []; for (let y = 0; y < H; y += 4) for (let xx = 0; xx < W; xx += 4) if (d[(y * W + xx) * 4] > 128) pts.push([xx, y]);
  sampled.set(key, pts); return pts;
}

export const LOOKS = {
  /* ------------------------------------------------ information and abstract ------------------------------------------------ */
  'math-diagram': { kind: '2d', fps: null, draw(g, t, W, H) {
    // chalk on navy: an equation builds term by term, each term in its own colour with its own curve on the plot, the sum curve draws on, then a tangent line slides along it and its slope is read out
    g.fillStyle = '#10213f'; g.fillRect(0, 0, W, H); g.lineCap = 'round'; g.lineJoin = 'round'; g.textBaseline = 'alphabetic';
    const X = (x) => 500 + ((x + 3) / 8) * 420, Y = (y) => 470 - ((y + 3) / 11) * 380, f = (x) => 0.5 * x * x - x - 1, AMB = '#ffb43a', PNK = '#ff6fa8', BLU = '#6aa8ff', GLD = '#ffe066';
    g.strokeStyle = 'rgba(255,255,255,.1)'; g.lineWidth = 1; g.beginPath(); for (let x = -3; x <= 5; x++) { g.moveTo(X(x), Y(-3)); g.lineTo(X(x), Y(8)); } for (let y = -3; y <= 8; y++) { g.moveTo(X(-3), Y(y)); g.lineTo(X(5), Y(y)); } g.stroke();
    g.strokeStyle = 'rgba(255,255,255,.75)'; g.lineWidth = 2.4; g.beginPath(); g.moveTo(X(-3), Y(0)); g.lineTo(X(5), Y(0)); g.moveTo(X(0), Y(-3)); g.lineTo(X(0), Y(8)); g.stroke();
    const k = [prog(t, 0.3, 0.8), prog(t, 1.2, 0.8), prog(t, 2.1, 0.7)], curve = (fn, x0, x1, kk, col, lw) => { if (kk <= 0) return; g.strokeStyle = col; g.lineWidth = lw; g.beginPath(); const n = 60; for (let i = 0; i <= n * kk; i++) { const x = lerp(x0, x1, i / n), y = fn(x); i ? g.lineTo(X(x), Y(y)) : g.moveTo(X(x), Y(y)); } g.stroke(); };
    curve((x) => 0.5 * x * x, -3, 3.99, k[0], AMB, 2.6); curve((x) => -x, -3, 5, k[1], PNK, 2.6); curve(() => -1, -3, 5, k[2], BLU, 2.6); curve(f, -3, 5, easeInOut(prog(t, 2.8, 1.2)), '#fff', 4.4);
    let x = 46; const y = 190; x += word(g, 'f(x) = ', x, y, 60, '#fff', prog(t, 0, 0.4)); x += word(g, '½x²', x, y, 60, AMB, k[0]); x += word(g, ' − x', x, y, 60, PNK, k[1]); word(g, ' − 1', x, y, 60, BLU, k[2]);
    const tk = prog(t, 3.6, 0.5); if (tk > 0) {
      const x0 = 1 + 3.2 * Math.sin((t - 3.6) * 1.1 + 0.4), m = x0 - 1, y0 = f(x0); g.strokeStyle = GLD; g.lineWidth = 3.4; g.beginPath(); g.moveTo(X(x0 - 2.2), Y(y0 - 2.2 * m)); g.lineTo(X(x0 + 2.2), Y(y0 + 2.2 * m)); g.stroke(); g.fillStyle = GLD; g.beginPath(); g.arc(X(x0), Y(y0), 8, 0, TAU); g.fill();
      let tx = 46; tx += word(g, 'f′(x) = ', tx, 300, 48, '#fff', tk); tx += word(g, 'x − 1', tx, 300, 48, GLD, tk); word(g, ` = ${m.toFixed(1)}`, tx, 300, 48, '#fff', tk);
    }
    speckle(g, W, H, 3, 28, [255, 255, 255]);
  } },
  'sticker-explainer': { kind: '2d', fps: null, draw(g, t, W, H) {
    // die-cut stickers with a thick white border and a drop shadow, popping onto a desk with a bounce and then swaying a little; bold word stickers beside icons
    g.fillStyle = '#f2ede2'; g.fillRect(0, 0, W, H); g.fillStyle = 'rgba(0,0,0,.07)'; for (let y = 20; y < H; y += 30) for (let x = 20; x < W; x += 30) g.fillRect(x, y, 2, 2);
    const P = (fn) => { const p = new Path2D(); fn(p); return p; }, burst = P((p) => star(0, 0, 92, 68, 12, 0).forEach(([x, y], i) => (i ? p.lineTo(x, y) : p.moveTo(x, y)))), bulb = P((p) => { p.arc(0, -16, 56, 0, TAU); p.roundRect(-26, 28, 52, 40, 8); }), heart = P((p) => { p.moveTo(0, 60); p.bezierCurveTo(-110, -10, -50, -90, 0, -34); p.bezierCurveTo(50, -90, 110, -10, 0, 60); }), pill = P((p) => p.roundRect(-112, -42, 224, 84, 42)), badge = P((p) => p.arc(0, 0, 72, 0, TAU)), arrow = P((p) => { [[-90, -26], [20, -26], [20, -62], [92, 0], [20, 62], [20, 26], [-90, 26]].forEach(([x, y], i) => (i ? p.lineTo(x, y) : p.moveTo(x, y))); p.closePath(); }), speech = P((p) => { p.roundRect(-96, -56, 192, 104, 36); p.moveTo(-40, 46); p.lineTo(-62, 84); p.lineTo(-8, 46); });
    const text = (s, col, size) => { g.font = `900 ${size}px ${BAUD}`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillStyle = col; g.fillText(s, 0, 4); };
    const S = [[190, 140, -0.1, 0.2, burst, '#ffd23f', () => text('WOW!', BLK, 40)], [480, 130, 0.06, 0.5, bulb, '#ffe14d', () => { g.strokeStyle = BLK; g.lineWidth = 5; g.beginPath(); g.moveTo(-14, -16); g.lineTo(-6, 6); g.lineTo(6, -10); g.lineTo(14, 6); g.stroke(); g.fillStyle = '#9aa0ad'; g.fillRect(-20, 38, 40, 8); }], [770, 150, 0.1, 0.8, heart, '#ff4d6d', () => { g.fillStyle = 'rgba(255,255,255,.5)'; g.beginPath(); g.ellipse(-40, -30, 14, 8, -0.7, 0, TAU); g.fill(); }],
      [200, 320, 0.08, 1.1, pill, '#ff5a8a', () => text('SIMPLE', '#fff', 46)], [480, 320, -0.05, 1.4, arrow, '#3d7bff', () => {}], [760, 320, 0.05, 1.7, badge, '#35b868', () => text('100%', '#fff', 38)], [300, 460, -0.06, 2.0, pill, '#ffb02e', () => text('FAST', BLK, 52)], [650, 460, 0.07, 2.3, speech, '#fff', () => text('HI!', BLK, 54)]];
    for (const [x, y, rot, st, shape, col, paint] of S) {
      const k = overshoot(prog(t, st, 0.55)); if (k <= 0.001) continue; g.save(); g.translate(x, y + (1 - clamp(k)) * 30); g.rotate(rot + Math.sin(t * 2 + x) * 0.025 * clamp(t - st)); g.scale(k, k);
      g.shadowColor = 'rgba(40,30,20,.35)'; g.shadowBlur = 16; g.shadowOffsetX = 4; g.shadowOffsetY = 9; g.fillStyle = '#fff'; g.strokeStyle = '#fff'; g.lineWidth = 22; g.lineJoin = 'round'; g.stroke(shape); g.fill(shape); g.shadowColor = 'transparent'; g.fillStyle = col; g.fill(shape); g.lineWidth = 3; g.strokeStyle = 'rgba(0,0,0,.18)'; g.lineJoin = 'round'; g.stroke(shape); paint(); g.restore();
    }
  } },
  memphis: { kind: '2d', fps: 12, draw(g, t, W, H) {
    // 1980s Memphis design: squiggles and zigzags, confetti shapes in red, yellow, blue and pink, black-and-white checks, stripes and dots, scattered and drifting on twos over a peach ground
    const ts = held(t, 12), PAL = ['#ff3b30', '#ffd60a', '#1e6bff', '#ff6bb5', '#14101a'], O = '#14101a'; g.fillStyle = '#ffe8d6'; g.fillRect(0, 0, W, H); g.lineCap = 'round'; g.lineJoin = 'round';
    for (let i = 0; i < 150; i++) { g.fillStyle = PAL[Math.floor(hash(i, 1) * 5)]; g.save(); g.translate(hash(i, 2) * W, hash(i, 3) * H); g.rotate(hash(i, 4) * TAU); g.fillRect(-6, -1.5, 12, 3); g.restore(); }
    for (let i = 0; i < 40; i++) {
      const st = hash(i, 5) * 1.6, k = overshoot(prog(ts, st, 0.45)); if (k <= 0.01) continue; const kind = Math.floor(hash(i, 6) * 8), sz = 38 + hash(i, 7) * 62, x = 60 + hash(i, 8) * (W - 120), y = 50 + hash(i, 9) * (H - 100) + Math.sin(ts * 0.8 + i) * 12, col = PAL[Math.floor(hash(i, 10) * 4)];
      g.save(); g.translate(x, y); g.rotate(hash(i, 11) * TAU + ts * 0.5 * (i % 2 ? 1 : -1) * 0.4); g.scale(k, k); g.lineWidth = 5; g.strokeStyle = O; g.fillStyle = col;
      if (kind === 0) { polyFill(g, [[0, -sz / 2], [sz / 2, sz / 2], [-sz / 2, sz / 2]], col, O, 5); }
      else if (kind === 1) { ell(g, 0, 0, sz / 2, sz / 2, col, O, 5); }
      else if (kind === 2) { g.beginPath(); g.arc(0, 0, sz / 2, Math.PI, TAU); g.closePath(); g.fill(); g.stroke(); }
      else if (kind === 3) { g.lineWidth = 11; g.strokeStyle = col; g.beginPath(); for (let j = 0; j <= 20; j++) { const px = -sz + j * (sz / 10), py = Math.sin(j * 1.1) * 11; j ? g.lineTo(px, py) : g.moveTo(px, py); } g.stroke(); }
      else if (kind === 4) { g.lineWidth = 9; g.strokeStyle = O; g.beginPath(); for (let j = 0; j <= 6; j++) { const px = -sz + j * (sz / 3), py = (j % 2 ? 14 : -14); j ? g.lineTo(px, py) : g.moveTo(px, py); } g.stroke(); }
      else if (kind === 5) { g.fillStyle = '#fff'; g.fillRect(-sz / 2, -sz / 2, sz, sz); g.fillStyle = O; for (let a = 0; a < 4; a++) for (let b = 0; b < 4; b++) if ((a + b) % 2 === 0) g.fillRect(-sz / 2 + a * sz / 4, -sz / 2 + b * sz / 4, sz / 4, sz / 4); g.strokeRect(-sz / 2, -sz / 2, sz, sz); }
      else if (kind === 6) { g.save(); g.beginPath(); g.arc(0, 0, sz / 2, 0, TAU); g.clip(); g.fillStyle = '#fff'; g.fillRect(-sz, -sz, 2 * sz, 2 * sz); g.fillStyle = O; for (let a = -sz; a < sz; a += 14) g.fillRect(a, -sz, 6, 2 * sz); g.restore(); g.beginPath(); g.arc(0, 0, sz / 2, 0, TAU); g.stroke(); }
      else { g.fillStyle = col; g.fillRect(-sz / 2, -sz / 2, sz, sz); g.fillStyle = O; for (let a = 0; a < 4; a++) for (let b = 0; b < 4; b++) { g.beginPath(); g.arc(-sz * 0.375 + a * sz / 4, -sz * 0.375 + b * sz / 4, 3.4, 0, TAU); g.fill(); } g.strokeRect(-sz / 2, -sz / 2, sz, sz); }
      g.restore();
    }
  } },
  particles: { kind: '2d', fps: null, draw(g, t, W, H) {
    // about three thousand particles drift in from all over the frame and settle into a word, hold it, then burst apart and reform; each is a small glowing dot coloured by where it lands
    g.fillStyle = '#070912'; g.fillRect(0, 0, W, H); const pts = wordPoints('MOTION', W, H, 190), N = 3200, cyc = t % 6.2, gather = easeInOut(clamp(cyc / 2.2)), burst = clamp((cyc - 3.4) / 1.6), hold = Math.sin(t * 3) * 1.2;
    g.globalCompositeOperation = 'lighter';
    for (let i = 0; i < N; i++) {
      const tg = pts[(i * 7) % pts.length], off = clamp(gather * 1.25 - hash(i, 1) * 0.25), e = easeOut(off), sx = hash(i, 2) * W, sy = hash(i, 3) * H, ang = hash(i, 4) * TAU, far = 200 + hash(i, 5) * 520;
      let x = lerp(sx, tg[0] + (hash(i, 6) - 0.5) * 3, e), y = lerp(sy, tg[1] + (hash(i, 7) - 0.5) * 3, e); if (e > 0.95) { x += Math.sin(t * 2 + i) * hold; y += Math.cos(t * 2.3 + i) * hold; }
      if (burst > 0) { const b = burst ** 1.8; x += Math.cos(ang + b * 1.5) * far * b; y += Math.sin(ang + b * 1.5) * far * b; }
      const u = tg[0] / W, col = u < 0.5 ? mix([255, 190, 70], [255, 80, 160], u * 2) : mix([255, 80, 160], [90, 150, 255], (u - 0.5) * 2), a = (0.4 + 0.5 * e) * (1 - burst * 0.5);
      g.fillStyle = rgba(col, a); g.fillRect(x - 1.4, y - 1.4, 2.8, 2.8);
    }
    g.globalCompositeOperation = 'source-over';
  } },
  'liquid-metaball': { kind: '2d', fps: null, draw(g, t, W, H) {
    // glossy liquid blobs that drift, merge and split: a field is summed from seven soft circles, thresholded, and lit with a rim, a highlight and a smooth warm-to-violet colour gradient
    const w = 240, h = 135, F = new Float32Array(w * h), img = new ImageData(w, h), B = [];
    for (let i = 0; i < 7; i++) B.push([w * (0.5 + 0.34 * Math.sin(t * (0.5 + i * 0.13) + i * 1.7)), h * (0.5 + 0.34 * Math.cos(t * (0.42 + i * 0.11) + i * 2.3)), 15 + (i % 3) * 5]);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { let s = 0; for (const [bx, by, r] of B) s += (r * r) / ((x - bx) ** 2 + (y - by) ** 2 + 1); F[y * w + x] = s; }
    const G = F.map((v) => Math.tanh(v * 0.55) * 2.4);   // a saturating copy for the surface normal: the field spikes at each blob's centre, and this keeps the tops round, not pitted
    const Lg = [-0.5, -0.6, 0.62];
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const i = y * w + x, bgk = y / h, a = clamp((F[i] - 0.92) / 0.16); let r = lerp(18, 44, bgk), gg = lerp(10, 14, bgk), b = lerp(42, 90, bgk);
      if (a > 0) {
        const gx = (G[i + 1] ?? G[i]) - (G[i - 1] ?? G[i]), gy = (G[i + w] ?? G[i]) - (G[i - w] ?? G[i]), nl = Math.hypot(gx, gy, 0.35), nx = -gx / nl, ny = -gy / nl, nz = 0.35 / nl, diff = Math.max(0, nx * Lg[0] + ny * Lg[1] + nz * Lg[2]), hx = nx * Lg[0] + ny * Lg[1] + nz * (Lg[2] + 1), spec = Math.max(0, hx / (Math.hypot(...Lg.map((v, k) => v + (k === 2 ? 1 : 0))) || 1)) ** 40, rim = (1 - nz) ** 2;
        const base = mix(mix([255, 61, 129], [255, 159, 28], x / w), [122, 92, 255], y / h), env = 0.35 + 0.65 * Math.max(0, ny) ** 0.8;
        r = lerp(r, base[0] * (0.25 + 0.75 * diff) + 120 * rim * env + 255 * spec, a); gg = lerp(gg, base[1] * (0.25 + 0.75 * diff) + 90 * rim * env + 255 * spec, a); b = lerp(b, base[2] * (0.25 + 0.75 * diff) + 160 * rim * env + 255 * spec, a);
      }
      img.data[i * 4] = r; img.data[i * 4 + 1] = gg; img.data[i * 4 + 2] = b; img.data[i * 4 + 3] = 255;
    }
    const sc = new OffscreenCanvas(w, h); sc.getContext('2d').putImageData(img, 0, 0); g.imageSmoothingEnabled = true; g.drawImage(sc, 0, 0, W, H);
  } },
  'flow-field': { kind: '2d', fps: null, draw(g, t, W, H) {
    // about three thousand short strokes follow a drifting noise field: they are laid down inside a circle so that an orb of swirling lines builds up, in warm and violet inks on a dark ground
    g.fillStyle = '#0d0f1c'; g.fillRect(0, 0, W, H); g.lineCap = 'round'; const N = 3400, shown = Math.floor(N * easeOut(prog(t, 0, 3.4))), PAL = [[255, 122, 89], [255, 193, 90], [246, 242, 235], [138, 123, 255], [255, 77, 154]];
    const ang = (x, y) => (vnoise(x / 150, y / 150 + t * 0.08, 7) * 2 + vnoise(x / 60, y / 60, 9) * 0.6) * TAU;
    for (let i = 0; i < shown; i++) {
      const r = (hash(i, 1) ** 0.6) * 215, th = hash(i, 2) * TAU, outside = hash(i, 3) > 0.9, rr = outside ? 215 + hash(i, 4) * 150 : r; let x = 480 + Math.cos(th) * rr, y = 270 + Math.sin(th) * rr * 0.9; const col = PAL[Math.floor(hash(i, 5) * 5)], a = outside ? 0.22 : 0.45 + 0.3 * (1 - r / 215);
      g.strokeStyle = rgba(col, a); g.lineWidth = 1.2 + hash(i, 6) * 1.2; g.beginPath(); g.moveTo(x, y);
      for (let s = 0; s < 14; s++) { const an = ang(x, y); x += Math.cos(an) * 5; y += Math.sin(an) * 5; g.lineTo(x, y); } g.stroke();
    }
  } },
  psychedelic: { kind: '2d', fps: null, draw(g, t, W, H) {
    // a 1960s concert poster: concentric rings warped by slow waves, filled in a cycling run of warm saturated colours with black ink lines, over rays that turn behind them
    const PAL = [[255, 77, 28], [255, 158, 27], [255, 213, 31], [255, 61, 143], [138, 43, 217], [255, 107, 107], [255, 179, 198]], cx = 480, cy = 270, sh = t * 2.2, base = Math.floor(sh), fr = sh - base;
    const colAt = (k) => rgba(mix(PAL[(k + base) % 7], PAL[(k + base + 1) % 7], fr)); g.lineJoin = 'round';
    for (let i = 0; i < 36; i++) { const a0 = (i / 36) * TAU + t * 0.12, a1 = a0 + TAU / 36; g.fillStyle = i % 2 ? '#ffb347' : '#ff4d8f'; g.beginPath(); g.moveTo(cx, cy); g.lineTo(cx + Math.cos(a0) * 900, cy + Math.sin(a0) * 900); g.lineTo(cx + Math.cos(a1) * 900, cy + Math.sin(a1) * 900); g.closePath(); g.fill(); }
    for (let k = 17; k >= 0; k--) {
      g.beginPath(); for (let j = 0; j <= 120; j++) { const a = (j / 120) * TAU, r = 28 + k * 25 + Math.sin(a * 5 + t * 1.3 + k * 0.35) * (6 + k * 1.6) + Math.sin(a * 3 - t * 0.9 + k * 0.2) * (4 + k * 1.1); j ? g.lineTo(cx + Math.cos(a) * r, cy + Math.sin(a) * r * 0.92) : g.moveTo(cx + Math.cos(a) * r, cy + Math.sin(a) * r * 0.92); }
      g.closePath(); g.fillStyle = colAt(k); g.fill(); g.strokeStyle = '#1a0a24'; g.lineWidth = 3.4; g.stroke();
    }
    g.fillStyle = '#1a0a24'; g.beginPath(); g.arc(cx, cy, 16, 0, TAU); g.fill();
  } },
  bauhaus: { kind: '2d', fps: 12, draw(g, t, W, H) {
    // a poster of primary-colour circles, squares and triangles with black bars on a grid of cream and black lines; every piece jumps cell by cell in clean steps, and each step settles quickly
    const ts = held(t, 12), CELL = 80, RED = '#d62828', YEL = '#f7b32b', BLU = '#1d4ea1', K = '#111', step = ts * 1.6, si = Math.floor(step), fr = step - si, e = easeOut(clamp(fr / 0.3));
    g.fillStyle = '#f0e6d0'; g.fillRect(0, 0, W, H); g.strokeStyle = 'rgba(17,17,17,.22)'; g.lineWidth = 1; g.beginPath(); for (let x = 0; x <= W; x += CELL) { g.moveTo(x, 0); g.lineTo(x, H); } for (let y = 0; y <= H; y += CELL) { g.moveTo(0, y); g.lineTo(W, y); } g.stroke();
    const at = (route) => { const a = route[si % route.length], b = route[(si + 1) % route.length]; return [lerp(a[0], b[0], e) * CELL, lerp(a[1], b[1], e) * CELL]; };
    const bar = (route, w, h) => { const [x, y] = at(route); g.fillStyle = K; g.fillRect(x, y, w * CELL, h * CELL); };
    bar([[0, 5], [0, 4], [1, 4], [0, 4]], 6, 0.35); bar([[8, 0], [9, 0], [9, 1], [8, 1]], 0.35, 5); bar([[5, 2], [5, 3], [4, 3], [5, 3]], 5, 0.25);
    { const [x, y] = at([[1, 1], [3, 1], [3, 3], [1, 3]]); g.fillStyle = YEL; g.fillRect(x, y, 2 * CELL, 2 * CELL); g.strokeStyle = K; g.lineWidth = 4; g.strokeRect(x, y, 2 * CELL, 2 * CELL); }
    { const [x, y] = at([[6, 2], [6, 4], [8, 4], [8, 2]]); g.fillStyle = RED; g.beginPath(); g.arc(x + CELL, y + CELL, CELL * 1.5, 0, TAU); g.fill(); g.fillStyle = K; g.beginPath(); g.arc(x + CELL, y + CELL, CELL * 0.45, 0, TAU); g.fill(); }
    { const [x, y] = at([[2, 4], [2, 5], [0, 5], [0, 4]]); g.fillStyle = BLU; g.beginPath(); g.moveTo(x, y + 2 * CELL); g.lineTo(x + 2 * CELL, y + 2 * CELL); g.lineTo(x + CELL, y); g.closePath(); g.fill(); }
    { const [x, y] = at([[9, 4], [10, 4], [10, 2], [9, 2]]); g.fillStyle = BLU; g.beginPath(); g.arc(x + CELL, y + CELL, CELL, Math.PI, TAU); g.closePath(); g.fill(); g.fillStyle = YEL; g.beginPath(); g.arc(x + CELL, y + CELL, CELL * 0.5, Math.PI, TAU); g.closePath(); g.fill(); }
    { const [x, y] = at([[4, 0], [4, 1], [5, 1], [6, 0]]); g.fillStyle = K; g.beginPath(); g.arc(x + CELL / 2, y + CELL / 2, CELL / 2, 0, TAU); g.fill(); }
    { const [x, y] = at([[3, 5], [4, 5], [4, 4], [3, 4]]); g.fillStyle = RED; g.fillRect(x, y, CELL, CELL); g.fillStyle = '#f0e6d0'; g.beginPath(); g.arc(x + CELL, y + CELL, CELL * 0.8, Math.PI, Math.PI * 1.5); g.lineTo(x + CELL, y + CELL); g.fill(); }
    { const [x, y] = at([[10, 5], [10, 6], [9, 6], [9, 5]]); g.fillStyle = YEL; g.beginPath(); g.moveTo(x, y + CELL); g.lineTo(x + CELL, y); g.lineTo(x + CELL, y + CELL); g.closePath(); g.fill(); }
    speckle(g, W, H, 5, 20, [90, 70, 40]);
  } },
};
export const IDS = Object.keys(LOOKS);
