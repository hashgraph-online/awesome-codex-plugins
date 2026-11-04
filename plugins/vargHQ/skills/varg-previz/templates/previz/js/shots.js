// Per-shot previz. Timing, text and the default camera come from the storyboard (and autocam.js); this file adds,
// only where a shot needs it:
//   cam     hand-made camera keys: a (START) and b (END): p = position, t = look-at target, fov (vertical deg), roll (deg); ease
//   shake   local times (s) of impacts that kick the camera
//   ref     scale entry the shot size is judged by (config.scale), e.g. 'car' for a car chase
//   anim    poses the set for this shot: anim(S, c) with S.o = the set's named objects and
//           c = { k: 0..1 progress, lt: local seconds, dur, T: timeline seconds, beat: seconds per beat, camPos, sh }
// anim() runs after set.reset() every frame, and must depend on time only, so scrubbing and export are exact.
// Camera edits made in the UI are saved to data/edits.json and override these keys.
//
// The entries below animate the sample storyboard (studio / room / street). Replace them with your shots.
import * as THREE from 'three';
import { pose, walk, talk } from './props.js';

const cl = x => Math.max(0, Math.min(1, x));
export const ramp = (x, a, b) => cl((x - a) / (b - a));
export const sm = x => x * x * (3 - 2 * x);
export const V = (x, y, z) => new THREE.Vector3(x, y, z);
// cam(startPos, startTarget, startFov, endPos, endTarget = startTarget, endFov = startFov, ease, startRoll, endRoll)
export const cam = (ap, at, af, bp, bt, bf, ease = 'inOut', ar = 0, br = 0) =>
  ({ a: { p: ap, t: at, fov: af, roll: ar }, b: { p: bp || ap, t: bt || at, fov: bf ?? af, roll: br }, ease });

export const SHOTS = {
  // ---------------- room: hook on the phone, then the laugh
  s01: {
    anim(S, c) {
      const a = S.o.a;
      const up = sm(ramp(c.lt, c.beat * 2, c.beat * 2.5));               // looks up on beat 3
      pose(a, [['sit', 1], ['phone', 1 - up], ['handsOnTable', up]]);
      a.userData.j.neck.rotation.x = 0.35 * (1 - up);
      S.o.phone.visible = up < 0.5;
      a.updateMatrixWorld(true);
      if (S.o.phone.visible) S.o.phone.position.copy(a.userData.j.handR.getWorldPosition(V(0, 0, 0))).add(V(0, 0.02, -0.04));
      S.o.phone.rotation.set(-0.9, 0, 0);
    },
  },
  s02: {
    anim(S, c) {
      talk(S.o.a, c.lt, 1, c.beat);
      S.o.a.userData.j.spine.rotation.x = -0.15 * Math.abs(Math.sin(c.lt * Math.PI / c.beat)); // laughing bounce on the beat
    },
  },
  // ---------------- street: the car passes, the walker crosses town
  s03: {
    ref: 'car',
    // hand-made camera (wins over the storyboard's camera words): high, looking down the street, trucking right
    cam: cam([1.5, 6, 12], [2, 0.5, -10], 55, [3.2, 6, 12], [3.7, 0.5, -10]),
    anim(S, c) {
      S.o.car.position.z = 6 - c.lt * 9;
      walk(S.o.walker, c.T, 2 * c.beat);
      S.o.walker.position.z = -1 - c.lt * 1.3;
    },
  },
  s04: {
    anim(S, c) {
      walk(S.o.walker, c.T, 2 * c.beat);
      S.o.walker.position.z = -1 - c.lt * 1.3;
    },
  },
  // ---------------- studio: product hero, then the presenter shows it
  s05: {
    anim(S, c) { S.o.product.rotation.y = c.lt * 0.8; S.o.rim.intensity = 4 + 4 * sm(c.k); },
  },
  s06: {
    anim(S, c) {
      const h = S.o.host, lift = sm(ramp(c.lt, 0, c.beat));
      pose(h, [['stand', 1], ['holdUp', lift]]);
      talk(h, c.lt, 1, c.beat);
      h.updateMatrixWorld(true);
      S.o.product.position.lerp(h.userData.j.handR.getWorldPosition(V(0, 0, 0)).add(V(0, -0.02, -0.04)), lift);
    },
  },
};
