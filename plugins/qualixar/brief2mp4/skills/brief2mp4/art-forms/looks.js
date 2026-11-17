// brief2mp4 art forms: looks.js. MIT. One small, deterministic demo per art form.
//
// Every look is a pure function of time: draw(g, t, W, H) paints the frame for second t and keeps nothing
// from the frame before. Render the same t twice and the pixels are identical, which is what a frame-by-frame
// renderer such as HyperFrames needs. Three rules make that true, and they are the rules for your own scenes:
//   1. no clock, no timers, no Math.random(): randomness comes from hash(), keyed by position or frame number;
//   2. handmade looks quantise time (onTwos, held) so the picture changes 8 to 12 times a second
//      while the video itself stays at 24 or 30 frames a second;
//   3. wobble, boil, flicker and misregistration are seeded by the frame number, so they repeat exactly.
// 2D looks draw on a canvas context. 3D looks get THREE and build a scene once, then pose it from t.
// Wire a look into HyperFrames the way references/threejs.md shows: a paused GSAP timeline tweens a plain
// object's t from 0 to the duration with ease "none", and its onUpdate calls draw.

export const TAU = Math.PI * 2;
export const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
export const lerp = (a, b, k) => a + (b - a) * k;
export const prog = (t, start, dur) => clamp((t - start) / dur);          // 0..1 while t runs from start to start + dur
export const easeOut = (k) => 1 - (1 - k) ** 3;
export const easeInOut = (k) => (k < 0.5 ? 4 * k * k * k : 1 - (-2 * k + 2) ** 3 / 2);
export const overshoot = (k) => 1 + 2.70158 * (k - 1) ** 3 + 1.70158 * (k - 1) ** 2;
export const bounce = (k) => { const n = 7.5625, d = 2.75; if (k < 1 / d) return n * k * k; if (k < 2 / d) return n * (k -= 1.5 / d) * k + 0.75; if (k < 2.5 / d) return n * (k -= 2.25 / d) * k + 0.9375; return n * (k -= 2.625 / d) * k + 0.984375; };
// a repeatable number in 0..1 from up to three integers: the only source of "randomness"
export function hash(a, b = 0, c = 0) { let n = (Math.imul(a | 0, 374761393) + Math.imul(b | 0, 668265263) + Math.imul(c | 0, 2147483647)) | 0; n = Math.imul(n ^ (n >>> 13), 1274126177); return ((n ^ (n >>> 16)) >>> 0) / 4294967295; }
export const frameOf = (t, fps) => Math.floor(t * fps + 1e-6);             // which drawing we are on
export const held = (t, fps) => frameOf(t, fps) / fps;                     // time, quantised: "on twos" is held(t, 12)
export const onTwos = (t) => held(t, 12);
export const jit = (frame, i, amount) => (hash(frame, i, 7) - 0.5) * 2 * amount;   // a seeded nudge

// textures are drawn once and cached; they depend only on their arguments
const cache = new Map();
export function grain(w, h, seed = 1, strength = 28, tint = [0, 0, 0]) {
  const key = `g${w}x${h}:${seed}:${strength}:${tint}`; if (cache.has(key)) return cache.get(key);
  const c = new OffscreenCanvas(w, h), g = c.getContext('2d'), im = g.createImageData(w, h);
  for (let i = 0; i < w * h; i++) { const v = hash(i, seed); im.data[i * 4] = tint[0]; im.data[i * 4 + 1] = tint[1]; im.data[i * 4 + 2] = tint[2]; im.data[i * 4 + 3] = v * strength; }
  g.putImageData(im, 0, 0); cache.set(key, c); return c;
}
// a closed blob outline: a circle whose radius wobbles by a few seeded sine waves (paper, felt, watercolour)
export function blob(g, x, y, r, seed, rough = 0.12, steps = 48) {
  g.beginPath();
  for (let i = 0; i <= steps; i++) {
    const a = (i / steps) * TAU;
    const k = 1 + rough * (Math.sin(a * 3 + hash(seed) * 6) * 0.5 + Math.sin(a * 7 + hash(seed, 1) * 6) * 0.3 + Math.sin(a * 13 + hash(seed, 2) * 6) * 0.2);
    const px = x + Math.cos(a) * r * k, py = y + Math.sin(a) * r * k; i ? g.lineTo(px, py) : g.moveTo(px, py);
  }
  g.closePath();
}
// a polygon with slightly nudged corners: a shape cut with scissors
export function cut(g, pts, seed, amount = 2.5) {
  g.beginPath(); pts.forEach(([x, y], i) => { const px = x + jit(seed, i, amount), py = y + jit(seed, i + 99, amount); i ? g.lineTo(px, py) : g.moveTo(px, py); }); g.closePath();
}
// draw the first k (0..1) of a polyline, each point optionally nudged by a seeded wobble (the "boil")
export function strokePart(g, pts, k, frame = 0, wobble = 0) {
  const n = pts.length - 1, upto = clamp(k) * n; if (upto <= 0) return;
  g.beginPath();
  for (let i = 0; i <= Math.floor(upto); i++) { const x = pts[i][0] + jit(frame, i, wobble), y = pts[i][1] + jit(frame, i + 500, wobble); i ? g.lineTo(x, y) : g.moveTo(x, y); }
  const i = Math.floor(upto), f = upto - i;
  if (i < n) g.lineTo(lerp(pts[i][0], pts[i + 1][0], f) + jit(frame, i, wobble), lerp(pts[i][1], pts[i + 1][1], f) + jit(frame, i + 500, wobble));
  g.stroke();
}
const circlePts = (x, y, r, n = 40, from = 0, to = TAU) => Array.from({ length: n + 1 }, (_, i) => [x + Math.cos(lerp(from, to, i / n)) * r, y + Math.sin(lerp(from, to, i / n)) * r]);
const fill = (g, c) => { g.fillStyle = c; g.fill(); };
const bg = (g, W, H, c) => { g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1; g.filter = 'none'; g.shadowColor = 'transparent'; g.fillStyle = c; g.fillRect(0, 0, W, H); };
const paper = (g, W, H, seed = 3, strength = 26) => { g.save(); g.globalCompositeOperation = 'multiply'; g.drawImage(grain(W, H, seed, strength, [60, 40, 20]), 0, 0); g.restore(); };
const FONT = '"Helvetica Neue", Arial, sans-serif';

export const LOOKS = {
  /* ------------------------------------------------ craft and handmade ------------------------------------------------ */
  'stop-motion': { kind: '2d', fps: 12, draw(g, t, W, H) {
    // blocks stack one by one. Time is held on twos, every pose is nudged a pixel, and the light flickers per frame.
    const f = frameOf(t, 12), ts = held(t, 12);
    bg(g, W, H, `hsl(34 30% ${86 + jit(f, 1, 1.2)}%)`);
    g.fillStyle = '#c9b48f'; g.fillRect(0, H * 0.74, W, H * 0.26);
    const cols = ['#c0392b', '#e0a526', '#2f6f8f', '#3d8b5a', '#7a4fa0'];
    for (let i = 0; i < 5; i++) {
      const k = bounce(prog(ts, 0.25 + i * 0.42, 0.5)); if (prog(ts, 0.25 + i * 0.42, 0.5) <= 0) continue;
      const x = W / 2 - 70 + (i % 2) * 34 + jit(f, i, 1.2), y = lerp(-90, H * 0.74 - 62 - i * 62, k) + jit(f, i + 9, 1.2);
      g.save(); g.translate(x + 60, y + 31); g.rotate(jit(f, i + 20, 0.012) + (i % 2 ? 0.03 : -0.02));
      g.shadowColor = 'rgba(60,40,10,.35)'; g.shadowBlur = 10; g.shadowOffsetY = 6; g.fillStyle = cols[i]; g.fillRect(-60, -31, 120, 62);
      g.shadowColor = 'transparent'; g.fillStyle = 'rgba(255,255,255,.14)'; g.fillRect(-60, -31, 120, 12); g.restore();
    }
    paper(g, W, H, 5, 18);
  } },
  'paper-cutout': { kind: '2d', fps: 12, draw(g, t, W, H) {
    // flat layers with scissor-cut edges and small shadows; the bird's wings hinge at the shoulder, on twos
    const ts = onTwos(t), f = frameOf(t, 12);
    bg(g, W, H, '#f3e6c8');
    const layer = (pts, col, seed, dy) => { g.save(); g.shadowColor = 'rgba(70,40,10,.38)'; g.shadowBlur = 5; g.shadowOffsetX = 3; g.shadowOffsetY = 4; cut(g, pts.map(([x, y]) => [x, y + dy]), seed, 3); fill(g, col); g.restore(); };
    g.save(); g.shadowColor = 'rgba(70,40,10,.3)'; g.shadowBlur = 4; g.shadowOffsetY = 3; blob(g, W * 0.76, H * 0.26, 62, 4, 0.03); fill(g, '#e9763b'); g.restore();
    layer([[0, 330], [170, 250], [330, 300], [520, 230], [720, 290], [960, 240], [960, 540], [0, 540]], '#7fa27a', 11, Math.sin(ts * 1.2) * 3);
    layer([[0, 400], [210, 340], [400, 390], [610, 330], [800, 380], [960, 350], [960, 540], [0, 540]], '#4f7d67', 12, Math.sin(ts * 1.2 + 1) * 4);
    layer([[0, 470], [250, 430], [500, 470], [760, 430], [960, 460], [960, 540], [0, 540]], '#2f5a52', 13, 0);
    const bx = lerp(-80, W + 80, (ts / 3) % 1), by = 150 + Math.sin(ts * 3) * 22, flap = Math.sin(ts * 14) * 0.7;
    g.save(); g.translate(bx, by); g.shadowColor = 'rgba(70,40,10,.4)'; g.shadowBlur = 4; g.shadowOffsetY = 4;
    for (const s of [-1, 1]) { g.save(); g.rotate(s * flap); cut(g, [[0, 0], [s * 58, -20], [s * 46, 12]], 30 + s, 1.5); fill(g, '#f7f1e3'); g.restore(); }
    cut(g, [[-26, -9], [30, -5], [44, 4], [26, 12], [-30, 9]], 33, 1.5); fill(g, '#fffaf0'); g.restore();
    paper(g, W, H, 2, 30 + jit(f, 3, 2));
  } },
  felt: { kind: '2d', fps: 12, draw(g, t, W, H) {
    // soft shapes with a halo of fibres along the edge and a row of stitches; everything bobs on twos
    const ts = onTwos(t);
    bg(g, W, H, '#d8cdb8');
    const fuzzy = (x, y, r, col, seed) => {
      blob(g, x, y, r, seed, 0.06); fill(g, col);
      g.strokeStyle = col; g.lineWidth = 1.1; g.globalAlpha = 0.75;
      for (let i = 0; i < 520; i++) { const a = hash(i, seed) * TAU, rr = r * (0.97 + hash(i, seed, 1) * 0.07), l = 3 + hash(i, seed, 2) * 7, tw = a + (hash(i, seed, 3) - 0.5) * 1.6; g.beginPath(); g.moveTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr); g.lineTo(x + Math.cos(a) * rr + Math.cos(tw) * l, y + Math.sin(a) * rr + Math.sin(tw) * l); g.stroke(); }
      g.globalAlpha = 1; g.setLineDash([9, 7]); g.strokeStyle = 'rgba(255,250,235,.85)'; g.lineWidth = 2.4; g.beginPath(); g.arc(x, y, r * 0.8, 0, TAU); g.stroke(); g.setLineDash([]);
      g.save(); g.globalCompositeOperation = 'multiply'; g.beginPath(); g.arc(x, y, r, 0, TAU); g.clip(); g.drawImage(grain(W, H, seed, 60, [40, 30, 30]), 0, 0); g.restore();
    };
    fuzzy(W * 0.3, H * 0.52 + Math.sin(ts * 2.4) * 10, 108, '#c85a54', 21);
    fuzzy(W * 0.56, H * 0.46 + Math.sin(ts * 2.4 + 1.3) * 12, 84, '#e2b23f', 22);
    fuzzy(W * 0.76, H * 0.56 + Math.sin(ts * 2.4 + 2.6) * 9, 66, '#5d8a72', 23);
  } },
  origami: { kind: '2d', fps: null, draw(g, t, W, H) {
    // a square folds corner to corner, holds, then folds again. Each fold is an eased move with a hold after it.
    bg(g, W, H, '#eef0ee');
    const cx = W / 2, cy = H / 2 + 20, s = 150;
    const f1 = easeInOut(prog(t, 0.3, 0.8)), f2 = easeInOut(prog(t, 1.5, 0.8));
    const face = (pts, col) => { g.beginPath(); pts.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.closePath(); fill(g, col); g.strokeStyle = 'rgba(40,50,60,.45)'; g.lineWidth = 1.2; g.stroke(); };
    g.save(); g.translate(cx, cy);
    g.fillStyle = 'rgba(30,40,50,.12)'; g.beginPath(); g.ellipse(0, s * 0.95, s * 1.05, 16, 0, 0, TAU); g.fill();
    // the fixed lower-left triangle, then the upper-right triangle swinging over the diagonal crease
    const a1 = f1 * Math.PI, k1 = Math.cos(a1);                         // 1 flat, -1 folded over
    face([[-s, -s], [s, s], [-s, s]], '#f7f7f4');
    const tip = [lerp(s, -s, (1 - k1) / 2), lerp(-s, s, (1 - k1) / 2)];
    face([[-s, -s], [s, s], tip], k1 > 0 ? `hsl(8 70% ${58 - (1 - k1) * 16}%)` : `hsl(0 0% ${90 - (1 + k1) * 6}%)`);
    if (f1 >= 1) {                                                       // second fold: the bottom-right corner comes up
      const k2 = Math.cos(f2 * Math.PI), tip2 = [lerp(s, 0, (1 - k2) / 2), lerp(s, 0, (1 - k2) / 2)];
      face([[0, 0], [0, s], [s, s], [0, 0]].slice(0, 3).map((p, i) => (i === 2 ? tip2 : p)), k2 > 0 ? '#e8e8e4' : '#d8553f');
    }
    g.setLineDash([6, 6]); g.strokeStyle = 'rgba(40,50,60,.5)'; g.beginPath(); g.moveTo(-s, -s); g.lineTo(s, s); g.stroke(); g.setLineDash([]);
    g.restore(); paper(g, W, H, 8, 12);
  } },
  'shadow-puppet': { kind: '2d', fps: 12, draw(g, t, W, H) {
    // a lamp-lit screen and jointless leather figures with punched patterns, moved whole on their rods (the Ravana Chhaya way)
    const f = frameOf(t, 12), ts = onTwos(t), flick = 1 + jit(f, 0, 0.05);
    bg(g, W, H, '#1a0d05');
    const lamp = g.createRadialGradient(W / 2, H * 0.55, 30, W / 2, H * 0.55, W * 0.62);
    lamp.addColorStop(0, `rgba(255,${196 * flick},110,1)`); lamp.addColorStop(0.55, `rgba(214,${120 * flick},48,1)`); lamp.addColorStop(1, 'rgba(60,24,8,1)');
    g.fillStyle = lamp; g.fillRect(24, 24, W - 48, H - 48);
    const puppet = (x, y, s, lean, far) => {
      g.save(); g.translate(x, y); g.rotate(lean); g.scale(s, s); g.filter = `blur(${far * 5}px)`; g.fillStyle = `rgba(18,8,2,${1 - far * 0.35})`;
      g.beginPath();   // one path, even-odd: the holes are part of the figure
      g.moveTo(-34, 150); g.lineTo(-44, 20); g.lineTo(-70, -30); g.lineTo(-40, -44); g.lineTo(-26, -96); g.lineTo(-44, -150); g.lineTo(0, -196); g.lineTo(44, -150); g.lineTo(26, -96); g.lineTo(40, -44); g.lineTo(84, -70); g.lineTo(92, -44); g.lineTo(44, 20); g.lineTo(34, 150); g.closePath();
      for (let i = 0; i < 5; i++) { g.moveTo(8, -20 + i * 30); g.arc(0, -20 + i * 30, 8, 0, TAU); }
      for (let i = 0; i < 7; i++) { const a = (i / 7) * TAU; g.moveTo(Math.cos(a) * 22 + 4, -140 + Math.sin(a) * 22); g.arc(Math.cos(a) * 22, -140 + Math.sin(a) * 22, 4, 0, TAU); }
      g.fill('evenodd'); g.filter = 'none'; g.fillRect(-3, 150, 6, 260); g.restore();
    };
    puppet(W * 0.34 + Math.sin(ts * 1.6) * 26, H * 0.62, 0.95, Math.sin(ts * 1.6) * 0.06, 0);
    puppet(W * 0.68 - Math.sin(ts * 1.3) * 34, H * 0.66, 0.8, -Math.sin(ts * 1.3) * 0.08, (Math.sin(ts * 0.9) + 1) / 2);
    g.globalCompositeOperation = 'multiply'; g.drawImage(grain(W, H, 6, 40, [80, 40, 10]), 0, 0); g.globalCompositeOperation = 'source-over';
  } },
  collage: { kind: '2d', fps: 8, draw(g, t, W, H) {
    // torn paper, a halftone "photo", tape. Pieces pop in on threes with a hard shadow, slightly rotated.
    const f = frameOf(t, 8), ts = held(t, 8);
    bg(g, W, H, '#e9e2d0');
    const torn = (x, y, w, h, col, seed, start, rot) => {
      const k = prog(ts, start, 0.25); if (k <= 0) return;
      g.save(); g.translate(x, y); g.rotate(rot + (1 - k) * 0.25); g.scale(lerp(1.25, 1, k), lerp(1.25, 1, k));
      g.shadowColor = 'rgba(20,10,0,.45)'; g.shadowOffsetX = 5; g.shadowOffsetY = 6; g.shadowBlur = 0;
      g.beginPath(); const n = 26; for (let i = 0; i < n; i++) { const e = i / n, px = e < 0.25 ? lerp(-w, w, e * 4) : e < 0.5 ? w : e < 0.75 ? lerp(w, -w, (e - 0.5) * 4) : -w, py = e < 0.25 ? -h : e < 0.5 ? lerp(-h, h, (e - 0.25) * 4) : e < 0.75 ? h : lerp(h, -h, (e - 0.75) * 4); const jx = jit(seed, i, 7), jy = jit(seed, i + 50, 7); i ? g.lineTo(px + jx, py + jy) : g.moveTo(px + jx, py + jy); } g.closePath(); fill(g, col);
      g.restore();
    };
    torn(W * 0.3, H * 0.42, 190, 130, '#2e4a7d', 41, 0.2, -0.08);
    torn(W * 0.62, H * 0.56, 210, 110, '#d94f30', 42, 0.6, 0.06);
    torn(W * 0.5, H * 0.3, 120, 70, '#f1c84b', 43, 1.0, -0.14);
    const k = prog(ts, 1.4, 0.25);
    if (k > 0) {                                                          // the halftone disc: dots sized by a gradient
      g.save(); g.translate(W * 0.47, H * 0.52); g.scale(lerp(1.3, 1, k), lerp(1.3, 1, k)); g.fillStyle = '#111';
      for (let y = -110; y <= 110; y += 11) for (let x = -110; x <= 110; x += 11) { const d = Math.hypot(x, y); if (d > 110) continue; g.beginPath(); g.arc(x + ((y / 11) % 2) * 5.5, y, 1 + 4.2 * (1 - (x + 110) / 220), 0, TAU); g.fill(); }
      g.restore();
    }
    const tk = prog(ts, 1.9, 0.2); if (tk > 0) { g.save(); g.translate(W * 0.47, H * 0.3); g.rotate(-0.2); g.fillStyle = 'rgba(240,225,170,.8)'; g.fillRect(-60 * tk, -14, 120 * tk, 28); g.restore(); }
    paper(g, W, H, 9, 32 + jit(f, 1, 3));
  } },
  risograph: { kind: '2d', fps: 8, draw(g, t, W, H) {
    // three ink layers printed with multiply. Each layer slips a pixel or two per frame (misregistration), with grain on top.
    const f = frameOf(t, 8);
    bg(g, W, H, '#f4efe2'); g.globalCompositeOperation = 'multiply';
    const off = (i) => [jit(f, i, 3), jit(f, i + 10, 3)];
    let [x, y] = off(1); g.fillStyle = '#ff48a0'; g.beginPath(); g.arc(W * 0.42 + x, H * 0.48 + y, 150, 0, TAU); g.fill();
    [x, y] = off(2); g.fillStyle = '#2a5cff'; g.beginPath(); g.moveTo(W * 0.5 + x, H * 0.2 + y); g.lineTo(W * 0.78 + x, H * 0.76 + y); g.lineTo(W * 0.3 + x, H * 0.76 + y); g.closePath(); g.fill();
    [x, y] = off(3); g.fillStyle = '#ffd400';                              // the yellow layer is a halftone: dots that grow left to right
    for (let py = H * 0.2; py < H * 0.82; py += 12) for (let px = W * 0.5; px < W * 0.86; px += 12) { g.beginPath(); g.arc(px + x + ((py / 12) % 2 | 0) * 6, py + y, 0.8 + 5 * ((px - W * 0.5) / (W * 0.36)), 0, TAU); g.fill(); }
    g.drawImage(grain(W, H, 10 + (f % 4), 46, [30, 30, 40]), 0, 0); g.globalCompositeOperation = 'source-over';
    g.fillStyle = '#2a5cff'; g.font = `800 34px ${FONT}`; g.fillText('3 INKS', 40, H - 40);
  } },

  /* ------------------------------------------------ drawn and painted ------------------------------------------------ */
  'flat-explainer': { kind: '2d', fps: null, draw(g, t, W, H) {
    // the explainer look: flat fills, one accent, smooth ease-out moves, a stagger, and a hold at the end
    bg(g, W, H, '#f5f7fb');
    const labels = ['Brief', 'Build', 'Check'];
    for (let i = 0; i < 3; i++) {
      const k = easeOut(prog(t, 0.2 + i * 0.22, 0.6)), x = W * (0.22 + i * 0.28), y = lerp(H * 0.62, H * 0.46, k);
      g.globalAlpha = k; g.fillStyle = i === 2 ? '#ff5a1f' : '#1f2a44'; g.beginPath(); g.roundRect(x - 92, y - 62, 184, 124, 22); g.fill();
      g.fillStyle = '#fff'; g.font = `700 30px ${FONT}`; g.textAlign = 'center'; g.fillText(labels[i], x, y + 10);
      if (i < 2) { const a = easeOut(prog(t, 0.9 + i * 0.25, 0.4)); g.globalAlpha = a; g.strokeStyle = '#1f2a44'; g.lineWidth = 5; g.lineCap = 'round'; g.beginPath(); g.moveTo(x + 104, H * 0.46); g.lineTo(x + 104 + 60 * a, H * 0.46); g.stroke(); }
    }
    g.globalAlpha = 1; g.textAlign = 'left';
    const c = prog(t, 1.7, 0.45); g.strokeStyle = '#fff'; g.lineWidth = 9; g.lineCap = 'round'; g.lineJoin = 'round';
    strokePart(g, [[W * 0.78 - 22, H * 0.46 - 44], [W * 0.78 - 8, H * 0.46 - 30], [W * 0.78 + 22, H * 0.46 - 60]], easeOut(c));
  } },
  whiteboard: { kind: '2d', fps: 10, draw(g, t, W, H) {
    // marker strokes that draw on in order, with a slight boil: the points are re-nudged ten times a second
    const f = frameOf(t, 10);
    bg(g, W, H, '#fbfbf8'); g.lineCap = 'round'; g.lineJoin = 'round'; g.strokeStyle = '#17202b'; g.lineWidth = 5;
    const bulb = circlePts(W * 0.3, H * 0.42, 78, 36, Math.PI * 0.72, Math.PI * 2.28);
    strokePart(g, bulb, prog(t, 0.1, 0.8), f, 1.6);
    strokePart(g, [[W * 0.3 - 34, H * 0.42 + 72], [W * 0.3 - 34, H * 0.42 + 112], [W * 0.3 + 34, H * 0.42 + 112], [W * 0.3 + 34, H * 0.42 + 72]], prog(t, 0.9, 0.35), f, 1.6);
    g.strokeStyle = '#e0532f'; for (let i = 0; i < 5; i++) { const a = -Math.PI * (0.15 + i * 0.175); strokePart(g, [[W * 0.3 + Math.cos(a) * 100, H * 0.42 + Math.sin(a) * 100], [W * 0.3 + Math.cos(a) * 132, H * 0.42 + Math.sin(a) * 132]], prog(t, 1.25 + i * 0.07, 0.15), f, 1.2); }
    g.strokeStyle = '#17202b'; strokePart(g, [[W * 0.45, H * 0.44], [W * 0.6, H * 0.44], [W * 0.57, H * 0.4], [W * 0.6, H * 0.44], [W * 0.57, H * 0.48]], prog(t, 1.6, 0.4), f, 1.6);
    strokePart(g, [[W * 0.65, H * 0.3], [W * 0.88, H * 0.3], [W * 0.88, H * 0.58], [W * 0.65, H * 0.58], [W * 0.65, H * 0.3]], prog(t, 2.0, 0.5), f, 1.6);
    const k = prog(t, 2.5, 0.3); if (k > 0) { g.globalAlpha = k; g.fillStyle = '#17202b'; g.font = `italic 600 34px "Marker Felt", "Comic Sans MS", ${FONT}`; g.fillText('idea → plan', W * 0.665, H * 0.46); g.globalAlpha = 1; }
  } },
  chalkboard: { kind: '2d', fps: 10, draw(g, t, W, H) {
    // the whiteboard recipe on a dark board: dusty, broken strokes (three thin passes) and a smudge of chalk dust
    const f = frameOf(t, 10);
    bg(g, W, H, '#24382f'); g.drawImage(grain(W, H, 12, 34, [230, 240, 235]), 0, 0);
    g.lineCap = 'round'; g.lineJoin = 'round';
    const chalk = (pts, k, col = '#f2f0e6') => { for (let p = 0; p < 3; p++) { g.strokeStyle = col; g.globalAlpha = 0.5; g.lineWidth = 3; g.setLineDash([14 + p * 5, 3 + p]); g.lineDashOffset = p * 7; strokePart(g, pts.map(([x, y]) => [x + p - 1, y + (p - 1) * 1.4]), k, f + p * 31, 1.3); } g.setLineDash([]); g.globalAlpha = 1; };
    chalk([[W * 0.16, H * 0.72], [W * 0.84, H * 0.72]], prog(t, 0.1, 0.5));
    chalk([[W * 0.16, H * 0.72], [W * 0.16, H * 0.2]], prog(t, 0.4, 0.5));
    chalk(Array.from({ length: 40 }, (_, i) => [W * (0.16 + 0.66 * i / 39), H * (0.72 - 0.46 * (i / 39) ** 2)]), prog(t, 0.9, 1.0), '#ffd966');
    const k = prog(t, 2.0, 0.4); if (k > 0) { g.globalAlpha = k * 0.9; g.fillStyle = '#f2f0e6'; g.font = `600 36px "Chalkduster", "Marker Felt", ${FONT}`; g.fillText('y = x²', W * 0.56, H * 0.34); g.globalAlpha = 1; }
  } },
  watercolour: { kind: '2d', fps: 12, draw(g, t, W, H) {
    // transparent washes that spread, with pigment pooling at the edge and paper showing through
    const ts = onTwos(t);
    bg(g, W, H, '#f6f1e6'); g.globalCompositeOperation = 'multiply';
    const wash = (x, y, r, rgb, seed, start) => {
      const k = easeOut(prog(ts, start, 1.6)); if (k <= 0) return; const rr = r * (0.35 + 0.65 * k);
      g.save(); blob(g, x, y, rr, seed, 0.16); g.clip();
      const grad = g.createRadialGradient(x, y, rr * 0.1, x, y, rr * 1.12);
      grad.addColorStop(0, `rgba(${rgb},${0.28 * k})`); grad.addColorStop(0.72, `rgba(${rgb},${0.42 * k})`); grad.addColorStop(0.93, `rgba(${rgb},${0.8 * k})`); grad.addColorStop(1, `rgba(${rgb},${0.3 * k})`);
      g.fillStyle = grad; g.fillRect(x - rr * 1.3, y - rr * 1.3, rr * 2.6, rr * 2.6); g.restore();
    };
    wash(W * 0.36, H * 0.5, 170, '52,110,170', 51, 0.1);
    wash(W * 0.58, H * 0.44, 150, '214,84,96', 52, 0.6);
    wash(W * 0.5, H * 0.66, 120, '232,178,60', 53, 1.1);
    g.drawImage(grain(W, H, 14, 44, [70, 55, 40]), 0, 0); g.globalCompositeOperation = 'source-over';
  } },
  'ink-wash': { kind: '2d', fps: 12, draw(g, t, W, H) {
    // bamboo in ink: tapered strokes laid down segment by segment, grey washes, a red seal, a lot of empty paper
    const ts = onTwos(t);
    bg(g, W, H, '#f2ecdd');
    const stroke = (x0, y0, x1, y1, w0, w1, k, alpha = 0.92) => { const n = 60; for (let i = 0; i <= n * clamp(k); i++) { const e = i / n, r = lerp(w0, w1, e) * (0.85 + 0.3 * hash(i, x0 | 0)); g.fillStyle = `rgba(22,22,24,${alpha * (0.55 + 0.45 * hash(i, y0 | 0))})`; g.beginPath(); g.arc(lerp(x0, x1, e), lerp(y0, y1, e) + Math.sin(e * 3) * 3, r, 0, TAU); g.fill(); } };
    for (let s = 0; s < 4; s++) stroke(W * 0.3 + s * 3, H * 0.96 - s * 118, W * 0.3 + (s + 1) * 3, H * 0.96 - (s + 1) * 118 + 8, 13 - s, 12 - s, prog(ts, 0.1 + s * 0.3, 0.3));
    const leaf = (x, y, a, l, start) => stroke(x, y, x + Math.cos(a) * l, y + Math.sin(a) * l, 9, 0.6, easeOut(prog(ts, start, 0.3)), 0.85);
    leaf(W * 0.31, H * 0.5, -0.3, 150, 1.4); leaf(W * 0.31, H * 0.5, 0.25, 130, 1.6); leaf(W * 0.31, H * 0.3, -0.7, 120, 1.8); leaf(W * 0.31, H * 0.3, -0.05, 160, 2.0);
    g.globalCompositeOperation = 'multiply'; const m = g.createRadialGradient(W * 0.7, H * 0.72, 10, W * 0.7, H * 0.72, 220); m.addColorStop(0, `rgba(60,62,66,${0.35 * prog(ts, 0.4, 1.5)})`); m.addColorStop(1, 'rgba(60,62,66,0)'); g.fillStyle = m; g.fillRect(0, 0, W, H); g.globalCompositeOperation = 'source-over';
    const k = prog(ts, 2.3, 0.2); if (k > 0) { g.fillStyle = '#b3261e'; g.fillRect(W * 0.82, H * 0.74, 38 * k, 38); }
    paper(g, W, H, 15, 22);
  } },
  'line-art': { kind: '2d', fps: 10, draw(g, t, W, H) {
    // one continuous line that draws a cup and its steam, then keeps quivering
    const f = frameOf(t, 10);
    bg(g, W, H, '#fffdf8'); g.strokeStyle = '#151515'; g.lineWidth = 3.2; g.lineCap = 'round'; g.lineJoin = 'round';
    const cup = [[W * 0.62, H * 0.5], [W * 0.36, H * 0.5], [W * 0.38, H * 0.7], [W * 0.42, H * 0.76], [W * 0.56, H * 0.76], [W * 0.6, H * 0.7], [W * 0.62, H * 0.5], ...circlePts(W * 0.625, H * 0.6, 44, 16, -Math.PI * 0.5, Math.PI * 0.5)];
    strokePart(g, cup, easeInOut(prog(t, 0.1, 1.5)), f, 1.3);
    for (let i = 0; i < 3; i++) strokePart(g, Array.from({ length: 24 }, (_, j) => [W * (0.43 + i * 0.06) + Math.sin(j * 0.6 + i) * 9, H * 0.45 - j * 6]), easeOut(prog(t, 1.5 + i * 0.2, 0.7)), f, 1.3);
    g.fillStyle = '#e0532f'; const k = easeOut(prog(t, 2.3, 0.3)); g.beginPath(); g.arc(W * 0.3, H * 0.8, 9 * k, 0, TAU); g.fill();
  } },
  rotoscope: { kind: '2d', fps: 12, draw(g, t, W, H) {
    // a walking figure traced on twos: flat colour fields that drift a little and an outline that never sits still
    const f = frameOf(t, 12), ts = onTwos(t), ph = ts * 5.5, x = W * 0.5, y = H * 0.58;
    bg(g, W, H, '#20263a'); g.fillStyle = '#2c3552'; g.fillRect(0, H * 0.8, W, H * 0.2);
    const limb = (x0, y0, a, l1, b, l2) => { const x1 = x0 + Math.sin(a) * l1, y1 = y0 + Math.cos(a) * l1; return [[x0, y0], [x1, y1], [x1 + Math.sin(a + b) * l2, y1 + Math.cos(a + b) * l2]]; };
    const parts = [limb(x, y, Math.sin(ph) * 0.6, 62, Math.max(0, -Math.sin(ph)) * 0.9, 62), limb(x, y, -Math.sin(ph) * 0.6, 62, Math.max(0, Math.sin(ph)) * 0.9, 62),
      limb(x, y - 112, -Math.sin(ph) * 0.7, 52, -0.5, 48), limb(x, y - 112, Math.sin(ph) * 0.7, 52, -0.5, 48)];
    const body = () => { g.beginPath(); g.moveTo(x - 26, y - 118); g.lineTo(x + 26, y - 118); g.lineTo(x + 18, y + 6); g.lineTo(x - 18, y + 6); g.closePath(); };
    for (let pass = 0; pass < 2; pass++) {
      g.lineCap = 'round'; g.lineJoin = 'round';
      const dx = pass ? 0 : jit(f, 1, 4), dy = pass ? 0 : jit(f, 2, 4);     // the colour field drifts off the line
      g.save(); g.translate(dx, dy);
      g.strokeStyle = pass ? '#f4f0e8' : '#e8643c'; g.lineWidth = pass ? 2.2 : 22;
      for (const [i, p] of parts.entries()) { g.beginPath(); p.forEach(([px, py], j) => { const qx = px + (pass ? jit(f, i * 9 + j, 2.2) : 0), qy = py + (pass ? jit(f, i * 9 + j + 40, 2.2) : 0); j ? g.lineTo(qx, qy) : g.moveTo(qx, qy); }); g.stroke(); }
      body(); pass ? g.stroke() : fill(g, '#f0b23c');
      g.beginPath(); g.arc(x + jit(f, 77, pass ? 1.5 : 0), y - 146 + Math.abs(Math.sin(ph)) * 5, 24, 0, TAU); pass ? g.stroke() : fill(g, '#f4d7b5');
      g.restore();
    }
  } },
  'motion-comic': { kind: '2d', fps: null, draw(g, t, W, H) {
    // two panels and a hard cut. Inside each: layers that move at different speeds under a slow push-in, with halftone shading.
    bg(g, W, H, '#f0ead8');
    const second = t >= 1.6, k = second ? prog(t, 1.6, 1.4) : prog(t, 0, 1.6), z = 1 + 0.07 * k;
    g.save(); g.beginPath(); g.rect(40, 40, W - 80, H - 80); g.clip();
    g.translate(W / 2, H / 2); g.scale(z, z); g.translate(-W / 2, -H / 2);
    g.fillStyle = second ? '#ffcf4a' : '#27335c'; g.fillRect(0, 0, W, H);
    g.fillStyle = second ? '#e9772b' : '#141b36';                           // far layer: slow
    for (let i = 0; i < 9; i++) { const h = 120 + hash(i, second ? 5 : 3) * 190; g.fillRect(i * 120 - 40 - k * 18, H - 120 - h, 96, h + 200); }
    g.fillStyle = 'rgba(0,0,0,.28)';                                        // halftone shade, dots shrink to the right
    for (let y = 60; y < H; y += 14) for (let x = 60; x < W * 0.5; x += 14) { g.beginPath(); g.arc(x + ((y / 14) % 2 | 0) * 7, y, 4.5 * (1 - x / (W * 0.5)), 0, TAU); g.fill(); }
    g.save(); g.translate(W * (second ? 0.62 : 0.4) + k * 46, H * 0.66);   // near layer: fast
    g.fillStyle = '#101010'; g.beginPath(); g.moveTo(-70, 220); g.lineTo(-52, -40); g.lineTo(-20, -70); g.arc(0, -108, 44, Math.PI * 0.7, Math.PI * 2.3); g.lineTo(52, -40); g.lineTo(70, 220); g.closePath(); g.fill(); g.restore();
    if (second) { const b = overshoot(prog(t, 1.75, 0.35)); g.save(); g.translate(W * 0.3, H * 0.34); g.scale(b, b); g.fillStyle = '#fff'; g.strokeStyle = '#101010'; g.lineWidth = 5; g.beginPath(); for (let i = 0; i < 20; i++) { const a = (i / 20) * TAU, r = i % 2 ? 62 : 104; i ? g.lineTo(Math.cos(a) * r, Math.sin(a) * r) : g.moveTo(Math.cos(a) * r, Math.sin(a) * r); } g.closePath(); g.fill(); g.stroke(); g.fillStyle = '#101010'; g.font = `900 46px ${FONT}`; g.textAlign = 'center'; g.fillText('NOW!', 0, 16); g.textAlign = 'left'; g.restore(); }
    g.restore(); g.strokeStyle = '#101010'; g.lineWidth = 8; g.strokeRect(40, 40, W - 80, H - 80);
  } },
  'upa-midcentury': { kind: '2d', fps: 8, draw(g, t, W, H) {
    // limited animation: flat geometric shapes, colour printed slightly off its outline, held poses that pop on threes
    const pose = frameOf(t, 8) % 12 < 6 ? 0 : 1, f = frameOf(t, 8);
    bg(g, W, H, '#e8dcc0');
    g.fillStyle = '#d98c3a'; g.fillRect(W * 0.08, H * 0.16, W * 0.3, H * 0.62); g.fillStyle = '#5a6fa5'; g.beginPath(); g.arc(W * 0.78, H * 0.28, 70, 0, TAU); g.fill();
    g.strokeStyle = '#1c1c1c'; g.lineWidth = 3; g.strokeRect(W * 0.08 + 9, H * 0.16 - 8, W * 0.3, H * 0.62); g.beginPath(); g.arc(W * 0.78 - 8, H * 0.28 + 6, 70, 0, TAU); g.stroke();
    const x = W * 0.55, y = H * 0.74, lean = pose ? 0.14 : -0.1;
    g.save(); g.translate(x, y); g.rotate(lean);
    g.fillStyle = '#c8452f'; g.beginPath(); g.moveTo(-70, 0); g.lineTo(70, 0); g.lineTo(0, -210); g.closePath(); g.fill();
    g.strokeStyle = '#1c1c1c'; g.beginPath(); g.moveTo(-64, -8); g.lineTo(76, -8); g.lineTo(6, -218); g.closePath(); g.stroke();
    g.fillStyle = '#f3e9d2'; g.beginPath(); g.arc(0, -236, 34, 0, TAU); g.fill(); g.stroke();
    g.lineWidth = 5; g.lineCap = 'round'; g.beginPath(); g.moveTo(-30, -130); g.lineTo(-96, pose ? -206 : -100); g.moveTo(30, -130); g.lineTo(100, pose ? -110 : -196); g.stroke();
    g.fillStyle = '#1c1c1c'; g.beginPath(); g.arc(pose ? 10 : -8, -240, 4, 0, TAU); g.fill(); g.restore();
    paper(g, W, H, 17, 26 + jit(f, 1, 2));
  } },
  'rubber-hose': { kind: '2d', fps: 12, draw(g, t, W, H) {
    // limbs are curves with no elbows or knees; the body squashes and stretches on the beat; film grain and a weaving gate
    const f = frameOf(t, 12), ts = onTwos(t), beat = Math.abs(Math.sin(ts * Math.PI * 2)), sq = 1 + 0.16 * (beat - 0.5);
    bg(g, W, H, '#d9d2c0');
    g.save(); g.translate(jit(f, 1, 1.5), jit(f, 2, 1.5));                  // gate weave
    const x = W / 2, y = H * 0.56 - beat * 26;
    g.fillStyle = 'rgba(0,0,0,.25)'; g.beginPath(); g.ellipse(x, H * 0.84, 90 - beat * 20, 12, 0, 0, TAU); g.fill();
    g.strokeStyle = '#111'; g.lineWidth = 15; g.lineCap = 'round';
    const hose = (x0, y0, x1, y1, bend) => { g.beginPath(); g.moveTo(x0, y0); g.quadraticCurveTo((x0 + x1) / 2 + bend, (y0 + y1) / 2 + Math.abs(bend) * 0.4, x1, y1); g.stroke(); };
    hose(x - 30, y + 60, x - 62, H * 0.83, -40 * beat); hose(x + 30, y + 60, x + 62, H * 0.83, 40 * beat);
    hose(x - 62, y - 10, x - 150, y - 60 - beat * 50, -50 + beat * 70); hose(x + 62, y - 10, x + 150, y - 60 - (1 - beat) * 50, 50 - beat * 70);
    g.fillStyle = '#111'; g.beginPath(); g.ellipse(x, y, 78 / sq, 84 * sq, 0, 0, TAU); g.fill();
    g.fillStyle = '#f4efe2'; g.beginPath(); g.ellipse(x, y - 8, 54 / sq, 56 * sq, 0, 0, TAU); g.fill();
    for (const s of [-1, 1]) { g.fillStyle = '#111'; g.beginPath(); g.ellipse(x + s * 20, y - 22, 9, 15 * sq, 0, 0, TAU); g.fill(); g.fillStyle = '#f4efe2'; g.beginPath(); g.moveTo(x + s * 20, y - 22); g.arc(x + s * 20, y - 22, 9, -0.9, -0.3); g.fill(); }
    g.strokeStyle = '#111'; g.lineWidth = 5; g.beginPath(); g.arc(x, y + 6, 26, 0.15 * Math.PI, 0.85 * Math.PI); g.stroke();
    for (const s of [-1, 1]) { g.fillStyle = '#f4efe2'; g.strokeStyle = '#111'; g.lineWidth = 5; g.beginPath(); g.arc(x + s * 150, y - 60 - (s < 0 ? beat : 1 - beat) * 50, 22, 0, TAU); g.fill(); g.stroke(); g.fillStyle = '#111'; g.beginPath(); g.ellipse(x + s * 62, H * 0.84, 34, 15, 0, 0, TAU); g.fill(); }
    g.restore(); g.drawImage(grain(W, H, 20 + (f % 5), 50, [20, 20, 20]), 0, 0);
    g.fillStyle = `rgba(0,0,0,${0.5 * hash(f, 9)})`; g.fillRect(hash(f, 3) * W, 0, 1.5, H);   // a scratch
  } },
  linocut: { kind: '2d', fps: 8, draw(g, t, W, H) {
    // two blocks, two inks. Bold shapes with white gouge marks cut out of them; the second colour lands a little off.
    const ts = held(t, 8);
    bg(g, W, H, '#efe7d3');
    const block = (col, k, dx, dy, shape, seed) => {
      if (k <= 0) return; const c = new OffscreenCanvas(W, H), b = c.getContext('2d');
      b.fillStyle = col; shape(b); b.globalCompositeOperation = 'destination-out'; b.strokeStyle = '#000'; b.lineCap = 'round';
      for (let i = 0; i < 230; i++) { const x = hash(i, seed) * W, y = hash(i, seed, 1) * H, a = -0.6 + hash(i, seed, 2) * 0.5, l = 14 + hash(i, seed, 3) * 38; b.lineWidth = 1.5 + hash(i, seed, 4) * 4; b.beginPath(); b.moveTo(x, y); b.lineTo(x + Math.cos(a) * l, y + Math.sin(a) * l); b.stroke(); }
      g.save(); g.globalCompositeOperation = 'multiply'; g.globalAlpha = 0.94; g.beginPath(); g.rect(0, 0, W, H * k); g.clip(); g.drawImage(c, dx, dy); g.restore();   // the print is "pulled" from the top
    };
    block('#1f3b57', prog(ts, 0.2, 0.9), 0, 0, (b) => { b.beginPath(); b.moveTo(0, H * 0.78); b.lineTo(W * 0.24, H * 0.4); b.lineTo(W * 0.42, H * 0.62); b.lineTo(W * 0.62, H * 0.26); b.lineTo(W, H * 0.7); b.lineTo(W, H); b.lineTo(0, H); b.closePath(); b.fill(); }, 61);
    block('#d6452b', prog(ts, 1.3, 0.9), 7, -5, (b) => { b.beginPath(); b.arc(W * 0.74, H * 0.26, 76, 0, TAU); b.fill(); b.fillRect(W * 0.1, H * 0.84, W * 0.8, 26); }, 62);
    paper(g, W, H, 19, 24);
  } },

  /* ------------------------------------------------ 2D geometry and pixels ------------------------------------------------ */
  isometric: { kind: '2d', fps: null, draw(g, t, W, H) {
    // a parallel projection: no perspective, three tones per cube, one light. Cubes drop in, staggered by grid position.
    bg(g, W, H, '#eaf0f6');
    const s = 44, ox = W / 2, oy = H * 0.34, iso = (x, y, z) => [ox + (x - y) * s, oy + (x + y) * s * 0.5 - z * s];
    const quad = (pts, col) => { g.beginPath(); pts.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.closePath(); fill(g, col); };
    for (let y = 0; y < 5; y++) for (let x = 0; x < 5; x++) quad([iso(x, y, 0), iso(x + 1, y, 0), iso(x + 1, y + 1, 0), iso(x, y + 1, 0)], (x + y) % 2 ? '#d5dfea' : '#dfe7f0');
    const towers = [[0, 0, 2], [1, 3, 1], [2, 1, 3], [3, 3, 2], [4, 0, 1], [3, 1, 1], [1, 1, 1], [4, 4, 3]];
    towers.sort((a, b) => a[0] + a[1] - (b[0] + b[1]));
    for (const [x, y, h] of towers) for (let z = 0; z < h; z++) {
      const k = prog(t, 0.2 + (x + y) * 0.12 + z * 0.14, 0.5); if (k <= 0) continue; const zz = z + (1 - bounce(k)) * 7, hue = 216 + (x * 7 + y * 13) % 40;
      quad([iso(x, y + 1, zz + 1), iso(x + 1, y + 1, zz + 1), iso(x + 1, y + 1, zz), iso(x, y + 1, zz)], `hsl(${hue} 52% 42%)`);
      quad([iso(x + 1, y, zz + 1), iso(x + 1, y + 1, zz + 1), iso(x + 1, y + 1, zz), iso(x + 1, y, zz)], `hsl(${hue} 52% 54%)`);
      quad([iso(x, y, zz + 1), iso(x + 1, y, zz + 1), iso(x + 1, y + 1, zz + 1), iso(x, y + 1, zz + 1)], `hsl(${hue} 60% 70%)`);
    }
  } },
  'pixel-art': { kind: '2d', fps: 8, draw(g, t, W, H) {
    // drawn on a 160 x 90 canvas with a six-colour palette, then scaled up six times with no smoothing. The walk cycle has four frames.
    const lw = 160, lh = 90, c = new OffscreenCanvas(lw, lh), p = c.getContext('2d'), f = frameOf(t, 8), PAL = ['#1b1f3b', '#3b4a8c', '#f4d35e', '#ee6c4d', '#f7f3e8', '#2e7d5b'];
    p.fillStyle = PAL[1]; p.fillRect(0, 0, lw, lh); p.fillStyle = PAL[0]; p.fillRect(0, 62, lw, 28);
    for (let i = 0; i < 26; i++) { p.fillStyle = PAL[4]; if (hash(i, 3) > 0.5 || f % 4 !== i % 4) p.fillRect((hash(i) * lw) | 0, (hash(i, 1) * 44) | 0, 1, 1); }
    p.fillStyle = PAL[2]; p.fillRect(124, 10, 12, 12);
    for (let x = 0; x < lw; x += 8) { p.fillStyle = PAL[5]; p.fillRect(((x - f * 2) % lw + lw) % lw, 62, 4, 2); }   // the ground scrolls two pixels a frame
    const SPR = ['..3333..', '.333333.', '.34343..', '.344443.', '..2222..', '.222222.', '.2.22.2.', '..1..1..'], legs = [['..1..1..', '.11..11.'], ['..11.1..', '..1..11.'], ['..1..1..', '.11..11.'], ['..1.11..', '.11..1..']][f % 4];
    const rows = [...SPR.slice(0, 7), ...legs], bx = 72, by = 62 - rows.length * 2 - (f % 2);
    rows.forEach((row, y) => [...row].forEach((ch, x) => { if (ch !== '.') { p.fillStyle = PAL[+ch]; p.fillRect(bx + x * 2, by + y * 2, 2, 2); } }));
    g.imageSmoothingEnabled = false; g.globalCompositeOperation = 'source-over'; g.drawImage(c, 0, 0, W, H); g.imageSmoothingEnabled = true;
  } },
  blueprint: { kind: '2d', fps: null, draw(g, t, W, H) {
    // white lines on blue, a grid, then the drawing itself, then its dimensions. Steady, with no bounce.
    bg(g, W, H, '#1d4f91');
    g.strokeStyle = 'rgba(255,255,255,.12)'; g.lineWidth = 1; g.beginPath(); for (let x = 0; x <= W; x += 30) { g.moveTo(x, 0); g.lineTo(x, H); } for (let y = 0; y <= H; y += 30) { g.moveTo(0, y); g.lineTo(W, y); } g.stroke();
    g.strokeStyle = '#eaf2ff'; g.lineWidth = 2.5; g.lineCap = 'round'; g.lineJoin = 'round';
    const cx = W * 0.42, cy = H * 0.52, gear = Array.from({ length: 97 }, (_, i) => { const a = (i / 96) * TAU, r = 120 + (Math.floor(i / 4) % 2 ? 22 : 0); return [cx + Math.cos(a) * r, cy + Math.sin(a) * r]; });
    strokePart(g, gear, prog(t, 0.1, 1.2)); strokePart(g, circlePts(cx, cy, 44, 40), prog(t, 1.1, 0.4));
    g.setLineDash([10, 6]); g.lineWidth = 1.4; strokePart(g, [[cx - 170, cy], [cx + 170, cy]], prog(t, 1.4, 0.3)); strokePart(g, [[cx, cy - 170], [cx, cy + 170]], prog(t, 1.5, 0.3)); g.setLineDash([]);
    const k = prog(t, 1.9, 0.4); if (k > 0) {
      g.globalAlpha = k; g.lineWidth = 1.6; const y = cy + 176; g.beginPath(); g.moveTo(cx - 142, y); g.lineTo(cx + 142, y); g.moveTo(cx - 142, y - 8); g.lineTo(cx - 142, y + 8); g.moveTo(cx + 142, y - 8); g.lineTo(cx + 142, y + 8); g.stroke();
      g.fillStyle = '#eaf2ff'; g.font = `500 20px ui-monospace, Menlo, monospace`; g.textAlign = 'center'; g.fillText('Ø 284', cx, y + 28); g.textAlign = 'left';
      g.strokeRect(W * 0.68, H * 0.66, W * 0.26, H * 0.22); g.fillText('GEAR  12 T', W * 0.68 + 14, H * 0.66 + 32); g.fillText('SCALE 1:1', W * 0.68 + 14, H * 0.66 + 62); g.fillText('DRG  B2M-01', W * 0.68 + 14, H * 0.66 + 92); g.globalAlpha = 1;
    }
  } },
  'neon-sign': { kind: '2d', fps: 24, draw(g, t, W, H) {
    // one continuous tube per letter, a bright core with a coloured halo, lit letter by letter, with a seeded flicker
    const f = frameOf(t, 24);
    bg(g, W, H, '#120a16'); g.fillStyle = 'rgba(255,255,255,.035)'; for (let y = 0; y < H; y += 34) for (let x = (y / 34) % 2 ? 0 : 45; x < W; x += 90) g.fillRect(x, y, 86, 30);
    const L = { O: circlePts(0, 0, 54, 30), P: [[-40, 60], [-40, -56], [10, -56], ...circlePts(10, -22, 34, 12, -Math.PI / 2, Math.PI / 2), [-40, 12]], E: [[40, -56], [-40, -56], [-40, 0], [20, 0], [-40, 0], [-40, 60], [40, 60]], N: [[-40, 60], [-40, -56], [40, 60], [40, -56]] };
    g.lineCap = 'round'; g.lineJoin = 'round'; g.globalCompositeOperation = 'lighter';
    [...'OPEN'].forEach((ch, i) => {
      const on = t > 0.3 + i * 0.35, stutter = on && t < 0.3 + i * 0.35 + 0.25 && hash(f, i) < 0.45, dim = i === 2 && hash(f, 44) < 0.06;   // a start-up stutter, and one tired tube
      const a = !on || stutter ? 0.08 : dim ? 0.35 : 1, pts = L[ch].map(([x, y]) => [W * (0.2 + i * 0.2) + x, H * 0.5 + y]), col = i % 2 ? '80,220,255' : '255,60,170';
      for (const [w, alpha, blur] of [[26, 0.16, 26], [12, 0.4, 12], [5, 1, 0]]) { g.strokeStyle = blur ? `rgba(${col},${alpha * a})` : `rgba(255,255,255,${a})`; g.shadowColor = `rgba(${col},${a})`; g.shadowBlur = blur; g.lineWidth = w; strokePart(g, pts, 1); }
    });
    g.shadowBlur = 0; g.globalCompositeOperation = 'source-over';
  } },

  /* ------------------------------------------------ type, data and retro ------------------------------------------------ */
  'kinetic-type': { kind: '2d', fps: null, draw(g, t, W, H) {
    // the words are the picture: each one lands with an overshoot, in reading order, then the line holds still
    bg(g, W, H, '#101319'); g.textAlign = 'center'; g.textBaseline = 'middle';
    const words = [['MAKE', '#f4f1ea', 0.15, H * 0.3, 118], ['IT', '#ff5a1f', 0.6, H * 0.52, 150], ['MOVE.', '#f4f1ea', 1.05, H * 0.76, 118]];
    for (const [w, col, start, y, size] of words) {
      const k = prog(t, start, 0.5); if (k <= 0) continue; const s = overshoot(k);
      g.save(); g.translate(W / 2, y + (1 - easeOut(k)) * 40); g.scale(s, s); g.globalAlpha = clamp(k * 3); g.fillStyle = col; g.font = `900 ${size}px ${FONT}`; g.fillText(w, 0, 0); g.restore();
    }
    const u = easeOut(prog(t, 1.7, 0.5)); g.fillStyle = '#ff5a1f'; g.fillRect(W / 2 - 190 * u, H * 0.9, 380 * u, 8);
    g.textAlign = 'left'; g.textBaseline = 'alphabetic';
  } },
  infographic: { kind: '2d', fps: null, draw(g, t, W, H) {
    // axes first, then the bars from a zero baseline, then the exact values. The numbers here are sample data.
    bg(g, W, H, '#fbfaf6');
    const data = [['2021', 12], ['2022', 19], ['2023', 31], ['2024', 44], ['2025', 62]], x0 = 130, y0 = H - 100, cw = (W - 220) / data.length, max = 70;
    g.strokeStyle = '#1b1e22'; g.lineWidth = 3; g.lineCap = 'round'; strokePart(g, [[x0, 70], [x0, y0], [W - 70, y0]], easeOut(prog(t, 0.1, 0.6)));
    g.font = `600 22px ${FONT}`; g.textAlign = 'center';
    data.forEach(([label, v], i) => {
      const k = easeOut(prog(t, 0.6 + i * 0.16, 0.8)), h = (v / max) * (y0 - 90) * k, x = x0 + 26 + i * cw;
      g.fillStyle = i === data.length - 1 ? '#c4271d' : '#9aa3ad'; g.fillRect(x, y0 - h, cw - 52, h);
      g.fillStyle = '#555b63'; g.globalAlpha = clamp(prog(t, 0.4, 0.4)); g.fillText(label, x + (cw - 52) / 2, y0 + 34);
      g.globalAlpha = clamp(k * 2); g.fillStyle = '#1b1e22'; g.fillText(String(Math.round(v * k)), x + (cw - 52) / 2, y0 - h - 14); g.globalAlpha = 1;
    });
    g.textAlign = 'left'; g.fillStyle = '#1b1e22'; g.font = `800 30px ${FONT}`; g.globalAlpha = clamp(prog(t, 0.1, 0.4)); g.fillText('Sample data: units per year', x0, 50); g.globalAlpha = 1;
  } },
  'lyric-video': { kind: '2d', fps: null, draw(g, t, W, H) {
    // one line at a time, and the word being sung is lit. Timing comes from a beat grid (here 120 beats a minute).
    const beat = t / 0.5, pulse = 1 - (beat % 1);
    const grad = g.createLinearGradient(0, 0, W, H); grad.addColorStop(0, `hsl(${258 + pulse * 8} 60% ${16 + pulse * 5}%)`); grad.addColorStop(1, 'hsl(320 60% 22%)');
    g.globalCompositeOperation = 'source-over'; g.fillStyle = grad; g.fillRect(0, 0, W, H);
    const lines = [['say', 'it', 'once'], ['and', 'let', 'it', 'move']], li = Math.min(1, Math.floor(beat / 3)), line = lines[li], wi = Math.min(line.length - 1, Math.floor(beat - li * 3));
    g.font = `800 84px ${FONT}`; g.textBaseline = 'middle';
    const widths = line.map((w) => g.measureText(w + ' ').width), total = widths.reduce((a, b) => a + b, 0); let x = (W - total) / 2;
    const enter = easeOut(prog(beat - li * 3, 0, 0.5));
    line.forEach((w, i) => {
      const active = i === wi, done = i < wi, s = active ? 1 + 0.08 * pulse : 1;
      g.save(); g.translate(x + widths[i] / 2, H / 2 + (1 - enter) * 30); g.scale(s, s); g.globalAlpha = enter * (active ? 1 : done ? 0.85 : 0.35);
      g.fillStyle = active ? '#ffd166' : '#ffffff'; g.textAlign = 'center'; g.fillText(w, 0, 0); g.restore(); x += widths[i];
    });
    g.textAlign = 'left'; g.textBaseline = 'alphabetic';
    for (let i = 0; i < 6; i++) { g.fillStyle = i <= beat % 6 ? '#ffd166' : 'rgba(255,255,255,.25)'; g.fillRect(W / 2 - 96 + i * 34, H - 70, 22, 6); }
  } },
  'vhs-glitch': { kind: '2d', fps: 30, draw(g, t, W, H) {
    // a clean frame first, then the damage on top: colour that bleeds sideways, scan lines, a tracking band, a seeded burst
    const f = frameOf(t, 30), c = new OffscreenCanvas(W, H), s = c.getContext('2d');
    s.fillStyle = '#0b1020'; s.fillRect(0, 0, W, H);
    ['#c0c0c0', '#c0c000', '#00c0c0', '#00c000', '#c000c0', '#c00000', '#0000c0'].forEach((col, i) => { s.fillStyle = col; s.fillRect(i * W / 7, H * 0.52, W / 7 + 1, H * 0.3); });
    s.fillStyle = '#fff'; s.font = `800 96px ${FONT}`; s.fillText('PLAY ▶', 60, 170); s.font = `600 34px ui-monospace, Menlo, monospace`; s.fillText('SP   0:00:' + String(Math.floor(t)).padStart(2, '0'), 60, H - 44); s.fillText('NOV 18 1994', W - 300, H - 44);
    bg(g, W, H, '#000');
    const burst = hash(Math.floor(f / 6), 5) < 0.22;                         // roughly one burst in five, 0.2 s long, the same every render
    for (let y = 0; y < H; y += 6) { const shift = (burst && hash(f, y) < 0.3 ? jit(f, y, 46) : 0) + Math.sin(y * 0.05 + f * 0.4) * 1.5; g.drawImage(c, 0, y, W, 6, shift, y, W, 6); }
    g.globalCompositeOperation = 'screen'; g.globalAlpha = 0.5; g.filter = 'blur(2px)'; g.drawImage(c, 7, 0); g.filter = 'none'; g.globalAlpha = 1;   // chroma is softer than brightness and sits a few pixels off
    g.globalCompositeOperation = 'source-over'; g.fillStyle = 'rgba(0,0,0,.22)'; for (let y = 0; y < H; y += 3) g.fillRect(0, y, W, 1);
    const band = H - 46 + Math.sin(f * 0.3) * 6; for (let i = 0; i < 260; i++) { g.fillStyle = `rgba(255,255,255,${hash(f, i) * 0.8})`; g.fillRect(hash(f, i, 1) * W, band + hash(f, i, 2) * 34, 4 + hash(f, i, 3) * 60, 2); }
    g.globalAlpha = 0.5; g.drawImage(grain(W, H, 30 + (f % 6), 40, [255, 255, 255]), 0, 0); g.globalAlpha = 1;
  } },

  /* ------------------------------------------------ 3D (three.js) ------------------------------------------------ */
  claymation: { kind: '3d', fps: 12, setup(THREE, scene, camera) {
    // rough, lumpy, matte spheres under soft light. Poses change 12 times a second and wobble a little between holds.
    scene.background = new THREE.Color('#e9d9c4');
    const tex = new THREE.CanvasTexture(grain(256, 256, 31, 255, [128, 128, 128])); tex.wrapS = tex.wrapT = THREE.RepeatWrapping; tex.repeat.set(3, 3);
    const clay = (col) => new THREE.MeshStandardMaterial({ color: col, roughness: 0.92, metalness: 0, bumpMap: tex, bumpScale: 2.2 });
    const lump = (r, seed, mat) => { const geo = new THREE.SphereGeometry(r, 40, 28), p = geo.attributes.position; for (let i = 0; i < p.count; i++) { const k = 1 + (hash(i, seed) - 0.5) * 0.045; p.setXYZ(i, p.getX(i) * k, p.getY(i) * k, p.getZ(i) * k); } geo.computeVertexNormals(); return new THREE.Mesh(geo, mat); };
    const body = lump(1, 1, clay('#d2603f')), head = lump(0.62, 2, clay('#e9b88f')), eyes = [-1, 1].map((s) => { const e = lump(0.1, 3, clay('#1c1c1c')); e.position.set(s * 0.22, 0.12, 0.56); head.add(e); return e; });
    const floor = new THREE.Mesh(new THREE.CircleGeometry(6, 48), clay('#b99b78')); floor.rotation.x = -Math.PI / 2; floor.position.y = -1;
    scene.add(body, head, floor, new THREE.HemisphereLight('#fff6ea', '#7a6048', 1.5)); const key = new THREE.DirectionalLight('#fff2dd', 2.2); key.position.set(3, 5, 4); scene.add(key);
    camera.position.set(0, 1.2, 7.2); camera.lookAt(0, 0.5, 0);
    return { body, head, eyes };
  }, draw(s, t) {
    const f = frameOf(t, 12), ts = held(t, 12), hop = Math.abs(Math.sin(ts * Math.PI * 1.2)), sq = 1 - 0.18 * (1 - hop);
    s.body.position.set(jit(f, 1, 0.02), hop * 0.9 + jit(f, 2, 0.015), 0); s.body.scale.set(1 / Math.sqrt(sq), sq, 1 / Math.sqrt(sq)); s.body.rotation.z = jit(f, 3, 0.03);
    s.head.position.set(jit(f, 4, 0.02), 1.42 * sq + hop * 0.9, 0.1); s.head.rotation.set(jit(f, 5, 0.04), Math.sin(ts * 2) * 0.4, jit(f, 6, 0.04));
    s.eyes.forEach((e) => e.scale.setScalar(f % 30 === 14 ? 0.15 : 1));     // a blink that lasts one drawing
  } },
  'cel-shaded': { kind: '3d', fps: 12, setup(THREE, scene, camera) {
    // light in three hard bands (a tiny gradient texture with no smoothing) and an outline made from a second, inside-out copy
    scene.background = new THREE.Color('#ffd9a8');
    const ramp = new THREE.DataTexture(new Uint8Array([70, 150, 255]), 3, 1, THREE.RedFormat); ramp.minFilter = ramp.magFilter = THREE.NearestFilter; ramp.needsUpdate = true;
    const group = new THREE.Group(), ink = new THREE.MeshBasicMaterial({ color: '#17131c', side: THREE.BackSide });
    const add = (geo, col, x, y, z) => { const m = new THREE.Mesh(geo, new THREE.MeshToonMaterial({ color: col, gradientMap: ramp })); m.position.set(x, y, z); const o = new THREE.Mesh(geo, ink); o.scale.setScalar(1.06); m.add(o); group.add(m); return m; };
    add(new THREE.SphereGeometry(1, 48, 32), '#3f7fd6', 0, 0, 0); add(new THREE.ConeGeometry(0.7, 1.5, 40), '#ff5a5f', 0, 1.5, 0); add(new THREE.TorusGeometry(1.5, 0.16, 20, 80), '#ffd23f', 0, 0, 0).rotation.x = 1.2;
    scene.add(group); const sun = new THREE.DirectionalLight('#ffffff', 3); sun.position.set(4, 5, 5); scene.add(sun, new THREE.AmbientLight('#8a7fb5', 0.9));
    camera.position.set(0, 1, 7.5); camera.lookAt(0, 0.4, 0);
    return { group };
  }, draw(s, t) { const ts = held(t, 12); s.group.rotation.y = ts * 1.4; s.group.rotation.z = Math.sin(ts * 2) * 0.12; s.group.position.y = Math.sin(ts * 2.5) * 0.25; } },
  'low-poly': { kind: '3d', fps: null, setup(THREE, scene, camera) {
    // few polygons, each lit as one flat facet. Clean, so the camera move is smooth, not stepped.
    scene.background = new THREE.Color('#bfe3f2'); scene.fog = new THREE.Fog('#bfe3f2', 9, 22);
    const geo = new THREE.PlaneGeometry(26, 26, 22, 22); geo.rotateX(-Math.PI / 2); const p = geo.attributes.position;
    for (let i = 0; i < p.count; i++) { const x = p.getX(i), z = p.getZ(i), d = Math.hypot(x, z); p.setY(i, Math.max(0, 3.2 - d * 0.42) * (0.6 + hash(i, 9) * 0.9) + hash(i, 4) * 0.25); }
    geo.computeVertexNormals(); const land = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: '#5fa36a', flatShading: true, roughness: 0.9 }));
    const sunBall = new THREE.Mesh(new THREE.IcosahedronGeometry(0.9, 1), new THREE.MeshBasicMaterial({ color: '#ffd166' })); sunBall.position.set(-5, 5.5, -8);
    const trees = new THREE.Group(); for (let i = 0; i < 22; i++) { const a = hash(i, 1) * TAU, r = 3.6 + hash(i, 2) * 5, tr = new THREE.Mesh(new THREE.ConeGeometry(0.34, 1.1, 5), new THREE.MeshStandardMaterial({ color: '#2f6b4f', flatShading: true })); tr.position.set(Math.cos(a) * r, 0.75, Math.sin(a) * r); trees.add(tr); }
    scene.add(land, sunBall, trees, new THREE.HemisphereLight('#ffffff', '#4a6a4a', 1.4)); const key = new THREE.DirectionalLight('#fff0d0', 2.4); key.position.set(-5, 6, 2); scene.add(key);
    return { camera };
  }, draw(s, t) { const a = 0.5 + t * 0.22; s.camera.position.set(Math.sin(a) * 11, 4.6, Math.cos(a) * 11); s.camera.lookAt(0, 1.4, 0); } },
  voxel: { kind: '3d', fps: 12, setup(THREE, scene, camera) {
    // every cube the same size, on a grid, in one instanced mesh. The model builds layer by layer, on twos.
    scene.background = new THREE.Color('#1c2333');
    const cells = []; for (let y = 0; y < 9; y++) for (let x = -4; x <= 4; x++) for (let z = -4; z <= 4; z++) { const d = Math.hypot(x, z); const trunk = y < 4 && d < 1.2, leaves = y >= 3 && Math.hypot(x, (y - 6) * 1.25, z) < 3.6 && hash(x + 9, y, z + 9) > 0.12; if (trunk || leaves) cells.push([x, y, z, trunk && y < 4 && !leaves ? '#7a4f2a' : hash(x, y, z) > 0.5 ? '#3f9b57' : '#2f7d47']); }
    const mesh = new THREE.InstancedMesh(new THREE.BoxGeometry(0.96, 0.96, 0.96), new THREE.MeshLambertMaterial(), cells.length), col = new THREE.Color();
    cells.forEach((c, i) => mesh.setColorAt(i, col.set(c[3]))); scene.add(mesh, new THREE.HemisphereLight('#ffffff', '#33405a', 1.6)); const key = new THREE.DirectionalLight('#ffffff', 2); key.position.set(6, 9, 4); scene.add(key);
    return { mesh, cells, m: new THREE.Matrix4(), camera };
  }, draw(s, t) {
    const ts = held(t, 12), shown = Math.floor(clamp(ts / 2.2) * 9.99);
    s.cells.forEach(([x, y, z], i) => { const on = y <= shown; s.m.makeScale(on ? 1 : 0.0001, on ? 1 : 0.0001, on ? 1 : 0.0001); s.m.setPosition(x, y - 4, z); s.mesh.setMatrixAt(i, s.m); });
    s.mesh.instanceMatrix.needsUpdate = true; const a = 0.7 + ts * 0.35; s.camera.position.set(Math.sin(a) * 15, 6, Math.cos(a) * 15); s.camera.lookAt(0, 0, 0);
  } },
  'product-render': { kind: '3d', fps: null, setup(THREE, scene, camera) {
    // a studio shot: a seamless backdrop, a key, a fill and a rim light, a contact shadow, a slow smooth turntable
    scene.background = new THREE.Color('#dfe3e8');
    const bottle = new THREE.Group(), glass = new THREE.MeshPhysicalMaterial({ color: '#b5462c', roughness: 0.18, metalness: 0, clearcoat: 1, clearcoatRoughness: 0.06 }), metal = new THREE.MeshStandardMaterial({ color: '#c9a25a', roughness: 0.28, metalness: 1 });
    const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.8, 1.5, 12, 40), glass), cap = new THREE.Mesh(new THREE.CylinderGeometry(0.34, 0.34, 0.5, 40), metal), band = new THREE.Mesh(new THREE.TorusGeometry(0.81, 0.04, 12, 60), metal);
    cap.position.y = 1.78; band.rotation.x = Math.PI / 2; band.position.y = 0.3; bottle.add(body, cap, band);
    const sh = new OffscreenCanvas(256, 256), sg = sh.getContext('2d'), rg = sg.createRadialGradient(128, 128, 0, 128, 128, 128); rg.addColorStop(0, 'rgba(20,24,34,.6)'); rg.addColorStop(1, 'rgba(20,24,34,0)'); sg.fillStyle = rg; sg.fillRect(0, 0, 256, 256);
    const shadow = new THREE.Mesh(new THREE.PlaneGeometry(4.4, 4.4), new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(sh), transparent: true, depthWrite: false })); shadow.rotation.x = -Math.PI / 2; shadow.position.y = -1.55;
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), new THREE.MeshStandardMaterial({ color: '#dfe3e8', roughness: 1 })); floor.rotation.x = -Math.PI / 2; floor.position.y = -1.56;
    const key = new THREE.DirectionalLight('#ffffff', 3.2); key.position.set(4, 5, 4); const fillL = new THREE.DirectionalLight('#cfe0ff', 1.1); fillL.position.set(-5, 2, 3); const rim = new THREE.DirectionalLight('#ffe2c0', 2.6); rim.position.set(-2, 4, -6);
    scene.add(floor, shadow, bottle, key, fillL, rim, new THREE.HemisphereLight('#ffffff', '#b0b6c0', 1.1)); camera.position.set(0, 0.9, 7.4); camera.lookAt(0, 0.2, 0);
    return { bottle };
  }, draw(s, t) { s.bottle.rotation.y = t * 0.7; } },
};
export const IDS = Object.keys(LOOKS);
