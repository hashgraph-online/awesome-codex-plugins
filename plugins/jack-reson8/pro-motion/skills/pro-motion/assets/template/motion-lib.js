// motion-lib.js — reusable MG primitives for deterministic canvas films (distilled from a real launch-film project).
// Load before film.js. Provides globals: cv, ctx, W, H, T (current time), BOIL (12fps boil frame), LANG.
// Contract: film.js defines render(t) that is PURE and DETERMINISTIC (no Math.random at draw time) — frames are rendered by parallel tabs.
//
// Index
//   math:      clamp seg lerp eox ein exio eio eback spring hash rand(seed) beatGrid(bpm, grid0)
//   shapes:    rr cover disc hero starPath cardShadow photoCard burst ring3d
//   doodle:    jit smoothPath partial doodle ellP starP heartP sparkle          (lines boil at 12 fps)
//   text:      HF lineIn penText                                                (penText = written on by a pen dot)
//   fx:        metaballs halftone stripes tint outline cutoutFrom lum blush grain
//   beat:      lastIdx since pulse within beatCam(t, lows, highs)                (feed from analysis.json)
//   time:      onTwos speedRamp withTime
//   noise:     noise2 fbm curl
//   layers:    layer(name, draw) samplePts                                      (render off-screen, then post-process)
//   particles: curlParticles assemble
//   light:     saber shine
//   transitions: whipPan iris inkReveal shatter zoomThrough pixelDissolve tear (drawA, drawB, p) · infiniteZoom panels morph resample
//   rhythm:    flash stutter
//   glitch:    rgbSplit glitchSlices mosaic dither crt glow
//   time fx:   slitScan echo
//   generative: scatterGrow taper clothDrop                                    (Blender geometry nodes / Grease Pencil / cloth, faked in 2D)
//   stylised:  extrude toonBall paper riso watercolor hatch ascii tategaki filmDamage textOnPath
//   (what each looks like, where it comes from, parameters: references/vfx-techniques.md)
//   boot:      loadImages loadFonts startFilm({ dur, setup, render })
const cv = document.getElementById('c'); let ctx = cv.getContext('2d');   // let: layer() swaps it to draw off-screen
const W = cv.width, H = cv.height;
let T = 0, BOIL = 0;
const LANG = new URLSearchParams(location.search).get('lang') || 'en';

// ---------- math ----------
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const seg = (t, a, b) => clamp((t - a) / (b - a));
const lerp = (a, b, p) => a + (b - a) * p;
const eox = p => p >= 1 ? 1 : 1 - Math.pow(2, -10 * p);                     // expo out: UI, type, slams
const ein = p => p <= 0 ? 0 : Math.pow(2, 10 * p - 10);                      // expo in: falls, convergence
const exio = p => p <= 0 ? 0 : p >= 1 ? 1 : p < .5 ? Math.pow(2, 20 * p - 10) / 2 : (2 - Math.pow(2, -20 * p + 10)) / 2;
const eio = p => p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;    // cubic in-out: camera, drift
const eback = p => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2); };
const spring = (p, k = 7, f = 12) => p <= 0 ? 0 : 1 - Math.exp(-k * p) * Math.cos(f * p);
const hash = n => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
function rand(seed) { let s = seed | 0 || 1; return () => (s = (s * 16807) % 2147483647) / 2147483647; }
const beatGrid = (bpm, grid0 = 0) => k => grid0 + k * 60 / bpm;               // beat(k) → seconds
const mk = (w, h) => { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; };

// ---------- shapes ----------
function rr(g, x, y, w, h, r) { g.beginPath(); g.roundRect(x, y, w, h, r); }
function cover(g, img, x, y, w, h, zoom = 1, fx = .5, fy = .5) { const iw = img.width, ih = img.height, s = Math.max(w / iw, h / ih) * zoom, sw = w / s, sh = h / s; g.drawImage(img, (iw - sw) * fx, (ih - sh) * fy, sw, sh, x, y, w, h); }
function disc(x, y, r, color, sx = 1, sy = 1, rot = 0) { ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(sx, sy); ctx.fillStyle = color; ctx.beginPath(); ctx.arc(0, 0, Math.max(0, r), 0, 7); ctx.fill(); ctx.restore(); }
// protagonist with squash & stretch: sq > 0 = squashed (landing), sq < 0 = stretched (falling)
function hero(x, y, r, { sq = 0, rot = 0, color = '#FCB901' } = {}) { disc(x, y, r, color, 1 + sq, 1 - sq, rot); }
function starPath(g, x, y, r, rot = 0) { g.beginPath(); for (let i = 0; i <= 10; i++) { const a = -Math.PI / 2 + rot + i * Math.PI / 5, rad = i % 2 ? r * .46 : r; g.lineTo(x + Math.cos(a) * rad, y + Math.sin(a) * rad); } g.closePath(); }
function cardShadow(x, y, w, h, r, a = .2, blur = 60) { ctx.save(); ctx.shadowColor = `rgba(20,25,35,${a})`; ctx.shadowBlur = blur; ctx.shadowOffsetY = blur * .4; ctx.fillStyle = '#fff'; rr(ctx, x, y, w, h, r); ctx.fill(); ctx.restore(); }
function photoCard(img, cx, cy, w, h, r = 44, o = {}) { const x = cx - w / 2, y = cy - h / 2; if (o.shadow !== 0) cardShadow(x, y, w, h, r, o.shadow ?? .2); ctx.save(); rr(ctx, x, y, w, h, r); ctx.clip(); if (img) cover(ctx, img, x, y, w, h, o.zoom || 1, o.fx ?? .5, o.fy ?? .5); else { ctx.fillStyle = o.fill || '#ddd'; ctx.fillRect(x, y, w, h); } ctx.restore(); }
// confetti burst of dots; p = 0..1 progress
function burst(cx, cy, p, n = 14, R = 520, seed = 1, cols = ['#FB7ACB', '#3B7AFA', '#FCB901', '#DC644A', '#388D56'], s0 = 18) {
  if (p <= 0 || p >= 1) return;
  for (let i = 0; i < n; i++) { const a = i / n * 6.283 + hash(seed + i) * .5, d = eox(p) * R * (.5 + hash(seed + i * 3) * .6), r = s0 * (1 - ein(p)) * (.6 + hash(i + seed) * .8); disc(cx + Math.cos(a) * d, cy + Math.sin(a) * d, r, cols[i % cols.length]); }
}
// 3D carousel ring: returns items sorted back→front with screen x, scale, facing; step = rotation in item units
function ring3d(n, step, { cx = W / 2, R = 560, f = 1500 } = {}) {
  return Array.from({ length: n }, (_, i) => { const a = (i - step) / n * 6.283, z = Math.cos(a), depth = f / (f + R * (1 - z)); return { i, a, z, depth, x: cx + Math.sin(a) * R * depth, facing: Math.max(.18, Math.abs(z) * .85 + .15) }; }).sort((p, q) => p.z - q.z);
}

// ---------- doodle layer (hand-drawn lines boil on twos) ----------
const jit = (s0, a) => (hash(s0 * 13.37 + BOIL * 91.7) - .5) * 2 * a;
function smoothPath(pts, close) { ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length - 1; i++) { const mx = (pts[i][0] + pts[i + 1][0]) / 2, my = (pts[i][1] + pts[i + 1][1]) / 2; ctx.quadraticCurveTo(pts[i][0], pts[i][1], mx, my); } const l = pts[pts.length - 1]; ctx.lineTo(l[0], l[1]); if (close) ctx.closePath(); }
function partial(pts, prog) { if (prog >= 1) return pts; if (prog <= 0) return []; const n = (pts.length - 1) * prog, k = Math.floor(n), f = n - k, out = pts.slice(0, k + 1); if (k + 1 < pts.length) { const a = pts[k], b = pts[k + 1]; out.push([lerp(a[0], b[0], f), lerp(a[1], b[1], f)]); } return out; }
// draw-on (trim path) with boil: prog 0..1
function doodle(pts, { color = '#4E8A6E', w = 9, prog = 1, amp = 2.2, seed = 1, close = false, alpha = 1 } = {}) {
  const p = partial(pts.map((q, i) => [q[0] + jit(seed + i * 1.3, amp), q[1] + jit(seed + i * 2.1 + 40, amp)]), prog); if (p.length < 2) return;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.strokeStyle = color; ctx.lineWidth = w; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; smoothPath(p, close && prog >= 1); ctx.stroke(); ctx.restore();
}
const ellP = (cx, cy, rx, ry, n = 40, a0 = 0, turn = 1) => Array.from({ length: n + 1 }, (_, i) => { const a = a0 + i / n * 6.283 * turn; return [cx + Math.cos(a) * rx, cy + Math.sin(a) * ry]; });
const starP = (cx, cy, r) => Array.from({ length: 11 }, (_, i) => { const a = -Math.PI / 2 + i * Math.PI / 5, rad = i % 2 ? r * .45 : r; return [cx + Math.cos(a) * rad, cy + Math.sin(a) * rad]; });
const heartP = (cx, cy, s) => Array.from({ length: 41 }, (_, i) => { const a = i / 40 * 6.283; return [cx + s * Math.pow(Math.sin(a), 3), cy - s * (13 * Math.cos(a) - 5 * Math.cos(2 * a) - 2 * Math.cos(3 * a) - Math.cos(4 * a)) / 16]; });
function sparkle(x, y, r, p, color = '#4E8A6E', seed = 1) { if (p <= 0 || p >= 1) return; const s = Math.sin(p * Math.PI); for (let k = 0; k < 4; k++) { const a = k * Math.PI / 2 + .3; doodle([[x + Math.cos(a) * r * .35, y + Math.sin(a) * r * .35], [x + Math.cos(a) * r * (.35 + .65 * s), y + Math.sin(a) * r * (.35 + .65 * s)]], { color, w: 7, seed: seed + k, amp: 1 }); } }

// ---------- text ----------
// handwriting families (declare @font-face in film.html): HandEN (Patrick Hand: EN+VI), HandZH (ZCOOL KuaiLe), HandJA (Yomogi), HandKO (Gaegu Bold)
const HAND = { en: 'HandEN', vi: 'HandEN', zh: 'HandZH', ja: 'HandJA', ko: 'HandKO' };
const HF = (s, lang = LANG) => `${lang === 'ko' ? 700 : 400} ${s * (lang === 'en' || lang === 'vi' ? 1.12 : 1)}px ${HAND[lang] || 'HandEN'}, "PingFang SC", sans-serif`;
const SANS = (w, s) => `${w} ${s}px "SF Pro Display", system-ui, "PingFang SC", "Hiragino Sans", "Apple SD Gothic Neo", sans-serif`;
const MONO = s => `600 ${s}px "SF Mono", Menlo, monospace`;
// mask-up reveal (clean sans); tout = optional exit time
function lineIn(text, x, y, font, color, tin, tout, { align = 'left', size = 60, spacing = '0px' } = {}) {
  const p = seg(T, tin, tin + .5), q = tout ? seg(T, tout, tout + .25) : 0; if (p <= 0 || q >= 1) return;
  ctx.save(); ctx.font = font; ctx.textAlign = align; ctx.letterSpacing = spacing; ctx.fillStyle = color;
  ctx.beginPath(); ctx.rect(0, y - size * 1.2, W, size * 1.6); ctx.clip(); ctx.fillText(text, x, y + (1 - eox(p)) * size * 1.2 - eox(q) * size * 1.2); ctx.restore();
}
// written on left→right; a pen dot rides the ink edge. Returns text width. out = 0..1 exit.
function penText(text, x, y, size, color, t0, dur, { align = 'center', pen = '#FCB901', tilt = -.03, alpha = 1, font = null, out = 0 } = {}) {
  const p = eio(seg(T, t0, t0 + dur)); if (p <= 0 || out >= 1) return 0;
  ctx.save(); ctx.font = font || HF(size); const w = ctx.measureText(text).width, x0 = align === 'center' ? x - w / 2 : align === 'right' ? x - w : x;
  ctx.translate(x0, y); ctx.rotate(tilt + jit(7, .006));
  ctx.beginPath(); ctx.rect(-30, -size * 1.4, (w + 60) * p, size * 2); ctx.clip();
  ctx.globalAlpha *= alpha * (1 - out); ctx.fillStyle = color; ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic'; ctx.fillText(text, jit(3, 1.2), jit(4, 1.2) - out * 40);
  ctx.restore();
  if (p > 0 && p < 1 && pen) hero(x0 + w * p, y - size * .38 + Math.sin(T * 40) * size * .12, Math.max(9, size * .11), { color: pen });
  return w;
}

// ---------- fx ----------
// metaballs: low-res field → smooth upscale. balls = [{x, y, r}] in canvas px
const MB = mk(Math.round(W / 4), Math.round(H / 4)), MBX = MB.getContext('2d'), MBD = MBX.createImageData(MB.width, MB.height);
function metaballs(balls, color) {
  const d = MBD.data, k = 4, v = parseInt(color.slice(1), 16), R = v >> 16, G = (v >> 8) & 255, B = v & 255;
  for (let y = 0; y < MB.height; y++) for (let x = 0; x < MB.width; x++) {
    let f = 0; const px = x * k, py = y * k; for (const b of balls) { const dx = px - b.x, dy = py - b.y; f += b.r * b.r / (dx * dx + dy * dy + 1); }
    const i = (y * MB.width + x) * 4; d[i] = R; d[i + 1] = G; d[i + 2] = B; d[i + 3] = clamp((f - .9) * 6) * 255;
  }
  MBX.putImageData(MBD, 0, 0); ctx.drawImage(MB, 0, 0, W, H);
}
const lum = c => c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
// halftone dots from luminance data d (w×h); curve maps lightness→radius factor
function halftone(g, d, w, h, sp, color, ang = 0, k = .64, curve = l => 1 - l, ox = 0, oy = 0) {
  g.fillStyle = color; const ca = Math.cos(ang), sa = Math.sin(ang), R = Math.hypot(w, h) * .55;
  for (let v = -R, row = 0; v < R; v += sp * .866, row++) for (let u = -R + (row % 2 ? sp / 2 : 0); u < R; u += sp) {
    const x = w / 2 + u * ca - v * sa, y = h / 2 + u * sa + v * ca; if (x < -sp || y < -sp || x > w + sp || y > h + sp) continue;
    const i = (clamp(y | 0, 0, h - 1) * w + clamp(x | 0, 0, w - 1)) * 4, l = clamp(((d[i] * .3 + d[i + 1] * .59 + d[i + 2] * .11) / 255 - .08) / .8), r = curve(l) * sp * k;
    if (r > .6) { g.beginPath(); g.arc(x + ox, y + oy, r, 0, 7); g.fill(); }
  }
}
function stripes(w, h, color, vertical = false, band = 22, gap = 18, paper = '#FBF8F2') { const c = mk(w, h), g = c.getContext('2d'); g.fillStyle = paper; g.fillRect(0, 0, w, h); g.fillStyle = color; if (vertical) for (let x = 0; x < w; x += band + gap) g.fillRect(x, 0, band, h); else for (let y = 0; y < h; y += band + gap) g.fillRect(0, y, w, band); return c; }
function tint(src, color) { const c = mk(src.width, src.height), g = c.getContext('2d'); g.drawImage(src, 0, 0); g.globalCompositeOperation = 'source-in'; g.fillStyle = color; g.fillRect(0, 0, c.width, c.height); return c; }
// sticker outline: dilate alpha by px in `color`, then the source on top
function outline(src, px, color = '#fff') { const c = mk(src.width, src.height), g = c.getContext('2d'); for (let a = 0; a < 24; a++) g.drawImage(src, Math.cos(a / 24 * 6.283) * px, Math.sin(a / 24 * 6.283) * px); g.globalCompositeOperation = 'source-in'; g.fillStyle = color; g.fillRect(0, 0, c.width, c.height); g.globalCompositeOperation = 'source-over'; g.drawImage(src, 0, 0); return c; }
// subject cut-out from an image + L8 mask PNG (from scripts/cutout.swift), at w×h
function cutoutFrom(img, maskImg, w = img.width, h = img.height) {
  const m = mk(w, h), mg = m.getContext('2d'); mg.drawImage(maskImg, 0, 0, w, h);
  const d = mg.getImageData(0, 0, w, h); for (let i = 0; i < d.data.length; i += 4) { d.data[i + 3] = d.data[i]; d.data[i] = d.data[i + 1] = d.data[i + 2] = 255; } mg.putImageData(d, 0, 0);
  const c = mk(w, h), g = c.getContext('2d'); cover(g, img, 0, 0, w, h); g.globalCompositeOperation = 'destination-in'; g.drawImage(m, 0, 0); return c;
}
// airy base: cream with three slow-drifting soft colour fields
function blush(t, base = '#F4F0E8', fields = [['#FB7ACB', .14, .17, .14], ['#62C0DA', .14, .89, .47], ['#FCB901', .12, .28, .86]]) {
  ctx.fillStyle = base; ctx.fillRect(0, 0, W, H);
  fields.forEach(([c, a, fx, fy], k) => { const px = fx * W + Math.sin(t * .4 + k) * 110, py = fy * H + Math.cos(t * .3 + k) * 130, g = ctx.createRadialGradient(px, py, 0, px, py, W * .76), v = parseInt(c.slice(1), 16), rgb = `${v >> 16},${(v >> 8) & 255},${v & 255}`; g.addColorStop(0, `rgba(${rgb},${a})`); g.addColorStop(1, `rgba(${rgb},0)`); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); });
}
// seeded film grain overlay (deterministic across workers)
let NOISE = null;
function grain(t, amount = .06) {
  if (!NOISE) { NOISE = mk(W + 512, H + 512); const g = NOISE.getContext('2d'), d = g.createImageData(NOISE.width, NOISE.height), r = rand(7); for (let i = 0; i < d.data.length; i += 4) { const v = r() * 255; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 255; } g.putImageData(d, 0, 0); }
  ctx.save(); ctx.globalAlpha = amount; ctx.globalCompositeOperation = 'overlay'; ctx.drawImage(NOISE, -((t * 431) % 256), -((t * 277) % 256)); ctx.restore();
}

// ---------- beat (feed from music/analysis.json: onsets / low_hits / high_hits) ----------
const lastIdx = (L, t) => { let i = -1; for (let k = 0; k < L.length && L[k] <= t; k++) i = k; return i; };
const since = (L, t) => { const i = lastIdx(L, t); return i < 0 ? 99 : t - L[i]; };
const pulse = (L, t, k = 12) => Math.exp(-since(L, t) * k);                  // 1 on a hit, decays; k = decay speed
const within = (L, a, b) => L.filter(x => x >= a && x < b);                  // build a scene's changes from the hits inside it
// beat camera: zoom punch + tilt on lows, micro jitter on hats. Call inside save/restore before a scene draws.
function beatCam(t, lows, highs = [], { amt = 1, punch = .05, tilt = .035, jitter = 16, cx = W / 2, cy = H / 2 } = {}) {
  const p = pulse(lows, t, 9) * amt, q = pulse(highs, t, 20) * amt, i = lastIdx(lows, t), j = lastIdx(highs, t), z = 1 + punch * p + .012 * q;
  ctx.translate(cx + (hash(j * 5.1) - .5) * jitter * q, cy + (hash(j * 2.3) - .5) * jitter * q); ctx.rotate((hash(i * 3.7) - .5) * tilt * p); ctx.scale(z, z); ctx.translate(-cx, -cy);
}

// ---------- time ----------
const onTwos = (t, fps = 12) => Math.floor(t * fps) / fps;                   // hold poses: 12 = on twos @24, 8 = on threes
// speed ramp: piecewise-linear time remap [[tIn, tOut], …] — flat segment = freeze, steep = punch, shallow = slow-mo
function speedRamp(t, keys) { if (t <= keys[0][0]) return keys[0][1] + t - keys[0][0]; for (let i = 1; i < keys.length; i++) if (t <= keys[i][0]) { const [a0, b0] = keys[i - 1], [a1, b1] = keys[i]; return lerp(b0, b1, (t - a0) / (a1 - a0)); } const l = keys[keys.length - 1]; return l[1] + t - l[0]; }
// draw a scene at another time (sets T / BOIL so lineIn, penText, doodle follow)
function withTime(t, fn) { const t0 = T, b0 = BOIL; T = t; BOIL = Math.floor(t * 12); try { return fn(t); } finally { T = t0; BOIL = b0; } }

// ---------- noise ----------
const noise2 = (x, y) => { const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi, u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf), h = (a, b) => hash(a * 57.31 + b * 113.7);
  return lerp(lerp(h(xi, yi), h(xi + 1, yi), u), lerp(h(xi, yi + 1), h(xi + 1, yi + 1), u), v); };
const fbm = (x, y, o = 4) => { let s = 0, a = .5, n = 0; for (let i = 0; i < o; i++) { s += a * noise2(x, y); n += a; x = x * 2.03 + 17; y = y * 2.03 + 31; a *= .5; } return s / n; };
// divergence-free flow (curl of a noise field), z = time-like slice → swirls without clumping (Trapcode Particular turbulence)
const curl = (x, y, z = 0) => { const e = .02, n = (a, b) => fbm(a + z * 1.7, b - z * 1.3, 2); return [(n(x, y + e) - n(x, y - e)) / (2 * e), -(n(x + e, y) - n(x - e, y)) / (2 * e)]; };

// ---------- layers (render a scene off-screen, then post-process it) ----------
const LAYERS = {};
function layer(name, draw, w = W, h = H) {
  const c = LAYERS[name] && LAYERS[name].width === w ? LAYERS[name] : (LAYERS[name] = mk(w, h)), g = c.getContext('2d'), prev = ctx;
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over'; g.filter = 'none'; g.clearRect(0, 0, w, h);
  ctx = g; try { draw(g); } finally { ctx = prev; } return c;
}
// points where a drawing is opaque — sample a logo / word, then assemble particles into it
function samplePts(draw, step = 12, seed = 1) {
  const c = layer('_sample', draw), d = c.getContext('2d').getImageData(0, 0, W, H).data, out = [];
  for (let y = 0; y < H; y += step) for (let x = 0; x < W; x += step) { const jx = x + (hash(seed + x * .13 + y) - .5) * step * .6, jy = y + (hash(seed + y * .17 + x) - .5) * step * .6; if (d[((jy | 0) * W + (jx | 0)) * 4 + 3] > 128) out.push([jx, jy]); }
  return out;
}

// ---------- particles ----------
// Trapcode-Particular-style flow: each particle is re-integrated from its birth every frame (deterministic, any frame order).
// emit(i, cycle) → [x, y]; rate = particles / s; life ≤ n / rate; trail = points kept per streak
function curlParticles(t, { n = 300, seed = 1, emit = () => [W / 2, H * .8], t0 = 0, rate = 150, life = 1.8, speed = 420, scale = .0022, drift = [0, -120], trail = 7, color = '#fff', size = 4, blend = 'lighter', dt = 1 / 30 } = {}) {
  const period = n / rate; if (t < t0) return;
  ctx.save(); ctx.globalCompositeOperation = blend; ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineCap = 'round';
  for (let i = 0; i < n; i++) {
    const local = t - t0 - i / rate; if (local < 0) continue;
    const cyc = Math.floor(local / period), age = local - cyc * period; if (age > life) continue;
    const s = seed + i * 7.3 + cyc * 131, birth = t - age; let [x, y] = emit(i, cyc); const pts = [[x, y]], steps = Math.floor(age / dt);
    const sp = speed * (.6 + hash(s) * .8);
    for (let k = 0; k < steps; k++) { const [vx, vy] = curl(x * scale, y * scale, (birth + k * dt) * .25 + seed); x += (vx * sp + drift[0]) * dt; y += (vy * sp + drift[1]) * dt; if (k >= steps - trail) pts.push([x, y]); }
    const f = 1 - age / life, w = size * f * (.5 + hash(s + 2)); ctx.globalAlpha = Math.min(1, f * 1.4);
    if (pts.length > 2) { ctx.lineWidth = w; ctx.beginPath(); pts.slice(-trail).forEach((q, k) => k ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1])); ctx.stroke(); }
    else { ctx.beginPath(); ctx.arc(x, y, w / 2, 0, 7); ctx.fill(); }
  }
  ctx.restore();
}
// scattered dots fly into target points (from samplePts) with stagger — logo / word assembles on the drop. p 0..1
function assemble(pts, p, { seed = 1, spread = 900, stagger = .35, r = 5, color = '#fff', from = null } = {}) {
  ctx.save(); ctx.fillStyle = color;
  pts.forEach(([x, y], i) => { const d = hash(seed + i * 1.7) * stagger, q = eox(seg(p, d, d + 1 - stagger)), a = hash(seed + i) * 6.283, R = spread * (.4 + hash(seed + i * 3)), sx = from ? from[0] : x + Math.cos(a) * R, sy = from ? from[1] : y + Math.sin(a) * R;
    ctx.beginPath(); ctx.arc(lerp(sx, x, q), lerp(sy, y, q), r * lerp(.4, 1, q), 0, 7); ctx.fill(); });
  ctx.restore();
}

// ---------- light ----------
// Saber-style neon stroke: three glow passes + hot core; flickers at 24 fps. pts as for doodle; prog = trim path
function saber(pts, { color = '#2FB6FF', core = '#fff', w = 8, glow = 46, prog = 1, flicker = .18, seed = 1 } = {}) {
  const p = partial(pts, prog); if (p.length < 2) return; const f = 1 - flicker * hash(seed + Math.floor(T * 24));
  ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.strokeStyle = color; ctx.shadowColor = color;
  [[w * 5, .16, glow], [w * 2.4, .4, glow * .5], [w * 1.3, .85, glow * .2]].forEach(([lw, a, b]) => { ctx.globalAlpha = a * f; ctx.lineWidth = lw * f; ctx.shadowBlur = b * f; smoothPath(p); ctx.stroke(); });
  ctx.shadowBlur = 0; ctx.globalAlpha = f; ctx.strokeStyle = core; ctx.lineWidth = w * .55; smoothPath(p); ctx.stroke(); ctx.restore();
}
// Trapcode-Shine-style rays: radial zoom-smear of a layer's bright parts from (x, y). Draw over the layer itself.
function shine(src, x, y, { len = .5, n = 14, alpha = .14, res = 4 } = {}) {
  const s = layer('_shine', g => g.drawImage(src, 0, 0, W / res, H / res), W / res, H / res);
  ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.filter = `blur(${8 / res}px)`;
  for (let i = 1; i <= n; i++) { const k = 1 + len * i / n; ctx.globalAlpha = alpha * (1 - i / (n + 1)); ctx.drawImage(s, x - x * k, y - y * k, W * k, H * k); }
  ctx.restore();
}

// ---------- transitions (drawA / drawB draw full frames; p 0..1) ----------
// whip pan with directional smear (AE motion blur); dir in radians (0 = A exits left)
function whipPan(drawA, drawB, p, { dir = 0, blur = 1, taps = 9, bg = '#000' } = {}) {
  const A = layer('_wa', drawA), B = layer('_wb', drawB), e = exio(clamp(p)), v = Math.pow(Math.sin(Math.PI * clamp(p)), 2) * blur, ux = -Math.cos(dir), uy = -Math.sin(dir), L = Math.abs(ux) * W + Math.abs(uy) * H;
  ctx.save(); ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);
  for (let j = 0; j < taps; j++) { const o = (j / (taps - 1) - .5) * v * L * .3, d = e * L + o; ctx.globalAlpha = 1 / (j + 1); // running average = box blur
    ctx.drawImage(A, ux * d, uy * d); ctx.drawImage(B, ux * (d - L), uy * (d - L)); }
  ctx.restore();
}
// iris / shape wipe: B appears inside a growing shape. shape: 'circle' | 'star' | 'heart' | (g, r) => path
function iris(drawA, drawB, p, { x = W / 2, y = H / 2, shape = 'circle', rot = 0, ring = 0, ringColor = '#fff' } = {}) {
  drawA(); const r = eio(clamp(p)) * Math.hypot(W, H) * (shape === 'circle' ? .6 : 1.05); if (r <= 0) return;
  const path = g => { g.beginPath(); if (typeof shape === 'function') shape(g, r); else if (shape === 'circle') g.arc(0, 0, r, 0, 6.2832); else (shape === 'star' ? starP(0, 0, r) : heartP(0, 0, r / 16)).forEach((q, i) => i ? g.lineTo(q[0], q[1]) : g.moveTo(q[0], q[1])); g.closePath(); };
  const B = layer('_iris', drawB); ctx.save(); ctx.translate(x, y); ctx.rotate(rot + p * .6); path(ctx); ctx.clip(); ctx.rotate(-(rot + p * .6)); ctx.drawImage(B, -x, -y); ctx.restore();
  if (ring) { ctx.save(); ctx.translate(x, y); ctx.rotate(rot + p * .6); path(ctx); ctx.strokeStyle = ringColor; ctx.lineWidth = ring; ctx.stroke(); ctx.restore(); }
}
// ink / liquid bleed: B spreads through a noise-edged blob from (cx, cy) — Shadertoy "noise dissolve" at 1/6 res
const INK = mk(Math.round(W / 6), Math.round(H / 6)), INKX = INK.getContext('2d'), INKD = INKX.createImageData(INK.width, INK.height);
function inkReveal(drawA, drawB, p, { cx = W / 2, cy = H / 2, scale = 5, seed = 1, soft = .05, noise = .55 } = {}) {
  drawA(); if (p <= 0) return; const w = INK.width, h = INK.height, d = INKD.data, th = p * (1 + noise + soft) - soft;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const r = Math.hypot(x / w - cx / W, (y / h - cy / H) * H / W) / 1.15, v = r * (1 - noise) + fbm(x / w * scale + seed * 7, y / w * scale) * noise, i = (y * w + x) * 4; d[i + 3] = clamp((th - v) / soft) * 255; }
  INKX.putImageData(INKD, 0, 0);
  const B = layer('_ink', drawB); B.getContext('2d').globalCompositeOperation = 'destination-in'; B.getContext('2d').drawImage(INK, 0, 0, W, H); ctx.drawImage(B, 0, 0);
}
// shatter: A breaks into triangles flying away from (cx, cy), revealing B behind. p 0..1
function shatter(drawA, drawB, p, { cx = W / 2, cy = H / 2, cols = 6, rows = 10, seed = 3, force = 1400 } = {}) {
  drawB(); if (p >= 1) return; const A = layer('_sh', drawA), cw = W / cols, ch = H / rows;
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) for (let k = 0; k < 2; k++) {
    const x0 = c * cw, y0 = r * ch, tri = k ? [[x0, y0], [x0 + cw, y0], [x0, y0 + ch]] : [[x0 + cw, y0], [x0 + cw, y0 + ch], [x0, y0 + ch]], mx = (tri[0][0] + tri[1][0] + tri[2][0]) / 3, my = (tri[0][1] + tri[1][1] + tri[2][1]) / 3;
    const id = seed + r * 31 + c * 7 + k, a = Math.atan2(my - cy, mx - cx), dd = Math.hypot(mx - cx, my - cy), q = ein(clamp((p - dd / 4000 * .5) / .8)), push = q * force * (.6 + hash(id) * .8);
    ctx.save(); ctx.translate(mx + Math.cos(a) * push, my + Math.sin(a) * push + q * q * 900); ctx.rotate((hash(id + 1) - .5) * 6 * q); ctx.scale(1 - q * .4, 1 - q * .4); ctx.translate(-mx, -my);
    ctx.beginPath(); tri.forEach((v, i) => i ? ctx.lineTo(v[0], v[1]) : ctx.moveTo(v[0], v[1])); ctx.closePath(); ctx.clip(); ctx.drawImage(A, 0, 0); ctx.restore();
  }
}
// infinite zoom (Droste): drawLevel(k) draws level k full-frame with a window of size W/ratio × H/ratio at the centre where level k+1 lives.
// z grows 0 → n; each integer = one level passed through.
function infiniteZoom(drawLevel, z, { ratio = 3.2, depth = 3 } = {}) {
  const k0 = Math.floor(z), s = Math.pow(ratio, z - k0);
  for (let k = k0; k < k0 + depth; k++) { const sc = s / Math.pow(ratio, k - k0), L = layer('_iz' + (k - k0), () => drawLevel(k));
    ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(sc, sc); ctx.drawImage(L, -W / 2, -H / 2); ctx.restore(); }
}
// manga / comic panels: [{poly: [[x,y]…], t0, draw(), from: [dx, dy]}] — each panel slides in on its hit, thick black frames
function panels(list, t, { border = 10, color = '#111', dur = .35 } = {}) {
  list.forEach(pn => { const q = eox(seg(t, pn.t0, pn.t0 + dur)); if (q <= 0) return; const [dx, dy] = pn.from || [0, 220], path = () => { ctx.beginPath(); pn.poly.forEach((v, i) => i ? ctx.lineTo(v[0], v[1]) : ctx.moveTo(v[0], v[1])); ctx.closePath(); };
    ctx.save(); path(); ctx.clip(); ctx.translate((1 - q) * dx, (1 - q) * dy); pn.draw(t); ctx.restore();
    ctx.save(); ctx.globalAlpha = Math.min(1, q * 3); path(); ctx.strokeStyle = color; ctx.lineWidth = border; ctx.lineJoin = 'miter'; ctx.stroke(); ctx.restore(); });
}

// ---------- glitch / digital (src = a layer) ----------
const CHN = [0, 1, 2].map(() => mk(W, H));
// RGB split: channels pulled apart along (dx, dy); draws an opaque frame
function rgbSplit(src, dx, dy = 0) {
  ctx.save(); ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H); ctx.globalCompositeOperation = 'lighter';
  ['#f00', '#0f0', '#00f'].forEach((c, k) => { const g = CHN[k].getContext('2d'); g.globalCompositeOperation = 'copy'; g.drawImage(src, 0, 0); g.globalCompositeOperation = 'multiply'; g.fillStyle = c; g.fillRect(0, 0, W, H); g.globalCompositeOperation = 'destination-in'; g.drawImage(src, 0, 0); ctx.drawImage(CHN[k], dx * (k - 1), dy * (k - 1)); });
  ctx.restore();
}
// block glitch: horizontal bands shoved sideways, re-rolled at `fps`; amt 0..1 (drive with pulse(highs, t))
function glitchSlices(src, amt, { seed = 1, bands = 14, max = 140, fps = 24 } = {}) {
  ctx.drawImage(src, 0, 0); if (amt <= 0) return; const f = Math.floor(T * fps);
  for (let i = 0; i < bands; i++) { const s = seed + i * 13 + f * 7.1; if (hash(s) > amt * .9) continue; const y = hash(s + 1) * H, h = 8 + hash(s + 2) * 90, dx = (hash(s + 3) - .5) * 2 * max * amt;
    ctx.drawImage(src, 0, y, W, h, dx, y, W, h); }
}
// mosaic / pixelate (size px); smoothing off keeps blocks hard
function mosaic(src, size = 24) { const w = Math.max(1, Math.round(W / size)), h = Math.max(1, Math.round(H / size)), s = layer('_mo', g => g.drawImage(src, 0, 0, w, h), w, h); ctx.save(); ctx.imageSmoothingEnabled = false; ctx.drawImage(s, 0, 0, w, h, 0, 0, W, H); ctx.restore(); }
// ordered (Bayer 4×4) dither to a palette ordered dark → light — Obra Dinn / Game Boy look. px = cell size
const BAYER = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5].map(v => (v + .5) / 16);
function dither(src, { palette = ['#1B1B2F', '#F2EBDD'], px = 4, contrast = 1.15 } = {}) {
  const w = Math.round(W / px), h = Math.round(H / px), c = layer('_di', g => g.drawImage(src, 0, 0, w, h), w, h), g = c.getContext('2d'), im = g.getImageData(0, 0, w, h), d = im.data, n = palette.length - 1;
  const P = palette.map(s => { const v = parseInt(s.slice(1), 16); return [v >> 16, (v >> 8) & 255, v & 255]; });
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const i = (y * w + x) * 4, l = clamp(((d[i] * .3 + d[i + 1] * .59 + d[i + 2] * .11) / 255 - .5) * contrast + .5), v = Math.min(n, Math.floor(l * n + BAYER[(y & 3) * 4 + (x & 3)])), q = P[v]; d[i] = q[0]; d[i + 1] = q[1]; d[i + 2] = q[2]; d[i + 3] = 255; }
  g.putImageData(im, 0, 0); ctx.save(); ctx.imageSmoothingEnabled = false; ctx.drawImage(c, 0, 0, w, h, 0, 0, W, H); ctx.restore();
}
// CRT: scanlines + RGB-mask shimmer + vignette over whatever is drawn
function crt({ lines = 3, alpha = .22, vignette = .55 } = {}) {
  ctx.save(); ctx.globalAlpha = alpha; ctx.fillStyle = '#000'; for (let y = (T * 60 | 0) % lines; y < H; y += lines) ctx.fillRect(0, y, W, 1);
  ctx.globalAlpha = 1; const g = ctx.createRadialGradient(W / 2, H / 2, H * .25, W / 2, H / 2, H * .75); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, `rgba(0,0,0,${vignette})`); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); ctx.restore();
}

// ---------- time displacement ----------
// slit-scan / AE Time Displacement: each band shows the scene `lag` s later than the previous. drawAt(t) draws a full frame.
function slitScan(drawAt, t, { bands = 24, lag = .5, vertical = false } = {}) {
  for (let i = 0; i < bands; i++) { const L = layer('_ss', () => withTime(t - lag * i / (bands - 1), drawAt)), a = (vertical ? W : H) * i / bands, b = (vertical ? W : H) / bands + 1;
    if (vertical) ctx.drawImage(L, a, 0, b, H, a, 0, b, H); else ctx.drawImage(L, 0, a, W, b, 0, a, W, b); }
}
// echo (AE Echo): past copies of a moving object, fading. drawAt(t) draws only the object (transparent bg).
function echo(drawAt, t, { n = 5, gap = .045, decay = .55, blend = 'source-over' } = {}) {
  ctx.save(); ctx.globalCompositeOperation = blend;
  for (let i = n; i >= 1; i--) { const L = layer('_ec', () => withTime(t - i * gap, drawAt)); ctx.globalAlpha = Math.pow(decay, i); ctx.drawImage(L, 0, 0); }
  ctx.restore(); withTime(t, drawAt);
}

// ---------- 3D-ish & stylised ----------
// extrusion (Element 3D / long shadow): drawShape(color, isFace) draws at the current origin; depth px along ang
function extrude(drawShape, { depth = 40, ang = 2.2, side = '#1a1a1a', step = 1.5 } = {}) {
  const ux = Math.cos(ang), uy = Math.sin(ang);
  for (let d = depth; d > 0; d -= step) { ctx.save(); ctx.translate(ux * d, uy * d); drawShape(side, false); ctx.restore(); }
  drawShape(null, true);
}
// cel-shaded sphere (Blender toon / anime): flat base, hard shadow crescent, rim light, hard highlight, ink outline. light = angle
function toonBall(x, y, r, { base = '#FB7ACB', shade = '#C04F98', hi = '#FFF4FA', rim = null, light = -2.3, ink = '#1a1020', line = 0 } = {}) {
  const lx = Math.cos(light), ly = Math.sin(light); line = line || Math.max(3, r * .045);
  ctx.save(); ctx.beginPath(); ctx.arc(x, y, r, 0, 6.2832); ctx.fillStyle = base; ctx.fill(); ctx.clip();
  ctx.beginPath(); ctx.arc(x + lx * r * .42, y + ly * r * .42, r * 1.08, 0, 6.2832); ctx.rect(x - r * 2, y - r * 2, r * 4, r * 4); ctx.fillStyle = shade; ctx.fill('evenodd');
  if (rim) { ctx.beginPath(); ctx.arc(x - lx * r * .1, y - ly * r * .1, r, 0, 6.2832); ctx.arc(x - lx * r * .2, y - ly * r * .2, r * .97, 0, 6.2832, true); ctx.fillStyle = rim; ctx.fill(); }
  ctx.beginPath(); ctx.ellipse(x + lx * r * .45, y + ly * r * .45, r * .2, r * .12, light + 1.2, 0, 6.2832); ctx.fillStyle = hi; ctx.fill(); ctx.restore();
  ctx.beginPath(); ctx.arc(x, y, r, 0, 6.2832); ctx.strokeStyle = ink; ctx.lineWidth = line; ctx.stroke();
}
// cut paper (Paper Mario / Tearaway / stop-motion craft): a layer lifted off the page with soft shadow, fibre texture and
// a 1–2 px stop-motion wobble on twos. draw() draws the shape(s) in flat colour.
let PAPER = null;
function paper(draw, { lift = 14, shadow = .28, wobble = 1.5, seed = 1, tex = .18 } = {}) {
  if (!PAPER) { PAPER = mk(512, 512); const g = PAPER.getContext('2d'), d = g.createImageData(512, 512); for (let y = 0; y < 512; y++) for (let x = 0; x < 512; x++) { const v = 255 - (fbm(x / 6, y / 40, 3) * .6 + noise2(x * 1.3, y * 1.3) * .4) * 90, i = (y * 512 + x) * 4; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 255; } g.putImageData(d, 0, 0); }
  const L = layer('_pp', draw), g = L.getContext('2d'); g.globalCompositeOperation = 'source-atop'; g.globalAlpha = tex; g.fillStyle = g.createPattern(PAPER, 'repeat'); g.fillRect(0, 0, W, H); // multiply-ish fibre shading
  const b = Math.floor(T * 12), jx = (hash(seed + b) - .5) * 2 * wobble, jy = (hash(seed + b * 1.7) - .5) * 2 * wobble;
  ctx.save(); ctx.shadowColor = `rgba(30,20,10,${shadow})`; ctx.shadowBlur = lift * 1.6; ctx.shadowOffsetX = lift * .35; ctx.shadowOffsetY = lift * .8; ctx.drawImage(L, jx, jy); ctx.restore();
}
// risograph: one mono drawing printed in 2–3 inks with misregistration + grain; draw() paints in black
function riso(draw, { inks = ['#FF48B0', '#0078BF'], off = 7, paperColor = '#F3EEE3', seed = 1, bg = true } = {}) {
  if (bg) { ctx.fillStyle = paperColor; ctx.fillRect(0, 0, W, H); }
  const L = layer('_ri', draw), b = Math.floor(T * 8);
  ctx.save(); ctx.globalCompositeOperation = 'multiply';
  inks.forEach((c, k) => { const g = CHN[k % 3].getContext('2d'); g.globalCompositeOperation = 'copy'; g.drawImage(L, 0, 0); g.globalCompositeOperation = 'source-in'; g.fillStyle = c; g.fillRect(0, 0, W, H);
    ctx.globalAlpha = .9; ctx.drawImage(CHN[k % 3], (hash(seed + k * 5 + b) - .5) * 2 * off + (k - .5) * off, (hash(seed + k * 9 + b) - .5) * 2 * off); });
  ctx.restore(); grain(T, .08);
}
// text riding a path (pts as for doodle); offset 0..1 slides it along
function textOnPath(text, pts, { offset = 0, font = SANS(800, 64), color = '#111', spacing = 1 } = {}) {
  const segs = []; let tot = 0; for (let i = 1; i < pts.length; i++) { const l = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); segs.push(l); tot += l; }
  const at = s => { s = clamp(s, 0, tot); let i = 0; while (i < segs.length - 1 && s > segs[i]) s -= segs[i++]; const a = pts[i], b = pts[i + 1], f = segs[i] ? s / segs[i] : 0; return [lerp(a[0], b[0], f), lerp(a[1], b[1], f), Math.atan2(b[1] - a[1], b[0] - a[0])]; };
  ctx.save(); ctx.font = font; ctx.fillStyle = color; ctx.textBaseline = 'middle'; let s = offset * tot;
  for (const ch of text) { const w = ctx.measureText(ch).width * spacing; if (s + w / 2 > tot) break; const [x, y, a] = at(s + w / 2); ctx.save(); ctx.translate(x, y); ctx.rotate(a); ctx.fillText(ch, -w / 2 / spacing, 0); ctx.restore(); s += w; }
  ctx.restore();
}
// ---------- more transitions ----------
// zoom-through: camera dives into a hole of A at (cx, cy); B is what's inside the hole and grows to full frame (no blend needed)
function zoomThrough(drawA, drawB, p, { cx = W / 2, cy = H / 2, hole = 90, maxZoom = 40, flash = .2 } = {}) {
  const s = 1 + ein(clamp(p)) * maxZoom, A = layer('_za', drawA), B = layer('_zb', drawB), R = hole * s, full = Math.hypot(W, H) / 2, sb = clamp(R / full, .04, 1);
  ctx.save(); ctx.translate(cx, cy); ctx.scale(s, s); ctx.drawImage(A, -cx, -cy); ctx.restore();
  ctx.save(); ctx.beginPath(); ctx.arc(cx, cy, R, 0, 6.2832); ctx.clip(); ctx.translate(lerp(cx, W / 2, sb), lerp(cy, H / 2, sb)); ctx.scale(sb, sb); ctx.drawImage(B, -W / 2, -H / 2); ctx.restore();
  if (flash && p > .85 && p < 1) { ctx.fillStyle = `rgba(255,255,255,${flash * Math.sin(seg(p, .85, 1) * Math.PI)})`; ctx.fillRect(0, 0, W, H); }
}
// pixel dissolve (gl-transitions style): cells flip A → B by a per-cell threshold; order 'random' | 'radial' | 'wipe'
function pixelDissolve(drawA, drawB, p, { cell = 48, order = 'random', seed = 1 } = {}) {
  const A = layer('_pa', drawA), B = layer('_pb', drawB);
  for (let y = 0; y < H; y += cell) for (let x = 0; x < W; x += cell) { const i = x / cell, j = y / cell, th = order === 'radial' ? Math.hypot(x - W / 2, y - H / 2) / Math.hypot(W / 2, H / 2) : order === 'wipe' ? (x / W * .3 + y / H * .7) : hash(seed + i * 31 + j * 17);
    ctx.drawImage(p * 1.02 > th ? B : A, x, y, cell, cell, x, y, cell, cell); }
}
// paper tear: A rips along a jagged vertical line, halves pull apart, B behind; white fibre edge
function tear(drawA, drawB, p, { x0 = W / 2, seed = 2, teeth = 26, edge = 10 } = {}) {
  drawB(); if (p >= 1) return; const A = layer('_ta', drawA), sep = eio(clamp(p)) * W * .6, zig = Array.from({ length: teeth + 1 }, (_, i) => [x0 + (hash(seed + i) - .5) * 70, i / teeth * H]);
  [-1, 1].forEach(side => { ctx.save(); ctx.translate(side * sep, 0); ctx.rotate(side * p * .05); ctx.beginPath(); ctx.moveTo(side < 0 ? -W : 2 * W, 0); zig.forEach(q => ctx.lineTo(q[0], q[1])); ctx.lineTo(side < 0 ? -W : 2 * W, H); ctx.closePath();
    ctx.save(); ctx.clip(); ctx.drawImage(A, 0, 0); ctx.restore(); ctx.strokeStyle = '#FBF8F2'; ctx.lineWidth = edge; ctx.beginPath(); zig.forEach((q, i) => i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1])); ctx.stroke(); ctx.restore(); });
}
// shape morph: resample both outlines to n points by arc length, align start, lerp. Returns points (fill with smoothPath)
function resample(pts, n = 64) { const L = [0]; for (let i = 1; i < pts.length; i++) L.push(L[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])); const tot = L[L.length - 1], out = []; let k = 0;
  for (let i = 0; i < n; i++) { const s = tot * i / n; while (k < L.length - 2 && L[k + 1] < s) k++; const f = (s - L[k]) / (L[k + 1] - L[k] || 1); out.push([lerp(pts[k][0], pts[k + 1][0], f), lerp(pts[k][1], pts[k + 1][1], f)]); } return out; }
function morph(ptsA, ptsB, p, n = 64) { const a = resample(ptsA, n), b0 = resample(ptsB, n); let best = 0, bd = Infinity; for (let s = 0; s < n; s++) { let d = 0; for (let i = 0; i < n; i += 4) { const q = b0[(i + s) % n]; d += (a[i][0] - q[0]) ** 2 + (a[i][1] - q[1]) ** 2; } if (d < bd) { bd = d; best = s; } }
  const e = eio(clamp(p)); return a.map((v, i) => { const q = b0[(i + best) % n]; return [lerp(v[0], q[0], e), lerp(v[1], q[1], e)]; }); }

// ---------- rhythm ----------
// flash frame on chosen hits (not every beat): mode 'white' | 'black' | 'invert'; frames at 60 fps
function flash(t, hits, { mode = 'white', frames = 2, alpha = .9 } = {}) {
  if (since(hits, t) > frames / 60) return; ctx.save(); if (mode === 'invert') { ctx.globalCompositeOperation = 'difference'; ctx.fillStyle = '#fff'; } else { ctx.globalAlpha = alpha; ctx.fillStyle = mode === 'black' ? '#000' : '#fff'; } ctx.fillRect(0, 0, W, H); ctx.restore();
}
// stutter: pick scene index from a pattern stepped at fps, e.g. stutter(t, t0, [0,0,1,0,1,1]) → draw scenes[k]
const stutter = (t, t0, pattern = [0, 0, 1, 0, 1, 1], fps = 30) => pattern[Math.floor(Math.max(0, t - t0) * fps) % pattern.length];

// ---------- light / glow ----------
// AE Glow: bright parts of src bloomed at three radii (downsampled for speed), added on top
function glow(src, { threshold = .65, radii = [12, 36, 96], intensity = 1.1, res = 4 } = {}) {
  const w = W / res, h = H / res, b = layer('_gl', g => { g.drawImage(src, 0, 0, w, h); const im = g.getImageData(0, 0, w, h), d = im.data; for (let i = 0; i < d.length; i += 4) { const l = (d[i] * .3 + d[i + 1] * .59 + d[i + 2] * .11) / 255, k = clamp((l - threshold) / (1 - threshold)); d[i] *= k; d[i + 1] *= k; d[i + 2] *= k; } g.putImageData(im, 0, 0); }, w, h);
  ctx.save(); ctx.globalCompositeOperation = 'lighter'; radii.forEach((r, i) => { ctx.globalAlpha = intensity / (i + 1.4); ctx.filter = `blur(${r / res}px)`; ctx.drawImage(b, 0, 0, W, H); }); ctx.restore();
}

// ---------- generative / Blender-ish ----------
// geometry-nodes-style scatter & grow: Poisson-ish points in a region, each pops in (eback) by its distance from an origin.
// item(x, y, s, i) draws one instance at scale s. p 0..1
function scatterGrow(p, item, { n = 160, x0 = 0, y0 = 0, w = W, h = H, origin = [W / 2, H / 2], seed = 1, minD = 60, spread = .7 } = {}) {
  const key = `${n},${x0},${y0},${w},${h},${seed},${minD}`; scatterGrow.c = scatterGrow.c || {};
  const pts = scatterGrow.c[key] || (scatterGrow.c[key] = (() => { const out = []; for (let k = 0; out.length < n && k < n * 30; k++) { const x = x0 + hash(seed + k * 1.31) * w, y = y0 + hash(seed + k * 2.77) * h; if (out.every(q => Math.hypot(q[0] - x, q[1] - y) > minD)) out.push([x, y]); } return out; })());
  const far = Math.max(...pts.map(q => Math.hypot(q[0] - origin[0], q[1] - origin[1]))) || 1;
  pts.forEach(([x, y], i) => { const d = Math.hypot(x - origin[0], y - origin[1]) / far * spread, s = eback(clamp((p - d) / (1 - spread))); if (s > 0) item(x, y, s, i); });
}
// Grease-Pencil-style tapered stroke: width follows sin(πu)^0.6, boils on twos
function taper(pts, { w = 14, color = '#1a1020', prog = 1, amp = 1.6, seed = 1 } = {}) {
  const p = partial(pts.map((q, i) => [q[0] + jit(seed + i * 1.3, amp), q[1] + jit(seed + i * 2.1 + 40, amp)]), prog); if (p.length < 2) return;
  ctx.save(); ctx.fillStyle = color; for (let i = 1; i < p.length; i++) { const u = i / (pts.length - 1), r = Math.max(.6, w / 2 * Math.pow(Math.sin(Math.PI * clamp(u)), .6)); ctx.beginPath(); ctx.arc(p[i][0], p[i][1], r, 0, 6.2832); ctx.fill();
    const a = p[i - 1], b = p[i], n = Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) / Math.max(1, r * .6)); for (let k = 1; k < n; k++) { ctx.beginPath(); ctx.arc(lerp(a[0], b[0], k / n), lerp(a[1], b[1], k / n), r, 0, 6.2832); ctx.fill(); } }
  ctx.restore();
}
// cloth drop: a banner/sheet (drawn by drawSheet into a layer) falls from the top with a travelling wave; settles with a spring
function clothDrop(drawSheet, p, { x = 0, y = 0, w = W, h = H, strips = 24, amp = 60, delay = .5 } = {}) {
  const L = layer('_cl', drawSheet), sh = h / strips;
  for (let i = 0; i < strips; i++) { const u = i / strips, q = clamp((p - u * delay) / (1 - delay)), fall = (1 - spring(q, 6, 10)) * -h * .9, wave = Math.sin(u * 9 - q * 14) * amp * (1 - q) * u;
    ctx.drawImage(L, x, y + i * sh, w, sh + 1, x + wave, y + i * sh + fall * (1 - u * .3), w, sh + 1); }
}

// ---------- stylised ----------
// watercolour blob (Tyler Hobbs): a polygon deformed recursively, stacked many times at low alpha → soft, darker-edged wash
function watercolor(cx, cy, r, color, { layers = 36, seed = 1, alpha = .045, depth = 5, spread = .9 } = {}) {
  const deform = (pts, d, s) => { if (!d) return pts; const out = []; pts.forEach((a, i) => { const b = pts[(i + 1) % pts.length], len = Math.hypot(b[0] - a[0], b[1] - a[1]), k = hash(s + i * 3.1), mx = (a[0] + b[0]) / 2 + (hash(s + i * 7.7) - .5) * len * spread, my = (a[1] + b[1]) / 2 + (k - .5) * len * spread; out.push(a, [mx, my]); }); return deform(out, d - 1, s + 11); };
  const base = deform(Array.from({ length: 10 }, (_, i) => [cx + Math.cos(i / 10 * 6.283) * r, cy + Math.sin(i / 10 * 6.283) * r]), 2, seed);
  ctx.save(); ctx.fillStyle = color; ctx.globalAlpha = alpha; for (let l = 0; l < layers; l++) { const poly = deform(base, depth - 2, seed + l * 97); ctx.beginPath(); poly.forEach((q, i) => i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1])); ctx.closePath(); ctx.fill(); } ctx.restore();
}
// pencil / crayon hatching from a layer's luminance: 1–3 hatch directions appear as it gets darker
function hatch(src, { gap = 9, w = 2, color = '#2a2433', paperColor = '#F4EFE4', angles = [.8, -.8, 0], res = 6, seed = 1 } = {}) {
  const sw = Math.round(W / res), sh = Math.round(H / res), d = layer('_ha', g => g.drawImage(src, 0, 0, sw, sh), sw, sh).getContext('2d').getImageData(0, 0, sw, sh).data, L = (x, y) => { const i = (clamp(y / res | 0, 0, sh - 1) * sw + clamp(x / res | 0, 0, sw - 1)) * 4; return (d[i] * .3 + d[i + 1] * .59 + d[i + 2] * .11) / 255; };
  ctx.fillStyle = paperColor; ctx.fillRect(0, 0, W, H); ctx.save(); ctx.strokeStyle = color; ctx.lineWidth = w; ctx.lineCap = 'round'; const R = Math.hypot(W, H) / 2, b = Math.floor(T * 12);
  angles.forEach((a, k) => { const th = .78 - k * .25, ca = Math.cos(a), sa = Math.sin(a); for (let v = -R; v < R; v += gap) { ctx.beginPath(); let on = false; for (let u = -R; u < R; u += 12) { const x = W / 2 + u * ca - v * sa + jit(seed + v + k, 1.2), y = H / 2 + u * sa + v * ca, dark = x > 0 && y > 0 && x < W && y < H && L(x, y) < th - hash(seed + v * .1 + u * .01 + b) * .08;
    if (dark && !on) { ctx.moveTo(x, y); on = true; } else if (dark) ctx.lineTo(x, y); else on = false; } ctx.globalAlpha = .55 + k * .1; ctx.stroke(); } });
  ctx.restore();
}
// ASCII render of a layer; ramp light → dark; decode = 0..1 scrambles glyphs until they lock (hash-timed)
function ascii(src, { cell = 18, ramp = ' .:-=+*#%@', color = '#9CFFB0', bg = '#05070A', decode = 1, seed = 1 } = {}) {
  const cw = Math.round(W / cell * 1.8), ch = Math.round(H / cell), d = layer('_as', g => g.drawImage(src, 0, 0, cw, ch), cw, ch).getContext('2d').getImageData(0, 0, cw, ch).data, f = Math.floor(T * 15);
  ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H); ctx.save(); ctx.fillStyle = color; ctx.font = MONO(cell); ctx.textBaseline = 'top'; const gw = W / cw;
  for (let y = 0; y < ch; y++) for (let x = 0; x < cw; x++) { const i = (y * cw + x) * 4, l = (d[i] * .3 + d[i + 1] * .59 + d[i + 2] * .11) / 255, locked = hash(seed + x * 7 + y * 13) < decode; let k = Math.round(l * (ramp.length - 1)); if (!locked) k = Math.floor(hash(seed + x + y * 99 + f) * ramp.length); if (ramp[k] !== ' ') ctx.fillText(ramp[k], x * gw, y * cell); }
  ctx.restore();
}
// Japanese OP title card type: vertical (tategaki) heavy serif, three-colour rule (#0a0a0a / #d6001c / #f2efe6), ink-stamp entrance
function tategaki(text, x, y, size, { color = '#f2efe6', t0 = 0, per = .05, font = null } = {}) {
  ctx.save(); ctx.font = font || `900 ${size}px "Hiragino Mincho ProN", "Noto Serif JP", "Songti SC", serif`; ctx.fillStyle = color; ctx.textAlign = 'center'; ctx.textBaseline = 'top';
  [...text].forEach((c, i) => { const q = seg(T, t0 + i * per, t0 + i * per + .1); if (q <= 0) return; const s = lerp(1.4, 1, eox(q)); ctx.save(); ctx.translate(x, y + i * size * 1.05 + size / 2); ctx.scale(s, s); ctx.fillText(c, 0, -size / 2); ctx.restore(); });
  ctx.restore();
}
// film damage: scratches on twos, dust, warm light leak that breathes (and swells on hits if given)
function filmDamage(t, { leak = .5, hits = [], seed = 1 } = {}) {
  const f = Math.floor(t * 12); ctx.save();
  for (let i = 0; i < 2; i++) { const x = hash(seed + f * 13 + i) * W; ctx.fillStyle = `rgba(255,255,255,${.12 + hash(f + i) * .2})`; ctx.fillRect(x, hash(f * 3 + i) * H * .3, 1.5, H * (.3 + hash(f * 5 + i) * .7)); }
  for (let i = 0; i < 10; i++) disc(hash(seed + f * 7 + i) * W, hash(seed + f * 11 + i) * H, 1 + hash(i + f) * 3, 'rgba(255,255,255,.45)');
  const a = leak * (.5 + .3 * Math.sin(t * 1.3) + .4 * (hits.length ? pulse(hits, t, 4) : 0)), g = ctx.createLinearGradient(0, 0, W * .5, 0); g.addColorStop(0, `rgba(255,122,42,${a})`); g.addColorStop(1, 'rgba(255,122,42,0)');
  ctx.globalCompositeOperation = 'lighter'; ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); ctx.restore();
}

// ---------- boot ----------
const loadImage = s => new Promise(r => { const i = new Image(); i.onload = () => r(i); i.onerror = () => r(null); i.src = s; });
async function loadImages(map) { const out = {}; await Promise.all(Object.entries(map).map(async ([k, src]) => { out[k] = await loadImage(src); })); return out; }
const loadFonts = (fonts = [SANS(700, 40), MONO(30), '40px HandEN', '40px HandZH', '40px HandJA', '40px HandKO']) => Promise.all(fonts.map(f => document.fonts.load(f)));
// startFilm: awaits setup, exposes window.READY / render / DUR for tools/render-fast.js, wires the preview UI (play, scrub, ?t=)
function startFilm({ dur, setup = async () => {}, render }) {
  const frame = t => { T = t; BOIL = Math.floor(t * 12); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.filter = 'none'; ctx.letterSpacing = '0px'; ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'left'; render(t); };
  window.DUR = dur; window.render = frame;
  window.READY = (async () => { await loadFonts(); await setup(); frame(0); return true; })();
  if (/render/.test(location.search)) { document.body.classList.add('render'); return; }
  const au = document.getElementById('au'), sc = document.getElementById('scrub'), tl = document.getElementById('tl'), pb = document.getElementById('play');
  if (!sc) return; sc.max = dur; let playing = false;
  const loop = () => { if (!playing) return; const t = au && au.src ? au.currentTime : (performance.now() - t0) / 1000; if (t >= dur) { playing = false; pb.textContent = '▶ play'; } frame(Math.min(t, dur - .001)); sc.value = t; tl.textContent = t.toFixed(2) + 's'; requestAnimationFrame(loop); };
  let t0 = 0; pb.onclick = () => { playing = !playing; pb.textContent = playing ? '❚❚ pause' : '▶ play'; if (playing) { const s = +sc.value >= dur - .05 ? 0 : +sc.value; t0 = performance.now() - s * 1000; if (au) { au.currentTime = s; au.play().catch(() => {}); } loop(); } else if (au) au.pause(); };
  sc.oninput = () => { frame(+sc.value); tl.textContent = (+sc.value).toFixed(2) + 's'; if (playing && au) au.currentTime = +sc.value; };
  window.READY.then(() => { const q = new URLSearchParams(location.search).get('t'); if (q) { sc.value = q; frame(+q); } });
}
