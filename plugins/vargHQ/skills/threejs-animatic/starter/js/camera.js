// Camera keys, moves, lens maths and the plain-words description used in the camera plan.
// A camera pose is { p: position, t: look-at target, fov: vertical degrees, roll: degrees }.
// Put the look-at target ON the subject (eyes, product): shot size, orbit and dolly all pivot on it.
import * as THREE from 'three';

const D2R = THREE.MathUtils.degToRad, R2D = THREE.MathUtils.radToDeg;

export function makePose(p, t, fov = 40, roll = 0) {
  return { p: new THREE.Vector3(...p), t: new THREE.Vector3(...t), fov, roll };
}
export const copyPose = (dst, src) => { dst.p.copy(src.p); dst.t.copy(src.t); dst.fov = src.fov; dst.roll = src.roll; return dst; };
const r3 = v => Math.round(v * 1000) / 1000;
export const poseToJSON = o => ({ p: o.p.toArray().map(r3), t: o.t.toArray().map(r3), fov: r3(o.fov), roll: r3(o.roll) });
export const camFromJSON = c => ({
  a: makePose(c.a.p, c.a.t, c.a.fov, c.a.roll || 0),
  b: makePose(c.b?.p || c.a.p, c.b?.t || c.a.t, c.b?.fov ?? c.a.fov, c.b?.roll || 0),
  ease: c.ease || 'inOut', path: c.path || 'line',
});
export const camToJSON = c => ({ a: poseToJSON(c.a), b: poseToJSON(c.b), ease: c.ease, path: c.path });

export function applyPose(camera, pose) {
  camera.position.copy(pose.p);
  camera.up.set(0, 1, 0);
  camera.lookAt(pose.t);
  if (pose.roll) camera.rotateZ(D2R(pose.roll));
  if (camera.fov !== pose.fov) { camera.fov = pose.fov; camera.updateProjectionMatrix(); }
}

// ------------------------------------------------------------------ lens
// Full-frame equivalent focal length: 36 mm along the LONG side of the frame (16:9 and 9:16 alike).
export function lensMM(vfov, aspect) {
  const t = Math.tan(D2R(vfov) / 2), long = aspect >= 1 ? t * aspect : t;
  return 18 / long;
}
export function fovFromMM(mm, aspect) {
  const long = 18 / mm;
  return R2D(2 * Math.atan(aspect >= 1 ? long / aspect : long));
}
export const hfov = (vfov, aspect) => R2D(2 * Math.atan(Math.tan(D2R(vfov) / 2) * aspect));

// ------------------------------------------------------------------ moves
export const EASE = {
  linear: k => k,
  inOut: k => k * k * (3 - 2 * k),
  in: k => k * k,
  out: k => 1 - (1 - k) * (1 - k),
  whip: k => (k < 0.5 ? 16 * k ** 5 : 1 - Math.pow(-2 * k + 2, 5) / 2),
  hold: () => 0,
};

const _s = new THREE.Spherical(), _s2 = new THREE.Spherical(), _v = new THREE.Vector3();
// Pose of a shot camera at local time lt (s). Local time may run past the shot end: the camera
// then holds its END key (a tail handle for the video-to-video reference).
// path 'line' lerps the position; 'arc' swings around the target, so an orbit keeps its distance
// instead of cutting the corner toward the subject.
export function evalCam(shot, lt) {
  const { a, b, ease, path } = shot.cam;
  const k = (EASE[ease] || EASE.inOut)(THREE.MathUtils.clamp(lt / shot.dur, 0, 1));
  const t = a.t.clone().lerp(b.t, k);
  let p;
  if (path === 'arc') {
    _s.setFromVector3(_v.subVectors(a.p, a.t));
    _s2.setFromVector3(_v.subVectors(b.p, b.t));
    let dth = _s2.theta - _s.theta;
    if (dth > Math.PI) dth -= 2 * Math.PI;
    if (dth < -Math.PI) dth += 2 * Math.PI;
    const s = new THREE.Spherical(_s.radius + (_s2.radius - _s.radius) * k, _s.phi + (_s2.phi - _s.phi) * k, _s.theta + dth * k);
    p = t.clone().add(new THREE.Vector3().setFromSpherical(s));
  } else p = a.p.clone().lerp(b.p, k);
  const pose = { p, t, fov: a.fov + (b.fov - a.fov) * k, roll: a.roll + (b.roll - a.roll) * k };
  // impacts: a decaying, deterministic shake (sines of local time, never Math.random)
  for (const at of shot.shake || []) {
    const d = lt - at;
    if (d < 0 || d > 0.5) continue;
    const amp = pose.p.distanceTo(pose.t) * 0.02 * Math.exp(-d * 9);
    const n = new THREE.Vector3(Math.sin(d * 97), Math.sin(d * 71 + 1), Math.sin(d * 83 + 2)).multiplyScalar(amp);
    pose.p.add(n); pose.t.add(n);
  }
  return pose;
}

// ------------------------------------------------------------------ plain-words description
// Shot size from the frame height at the look-at distance (vertical extent of the frame at the subject).
// Thresholds are for a person. For an object set shot.refScale = object height / 1.8 (a 0.3 m bottle:
// 0.17), so "CU" means the object fills the frame. See references/camera-language.md.
const SIZES = [[0.2, 'ECU', 'extreme close-up'], [0.4, 'CU', 'close-up'], [0.7, 'MCU', 'medium close-up'],
  [1.1, 'MS', 'medium shot'], [1.5, 'MLS', 'medium long shot'], [2.4, 'FS', 'full shot'], [8, 'WS', 'wide shot'], [Infinity, 'EWS', 'extreme wide']];
export function frameHeightAt(pose) { return 2 * pose.p.distanceTo(pose.t) * Math.tan(D2R(pose.fov) / 2); }
export function sizeOf(pose, refScale = 1) {
  const h = frameHeightAt(pose) / refScale;
  return SIZES.find(([max]) => h < max).slice(1);
}
export function angleOf(pose) {
  const d = _v.subVectors(pose.t, pose.p).normalize();
  const pitch = R2D(Math.asin(d.y));
  let a = pitch < -60 ? 'top shot' : pitch < -15 ? 'high angle' : pitch > 60 ? "worm's eye" : pitch > 15 ? 'low angle' : 'eye level';
  if (Math.abs(pose.roll) > 5) a += ', dutch';
  return a;
}
export function moveOf(shot) {
  const { a, b } = shot.cam, out = [];
  const dist = a.p.distanceTo(b.p), scale = (a.p.distanceTo(a.t) + b.p.distanceTo(b.t)) / 2;
  const da = a.t.clone().sub(a.p).normalize(), db = b.t.clone().sub(b.p).normalize();
  const turn = R2D(da.angleTo(db));
  let orbit = false;
  if (dist > scale * 0.04) {
    const m = b.p.clone().sub(a.p), along = m.dot(da) / dist;
    const orbitDeg = R2D(a.p.clone().sub(a.t).angleTo(b.p.clone().sub(b.t)));
    if (orbitDeg > 8 && a.t.distanceTo(b.t) < scale * 0.2) { out.push(`orbit ${Math.round(orbitDeg)}°`); orbit = true; }
    else if (Math.abs(m.y) / dist > 0.6) out.push(m.y > 0 ? 'crane up' : 'crane down');
    else if (along > 0.6) out.push('push in');
    else if (along < -0.6) out.push('pull out');
    else out.push('truck');
  }
  if (turn > 4 && !orbit) {
    const dy = R2D(Math.asin(db.y) - Math.asin(da.y));
    out.push(Math.abs(dy) > turn * 0.7 ? `tilt ${dy > 0 ? 'up' : 'down'} ${Math.round(Math.abs(dy))}°` : `pan ${Math.round(turn)}°`);
  }
  if (Math.abs(b.fov - a.fov) > 1.5) out.push(b.fov < a.fov ? 'zoom in' : 'zoom out');
  if (Math.abs(b.roll - a.roll) > 2) out.push(`roll ${Math.round(b.roll - a.roll)}°`);
  if ((shot.shake || []).length) out.push('shake on impact');
  return out.length ? out.join(' + ') : 'static';
}
export function describe(shot, aspect) {
  const sa = sizeOf(shot.cam.a, shot.refScale), sb = sizeOf(shot.cam.b, shot.refScale);
  const la = Math.round(lensMM(shot.cam.a.fov, aspect)), lb = Math.round(lensMM(shot.cam.b.fov, aspect));
  return {
    size: sa[0] === sb[0] ? sa[0] : `${sa[0]} → ${sb[0]}`,
    sizeWords: sa[0] === sb[0] ? sa[1] : `${sa[1]} to ${sb[1]}`,
    angle: angleOf(shot.cam.a),
    lens: la === lb ? `${la} mm` : `${la} → ${lb} mm`,
    move: moveOf(shot),
    ease: shot.cam.ease,
  };
}

// ------------------------------------------------------------------ mouse/keyboard rig for framing
//   drag: orbit around the target · shift+drag: look around from a fixed spot (pan/tilt)
//   right-drag: truck/pedestal · wheel: dolly · alt+wheel: FOV · W A S D / Q E: fly
export class Rig {
  constructor(el, { onChange } = {}) {
    this.el = el; this.pose = null; this.enabled = true; this.keys = new Set(); this.hover = false;
    this.onChange = onChange || (() => {});
    el.addEventListener('contextmenu', e => e.preventDefault());
    el.addEventListener('pointerenter', () => (this.hover = true));
    el.addEventListener('pointerleave', () => (this.hover = false));
    el.addEventListener('pointerdown', e => {
      if (!this.enabled || !this.pose) return;
      el.setPointerCapture(e.pointerId);
      this.drag = { x: e.clientX, y: e.clientY, mode: e.button === 2 || e.ctrlKey ? 'pan' : e.shiftKey ? 'look' : 'orbit' };
    });
    el.addEventListener('pointermove', e => {
      if (!this.drag) return;
      const dx = e.clientX - this.drag.x, dy = e.clientY - this.drag.y;
      this.drag.x = e.clientX; this.drag.y = e.clientY;
      this[this.drag.mode](dx, dy); this.onChange();
    });
    const end = () => (this.drag = null);
    el.addEventListener('pointerup', end); el.addEventListener('pointercancel', end);
    el.addEventListener('wheel', e => {
      if (!this.enabled || !this.pose) return;
      e.preventDefault();
      if (e.altKey) this.pose.fov = THREE.MathUtils.clamp(this.pose.fov + Math.sign(e.deltaY), 4, 110);
      else this.dolly(e.deltaY);
      this.onChange();
    }, { passive: false });
  }
  orbit(dx, dy) {
    const { p, t } = this.pose; _s.setFromVector3(_v.subVectors(p, t));
    _s.theta -= dx * 0.006; _s.phi = THREE.MathUtils.clamp(_s.phi - dy * 0.006, 0.02, Math.PI - 0.02);
    p.copy(t).add(_v.setFromSpherical(_s));
  }
  look(dx, dy) {
    const { p, t } = this.pose; _s.setFromVector3(_v.subVectors(t, p));
    _s.theta -= dx * 0.004; _s.phi = THREE.MathUtils.clamp(_s.phi + dy * 0.004, 0.02, Math.PI - 0.02);
    t.copy(p).add(_v.setFromSpherical(_s));
  }
  basis() {
    const fwd = new THREE.Vector3().subVectors(this.pose.t, this.pose.p).normalize();
    const right = new THREE.Vector3().crossVectors(fwd, new THREE.Vector3(0, 1, 0)).normalize();
    return { fwd, right, up: new THREE.Vector3().crossVectors(right, fwd) };
  }
  pan(dx, dy) {
    const { p, t, fov } = this.pose, { right, up } = this.basis();
    const s = (p.distanceTo(t) * 2 * Math.tan(D2R(fov) / 2)) / (this.el.clientHeight || 1);
    const m = right.multiplyScalar(-dx * s).add(up.multiplyScalar(dy * s));
    p.add(m); t.add(m);
  }
  dolly(dy) {
    const { p, t } = this.pose; _v.subVectors(p, t);
    p.copy(t).add(_v.setLength(Math.max(0.05, _v.length() * Math.exp(dy * 0.001))));
  }
  tick(dt) {
    if (!this.enabled || !this.pose || !this.hover || !this.keys.size) return;
    const { fwd, right } = this.basis(), m = new THREE.Vector3();
    if (this.keys.has('w')) m.add(fwd); if (this.keys.has('s')) m.sub(fwd);
    if (this.keys.has('d')) m.add(right); if (this.keys.has('a')) m.sub(right);
    if (this.keys.has('e')) m.y += 1; if (this.keys.has('q')) m.y -= 1;
    if (!m.lengthSq()) return;
    m.normalize().multiplyScalar(this.pose.p.distanceTo(this.pose.t) * (this.keys.has('shift') ? 2 : 0.6) * dt);
    this.pose.p.add(m); this.pose.t.add(m); this.onChange();
  }
}
