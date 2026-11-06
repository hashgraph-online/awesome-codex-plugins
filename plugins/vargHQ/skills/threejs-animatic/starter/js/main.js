// Review app: shot view + top-down set map with every camera's frustum, timeline, camera editor,
// approval, save and camera-plan export. ?export=1 switches to the clean capture view instead.
import * as THREE from 'three';
import { createFilm, createVideoRenderer, installExportHooks } from './film.js';
import { FILM, BEAT } from './shots.js';
import { labelSprite } from './props.js';
import { Rig, makePose, copyPose, applyPose, camFromJSON, camToJSON, describe, evalCam, lensMM, sizeOf, angleOf } from './camera.js';

const $ = s => document.querySelector(s);
const qs = new URLSearchParams(location.search);

let edits = {};
try { const r = await fetch('data/edits.json', { cache: 'no-store' }); if (r.ok) edits = await r.json(); } catch { /* first run */ }
// ?look=1: the optional look blockout (js/look.js); its images load before the first frame
const film = createFilm(edits, { look: qs.has('look') });
await film.ready;
const { set, shots } = film;

if (qs.has('export')) {
  // clean capture view: only the canvas, at the export size, no HUD, no labels
  document.body.classList.add('is-export');
  const w = +(qs.get('w') || FILM.export.width), h = +(qs.get('h') || FILM.export.height);
  const canvas = $('#gl');
  Object.assign(canvas.style, { width: w + 'px', height: h + 'px' });
  installExportHooks(film, createVideoRenderer(canvas, w, h));
} else review();

function review() {
  document.title = `${FILM.title} · animatic`;
  $('#title').textContent = FILM.title;
  const scene = set.scene, cam = film.camera;
  cam.aspect = FILM.aspect; cam.updateProjectionMatrix();
  const renderer = new THREE.WebGLRenderer({ canvas: $('#gl'), antialias: true });
  renderer.setPixelRatio(Math.min(2, devicePixelRatio));
  renderer.setScissorTest(true);
  renderer.outputColorSpace = THREE.SRGBColorSpace;

  // ---------------------------------------------------------------- map: top-down orthographic, -Z up
  const mapCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 100);
  mapCam.layers.enable(1); // ghosts, paths and ids live on layer 1: the shot camera never sees them
  const map = { cx: set.mapView.center[0], cz: set.mapView.center[1], half: set.mapView.half };
  const mapHome = () => Object.assign(map, { cx: set.mapView.center[0], cz: set.mapView.center[1], half: set.mapView.half });
  function placeMap(aspect) {
    Object.assign(mapCam, { left: -map.half * aspect, right: map.half * aspect, top: map.half, bottom: -map.half });
    mapCam.position.set(map.cx, 30, map.cz); mapCam.up.set(0, 0, -1); mapCam.lookAt(map.cx, 0, map.cz);
    mapCam.updateProjectionMatrix();
  }
  const mapEl = $('#view-map');
  mapEl.addEventListener('pointerdown', e => { mapEl.setPointerCapture(e.pointerId); map.drag = [e.clientX, e.clientY]; });
  mapEl.addEventListener('pointermove', e => {
    if (!map.drag) return;
    const s = (2 * map.half) / mapEl.clientHeight;
    map.cx -= (e.clientX - map.drag[0]) * s; map.cz -= (e.clientY - map.drag[1]) * s; map.drag = [e.clientX, e.clientY];
  });
  mapEl.addEventListener('pointerup', () => (map.drag = null));
  mapEl.addEventListener('wheel', e => { e.preventDefault(); map.half = THREE.MathUtils.clamp(map.half * Math.exp(e.deltaY * 0.001), 0.5, 60); }, { passive: false });

  // ---------------------------------------------------------------- ghosts: START/END frustum of every shot
  const FAR = 1.6, COL = { a: new THREE.Color(0x3dff9a), b: new THREE.Color(0xff8a3d), dim: new THREE.Color(0x4a5270), live: new THREE.Color(0xffd23d) };
  const helperCam = () => {
    const c = new THREE.PerspectiveCamera(40, FILM.aspect, 0.05, FAR), h = new THREE.CameraHelper(c);
    h.layers.set(1); scene.add(c, h);
    return { c, h };
  };
  for (const sh of shots) {
    sh.ghost = { a: helperCam(), b: helperCam() };
    sh.ghost.path = new THREE.Line(new THREE.BufferGeometry(), new THREE.LineDashedMaterial({ color: 0xffffff, dashSize: 0.1, gapSize: 0.07 }));
    sh.ghost.label = labelSprite(sh.id, { h: 0.22 });
    for (const o of [sh.ghost.path, sh.ghost.label]) { o.layers.set(1); scene.add(o); }
  }
  const live = helperCam();
  live.c.far = FAR * 1.4;
  live.h.setColors(COL.live, COL.live, COL.live, COL.live, COL.live);
  function updateGhost(sh, current) {
    const g = sh.ghost, show = current || state.all;
    for (const k of ['a', 'b']) {
      applyPose(g[k].c, sh.cam[k]);
      g[k].c.updateProjectionMatrix(); g[k].c.updateMatrixWorld(true); g[k].h.update();
      const c = current ? COL[k] : COL.dim;
      g[k].h.setColors(c, c, c, c, c);
      g[k].h.visible = show;
    }
    const still = { ...sh, shake: [] }, pts = [];
    for (let i = 0; i <= 16; i++) pts.push(evalCam(still, (i / 16) * sh.dur).p);
    g.path.geometry.setFromPoints(pts); g.path.computeLineDistances();
    g.path.material.color.copy(current ? new THREE.Color(0xffffff) : COL.dim);
    g.label.position.copy(sh.cam.a.p).add(new THREE.Vector3(0, 0.35, 0));
    g.path.visible = g.label.visible = show;
  }

  // ---------------------------------------------------------------- automatic frame checks
  // Out of the frame, blocked by something, camera inside geometry: the bugs a grey-box shows only
  // if somebody looks. Run at START, middle and END of each shot.
  const ray = new THREE.Raycaster();
  ray.camera = cam; // sprites (name tags) need it, or three logs an error on every raycast
  const statics = [];
  for (const g of [scene.getObjectByName('room'), set.o.table, set.o.chairA, set.o.chairB])
    g.traverse(m => { if (m.isMesh) statics.push({ name: nameOf(m), box: new THREE.Box3().setFromObject(m).expandByScalar(0.02) }); });
  // outermost named ancestor below the scene ('table', 'A', 'pillar'); plain room meshes are 'wall'
  function nameOf(o) { let n = ''; for (let x = o; x && x !== scene; x = x.parent) if (x.name && x.name !== 'room') n = x.name; return n || 'wall'; }
  const isPart = (o, root) => { for (let x = o; x; x = x.parent) if (x === root) return true; return false; };
  function subjectPoint(key) {
    const o = set.o[key];
    return (o.userData.j ? o.userData.j.head : o).getWorldPosition(new THREE.Vector3());
  }
  function checkShot(sh) {
    const out = [];
    for (const [tag, lt] of [['START', 1e-4], ['middle', sh.dur / 2], ['END', sh.dur - 1e-3]]) {
      const { pose } = film.pose(sh.start + lt, { shot: sh });
      cam.updateMatrixWorld();
      const inside = statics.find(s => s.box.containsPoint(pose.p));
      if (inside) out.push(`camera inside ${inside.name} at ${tag}`);
      for (const key of sh.subjects || []) {
        const w = subjectPoint(key), v = w.clone().project(cam), name = set.o[key].name;
        if (v.z > 1 || Math.abs(v.x) > 1 || Math.abs(v.y) > 1) { out.push(`${name} out of frame at ${tag}`); continue; }
        if (Math.abs(v.x) > 0.9 || Math.abs(v.y) > 0.9) out.push(`${name} on the frame edge at ${tag}`);
        ray.set(pose.p, w.clone().sub(pose.p).normalize()); ray.far = pose.p.distanceTo(w) - 0.12;
        const hit = ray.intersectObject(scene, true).find(h => h.object.isMesh && h.object.visible && !isPart(h.object, set.o[key]));
        if (hit) out.push(`${name} blocked by ${nameOf(hit.object)} at ${tag}`);
      }
    }
    return [...new Set(out)];
  }

  // ---------------------------------------------------------------- state, timeline
  const state = { time: 0, playing: false, loop: false, loopShot: null, framing: false, frameKey: null, all: true, click: false, dirty: false, cur: null };
  const D = FILM.duration, pct = t => (t / D) * 100 + '%';
  for (let i = 0, t = 0; t < D; i++, t = i * BEAT) {
    const el = document.createElement('i'); el.style.left = pct(t); if (i % 4 === 0) el.className = 'bar'; $('#tl-beats').appendChild(el);
  }
  for (const sh of shots) {
    const el = document.createElement('div');
    el.className = 'tl-shot'; el.style.left = pct(sh.start); el.style.width = `calc(${pct(sh.dur)} - 2px)`;
    el.textContent = sh.id; el.title = sh.picture; el.dataset.status = sh.status;
    $('#tl-shots').appendChild(el); sh.el = el;
  }
  const tl = $('#timeline');
  const scrub = e => { const r = tl.getBoundingClientRect(); seek(THREE.MathUtils.clamp((e.clientX - r.left) / r.width, 0, 0.9999) * D); };
  tl.addEventListener('pointerdown', e => { tl.setPointerCapture(e.pointerId); tl.dataset.drag = 1; if (state.framing) exitFrame(); scrub(e); });
  tl.addEventListener('pointermove', e => tl.dataset.drag && scrub(e));
  tl.addEventListener('pointerup', () => delete tl.dataset.drag);

  // ---------------------------------------------------------------- audio: the track, or a click on every beat
  // The track is fetched into a blob URL: a static server without HTTP Range support cannot seek audio.
  let audio = null, actx = null;
  if (FILM.audio) fetch(FILM.audio).then(r => (r.ok ? r.blob() : Promise.reject(r.status)))
    .then(b => { audio = new Audio(URL.createObjectURL(b)); }).catch(() => flash(`audio ${FILM.audio} not found: click track only`));
  function click(accent) {
    actx ||= new AudioContext();
    const o = actx.createOscillator(), g = actx.createGain(), t = actx.currentTime;
    o.frequency.value = accent ? 1600 : 1000; g.gain.setValueAtTime(0.25, t); g.gain.exponentialRampToValueAtTime(0.001, t + 0.05);
    o.connect(g).connect(actx.destination); o.start(t); o.stop(t + 0.06);
  }

  // ---------------------------------------------------------------- transport
  function seek(t) {
    state.time = THREE.MathUtils.clamp(t, 0, D - 1e-3);
    state.loopShot = film.shotAt(state.time);
    if (audio) try { audio.currentTime = state.time; } catch { /* not ready */ }
  }
  let clockRef = 0;
  function play() {
    if (state.framing) exitFrame();
    state.playing = true; clockRef = performance.now(); state.loopShot = film.shotAt(state.time);
    if (audio) { audio.currentTime = state.time; audio.play().catch(() => {}); }
    $('#b-play').textContent = 'pause';
  }
  function pause() { state.playing = false; audio?.pause(); $('#b-play').textContent = 'play'; }
  function step(d) {
    seek(shots[THREE.MathUtils.clamp(state.cur.i + d, 0, shots.length - 1)].start + 1e-4);
    if (state.framing) enterFrame('a');
  }

  // ---------------------------------------------------------------- framing: edit a key by looking through it
  const editPose = makePose([0, 0, 0], [0, 0, -1]);
  const rig = new Rig($('#view-shot'), { onChange: frameUI });
  rig.enabled = false;
  function enterFrame(key) {
    pause();
    const sh = state.cur;
    if (key) { seek(key === 'a' ? sh.start + 1e-4 : sh.end - 1e-3); copyPose(editPose, sh.cam[key]); }
    else copyPose(editPose, film.pose(state.time).pose);
    Object.assign(state, { framing: true, frameKey: key || null });
    rig.pose = editPose; rig.enabled = true;
    document.body.classList.add('is-framing'); $('#frame-bar').hidden = false; frameUI();
  }
  function exitFrame() {
    Object.assign(state, { framing: false, frameKey: null }); rig.enabled = false;
    document.body.classList.remove('is-framing'); $('#frame-bar').hidden = true;
  }
  function frameUI() {
    $('#f-fov').value = editPose.fov;
    $('#f-fov-v').textContent = `${editPose.fov.toFixed(1)}° · ${Math.round(lensMM(editPose.fov, FILM.aspect))} mm · ${sizeOf(editPose)[0]} · ${angleOf(editPose)}`;
  }
  $('#f-fov').addEventListener('input', e => { editPose.fov = +e.target.value; frameUI(); });
  const write = k => {
    if (!state.framing) return flash('frame the shot first (1, 2 or F)');
    copyPose(state.cur.cam[k], editPose); touched(); flash(`${k === 'a' ? 'START' : 'END'} written for ${state.cur.id}`);
  };
  $('#f-to-a').addEventListener('click', () => write('a'));
  $('#f-to-b').addEventListener('click', () => write('b'));
  $('#f-exit').addEventListener('click', exitFrame);

  // ---------------------------------------------------------------- panel
  const fmt = t => `${Math.floor(t / 60)}:${(t % 60).toFixed(2).padStart(5, '0')}`;
  const vec = v => v.toArray().map(x => x.toFixed(2)).join(', ');
  function renderPanel() {
    const sh = state.cur;
    $('#p-id').textContent = sh.id;
    $('#p-time').textContent = `${fmt(sh.start)}–${fmt(sh.end)} · ${sh.dur.toFixed(2)} s · ${(sh.dur / BEAT).toFixed(1)} beats`;
    $('#p-picture').textContent = sh.picture || '';
    $('#p-action').textContent = sh.action || '';
    renderCam();
    document.querySelectorAll('#p-status button').forEach(b => b.classList.toggle('on', b.dataset.s === sh.status));
    $('#p-note').value = sh.note;
    shots.forEach(s => s.el.classList.toggle('cur', s === sh));
  }
  function renderCam() {
    const sh = state.cur, d = describe(sh, FILM.aspect);
    $('#p-spec').innerHTML = `<b>${d.size}</b> ${d.sizeWords} · ${d.angle} · ${d.lens}<br>${d.move} <span class="muted">(${d.ease}, ${sh.cam.path})</span>`;
    for (const k of ['a', 'b']) {
      const c = sh.cam[k];
      $(`#p-${k}`).textContent = `p ${vec(c.p)} → t ${vec(c.t)} · ${Math.round(lensMM(c.fov, FILM.aspect))} mm${c.roll ? ` · roll ${c.roll.toFixed(0)}°` : ''}`;
    }
    $('#p-ease').value = sh.cam.ease; $('#p-path').value = sh.cam.path;
    $('#p-reset').disabled = JSON.stringify(camToJSON(sh.cam)) === JSON.stringify(camToJSON(camFromJSON(sh.defCam)));
    sh.warn = checkShot(sh);
    $('#p-warn').innerHTML = sh.warn.map(w => `<div>${w}</div>`).join('');
  }
  $('#p-ease').addEventListener('change', e => { state.cur.cam.ease = e.target.value; touched(); });
  $('#p-path').addEventListener('change', e => { state.cur.cam.path = e.target.value; touched(); });
  $('#p-reset').addEventListener('click', () => { state.cur.cam = camFromJSON(state.cur.defCam); touched(); });
  $('#p-go-a').addEventListener('click', () => enterFrame('a'));
  $('#p-go-b').addEventListener('click', () => enterFrame('b'));
  document.querySelectorAll('#p-status button').forEach(b => b.addEventListener('click', () => {
    const sh = state.cur; sh.status = sh.status === b.dataset.s ? '' : b.dataset.s; sh.el.dataset.status = sh.status; markDirty(); renderPanel();
  }));
  $('#p-note').addEventListener('input', e => { state.cur.note = e.target.value; markDirty(); });
  function touched() { markDirty(); updateGhost(state.cur, true); renderCam(); }

  // ---------------------------------------------------------------- toggles + keys
  const toggle = (name, btn, v) => { state[name] = v ?? !state[name]; $(btn).classList.toggle('on', state[name]); };
  $('#b-play').addEventListener('click', () => (state.playing ? pause() : play()));
  $('#b-prev').addEventListener('click', () => step(-1));
  $('#b-next').addEventListener('click', () => step(1));
  $('#b-loop').addEventListener('click', () => toggle('loop', '#b-loop'));
  $('#b-click').addEventListener('click', () => toggle('click', '#b-click'));
  $('#b-guides').addEventListener('click', () => { document.body.classList.toggle('is-guides'); $('#b-guides').classList.toggle('on'); });
  $('#b-all').addEventListener('click', () => { toggle('all', '#b-all'); shots.forEach(s => updateGhost(s, s === state.cur)); });
  $('#b-save').addEventListener('click', save);
  $('#b-export').addEventListener('click', exportPlan);
  addEventListener('keydown', e => {
    if (e.target instanceof Element && e.target.matches('input, textarea, select')) { if (e.key === 'Escape') e.target.blur(); return; }
    const k = e.key.toLowerCase();
    if ((e.metaKey || e.ctrlKey) && k === 's') { e.preventDefault(); save(); return; }
    if (e.metaKey || e.ctrlKey) return;
    if (state.framing && 'wasdqe'.includes(k) && k.length === 1) { rig.keys.add(k); return; }
    if (e.key === 'Shift') rig.keys.add('shift');
    if (e.code === 'Space') { e.preventDefault(); state.playing ? pause() : play(); }
    else if (e.key === 'ArrowRight') step(1);
    else if (e.key === 'ArrowLeft') step(-1);
    else if (k === '1') enterFrame('a');
    else if (k === '2') enterFrame('b');
    else if (k === 'f') state.framing ? exitFrame() : enterFrame();
    else if (e.key === 'Escape') exitFrame();
    else if (k === 'l') $('#b-loop').click();
    else if (k === 'k') $('#b-click').click();
    else if (k === 'g') $('#b-guides').click();
    else if (k === 'h') $('#b-all').click();
    else if (k === 'm') mapHome();
  });
  addEventListener('keyup', e => rig.keys.delete(e.key === 'Shift' ? 'shift' : e.key.toLowerCase()));
  addEventListener('blur', () => rig.keys.clear());

  // ---------------------------------------------------------------- save / export
  function markDirty() { state.dirty = true; $('#save-state').textContent = '● unsaved'; $('#save-state').className = 'dirty'; }
  function flash(msg) { const t = $('#toast'); t.textContent = msg; t.classList.add('show'); clearTimeout(flash.h); flash.h = setTimeout(() => t.classList.remove('show'), 2200); }
  function download(name, text, type) { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([text], { type })); a.download = name; a.click(); }
  async function post(path, body) {
    const r = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    if (!r.ok) throw new Error(r.status);
    return r.json();
  }
  function collect() {
    const out = { version: 1, updated: new Date().toISOString(), note: 'Overrides js/shots.js. p = position, t = look-at target (m), fov = vertical degrees, roll = degrees.', shots: {} };
    for (const sh of shots) {
      const c = camToJSON(sh.cam), changed = JSON.stringify(c) !== JSON.stringify(camToJSON(camFromJSON(sh.defCam)));
      if (changed || sh.status || sh.note) out.shots[sh.id] = { ...(changed && { cam: c }), ...(sh.status && { status: sh.status }), ...(sh.note && { note: sh.note }) };
    }
    return out;
  }
  async function save() {
    const data = collect();
    try { await post('/api/save', data); state.dirty = false; $('#save-state').textContent = 'saved'; $('#save-state').className = ''; flash('saved: data/edits.json'); }
    catch { download('edits.json', JSON.stringify(data, null, 1), 'application/json'); flash('no save server: downloaded edits.json, put it in data/'); }
  }
  function plan() {
    const rows = shots.map(sh => ({ id: sh.id, start: sh.start, end: sh.end, picture: sh.picture, action: sh.action, ...describe(sh, FILM.aspect), path: sh.cam.path, cam: camToJSON(sh.cam), status: sh.status, note: sh.note, warnings: checkShot(sh) }));
    const ok = rows.filter(r => r.status === 'ok').length, fix = rows.filter(r => r.status === 'fix').length;
    const md = [`# Camera plan · ${FILM.title}`, '',
      `Exported ${new Date().toISOString().slice(0, 16).replace('T', ' ')} UTC. Approved ${ok}/${rows.length}, needs a fix ${fix}. ` +
      `Size = frame height at the look-at target; lens = full-frame equivalent (36 mm on the long side of a ${FILM.export.width}×${FILM.export.height} frame).`, '',
      '| shot | time | size | angle | lens | move (ease) | START → END position (m) | status | note |', '|---|---|---|---|---|---|---|---|---|',
      ...rows.map(r => `| ${r.id} | ${fmt(r.start)}–${fmt(r.end)} | ${r.size} | ${r.angle} | ${r.lens} | ${r.move} (${r.ease}) | ${r.cam.a.p.join(', ')} → ${r.cam.b.p.join(', ')} | ${{ ok: 'approved', fix: 'needs a fix' }[r.status] || '—'} | ${(r.note || '').replace(/\n/g, ' ')}${r.warnings.length ? ' ⚠ ' + r.warnings.join('; ') : ''} |`), ''];
    return { md: md.join('\n'), json: JSON.stringify({ title: FILM.title, fps: FILM.fps, bpm: FILM.bpm, aspect: FILM.aspect, duration: D, shots: rows }, null, 1) };
  }
  async function exportPlan() {
    const { md, json } = plan();
    try { await post('/api/export', { name: 'camera_plan.md', text: md }); await post('/api/export', { name: 'camera_plan.json', text: json }); flash('exported camera_plan.md + camera_plan.json'); }
    catch { download('camera_plan.md', md, 'text/markdown'); download('camera_plan.json', json, 'application/json'); flash('no save server: downloaded the plan'); }
  }
  addEventListener('beforeunload', e => { if (state.dirty) e.preventDefault(); });

  // ---------------------------------------------------------------- render loop
  function fitShot() {
    const r = $('#fit-shot').getBoundingClientRect();
    let w = r.width, h = w / FILM.aspect;
    if (h > r.height) { h = r.height; w = h * FILM.aspect; }
    Object.assign($('#view-shot').style, { width: w + 'px', height: h + 'px' });
  }
  function onResize() { renderer.setSize(innerWidth, innerHeight, false); fitShot(); }
  addEventListener('resize', onResize);
  new ResizeObserver(onResize).observe(document.body);
  onResize();

  function renderView(el, camera) {
    const r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) return;
    const x = r.left, y = innerHeight - r.bottom;
    renderer.setViewport(x, y, r.width, r.height); renderer.setScissor(x, y, r.width, r.height);
    if (camera.isOrthographicCamera) placeMap(r.width / r.height);
    renderer.render(scene, camera);
  }
  function selectShot(sh) {
    if (state.cur) updateGhost(state.cur, false);
    state.cur = sh; updateGhost(sh, true); renderPanel();
  }
  shots.forEach(s => updateGhost(s, false));
  if (qs.has('shot')) { // deep link for reviews and headless checks: ?shot=s02&k=0.5
    const sh = shots.find(s => s.id === qs.get('shot'));
    if (sh) state.time = sh.start + sh.dur * Math.min(0.999, +(qs.get('k') ?? 0.5));
  }
  selectShot(film.shotAt(state.time)); // synchronously, so keys work before the first frame

  let last = performance.now();
  function frame(now) {
    const dt = Math.min(0.1, (now - last) / 1000); last = now; // wall clock: UI playback only, never the film
    const before = state.time;
    if (state.playing) {
      state.time = audio && !audio.paused ? audio.currentTime : state.time + (now - clockRef) / 1000;
      clockRef = now;
      if (state.loop && state.time >= state.loopShot.end) seek(state.loopShot.start);
      if (state.time >= D - 0.01) seek(0);
      if (state.click && Math.floor(state.time / BEAT) !== Math.floor(before / BEAT)) click(Math.floor(state.time / BEAT) % 4 === 0);
    }
    const sh = state.loop && state.playing ? state.loopShot : film.shotAt(state.time);
    if (sh !== state.cur) selectShot(sh);
    const { pose, lt } = film.pose(state.time, { shot: sh });
    rig.tick(dt);
    const p = state.framing ? editPose : pose;
    applyPose(cam, p);
    applyPose(live.c, p); live.c.updateMatrixWorld(true); live.h.update();
    renderer.setScissor(0, 0, innerWidth, innerHeight); renderer.setClearColor(0x0c0e14, 1); renderer.clear();
    renderView($('#view-shot'), cam);
    const fog = scene.fog; scene.fog = null; // the map looks from 30 m up: no fog there
    renderView(mapEl, mapCam);
    scene.fog = fog;

    const d = describe(sh, FILM.aspect);
    $('#hud-id').textContent = sh.id;
    $('#hud-time').textContent = `${fmt(state.time)} · bar ${Math.floor(state.time / (4 * BEAT)) + 1}.${Math.floor((state.time / BEAT) % 4) + 1}`;
    $('#hud-beat').classList.toggle('on', (state.time / BEAT) % 1 < 0.18);
    $('#hud-mode').textContent = state.framing ? `FRAMING ${state.frameKey === 'a' ? 'START' : state.frameKey === 'b' ? 'END' : 'NOW'}` : sh.status === 'ok' ? 'approved' : sh.status === 'fix' ? 'needs a fix' : '';
    $('#hud-spec').textContent = state.framing ? `${sizeOf(p)[0]} · ${angleOf(p)} · ${Math.round(lensMM(p.fov, FILM.aspect))} mm` : `${d.size} · ${d.angle} · ${d.lens} · ${d.move}`;
    $('#hud-k').style.width = (Math.min(1, lt / sh.dur) * 100) + '%';
    $('#playhead').style.left = pct(state.time);
    $('#t-now').textContent = `${fmt(state.time)} / ${fmt(D)}`;
    window.__ready = true;
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
  window.app = { film, state, shots, seek, save, exportPlan, plan, check: checkShot, describe: sh => describe(sh, FILM.aspect) };
}
