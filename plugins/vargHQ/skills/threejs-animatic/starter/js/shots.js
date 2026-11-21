// The film: timing, shots and blocking. This is the file you edit per project.
//
// FILM     format and timing, in config.js (re-exported here).
// SHOTS    one entry per shot: id, start/end (s), picture (what we see), action (what happens, written
//          for the video model), cam = START (a) and END (b) keys + ease + path. Edits saved from the
//          UI (data/edits.json) override cam, so keep these as the defaults.
// BLOCKING poses the whole set from world time T. Action is blocked once, in world time, and every
//          shot is only a camera on it: continuity across cuts comes for free.
//          Optional shot.cheat(S, c) runs after BLOCKING for a per-shot cheat (c.lt = local seconds).
import * as THREE from 'three';
import { pose } from './props.js';
import { fovFromMM } from './camera.js';
import { FILM, BEAT } from './config.js';

export { FILM, BEAT };

const mm = f => fovFromMM(f, FILM.aspect);
const cam = (ap, at, af, bp, bt, bf, ease = 'inOut', path = 'line') =>
  ({ a: { p: ap, t: at, fov: mm(af), roll: 0 }, b: { p: bp, t: bt || at, fov: mm(bf ?? af), roll: 0 }, ease, path });

export const SHOTS = [
  {
    id: 's01', start: 0, end: 4,
    picture: 'Wide: two people at a small round cafe table by a big window, talking.',
    action: 'The person on the left talks and gestures with the right hand; the person on the right listens and nods. ' +
      'At about 3 s a small drone appears far away outside the window.',
    subjects: ['a', 'b'], // checked automatically: in frame, not blocked, camera not inside geometry
    cam: cam([0.25, 1.35, 4.2], [0, 0.95, 0], 35, [0.1, 1.28, 3.1], null, 35, 'inOut'),
  },
  {
    id: 's02', start: 4, end: 6,
    picture: 'Over the left person\'s shoulder onto the right person, medium close-up.',
    action: 'The right person hears something, stops listening and looks up and to the window.',
    subjects: ['b'],
    cam: cam([-1.75, 1.32, 0.42], [0.72, 1.2, -0.02], 75, [-1.6, 1.31, 0.38], null, 75, 'out'),
  },
  {
    id: 's03', start: 6, end: 10,
    picture: 'Low angle from the table edge, both people on the sides of the frame, the drone comes in over the table.',
    action: 'The drone flies in through the window, slows over the table and lands between the cups. ' +
      'Both people lean back; the left person lifts both hands; at the end the right person leans in to look at it.',
    subjects: ['a', 'b'],
    cam: cam([0.15, 0.95, 1.6], [0, 1.65, -0.8], 24, [0.1, 1.15, 1.75], [0, 0.95, 0], 24, 'inOut'),
  },
];

// ------------------------------------------------------------------ blocking (world time)
const clamp01 = x => Math.max(0, Math.min(1, x));
const ramp = (x, a, b) => clamp01((x - a) / (b - a));
const smooth = x => x * x * (3 - 2 * x);
const win = (x, a, b, f = 0.25) => smooth(ramp(x, a, a + f)) * (1 - smooth(ramp(x, b - f, b)));
const pulse = (T, every, len) => win(T % every, 0, len, len / 2);

// Drone flight: one curve through the window to the table; arc-length sampling = even speed.
const FLIGHT = new THREE.CatmullRomCurve3([
  new THREE.Vector3(-4, 4.5, -12), new THREE.Vector3(-1.5, 3, -7), new THREE.Vector3(0, 2.1, -3.5),
  new THREE.Vector3(0.05, 1.8, -1.2), new THREE.Vector3(0, 1.35, 0), new THREE.Vector3(0, 0.8, 0),
]);
const FLY_FROM = 3.0, FLY_TO = 8.6;

export function BLOCKING(S, T) {
  const { a, b, drone } = S.o;
  // A talks with the right hand on the beat until the drone is close; B nods on every bar
  const talk = (1 - ramp(T, 5.2, 5.6)) * (0.5 + 0.5 * Math.sin((T / BEAT) * Math.PI));
  const lookA = smooth(ramp(T, 5.3, 5.8));
  const lookB = smooth(ramp(T, 4.4, 4.9));
  const lean = smooth(ramp(T, 6.6, 7.2)) * (1 - smooth(ramp(T, 9.0, 9.6)));
  const hands = smooth(ramp(T, 7.0, 7.5)) * (1 - smooth(ramp(T, 8.8, 9.3)));
  pose(a, [['sit', 1], ['handsOnTable', 1 - talk], ['gestureR', talk], ['leanBack', lean], ['handsUp', hands * 0.8]]);
  pose(b, [['sit', 1], ['handsOnTable', 1], ['nod', pulse(T, 2, 0.5) * (1 - lookB)], ['lookUp', lookB * (1 - lean * 0.4)], ['leanBack', lean]]);
  // head turns toward the window (at -Z): it is on A's left (+y) and on B's right (-y)
  a.userData.j.head.rotation.y = 0.55 * lookA;
  a.userData.j.neck.rotation.x += 0.25 * lookA;
  b.userData.j.head.rotation.y = -0.6 * lookB * (1 - smooth(ramp(T, 6.8, 7.6)));
  // B leans in at the end to look at the landed drone
  const inspect = smooth(ramp(T, 9.0, 9.6));
  b.userData.j.spine.rotation.x -= 0.35 * inspect;
  b.userData.j.neck.rotation.x -= 0.45 * inspect;

  // drone: hidden until it starts, flies the curve, turns to face A while it lands
  const u = smooth(ramp(T, FLY_FROM, FLY_TO));
  drone.visible = T >= FLY_FROM;
  drone.position.copy(FLIGHT.getPointAt(u));
  if (u > 0 && u < 1) drone.position.y += 0.03 * Math.sin(T * 7) * (1 - u);
  drone.rotation.y = Math.PI + (Math.PI / 2 - Math.PI) * smooth(ramp(T, 6.6, 8.2));
  drone.rotation.x = -0.25 * (1 - smooth(ramp(T, 5.5, 7.5))) * (u > 0 ? 1 : 0); // nose down while it travels
  // rotors spin down after landing. Seek-safe rule: a changing speed is INTEGRATED in closed form
  // (angle = ∫ speed dT), never multiplied (T * speed * k runs backwards) or accumulated per frame.
  const T0 = FLY_TO + 0.4, T1 = FLY_TO + 1.0, x = ramp(T, T0, T1);
  const angle = 26 * (Math.min(T, T0) + (T1 - T0) * (x - x ** 3 + x ** 4 / 2)); // ∫(1 - smoothstep)
  drone.userData.rotors.forEach((r, i) => (r.rotation.y = (i % 2 ? -1 : 1) * angle));
}
