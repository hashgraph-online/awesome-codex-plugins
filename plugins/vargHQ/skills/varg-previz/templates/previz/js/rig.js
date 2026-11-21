// Camera rig for a DOM view: operates on a pose {p: Vector3, t: Vector3, fov, roll}.
//   left drag ........ orbit around the target
//   shift/alt + drag . look around (pan/tilt from a fixed position)
//   right drag ....... truck/pedestal (move camera and target together)
//   wheel ............ dolly toward/away from the target; alt + wheel = FOV (zoom)
//   W A S D / Q E .... fly (while the pointer is over the view); shift = faster
import * as THREE from 'three';

const _s = new THREE.Spherical(), _v = new THREE.Vector3();

export function makePose(p, t, fov = 40, roll = 0) {
  return { p: new THREE.Vector3(...p), t: new THREE.Vector3(...t), fov, roll };
}
export function poseToJSON(o) {
  const r = v => Math.round(v * 1000) / 1000;
  return { p: o.p.toArray().map(r), t: o.t.toArray().map(r), fov: r(o.fov), roll: r(o.roll) };
}
export function applyPose(camera, pose) {
  camera.position.copy(pose.p);
  camera.up.set(0, 1, 0);
  camera.lookAt(pose.t);
  if (pose.roll) camera.rotateZ(THREE.MathUtils.degToRad(pose.roll));
  if (camera.fov !== pose.fov) { camera.fov = pose.fov; camera.updateProjectionMatrix(); }
}

export class Rig {
  constructor(el, { onChange } = {}) {
    this.el = el; this.pose = null; this.enabled = true; this.hover = false; this.keys = new Set();
    this.onChange = onChange || (() => {});
    el.addEventListener('contextmenu', e => e.preventDefault());
    el.addEventListener('pointerenter', () => (this.hover = true));
    el.addEventListener('pointerleave', () => (this.hover = false));
    el.addEventListener('pointerdown', e => {
      if (!this.enabled || !this.pose || e.target.closest('.no-rig')) return;
      el.setPointerCapture(e.pointerId);
      const mode = e.button === 2 || e.ctrlKey ? 'pan' : e.button === 1 ? 'dolly' : e.shiftKey || e.altKey ? 'look' : 'orbit';
      this.drag = { x: e.clientX, y: e.clientY, mode };
    });
    el.addEventListener('pointermove', e => {
      if (!this.drag) return;
      const dx = e.clientX - this.drag.x, dy = e.clientY - this.drag.y;
      this.drag.x = e.clientX; this.drag.y = e.clientY;
      this[this.drag.mode](dx, dy);
      this.onChange();
    });
    const end = () => (this.drag = null);
    el.addEventListener('pointerup', end); el.addEventListener('pointercancel', end);
    el.addEventListener('wheel', e => {
      if (!this.enabled || !this.pose) return;
      e.preventDefault();
      if (e.altKey) this.pose.fov = THREE.MathUtils.clamp(this.pose.fov + Math.sign(e.deltaY) * 1, 5, 120);
      else this.dolly(0, e.deltaY * 0.5);
      this.onChange();
    }, { passive: false });
  }
  orbit(dx, dy) {
    const { p, t } = this.pose;
    _v.subVectors(p, t); _s.setFromVector3(_v);
    _s.theta -= dx * 0.006; _s.phi = THREE.MathUtils.clamp(_s.phi - dy * 0.006, 0.02, Math.PI - 0.02);
    p.copy(t).add(_v.setFromSpherical(_s));
  }
  look(dx, dy) {
    const { p, t } = this.pose;
    _v.subVectors(t, p); _s.setFromVector3(_v);
    _s.theta -= dx * 0.004; _s.phi = THREE.MathUtils.clamp(_s.phi + dy * 0.004, 0.02, Math.PI - 0.02);
    t.copy(p).add(_v.setFromSpherical(_s));
  }
  basis() {
    const { p, t } = this.pose;
    const fwd = _v.subVectors(t, p).normalize().clone();
    const right = new THREE.Vector3().crossVectors(fwd, new THREE.Vector3(0, 1, 0)).normalize();
    if (right.lengthSq() < 1e-6) right.set(1, 0, 0);
    const up = new THREE.Vector3().crossVectors(right, fwd);
    return { fwd, right, up };
  }
  pan(dx, dy) {
    const { p, t, fov } = this.pose, { right, up } = this.basis();
    const h = this.el.clientHeight || 1;
    const s = (p.distanceTo(t) * 2 * Math.tan(THREE.MathUtils.degToRad(fov) / 2)) / h;
    const m = right.multiplyScalar(-dx * s).add(up.multiplyScalar(dy * s));
    p.add(m); t.add(m);
  }
  dolly(dx, dy) {
    const { p, t } = this.pose;
    _v.subVectors(p, t);
    const len = Math.max(0.03, _v.length() * Math.exp(dy * 0.002));
    p.copy(t).add(_v.setLength(len));
  }
  // Called every frame with dt (s): keyboard fly.
  tick(dt) {
    if (!this.enabled || !this.pose || !this.hover || !this.keys.size) return false;
    const { fwd, right } = this.basis();
    const sp = this.pose.p.distanceTo(this.pose.t) * (this.keys.has('shift') ? 2.5 : 0.8) * dt;
    const m = new THREE.Vector3();
    if (this.keys.has('w')) m.add(fwd); if (this.keys.has('s')) m.sub(fwd);
    if (this.keys.has('d')) m.add(right); if (this.keys.has('a')) m.sub(right);
    if (this.keys.has('e')) m.y += 1; if (this.keys.has('q')) m.y -= 1;
    if (!m.lengthSq()) return false;
    m.normalize().multiplyScalar(sp);
    this.pose.p.add(m); this.pose.t.add(m);
    this.onChange();
    return true;
  }
}
