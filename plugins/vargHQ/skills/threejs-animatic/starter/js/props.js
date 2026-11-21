// Schematic props built from primitives. Units are metres.
// Axes: up = +Y. A character or vehicle faces -Z in its own space; its right hand is +X.
// Everything here is deterministic: no Math.random (use rng() below if you need scatter).
import * as THREE from 'three';

// Colours are picked so A and B still separate after the Seedance reference is turned greyscale:
// A is light, B is dark, the set is mid grey.
export const C = {
  floor: 0x8a8f99, wall: 0xb4b8c0, wood: 0x9a7b5a, dark: 0x2b2e36, metal: 0xc9ced6,
  a: 0xf0c9a0, aPants: 0x5a4a3a, b: 0x2f5f6f, bPants: 0x1d2228, skin: 0xd8b49a,
  drone: 0x23252b, eye: 0xff4a3d, plant: 0x4f7a4a,
};

export const mat = (color, o = {}) =>
  new THREE.MeshStandardMaterial({ color, roughness: 0.7, metalness: 0.05, flatShading: true, ...o });
export const glow = (color, intensity = 2) =>
  new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: intensity, roughness: 1 });

// Seeded PRNG (mulberry32). Same seed, same scatter, every load and every render.
export function rng(seed = 1) {
  return () => {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Ink outline on every mesh: the grey-box reads like storyboard line art.
const inkMat = new THREE.LineBasicMaterial({ color: 0x0b0c10, transparent: true, opacity: 0.6 });
export function ink(root, angle = 35) {
  const meshes = [];
  root.traverse(o => { if (o.isMesh && !o.userData.noInk) meshes.push(o); });
  for (const m of meshes) {
    const e = new THREE.LineSegments(new THREE.EdgesGeometry(m.geometry, angle), inkMat);
    e.raycast = () => {};
    m.add(e);
  }
  return root;
}

export function mesh(geo, material, pos, rot, name) {
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
// A capsule hanging down (-Y) from its pivot: rotating the pivot swings the limb.
function limb(parent, len, r, material) {
  parent.add(mesh(new THREE.CapsuleGeometry(r, len - 2 * r, 3, 8), material, [0, -len / 2, 0]));
}

// ------------------------------------------------------------------ mannequin
// Root origin = pelvis. Standing: root.position.y = 0.95. Seated: seat height + 0.05.
// Joints live in root.userData.j. Real limbs, head, nose and feet: AI models read a featureless
// capsule as a log or a bollard, and a face without a nose has no readable direction.
export function makeMannequin({ name = 'person', top = C.a, pants = C.aPants, skin = C.skin } = {}) {
  const root = new THREE.Group();
  root.name = name;
  const shirt = mat(top), legs = mat(pants), skinM = mat(skin), shoe = mat(C.dark);
  root.add(mesh(new THREE.BoxGeometry(0.32, 0.16, 0.2), legs));

  const spine = pivot(root, 'spine', [0, 0.05, 0]);
  spine.add(mesh(new THREE.CapsuleGeometry(0.15, 0.32, 3, 10), shirt, [0, 0.27, 0]));
  const neck = pivot(spine, 'neck', [0, 0.52, 0]);
  const head = pivot(neck, 'head', [0, 0.13, 0]);
  head.add(mesh(new THREE.SphereGeometry(0.11, 16, 12), skinM, [0, 0, 0], null, 'face'));
  head.add(mesh(new THREE.ConeGeometry(0.022, 0.05, 6), skinM, [0, -0.005, -0.115], [-Math.PI / 2, 0, 0], 'nose'));
  head.add(mesh(new THREE.SphereGeometry(0.116, 14, 8, 0, Math.PI * 2, 0, Math.PI * 0.45), mat(C.dark), [0, 0.012, 0.01], null, 'hair'));
  for (const s of [-1, 1]) { // eyes: black dots, no outline
    const e = mesh(new THREE.SphereGeometry(0.014, 8, 6), new THREE.MeshBasicMaterial({ color: 0x111111 }), [0.04 * s, 0.02, -0.1]);
    e.userData.noInk = true;
    head.add(e);
  }

  const j = { spine, neck, head };
  for (const [side, s] of [['L', -1], ['R', 1]]) {
    const sh = pivot(spine, 'shoulder' + side, [0.21 * s, 0.45, 0]);
    limb(sh, 0.3, 0.055, shirt);
    const el = pivot(sh, 'elbow' + side, [0, -0.3, 0]);
    limb(el, 0.28, 0.048, skinM);
    const hand = pivot(el, 'hand' + side, [0, -0.29, 0]);
    hand.add(mesh(new THREE.BoxGeometry(0.07, 0.1, 0.04), skinM, [0, -0.03, 0]));
    const hip = pivot(root, 'hip' + side, [0.1 * s, 0, 0]);
    limb(hip, 0.46, 0.07, legs);
    const kn = pivot(hip, 'knee' + side, [0, -0.46, 0]);
    limb(kn, 0.44, 0.06, legs);
    kn.add(mesh(new THREE.BoxGeometry(0.1, 0.07, 0.25), shoe, [0, -0.46, -0.06]));
    Object.assign(j, { ['shoulder' + side]: sh, ['elbow' + side]: el, ['hand' + side]: hand, ['hip' + side]: hip, ['knee' + side]: kn });
  }
  root.userData.j = j;
  return ink(root);
}

// Joint-angle poses, Euler XYZ in radians; a missing joint means 0.
// Hanging limbs (arms, legs): x > 0 swings them forward/up; knee x < 0 bends the shin back;
// elbow x > 0 bends the forearm up. Upright joints (spine, neck): x > 0 leans back / looks up,
// x < 0 leans forward / looks down. head y > 0 turns the face to the character's left.
// Shoulder z: the right arm (+X) lifts outward with z > 0, the left arm with z < 0.
export const POSE = {
  stand: {},
  sit: { hipL: [1.5, 0, 0.06], hipR: [1.5, 0, -0.06], kneeL: [-1.5, 0, 0], kneeR: [-1.5, 0, 0], shoulderL: [0.35, 0, -0.1], shoulderR: [0.35, 0, 0.1], elbowL: [1.0, 0, 0], elbowR: [1.0, 0, 0] },
  handsOnTable: { shoulderL: [0.75, 0, -0.12], elbowL: [0.65, 0, 0], shoulderR: [0.75, 0, 0.12], elbowR: [0.65, 0, 0], spine: [-0.08, 0, 0] },
  gestureR: { shoulderR: [1.15, 0, 0.35], elbowR: [1.25, 0, 0] },
  cupR: { shoulderR: [0.9, 0, 0.08], elbowR: [1.75, 0, 0] },
  lookUp: { neck: [0.5, 0, 0], spine: [0.1, 0, 0] },
  leanBack: { spine: [0.32, 0, 0], neck: [0.2, 0, 0] },
  handsUp: { shoulderL: [2.3, 0, -0.35], elbowL: [0.6, 0, 0], shoulderR: [2.3, 0, 0.35], elbowR: [0.6, 0, 0] },
  point: { shoulderR: [1.55, 0, 0.1], elbowR: [0.1, 0, 0] },
  nod: { neck: [-0.22, 0, 0] },
};
const JOINTS = ['spine', 'neck', 'head', 'shoulderL', 'elbowL', 'handL', 'shoulderR', 'elbowR', 'handR', 'hipL', 'kneeL', 'hipR', 'kneeR'];

// Layered blend: pose(m, [['sit', 1], ['handsOnTable', 1], ['lookUp', k]]).
// Each layer lerps the joints it names toward its value by its weight; later layers win.
export function pose(m, layers) {
  const j = m.userData.j;
  for (const name of JOINTS) {
    let v = [0, 0, 0];
    for (const [p, w] of layers) {
      const src = POSE[p]?.[name];
      if (!src || w <= 0) continue;
      v = v.map((x, i) => x + (src[i] - x) * Math.min(1, w));
    }
    j[name].rotation.set(v[0], v[1], v[2]);
  }
}

// ------------------------------------------------------------------ furniture
export function makeTable({ r = 0.42, h = 0.74 } = {}) {
  const g = new THREE.Group(); g.name = 'table';
  const wood = mat(C.wood), metal = mat(C.metal, { metalness: 0.4, roughness: 0.4 });
  g.add(mesh(new THREE.CylinderGeometry(r, r, 0.035, 32), wood, [0, h, 0], null, 'top'));
  g.add(mesh(new THREE.CylinderGeometry(0.035, 0.035, h, 10), metal, [0, h / 2, 0]));
  g.add(mesh(new THREE.CylinderGeometry(0.26, 0.3, 0.03, 20), metal, [0, 0.015, 0]));
  return ink(g);
}
// Seat at 0.45 m. Faces -Z like a person: the back is at +Z.
export function makeChair() {
  const g = new THREE.Group(); g.name = 'chair';
  const m = mat(C.dark);
  g.add(mesh(new THREE.BoxGeometry(0.44, 0.04, 0.42), m, [0, 0.45, 0]));
  g.add(mesh(new THREE.BoxGeometry(0.44, 0.42, 0.04), m, [0, 0.68, 0.2], [-0.1, 0, 0]));
  for (const [x, z] of [[-0.19, -0.18], [0.19, -0.18], [-0.19, 0.18], [0.19, 0.18]])
    g.add(mesh(new THREE.CylinderGeometry(0.018, 0.018, 0.45, 6), m, [x, 0.225, z]));
  return ink(g);
}
export function makeCup() {
  const g = new THREE.Group(); g.name = 'cup';
  g.add(mesh(new THREE.CylinderGeometry(0.04, 0.032, 0.09, 12), mat(0xf2f2f2), [0, 0.045, 0]));
  return ink(g);
}
export function makePlant(h = 1.2) {
  const g = new THREE.Group(); g.name = 'plant';
  g.add(mesh(new THREE.CylinderGeometry(0.2, 0.16, 0.38, 12), mat(C.dark), [0, 0.19, 0]));
  g.add(mesh(new THREE.ConeGeometry(0.34, h, 8), mat(C.plant), [0, 0.38 + h / 2, 0]));
  return ink(g);
}

// ------------------------------------------------------------------ drone (~0.55 m across, faces -Z)
export function makeDrone() {
  const g = new THREE.Group(); g.name = 'drone';
  g.rotation.order = 'YXZ'; // yaw first, then pitch about its own X: rotation.x < 0 = nose down
  const body = mat(C.drone, { metalness: 0.3, roughness: 0.4 });
  g.add(mesh(new THREE.BoxGeometry(0.2, 0.07, 0.26), body));
  const rotors = [];
  for (const [x, z] of [[-0.2, -0.2], [0.2, -0.2], [-0.2, 0.2], [0.2, 0.2]]) {
    const arm = mesh(new THREE.BoxGeometry(0.03, 0.02, 0.3), body, [x / 2, 0.01, z / 2], [0, Math.atan2(x, z), 0]);
    g.add(arm);
    const rotor = mesh(new THREE.CylinderGeometry(0.11, 0.11, 0.006, 16), mat(0x9aa0aa, { transparent: true, opacity: 0.55 }), [x, 0.05, z]);
    rotor.add(mesh(new THREE.BoxGeometry(0.21, 0.004, 0.025), body));
    rotors.push(rotor);
    g.add(rotor);
  }
  const eye = mesh(new THREE.SphereGeometry(0.03, 10, 8), glow(C.eye, 3), [0, -0.01, -0.13], null, 'eye');
  eye.userData.noInk = true;
  g.add(eye);
  g.userData.rotors = rotors;
  return ink(g);
}

// ------------------------------------------------------------------ text label (review only)
// Name tags and signs for the review UI. Flagged userData.label: hidden in every export,
// because text in a video-to-video reference comes back as garbled letters.
export function labelSprite(text, { color = '#fff', bg = 'rgba(12,14,20,0.8)', h = 0.12 } = {}) {
  const c = document.createElement('canvas'); c.width = 256; c.height = 96;
  const x = c.getContext('2d');
  x.fillStyle = bg; x.fillRect(0, 0, 256, 96);
  x.fillStyle = color; x.font = 'bold 54px ui-monospace, Menlo, monospace';
  x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(text, 128, 50);
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, depthTest: false, transparent: true }));
  s.scale.set(h * 256 / 96, h, 1);
  s.renderOrder = 10;
  s.userData.label = true;
  return s;
}
