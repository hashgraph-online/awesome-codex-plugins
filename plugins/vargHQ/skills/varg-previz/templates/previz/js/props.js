// Schematic props built from primitives. Units are metres.
// Conventions: forward = -Z (a person's face, a car's nose, a product's label), up = +Y, a character's right hand = +X.
// Everything is grey-box on purpose: the previz locks camera, timing and blocking, never the look.
import * as THREE from 'three';

export const C = {
  white: 0xf2f4f8, light: 0xd9dee6, grey: 0x8a909c, dark: 0x2a2d36, black: 0x16171c,
  skin: 0xe2bc9c, hair: 0x2a1f4a, wood: 0x8a6a4a,
  red: 0xff2a3d, orange: 0xff5315, yellow: 0xffd23d, green: 0x3dff9a, cyan: 0x2ee6ff, blue: 0x4a7dff,
  magenta: 0xff3df2, violet: 0x7a4dff, navy: 0x0b1030, gold: 0xe0a83a,
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
// Outline every mesh: gives the grey-box a storyboard "line art" read. InstancedMesh is skipped (edges are not instanced).
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

export function mesh(geo, material, pos, rot, name) {
  const m = new THREE.Mesh(geo, material);
  if (pos) m.position.set(...pos);
  if (rot) m.rotation.set(...rot);
  if (name) m.name = name;
  return m;
}
export function box(w, h, d, material, pos, name) {
  return mesh(new THREE.BoxGeometry(w, h, d), material, pos, null, name);
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

// ---------------------------------------------------------------- person (1.8 m mannequin)
// Root origin = pelvis. Standing: root.position.y = 0.95. Joints in root.userData.j.
// Eyes + mouth make facing and talking/singing readable from any camera.
export function makePerson({ top = C.white, bottom = C.dark, hair = C.hair, skin = C.skin, long = false, headset = false, name = 'person' } = {}) {
  const root = new THREE.Group();
  root.name = name;
  const jacket = mat(top), dark = mat(bottom), hand = mat(skin), skinM = mat(skin), hairM = mat(hair);
  root.add(mesh(new THREE.BoxGeometry(0.32, 0.16, 0.2), dark, [0, 0, 0]));

  const spine = pivot(root, 'spine', [0, 0.05, 0]);
  spine.add(mesh(new THREE.CapsuleGeometry(long ? 0.14 : 0.16, 0.3, 3, 10), jacket, [0, 0.27, 0]));

  const neck = pivot(spine, 'neck', [0, 0.52, 0]);
  const head = pivot(neck, 'head', [0, 0.13, 0]);
  head.add(mesh(new THREE.SphereGeometry(0.11, 16, 12), skinM, [0, 0, 0], null, 'face'));
  head.add(mesh(new THREE.SphereGeometry(0.122, 14, 10, 0, Math.PI * 2, 0, Math.PI * (long ? 0.62 : 0.5)), hairM, [0, 0.015, 0.012]));
  if (long) head.add(mesh(new THREE.CapsuleGeometry(0.08, 0.16, 3, 8), hairM, [0, -0.08, 0.07]));
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
  if (headset) {
    head.add(mesh(new THREE.TorusGeometry(0.125, 0.008, 4, 16, Math.PI), mat(C.dark), [0, 0.01, 0.01]));
    head.add(mesh(new THREE.CylinderGeometry(0.004, 0.004, 0.12, 4), mat(C.dark), [-0.085, -0.04, -0.07], [Math.PI / 2, 0, 0.9], 'boom'));
  }

  const j = { spine, neck, head };
  for (const [side, s] of [['L', -1], ['R', 1]]) {
    const sh = pivot(spine, 'shoulder' + side, [0.21 * s, 0.45, 0]);
    limb(sh, 0.3, 0.055, jacket);
    const el = pivot(sh, 'elbow' + side, [0, -0.3, 0]);
    limb(el, 0.28, 0.048, jacket);
    const h = pivot(el, 'hand' + side, [0, -0.3, 0]);
    h.add(mesh(new THREE.SphereGeometry(0.05, 8, 6), hand, [0, 0, 0]));
    const hip = pivot(root, 'hip' + side, [0.1 * s, 0, 0]);
    limb(hip, 0.46, 0.07, dark);
    const kn = pivot(hip, 'knee' + side, [0, -0.46, 0]);
    limb(kn, 0.44, 0.06, dark);
    kn.add(mesh(new THREE.BoxGeometry(0.1, 0.07, 0.24), mat(C.black), [0, -0.46, -0.06]));
    Object.assign(j, { ['shoulder' + side]: sh, ['elbow' + side]: el, ['hand' + side]: h, ['hip' + side]: hip, ['knee' + side]: kn });
  }
  root.userData.j = j;
  root.userData.height = 1.8;
  root.position.y = 0.95;
  ink(root);
  return root;
}

// Joint-angle poses. Values are Euler XYZ in radians; missing joints = 0.
// shoulder.x > 0 raises the arm forward; elbow.x > 0 bends the forearm forward/up; a right arm swings inward with negative z;
// hip.x > 0 lifts the thigh forward; knee.x < 0 bends the shin back.
// Seated: put the pelvis at the seat height (root.position.y ≈ seat + 0.05).
export const POSE = {
  stand: {},
  sit: { hipL: [1.45, 0, 0.05], hipR: [1.45, 0, -0.05], kneeL: [-1.4, 0, 0], kneeR: [-1.4, 0, 0], shoulderL: [0.35, 0, -0.15], shoulderR: [0.35, 0, 0.15], elbowL: [0.9, 0, 0], elbowR: [0.9, 0, 0] },
  handsOnTable: { shoulderL: [0.75, 0, -0.1], elbowL: [0.7, 0, 0], shoulderR: [0.75, 0, 0.1], elbowR: [0.7, 0, 0] },
  armsCrossed: { shoulderL: [0.6, 0, 0.5], elbowL: [1.9, 0, 0], shoulderR: [0.6, 0, -0.5], elbowR: [1.9, 0, 0] },
  wave: { shoulderR: [0.2, 0, 2.5], elbowR: [0, 0, 0.6] },
  point: { shoulderR: [1.5, 0, 0.05], elbowR: [0.05, 0, 0] },
  reach: { shoulderR: [1.2, 0, 0.05], elbowR: [0.35, 0, 0] },
  holdUp: { shoulderR: [0.5, 0, -0.1], elbowR: [1.9, 0, 0] },              // show a product / phone next to the face
  phone: { shoulderR: [0.75, 0, -0.25], elbowR: [1.6, 0, 0], neck: [0.35, 0, 0] }, // looking down at a phone
  phoneEar: { shoulderR: [0.6, 0, -0.9], elbowR: [2.45, 0, 0] },
  selfie: { shoulderR: [1.45, 0.35, 0.1], elbowR: [0.25, 0, 0] },
  talk: { shoulderL: [0.35, 0, -0.1], elbowL: [1.1, 0, 0.2], shoulderR: [0.35, 0, 0.1], elbowR: [1.1, 0, -0.2] },
  handsOnHead: { shoulderL: [2.5, 0, -0.75], elbowL: [2.1, 0, 0], shoulderR: [2.5, 0, 0.75], elbowR: [2.1, 0, 0] },
  coverFace: { shoulderL: [1.2, 0, 0.8], elbowL: [2.35, 0, 0], shoulderR: [1.2, 0, -0.8], elbowR: [2.35, 0, 0], neck: [0.3, 0, 0] },
  behindHead: { shoulderL: [2.7, 0, -0.95], elbowL: [2.4, 0, 0], shoulderR: [2.7, 0, 0.95], elbowR: [2.4, 0, 0], spine: [-0.28, 0, 0], neck: [-0.1, 0, 0] },
  armsUp: { shoulderL: [2.9, 0, -0.35], elbowL: [0.2, 0, 0], shoulderR: [2.9, 0, 0.35], elbowR: [0.2, 0, 0], neck: [-0.25, 0, 0] },
  crouch: { hipL: [1.6, 0, 0.15], hipR: [1.6, 0, -0.15], kneeL: [-2.2, 0, 0], kneeR: [-2.2, 0, 0], spine: [0.5, 0, 0], shoulderL: [1.0, 0, -0.3], shoulderR: [1.0, 0, 0.3] },
  lookDown: { neck: [0.45, 0, 0] },
  lookUp: { neck: [-0.45, 0, 0] },
};
const JOINTS = ['spine', 'neck', 'head', 'shoulderL', 'elbowL', 'handL', 'shoulderR', 'elbowR', 'handR', 'hipL', 'kneeL', 'hipR', 'kneeR'];

// Apply a blend of layered poses: pose(person, [['sit',1], ['handsOnTable',1], ['coverFace', k]]).
// Later layers override earlier ones by weight (joint-wise lerp). A layer can also be an object of joint Eulers.
export function pose(person, layers) {
  const j = person.userData.j;
  for (const name of JOINTS) {
    let v = [0, 0, 0];
    for (const [p, w] of layers) {
      const src = typeof p === 'string' ? POSE[p] : p;
      if (!src || !(name in src) || w <= 0) continue;
      const t = src[name];
      v = [v[0] + (t[0] - v[0]) * w, v[1] + (t[1] - v[1]) * w, v[2] + (t[2] - v[2]) * w];
    }
    j[name].rotation.set(v[0], v[1], v[2]);
  }
}
// Walk cycle: one stride per `stride` seconds (on a song, use 2 * BEAT so feet land on beats).
export function walk(person, T, stride = 1, amt = 1) {
  const ph = (T / stride) * Math.PI * 2, j = person.userData.j;
  j.hipL.rotation.x = Math.sin(ph) * 0.42 * amt; j.hipR.rotation.x = -Math.sin(ph) * 0.42 * amt;
  j.kneeL.rotation.x = -Math.max(0, -Math.sin(ph + 0.6)) * 0.7 * amt; j.kneeR.rotation.x = -Math.max(0, Math.sin(ph + 0.6)) * 0.7 * amt;
  j.shoulderL.rotation.x = -Math.sin(ph) * 0.35 * amt; j.shoulderR.rotation.x = Math.sin(ph) * 0.35 * amt;
  person.position.y = 0.95 + Math.abs(Math.cos(ph)) * 0.03 * amt;
}
// Mouth + small head motion so a talking or singing character reads in the previz. beat = seconds per beat.
export function talk(person, lt, amt = 1, beat = 0.5) {
  const m = person.getObjectByName('mouth');
  m.scale.y = 1 + amt * 4 * Math.abs(Math.sin(lt * 11) * Math.sin(lt * 3.3 + 1));
  const j = person.userData.j;
  j.neck.rotation.x += Math.sin(lt * 2 * Math.PI / beat) * 0.04 * amt;
  j.neck.rotation.z += Math.sin(lt * 1.7) * 0.05 * amt;
}

// ---------------------------------------------------------------- vehicles and objects
// Car ~4.5 m long: always clearly bigger than a 1.8 m person. Nose = -Z. Origin on the ground.
export function makeCar({ color = C.light, name = 'car' } = {}) {
  const g = new THREE.Group(); g.name = name;
  const body = mat(color, { metalness: 0.3, roughness: 0.4 }), glass = mat(0x5fb7c4, { transparent: true, opacity: 0.6, roughness: 0.1 });
  g.add(box(1.8, 0.6, 4.5, body, [0, 0.55, 0], 'body'));
  g.add(box(1.6, 0.55, 2.3, glass, [0, 1.12, 0.25], 'cabin'));
  for (const [x, z] of [[-0.85, -1.4], [0.85, -1.4], [-0.85, 1.4], [0.85, 1.4]]) {
    g.add(mesh(new THREE.CylinderGeometry(0.34, 0.34, 0.24, 14), mat(C.black), [x, 0.34, z], [0, 0, Math.PI / 2]));
  }
  for (const s of [-1, 1]) {
    const hl = mesh(new THREE.CircleGeometry(0.12, 10), glow(0xfff4d0, 2), [0.6 * s, 0.62, -2.26], [0, Math.PI, 0], 'headlight');
    hl.userData.noInk = true; g.add(hl);
    const tl = mesh(new THREE.CircleGeometry(0.1, 10), glow(C.red, 1.5), [0.65 * s, 0.65, 2.26], null, 'taillight');
    tl.userData.noInk = true; g.add(tl);
  }
  g.userData.height = 1.45;
  ink(g);
  return g;
}

// Hero product stand-in. kind: 'bottle' | 'can' | 'box' | 'phone' | 'cup'. Label faces -Z. Origin on its base.
export function makeProduct({ kind = 'bottle', color = C.orange, h = 0.25, name = 'product' } = {}) {
  const g = new THREE.Group(); g.name = name;
  const m = mat(color, { roughness: 0.35, metalness: 0.2 }), cap = mat(C.dark);
  if (kind === 'bottle') {
    g.add(mesh(new THREE.CylinderGeometry(h * 0.2, h * 0.2, h * 0.62, 20), m, [0, h * 0.31, 0]));
    g.add(mesh(new THREE.CylinderGeometry(h * 0.08, h * 0.2, h * 0.2, 20), m, [0, h * 0.72, 0]));
    g.add(mesh(new THREE.CylinderGeometry(h * 0.085, h * 0.085, h * 0.1, 12), cap, [0, h * 0.87, 0]));
  } else if (kind === 'can') {
    g.add(mesh(new THREE.CylinderGeometry(h * 0.27, h * 0.27, h, 20), m, [0, h / 2, 0]));
  } else if (kind === 'cup') {
    g.add(mesh(new THREE.CylinderGeometry(h * 0.4, h * 0.3, h, 20), m, [0, h / 2, 0]));
    g.add(mesh(new THREE.CylinderGeometry(h * 0.42, h * 0.42, h * 0.08, 20), cap, [0, h, 0]));
  } else if (kind === 'phone') {
    g.add(box(h * 0.48, h, h * 0.04, mat(C.black), [0, h / 2, 0]));
    const scr = box(h * 0.44, h * 0.94, 0.002, glow(C.cyan, 0.8), [0, h / 2, -h * 0.021], 'screen');
    scr.userData.noInk = true; g.add(scr);
  } else {
    g.add(box(h * 0.7, h, h * 0.35, m, [0, h / 2, 0]));
  }
  // white label band on the front, so "label to camera" is checkable in every shot
  if (kind === 'bottle' || kind === 'can' || kind === 'cup') {
    const r = kind === 'bottle' ? h * 0.205 : kind === 'can' ? h * 0.275 : h * 0.36;
    const lab = mesh(new THREE.CylinderGeometry(r, r, h * 0.2, 20, 1, true, Math.PI * 0.75, Math.PI * 0.5), basic(C.white, { side: THREE.DoubleSide }), [0, h * 0.4, 0], null, 'label');
    lab.userData.noInk = true; g.add(lab);
  }
  g.userData.height = h;
  ink(g);
  return g;
}

export function makeTable({ w = 1.4, d = 0.8, h = 0.75, color = C.wood } = {}) {
  const g = new THREE.Group(); g.name = 'table';
  const m = mat(color);
  g.add(box(w, 0.05, d, m, [0, h, 0], 'top'));
  for (const [x, z] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) g.add(box(0.05, h, 0.05, m, [x * (w / 2 - 0.06), h / 2, z * (d / 2 - 0.06)]));
  ink(g);
  return g;
}
// Seat height 0.45 m. The sitter faces -Z.
export function makeChair({ color = C.dark } = {}) {
  const g = new THREE.Group(); g.name = 'chair';
  const m = mat(color);
  g.add(box(0.45, 0.05, 0.45, m, [0, 0.45, 0]));
  g.add(box(0.45, 0.5, 0.05, m, [0, 0.72, 0.2]));
  for (const [x, z] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) g.add(box(0.04, 0.45, 0.04, m, [x * 0.2, 0.225, z * 0.2]));
  ink(g);
  return g;
}

// ---------------------------------------------------------------- environment helpers
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
// Soft coloured blob for sky glows, sun discs, practical lights.
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
// Vertical gradient for a sky / backdrop: stops = [[0, '#hex'], [1, '#hex']] from top to bottom.
export function gradientTex(stops) {
  const c = document.createElement('canvas'); c.width = 4; c.height = 256;
  const x = c.getContext('2d'), g = x.createLinearGradient(0, 0, 0, 256);
  for (const [o, col] of stops) g.addColorStop(o, col);
  x.fillStyle = g; x.fillRect(0, 0, 4, 256);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

// Text label as a flat plane (signs, UI cards, name badges). World-sized.
// Flagged userData.label: hidden in the clean export, because reference clips must carry no text.
// Set userData.billboard = true to make it face whichever camera renders it.
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
  m.userData.label = true;
  return m;
}

// ---------------------------------------------------------------- effects (all driven by a 0..1 progress so scrubbing is exact)
// Helix trail (missile, spark, magic). Draw progressively with trailAt.
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
// Expanding ring (shockwave, sound ring, reveal). Faces +Z by default.
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
// Sphere around the camera for blackouts / flashes; only objects with a higher renderOrder show through.
export function blackout(color = 0x000000) {
  const m = new THREE.Mesh(new THREE.SphereGeometry(2, 16, 12), basic(color, { side: THREE.BackSide, transparent: true, opacity: 0, depthWrite: false, depthTest: false, fog: false }));
  m.renderOrder = 10; m.visible = false; m.name = 'blackout';
  return m;
}
