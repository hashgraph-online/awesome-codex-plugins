// Auto camera: turns a storyboard's camera words into START/END keys, so a storyboard renders before anyone
// hand-places a camera. Hand-made cameras in js/shots.js and edits saved from the UI always win.
//
// storyboard shot fields it reads:
//   camera   "MCU, 3/4 left, low angle, slow push in"  or  { size, angle, move, subject, fov }
//   subject  name of one of the set's subjects (default: a subject named in the camera words, else the set's first)
//
// size   ECU | CU | MCU | MS | MLS | FS | WS | EWS (also "close-up", "medium", "wide", "establishing"…)
// angle  front (default) | 3/4 left | 3/4 right | profile left | profile right | back | ots (over the shoulder) | pov
//        + eye level (default) | low | high | top (overhead) | dutch
// move   static (default) | push in | pull out | orbit left/right | crane up/down | truck left/right | pan left/right |
//        tilt up/down | zoom in/out | whip (ease)
// Left/right are the SUBJECT's left/right. A person's right hand is +X, faces -Z (see props.js).
import * as THREE from 'three';

export const SIZE_ORDER = ['ECU', 'CU', 'MCU', 'MS', 'MLS', 'FS', 'WS', 'EWS'];
// Frame height for a 1.8 m person (m), and how far below the top of the subject the frame centre sits (fraction of height).
// Calibrated against the size thresholds in main.js sizeOf, so an auto "MCU" also reads back as MCU.
const PERSON = { ECU: [0.25, 0.09], CU: [0.5, 0.1], MCU: [0.82, 0.17], MS: [1.2, 0.28], MLS: [1.7, 0.38], FS: [2.6, 0.5], WS: [6, 0.5], EWS: [25, 0.5] };
// Objects (product, car, building): frame height as a multiple of the object's height; centre on the object.
const OBJECT = { ECU: 0.3, CU: 1.15, MCU: 1.5, MS: 2, MLS: 2.6, FS: 3.2, WS: 8, EWS: 25 };
const FOV = { ECU: 28, CU: 30, MCU: 35, MS: 40, MLS: 42, FS: 45, WS: 50, EWS: 55 }; // vertical degrees

const SIZE_WORDS = [
  ['ECU', /\b(ecu|extreme close|macro|detail|insert)\b/], ['MCU', /\b(mcu|medium close|chest)\b/], ['CU', /\b(cu|close[- ]?up|close)\b/],
  ['MLS', /\b(mls|medium long|medium wide|cowboy|knee)\b/], ['EWS', /\b(ews|extreme wide|establishing|aerial)\b/],
  ['MS', /\b(ms|mid|medium|waist)\b/], ['FS', /\b(fs|full|full[- ]body|long shot|ls)\b/], ['WS', /\b(ws|wide)\b/],
];

export function parseCamera(c) {
  if (c && typeof c === 'object') { // { size, angle, height, move, subject, fov }: normalise through the word parser
    const p = parseCamera([c.size, c.angle, c.height, c.move].flat().filter(Boolean).join(', '));
    return { ...p, ...(c.fov && { fov: c.fov }), ...(c.subject && { subject: c.subject }) };
  }
  const t = String(c || '').toLowerCase();
  const out = { text: t };
  for (const [k, re] of SIZE_WORDS) if (re.test(t)) { out.size = k; break; }
  const side = w => (/\bleft\b/.test(w) ? -1 : /\bright\b/.test(w) ? 1 : 0);
  if (/\bots\b|over[- ]the[- ]shoulder/.test(t)) out.angle = 'ots';
  else if (/\bpov\b|point of view/.test(t)) out.angle = 'pov';
  else if (/3\/4|three[- ]quarter/.test(t)) out.angle = side(t.match(/(3\/4|three[- ]quarter)[^,;.]*/)[0]) < 0 ? '3/4 left' : '3/4 right';
  else if (/profile|side on|side view/.test(t)) out.angle = side(t.match(/(profile|side)[^,;.]*/)[0]) < 0 ? 'profile left' : 'profile right';
  else if (/(?<!(pull|track|dolly|move)[- ])\bback\b|from behind|\bbehind\b/.test(t)) out.angle = 'back';
  out.height = /\btop\b|top[- ]down|overhead|bird/.test(t) ? 'top' : /\blow\b|worm/.test(t) ? 'low' : /\bhigh\b/.test(t) ? 'high' : 'eye';
  out.dutch = /dutch|canted/.test(t);
  const m = [];
  if (/push[- ]?in|dolly in|move in|track in/.test(t)) m.push('push');
  if (/pull[- ]?(out|back)|dolly (out|back)|track (out|back)|move back/.test(t)) m.push('pull');
  if (/\borbit|\barc\b/.test(t)) m.push('orbit ' + (side(t.match(/(\borbit|\barc\b)[^,;.]*/)[0]) < 0 ? 'left' : 'right'));
  if (/crane up|boom up|\brises?\b|pedestal up/.test(t)) m.push('crane up');
  if (/crane down|boom down|descend|pedestal down/.test(t)) m.push('crane down');
  if (/truck|track(ing)? (left|right)|slide/.test(t)) m.push('truck ' + (side(t.match(/(truck|track|slide)[^,;.]*/)[0]) < 0 ? 'left' : 'right'));
  if (/\bpan\b/.test(t)) m.push('pan ' + (side(t.match(/\bpan[^,;.]*/)[0]) < 0 ? 'left' : 'right'));
  if (/tilt up/.test(t)) m.push('tilt up');
  if (/tilt down/.test(t)) m.push('tilt down');
  if (/zoom in|crash zoom|snap zoom/.test(t)) m.push('zoom in');
  if (/zoom out/.test(t)) m.push('zoom out');
  out.move = m;
  out.ease = /whip|snap|crash/.test(t) ? 'whip' : /slow|gentle|drift/.test(t) ? 'inOut' : 'inOut';
  return out;
}

const isPerson = o => !!o.userData.j;
const AZ = { front: 0, '3/4 left': -40, '3/4 right': 40, 'profile left': -90, 'profile right': 90, back: 180, ots: 160, pov: 0 };
const EL = { eye: 0, low: -18, high: 25, top: 80 };
// Head-relative frame centre for people (m below the head centre), by size; wide sizes centre on the body.
const HEAD_DROP = { ECU: -0.02, CU: 0.02, MCU: 0.15, MS: 0.35, MLS: 0.55 };

export function subjectOf(set, sh) {
  const spec = parseCamera(sh.camera);
  const subjects = set.subjects || {};
  const names = Object.keys(subjects);
  const name = sh.subject || spec.subject || names.find(n => spec.text.includes(n.toLowerCase())) || names[0];
  return { name, obj: subjects[name], spec };
}

// Where the subject is right now and how a given size frames it.
function frameOf(obj, size, fov) {
  obj.updateWorldMatrix(true, true);
  const box = new THREE.Box3().setFromObject(obj);
  const person = isPerson(obj);
  const h = obj.userData.height || box.getSize(new THREE.Vector3()).y || 1;
  const q = obj.getWorldQuaternion(new THREE.Quaternion());
  const fwd = new THREE.Vector3(0, 0, -1).applyQuaternion(q).setY(0).normalize();
  const right = new THREE.Vector3(1, 0, 0).applyQuaternion(q).setY(0).normalize();
  const centre = box.getCenter(new THREE.Vector3());
  let H, target, head = null;
  if (person) {
    head = obj.userData.j.head.getWorldPosition(new THREE.Vector3());
    H = PERSON[size][0] * (h / 1.8);
    target = size in HEAD_DROP
      ? new THREE.Vector3(head.x, Math.max(head.y - HEAD_DROP[size] * (h / 1.8), centre.y), head.z)
      : new THREE.Vector3(head.x, centre.y, head.z).lerp(centre, 0.5);
  } else {
    H = OBJECT[size] * h;
    target = centre.clone();
  }
  return { box, person, h, fwd, right, centre, head, H, target, dist: H / (2 * Math.tan(THREE.MathUtils.degToRad(fov) / 2)) };
}
function place(f, az, el, d, tgt = f.target) {
  const a = THREE.MathUtils.degToRad(az), e = THREE.MathUtils.degToRad(el);
  const dir = f.fwd.clone().multiplyScalar(Math.cos(a)).addScaledVector(f.right, Math.sin(a)).multiplyScalar(Math.cos(e));
  dir.y = Math.sin(e);
  return tgt.clone().addScaledVector(dir, d);
}
function keyOf(f, angle, az, el) {
  if (angle === 'pov' && f.person) {          // from the eyes, looking where the subject looks
    return { p: f.head.clone().addScaledVector(f.fwd, 0.12), t: f.head.clone().addScaledVector(f.fwd, 3).add(new THREE.Vector3(0, -0.4, 0)) };
  }
  if (angle === 'ots' && f.person) {          // behind the subject's right shoulder, looking where they look
    const p = f.head.clone().add(new THREE.Vector3(0, -0.1, 0)).addScaledVector(f.right, 0.35).addScaledVector(f.fwd, -0.6);
    return { p, t: f.head.clone().addScaledVector(f.fwd, Math.max(1.2, f.dist)).add(new THREE.Vector3(0, -0.1, 0)) };
  }
  return { p: place(f, az, el, f.dist), t: f.target.clone() };
}

// posedAt(lt) poses the set at a local time of the shot (reset + the shot's anim), so a subject that moves during
// the shot is framed where it is at START and at END: the camera tracks it unless the words say "static"/"locked".
export function autoCam(set, sh, posedAt = () => {}) {
  const { obj, spec } = subjectOf(set, sh);
  if (!obj) return { a: { p: [0, 1.6, -4], t: [0, 1.2, 0], fov: 40, roll: 0 }, b: { p: [0, 1.6, -4], t: [0, 1.2, 0], fov: 40, roll: 0 }, ease: 'inOut' };
  const size = spec.size || (isPerson(obj) ? 'MS' : 'CU');
  const fov = spec.fov || FOV[size];
  const angle = spec.angle || 'front', az = AZ[angle] ?? 0, el = EL[spec.height] ?? 0;
  posedAt(0);
  const fA = frameOf(obj, size, fov), A = keyOf(fA, angle, az, el);
  posedAt(sh.end - sh.start);
  const fB = frameOf(obj, size, fov);
  const locked = /\b(static|locked|lock[- ]off|fixed)\b/.test(spec.text) || fA.target.distanceTo(fB.target) < 0.02;
  const B = locked ? { p: A.p.clone(), t: A.t.clone() } : keyOf(fB, angle, az, el);
  posedAt(null);

  // END key: tracked frame, then the move words on top of it
  let fovB = fov;
  const d0 = B.p.distanceTo(B.t);
  const camRight = new THREE.Vector3().subVectors(B.t, B.p).normalize().cross(new THREE.Vector3(0, 1, 0)).normalize();
  for (const m of spec.move) {
    if (m === 'push') B.p.lerp(B.t, 0.3);
    else if (m === 'pull') B.p.addScaledVector(B.p.clone().sub(B.t).normalize(), d0 * 0.45);
    else if (m.startsWith('orbit')) B.p = place(fB, az + (m.endsWith('left') ? -35 : 35), el, d0, B.t);
    else if (m === 'crane up') B.p.y += d0 * 0.35;
    else if (m === 'crane down') B.p.y -= Math.min(d0 * 0.35, B.p.y - 0.15);
    else if (m.startsWith('truck')) { const s = (m.endsWith('left') ? -1 : 1) * fB.H * 0.45; B.p.addScaledVector(camRight, s); B.t.addScaledVector(camRight, s); }
    else if (m.startsWith('pan')) B.t.addScaledVector(camRight, (m.endsWith('left') ? -1 : 1) * d0 * 0.35);
    else if (m === 'tilt up') B.t.y += d0 * 0.3;
    else if (m === 'tilt down') B.t.y -= d0 * 0.3;
    else if (m === 'zoom in') fovB = fov * 0.7;
    else if (m === 'zoom out') fovB = Math.min(100, fov * 1.4);
  }
  // never under the floor: a low angle on a wide frame would otherwise put the camera below ground
  const floor = (set.groundY ?? 0) + 0.15;
  A.p.y = Math.max(A.p.y, floor); B.p.y = Math.max(B.p.y, floor);
  const roll = spec.dutch ? 12 : 0;
  const r3 = v => v.toArray().map(x => Math.round(x * 1000) / 1000);
  return { a: { p: r3(A.p), t: r3(A.t), fov, roll }, b: { p: r3(B.p), t: r3(B.t), fov: fovB, roll }, ease: spec.ease };
}
