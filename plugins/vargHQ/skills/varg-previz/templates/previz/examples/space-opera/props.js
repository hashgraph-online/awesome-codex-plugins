// Schematic props built from primitives. Units are metres.
// Conventions: forward = -Z (ship nose, pilot face), up = +Y, a character's right hand = +X.
import * as THREE from 'three';

export const C = {
  hull: 0xd9dee6, white: 0xf2f4f8, dark: 0x2a2d36, black: 0x16171c, glove: 0x1c1d22,
  red: 0xff2a3d, orange: 0xff5315, cyan: 0x2ee6ff, magenta: 0xff3df2, violet: 0x7a4dff,
  navy: 0x0b1030, skin: 0xe2bc9c, hair: 0x2a1f4a, gold: 0xe0a83a, screen: 0xb8c0c8,
};

export function mat(color, o = {}) {
  return new THREE.MeshStandardMaterial({ color, roughness: 0.65, metalness: 0.05, flatShading: true, ...o });
}
export function glow(color, intensity = 2, o = {}) {
  return new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: intensity, roughness: 1, ...o });
}
export function basic(color, o = {}) {
  return new THREE.MeshBasicMaterial({ color, ...o });
}

const inkMat = new THREE.LineBasicMaterial({ color: 0x07080c, transparent: true, opacity: 0.55 });
// Outline every mesh: gives the grey-box a storyboard "line art" read.
export function ink(root, angle = 35) {
  const meshes = [];
  root.traverse(o => { if (o.isMesh && !o.isInstancedMesh && !o.userData.noInk && !o.parent?.userData.noInk) meshes.push(o); });
  for (const m of meshes) {
    const e = new THREE.LineSegments(new THREE.EdgesGeometry(m.geometry, angle), inkMat);
    e.userData.isInk = true;
    e.raycast = () => {};
    m.add(e);
  }
  return root;
}

function mesh(geo, material, pos, rot, name) {
  const m = new THREE.Mesh(geo, material);
  if (pos) m.position.set(...pos);
  if (rot) m.rotation.set(...rot);
  if (name) m.name = name;
  return m;
}
function pivot(parent, name, pos) {
  const g = new THREE.Group();
  g.name = name;
  g.position.set(...pos);
  parent.add(g);
  return g;
}
// Capsule hanging down from a pivot (limb).
function limb(parent, len, r, material) {
  const m = mesh(new THREE.CapsuleGeometry(r, len - 2 * r, 3, 8), material, [0, -len / 2, 0]);
  parent.add(m);
  return m;
}

// ---------------------------------------------------------------- pilot
// Root origin = pelvis. Standing: root.y = 0.95. Joints in root.userData.j.
export function makePilot({ suit = C.white, pants = C.black, hair = C.hair, female = false, helmetInHand = false } = {}) {
  const root = new THREE.Group();
  root.name = 'pilot';
  const jacket = mat(suit), dark = mat(pants), glove = mat(C.glove), skin = mat(C.skin), hairM = mat(hair);
  root.add(mesh(new THREE.BoxGeometry(0.32, 0.16, 0.2), dark, [0, 0, 0]));

  const spine = pivot(root, 'spine', [0, 0.05, 0]);
  spine.add(mesh(new THREE.CapsuleGeometry(female ? 0.14 : 0.16, 0.3, 3, 10), jacket, [0, 0.27, 0]));
  spine.add(mesh(new THREE.CylinderGeometry(0.09, 0.1, 0.36, 8), dark, [0, 0.28, -0.1])); // black under-shirt panel
  for (const s of [-1, 1]) spine.add(mesh(new THREE.BoxGeometry(0.1, 0.035, 0.18), glow(C.orange, 0.6), [0.17 * s, 0.47, 0]));

  const neck = pivot(spine, 'neck', [0, 0.52, 0]);
  const head = pivot(neck, 'head', [0, 0.13, 0]);
  head.add(mesh(new THREE.SphereGeometry(0.11, 16, 12), skin, [0, 0, 0], null, 'face'));
  const hairMesh = mesh(new THREE.SphereGeometry(0.122, 14, 10, 0, Math.PI * 2, 0, Math.PI * (female ? 0.62 : 0.5)), hairM, [0, 0.015, 0.012]);
  head.add(hairMesh);
  if (female) head.add(mesh(new THREE.CapsuleGeometry(0.08, 0.16, 3, 8), hairM, [0, -0.08, 0.07]));
  const eyes = new THREE.Group(); eyes.name = 'eyes'; head.add(eyes);
  for (const s of [-1, 1]) {
    const eye = mesh(new THREE.SphereGeometry(0.016, 10, 8), basic(0xffffff), [0.038 * s, 0.015, -0.098], null, s < 0 ? 'eyeL' : 'eyeR');
    eye.add(mesh(new THREE.SphereGeometry(0.008, 8, 6), basic(0x111111), [0, 0, -0.011]));
    eye.userData.noInk = true;
    eyes.add(eye);
  }
  const mouth = mesh(new THREE.BoxGeometry(0.05, 0.012, 0.01), basic(0x5a2020), [0, -0.05, -0.105], null, 'mouth');
  mouth.userData.noInk = true;
  head.add(mouth);
  if (!female) { // headset + boom mic (left ear → mouth)
    head.add(mesh(new THREE.TorusGeometry(0.125, 0.008, 4, 16, Math.PI), mat(C.dark), [0, 0.01, 0.01]));
    const boom = mesh(new THREE.CylinderGeometry(0.004, 0.004, 0.12, 4), mat(C.dark), [-0.085, -0.04, -0.07], [Math.PI / 2, 0, 0.9], 'boom');
    head.add(boom);
    head.add(mesh(new THREE.SphereGeometry(0.012, 6, 4), glow(C.red, 1.5), [-0.035, -0.055, -0.115], null, 'micTip'));
  }

  const j = { spine, neck, head };
  for (const [side, s] of [['L', -1], ['R', 1]]) {
    const sh = pivot(spine, 'shoulder' + side, [0.21 * s, 0.45, 0]);
    limb(sh, 0.3, 0.055, jacket);
    const el = pivot(sh, 'elbow' + side, [0, -0.3, 0]);
    limb(el, 0.28, 0.048, jacket);
    const hand = pivot(el, 'hand' + side, [0, -0.3, 0]);
    hand.add(mesh(new THREE.SphereGeometry(0.05, 8, 6), glove, [0, 0, 0]));
    const hip = pivot(root, 'hip' + side, [0.1 * s, 0, 0]);
    limb(hip, 0.46, 0.07, dark);
    const kn = pivot(hip, 'knee' + side, [0, -0.46, 0]);
    limb(kn, 0.44, 0.06, dark);
    kn.add(mesh(new THREE.BoxGeometry(0.1, 0.07, 0.24), dark, [0, -0.46, -0.06]));
    Object.assign(j, { ['shoulder' + side]: sh, ['elbow' + side]: el, ['hand' + side]: hand, ['hip' + side]: hip, ['knee' + side]: kn });
  }
  if (helmetInHand) {
    const helm = mesh(new THREE.SphereGeometry(0.15, 14, 10), mat(C.white), [0.02, -0.08, -0.06], null, 'helmet');
    helm.add(mesh(new THREE.SphereGeometry(0.152, 14, 8, -0.9, 1.8, 1.1, 0.8), glow(C.cyan, 0.5), [0, 0, 0], [0, Math.PI, 0]));
    j.handL.add(helm);
    j.helmet = helm;
  }
  root.userData.j = j;
  ink(root);
  root.traverse(o => { if (o.isMesh) o.castShadow = true; });
  return root;
}

// Joint-angle poses. Values are Euler XYZ in radians; missing joints = 0.
// shoulder.x > 0 raises the arm forward; elbow.x > 0 bends the forearm forward/up;
// hip.x > 0 lifts the thigh forward; knee.x < 0 bends the shin back.
export const POSE = {
  stand: {},
  sit: { hipL: [1.45, 0, 0.05], hipR: [1.45, 0, -0.05], kneeL: [-1.4, 0, 0], kneeR: [-1.4, 0, 0], shoulderL: [0.35, 0, -0.15], shoulderR: [0.35, 0, 0.15], elbowL: [0.9, 0, 0], elbowR: [0.9, 0, 0] },
  stickAndThrottle: { shoulderL: [0.45, 0, -0.22], elbowL: [0.95, 0, 0.05], shoulderR: [0.45, 0, 0.22], elbowR: [0.95, 0, -0.05] },
  handsOnHead: { shoulderL: [2.5, 0, -0.75], elbowL: [2.1, 0, 0], shoulderR: [2.5, 0, 0.75], elbowR: [2.1, 0, 0] },
  coverFace: { shoulderL: [1.2, 0, 0.8], elbowL: [2.35, 0, 0], shoulderR: [1.2, 0, -0.8], elbowR: [2.35, 0, 0], neck: [0.3, 0, 0] },
  behindHead: { shoulderL: [2.7, 0, -0.95], elbowL: [2.4, 0, 0], shoulderR: [2.7, 0, 0.95], elbowR: [2.4, 0, 0], spine: [-0.28, 0, 0], neck: [-0.1, 0, 0] },
  headsetL: { shoulderL: [0.9, 0, -0.75], elbowL: [2.35, 0, 0], shoulderR: [0.45, 0, 0.22], elbowR: [0.95, 0, -0.05] },
  pressR: { shoulderR: [0.95, 0, 0.05], elbowR: [0.45, 0, 0] },
  pressC: { shoulderR: [1.05, 0, -0.5], elbowR: [0.55, 0, 0] },
  pressCUp: { shoulderR: [1.6, 0, -0.45], elbowR: [1.2, 0, 0] },
  showCard: { shoulderR: [0.95, 0, -0.1], elbowR: [1.45, 0, 0] },
  pressRUp: { shoulderR: [1.35, 0, 0.05], elbowR: [1.15, 0, 0] },
  toggles: { shoulderL: [0.95, 0, -0.05], elbowL: [0.5, 0, 0], shoulderR: [0.95, 0, 0.05], elbowR: [0.5, 0, 0] },
  handsUp: { shoulderL: [1.2, 0, -0.3], elbowL: [1.0, 0, 0], shoulderR: [1.2, 0, 0.3], elbowR: [1.0, 0, 0], spine: [-0.08, 0, 0] },
  slideCard: { shoulderR: [1.1, 0.2, 0.05], elbowR: [0.3, 0, 0], shoulderL: [0.2, 0, -0.1], elbowL: [0.4, 0, 0] },
  throttleFwd: { shoulderL: [0.9, 0, -0.18], elbowL: [0.45, 0, 0.05], spine: [0.12, 0, 0] },
  sax: { shoulderL: [0.9, 0, -0.35], elbowL: [1.55, 0, 0], shoulderR: [0.6, 0, 0.3], elbowR: [1.35, 0, 0], neck: [-0.15, 0, 0] },
  saxHigh: { shoulderL: [1.2, 0, -0.35], elbowL: [1.6, 0, 0], shoulderR: [0.9, 0, 0.3], elbowR: [1.4, 0, 0], spine: [-0.2, 0, 0], neck: [-0.4, 0, 0] },
  crouch: { hipL: [1.6, 0, 0.15], hipR: [1.6, 0, -0.15], kneeL: [-2.2, 0, 0], kneeR: [-2.2, 0, 0], spine: [0.5, 0, 0], shoulderL: [1.0, 0, -0.3], shoulderR: [1.0, 0, 0.3] },
  helmetOn: { shoulderL: [2.75, 0, -0.55], elbowL: [1.65, 0, 0], shoulderR: [2.75, 0, 0.55], elbowR: [1.65, 0, 0] },
};
const JOINTS = ['spine', 'neck', 'head', 'shoulderL', 'elbowL', 'handL', 'shoulderR', 'elbowR', 'handR', 'hipL', 'kneeL', 'hipR', 'kneeR'];

// Apply a blend of layered poses: pose(pilot, [['sit',1], ['stickAndThrottle',1], ['coverFace', k]]).
// Later layers override earlier ones by weight (joint-wise lerp).
export function pose(pilot, layers) {
  const j = pilot.userData.j;
  for (const name of JOINTS) {
    let v = [0, 0, 0];
    for (const [p, w] of layers) {
      const src = POSE[p];
      if (!src || !(name in src) || w <= 0) continue;
      const t = src[name];
      v = [v[0] + (t[0] - v[0]) * w, v[1] + (t[1] - v[1]) * w, v[2] + (t[2] - v[2]) * w];
    }
    j[name].rotation.set(v[0], v[1], v[2]);
  }
}

// ---------------------------------------------------------------- ship
// ~9 m long, ~7 m span: always clearly bigger than the 1.8 m pilot.
export function makeShip({ accent = C.orange, name = 'ship', canopy = true } = {}) {
  const g = new THREE.Group();
  g.name = name;
  const hull = mat(C.hull, { metalness: 0.3, roughness: 0.4 });
  const body = mesh(new THREE.CapsuleGeometry(0.95, 5.2, 6, 12), hull, [0, 0, 0], [Math.PI / 2, 0, 0], 'body');
  body.scale.set(1, 1, 0.82);
  g.add(body);
  g.add(mesh(new THREE.ConeGeometry(0.75, 1.6, 12), hull, [0, -0.05, -4.0], [-Math.PI / 2, 0, 0]));
  if (canopy) {
    const glass = mesh(new THREE.SphereGeometry(0.75, 16, 10, 0, Math.PI * 2, 0, Math.PI / 2), mat(0x5fb7c4, { transparent: true, opacity: 0.55, roughness: 0.1 }), [0, 0.55, -1.4], null, 'canopy');
    glass.scale.set(0.85, 0.75, 1.9);
    g.add(glass);
  }
  for (const [side, s] of [['L', -1], ['R', 1]]) {
    const nac = mesh(new THREE.CylinderGeometry(0.62, 0.55, 3.6, 12), hull, [1.45 * s, -0.05, 1.2], [Math.PI / 2, 0, 0]);
    g.add(nac);
    const ring = mesh(new THREE.TorusGeometry(0.5, 0.09, 6, 14), mat(C.dark), [1.45 * s, -0.05, 3.0]);
    g.add(ring);
    const eng = mesh(new THREE.CircleGeometry(0.46, 16), glow(accent, 3), [1.45 * s, -0.05, 3.02], null, 'engine' + side);
    eng.userData.noInk = true;
    g.add(eng);
    // exhaust flame (scaled per shot)
    const flame = mesh(new THREE.ConeGeometry(0.42, 3.2, 10, 1, true), glow(accent, 2.2, { transparent: true, opacity: 0.55, side: THREE.DoubleSide, depthWrite: false }), [1.45 * s, -0.05, 4.65], [Math.PI / 2, 0, 0], 'flame' + side);
    flame.userData.noInk = true;
    g.add(flame);
    const wing = new THREE.Shape();
    wing.moveTo(0, -1.2); wing.lineTo(2.6, 0.2); wing.lineTo(2.9, 1.5); wing.lineTo(0, 1.4); wing.closePath();
    const wg = new THREE.ExtrudeGeometry(wing, { depth: 0.1, bevelEnabled: false });
    const w = mesh(wg, hull, [1.6 * s, -0.25, 0.6], [Math.PI / 2, 0, 0]);
    w.scale.x = s;
    g.add(w);
    g.add(mesh(new THREE.BoxGeometry(1.4, 0.04, 0.25), glow(accent, 0.8), [3.0 * s, -0.19, 0.9]));
  }
  const ant = new THREE.Group(); ant.name = 'antenna'; ant.position.set(0, 0.75, 2.0);
  ant.add(mesh(new THREE.CylinderGeometry(0.03, 0.05, 1.1, 5), mat(C.dark), [0, 0.5, 0], [-0.4, 0, 0]));
  ant.add(mesh(new THREE.SphereGeometry(0.07, 6, 4), glow(C.red, 2), [0, 0.98, 0.22]));
  g.add(ant);
  ink(g);
  return g;
}

// ---------------------------------------------------------------- drone
export function makeDrone(r = 0.7) {
  const g = new THREE.Group();
  g.name = 'drone';
  g.add(mesh(new THREE.SphereGeometry(r, 14, 10), mat(0x1d1e24, { metalness: 0.4, roughness: 0.3 })));
  const ring = mesh(new THREE.TorusGeometry(r * 0.55, r * 0.12, 6, 16), glow(C.red, 2.5), [0, 0, -r * 0.88]);
  ring.userData.noInk = true;
  g.add(ring);
  const eye = mesh(new THREE.CircleGeometry(r * 0.3, 12), glow(C.red, 3.5), [0, 0, -r * 0.97], [0, Math.PI, 0]);
  eye.userData.noInk = true;
  g.add(eye);
  ink(g);
  return g;
}

// ---------------------------------------------------------------- THE 503
// Leviathan of noise: dome of dead TV screens, one red eye, a toothed maw.
// Origin = centre of the mouth. Faces +Z (toward the hero who flies -Z at it).
export function make503(R = 110) {
  const g = new THREE.Group();
  g.name = 'the503';
  const dark = mat(0x24252b, { roughness: 0.9 });
  const upper = new THREE.Group(); upper.name = 'jawUpper'; g.add(upper);
  const lower = new THREE.Group(); lower.name = 'jawLower'; g.add(lower);
  const dome = mesh(new THREE.SphereGeometry(R, 24, 16, 0, Math.PI * 2, 0, Math.PI / 2), dark, [0, 0, 0], [0, 0, 0]);
  dome.scale.set(1.15, 1.0, 0.9);
  upper.add(dome);
  const chin = mesh(new THREE.SphereGeometry(R, 24, 10, 0, Math.PI * 2, Math.PI / 2, Math.PI / 4), dark);
  chin.scale.set(1.15, 0.7, 0.9);
  lower.add(chin);
  // screen tiles on the dome
  const tileGeo = new THREE.BoxGeometry(R * 0.14, R * 0.1, R * 0.02);
  const tiles = new THREE.InstancedMesh(tileGeo, mat(C.screen, { emissive: 0x666a70, emissiveIntensity: 0.4 }), 160);
  const frame = new THREE.InstancedMesh(new THREE.BoxGeometry(R * 0.16, R * 0.12, R * 0.015), mat(0x5a1a1e), 160);
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), p = new THREE.Vector3(), n = new THREE.Vector3();
  let k = 0;
  for (let i = 0; i < 160; i++) {
    const phi = Math.acos(1 - (i + 0.5) / 160); // upper hemisphere
    const th = i * 2.399963;
    n.set(Math.sin(phi) * Math.sin(th), Math.cos(phi), Math.sin(phi) * Math.cos(th));
    if (n.z > 0.55 && n.y > 0.35 && n.y < 0.8 && Math.abs(n.x) < 0.3) continue; // leave room for the eye
    p.set(n.x * R * 1.15, n.y * R, n.z * R * 0.9);
    q.setFromUnitVectors(new THREE.Vector3(0, 0, 1), n);
    m4.compose(p, q, new THREE.Vector3(1, 1, 1));
    tiles.setMatrixAt(k, m4);
    m4.compose(p.clone().addScaledVector(n, -R * 0.01), q, new THREE.Vector3(1, 1, 1));
    frame.setMatrixAt(k, m4);
    k++;
  }
  tiles.count = frame.count = k;
  upper.add(tiles, frame);
  // eye
  const eye = new THREE.Group(); eye.name = 'eye';
  eye.position.set(0, R * 0.62, R * 0.72);
  eye.lookAt(0, R * 0.62, R * 3);
  eye.add(mesh(new THREE.CircleGeometry(R * 0.26, 24), mat(0x101014)));
  const iris = mesh(new THREE.TorusGeometry(R * 0.19, R * 0.045, 8, 28), glow(C.red, 2.5), [0, 0, R * 0.01], null, 'iris');
  iris.userData.noInk = true;
  eye.add(iris);
  const pupil = mesh(new THREE.CircleGeometry(R * 0.12, 20), glow(C.red, 4), [0, 0, R * 0.012], null, 'pupil');
  pupil.userData.noInk = true;
  eye.add(pupil);
  const lid = mesh(new THREE.CircleGeometry(R * 0.27, 24), mat(0x24252b), [0, 0, R * 0.02], null, 'lid');
  eye.add(lid);
  upper.add(eye);
  // mouth: black void + rows of teeth
  const voidM = mesh(new THREE.CircleGeometry(R * 0.55, 24), basic(0x000000), [0, -R * 0.02, R * 0.55], null, 'maw');
  voidM.scale.y = 0.45;
  voidM.userData.noInk = true;
  g.add(voidM);
  const toothGeo = new THREE.ConeGeometry(R * 0.035, R * 0.16, 5);
  const toothMat = mat(0xdfe3ea);
  for (let i = 0; i < 18; i++) {
    const a = -1 + (2 * i) / 17;
    const x = a * R * 0.68, z = R * (0.78 - 0.18 * a * a);
    const tu = mesh(toothGeo, toothMat, [x, -R * 0.02, z], [Math.PI, 0, 0]);
    upper.add(tu);
    const tl = mesh(toothGeo, toothMat, [x + R * 0.02, R * 0.02, z]);
    lower.add(tl);
  }
  ink(g, 40);
  return g;
}

// ---------------------------------------------------------------- agent orb
export function makeOrb(r = 0.07) {
  const g = new THREE.Group();
  g.name = 'orb';
  const core = mesh(new THREE.SphereGeometry(r, 16, 12), glow(C.orange, 3), null, null, 'core');
  core.userData.noInk = true;
  g.add(core);
  const halo = mesh(new THREE.SphereGeometry(r * 1.35, 16, 12), basic(C.orange, { transparent: true, opacity: 0.14, depthWrite: false }), null, null, 'halo');
  halo.userData.noInk = true;
  g.add(halo);
  const light = new THREE.PointLight(C.orange, 0.6, 3, 1.5);
  light.name = 'light';
  g.add(light);
  return g;
}

// ---------------------------------------------------------------- saxophone (in hand space)
export function makeSax() {
  const g = new THREE.Group();
  g.name = 'sax';
  const brass = mat(C.gold, { metalness: 0.7, roughness: 0.3, emissive: 0x3a2400 });
  g.add(mesh(new THREE.CylinderGeometry(0.025, 0.045, 0.55, 10), brass, [0, -0.2, 0]));
  g.add(mesh(new THREE.TorusGeometry(0.07, 0.045, 8, 12, Math.PI), brass, [0.07, -0.48, 0], [0, 0, Math.PI]));
  g.add(mesh(new THREE.CylinderGeometry(0.1, 0.05, 0.22, 12, 1, true), brass, [0.14, -0.38, 0]));
  g.add(mesh(new THREE.CylinderGeometry(0.012, 0.02, 0.12, 6), mat(C.black), [0, 0.12, 0.03], [0.5, 0, 0]));
  for (let i = 0; i < 5; i++) g.add(mesh(new THREE.CylinderGeometry(0.014, 0.014, 0.01, 8), mat(0xf5e6c0), [0, -0.05 - i * 0.07, -0.035], [Math.PI / 2, 0, 0]));
  ink(g);
  return g;
}

// ---------------------------------------------------------------- misc
export function starfield(n = 1500, radius = 600, size = 1.4) {
  const pos = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    const v = new THREE.Vector3().randomDirection().multiplyScalar(radius * (0.6 + Math.random() * 0.4));
    pos.set([v.x, v.y, v.z], i * 3);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const p = new THREE.Points(g, new THREE.PointsMaterial({ color: 0xffffff, size, sizeAttenuation: false }));
  p.name = 'stars';
  return p;
}

// Soft coloured blob for nebulae / sun glows.
export function blob(color, size, opacity = 0.35) {
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const x = c.getContext('2d');
  const gr = x.createRadialGradient(64, 64, 0, 64, 64, 64);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  x.fillStyle = gr; x.fillRect(0, 0, 128, 128);
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(c), color, transparent: true, opacity, depthWrite: false }));
  s.scale.set(size, size, 1);
  return s;
}

// Text label as a flat plane (for badges, HUD cards). World-sized.
export function labelPlane(text, { w = 1, h = 0.3, bg = 'rgba(255,83,21,0.9)', fg = '#fff', font = 'bold 64px system-ui' } = {}) {
  const c = document.createElement('canvas'); c.width = 512; c.height = Math.round(512 * h / w);
  const x = c.getContext('2d');
  x.fillStyle = bg; x.fillRect(0, 0, c.width, c.height);
  x.fillStyle = fg; x.font = font; x.textAlign = 'center'; x.textBaseline = 'middle';
  x.fillText(text, c.width / 2, c.height / 2, c.width * 0.92);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: tex, transparent: true, side: THREE.DoubleSide, depthWrite: false }));
  m.userData.noInk = true;
  m.userData.label = true; // hidden in the clean export (no text in Seedance references)
  return m;
}

// Helix trail (Itano circus missile). Draw progressively with setDrawRange.
export function helixTrail(from, to, { turns = 3, radius = 3, color = C.red, seg = 160, phase = 0 } = {}) {
  const a = new THREE.Vector3(...from), b = new THREE.Vector3(...to);
  const dir = b.clone().sub(a);
  const up = Math.abs(dir.clone().normalize().y) > 0.9 ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3(0, 1, 0);
  const u = new THREE.Vector3().crossVectors(dir, up).normalize(), v = new THREE.Vector3().crossVectors(dir, u).normalize();
  const pts = [];
  for (let i = 0; i <= seg; i++) {
    const t = i / seg, ang = phase + t * turns * Math.PI * 2, r = radius * Math.sin(Math.PI * t);
    pts.push(a.clone().addScaledVector(dir, t).addScaledVector(u, Math.cos(ang) * r).addScaledVector(v, Math.sin(ang) * r));
  }
  const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({ color }));
  line.userData.seg = seg;
  line.userData.pts = pts;
  return line;
}
// Show a moving window [t-tail, t] of a trail; returns the head position.
export function trailAt(line, t, tail = 0.35) {
  const seg = line.userData.seg;
  const head = Math.max(0, Math.min(seg, Math.floor(t * seg)));
  const start = Math.max(0, Math.floor((t - tail) * seg));
  line.geometry.setDrawRange(start, Math.max(0, head - start + 1));
  line.visible = t > 0;
  return line.userData.pts[head];
}

// Burst: an expanding glow sphere with debris; k in [0..1].
export function makeBurst(color = C.red, size = 3) {
  const g = new THREE.Group(); g.name = 'burst';
  const s = mesh(new THREE.SphereGeometry(1, 12, 8), basic(color, { transparent: true, opacity: 0.8, depthWrite: false }), null, null, 'ball');
  s.userData.noInk = true;
  g.add(s);
  const debris = [];
  for (let i = 0; i < 14; i++) {
    const d = mesh(new THREE.TetrahedronGeometry(0.12 * size), mat(C.dark));
    d.userData.dir = new THREE.Vector3().randomDirection();
    debris.push(d); g.add(d);
  }
  g.userData = { size, debris, ball: s };
  g.visible = false;
  return g;
}
export function burstAt(b, k) {
  b.visible = k > 0 && k < 1;
  if (!b.visible) return;
  const { size, debris, ball } = b.userData;
  ball.scale.setScalar(size * (0.3 + k * 1.2));
  ball.material.opacity = 0.9 * (1 - k);
  for (const d of debris) { d.position.copy(d.userData.dir).multiplyScalar(size * 2.5 * k); d.rotation.set(k * 9, k * 7, 0); }
}

// Expanding ring (sound ring / shockwave). Faces +Z by default.
export function makeRing(color = C.orange, r = 1) {
  const m = mesh(new THREE.TorusGeometry(r, r * 0.04, 6, 48), basic(color, { transparent: true, opacity: 0.9, depthWrite: false }));
  m.userData.noInk = true;
  m.visible = false;
  return m;
}
export function ringAt(m, k, maxScale = 6) {
  m.visible = k > 0 && k < 1;
  if (!m.visible) return;
  m.scale.setScalar(0.2 + k * maxScale);
  m.material.opacity = 0.95 * (1 - k);
}
