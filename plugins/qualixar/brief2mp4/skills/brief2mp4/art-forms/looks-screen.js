// brief2mp4 art forms: looks-screen.js, batch 5 (screens and cinema). MIT. Same rules as looks.js: every look is a pure
// function of time, no clock, all roughness from hash(); the pixel looks read and write a small ImageData each frame.
import { TAU, clamp, lerp, prog, easeOut, easeInOut, hash, frameOf, held, jit, circlePts, FONT } from './looks.js';
import { rgba, mix, speckle, vnoise } from './looks-painted.js';
import { path, polyFill, ell, star } from './looks-toon.js';

const mono = '13px "Courier New", Courier, monospace';
// a small ordered-dither threshold, 0..1, from the bits of x and y (an 8 by 8 Bayer matrix)
const bayer = (x, y) => { let b = 0; for (let bit = 2; bit >= 0; bit--) { const xb = (x >> bit) & 1, yb = (y >> bit) & 1; b = (b << 2) | ((xb ^ yb) << 1) | yb; } return (b + 0.5) / 64; };
const scanlines = (g, W, H, a = 0.22, step = 3) => { g.fillStyle = `rgba(0,0,0,${a})`; for (let y = 0; y < H; y += step) g.fillRect(0, y, W, 1); };
const vignette = (g, W, H, a = 0.5, r0 = 0.45) => { const v = g.createRadialGradient(W / 2, H / 2, H * r0, W / 2, H / 2, H * 1.05); v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, `rgba(0,0,0,${a})`); g.fillStyle = v; g.fillRect(0, 0, W, H); };
// a glowing stroke: a wide faint pass, then the bright line
const neon = (g, col, w, draw) => { g.save(); g.strokeStyle = col; g.lineCap = 'round'; g.lineJoin = 'round'; g.shadowColor = col; g.shadowBlur = w * 4; g.lineWidth = w; draw(); g.stroke(); g.shadowBlur = 0; g.lineWidth = w * 0.45; g.strokeStyle = '#fff'; g.globalAlpha = 0.7; draw(); g.stroke(); g.restore(); };

// film damage shared by the cinema looks: vertical scratches that last two frames, dust, hairs, flicker and grain, all keyed to the frame number
function filmDamage(g, W, H, f, o = {}) {
  const k = f >> 1; g.save();
  for (let i = 0; i < 3; i++) if (hash(k, i, 1) > 0.45) { g.fillStyle = `rgba(255,255,255,${0.18 + hash(k, i, 2) * 0.35})`; g.fillRect(hash(k, i, 3) * W, 0, 0.8 + hash(k, i, 4) * 1.4, H); }
  for (let i = 0; i < 14; i++) { g.fillStyle = hash(f, i, 5) > 0.5 ? 'rgba(10,10,10,.6)' : 'rgba(255,255,255,.5)'; g.beginPath(); g.arc(hash(f, i, 6) * W, hash(f, i, 7) * H, 0.8 + hash(f, i, 8) * 2.2, 0, TAU); g.fill(); }
  if (hash(k, 11, 9) > 0.8) { g.strokeStyle = 'rgba(10,10,10,.55)'; g.lineWidth = 1.1; const x = hash(k, 12, 1) * W, y = hash(k, 13, 1) * H; g.beginPath(); g.moveTo(x, y); g.bezierCurveTo(x + 30, y - 20, x + 40, y + 30, x + 80, y + 10); g.stroke(); }
  g.fillStyle = `rgba(${o.warm ? '255,230,190' : '255,255,255'},${(hash(f, 14, 2) - 0.5) * 0.1 + 0.02})`; g.fillRect(0, 0, W, H); g.restore();
  speckle(g, W, H, 60 + (f % 8), o.grain || 46, o.warm ? [255, 235, 200] : [255, 255, 255]);
}
const gray = (v) => `rgb(${v | 0},${v | 0},${v | 0})`;
const sepia = (k) => rgba(mix([24, 14, 6], [244, 228, 196], clamp(k)));

export const LOOKS = {
  /* ------------------------------------------------ screens and cinema ------------------------------------------------ */
  synthwave: { kind: '2d', fps: null, draw(g, t, W, H) {
    // an outrun night: a striped sun sinking behind wireframe mountains, and a neon grid that streams toward the horizon, in magenta and cyan on deep purple
    const hz = 300, sky = g.createLinearGradient(0, 0, 0, hz); sky.addColorStop(0, '#12062e'); sky.addColorStop(0.6, '#3a0a6a'); sky.addColorStop(0.92, '#c2188f'); sky.addColorStop(1, '#ff5f9e'); g.fillStyle = sky; g.fillRect(0, 0, W, hz);
    for (let i = 0; i < 60; i++) { g.fillStyle = `rgba(255,255,255,${0.3 + 0.6 * ((Math.sin(t * 2 + i) + 1) / 2)})`; g.fillRect(hash(i, 1) * W, hash(i, 2) * 200, 1.6, 1.6); }
    g.save(); g.beginPath(); g.rect(0, 0, W, hz); g.clip(); const sy = hz - 60, sun = g.createLinearGradient(0, sy - 140, 0, sy + 140); sun.addColorStop(0, '#fff25e'); sun.addColorStop(0.5, '#ff7a3a'); sun.addColorStop(1, '#ff2bd6'); g.fillStyle = sun; g.beginPath(); g.arc(480, sy, 140, 0, TAU); g.fill();
    g.fillStyle = '#c2188f'; const ph = (t * 0.3) % 1; for (let k = 0; k < 7; k++) g.fillRect(300, sy + 6 + (k + ph) * 17, 360, 2 + k * 2.3); g.restore();
    for (const [x0, x1, pk, hh] of [[0, 380, 130, 120], [600, 960, 840, 150]]) { const pts = [[x0, hz], [lerp(x0, x1, 0.2), hz - hh * 0.5], [pk, hz - hh], [lerp(x0, x1, 0.62), hz - hh * 0.4], [lerp(x0, x1, 0.8), hz - hh * 0.7], [x1, hz]]; polyFill(g, pts, '#1a0840'); neon(g, '#2ad4ff', 2, () => path(g, pts, false)); }
    const fl = g.createLinearGradient(0, hz, 0, H); fl.addColorStop(0, '#2a0a52'); fl.addColorStop(1, '#0d0320'); g.fillStyle = fl; g.fillRect(0, hz, W, H - hz);
    const glow = g.createLinearGradient(0, hz - 20, 0, hz + 70); glow.addColorStop(0, 'rgba(255,60,200,0)'); glow.addColorStop(0.3, 'rgba(255,60,200,.55)'); glow.addColorStop(1, 'rgba(255,60,200,0)'); g.fillStyle = glow; g.fillRect(0, hz - 20, W, 90);
    g.save(); g.beginPath(); g.rect(0, hz, W, H - hz); g.clip(); const ph2 = (t * 0.7) % 1;
    neon(g, '#ff2bd6', 2.4, () => { g.beginPath(); for (let i = -24; i <= 24; i++) { g.moveTo(480 + i * 16, hz); g.lineTo(480 + i * 190, H); } for (let k = 0; k < 16; k++) { const y = hz + (H - hz) * ((k + ph2) / 16) ** 2.3; g.moveTo(0, y); g.lineTo(W, y); } });
    g.restore(); neon(g, '#2ad4ff', 2.4, () => { g.beginPath(); g.moveTo(0, hz); g.lineTo(W, hz); });
  } },
  cyberpunk: { kind: '2d', fps: 12, draw(g, t, W, H) {
    // a rainy night street in purple and amber: towers hung with flickering neon signs, a wet road that mirrors them, and a figure under an umbrella
    const ts = held(t, 12), f = frameOf(t, 12), sc = new OffscreenCanvas(W, H), c = sc.getContext('2d'), sky = c.createLinearGradient(0, 0, 0, 380); sky.addColorStop(0, '#14061f'); sky.addColorStop(1, '#4a1a66'); c.fillStyle = sky; c.fillRect(0, 0, W, H);
    const tower = (x, w, top, col, win, seed) => { c.fillStyle = col; c.fillRect(x, top, w, 400 - top); for (let wy = top + 14; wy < 380; wy += 18) for (let wx = x + 8; wx < x + w - 8; wx += 14) if (hash(wx | 0, wy | 0, seed) > 0.55) { c.fillStyle = hash(wx | 0, wy | 0, seed + 1) > 0.7 ? '#a855f7' : win; c.fillRect(wx, wy, 6, 9); } };
    for (let x = 250; x < 720; x += 46) tower(x, 40, 150 + hash(x, 1) * 120, '#2a0f45', '#ffb347', 3);
    tower(120, 130, 90, '#150a24', '#ffb347', 5); tower(650, 160, 70, '#150a24', '#ffb347', 6); tower(0, 150, 20, '#0d0616', '#ffb347', 7); tower(810, 150, 40, '#0d0616', '#ffb347', 8);
    const sign = (i, x, y, w, h, col, kind) => { if ((f + i * 7) % 23 < 2) return; c.save(); c.strokeStyle = col; c.shadowColor = col; c.shadowBlur = 18; c.lineWidth = 5; c.lineJoin = 'round'; if (kind === 0) { c.strokeRect(x, y, w, h); for (let k = 1; k < 5; k++) { c.beginPath(); c.moveTo(x + 6, y + k * h / 5); c.lineTo(x + w - 6 - (k % 2) * 12, y + k * h / 5); c.stroke(); } } else if (kind === 1) { c.beginPath(); c.arc(x + w / 2, y + w / 2, w / 2, 0, TAU); c.stroke(); c.beginPath(); c.moveTo(x + w * 0.25, y + w / 2); c.lineTo(x + w * 0.75, y + w / 2); c.stroke(); } else { c.beginPath(); c.moveTo(x, y + h / 2); c.lineTo(x + w * 0.65, y + h / 2); c.lineTo(x + w * 0.65, y); c.lineTo(x + w, y + h / 2); c.lineTo(x + w * 0.65, y + h); c.lineTo(x + w * 0.65, y + h / 2); c.stroke(); } c.restore(); };
    sign(0, 40, 120, 46, 230, '#ff2e97', 0); sign(1, 170, 300, 120, 50, '#ffb02e', 2); sign(2, 880, 160, 44, 200, '#9b5cff', 0); sign(3, 690, 250, 80, 80, '#ff2e97', 1); sign(4, 300, 120, 90, 36, '#ffb02e', 2);
    g.drawImage(sc, 0, 0);
    g.fillStyle = '#0f0a18'; g.beginPath(); g.moveTo(0, 400); g.lineTo(W, 400); g.lineTo(W, H); g.lineTo(0, H); g.fill();
    g.save(); g.beginPath(); g.rect(0, 400, W, H - 400); g.clip(); g.globalAlpha = 0.42; g.filter = 'blur(3px)'; g.translate(0, 800); g.scale(1, -1); g.drawImage(sc, 0, 60, W, 340, 0, 60, W, 340); g.restore(); g.filter = 'none';
    const wet = g.createLinearGradient(0, 400, 0, H); wet.addColorStop(0, 'rgba(10,5,20,0)'); wet.addColorStop(1, 'rgba(10,5,20,.7)'); g.fillStyle = wet; g.fillRect(0, 400, W, H - 400);
    g.fillStyle = '#05030a'; g.beginPath(); g.ellipse(520, 470, 30, 8, 0, 0, TAU); g.fill(); g.beginPath(); g.moveTo(502, 470); g.lineTo(506, 410); g.lineTo(534, 410); g.lineTo(538, 470); g.fill(); ell(g, 520, 402, 14, 14, '#05030a'); g.beginPath(); g.ellipse(520, 372, 66, 34, 0, Math.PI, 0); g.fill(); g.strokeStyle = '#ffb347'; g.lineWidth = 2; g.beginPath(); g.ellipse(520, 372, 66, 34, 0, Math.PI * 1.1, Math.PI * 1.9); g.stroke(); g.lineWidth = 3; g.beginPath(); g.moveTo(520, 372); g.lineTo(520, 410); g.stroke();   // the umbrella and the figure
    for (let i = 0; i < 150; i++) { const x = (hash(i, 1) * W + ts * 60) % W, y = (hash(i, 2) * H + ts * 1100 * (0.7 + hash(i, 3) * 0.6)) % H; g.strokeStyle = `rgba(210,190,255,${0.15 + hash(i, 4) * 0.25})`; g.lineWidth = 1.2; g.beginPath(); g.moveTo(x, y); g.lineTo(x - 5, y + 26); g.stroke(); }
    for (let i = 0; i < 9; i++) { const r = ((ts * 1.6 + hash(i, 5)) % 1); g.strokeStyle = `rgba(255,200,140,${0.4 * (1 - r)})`; g.lineWidth = 1.4; g.beginPath(); g.ellipse(100 + hash(i, 6) * 760, 430 + hash(i, 7) * 100, r * 26, r * 7, 0, 0, TAU); g.stroke(); }
    const haze = g.createLinearGradient(0, 330, 0, 420); haze.addColorStop(0, 'rgba(160,70,210,0)'); haze.addColorStop(1, 'rgba(160,70,210,.28)'); g.fillStyle = haze; g.fillRect(0, 330, W, 90); vignette(g, W, H, 0.5);
  } },
  ascii: { kind: '2d', fps: 12, draw(g, t, W, H) {
    // a sunrise over a sea and a headland, drawn only from big monospaced characters picked by brightness from " .:-=+*#%@", in a colour per region: a violet-to-orange sky, a golden sun, a brown headland, a blue sea with glitter
    const ts = held(t, 12), cols = 96, rows = 34, RAMP = ' .:-=+*#%@'; g.fillStyle = '#080508'; g.fillRect(0, 0, W, H); g.font = '17px "Courier New", Courier, monospace'; g.textBaseline = 'top';
    const cw = g.measureText('M').width, sx = W / (cols * cw), rh = H / rows;
    const PAL = { sky: ['#5a4a9a', '#8a5aa8', '#c86aa0', '#ff8f6a', '#ffd9a0'], sun: ['#ffb347', '#ffc65a', '#ffd97a', '#fff0a8', '#ffffff'], land: ['#6a4a2a', '#8a5e34', '#a8743c', '#c88a48', '#e0a45a'], sea: ['#2a5fd0', '#3f86e0', '#6aa8ff', '#a8d0ff', '#e6f4ff'] };
    const cell = (u, v) => {
      const dx = (u - 0.64) * 1.78, dy = v - (0.4 - 0.015 * Math.sin(ts)), d = Math.hypot(dx, dy), ridge = 0.52 - 0.1 * vnoise(u * 6, 0, 3) - 0.05 * Math.abs(Math.sin(u * 7));
      if (v >= 0.64) { const k = v - 0.64; let L = 0.14 + 0.28 * Math.max(0, Math.sin(u * 40 + ts * 3.2 + k * 60)) ** 1.5; if (Math.abs(u - 0.64) < 0.05 + k * 0.45) L += 0.6 * Math.max(0, Math.sin(k * 110 + ts * 5)) ** 2 * (1 - k * 2.2); return [clamp(L), 'sea']; }
      if (d < 0.19) return [clamp(0.62 + 0.38 * (1 - d / 0.19)), 'sun'];
      if (u < 0.4 && v > ridge) return [0.46 + 0.3 * vnoise(u * 40, v * 40, 5), 'land'];
      return [clamp(0.04 + 0.3 * Math.max(0, 0.64 - v) ** 1.4 + 0.65 * Math.exp(-d * 5) + (v > 0.18 && v < 0.28 && Math.sin(u * 20 + ts * 0.5 + v * 30) > 0.8 ? 0.22 : 0)), 'sky'];
    };
    g.save(); g.scale(sx, 1);
    for (let r = 0; r < rows; r++) { const rowsTxt = {}; for (let c = 0; c < cols; c++) { const [L, cls] = cell(c / cols, r / rows), ch = RAMP[Math.floor(L * 9.99)]; if (ch === ' ') continue; const b = Math.min(4, Math.floor(L * 5)), key = cls + b; (rowsTxt[key] = rowsTxt[key] || { cls, b, s: Array(cols).fill(' ') }).s[c] = ch; } for (const k of Object.keys(rowsTxt)) { const o = rowsTxt[k]; g.fillStyle = PAL[o.cls][o.b]; g.fillText(o.s.join(''), 0, r * rh); } }
    for (let i = 0; i < 4; i++) { const bx = (ts * 7 + i * 24) % cols, by = 5 + i * 2 + Math.round(Math.sin(ts * 2 + i)); g.fillStyle = '#ffe9c0'; g.fillText(Math.floor(ts * 4 + i) % 2 ? 'v' : '^', bx * cw, by * rh); }
    g.restore(); scanlines(g, W, H, 0.08, 4);
  } },
  'dither-1bit': { kind: '2d', fps: 12, draw(g, t, W, H) {
    // two colours only, ink and paper: a gradient sky and a bouncing ball turned into pure dots by an ordered dither, inside a window with a striped title bar, like an early desktop computer
    const ts = held(t, 12), w = 480, h = 270, img = new ImageData(w, h), INKc = [17, 17, 17], PAP = [241, 239, 228], by = 152 - Math.abs(Math.sin(ts * 2.6)) * 62, bx = 240 + Math.sin(ts * 1.3) * 90, R = 52, Lg = [-0.5, -0.6, 0.62];
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      let L = y < 170 ? 0.12 + 0.8 * (y / 170) ** 1.3 : 0.3 + 0.35 * ((y - 170) / 100); const dx = (x - bx) / R, dy = (y - by) / R, r2 = dx * dx + dy * dy;
      if (y >= 170) { const sd = ((x - bx - 24) / (R * 1.5)) ** 2 + ((y - 214) / 12) ** 2; if (sd < 1) L *= 0.35; if (((x >> 5) + ((y - 170) >> 3)) % 2 === 0) L += 0.07; }
      if (r2 < 1) { const nz = Math.sqrt(1 - r2); L = clamp(0.12 + 0.95 * Math.max(0, dx * Lg[0] + dy * Lg[1] + nz * Lg[2])); }
      const c = L > bayer(x, y) ? PAP : INKc, i = (y * w + x) * 4; img.data[i] = c[0]; img.data[i + 1] = c[1]; img.data[i + 2] = c[2]; img.data[i + 3] = 255;
    }
    const sc = new OffscreenCanvas(w, h); sc.getContext('2d').putImageData(img, 0, 0); g.fillStyle = '#f1efe4'; g.fillRect(0, 0, W, H); g.save(); g.imageSmoothingEnabled = false; g.drawImage(sc, 0, 0, w, h, 0, 0, W, H); g.restore();
    g.fillStyle = '#f1efe4'; g.fillRect(0, 0, W, 34); g.fillStyle = '#111'; g.fillRect(0, 34, W, 3); for (let y = 8; y < 28; y += 4) g.fillRect(70, y, W - 140, 2); g.fillStyle = '#f1efe4'; g.fillRect(W / 2 - 80, 4, 160, 26); g.fillStyle = '#111'; g.font = `700 16px ${FONT}`; g.textAlign = 'center'; g.fillText('One bit', W / 2, 23); g.textAlign = 'left'; g.fillRect(12, 8, 18, 18); g.fillStyle = '#f1efe4'; g.fillRect(15, 11, 12, 12);
    g.strokeStyle = '#111'; g.lineWidth = 6; g.strokeRect(3, 3, W - 6, H - 6);
  } },
  'crt-terminal': { kind: '2d', fps: 24, draw(g, t, W, H) {
    // an amber phosphor terminal: text typed one character at a time, a block cursor, scanlines, glow, a slow rolling bar, and a screen that bulges at the middle
    const f = frameOf(t, 24), sc = new OffscreenCanvas(W, H), c = sc.getContext('2d'), AMB = '#ffb000', script = ['> route brief.md', 'art form: crt terminal', 'cadence: smooth, full frame rate', '', '> render --fps 24', 'frames 0001 .. 0096 ok', 'checking delivery ... pass', '', '> done'], typed = Math.floor(t < 0.25 ? t * 66 : 16 + (t - 0.25) * 36);   // the first prompt is typed by 0.25 s
    c.fillStyle = '#0a0600'; c.fillRect(0, 0, W, H); c.font = '700 26px "Courier New", Courier, monospace'; c.textBaseline = 'top'; c.shadowColor = AMB; c.shadowBlur = 14; c.fillStyle = AMB;
    c.fillText('BRIEF2MP4 TERMINAL', 70, 56); let left = typed, cur = null; for (let i = 0; i < script.length && !cur; i++) { const line = script[i], n = clamp(left, 0, line.length); c.fillText(line.slice(0, n), 70, 56 + (i + 2) * 38); if (left <= line.length) cur = [i, n]; left -= line.length + 2; }
    if (cur && Math.floor(t * 2) % 2 === 0) c.fillRect(70 + cur[1] * 15.6, 56 + (cur[0] + 2) * 38, 14, 26);   // a blinking block cursor at the end of what has been typed
    c.shadowBlur = 0; scanlines(c, W, H, 0.22, 3); const bar = ((t * 0.18) % 1.3) * (H + 120) - 120; const bg2 = c.createLinearGradient(0, bar, 0, bar + 120); bg2.addColorStop(0, 'rgba(255,176,0,0)'); bg2.addColorStop(0.5, 'rgba(255,176,0,.1)'); bg2.addColorStop(1, 'rgba(255,176,0,0)'); c.fillStyle = bg2; c.fillRect(0, bar, W, 120);
    g.fillStyle = '#050403'; g.fillRect(0, 0, W, H); const flick = 0.94 + 0.06 * hash(f, 3); g.globalAlpha = flick;
    for (let y = 0; y < H; y += 3) { const k = ((y - H / 2) / (H / 2)) ** 2, sw = W * (1 - 0.07 * k), dh = 3; g.drawImage(sc, 0, y, W, dh, (W - sw) / 2, y, sw, dh); }
    g.globalAlpha = 1; vignette(g, W, H, 0.7, 0.35); g.strokeStyle = 'rgba(255,255,255,.07)'; g.lineWidth = 4; g.beginPath(); g.ellipse(300, 90, 160, 28, -0.2, Math.PI * 1.1, Math.PI * 1.7); g.stroke();
    g.fillStyle = '#050403'; g.beginPath(); g.rect(0, 0, W, H); g.roundRect(14, 14, W - 28, H - 28, 46); g.fill('evenodd');
  } },
  'hologram-hud': { kind: '2d', fps: 24, draw(g, t, W, H) {
    // a cyan and blue wireframe globe turning in the dark, with a ring and a satellite, HUD readouts, corner brackets, a scan band, and a flicker with an occasional slipped strip
    const f = frameOf(t, 24), CY = '#58e6ff', BL = '#2a7bff', a = t * 0.6, tilt = 0.4, flick = hash(f, 1) > 0.92 ? 0.45 : 0.9 + 0.1 * hash(f, 2); g.fillStyle = '#030a18'; g.fillRect(0, 0, W, H); const bgl = g.createRadialGradient(480, 280, 20, 480, 280, 400); bgl.addColorStop(0, 'rgba(40,120,255,.28)'); bgl.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = bgl; g.fillRect(0, 0, W, H);
    g.save(); g.globalAlpha = flick; const proj = (la, lo, R) => { const X = Math.cos(la) * Math.sin(lo + a), Y = Math.sin(la), Z = Math.cos(la) * Math.cos(lo + a), Yp = Y * Math.cos(tilt) - Z * Math.sin(tilt), Zp = Y * Math.sin(tilt) + Z * Math.cos(tilt); return [480 + R * X, 280 - R * Yp, Zp]; };
    const wire = (col, lw, shift) => neon(g, col, lw, () => { g.beginPath(); for (let i = -4; i <= 4; i++) { let pen = false; for (let k = 0; k <= 48; k++) { const p = proj((i / 5) * 1.35, (k / 48) * TAU, 150); if (p[2] > -0.1) { pen ? g.lineTo(p[0] + shift, p[1]) : g.moveTo(p[0] + shift, p[1]); pen = true; } else pen = false; } } for (let j = 0; j < 12; j++) { let pen = false; for (let k = 0; k <= 36; k++) { const p = proj(-1.5 + (k / 36) * 3, (j / 12) * TAU, 150); if (p[2] > -0.05) { pen ? g.lineTo(p[0] + shift, p[1]) : g.moveTo(p[0] + shift, p[1]); pen = true; } else pen = false; } } });
    wire(BL, 1.6, 3); wire(CY, 1.8, 0);
    neon(g, CY, 1.6, () => { g.beginPath(); for (let k = 0; k <= 80; k++) { const th = (k / 80) * TAU, x = Math.cos(th) * 230, y = Math.sin(th) * 52; k ? g.lineTo(480 + x, 280 + y * 1 - x * 0.2) : g.moveTo(480 + x, 280 + y - x * 0.2); } }); const sat = a * 1.7; disc2(g, 480 + Math.cos(sat) * 230, 280 + Math.sin(sat) * 52 - Math.cos(sat) * 46, 6, CY);
    g.restore();
    g.strokeStyle = CY; g.fillStyle = CY; g.font = '700 13px "Courier New", monospace'; g.lineWidth = 1.6;
    for (const [x, y, sx, sy] of [[28, 28, 1, 1], [W - 28, 28, -1, 1], [28, H - 28, 1, -1], [W - 28, H - 28, -1, -1]]) { g.beginPath(); g.moveTo(x, y + sy * 36); g.lineTo(x, y); g.lineTo(x + sx * 36, y); g.stroke(); }
    ['PWR', 'SYNC', 'LINK'].forEach((l, i) => { const v = 0.35 + 0.6 * hash(Math.floor(f / 6), i, 4); g.fillText(l, 50, 120 + i * 34); g.strokeRect(100, 109 + i * 34, 120, 12); g.fillRect(100, 109 + i * 34, 120 * v, 12); g.fillText(String(Math.round(v * 100)).padStart(3, '0'), 232, 120 + i * 34); });
    for (let i = 0; i < 9; i++) { const v = 0.2 + 0.8 * hash(Math.floor(f / 5), i, 6); g.fillRect(730 + i * 17, 230 - 90 * v, 10, 90 * v); }
    g.beginPath(); g.arc(800, 360, 54, 0, TAU); g.stroke(); for (let i = 0; i < 24; i++) { const an = (i / 24) * TAU + t * 0.8; g.beginPath(); g.moveTo(800 + Math.cos(an) * 54, 360 + Math.sin(an) * 54); g.lineTo(800 + Math.cos(an) * (i % 3 ? 62 : 70), 360 + Math.sin(an) * (i % 3 ? 62 : 70)); g.stroke(); }
    g.fillText('SCAN ' + String(Math.floor((t * 22) % 100)).padStart(3, '0') + '%', 50, 470); g.fillText('ALT 4' + String(120 + Math.floor(hash(Math.floor(f / 8), 9) * 80)), 50, 490);
    const bandY = (t * 150) % (H + 80) - 40, band = g.createLinearGradient(0, bandY - 40, 0, bandY + 40); band.addColorStop(0, 'rgba(88,230,255,0)'); band.addColorStop(0.5, 'rgba(88,230,255,.22)'); band.addColorStop(1, 'rgba(88,230,255,0)'); g.fillStyle = band; g.fillRect(0, bandY - 40, W, 80);
    scanlines(g, W, H, 0.18, 3); if (hash(f, 11) > 0.9) { const y = hash(f, 12) * H; g.drawImage(g.canvas, 0, y, W, 24, 8, y, W, 24); }
  } },
  thermal: { kind: '2d', fps: 12, draw(g, t, W, H) {
    // a thermal-camera view: a heat field mapped through black, purple, red, orange, yellow and white, with a hot head and hands, a warm mug, a cold window, and a crosshair and a colour scale
    const ts = held(t, 12), w = 240, h = 135, c = new OffscreenCanvas(w, h).getContext('2d'), sway = Math.sin(ts * 1.2) * 2, pulse = 0.95 + 0.05 * Math.sin(ts * 3);
    c.fillStyle = gray(34); c.fillRect(0, 0, w, h); c.fillStyle = gray(58); c.fillRect(0, 100, w, 35); c.filter = 'blur(2px)'; c.fillStyle = gray(18); c.fillRect(186, 28, 44, 56);
    const blob = (x, y, rx, ry, v) => { c.fillStyle = gray(v * pulse); c.beginPath(); c.ellipse(x, y, rx, ry, 0, 0, TAU); c.fill(); }, limb = (x0, y0, x1, y1, lw, v) => { c.strokeStyle = gray(v * pulse); c.lineWidth = lw; c.lineCap = 'round'; c.beginPath(); c.moveTo(x0, y0); c.lineTo(x1, y1); c.stroke(); };
    blob(118, 128, 34, 5, 80); limb(108 + sway, 88, 106, 124, 12, 140); limb(130 + sway, 88, 132, 124, 12, 140); blob(120 + sway, 64, 21, 28, 190); limb(102 + sway, 48, 88, 78, 9, 165); limb(138 + sway, 48, 156, 82, 9, 165); blob(120 + sway, 46, 5, 8, 205);
    blob(120 + sway, 33, 11, 13, 238); blob(88, 80, 6, 6, 225); blob(157, 85, 6, 6, 225); blob(160, 82, 5, 5, 255); blob(30, 26, 9, 9, 255); blob(30, 26, 20, 20, 120);
    const d = c.getImageData(0, 0, w, h), out = new ImageData(w, h), STOPS = [[0, [0, 0, 8]], [0.18, [40, 0, 90]], [0.4, [170, 20, 60]], [0.62, [240, 90, 20]], [0.82, [255, 200, 40]], [1, [255, 255, 230]]];
    const ramp = (v) => { for (let i = 1; i < STOPS.length; i++) if (v <= STOPS[i][0]) { const a = STOPS[i - 1], b = STOPS[i], k = (v - a[0]) / (b[0] - a[0]); return mix(a[1], b[1], k); } return STOPS[STOPS.length - 1][1]; };
    const lut = Array.from({ length: 256 }, (_, i) => ramp(i / 255)); for (let i = 0; i < w * h; i++) { const col = lut[d.data[i * 4] | 0], n = (hash(i, ts * 12 | 0) - 0.5) * 8; out.data[i * 4] = col[0] + n; out.data[i * 4 + 1] = col[1] + n; out.data[i * 4 + 2] = col[2] + n; out.data[i * 4 + 3] = 255; }
    const fc = new OffscreenCanvas(w, h); fc.getContext('2d').putImageData(out, 0, 0); g.imageSmoothingEnabled = true; g.drawImage(fc, 0, 0, W, H);
    g.strokeStyle = '#fff'; g.fillStyle = '#fff'; g.lineWidth = 2; g.font = '700 16px "Courier New", monospace'; const hx = (120 + sway) * 4, hy = 33 * 4; g.beginPath(); g.arc(hx, hy, 34, 0, TAU); g.moveTo(hx - 50, hy); g.lineTo(hx - 20, hy); g.moveTo(hx + 20, hy); g.lineTo(hx + 50, hy); g.moveTo(hx, hy - 50); g.lineTo(hx, hy - 20); g.moveTo(hx, hy + 20); g.lineTo(hx, hy + 50); g.stroke(); g.fillText('36.' + (4 + Math.floor((Math.sin(ts * 2) + 1) * 2)) + ' C', hx + 40, hy - 36);
    const sc = g.createLinearGradient(0, 100, 0, 440); STOPS.slice().reverse().forEach(([k, col]) => sc.addColorStop(1 - k, rgba(col))); g.fillStyle = sc; g.fillRect(900, 100, 22, 340); g.strokeRect(900, 100, 22, 340); g.fillStyle = '#fff'; g.fillText('40', 928, 112); g.fillText('20', 928, 276); g.fillText('0', 928, 440);
    for (const [x, y, sx, sy] of [[28, 28, 1, 1], [W - 28, 28, -1, 1], [28, H - 28, 1, -1], [W - 28, H - 28, -1, -1]]) { g.beginPath(); g.moveTo(x, y + sy * 30); g.lineTo(x, y); g.lineTo(x + sx * 30, y); g.stroke(); }
    g.fillText('THERMAL  ' + String(Math.floor(t * 10) % 1000).padStart(3, '0'), 44, 60); scanlines(g, W, H, 0.1, 4);
  } },
  'silent-film': { kind: '2d', fps: 18, draw(g, t, W, H) {
    // black and white at 18 frames a second: an iris opens on a man in a bowler hat walking past a street lamp, the gate wanders, the light flickers and the print is scratched; then an iris closes and an intertitle card appears
    const f = frameOf(t, 18), ts = f / 18; g.fillStyle = '#000'; g.fillRect(0, 0, W, H);
    if (ts < 2.75) {
      const R = 660 * easeOut(prog(ts, 0, 0.6)) * (1 - easeInOut(prog(ts, 2.1, 0.6))); g.save(); g.translate(jit(f, 1, 2.6), jit(f, 2, 2) + (hash(f >> 2, 3) > 0.97 ? 7 : 0));
      g.beginPath(); g.arc(480, 270, Math.max(0, R), 0, TAU); g.clip(); const sky = g.createLinearGradient(0, 0, 0, 400); sky.addColorStop(0, gray(215)); sky.addColorStop(1, gray(150)); g.fillStyle = sky; g.fillRect(0, 0, W, H);
      for (let i = 0; i < 12; i++) { const x = i * 90 - 20, hh = 120 + hash(i, 1) * 160; g.fillStyle = gray(110); g.fillRect(x, 400 - hh, 76, hh); } for (let i = 0; i < 9; i++) { const x = i * 120 + 10, hh = 170 + hash(i, 2) * 120; g.fillStyle = gray(52); g.fillRect(x, 410 - hh, 100, hh); for (let wy = 410 - hh + 14; wy < 390; wy += 26) for (let wx = x + 12; wx < x + 88; wx += 24) { g.fillStyle = hash(wx | 0, wy | 0, 3) > 0.5 ? gray(225) : gray(30); g.fillRect(wx, wy, 11, 15); } }
      g.fillStyle = gray(38); g.fillRect(0, 400, W, 140); g.fillStyle = gray(70); for (let i = 0; i < 14; i++) g.fillRect(i * 80 - ((ts * 60) % 80), 470, 46, 6);
      g.fillStyle = '#111'; g.fillRect(768, 150, 8, 260); ell(g, 772, 144, 18, 14, gray(250)); const wx = lerp(-40, 1000, ts / 2.6), wk = Math.sin(f * 0.95), by = 350 - Math.abs(wk) * 6;
      g.strokeStyle = '#050505'; g.lineWidth = 15; g.lineCap = 'round'; for (const d of [-1, 1]) { g.beginPath(); g.moveTo(wx + d * 6, by + 26); g.lineTo(wx + d * 6 + d * wk * 24, by + 100); g.stroke(); } g.fillStyle = '#050505'; g.beginPath(); g.moveTo(wx - 24, by + 34); g.lineTo(wx + 24, by + 34); g.lineTo(wx + 20, by - 40); g.lineTo(wx - 20, by - 40); g.fill();
      g.lineWidth = 10; g.beginPath(); g.moveTo(wx + 18, by - 30); g.lineTo(wx + 40 - wk * 8, by + 10); g.stroke(); g.lineWidth = 4; g.beginPath(); g.moveTo(wx + 40 - wk * 8, by + 10); g.lineTo(wx + 56, by + 100); g.stroke(); ell(g, wx, by - 62, 17, 19, gray(235)); ell(g, wx, by - 82, 22, 6, '#050505'); g.fillRect(wx - 14, by - 100, 28, 20); g.fillStyle = '#111'; g.fillRect(wx - 7, by - 52, 14, 3);
      g.restore();
    } else {
      g.fillStyle = '#0a0a0a'; g.fillRect(0, 0, W, H); g.strokeStyle = gray(235); g.lineWidth = 6; g.strokeRect(46, 46, W - 92, H - 92); g.lineWidth = 2; g.strokeRect(64, 64, W - 128, H - 128); for (const [x, y] of [[80, 80], [W - 80, 80], [80, H - 80], [W - 80, H - 80]]) { g.beginPath(); g.arc(x, y, 14, 0, TAU); g.stroke(); }
      g.fillStyle = gray(240); g.textAlign = 'center'; g.font = '700 58px Georgia, "Times New Roman", serif'; g.fillText('AND SO, ONE FINE', W / 2, 240); g.fillText('MORNING . . .', W / 2, 316); g.fillRect(380, 350, 200, 3); g.textAlign = 'left';
    }
    vignette(g, W, H, 0.55, 0.4); filmDamage(g, W, H, f, { grain: 52 }); g.fillStyle = `rgba(0,0,0,${0.08 * hash(f, 20)})`; g.fillRect(0, 0, W, H);
  } },
  newsreel: { kind: '2d', fps: 18, draw(g, t, W, H) {
    // sepia 1940s newsreel footage: a steam train racing across the frame past telegraph poles, a slanted headline banner, and a damaged print: scratches, hairs, dust, a burn flash and a jolt of the frame
    const f = frameOf(t, 18), ts = f / 18; g.save(); g.translate(jit(f, 1, 2), jit(f, 2, 1.5) + (hash(f >> 1, 3) > 0.94 ? 9 : 0));
    const sky = g.createLinearGradient(0, 0, 0, 380); sky.addColorStop(0, sepia(0.86)); sky.addColorStop(1, sepia(0.6)); g.fillStyle = sky; g.fillRect(-20, -20, W + 40, 420);
    g.fillStyle = sepia(0.4); g.beginPath(); g.moveTo(-20, 360); for (let x = 0; x <= W + 20; x += 20) g.lineTo(x, 330 - 40 * vnoise((x + ts * 40) / 120, 0, 4)); g.lineTo(W + 20, 400); g.lineTo(-20, 400); g.fill();
    g.fillStyle = sepia(0.2); g.fillRect(-20, 392, W + 40, 160); g.fillStyle = sepia(0.12); for (let i = 0; i < 14; i++) g.fillRect(((i * 90 - ts * 420) % (W + 90) + W + 90) % (W + 90) - 40, 478, 44, 8);
    g.strokeStyle = sepia(0.08); g.lineWidth = 6; for (let i = 0; i < 5; i++) { const x = ((i * 230 - ts * 640) % (W + 230) + W + 230) % (W + 230) - 60; g.beginPath(); g.moveTo(x, 190); g.lineTo(x, 400); g.moveTo(x - 36, 214); g.lineTo(x + 36, 214); g.stroke(); }
    const ex = 380, ey = 360; g.fillStyle = sepia(0.07); g.fillRect(ex - 160, ey - 76, 250, 76); g.beginPath(); g.arc(ex - 160, ey - 38, 38, Math.PI / 2, Math.PI * 1.5); g.fill(); g.fillRect(ex - 170, ey - 120, 34, 52); g.fillRect(ex + 24, ey - 140, 104, 140); g.fillRect(ex + 10, ey - 150, 132, 14); g.fillStyle = sepia(0.5); g.fillRect(ex + 46, ey - 112, 56, 40);
    for (const wxp of [-120, -50, 20, 90]) { g.fillStyle = sepia(0.05); g.beginPath(); g.arc(ex + wxp, ey + 6, 30, 0, TAU); g.fill(); g.strokeStyle = sepia(0.6); g.lineWidth = 3; for (let sp = 0; sp < 4; sp++) { const a = f * 0.5 + (sp * Math.PI) / 4; g.beginPath(); g.moveTo(ex + wxp + Math.cos(a) * 26, ey + 6 + Math.sin(a) * 26); g.lineTo(ex + wxp - Math.cos(a) * 26, ey + 6 - Math.sin(a) * 26); g.stroke(); } }
    for (let i = 0; i < 7; i++) { const k = (ts * 1.2 + i / 7) % 1, x = ex - 150 - k * 320, y = ey - 150 - k * 150; g.fillStyle = `rgba(${240 - k * 40},${230 - k * 40},${210 - k * 40},${0.7 * (1 - k)})`; g.beginPath(); g.arc(x, y, 18 + k * 44, 0, TAU); g.fill(); }
    g.restore(); g.save(); g.translate(W / 2, 450); g.rotate(-0.07); g.fillStyle = sepia(0.06); g.fillRect(-380, -34, 760, 70); g.fillStyle = sepia(0.92); g.fillRect(-380, 36, 540, 26); g.fillStyle = sepia(0.95); g.font = '400 50px Impact, "Arial Black", sans-serif'; g.textAlign = 'center'; g.fillText('THE WORLD IN MOTION', 0, 18); g.fillStyle = sepia(0.08); g.font = '700 17px "Arial Narrow", Arial, sans-serif'; g.fillText('NEWS OF THE WEEK', -110, 56); g.restore();
    if (hash(f >> 1, 9) > 0.9) { const bx = hash(f, 10) * W, bg2 = g.createRadialGradient(bx, 200, 10, bx, 200, 300); bg2.addColorStop(0, 'rgba(255,240,200,.45)'); bg2.addColorStop(1, 'rgba(255,240,200,0)'); g.fillStyle = bg2; g.fillRect(0, 0, W, H); }
    vignette(g, W, H, 0.65, 0.35); filmDamage(g, W, H, f, { warm: true, grain: 56 });
  } },
  'film-noir': { kind: '2d', fps: null, draw(g, t, W, H) {
    // high-contrast black and white: a wall striped with light through venetian blinds, a man in a fedora and trench coat under a street lamp, rain slanting through the lamp's cone, and a wet pavement
    g.fillStyle = '#030303'; g.fillRect(0, 0, W, H); const wall = g.createLinearGradient(0, 0, W, 0); wall.addColorStop(0, gray(60)); wall.addColorStop(1, gray(14)); g.fillStyle = wall; g.fillRect(0, 0, W, 390);
    g.fillStyle = gray(22); g.fillRect(0, 390, W, 150); const ref = g.createLinearGradient(760, 390, 760, H); ref.addColorStop(0, 'rgba(255,255,255,.35)'); ref.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = ref; g.fillRect(730, 390, 60, 150);
    const lamp = g.createLinearGradient(0, 100, 0, 400); lamp.addColorStop(0, 'rgba(255,255,255,.7)'); lamp.addColorStop(1, 'rgba(255,255,255,.1)'); g.fillStyle = lamp; g.beginPath(); g.moveTo(752, 110); g.lineTo(792, 110); g.lineTo(940, 410); g.lineTo(610, 410); g.closePath(); g.fill();
    g.fillStyle = gray(200); g.fillRect(768, 118, 8, 296); g.fillStyle = '#050505'; g.beginPath(); g.moveTo(742, 112); g.lineTo(800, 112); g.lineTo(784, 94); g.lineTo(758, 94); g.fill(); ell(g, 772, 120, 14, 8, gray(255));
    const wg = g.createRadialGradient(772, 170, 20, 772, 170, 300); wg.addColorStop(0, 'rgba(255,255,255,.5)'); wg.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = wg; g.fillRect(480, 0, 480, 410);
    g.save(); g.translate(640, 410); g.scale(1.3, 1.3); const K = '#040404', rim = gray(215), blk = (pts) => { path(g, pts); g.fillStyle = K; g.fill(); }, edge = (pts, w = 2, col = rim) => { path(g, pts, false); g.strokeStyle = col; g.lineWidth = w; g.stroke(); };
    blk([[-22, -84], [-4, -84], [-6, 0], [-28, 0]]); blk([[4, -84], [22, -84], [28, 0], [6, 0]]); ell(g, -20, 0, 16, 5, K); ell(g, 20, 0, 16, 5, K);   // trousers and shoes
    g.strokeStyle = K; g.lineCap = 'round'; g.lineWidth = 17; path(g, [[-48, -212], [-62, -158], [-58, -108]], false); g.stroke(); ell(g, -58, -100, 9, 9, K);   // the hanging arm
    blk([[-50, -214], [-36, -232], [36, -232], [50, -214], [58, -130], [64, -78], [0, -70], [-64, -78], [-58, -130]]);   // the trench coat
    blk([[-36, -232], [-24, -256], [-6, -230]]); blk([[36, -232], [24, -256], [6, -230]]);   // the collar, turned up
    g.fillStyle = gray(70); g.fillRect(-58, -136, 116, 11); g.fillStyle = gray(160); g.fillRect(-7, -138, 14, 15); g.strokeStyle = gray(70); g.lineWidth = 2; path(g, [[-34, -232], [0, -176], [34, -232]], false); g.stroke(); path(g, [[0, -176], [0, -138]], false); g.stroke(); path(g, [[-56, -126], [-62, -78]], false); g.stroke();   // belt, buckle, lapels
    g.strokeStyle = K; g.lineWidth = 15; path(g, [[44, -212], [68, -176], [28, -246]], false); g.stroke(); ell(g, 25, -248, 8, 8, K);   // the arm raised to the mouth
    ell(g, 0, -252, 16, 21, gray(46)); ell(g, 7, -252, 6, 18, gray(120));   // the face, mostly in shadow, with a sliver of light on the cheek
    blk([[-27, -270], [-24, -298], [-6, -304], [0, -297], [6, -304], [24, -298], [27, -270]]); g.fillStyle = gray(80); g.fillRect(-26, -280, 52, 7); ell(g, 0, -270, 53, 9, K);   // a fedora: pinched crown, band and a wide brim
    g.strokeStyle = gray(235); g.lineWidth = 2.4; path(g, [[4, -244], [19, -247]], false); g.stroke(); ell(g, 21, -247, 2.6, 2.6, '#fff');   // the cigarette and its ember
    edge([[50, -214], [58, -130], [64, -78]]); edge([[36, -232], [24, -256]]); edge([[53, -270], [40, -268]], 2); edge([[24, -298], [27, -272]], 1.6);
    g.restore();
    g.strokeStyle = 'rgba(255,255,255,.5)'; g.lineWidth = 2; g.beginPath(); for (let i = 0; i < 16; i++) g.lineTo(669 + Math.sin(t * 2 + i * 0.55) * (3 + i * 1.5), 90 - i * 11); g.stroke();   // a curl of smoke
    g.save(); g.globalCompositeOperation = 'lighter'; const drift = (t * 7) % 52; g.fillStyle = 'rgba(235,235,235,.3)'; for (let i = -2; i < 14; i++) { const y = i * 52 + drift; g.beginPath(); g.moveTo(0, y); g.lineTo(540, y + 96); g.lineTo(540, y + 126); g.lineTo(0, y + 30); g.closePath(); g.fill(); } g.restore();
    for (let i = 0; i < 220; i++) { const x = (hash(i, 1) * W + t * 40) % W, y = (hash(i, 2) * H + t * 1000 * (0.7 + hash(i, 3) * 0.5)) % H, inCone = y > 110 && Math.abs(x - 772) < (y - 110) * 0.55 + 20; g.strokeStyle = `rgba(255,255,255,${inCone ? 0.7 : 0.14})`; g.lineWidth = 1.2; g.beginPath(); g.moveTo(x, y); g.lineTo(x - 6, y + 28); g.stroke(); }
    for (let i = 0; i < 6; i++) { const r = ((t * 1.4 + hash(i, 5)) % 1); g.strokeStyle = `rgba(255,255,255,${0.5 * (1 - r)})`; g.lineWidth = 1.4; g.beginPath(); g.ellipse(680 + hash(i, 6) * 220, 430 + hash(i, 7) * 80, r * 30, r * 7, 0, 0, TAU); g.stroke(); }
    vignette(g, W, H, 0.7, 0.4); speckle(g, W, H, 77, 30, [255, 255, 255]);
  } },
  'archive-documentary': { kind: '2d', fps: null, draw(g, t, W, H) {
    // a slow pan and zoom over three still photographs laid on a desk, each with a white border and a shadow, then a lower-third caption and date that slide in for each picture, over film grain
    const KF = [[0, 300, 260, 1.2], [2.6, 330, 250, 1.7], [4.6, 860, 210, 1.5], [7, 870, 200, 1.9], [9, 1380, 320, 1.4]], seg = Math.max(0, KF.findIndex((k, i) => i < KF.length - 1 && t < KF[i + 1][0])), a = KF[seg], b = KF[Math.min(seg + 1, KF.length - 1)], k = t >= KF[KF.length - 1][0] ? 1 : easeInOut(clamp((t - a[0]) / (b[0] - a[0])));
    const cx = lerp(a[1], b[1], k), cy = lerp(a[2], b[2], k), sc = lerp(a[3], b[3], k); g.fillStyle = '#17120e'; g.fillRect(0, 0, W, H);
    g.save(); g.translate(W / 2, H / 2); g.scale(sc, sc); g.translate(-cx, -cy);
    for (let i = 0; i < 80; i++) { g.fillStyle = `rgba(255,240,210,${0.02 + hash(i, 1) * 0.03})`; g.fillRect(hash(i, 2) * 1800 - 200, hash(i, 3) * 800 - 100, 60 + hash(i, 4) * 200, 2); }
    const photo = (x, y, w, h, a2, kind) => {
      g.save(); g.translate(x, y); g.rotate(a2); g.shadowColor = 'rgba(0,0,0,.6)'; g.shadowBlur = 28; g.shadowOffsetX = 8; g.shadowOffsetY = 12; g.fillStyle = '#efe6d2'; g.fillRect(-w / 2 - 14, -h / 2 - 14, w + 28, h + 28); g.shadowColor = 'transparent';
      g.save(); g.beginPath(); g.rect(-w / 2, -h / 2, w, h); g.clip(); const sky = g.createLinearGradient(0, -h / 2, 0, h / 2); sky.addColorStop(0, sepia(0.88)); sky.addColorStop(1, sepia(0.55)); g.fillStyle = sky; g.fillRect(-w / 2, -h / 2, w, h);
      if (kind === 0) { g.fillStyle = sepia(0.32); g.fillRect(-w / 2, 20, w, h / 2); g.fillStyle = sepia(0.08); g.fillRect(-120, -10, 220, 40); g.fillRect(-60, -60, 14, 60); g.fillRect(10, -90, 10, 90); g.beginPath(); g.moveTo(-130, 30); g.lineTo(120, 30); g.lineTo(90, 52); g.lineTo(-100, 52); g.fill(); for (let i = 0; i < 4; i++) { g.fillRect(-w / 2 + 30 + i * 28, -20, 5, 60); } }
      else if (kind === 1) { for (let i = 0; i < 6; i++) { g.fillStyle = sepia(0.12 + i * 0.05); const hx = -w / 2 + i * (w / 6), hh = 90 + hash(i, 5) * 50; g.fillRect(hx, 40 - hh, w / 6 - 6, hh + 70); g.beginPath(); g.moveTo(hx - 4, 40 - hh); g.lineTo(hx + w / 12 - 3, 10 - hh); g.lineTo(hx + w / 6 - 2, 40 - hh); g.fill(); } g.fillStyle = sepia(0.3); g.beginPath(); g.moveTo(-w / 2, h / 2); g.lineTo(-30, 60); g.lineTo(30, 60); g.lineTo(w / 2, h / 2); g.fill(); }
      else { g.fillStyle = sepia(0.3); g.beginPath(); g.moveTo(-w / 2, 70); g.lineTo(-90, -80); g.lineTo(-30, -10); g.lineTo(60, -110); g.lineTo(150, 20); g.lineTo(w / 2, 70); g.lineTo(w / 2, h / 2); g.lineTo(-w / 2, h / 2); g.fill(); g.fillStyle = sepia(0.9); g.beginPath(); g.moveTo(40, -80); g.lineTo(60, -110); g.lineTo(82, -76); g.lineTo(60, -86); g.fill(); }
      const v = g.createRadialGradient(0, 0, h * 0.3, 0, 0, w * 0.62); v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(30,18,6,.55)'); g.fillStyle = v; g.fillRect(-w / 2, -h / 2, w, h); g.restore(); g.restore();
    };
    photo(300, 260, 440, 300, -0.02, 0); photo(860, 200, 400, 280, 0.025, 1); photo(1380, 320, 420, 300, -0.015, 2); g.restore();
    const idx = t < 3.3 ? 0 : t < 7.3 ? 1 : 2, st = [0, 3.3, 7.3][idx], slide = easeOut(prog(t, st, 0.5)), caps = [['HARBOUR AT DAWN', 'MARCH 1931'], ['MARKET STREET', 'JUNE 1934'], ['THE MOUNTAIN ROAD', 'OCTOBER 1937']][idx];
    g.save(); g.translate(lerp(-520, 0, slide), 0); g.fillStyle = 'rgba(12,10,8,.82)'; g.fillRect(40, 418, 470, 82); g.fillStyle = '#d6a21f'; g.fillRect(40, 418, 6, 82); g.fillStyle = '#f4ead4'; g.font = `700 30px ${FONT}`; g.fillText(caps[0], 62, 456); g.fillStyle = '#c9b88e'; g.font = `400 20px ${FONT}`; g.fillText(caps[1], 62, 486); g.restore();
    vignette(g, W, H, 0.55, 0.4); speckle(g, W, H, 70 + (Math.floor(t * 12) % 8), 34, [255, 245, 220]);
  } },
};
function disc2(g, x, y, r, col) { g.fillStyle = col; g.shadowColor = col; g.shadowBlur = 12; g.beginPath(); g.arc(x, y, r, 0, TAU); g.fill(); g.shadowBlur = 0; }
export const IDS = Object.keys(LOOKS);
