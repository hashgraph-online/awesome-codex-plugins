// The Smallest Star, live: the film's own renderer running progressively in the browser.
import { Engine, QUALITY } from '../src/engine.js';
import { VS, ptFS, PREP_FS, ATROUS_FS, COMP_FS, DOWN_FS, UP_FS, FINAL_FS } from '../src/shader.js';
import { state, toUniforms, setTimeline } from '../src/shots.js';
import { add, sub, mul, cross, norm, len } from '../src/vec.js';
import TL from '../timeline.json';

setTimeline(TL);
const $ = (id) => document.getElementById(id);
const canvas = $('view'), statusEl = $('status'), stage = $('stage');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const ATROUS_LIVE = ATROUS_FS.replace('uniform vec4 uSig;', 'uniform vec4 uSig; uniform float uFloor;').replace('uSig.w*sdv + 1e-4', 'uSig.w*sdv + uFloor');
const TIERS = [[384, 216], [512, 288], [640, 360], [800, 450], [960, 540]];
const SCENES = [
  { id: 'first-light', t: 7.4 }, { id: 'the-moon', t: 17.0 }, { id: 'the-meeting', t: 31.6 },
  { id: 'the-crossing', t: 42.5 }, { id: 'home', t: 48.7 }, { id: 'the-star', t: 58.6 },
];

let eng = null, gl = null, lost = false;
let t = 31.6, playing = false, mode = 0, yaw = 0, pitch = 0, zoom = 1, light = 1;
let acc = 0, dirty = true, tier = 1, tuned = false, msAvg = 0, msN = 0, last = 0, fine = false;

function say(msg, busy) { statusEl.textContent = msg; stage.classList.toggle('busy', !!busy); }

function alloc(w, h) {
  const g = gl;
  for (const k of ['acc', 'dnA', 'dnB', 'hdr', 'out']) if (eng[k]) { g.deleteFramebuffer(eng[k].f); eng[k].tex.forEach((x) => g.deleteTexture(x)); }
  if (eng.bloom) for (const b of eng.bloom) { g.deleteFramebuffer(b.f); b.tex.forEach((x) => g.deleteTexture(x)); }
  eng.w = w; eng.h = h; canvas.width = w; canvas.height = h;
  eng.acc = eng.fbo(w, h, [g.RGBA32F, g.RGBA32F, g.RGBA32F, g.RGBA32F], g.NEAREST);
  eng.dnA = eng.fbo(w, h, [g.RGBA16F], g.NEAREST); eng.dnB = eng.fbo(w, h, [g.RGBA16F], g.NEAREST);
  eng.hdr = eng.fbo(w, h, [g.RGBA16F], g.LINEAR);
  eng.bloom = []; let bw = w, bh = h;
  for (let i = 0; i < 6; i++) { bw = Math.max(2, bw >> 1); bh = Math.max(2, bh >> 1); eng.bloom.push(eng.fbo(bw, bh, [g.RGBA16F], g.LINEAR)); }
  eng.out = eng.fbo(w, h, [g.RGBA8], g.NEAREST);
  eng.pixels = new Uint8Array(4);
  acc = 0;
}

async function boot() {
  eng = Object.create(Engine.prototype);
  gl = canvas.getContext('webgl2', { antialias: false, alpha: false, depth: false, stencil: false, powerPreference: 'high-performance' });
  if (!gl) throw new Error('This browser has no WebGL2, which the renderer needs.');
  eng.gl = gl;
  for (const e of ['EXT_color_buffer_float', 'EXT_float_blend', 'OES_texture_float_linear']) {
    if (!gl.getExtension(e)) throw new Error('This graphics card cannot render to floating-point buffers, which the path tracer needs.');
  }
  const par = gl.getExtension('KHR_parallel_shader_compile');
  const srcs = { pPT: ptFS(QUALITY.draft), pPrep: PREP_FS, pAtrous: ATROUS_LIVE, pComp: COMP_FS, pDown: DOWN_FS, pUp: UP_FS, pFinal: FINAL_FS };
  const pend = [];
  for (const [k, fs] of Object.entries(srcs)) {
    const p = gl.createProgram();
    const mk = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); gl.attachShader(p, s); return s; };
    mk(gl.VERTEX_SHADER, VS); const f = mk(gl.FRAGMENT_SHADER, fs);
    gl.bindAttribLocation(p, 0, 'aPos'); gl.linkProgram(p); pend.push({ k, p, f });
  }
  if (par) { while (!pend.every((x) => gl.getProgramParameter(x.p, par.COMPLETION_STATUS_KHR))) await sleep(80); } else await sleep(40);
  for (const x of pend) {
    if (!gl.getProgramParameter(x.p, gl.LINK_STATUS)) throw new Error('The renderer did not compile on this graphics driver.');
    eng[x.k] = { p: x.p, loc: new Map(), name: x.k };
  }
  const vb = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, vb);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  eng.vao = gl.createVertexArray(); gl.bindVertexArray(eng.vao);
  gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
  alloc(...TIERS[tier]);
}

function uniformsNow() {
  const S = state(t);
  const c = S.cam; let v = sub(c.pos, c.tgt);
  const d0 = len(v);
  const cy = Math.cos(yaw), sy = Math.sin(yaw);
  v = [v[0] * cy + v[2] * sy, v[1], -v[0] * sy + v[2] * cy];
  const r = norm(cross([0, 1, 0], v));
  const cp = Math.cos(pitch), sp = Math.sin(pitch);
  const up = cross(v, r);
  v = add(mul(v, cp), mul(norm(up), sp * len(v)));
  v = mul(norm(v), d0 * zoom);
  c.pos = add(c.tgt, v);
  if (c.pos[1] < -0.2) c.pos[1] = -0.2;
  c.focus *= zoom;
  S.ff.glow *= light; S.ff.emi = 0.5 + (S.ff.emi - 0.5) * Math.min(light, 1.6);
  S.post.grain = 0.02;
  return toUniforms(S);
}

function pass(U, s) {
  gl.bindVertexArray(eng.vao);
  gl.bindFramebuffer(gl.FRAMEBUFFER, eng.acc.f); gl.viewport(0, 0, eng.w, eng.h);
  if (s === 0) { gl.disable(gl.BLEND); gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT); }
  gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE);
  eng.use(eng.pPT);
  for (const k in U.pt) eng.set(k, U.pt[k]);
  eng.set('uRes', [eng.w, eng.h]); eng.set('uTime', t); eng.set('uSlice', 1 / 48);
  eng.seti('uPass', s); eng.seti('uSeed', Math.floor(t * 24) + 7);
  eng.draw();
  gl.disable(gl.BLEND);
}

function show(U) {
  eng.use(eng.pAtrous); eng.set('uFloor', 0.35 / (acc * acc) + 1e-4);
  const iters = mode === 4 ? 0 : (acc < 4 ? 5 : acc < 24 ? 4 : acc < 96 ? 3 : 2);
  eng.resolve(U.post, { spp: acc, mode, denoise: iters, seed: acc });
  gl.bindFramebuffer(gl.READ_FRAMEBUFFER, eng.out.f); gl.bindFramebuffer(gl.DRAW_FRAMEBUFFER, null);
  gl.blitFramebuffer(0, 0, eng.w, eng.h, 0, eng.h, eng.w, 0, gl.COLOR_BUFFER_BIT, gl.NEAREST);
  gl.bindFramebuffer(gl.FRAMEBUFFER, null);
}

function readout() {
  const cap = mode === 4 ? 1 : (mode === 1 || mode === 2) ? 16 : 256;
  $('r-spp').textContent = String(Math.min(acc, cap));
  $('r-ms').textContent = msN ? msAvg.toFixed(0) : '–';
  $('r-res').textContent = `${eng.w}×${eng.h}`;
  $('r-time').textContent = t.toFixed(1) + ' s';
}

function frame(now) {
  if (lost) return;
  const dt = Math.min(0.1, (now - last) / 1000 || 0); last = now;
  if (playing) { t += dt; if (t >= 60) t = 0; $('scrub').value = String(t); dirty = true; markScene(); }
  // any change drops back to the fast size; once the picture has settled it is traced again, larger
  if (dirty) { if (fine) { fine = false; alloc(...TIERS[tier]); } acc = 0; dirty = false; }
  const cap = mode === 4 ? 1 : (mode === 1 || mode === 2) ? 16 : (fine ? 160 : 256);
  if (acc < cap) {
    const U = uniformsNow();
    const n = playing ? 2 : 1;
    const t0 = performance.now();
    for (let i = 0; i < n && acc < cap; i++) { pass(U, acc); acc++; }
    eng.sync();
    const ms = (performance.now() - t0) / n;
    if (!fine) { msN++; msAvg = msN <= 4 ? ms : msAvg * 0.8 + ms * 0.2; }   // the first passes include driver warm-up
    show(U);
    if (!tuned && msN === 12) {
      tuned = true;
      const px = eng.w * eng.h; let best = 0;
      for (let i = 0; i < TIERS.length; i++) if (msAvg * (TIERS[i][0] * TIERS[i][1]) / px <= 45) best = i;
      if (best !== tier) { tier = best; alloc(...TIERS[tier]); msN = 0; }
    }
    if (tuned && !fine && !playing && mode === 0 && acc >= 36 && tier < TIERS.length - 1) {
      const up = Math.min(TIERS.length - 1, tier + 2);
      if (msAvg * (TIERS[up][0] * TIERS[up][1]) / (eng.w * eng.h) <= 260) { fine = true; alloc(...TIERS[up]); }
    }
    readout();
  }
  requestAnimationFrame(frame);
}

function markScene() {
  let cur = null;
  for (const s of SCENES) if (Math.abs(s.t - t) < 0.05) cur = s.id;
  document.querySelectorAll('[data-scene]').forEach((b) => b.setAttribute('aria-pressed', b.dataset.scene === cur ? 'true' : 'false'));
}

function wire() {
  document.querySelectorAll('[data-scene]').forEach((b) => b.addEventListener('click', () => {
    const s = SCENES.find((x) => x.id === b.dataset.scene); t = s.t; yaw = 0; pitch = 0; zoom = 1; playing = false;
    $('play').textContent = 'Play'; $('scrub').value = String(t); dirty = true; markScene(); readout();
  }));
  document.querySelectorAll('[data-mode]').forEach((b) => b.addEventListener('click', () => {
    mode = +b.dataset.mode; dirty = true;
    document.querySelectorAll('[data-mode]').forEach((x) => x.setAttribute('aria-pressed', x === b ? 'true' : 'false'));
  }));
  $('play').addEventListener('click', () => { playing = !playing; $('play').textContent = playing ? 'Pause' : 'Play'; dirty = true; });
  $('scrub').addEventListener('input', (e) => { t = +e.target.value; dirty = true; markScene(); readout(); });
  $('light').addEventListener('input', (e) => { light = +e.target.value; dirty = true; });
  $('zin').addEventListener('click', () => { zoom = Math.max(0.45, zoom * 0.85); dirty = true; });
  $('zout').addEventListener('click', () => { zoom = Math.min(2.2, zoom / 0.85); dirty = true; });
  $('reset').addEventListener('click', () => { yaw = 0; pitch = 0; zoom = 1; dirty = true; });
  let drag = null;
  canvas.addEventListener('pointerdown', (e) => { drag = { x: e.clientX, y: e.clientY }; canvas.setPointerCapture(e.pointerId); });
  canvas.addEventListener('pointermove', (e) => {
    if (!drag) return;
    yaw += (e.clientX - drag.x) * 0.006; pitch = Math.max(-0.5, Math.min(0.9, pitch + (e.clientY - drag.y) * 0.004));
    drag = { x: e.clientX, y: e.clientY }; dirty = true;
  });
  const end = () => { drag = null; };
  canvas.addEventListener('pointerup', end); canvas.addEventListener('pointercancel', end);
  canvas.addEventListener('keydown', (e) => {
    const k = { ArrowLeft: [-0.08, 0], ArrowRight: [0.08, 0], ArrowUp: [0, 0.05], ArrowDown: [0, -0.05] }[e.key];
    if (!k) return; e.preventDefault(); yaw += k[0]; pitch = Math.max(-0.5, Math.min(0.9, pitch + k[1])); dirty = true;
  });
  canvas.addEventListener('webglcontextlost', (e) => { e.preventDefault(); lost = true; say('The graphics card dropped the renderer. Reload the page to start it again.', false); stage.classList.add('failed'); });
}

(async () => {
  say('Compiling the path tracer for your graphics card…', true);
  try {
    await boot(); wire(); markScene();
    say('Rendering live. Drag the picture to move the camera.', false);
    stage.classList.add('live');
    requestAnimationFrame(frame);
  } catch (err) {
    stage.classList.add('failed');
    say(String(err && err.message || err) + ' The still shows a frame from the film.', false);
  }
})();
