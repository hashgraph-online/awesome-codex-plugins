// explainer.js: the generic runtime of a code-3d-explainer film (subject-agnostic).
//
// A film = story.json (timing, camera keys, labels, texts) + a subject module (build(ctx) -> parts).
// What is on screen is a pure function of t: render(t) poses every part, the camera, the labels and
// the scale bar from t alone (no clocks, no state between frames, seeded randomness only), so frames
// can be rendered in any order, in parallel, by scripts/capture.ts or by HyperFrames (hf-seek).
//
// Contract published on window.__film:
//   { ready: Promise, fps, duration, width, height, render(t), labels() -> visible label/text boxes }
// Dev view: open index.html?dev=1 in a browser for a scrubber (space = play, arrows = step).

import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { BokehPass } from 'three/addons/postprocessing/BokehPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

// ---------- math ----------
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, k) => a + (b - a) * k;
export const smooth = (k) => { k = clamp(k); return k * k * (3 - 2 * k); };
export const ease = {
  outCubic: (k) => 1 - Math.pow(1 - clamp(k), 3),
  inOutCubic: (k) => { k = clamp(k); return k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2; },
  outBack: (k) => { k = clamp(k); const c1 = 1.5, c3 = c1 + 1; return 1 + c3 * Math.pow(k - 1, 3) + c1 * Math.pow(k - 1, 2); },
  inOutSine: (k) => -(Math.cos(Math.PI * clamp(k)) - 1) / 2,
};
/** progress of t through [a, b], clamped 0..1 */
export const win = (t, a, b) => clamp((t - a) / (b - a));
/** 0 -> 1 -> 0 envelope: rises over [a, a+fi], holds, falls over [b-fo, b] */
export const env = (t, a, b, fi = 0.3, fo = 0.3) => Math.min(smooth((t - a) / fi), smooth((b - t) / fo));
/** seeded PRNG (mulberry32): same seed, same film */
export function rng(seed) {
  let s = seed >>> 0;
  return () => { s = (s + 0x6d2b79f5) >>> 0; let r = Math.imul(s ^ (s >>> 15), 1 | s); r = (r + Math.imul(r ^ (r >>> 7), 61 | r)) ^ r; return ((r ^ (r >>> 14)) >>> 0) / 4294967296; };
}

// ---------- camera keys: C1 monotone cubic (PCHIP) through keys: smooth, never overshoots a key ----------
// A key is { t, pos, look, fov?, push? }. pos/look: [x,y,z], an anchor name, or {at: anchor, off: [dx,dy,dz]}.
// push: 0.92 puts the camera 8% closer to look than pos says (a slow drift-in for a "hold" key).
// Pairs of keys on one subject (arrive, then a small push) give move-hold-move pacing without a dead stop.
function pchipTrack(ts, vs) {
  const n = ts.length, dim = vs[0].length, h = [], d = [];
  for (let i = 0; i < n - 1; i++) { h.push(ts[i + 1] - ts[i]); d.push(vs[i].map((v, k) => (vs[i + 1][k] - v) / h[i])); }
  const m = vs.map((_, i) => Array.from({ length: dim }, (_, k) => {
    if (i === 0 || i === n - 1) return 0;
    const a = d[i - 1][k], b = d[i][k]; if (a * b <= 0) return 0;
    const w1 = 2 * h[i] + h[i - 1], w2 = h[i] + 2 * h[i - 1]; return (w1 + w2) / (w1 / a + w2 / b);
  }));
  return (t) => {
    if (t <= ts[0]) return vs[0].slice();
    if (t >= ts[n - 1]) return vs[n - 1].slice();
    let i = 0; while (t > ts[i + 1]) i++;
    const s = (t - ts[i]) / h[i], s2 = s * s, s3 = s2 * s;
    const h00 = 2 * s3 - 3 * s2 + 1, h10 = s3 - 2 * s2 + s, h01 = -2 * s3 + 3 * s2, h11 = s3 - s2;
    return vs[i].map((p0, k) => h00 * p0 + h10 * h[i] * m[i][k] + h01 * vs[i + 1][k] + h11 * h[i] * m[i + 1][k]);
  };
}
export function cameraPath(keys, anchors = {}) {
  const P = (v) => {
    if (typeof v === 'string') { if (!anchors[v]) throw new Error(`camera: unknown anchor ${v}`); return anchors[v].toArray(); }
    if (v && !Array.isArray(v) && v.at) { const a = anchors[v.at]; if (!a) throw new Error(`camera: unknown anchor ${v.at}`); return a.toArray().map((x, i) => x + (v.off?.[i] ?? 0)); }
    return v;
  };
  const ts = keys.map(k => k.t), looks = keys.map(k => P(k.look));
  const poss = keys.map((k, i) => { const p = P(k.pos), l = looks[i], f = k.push ?? 1; return p.map((x, d) => l[d] + (x - l[d]) * f); });
  const pos = pchipTrack(ts, poss), look = pchipTrack(ts, looks), fov = pchipTrack(ts, keys.map(k => [k.fov ?? 30]));
  return (t) => ({ pos: pos(t), look: look(t), fov: fov(t)[0] });
}

// ---------- scale bar: a true length at the look-at depth ----------
const NICE = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000];
export function scaleBar(camera, lookAt, H, { minPx = 150, unitsLabel = 'µm' } = {}) {
  const d = camera.position.distanceTo(lookAt);
  const upp = (2 * d * Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2)) / H; // world units per pixel
  let L = NICE[0];
  for (const v of NICE) if (v / upp >= minPx) { L = v; break; } else L = v;
  const text = unitsLabel === 'µm' && L < 1 ? `${Math.round(L * 1000)} nm` : `${L} ${unitsLabel}`;
  return { px: L / upp, text };
}

// ---------- the film ----------
export async function createFilm({ story, build, root = document.getElementById('root') }) {
  const W = story.width, H = story.height;
  const canvas = root.querySelector('canvas');
  const overlay = root.querySelector('.overlay');
  const dev = new URLSearchParams(location.search).has('dev');

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(1);
  renderer.setSize(W, H, false);
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.toneMappingExposure = story.look?.exposure ?? 1.0;
  renderer.localClippingEnabled = true;
  renderer.setClearColor(new THREE.Color(story.look?.background ?? '#05070a'), 1);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(story.look?.background ?? '#05070a');
  if (story.look?.fog) scene.fog = new THREE.FogExp2(scene.background.getHex(), story.look.fog);
  const camera = new THREE.PerspectiveCamera(30, W / H, 0.02, 400);

  // post: MSAA render -> depth of field -> bloom -> tone map + sRGB -> grade (vignette, grain)
  const rt = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 4 });
  const composer = new EffectComposer(renderer, rt);
  composer.setPixelRatio(1);
  composer.setSize(W, H);
  composer.addPass(new RenderPass(scene, camera));
  const L = story.look || {};
  let bokeh = null;
  if (L.dof) {
    bokeh = new BokehPass(scene, camera, { focus: 20, aperture: L.dof.aperture ?? 0.002, maxblur: L.dof.maxblur ?? 0.006 });
    // transparent shells must not write the DOF depth (the whole interior would take the shell's focus)
    const origRender = bokeh.render.bind(bokeh);
    bokeh.render = (...a) => { const hidden = []; scene.traverse(o => { if (o.visible && o.userData.noDepth) { o.visible = false; hidden.push(o); } }); try { origRender(...a); } finally { hidden.forEach(o => (o.visible = true)); } };
    composer.addPass(bokeh);
  }
  const bloom = new UnrealBloomPass(new THREE.Vector2(W, H), L.bloom?.strength ?? 0.7, L.bloom?.radius ?? 0.55, L.bloom?.threshold ?? 0.62);
  composer.addPass(bloom);
  composer.addPass(new OutputPass());
  const grade = new ShaderPass({
    uniforms: { tDiffuse: { value: null }, uFrame: { value: 0 }, uVig: { value: L.vignette ?? 0.32 }, uGrain: { value: L.grain ?? 0.025 }, uRes: { value: new THREE.Vector2(W, H) }, uGlow: { value: new THREE.Color(L.backGlow ?? '#000000') } },
    vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
    fragmentShader: `uniform sampler2D tDiffuse; uniform float uFrame, uVig, uGrain; uniform vec2 uRes; uniform vec3 uGlow; varying vec2 vUv;
      float h(vec2 p){ p = fract(p * vec2(443.897, 441.423)); p += dot(p, p.yx + 19.19); return fract((p.x + p.y) * p.x); }
      void main(){ vec4 c = texture2D(tDiffuse, vUv); vec2 q = vUv - 0.5; q.x *= uRes.x / uRes.y;
        float v = 1.0 - uVig * smoothstep(0.35, 1.05, length(q));
        float g = (h(vUv * uRes + uFrame * 17.0) - 0.5) * uGrain;
        vec3 back = uGlow * (1.0 - smoothstep(0.0, 0.95, length(q))) * (1.0 - clamp(dot(c.rgb, vec3(0.33)) * 3.0, 0.0, 1.0)); // soft backlight where the frame is dark
        gl_FragColor = vec4((c.rgb + back) * v + g, 1.0); }`,
  });
  composer.addPass(grade);

  // subject
  const ctx = { THREE, scene, camera, renderer, story, rng, clamp, lerp, smooth, ease, win, env };
  const subject = await build(ctx);
  const anchors = subject.anchors || {};
  const cam = cameraPath(story.camera, anchors);

  // ---------- overlay: labels, texts, scale bar ----------
  overlay.innerHTML = `<svg class="lines" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"></svg>`;
  const svg = overlay.querySelector('svg');
  const NS = 'http://www.w3.org/2000/svg';
  const mk = (tag, cls, parent = overlay) => { const e = document.createElement(tag); if (cls) e.className = cls; parent.appendChild(e); return e; };
  const labels = (story.labels || []).map((lb, i) => {
    const el = mk('div', `label ${lb.small ? 'is-small' : ''}`);
    el.dataset.id = lb.id;
    if (!lb.small) mk('div', 'label-idx', el).textContent = lb.index ?? String(i + 1).padStart(2, '0');
    const name = mk('div', 'label-name', el); name.textContent = lb.name;
    let fact = null; if (lb.fact) { fact = mk('div', 'label-fact', el); fact.textContent = lb.fact; }
    const g = document.createElementNS(NS, 'g'); svg.appendChild(g);
    const ring = document.createElementNS(NS, 'circle'); ring.setAttribute('class', 'ring'); ring.setAttribute('r', lb.small ? 7 : 10); g.appendChild(ring);
    const dot = document.createElementNS(NS, 'circle'); dot.setAttribute('class', 'dot'); dot.setAttribute('r', lb.small ? 3 : 4); g.appendChild(dot);
    const path = document.createElementNS(NS, 'path'); path.setAttribute('class', 'leader'); g.appendChild(path);
    return { lb, el, name, fact, g, ring, dot, path, w: 0, h: 0 };
  });
  const texts = (story.texts || []).map(tx => { const el = mk('div', `text ${tx.class || ''}`); el.textContent = tx.text; Object.assign(el.style, tx.style || {}); return { tx, el, fontPx: [0] }; });
  const sb = story.scaleBar ? (() => { const el = mk('div', 'scalebar'); const bar = mk('div', 'scalebar-bar', el); const txt = mk('div', 'scalebar-text', el); return { el, bar, txt }; })() : null;

  // fonts and layout must be final before the first measured frame
  await document.fonts.ready;
  for (const f of story.fonts || []) await document.fonts.load(f);
  const fpx = (el) => parseFloat(getComputedStyle(el).fontSize);
  for (const l of labels) { l.w = l.el.offsetWidth; l.h = l.el.offsetHeight; l.fontPx = [fpx(l.name), ...(l.fact ? [fpx(l.fact)] : [])]; }
  for (const x of texts) x.fontPx = [fpx(x.el)];
  if (sb) sb.fontPx = [fpx(sb.txt)];

  const v3 = new THREE.Vector3();
  const project = (p) => { v3.copy(p).project(camera); return [(v3.x * 0.5 + 0.5) * W, (-v3.y * 0.5 + 0.5) * H, v3.z]; };
  const SAFE = story.safe ?? { x: 96, top: 80, bottom: 96 };
  const visible = [];

  const inFrame = (x, y, m = 40) => smooth(Math.min(x - m, W - m - x, y - m, H - m - y) / 120 + 0.5);
  const pastCam = new THREE.PerspectiveCamera(30, W / H, 0.02, 400), pv = new THREE.Vector3();
  const leadAt = (p, tt) => { const c = cam(Math.max(0, tt)); pastCam.position.set(...c.pos); pastCam.fov = c.fov; pastCam.up.set(0, 1, 0); pastCam.lookAt(...c.look); pastCam.updateProjectionMatrix(); pastCam.updateMatrixWorld();
    pv.copy(p).project(pastCam); return pv.z > 1 ? 0 : inFrame((pv.x * 0.5 + 0.5) * W, (-pv.y * 0.5 + 0.5) * H); };
  // column layout (end cards): labels with lb.column = 'left'|'right' stack in a column at story.columns[side],
  // sorted by their anchor's screen height so leaders do not cross, at least `gap` px apart
  function layoutColumns() {
    for (const side of ['left', 'right']) {
      // every tag of the column is laid out from the start (even before it fades in), so nothing re-flows
      const items = labels.filter(l => l.lb.column === side && l._ay !== undefined).sort((p, q) => p._ay - q._ay);
      if (!items.length) continue;
      const gap = story.columnGap ?? 26; let y = -1e9;
      for (const it of items) { it._y = Math.max(it._ay - it.h / 2, y, SAFE.top); y = it._y + it.h + gap; }
      const over = y - gap - (H - SAFE.bottom - 14); if (over > 0) items.forEach(it => (it._y -= over));
      const cx = (story.columns || {})[side] ?? (side === 'left' ? W * 0.28 : W * 0.72);
      items.forEach(it => (it._x = side === 'left' ? cx - it.w : cx));
    }
  }
  function poseLabels(t) {
    for (const l of labels) {
      const { lb } = l; l._on = false; l._ay = undefined;
      l._a = env(t, lb.in, lb.out, 0.3, 0.35);
      if (l._a <= 0.001 && !(lb.column && t >= lb.in - 2 && t < lb.out)) continue;
      const anchor = typeof lb.anchor === 'string' ? anchors[lb.anchor] : new THREE.Vector3(...lb.anchor);
      if (!anchor) throw new Error(`label ${lb.id}: unknown anchor ${lb.anchor}`);
      [l._ax, l._ay, l._az] = project(anchor); l._on = l._az <= 1;
      // the leader fades as soon as the anchor leaves the frame; the text lingers only while the anchor was on
      // screen within the last `linger` seconds (camera pose at t - linger, so it stays a pure function of t)
      l._lead = l._on ? inFrame(l._ax, l._ay) : 0;
      if (!lb.column) l._a *= Math.max(l._lead, leadAt(anchor, t - (story.linger ?? 0.25)));
      if (!l._on) { l._ax = W / 2; l._ay = H / 2; l._on = l._a > 0.001; }
    }
    layoutColumns();
    for (const l of labels) {
      const { lb } = l;
      const a = l._a;
      l.el.style.opacity = 0; l.g.style.opacity = 0;
      if (!l._on || a <= 0.001) continue;
      const ax = l._ax, ay = l._ay;
      const k = t - lb.in; // seconds since in
      const side = lb.side === 'left' ? -1 : 1;
      const [ox, oy] = lb.offset || [side * 190, -150];
      // the text block sits above a horizontal rule; the leader runs from the anchor to the rule's near end
      let x = side > 0 ? ax + ox : ax + ox - l.w; let y = ay + oy - l.h;
      if (lb.fixed) { x = lb.fixed[0] >= 0 ? lb.fixed[0] : W + lb.fixed[0] - l.w; y = lb.fixed[1]; } // negative x = from the right edge
      if (lb.column) { x = l._x; y = l._y; }
      x = clamp(x, SAFE.x, W - SAFE.x - l.w); y = clamp(y, SAFE.top, H - SAFE.bottom - l.h - 14);
      const ruleY = y + l.h + 10, ex = side > 0 ? x - 6 : x + l.w + 6, fx = side > 0 ? x + l.w : x;
      const pin = lb.small ? 1 : smooth(k / 0.25), d1 = lb.small ? 1 : smooth((k - 0.1) / 0.3), d2 = lb.small ? 1 : smooth((k - 0.3) / 0.35);
      const mx = lerp(ax, ex, d1), my = lerp(ay, ruleY, d1);
      l.path.setAttribute('d', `M${ax.toFixed(1)},${ay.toFixed(1)} L${mx.toFixed(1)},${my.toFixed(1)}` + (d1 >= 1 ? ` L${lerp(ex, fx, d2).toFixed(1)},${ruleY.toFixed(1)}` : ''));
      l.ring.setAttribute('cx', ax); l.ring.setAttribute('cy', ay); l.ring.setAttribute('transform', `translate(${ax} ${ay}) scale(${pin}) translate(${-ax} ${-ay})`);
      l.dot.setAttribute('cx', ax); l.dot.setAttribute('cy', ay);
      l.g.style.opacity = a * l._lead;
      const ty = lb.small ? 0 : (1 - ease.outCubic((k - 0.15) / 0.45)) * 26;
      l.el.style.transform = `translate(${x.toFixed(1)}px, ${(y + ty).toFixed(1)}px)`;
      l.el.style.opacity = a * (lb.small ? 1 : smooth((k - 0.15) / 0.3));
      if (l.fact) l.fact.style.opacity = lb.small ? 1 : smooth((k - 0.25) / 0.3);
      visible.push({ kind: 'label', id: lb.id, factId: lb.factId, text: [lb.name, lb.fact].filter(Boolean), ui: lb.small ? [] : [lb.index ?? String(labels.indexOf(l) + 1).padStart(2, '0')], fontPx: l.fontPx, role: lb.small ? 'tag' : 'label', box: [x, y, l.w, l.h], anchor: [ax, ay], opacity: +a.toFixed(3) });
    }
  }
  function poseTexts(t) {
    for (const { tx, el, fontPx } of texts) {
      const a = env(t, tx.in, tx.out, tx.fade ?? 0.45, tx.fade ?? 0.35);
      el.style.opacity = a;
      const k = ease.outCubic((t - tx.in) / 0.7);
      el.style.transform = `translateY(${((1 - k) * (tx.rise ?? 18)).toFixed(1)}px)`;
      if (a > 0.001) { const r = el.getBoundingClientRect(), o = root.getBoundingClientRect(); visible.push({ kind: 'text', id: tx.id, factId: tx.factId, text: [tx.text], fontPx, role: tx.role || (/title/.test(tx.class || '') ? 'title' : 'note'), box: [r.left - o.left, r.top - o.top, r.width, r.height], opacity: +a.toFixed(3) }); }
    }
  }
  function poseScaleBar(t, look) {
    if (!sb) return;
    // hidden where the drawing is deliberately not to scale (e.g. enlarged ribosomes), see the fact sheet
    const a = (story.scaleBar.hide || []).reduce((acc, [h0, h1]) => acc * (1 - env(t, h0, h1, 0.3, 0.3)), env(t, story.scaleBar.in, story.scaleBar.out, 0.5, 0.4));
    sb.el.style.opacity = a;
    if (a <= 0.001) return;
    const s = scaleBar(camera, look, H, story.scaleBar);
    sb.bar.style.width = `${s.px.toFixed(1)}px`; sb.txt.textContent = s.text;
    const r = sb.el.getBoundingClientRect(), o = root.getBoundingClientRect();
    visible.push({ kind: 'scalebar', id: 'scalebar', factId: 'SB', text: [s.text], fontPx: sb.fontPx, role: 'note', box: [r.left - o.left, r.top - o.top, r.width, r.height], opacity: +a.toFixed(3) });
  }

  const look = new THREE.Vector3();
  function render(t) {
    t = clamp(t, 0, story.duration);
    visible.length = 0;
    const c = cam(t);
    camera.position.set(...c.pos); look.set(...c.look); camera.fov = c.fov; camera.up.set(0, 1, 0);
    camera.lookAt(look); camera.updateProjectionMatrix(); camera.updateMatrixWorld();
    subject.update(t, { camera, look });
    if (bokeh) { const u = bokeh.uniforms || bokeh.materialBokeh.uniforms; u.focus.value = camera.position.distanceTo(look); }
    grade.uniforms.uFrame.value = Math.round(t * story.fps) % 97;
    composer.render();
    poseLabels(t); poseTexts(t); poseScaleBar(t, look);
    return t;
  }

  const film = {
    fps: story.fps, duration: story.duration, width: W, height: H, render,
    labels: () => JSON.parse(JSON.stringify(visible)),
    anchors: () => Object.fromEntries(Object.entries(anchors).map(([k, v]) => [k, v.toArray().map(x => +x.toFixed(2))])),
    camera: (t) => cam(t),
    // debug: screen position of an anchor at time t (for choosing label anchors): [x, y, inFront]
    project: (name, t) => { const a = anchors[name], c = cam(t); pastCam.position.set(...c.pos); pastCam.fov = c.fov; pastCam.up.set(0, 1, 0); pastCam.lookAt(...c.look); pastCam.updateProjectionMatrix(); pastCam.updateMatrixWorld(); pv.copy(a).project(pastCam); return [Math.round((pv.x * 0.5 + 0.5) * W), Math.round((-pv.y * 0.5 + 0.5) * H), pv.z < 1]; },
  };
  // HyperFrames three adapter: render exactly the seeked time
  window.addEventListener('hf-seek', (e) => render(e.detail.time));
  render(window.__hfThreeTime || 0);
  if (dev) devScrubber(film);
  return film;
}

function devScrubber(film) {
  const bar = document.createElement('div'); bar.className = 'dev';
  bar.innerHTML = `<button>play</button><input type="range" min="0" max="${film.duration}" step="${1 / film.fps}" value="0"><span>0.00</span>`;
  document.body.appendChild(bar);
  const [btn, range, out] = bar.children; let playing = false, t0 = 0, s0 = 0;
  const show = (t) => { film.render(t); range.value = t; out.textContent = t.toFixed(2); };
  range.oninput = () => { playing = false; show(+range.value); };
  const loop = (now) => { if (!playing) return; const t = s0 + (now - t0) / 1000; show(t % film.duration); requestAnimationFrame(loop); }; // wall clock in the dev view only
  btn.onclick = () => { playing = !playing; if (playing) { t0 = performance.now(); s0 = +range.value; requestAnimationFrame(loop); } };
  addEventListener('keydown', (e) => { if (e.key === ' ') btn.onclick(); if (e.key === 'ArrowRight') show(+range.value + 1 / film.fps); if (e.key === 'ArrowLeft') show(+range.value - 1 / film.fps); });
}
