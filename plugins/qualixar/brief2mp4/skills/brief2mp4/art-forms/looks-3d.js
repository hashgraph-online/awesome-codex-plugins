// brief2mp4 art forms: looks-3d.js, batch 4 (3D looks). MIT. These demos are 2D: they fake the 3D with gradients, rotation
// maths and a painter's sort, so that they render with no WebGL. Each form's `build` recipe gives the real Three.js route.
// Same rules as looks.js: a pure function of time, no clock, all roughness from hash().
import { TAU, clamp, lerp, prog, easeOut, easeInOut, hash, circlePts } from './looks.js';
import { rgba, mix, poly, speckle, vnoise } from './looks-painted.js';
import { lines, halftone } from './looks-folk.js';
import { path, polyFill, ell, star, shadeHex } from './looks-toon.js';

const norm3 = (v) => { const l = Math.hypot(...v); return v.map((x) => x / l); };
const dot3 = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
// turn a point about the vertical axis by a, then tip it forward by tilt: x right, y up, z toward the viewer
function turn(p, a, tilt) { const c = Math.cos(a), s = Math.sin(a), x = p[0] * c + p[2] * s, z = -p[0] * s + p[2] * c, ct = Math.cos(tilt), st = Math.sin(tilt); return [x, p[1] * ct - z * st, p[1] * st + z * ct]; }
// a soft ellipsoid lit from the upper left: a warm glow where the light bleeds through its skin, a cool rim light on the right, a soft highlight
function ball(g, x, y, rx, ry, base, o = {}) {
  g.save(); g.translate(x, y); g.scale(1, ry / rx);
  const gr = g.createRadialGradient(-rx * 0.36, -rx * 0.4, rx * 0.06, 0, 0, rx * 1.03); gr.addColorStop(0, rgba(mix(base, [255, 255, 255], 0.42))); gr.addColorStop(0.5, rgba(base)); gr.addColorStop(0.86, rgba(mix(base, [50, 12, 22], 0.35))); gr.addColorStop(1, rgba(mix(base, [24, 6, 12], 0.55)));
  g.fillStyle = gr; g.beginPath(); g.arc(0, 0, rx, 0, TAU); g.fill();
  if (o.warm !== false) { g.save(); g.beginPath(); g.arc(0, 0, rx, 0, TAU); g.clip(); const ss = g.createRadialGradient(rx * 0.25, rx * 0.35, rx * 0.45, rx * 0.25, rx * 0.35, rx * 1.05); ss.addColorStop(0, 'rgba(255,130,70,0)'); ss.addColorStop(1, 'rgba(255,130,70,.4)'); g.fillStyle = ss; g.fillRect(-rx, -rx, 2 * rx, 2 * rx); g.restore(); }
  if (o.rim !== false) { g.strokeStyle = 'rgba(255,215,235,.75)'; g.lineWidth = Math.max(2, rx * 0.045); g.lineCap = 'round'; g.beginPath(); g.arc(0, 0, rx * 0.965, -0.95, 0.85); g.stroke(); }
  const sp = g.createRadialGradient(-rx * 0.4, -rx * 0.48, 0, -rx * 0.4, -rx * 0.48, rx * 0.3); sp.addColorStop(0, 'rgba(255,255,255,.9)'); sp.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = sp; g.beginPath(); g.arc(-rx * 0.4, -rx * 0.48, rx * 0.3, 0, TAU); g.fill();
  g.restore();
}
// three hard shading bands from a light angle: the lit colour, the base colour and a purple-tinted shadow
const band3 = (base, v) => rgba(v > 0.55 ? mix(base, [255, 245, 220], 0.28) : v > 0.1 ? base : mix(base, [70, 30, 110], 0.42));
const INK = '#17101f';
const hexOf = (c) => '#' + c.map((v) => Math.round(v).toString(16).padStart(2, '0')).join('');
const halftoneDots = (g, bb, pitch, val) => halftone(g, bb, pitch, 0.78, val);   // a screen of dots whose size follows val(x, y), 0..1

export const LOOKS = {
  /* ------------------------------------------------ 3D looks, faked in 2D ------------------------------------------------ */
  'stylised-3d': { kind: '2d', fps: null, draw(g, t, W, H) {
    // a soft, rounded 3D cartoon chef: a tomato with a big readable face, a soft key light from the upper left, a cool rim light on the right, warm light bleeding through the skin, and a contact shadow
    const breath = Math.sin(t * 2.2) * 0.012, bob = Math.abs(Math.sin(t * 1.6)) * 10, blink = (t % 3.1) < 0.12, wave = Math.sin(t * 5) * 0.35;
    const wall = g.createLinearGradient(0, 0, 0, H); wall.addColorStop(0, '#ffe9cf'); wall.addColorStop(1, '#f2b97a'); g.fillStyle = wall; g.fillRect(0, 0, W, H);
    for (let i = 0; i < 12; i++) { const x = hash(i, 1) * W, y = hash(i, 2) * 300, r = 18 + hash(i, 3) * 40; g.fillStyle = `rgba(255,255,255,${0.05 + hash(i, 4) * 0.12})`; g.beginPath(); g.arc(x, y, r, 0, TAU); g.fill(); }   // out-of-focus kitchen lights
    g.fillStyle = '#c98a52'; g.fillRect(0, 440, W, 100); g.fillStyle = 'rgba(255,255,255,.2)'; g.fillRect(0, 440, W, 6);
    const sh = g.createRadialGradient(480, 468, 10, 480, 468, 170); sh.addColorStop(0, `rgba(70,30,10,${0.5 - bob * 0.02})`); sh.addColorStop(1, 'rgba(70,30,10,0)'); g.save(); g.translate(0, 468); g.scale(1, 0.18); g.translate(0, -468); g.fillStyle = sh; g.fillRect(280, 280, 400, 400); g.restore();
    g.save(); g.translate(480, 440 - bob); g.scale(1 + breath, 1 - breath); g.translate(-480, -440);
    for (const d of [-1, 1]) { ball(g, 480 + d * 52, 428, 36, 24, [74, 44, 36], { warm: false }); g.strokeStyle = '#f4e8d8'; g.lineWidth = 16; g.lineCap = 'round'; g.beginPath(); g.moveTo(480 + d * 52, 420); g.lineTo(480 + d * 50, 386); g.stroke(); }   // legs and shoes
    g.lineCap = 'round'; g.lineWidth = 34; g.strokeStyle = '#c93a2a'; g.beginPath(); g.moveTo(340, 330); g.quadraticCurveTo(300, 360, 306, 396); g.stroke(); g.lineWidth = 12; g.strokeStyle = 'rgba(255,190,150,.5)'; g.beginPath(); g.moveTo(334, 322); g.quadraticCurveTo(292, 354, 298, 392); g.stroke(); ball(g, 306, 402, 28, 26, [250, 246, 238]);
    g.save(); g.translate(620, 312); g.rotate(-0.5 - wave); g.lineWidth = 34; g.strokeStyle = '#c93a2a'; g.beginPath(); g.moveTo(0, 0); g.quadraticCurveTo(50, -10, 76, -52); g.stroke(); g.lineWidth = 12; g.strokeStyle = 'rgba(255,190,150,.5)'; g.beginPath(); g.moveTo(0, -8); g.quadraticCurveTo(48, -18, 70, -58); g.stroke(); ball(g, 80, -60, 30, 28, [250, 246, 238]); g.restore();   // the waving arm
    ball(g, 480, 300, 158, 142, [226, 56, 40]);
    polyFill(g, star(480, 168, 58, 22, 7, -1.57, 0.3, 4), '#4f9a3a'); g.fillStyle = 'rgba(255,255,255,.25)'; g.beginPath(); g.ellipse(466, 160, 16, 6, -0.4, 0, TAU); g.fill();
    for (const [x, y, r] of [[420, 112, 40], [480, 92, 48], [542, 112, 40]]) ball(g, x, y, r, r * 0.92, [252, 250, 244], { warm: false }); g.fillStyle = '#f4efe6'; g.beginPath(); g.roundRect(424, 124, 112, 40, 12); g.fill(); g.fillStyle = 'rgba(0,0,0,.12)'; g.fillRect(424, 150, 112, 14);   // the chef's hat
    for (const d of [-1, 1]) {
      const ex = 480 + d * 52, ey = 292;
      if (blink) { g.strokeStyle = '#3a1a14'; g.lineWidth = 7; g.lineCap = 'round'; g.beginPath(); g.arc(ex, ey + 6, 22, 0.15 * Math.PI, 0.85 * Math.PI); g.stroke(); continue; }
      ball(g, ex, ey, 31, 36, [255, 255, 255], { warm: false }); ball(g, ex + d * -1 + 4, ey + 4, 17, 20, [58, 30, 24], { warm: false, rim: false }); ell(g, ex - 2, ey - 3, 6, 7, '#fff'); ell(g, ex + 8, ey + 10, 3, 3, 'rgba(255,255,255,.8)');
      g.strokeStyle = '#3a1a14'; g.lineWidth = 8; g.lineCap = 'round'; g.beginPath(); g.moveTo(ex - d * 24, ey - 46 + d * 4); g.quadraticCurveTo(ex, ey - 62, ex + d * 28, ey - 44 - d * 6); g.stroke();
    }
    for (const d of [-1, 1]) { g.fillStyle = 'rgba(255,120,110,.4)'; g.beginPath(); g.ellipse(480 + d * 100, 340, 22, 13, 0, 0, TAU); g.fill(); }
    g.fillStyle = '#4a1a1a'; g.beginPath(); g.moveTo(436, 350); g.quadraticCurveTo(480, 410, 524, 350); g.quadraticCurveTo(480, 366, 436, 350); g.fill(); g.fillStyle = '#fffaf0'; g.fillRect(452, 352, 56, 9);
    g.restore();
  } },
  'toon-3d': { kind: '2d', fps: null, draw(g, t, W, H) {
    // solid forms lit from the upper left and cut into three flat shading bands, with a thick ink line round every silhouette and a printed-comic feel: halftone shadow, hatching, paper grain
    const L = norm3([-0.5, 0.7, 0.6]), tilt = 0.5, back = g.createLinearGradient(0, 0, 0, H); back.addColorStop(0, '#ffd9a0'); back.addColorStop(0.55, '#ffe8c2'); back.addColorStop(0.55, '#f2d3a0'); back.addColorStop(1, '#e8bd84'); g.fillStyle = back; g.fillRect(0, 0, W, H);
    g.fillStyle = 'rgba(214,120,90,.35)'; halftoneDots(g, [0, 0, W, 150], 9, (x, y) => 1 - y / 150);
    g.lineJoin = 'round'; g.lineCap = 'round';
    const shadow = (x, y, rx) => { g.fillStyle = 'rgba(90,50,110,.45)'; g.beginPath(); g.ellipse(x + rx * 0.35, y, rx, rx * 0.28, 0, 0, TAU); g.fill(); };
    const solid = (verts, faces, base, cx, cy, S, a) => {
      const pts = verts.map((v) => turn(v, a, tilt)), out = faces.map((f) => { const n = turn(f.n, a, tilt), p = f.v.map((i) => pts[i]); return { n, p, d: p.reduce((s, q) => s + q[2], 0) }; }).filter((f) => f.n[2] > 0).sort((u, v) => u.d - v.d);
      for (const f of out) { const v = dot3(f.n, L), scr = f.p.map(([x, y]) => [cx + x * S, cy - y * S]); polyFill(g, scr, band3(base, v), INK, 5.5); if (v <= 0.1) { g.save(); path(g, scr); g.clip(); g.globalAlpha = 0.35; lines(g, [cx - S * 2, cy - S * 2, cx + S * 2, cy + S * 2], 0.8, 7, 1.6, INK); g.restore(); } }
    };
    const cube = [[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1], [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], cf = [{ v: [4, 5, 6, 7], n: [0, 0, 1] }, { v: [1, 0, 3, 2], n: [0, 0, -1] }, { v: [5, 1, 2, 6], n: [1, 0, 0] }, { v: [0, 4, 7, 3], n: [-1, 0, 0] }, { v: [7, 6, 2, 3], n: [0, 1, 0] }, { v: [0, 1, 5, 4], n: [0, -1, 0] }];
    const pyr = [[-1, -1, -1], [1, -1, -1], [1, -1, 1], [-1, -1, 1], [0, 1.3, 0]], pf = [{ v: [3, 2, 4], n: norm3([0, 0.5, 1]) }, { v: [2, 1, 4], n: norm3([1, 0.5, 0]) }, { v: [1, 0, 4], n: norm3([0, 0.5, -1]) }, { v: [0, 3, 4], n: norm3([-1, 0.5, 0]) }];
    shadow(250, 420, 110); solid(cube, cf, [226, 70, 52], 250, 330, 78, t * 0.8);
    shadow(700, 430, 100); solid(pyr, pf, [246, 200, 50], 700, 350, 86, -t * 0.6 + 0.4);
    const by = 330 - Math.abs(Math.sin(t * 2.2)) * 60, R = 92, bx = 480; shadow(bx, 440, 80 - (330 - by) * 0.2);
    g.save(); g.beginPath(); g.arc(bx, by, R, 0, TAU); g.clip(); g.fillStyle = band3([52, 112, 224], -1); g.fillRect(bx - R, by - R, 2 * R, 2 * R); g.fillStyle = band3([52, 112, 224], 0.3); g.beginPath(); g.arc(bx - 0.28 * R, by - 0.3 * R, 0.94 * R, 0, TAU); g.fill(); g.fillStyle = band3([52, 112, 224], 0.9); g.beginPath(); g.arc(bx - 0.4 * R, by - 0.42 * R, 0.6 * R, 0, TAU); g.fill();
    g.globalAlpha = 0.4; g.fillStyle = INK; halftoneDots(g, [bx - R, by - R, bx + R, by + R], 7, (x, y) => clamp(((x - bx) + (y - by)) / (1.4 * R))); g.restore();
    g.fillStyle = '#fff'; g.beginPath(); g.ellipse(bx - 0.46 * R, by - 0.5 * R, 0.16 * R, 0.09 * R, -0.7, 0, TAU); g.fill();
    g.strokeStyle = INK; g.lineWidth = 6.5; g.beginPath(); g.arc(bx, by, R, 0, TAU); g.stroke();
    speckle(g, W, H, 4, 36, [120, 80, 50]);
  } },
  'point-cloud': { kind: '2d', fps: null, draw(g, t, W, H) {
    // a scan made of about six thousand glowing points on black: a gold knot over a blue ground that a pulse of light sweeps across, turning slowly, with points fading and shrinking as they recede
    g.fillStyle = '#04050a'; g.fillRect(0, 0, W, H); const vg = g.createRadialGradient(480, 280, 40, 480, 280, 520); vg.addColorStop(0, 'rgba(20,30,70,.5)'); vg.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = vg; g.fillRect(0, 0, W, H);
    const a = t * 0.35, tilt = 0.55, sweep = (t * 2.2) % 8, grow = easeOut(prog(t, 0, 1.6)); g.globalCompositeOperation = 'lighter';
    const plot = (p, col, boost) => {
      const [x, y, z] = turn(p, a, tilt), f = 640 / (640 - z * 60), sx = 480 + x * 78 * f, sy = 292 - y * 78 * f, zn = clamp((z + 5) / 10), al = clamp((0.2 + 0.8 * zn * zn) * boost), sz = (1.1 + 2.4 * zn) * (boost > 1 ? 1.4 : 1);
      g.fillStyle = rgba(col, al); g.fillRect(sx - sz / 2, sy - sz / 2, sz, sz);
    };
    for (let i = 0; i < 5200 * grow; i++) {   // a trefoil knot, thickened into a tube of points
      const u = (i / 5200) * TAU, r = 2 + Math.cos(3 * u), k = [r * Math.cos(2 * u) * 0.85 + (hash(i, 1) - 0.5) * 0.4, Math.sin(3 * u) * 0.85 + 0.2 + (hash(i, 2) - 0.5) * 0.4, r * Math.sin(2 * u) * 0.85 + (hash(i, 3) - 0.5) * 0.4];
      plot(k, mix([255, 196, 80], [255, 240, 190], clamp((k[1] + 1) / 2)), 1);
    }
    for (let i = 0; i < 5200 * grow; i++) {   // the ground, scanned in rings: a disc of points with low hills, and a bright ring where the pulse is passing
      const r = 0.6 + Math.floor(Math.sqrt(hash(i, 4)) * 30) * 0.2 + hash(i, 9) * 0.03, th = hash(i, 5) * TAU, hgt = -2.3 + 0.38 * Math.sin(r * 1.5 + th * 3) + 0.2 * Math.sin(th * 5 + r), near = Math.abs(r - sweep) < 0.28;
      plot([Math.cos(th) * r, hgt, Math.sin(th) * r], near ? [190, 230, 255] : mix([50, 110, 255], [120, 180, 255], clamp(1 - r / 7)), near ? 2.4 : 1.3);
    }
    for (let i = 0; i < 260; i++) { const th = hash(i, 6) * TAU, r = 3.5 + hash(i, 7) * 0.2, hh = hash(i, 8) * 2.6 - 2.3; plot([Math.cos(th) * r * 0.5 + 3.4, hh, Math.sin(th) * r * 0.5 - 2], [120, 190, 255], 1); }   // a thin tower
    g.globalCompositeOperation = 'source-over';
  } },
  diorama: { kind: '2d', fps: null, draw(g, t, W, H) {
    // a tiny town seen from a high camera: saturated toy colours, little cars looping round the roads, and a tilt-shift blur that grows toward the top and the bottom of the frame
    const sc = new OffscreenCanvas(W, H), c = sc.getContext('2d'), cx = 480, cy = 46, cw = 31, ch = 15.5, bh = 22, iso = (x, y, z) => [cx + (x - y) * cw, cy + (x + y) * ch - z * bh];
    const sky = c.createLinearGradient(0, 0, 0, H); sky.addColorStop(0, '#bfe3ff'); sky.addColorStop(1, '#fff3d6'); c.fillStyle = sky; c.fillRect(0, 0, W, H); c.lineJoin = 'round';
    const slab = (z0, z1, x0, y0, x1, y1, col, top = col) => { polyFill(c, [iso(x0, y1, z1), iso(x1, y1, z1), iso(x1, y1, z0), iso(x0, y1, z0)], shadeHex(col, 0.8)); polyFill(c, [iso(x1, y0, z1), iso(x1, y1, z1), iso(x1, y1, z0), iso(x1, y0, z0)], shadeHex(col, 0.62)); polyFill(c, [iso(x0, y0, z1), iso(x1, y0, z1), iso(x1, y1, z1), iso(x0, y1, z1)], top); };
    slab(-0.6, 0, 0, 0, 14, 14, '#8a5a2b', '#7bc74e');
    c.fillStyle = '#59606b'; polyFill(c, [iso(0, 6, 0.02), iso(14, 6, 0.02), iso(14, 8, 0.02), iso(0, 8, 0.02)], '#59606b'); polyFill(c, [iso(6, 0, 0.02), iso(8, 0, 0.02), iso(8, 14, 0.02), iso(6, 14, 0.02)], '#59606b');
    c.strokeStyle = '#f5d742'; c.lineWidth = 2; c.setLineDash([9, 9]); for (const [a, b] of [[iso(0, 7, 0.03), iso(14, 7, 0.03)], [iso(7, 0, 0.03), iso(7, 14, 0.03)]]) { c.beginPath(); c.moveTo(...a); c.lineTo(...b); c.stroke(); } c.setLineDash([]);
    const objs = [], PAL = [[226, 70, 52], [245, 197, 24], [47, 111, 223], [244, 241, 234], [236, 110, 170], [64, 168, 92]];
    for (const [qx, qy] of [[0.4, 0.4], [8.4, 0.4], [0.4, 8.4], [8.4, 8.4]]) for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) {
      const h = hash(qx * 7 + i, qy * 5 + j, 3), x = qx + i * 1.85, y = qy + j * 1.85, col = PAL[Math.floor(hash(qx + i, qy + j, 9) * 6)];
      if (h < 0.22) objs.push({ k: x + y + 1, draw: () => { slab(0, 0.35 + h * 2, x + 0.5, y + 0.5, x + 1.3, y + 1.3, '#2e7a3a', '#3f9b4f'); } });   // a tree: a green block
      else objs.push({ k: x + y + 1.6, draw: () => { const ht = 0.9 + h * 3.2; slab(0, ht, x, y, x + 1.55, y + 1.55, hexOf(col), hexOf(mix(col, [255, 255, 255], 0.18))); for (let w = 0; w < ht - 0.5; w++) polyFill(c, [iso(x + 1.55, y + 0.3, w + 0.8), iso(x + 1.55, y + 0.6, w + 0.8), iso(x + 1.55, y + 0.6, w + 0.45), iso(x + 1.55, y + 0.3, w + 0.45)], 'rgba(255,240,170,.85)'); } });
    }
    const CARS = ['#e24634', '#2f6fdf', '#f5c518', '#f4f1ea', '#40a85c'];
    for (let i = 0; i < 8; i++) {
      const lane = i % 4, u = ((t * (1.6 + (i % 3) * 0.3) + i * 3.3) % 16) - 1, vert = lane > 1, fixed = lane % 2 ? 7.45 : 6.55, x = vert ? fixed : (lane % 2 ? 14 - u : u), y = vert ? (lane % 2 ? 14 - u : u) : fixed;
      objs.push({ k: x + y + 0.6, draw: () => slab(0.02, 0.45, x - (vert ? 0.25 : 0.45), y - (vert ? 0.45 : 0.25), x + (vert ? 0.25 : 0.45), y + (vert ? 0.45 : 0.25), CARS[i % 5], CARS[i % 5]) });
    }
    objs.sort((a, b) => a.k - b.k).forEach((o) => o.draw());
    g.drawImage(sc, 0, 0);
    for (const [y0, y1, px] of [[0, 40, 8], [40, 80, 5], [80, 120, 3], [120, 150, 1.5], [390, 420, 1.5], [420, 460, 3], [460, 500, 5], [500, 540, 8]]) { g.save(); g.beginPath(); g.rect(0, y0, W, y1 - y0); g.clip(); g.filter = `blur(${px}px)`; g.drawImage(sc, 0, 0); g.restore(); }
    g.filter = 'none'; const vg = g.createRadialGradient(480, 270, 250, 480, 270, 620); vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(40,20,0,.25)'); g.fillStyle = vg; g.fillRect(0, 0, W, H);
  } },
  'parallax-2-5d': { kind: '2d', fps: null, draw(g, t, W, H) {
    // flat painted layers as the camera pans: a sky, far mountains, rolling hills, a row of pines, a field with flowers and a fence, and dark grass blades in front, each moving at its own speed
    const cam = t * 90, bob = Math.sin(t * 1.1) * 3, haze = (col, k) => rgba(mix(col, [255, 226, 180], k));
    const sky = g.createLinearGradient(0, 0, 0, 400); sky.addColorStop(0, '#6fb8f0'); sky.addColorStop(1, '#ffe7b0'); g.fillStyle = sky; g.fillRect(0, 0, W, H);
    const sx = 700 - ((cam * 0.02) % 1400), sunG = g.createRadialGradient(sx, 130, 10, sx, 130, 160); sunG.addColorStop(0, 'rgba(255,250,210,1)'); sunG.addColorStop(0.3, 'rgba(255,240,170,.6)'); sunG.addColorStop(1, 'rgba(255,230,160,0)'); g.fillStyle = sunG; g.fillRect(sx - 170, -40, 340, 340);
    const col = (speed, cw, fn) => { const off = cam * speed; for (let i = Math.floor(off / cw) - 1; i * cw - off < W + cw; i++) fn(i, i * cw - off, cw); };
    col(0.07, 320, (i, x) => { const y = 70 + hash(i, 1) * 90, w = 90 + hash(i, 2) * 70; g.fillStyle = 'rgba(255,255,255,.85)'; for (const [dx, dy, r] of [[0, 0, 28], [30, -10, 34], [66, 2, 26]]) { g.beginPath(); g.arc(x + dx + w * 0.2, y + dy, r, 0, TAU); g.fill(); } });
    const ridge = (speed, base, amp, scale, seed, colr, top) => { const off = cam * speed; g.beginPath(); g.moveTo(0, H); for (let x = 0; x <= W; x += 6) g.lineTo(x, base - amp * vnoise((x + off) / scale, 0, seed)); g.lineTo(W, H); g.closePath(); const gr = g.createLinearGradient(0, base - amp, 0, base + 60); gr.addColorStop(0, top); gr.addColorStop(1, colr); g.fillStyle = gr; g.fill(); };
    ridge(0.12, 330 + bob * 0.2, 170, 90, 3, haze([120, 140, 200], 0.35), haze([220, 230, 250], 0.2));   // far mountains
    ridge(0.28, 380 + bob * 0.5, 80, 160, 7, haze([84, 150, 90], 0.2), haze([140, 190, 110], 0.1));   // rolling hills
    col(0.55, 70, (i, x) => { const h = 70 + hash(i, 3) * 70, y = 408 + bob; if (hash(i, 4) < 0.2) return; g.fillStyle = '#2a5a34'; g.fillRect(x + 30, y - 10, 8, 16); for (let k = 0; k < 3; k++) { g.beginPath(); g.moveTo(x + 6 + k * 4, y - 6 - k * h * 0.28); g.lineTo(x + 34, y - 20 - h * (0.35 + k * 0.28)); g.lineTo(x + 62 - k * 4, y - 6 - k * h * 0.28); g.closePath(); g.fillStyle = k % 2 ? '#2f6b3a' : '#2a5a34'; g.fill(); } });
    g.fillStyle = '#5aa63e'; g.fillRect(0, 420 + bob, W, H); const grass = g.createLinearGradient(0, 420, 0, H); grass.addColorStop(0, '#6cba46'); grass.addColorStop(1, '#3f8a2e'); g.fillStyle = grass; g.fillRect(0, 420 + bob, W, H);
    col(1, 120, (i, x) => { g.fillStyle = '#e8d3a8'; g.fillRect(x, 452 + bob, 8, 46); g.fillRect(x + 40, 452 + bob, 8, 46); g.fillRect(x - 4, 462 + bob, 128, 7); g.fillRect(x - 4, 480 + bob, 128, 7); for (let k = 0; k < 2; k++) { const fx = x + 20 + hash(i, k) * 90, fy = 500 + hash(i, k + 5) * 30 + bob; g.fillStyle = '#f2f2e6'; for (let p = 0; p < 5; p++) { g.beginPath(); g.arc(fx + Math.cos(p * 1.26) * 6, fy + Math.sin(p * 1.26) * 6, 4, 0, TAU); g.fill(); } g.fillStyle = hash(i, k + 9) > 0.5 ? '#f5c518' : '#e24634'; g.beginPath(); g.arc(fx, fy, 3.4, 0, TAU); g.fill(); } });
    col(1.8, 26, (i, x) => { const h = 50 + hash(i, 7) * 60, sw = Math.sin(t * 2 + i) * 6; g.fillStyle = hash(i, 8) > 0.5 ? '#2a6a2a' : '#1f5420'; g.beginPath(); g.moveTo(x, H); g.quadraticCurveTo(x + 6 + sw * 0.5, H - h * 0.6, x + 12 + sw, H - h); g.quadraticCurveTo(x + 16, H - h * 0.5, x + 22, H); g.closePath(); g.fill(); });
    speckle(g, W, H, 7, 22, [255, 240, 200]);
  } },
};
export const IDS = Object.keys(LOOKS);
