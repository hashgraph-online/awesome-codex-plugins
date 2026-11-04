import * as THREE from 'three';
import { buildSets } from './sets.js';
import { SHOTS } from './shots.js';
import { Rig, makePose, poseToJSON, applyPose } from './rig.js';
import { autoCam, subjectOf, SIZE_ORDER } from './autocam.js';

const $ = s => document.querySelector(s);
const qs = new URLSearchParams(location.search);
// storyboards are often model-written: escape every value that goes into innerHTML
const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

// ------------------------------------------------------------------ config + storyboard
// config.json lives next to index.html; its paths are relative to this folder (the server serves the project root).
const cfg = await (await fetch('config.json', { cache: 'no-store' })).json();
const sb = await (await fetch(cfg.storyboard || '../storyboard.json', { cache: 'no-store' })).json();
const TITLE = cfg.title || sb.title || 'Previz';
const BPM = cfg.bpm ?? sb.bpm ?? null;
const BEAT = BPM ? 60 / BPM : 0.5;                     // anim helpers always get a beat; without a song it is 0.5 s
const PER_BAR = cfg.beatsPerBar || 4;
const [AW, AH] = String(cfg.aspect || sb.aspect || '9:16').split(':').map(Number);
const AR = AW / AH;
const SAFE = cfg.safe || (AR < 1 ? { top: 0.1, bottom: 0.2 } : { top: 0.05, bottom: 0.05 }); // vertical: social-app UI zones
const EXPORT_SIZE = cfg.export || (AR < 1 ? { width: 480, height: Math.round(480 / AR / 2) * 2 } : { width: Math.round(480 * AR / 2) * 2, height: 480 });
const SCALE = { human: 1.8, ...(cfg.scale || {}) };   // reference heights (m) for shot-size maths
const PALETTE = ['#ff7a2f', '#2ee6ff', '#8a5cff', '#ff3df2', '#3dff9a', '#ffb020', '#6a8cff', '#ff2a3d', '#c8ff3d', '#8f96a3'];
const SCENES = { ...(cfg.scenes || {}) };
for (const s of sb.shots) if (!SCENES[s.scene]) {
  const n = Object.keys(SCENES).length;
  SCENES[s.scene] = { label: String(s.scene || 'scene').replace(/_/g, ' '), color: PALETTE[n % PALETTE.length] };
}
const EASE = {
  linear: k => k, inOut: k => k * k * (3 - 2 * k), in: k => k * k, out: k => 1 - (1 - k) * (1 - k),
  whip: k => (k < 0.5 ? 16 * k ** 5 : 1 - Math.pow(-2 * k + 2, 5) / 2), hold: () => 0,
};
const EASE_LABEL = { linear: 'linear', inOut: 'ease in-out', in: 'ease in', out: 'ease out', whip: 'whip', hold: 'hold on START' };
document.title = `Previz · ${TITLE}`;
document.documentElement.style.setProperty('--ar', `${AW} / ${AH}`);

let saved = { shots: {} };
try { const r = await fetch('data/edits.json', { cache: 'no-store' }); if (r.ok) saved = await r.json(); } catch { /* first run */ }
const camFromJSON = c => ({ a: makePose(c.a.p, c.a.t, c.a.fov, c.a.roll || 0), b: makePose(c.b.p, c.b.t, c.b.fov, c.b.roll || 0), ease: c.ease || 'inOut' });
const camToJSON = c => ({ a: poseToJSON(c.a), b: poseToJSON(c.b), ease: c.ease });

// ------------------------------------------------------------------ three
const canvas = $('#gl');
const EXPORT = qs.has('export');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: qs.has('shot') || EXPORT });
renderer.setPixelRatio(EXPORT ? 1 : Math.min(2, devicePixelRatio));
renderer.setScissorTest(true);
renderer.outputColorSpace = THREE.SRGBColorSpace;
const sets = buildSets();
const SET_IDS = Object.keys(sets);

// Shots: timing and text come from the storyboard; js/shots.js adds animation and hand-made cameras;
// a shot without a camera gets one from its storyboard "camera" words (autocam.js); data/edits.json overrides both.
const shots = sb.shots.map((s, i) => {
  const d = SHOTS[s.id] || {};
  let setId = s.set || d.set || SET_IDS[0], warn = '';
  if (!sets[setId]) { warn = `unknown set "${setId}" (built: ${SET_IDS.join(', ')}), shown in ${SET_IDS[0]}`; console.warn(s.id, warn); setId = SET_IDS[0]; }
  const sh = { ...s, ...d, set: setId, i, dur: s.end - s.start, shake: d.shake || s.shake || [], warn };
  sh.line = s.line ?? s.lyric ?? '';
  sh.overlay = s.overlay ?? d.overlay ?? '';
  // a broken anim must not stop the app: log it once, show it in the panel, keep rendering the static set
  sh.anim = d.anim ? (S, c) => { try { d.anim(S, c); } catch (e) { if (!sh.warn) console.error(s.id, e); sh.warn = 'anim error: ' + e.message; } } : () => {};
  const S = sets[setId];
  sh.defCam = d.cam || autoCam(S, sh, lt => {
    S.reset();
    if (lt != null) sh.anim(S, { k: THREE.MathUtils.clamp(lt / sh.dur, 0, 1), lt, dur: sh.dur, T: s.start + lt, camPos: new THREE.Vector3(), beat: BEAT, sh });
  });
  const ed = saved.shots?.[s.id] || {};
  return Object.assign(sh, { cam: camFromJSON(ed.cam || sh.defCam), status: ed.status || '', note: ed.note || '' });
});
const DURATION = sb.duration || shots[shots.length - 1].end;

const shotCam = new THREE.PerspectiveCamera(40, AR, 0.01, 4000);
const mapCam = new THREE.PerspectiveCamera(50, 1, 0.01, 6000);
mapCam.layers.enable(1);

// ghosts: start/end frustum of every shot, drawn only in the map (layer 1, the shot camera never sees them)
function textSprite(text, color) {
  const c = document.createElement('canvas'); c.width = 128; c.height = 48;
  const x = c.getContext('2d');
  x.fillStyle = 'rgba(10,12,20,0.75)'; x.fillRect(0, 0, 128, 48);
  x.fillStyle = color; x.font = 'bold 30px ui-monospace, Menlo, monospace'; x.textAlign = 'center'; x.textBaseline = 'middle';
  x.fillText(text, 64, 25);
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(c), depthTest: false, transparent: true }));
  s.renderOrder = 20; s.layers.set(1);
  return s;
}
const farOf = sh => sh.helperFar || sets[sh.set].helperFar || 1;
for (const sh of shots) {
  const set = sets[sh.set], far = farOf(sh);
  const mk = () => {
    const c = new THREE.PerspectiveCamera(40, AR, far * 0.02, far);
    const h = new THREE.CameraHelper(c); h.layers.set(1);
    set.scene.add(c, h);
    return { c, h };
  };
  sh.ghost = { a: mk(), b: mk() };
  sh.ghost.path = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]), new THREE.LineDashedMaterial({ color: 0xffffff, dashSize: far * 0.1, gapSize: far * 0.06 }));
  sh.ghost.path.layers.set(1); set.scene.add(sh.ghost.path);
  sh.ghost.label = textSprite(sh.id, SCENES[sh.scene]?.color || '#fff');
  sh.ghost.label.scale.set(far * 0.5, far * 0.19, 1);
  set.scene.add(sh.ghost.label);
}
const live = { c: new THREE.PerspectiveCamera(40, AR, 0.01, 1) };
live.h = new THREE.CameraHelper(live.c); live.h.layers.set(1);
live.h.setColors(new THREE.Color(0xffd23d), new THREE.Color(0xffd23d), new THREE.Color(0xffffff), new THREE.Color(0xffd23d), new THREE.Color(0xffd23d));

function updateGhost(sh, current) {
  const g = sh.ghost;
  for (const k of ['a', 'b']) {
    applyPose(g[k].c, sh.cam[k]);
    g[k].c.updateProjectionMatrix(); g[k].c.updateMatrixWorld(); g[k].h.update();
    const col = new THREE.Color(current ? (k === 'a' ? 0x3dff9a : 0xff5315) : 0x5a6275);
    g[k].h.setColors(col, col, col, col, col);
    g[k].h.visible = current || state.allGhosts;
  }
  g.path.geometry.setFromPoints([sh.cam.a.p, sh.cam.b.p]); g.path.computeLineDistances();
  g.path.material.color.setHex(current ? 0xffffff : 0x5a6275);
  g.path.visible = current || state.allGhosts;
  g.label.position.copy(sh.cam.a.p).add(new THREE.Vector3(0, farOf(sh) * 0.35, 0));
  g.label.visible = current || state.allGhosts;
}

// ------------------------------------------------------------------ state
const state = {
  time: 0, playing: false, loop: false, frame: false, cinema: qs.has('cinema'), onion: false, guides: true,
  allGhosts: true, dirty: false, cur: null,
};
const editPose = makePose([0, 0, 0], [0, 0, -1]);
const mapPoses = {};

const shotRig = new Rig($('#view-shot'), { onChange: () => frameUI() });
shotRig.enabled = false;
const mapRig = new Rig($('#view-map'));

// The track is loaded as a blob: seeking works without HTTP Range support on the local server.
const audio = new Audio();
let audioOK = false;
const AUDIO = cfg.audio ?? (sb.song ? '../' + sb.song : null);
if (AUDIO) fetch(AUDIO).then(r => (r.ok ? r.blob() : Promise.reject(r.status))).then(b => {
  audio.src = URL.createObjectURL(b); audioOK = true;
}).catch(() => ($('#audio-warn').hidden = false));

const shotAt = t => shots.find(s => t >= s.start && t < s.end) || shots[shots.length - 1];

function evalCam(sh, lt) {
  const k = THREE.MathUtils.clamp(lt / sh.dur, 0, 1), e = (EASE[sh.cam.ease] || EASE.inOut)(k);
  const { a, b } = sh.cam;
  const pose = { p: a.p.clone().lerp(b.p, e), t: a.t.clone().lerp(b.t, e), fov: a.fov + (b.fov - a.fov) * e, roll: a.roll + (b.roll - a.roll) * e };
  for (const at of sh.shake) {
    const d = lt - at;
    if (d < 0 || d > 0.4) continue;
    const amp = pose.p.distanceTo(pose.t) * 0.035 * Math.exp(-d * 9);
    const n = new THREE.Vector3(Math.sin(d * 97), Math.sin(d * 71 + 1), Math.sin(d * 83 + 2)).multiplyScalar(amp);
    pose.p.add(n); pose.t.add(n.multiplyScalar(1.5));
  }
  return pose;
}

// ------------------------------------------------------------------ shot description (for the camera plan)
// Shot size is judged against the shot's main subject: config.scale[sh.ref | set.ref] (a 1.8 m person by default).
// Without an explicit ref, a shot framed on an object (product, car) is judged by that object's own height.
function refOf(sh) {
  const name = sh.ref || sets[sh.set].ref;
  if (name) return [SCALE[name] ?? 1.8, name === 'human' ? '' : `(by ${name})`, false];
  const { name: sub, obj } = subjectOf(sets[sh.set], sh);
  if (obj && !obj.userData.j && obj.userData.height) return [SCALE[sub] ?? obj.userData.height, `(by ${sub})`, true];
  return [SCALE.human, '', false];
}
const SIZE_NAMES = { ECU: 'extreme close-up', CU: 'close-up', MCU: 'medium close-up', MS: 'medium', MLS: 'medium long', FS: 'full', WS: 'wide', EWS: 'extreme wide' };
function sizeOf(pose, refH = 1.8, object = false) {
  const h = 2 * pose.p.distanceTo(pose.t) * Math.tan(THREE.MathUtils.degToRad(pose.fov) / 2); // frame height at the target
  const r = refH / h; // how many frame-heights the subject would take
  if (object) { // an object "fills the frame" at CU, a person's head does
    const k = r >= 2 ? 'ECU' : r >= 0.75 ? 'CU' : r >= 0.58 ? 'MCU' : r >= 0.45 ? 'MS' : r >= 0.35 ? 'MLS' : r >= 0.25 ? 'FS' : r >= 0.07 ? 'WS' : 'EWS';
    return [k, SIZE_NAMES[k]];
  }
  if (r >= 4.5) return ['ECU', 'extreme close-up'];
  if (r >= 2.6) return ['CU', 'close-up'];
  if (r >= 1.8) return ['MCU', 'medium close-up'];
  if (r >= 1.25) return ['MS', 'medium'];
  if (r >= 0.9) return ['MLS', 'medium long'];
  if (r >= 0.5) return ['FS', 'full'];
  if (r >= 0.12) return ['WS', 'wide'];
  return ['EWS', 'extreme wide'];
}
// Full-frame-equivalent focal length: 36 mm along the long side of the frame (24 mm along the short side).
const FRAME_MM = AR < 1 ? 36 : 24;
const lensMM = fov => Math.round((FRAME_MM / 2) / Math.tan(THREE.MathUtils.degToRad(fov) / 2));
function angleOf(pose) {
  const d = pose.t.clone().sub(pose.p).normalize();
  const deg = THREE.MathUtils.radToDeg(Math.asin(d.y));
  if (deg < -55) return 'top-down';
  if (deg < -12) return 'high angle';
  if (deg > 12) return 'low angle';
  return 'eye level';
}
function moveOf(sh) {
  const { a, b } = sh.cam, out = [];
  const dist = a.p.distanceTo(b.p), scale = (a.p.distanceTo(a.t) + b.p.distanceTo(b.t)) / 2;
  const da = a.t.clone().sub(a.p).normalize(), db = b.t.clone().sub(b.p).normalize();
  const turn = THREE.MathUtils.radToDeg(da.angleTo(db));
  if (dist > scale * 0.04) {
    const m = b.p.clone().sub(a.p), along = m.dot(da) / dist;
    const orbitDeg = THREE.MathUtils.radToDeg(a.p.clone().sub(a.t).angleTo(b.p.clone().sub(b.t)));
    if (Math.abs(m.y) / dist > 0.7) out.push(m.y > 0 ? 'crane up' : 'crane down');
    else if (orbitDeg > 8 && a.t.distanceTo(b.t) < scale * 0.2) out.push(`orbit ${Math.round(orbitDeg)}°`);
    else if (along > 0.6) out.push('push in');
    else if (along < -0.6) out.push('pull out');
    else out.push('truck');
  }
  if (turn > 4 && !out.some(x => x.startsWith('orbit'))) out.push(`pan/tilt ${Math.round(turn)}°`);
  if (Math.abs(b.fov - a.fov) > 2) out.push(b.fov < a.fov ? 'zoom in' : 'zoom out');
  if (Math.abs(b.roll - a.roll) > 2) out.push(`roll ${Math.round(b.roll - a.roll)}°`);
  if (sh.shake.length) out.push('shake on impact');
  return out.length ? out.join(' + ') : 'static';
}
function describe(sh) {
  const [refH, by, obj] = refOf(sh), sa = sizeOf(sh.cam.a, refH, obj), sb_ = sizeOf(sh.cam.b, refH, obj);
  const size = (sa[0] === sb_[0] ? `${sa[0]} (${sa[1]})` : `${sa[0]} → ${sb_[0]}`) + (by ? ` ${by}` : '');
  const lens = lensMM(sh.cam.a.fov) === lensMM(sh.cam.b.fov) ? `${lensMM(sh.cam.a.fov)} mm` : `${lensMM(sh.cam.a.fov)}→${lensMM(sh.cam.b.fov)} mm`;
  return { size, lens, angle: angleOf(sh.cam.a), move: moveOf(sh), ease: EASE_LABEL[sh.cam.ease] };
}

// ------------------------------------------------------------------ timeline
const tl = $('#tl-shots'), tlScenes = $('#tl-scenes'), tlBars = $('#tl-bars');
const pct = t => (t / DURATION) * 100 + '%';
const GRID = BPM ? PER_BAR * BEAT : 1, MAJOR = BPM ? 4 : 5; // bars (every 4th bold) or seconds (every 5th bold)
for (let b = 0, t = 0; t < DURATION; b++, t = b * GRID) {
  const d = document.createElement('i'); d.style.left = pct(t); if (b % MAJOR === 0) d.className = 'major'; tlBars.appendChild(d);
}
let run = null;
for (const sh of shots) {
  if (!run || run.scene !== sh.scene) {
    run = { scene: sh.scene, start: sh.start, el: document.createElement('div') };
    run.el.className = 'tl-scene'; run.el.style.left = pct(sh.start);
    run.el.style.setProperty('--c', SCENES[sh.scene].color);
    run.el.textContent = SCENES[sh.scene].label;
    tlScenes.appendChild(run.el);
  }
  run.el.style.width = `calc(${pct(sh.end)} - ${pct(run.start)})`;
  const el = document.createElement('div');
  el.className = 'tl-shot'; el.style.left = pct(sh.start); el.style.width = `calc(${pct(sh.dur)} - 1px)`;
  el.style.setProperty('--c', SCENES[sh.scene].color);
  el.innerHTML = `<b>${esc(sh.id)}</b><span class="dot"></span>`;
  el.title = `${sh.id}${sh.line ? ' · ' + sh.line : ''}\n${sh.picture || ''}`;
  tl.appendChild(el); sh.tlEl = el;
}
const tlWrap = $('#timeline');
function scrubFrom(e) {
  const r = tl.getBoundingClientRect();
  seek(THREE.MathUtils.clamp((e.clientX - r.left) / r.width, 0, 0.99999) * DURATION);
}
tlWrap.addEventListener('pointerdown', e => { tlWrap.setPointerCapture(e.pointerId); tlWrap.dataset.drag = '1'; scrubFrom(e); });
tlWrap.addEventListener('pointermove', e => { if (tlWrap.dataset.drag) scrubFrom(e); });
tlWrap.addEventListener('pointerup', () => delete tlWrap.dataset.drag);
function tlStatus(sh) { sh.tlEl.dataset.status = sh.status; }
shots.forEach(tlStatus);

// ------------------------------------------------------------------ panel
function fmt(t) { const m = Math.floor(t / 60), s = (t % 60).toFixed(2).padStart(5, '0'); return `${m}:${s}`; }
const vecStr = v => v.toArray().map(x => x.toFixed(2)).join(', ');
const has = v => v != null && v !== '' && v !== '—';
const stillOf = sh => sh.still || (cfg.stills ? cfg.stills.replace('{id}', sh.id) : '');
function renderPanel() {
  const sh = state.cur, sc = SCENES[sh.scene];
  $('#p-id').textContent = sh.id;
  $('#p-scene').textContent = sc.label; $('#p-scene').style.setProperty('--c', sc.color);
  $('#p-time').textContent = `${fmt(sh.start)}–${fmt(sh.end)} · ${BPM ? `${sh.bars ?? +(sh.dur / (PER_BAR * BEAT)).toFixed(2)} bars · ` : ''}${sh.dur.toFixed(2)} s`;
  $('#p-lyric').textContent = has(sh.line) ? `“${sh.line}”` : 'no line';
  $('#p-picture').textContent = sh.picture || '';
  $('#p-meta').innerHTML = [
    has(sh.act) || has(sh.campbell) || has(sh.beat) ? esc([sh.act && `act ${sh.act}`, sh.campbell, sh.beat].filter(has).join(' · ')) : '',
    esc([sh.kind, sh.source].filter(has).join(' · ')), has(sh.film_ref) ? `ref: ${esc(sh.film_ref)}` : '',
    has(sh.camera) ? `camera note: ${esc(typeof sh.camera === 'string' ? sh.camera : JSON.stringify(sh.camera))}` : '',
    has(sh.overlay) ? `add in edit: ${esc(sh.overlay)}` : '', `set: ${esc(sets[sh.set].title)}`,
    sh.warn ? `<span class="warn">⚠ ${esc(sh.warn)}</span>` : '',
  ].filter(Boolean).map(x => `<div>${x}</div>`).join('');
  const still = stillOf(sh);
  $('#p-still').hidden = !still; $('#onion').src = still || '';
  if (still) $('#p-still').src = still;
  $('#p-still-cap').textContent = !still ? 'No still for this shot yet: the 3D frame is the reference.'
    : sh.needs_new_still ? 'Still is stale: the shot was rewritten, a new one is needed. Trust the 3D frame.'
    : 'Current still of the shot. "still" overlays it on the frame to compare composition.';
  $('#p-still-cap').classList.toggle('warn', !!sh.needs_new_still);
  renderCam();
  document.querySelectorAll('#p-status button').forEach(b => b.classList.toggle('on', b.dataset.s === sh.status));
  $('#p-note').value = sh.note;
}
$('#p-still').addEventListener('error', () => { $('#p-still').hidden = true; $('#p-still-cap').textContent = 'Still not found at ' + stillOf(state.cur); });
function renderCam() {
  const sh = state.cur, d = describe(sh);
  $('#p-spec').innerHTML = `<b>${d.size}</b> · ${d.angle} · ${d.lens}<br>${d.move} <span class="muted">(${d.ease})</span>`;
  for (const k of ['a', 'b']) {
    const c = sh.cam[k];
    $(`#p-${k}-p`).textContent = vecStr(c.p); $(`#p-${k}-t`).textContent = vecStr(c.t);
    $(`#p-${k}-fov`).value = c.fov.toFixed(1); $(`#p-${k}-roll`).value = c.roll.toFixed(1);
    $(`#p-${k}-mm`).textContent = `${lensMM(c.fov)} mm`;
  }
  $('#p-ease').value = sh.cam.ease;
  const changed = JSON.stringify(camToJSON(sh.cam)) !== JSON.stringify(camToJSON(camFromJSON(sh.defCam)));
  $('#p-reset').disabled = !changed;
  $('#p-changed').hidden = !changed;
}
for (const k of ['a', 'b']) {
  $(`#p-${k}-fov`).addEventListener('change', e => { state.cur.cam[k].fov = +e.target.value; touched(); });
  $(`#p-${k}-roll`).addEventListener('change', e => { state.cur.cam[k].roll = +e.target.value; touched(); });
}
$('#p-ease').addEventListener('change', e => { state.cur.cam.ease = e.target.value; touched(); });
$('#p-reset').addEventListener('click', () => { state.cur.cam = camFromJSON(state.cur.defCam); touched(); });
$('#p-go-a').addEventListener('click', () => enterFrame('a'));
$('#p-go-b').addEventListener('click', () => enterFrame('b'));
document.querySelectorAll('#p-status button').forEach(b => b.addEventListener('click', () => {
  const sh = state.cur; sh.status = sh.status === b.dataset.s ? '' : b.dataset.s; tlStatus(sh); markDirty(); renderPanel();
}));
$('#p-note').addEventListener('input', e => { state.cur.note = e.target.value; markDirty(); });
function touched() { markDirty(); updateGhost(state.cur, true); renderCam(); }

// ------------------------------------------------------------------ frame mode (edit the shot camera by looking through it)
function enterFrame(key) {
  const sh = state.cur;
  pause();
  if (key) { seek(key === 'a' ? sh.start + 1e-4 : sh.end - 1e-3); copyPose(editPose, sh.cam[key]); }
  else copyPose(editPose, evalCam(sh, state.time - sh.start));
  state.frame = true; shotRig.pose = editPose; shotRig.enabled = true;
  document.body.classList.add('framing');
  frameUI();
}
function exitFrame() { state.frame = false; shotRig.enabled = false; document.body.classList.remove('framing'); }
function copyPose(dst, src) { dst.p.copy(src.p); dst.t.copy(src.t); dst.fov = src.fov; dst.roll = src.roll; }
function frameUI() {
  $('#f-fov').value = editPose.fov; $('#f-fov-v').textContent = `${editPose.fov.toFixed(0)}° · ${lensMM(editPose.fov)} mm`;
  $('#f-roll').value = editPose.roll; $('#f-roll-v').textContent = `${editPose.roll.toFixed(0)}°`;
  const [refH, , obj] = refOf(state.cur), [abbr, name] = sizeOf(editPose, refH, obj);
  $('#f-size').textContent = `${abbr} · ${name} · ${angleOf(editPose)}`;
}
$('#f-fov').addEventListener('input', e => { editPose.fov = +e.target.value; frameUI(); });
$('#f-roll').addEventListener('input', e => { editPose.roll = +e.target.value; frameUI(); });
$('#f-to-a').addEventListener('click', () => { copyPose(state.cur.cam.a, editPose); touched(); flash('START written'); });
$('#f-to-b').addEventListener('click', () => { copyPose(state.cur.cam.b, editPose); touched(); flash('END written'); });
$('#f-exit').addEventListener('click', exitFrame);

// ------------------------------------------------------------------ transport
function seek(t) {
  state.time = THREE.MathUtils.clamp(t, 0, DURATION - 1e-3);
  state.loopShot = shotAt(state.time);
  if (audioOK) try { audio.currentTime = state.time; } catch { /* not loaded yet */ }
}
let clockRef = 0;
function play() {
  if (state.frame) exitFrame();
  state.playing = true; clockRef = performance.now(); state.loopShot = shotAt(state.time);
  if (audioOK) { audio.currentTime = state.time; audio.play().catch(() => (audioOK = false)); }
  document.body.classList.add('playing');
}
function pause() { state.playing = false; audio.pause(); document.body.classList.remove('playing'); }
function step(d) {
  const i = THREE.MathUtils.clamp(state.cur.i + d, 0, shots.length - 1);
  seek(shots[i].start + 1e-4);
  if (state.frame) enterFrame('a');
}
$('#b-play').addEventListener('click', () => (state.playing ? pause() : play()));
$('#b-prev').addEventListener('click', () => step(-1));
$('#b-next').addEventListener('click', () => step(1));
const toggles = {
  loop: ['#b-loop', 'loop'], cinema: ['#b-cinema', 'cinema'], onion: ['#b-onion', 'onion'], guides: ['#b-guides', 'guides'], allGhosts: ['#b-ghosts', 'allGhosts'],
};
function setToggle(name, v) {
  const [sel, key] = toggles[name]; state[key] = v ?? !state[key];
  $(sel).classList.toggle('on', state[key]);
  document.body.classList.toggle('is-' + key, state[key]); // prefixed: a body class equal to a component class once hid the page
  if (name === 'allGhosts') shots.forEach(s => updateGhost(s, s === state.cur));
  if (name === 'loop') state.loopShot = shotAt(state.time);
  onResize();
}
$('#onion-op').addEventListener('input', e => ($('#onion').style.opacity = e.target.value));
$('#b-frame').addEventListener('click', () => (state.frame ? exitFrame() : enterFrame()));
$('#b-map-home').addEventListener('click', () => mapFocus(true));
$('#b-save').addEventListener('click', save);
$('#b-export').addEventListener('click', exportPlan);

addEventListener('keydown', e => {
  if (e.target.matches('input, textarea, select')) { if (e.key === 'Escape') e.target.blur(); return; }
  const k = e.key.toLowerCase();
  if ((e.metaKey || e.ctrlKey) && k === 's') { e.preventDefault(); save(); return; }
  if (e.metaKey || e.ctrlKey) return;
  if ('wasdqe'.includes(k) && k.length === 1) { shotRig.keys.add(k); mapRig.keys.add(k); return; }
  if (e.key === 'Shift') { shotRig.keys.add('shift'); mapRig.keys.add('shift'); }
  if (e.code === 'Space') { e.preventDefault(); state.playing ? pause() : play(); }
  else if (e.key === 'ArrowRight') step(1);
  else if (e.key === 'ArrowLeft') step(-1);
  else if (k === 'f') state.frame ? exitFrame() : enterFrame();
  else if (k === '1') enterFrame('a');
  else if (k === '2') enterFrame('b');
  else if (e.key === 'Escape') exitFrame();
  else if (k === 'l') setToggle('loop');
  else if (k === 'c') setToggle('cinema');
  else if (k === 'o') setToggle('onion');
  else if (k === 'g') setToggle('guides');
  else if (k === 'h') setToggle('allGhosts');
  else if (k === 'm') mapFocus(true);
});
addEventListener('keyup', e => {
  const k = e.key === 'Shift' ? 'shift' : e.key.toLowerCase();
  shotRig.keys.delete(k); mapRig.keys.delete(k);
});
addEventListener('blur', () => { shotRig.keys.clear(); mapRig.keys.clear(); });

// ------------------------------------------------------------------ save / export
function markDirty() { state.dirty = true; $('#save-state').textContent = '● unsaved'; $('#save-state').className = 'dirty'; }
function flash(msg) { const t = $('#toast'); t.textContent = msg; t.classList.add('show'); clearTimeout(flash.h); flash.h = setTimeout(() => t.classList.remove('show'), 2200); }
function download(name, text, type) {
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([text], { type })); a.download = name; a.click();
}
function collect() {
  const out = { version: 1, updated: new Date().toISOString(), note: 'Overrides for js/shots.js and auto cameras. Camera keys: p = position, t = look-at target, fov = vertical deg, roll = deg.', shots: {} };
  for (const sh of shots) {
    const cam = camToJSON(sh.cam), changed = JSON.stringify(cam) !== JSON.stringify(camToJSON(camFromJSON(sh.defCam)));
    if (changed || sh.status || sh.note) out.shots[sh.id] = { ...(changed && { cam }), ...(sh.status && { status: sh.status }), ...(sh.note && { note: sh.note }) };
  }
  return out;
}
async function post(path, body) {
  const r = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body });
  if (!r.ok) throw new Error(r.status);
  return r.json();
}
async function save() {
  const text = JSON.stringify(collect(), null, 1);
  try {
    const r = await post('/api/save', text);
    state.dirty = false; $('#save-state').textContent = '✓ saved'; $('#save-state').className = '';
    flash('Saved: ' + r.path);
  } catch {
    download('edits.json', text, 'application/json');
    flash('Server not answering: downloaded edits.json, put it in data/');
  }
}
const PLAN_FILE = cfg.planFile || 'camera_plan.md';
function planMarkdown() {
  const rows = shots.map(sh => {
    const d = describe(sh), st = { ok: '✅ ok', fix: '✏️ fix' }[sh.status] || '—';
    const c = sh.cam;
    return `| ${sh.id} | ${fmt(sh.start)} | ${SCENES[sh.scene].label} | ${d.size} | ${d.angle} | ${d.lens} | ${d.move} | ${vecStr(c.a.p)} → ${vecStr(c.b.p)} | ${st} | ${(sh.note || '').replace(/\n/g, ' ')} |`;
  });
  const ok = shots.filter(s => s.status === 'ok').length, fix = shots.filter(s => s.status === 'fix').length;
  return `# Camera plan · ${TITLE}\n\nExported from the previz (${new Date().toISOString().slice(0, 16).replace('T', ' ')}). Approved ${ok}/${shots.length}, to fix ${fix}.\n` +
    `Shot size is judged against the main subject in a ${AW}:${AH} frame (a 1.8 m person unless noted); lens = full-frame equivalent.\n\n` +
    `| shot | time | scene | size | angle | lens | move | START → END position (m) | status | note |\n|---|---|---|---|---|---|---|---|---|---|\n${rows.join('\n')}\n`;
}
async function exportPlan() {
  const md = planMarkdown();
  try { const r = await post('/api/export', JSON.stringify({ name: PLAN_FILE, text: md })); flash('Exported: ' + r.path); }
  catch { download(PLAN_FILE, md, 'text/markdown'); flash('Downloaded ' + PLAN_FILE); }
}
addEventListener('beforeunload', e => { if (state.dirty) e.preventDefault(); });

// ------------------------------------------------------------------ layout + render loop
function layoutShotView() {
  const col = $('.col-shot'), main = $('main');
  if (EXPORT) { col.style.width = EXPORT_SIZE.width + 'px'; col.style.height = EXPORT_SIZE.height + 'px'; return; }
  const mh = main.clientHeight - 20, mw = main.clientWidth - 20;
  const maxW = state.cinema ? mw : mw * (AR < 1 ? 0.4 : 0.45);
  const w = Math.min(mh * AR, maxW);
  col.style.width = w + 'px'; col.style.height = w / AR + 'px';
}
function onResize() { layoutShotView(); renderer.setSize(innerWidth, innerHeight, false); }
addEventListener('resize', onResize);
new ResizeObserver(onResize).observe(document.body);

// Map camera: the set's mapHome, or framed around its subjects.
function homeOf(set) {
  if (set.mapHome) return makePose(set.mapHome[0], set.mapHome[1], 50);
  const b = new THREE.Box3();
  for (const o of Object.values(set.subjects || {})) b.expandByObject(o);
  const c = b.getCenter(new THREE.Vector3()), r = Math.max(2, b.getSize(new THREE.Vector3()).length());
  return makePose([c.x + r * 1.2, c.y + r * 0.9, c.z - r * 1.4], c.toArray(), 50);
}
function mapFocus(home) {
  const sh = state.cur, set = sets[sh.set];
  if (!mapPoses[sh.set]) mapPoses[sh.set] = homeOf(set);
  if (home) {
    if (set.mapFollowShot) { // sets made of separate islands: frame the current shot instead
      const tgt = sh.cam.a.t, off = sh.cam.a.p.clone().sub(tgt).setLength(farOf(sh) * 14);
      copyPose(mapPoses[sh.set], { p: tgt.clone().add(off).add(new THREE.Vector3(off.length() * 0.6, off.length() * 0.4, 0)), t: tgt.clone(), fov: 50, roll: 0 });
    } else copyPose(mapPoses[sh.set], homeOf(set));
  }
  mapRig.pose = mapPoses[sh.set];
}
// Labels flagged billboard always face the camera that is rendering.
const billboards = new Map();
function faceCamera(scene, cam) {
  if (!billboards.has(scene)) { const l = []; scene.traverse(o => o.userData.billboard && l.push(o)); billboards.set(scene, l); }
  const q = new THREE.Quaternion();
  for (const b of billboards.get(scene)) {
    b.parent.getWorldQuaternion(q);
    b.quaternion.copy(q.invert().multiply(cam.quaternion));
  }
}
function render(el, scene, cam, aspectFixed) {
  const r = el.getBoundingClientRect();
  if (r.width < 2 || r.height < 2) return;
  const x = r.left, y = innerHeight - r.bottom;
  renderer.setViewport(x, y, r.width, r.height); renderer.setScissor(x, y, r.width, r.height);
  if (!aspectFixed) { cam.aspect = r.width / r.height; cam.updateProjectionMatrix(); }
  scene.updateMatrixWorld();
  faceCamera(scene, cam);
  renderer.render(scene, cam);
}

let last = performance.now(), lastShot = null;
function selectShot(sh) {
  const prevSet = lastShot?.set;
  if (lastShot) updateGhost(lastShot, false);
  state.cur = sh; lastShot = sh;
  sets[sh.set].scene.add(live.c, live.h);
  live.c.far = farOf(sh) * 1.25;
  updateGhost(sh, true);
  if (prevSet !== sh.set || sets[sh.set].mapFollowShot) mapFocus(!!sets[sh.set].mapFollowShot);
  renderPanel();
}
const animCtx = (sh, lt, T, camPos) => ({ k: THREE.MathUtils.clamp(lt / sh.dur, 0, 1), lt, dur: sh.dur, T, camPos, beat: BEAT, sh });
const HUD = cfg.hud || [];
function frame(now) {
  const dt = Math.min(0.1, (now - last) / 1000); last = now;
  if (state.playing) {
    if (audioOK && !audio.paused) state.time = audio.currentTime;
    else { state.time += (now - clockRef) / 1000; }
    clockRef = now;
    if (state.loop && state.loopShot && state.time >= state.loopShot.end) seek(state.loopShot.start);
    if (state.time >= DURATION - 0.01) seek(0);
  }
  const sh = state.loop && state.playing && state.loopShot ? state.loopShot : shotAt(state.time);
  if (sh !== lastShot) selectShot(sh);
  const lt = state.time - sh.start, set = sets[sh.set];
  set.reset();
  shotRig.tick(dt); mapRig.tick(dt);
  const pose = state.frame ? editPose : evalCam(sh, lt);
  sh.anim(set, animCtx(sh, lt, state.time, pose.p));
  applyPose(shotCam, pose);
  applyPose(live.c, pose); live.c.updateProjectionMatrix(); live.c.updateMatrixWorld(); live.h.update();
  applyPose(mapCam, mapRig.pose);

  renderer.setClearColor(0x000000, 0); renderer.setScissor(0, 0, innerWidth, innerHeight); renderer.clear();
  live.h.visible = false;
  render($('#view-shot'), set.scene, shotCam, true);
  live.h.visible = true;
  if (!state.cinema) render($('#view-map'), set.scene, mapCam, false);

  // HUD
  $('#hud-id').textContent = sh.id;
  $('#hud-scene').textContent = SCENES[sh.scene].label;
  $('#hud-scene').style.setProperty('--c', SCENES[sh.scene].color);
  $('#hud-beat').textContent = BPM
    ? `${fmt(state.time)} · bar ${Math.floor(state.time / (PER_BAR * BEAT)) + 1}.${Math.floor((state.time / BEAT) % PER_BAR) + 1}`
    : fmt(state.time);
  $('#hud-beatdot').hidden = !BPM;
  $('#hud-beatdot').classList.toggle('on', (lt / BEAT) % 1 < 0.18);
  $('#hud-k').style.width = (lt / sh.dur) * 100 + '%';
  $('#hud-lyric').textContent = has(sh.line) ? sh.line : '';
  $('#hud-code').textContent = has(sh.overlay) ? 'ADD IN EDIT: ' + sh.overlay : '';
  const card = HUD.find(h => state.time >= (h.from ?? 0) && state.time < (h.to ?? DURATION));
  $('#hud-card').hidden = !card; if (card) { $('#hud-card').textContent = card.text; $('#hud-card').dataset.pos = card.pos || 'top'; }
  $('#playhead').style.left = pct(state.time);
  $('#t-now').textContent = `${fmt(state.time)} / ${fmt(DURATION)}`;
  requestAnimationFrame(frame);
}

// ------------------------------------------------------------------ static UI from config
$('#title').textContent = TITLE;
$('#subtitle').textContent = `· ${shots.length} shots · ${new Set(shots.map(s => s.scene)).size} scenes · ${AW}:${AH}${BPM ? ` · ${BPM} BPM` : ''}`;
$('#safe-top').style.height = SAFE.top * 100 + '%';
$('#safe-bottom').style.height = SAFE.bottom * 100 + '%';
$('#audio-warn').textContent = AUDIO ? 'audio did not load: run through serve.py and check config.audio' : '';
for (const name of Object.keys(toggles)) { $(toggles[name][0]).addEventListener('click', () => setToggle(name)); setToggle(name, state[toggles[name][1]]); }

// deep link: ?shot=s03&k=0.5 (also used for headless checks)
if (qs.has('shot')) {
  const sh = shots.find(s => s.id === qs.get('shot'));
  if (sh) state.time = sh.start + sh.dur * Math.min(0.999, +(qs.get('k') ?? 0.5));
}
selectShot(shotAt(state.time)); // synchronously, so keys pressed before the first frame have a shot
onResize();

// ------------------------------------------------------------------ clean export (reference video for video-to-video)
// ?export=1 shows only the shot view at EXPORT_SIZE with no HUD and no text; frames are driven from outside
// with app.exportFrame(id, localTime). Local time may run past the shot end to render a tail handle.
const textLabels = Object.values(sets).flatMap(s => { const l = []; s.scene.traverse(o => o.userData.label && l.push(o)); return l; });
function exportFrame(id, lt) {
  const sh = shots.find(s => s.id === id), set = sets[sh.set];
  if (sh !== lastShot) selectShot(sh);
  set.reset();
  const pose = evalCam(sh, lt);
  sh.anim(set, animCtx(sh, lt, sh.start + lt, pose.p));
  textLabels.forEach(l => (l.visible = false));
  applyPose(shotCam, pose);
  renderer.setClearColor(0x000000, 1); renderer.setScissor(0, 0, innerWidth, innerHeight); renderer.clear();
  render($('#view-shot'), set.scene, shotCam, true);
}
if (EXPORT) { document.body.classList.add('is-export'); onResize(); }
else requestAnimationFrame(frame);
window.app = { cfg, shots, sets, state, seek, save, exportFrame, exportSize: EXPORT_SIZE, describe, sizes: SIZE_ORDER };
