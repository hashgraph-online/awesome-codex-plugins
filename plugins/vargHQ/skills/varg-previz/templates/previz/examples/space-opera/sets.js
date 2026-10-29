// Master sets (one per location, per scenes_v4.md). Every shot of a location is
// framed inside the same set, so geography stays consistent between wide and close coverage.
// Each set: { id, title, scene, o (named objects), helperFar, reset() }.
// reset() restores the neutral state; a shot's anim() then poses it for a given time.
import * as THREE from 'three';
import {
  C, mat, glow, basic, ink, makePilot, pose, makeShip, makeDrone, make503, makeOrb, makeSax,
  starfield, blob, labelPlane, helixTrail, makeBurst, makeRing,
} from './props.js';

function scene(bg, fog) {
  const s = new THREE.Scene();
  s.background = bg instanceof THREE.Texture ? bg : new THREE.Color(bg);
  if (fog) s.fog = fog;
  return s;
}
function gradientTex(stops) {
  const c = document.createElement('canvas'); c.width = 4; c.height = 256;
  const x = c.getContext('2d'), g = x.createLinearGradient(0, 0, 0, 256);
  for (const [o, col] of stops) g.addColorStop(o, col);
  x.fillStyle = g; x.fillRect(0, 0, 4, 256);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
function noiseTex(w = 256, h = 128) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const x = c.getContext('2d'), d = x.createImageData(w, h);
  for (let i = 0; i < w * h; i++) { const v = Math.random() * 255; d.data.set([v, v, v, 255], i * 4); }
  x.putImageData(d, 0, 0);
  const t = new THREE.CanvasTexture(c); t.magFilter = THREE.NearestFilter;
  return t;
}
function stripeTex(colors, n = 24) {
  const c = document.createElement('canvas'); c.width = 512; c.height = 8;
  const x = c.getContext('2d');
  for (let i = 0; i < n; i++) { x.fillStyle = colors[i % colors.length]; x.fillRect((512 / n) * i, 0, 512 / n * 0.55, 8); }
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
function box(w, h, d, m, pos, name) {
  const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m);
  b.position.set(...pos);
  if (name) b.name = name;
  return b;
}
function lines(points, color, name) {
  const g = new THREE.BufferGeometry().setFromPoints(points);
  const l = new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color }));
  if (name) l.name = name;
  return l;
}

// Black sphere drawn over everything around the camera (only things with a higher renderOrder show).
function blackout() {
  const m = new THREE.Mesh(new THREE.SphereGeometry(2, 16, 12), basic(0x000000, { side: THREE.BackSide, transparent: true, opacity: 0, depthWrite: false, depthTest: false, fog: false }));
  m.renderOrder = 10; m.visible = false;
  return m;
}

export const SERVICES = ['Runway', 'Higgsfield', 'fal', 'HeyGen', 'Krea', 'Kling', 'Veo', 'Seedance', 'GPT Image', 'Nano Banana', 'Replicate', 'Luma'];

// ================================================================ COCKPIT (scenes A, D, G)
function buildCockpit() {
  const s = scene(0x05060d);
  const o = {};
  s.add(starfield(1200, 300));
  s.add(blob(C.magenta, 260, 0.25).translateZ(-280).translateY(60).translateX(-90));
  s.add(blob(C.cyan, 200, 0.2).translateZ(-260).translateX(120));

  o.hemi = new THREE.HemisphereLight(0x8890b0, 0x101018, 0.6); s.add(o.hemi);
  o.key = new THREE.PointLight(C.red, 6, 6, 1.2); o.key.position.set(0.4, 1.9, -1.0); s.add(o.key);
  o.fill = new THREE.PointLight(0x4060ff, 1.5, 6, 1.5); o.fill.position.set(-1, 1.3, 0.8); s.add(o.fill);
  o.consoleLight = new THREE.PointLight(C.cyan, 1.2, 2, 1.5); o.consoleLight.position.set(0, 0.95, -0.7); s.add(o.consoleLight);

  const shell = mat(0x3a3e4a), panel = mat(0x2a2d36), metal = mat(0xb9c0cc, { metalness: 0.5, roughness: 0.35 });
  const cockpit = new THREE.Group(); cockpit.name = 'cockpit'; s.add(cockpit);
  cockpit.add(box(2.4, 0.1, 2.6, shell, [0, 0.05, -0.2]));                          // floor
  cockpit.add(box(0.6, 0.12, 0.55, panel, [0, 0.48, 0.12]));                         // seat pan
  cockpit.add(box(0.62, 0.95, 0.14, panel, [0, 1.0, 0.45]).rotateX(-0.12));           // seat back
  cockpit.add(box(0.32, 0.22, 0.12, panel, [0, 1.58, 0.52]).rotateX(-0.12));          // headrest
  for (const sx of [-1, 1]) {
    cockpit.add(box(0.08, 0.2, 0.5, panel, [0.34 * sx, 0.62, 0.15]));                // armrests
    cockpit.add(box(0.35, 0.5, 0.9, shell, [0.6 * sx, 0.3, -0.2]));                   // side consoles
    cockpit.add(box(0.12, 0.9, 1.9, shell, [1.05 * sx, 0.6, -0.4]));                  // side walls
  }
  cockpit.add(box(2.2, 1.6, 0.12, shell, [0, 0.9, 0.85]));                            // rear bulkhead
  // main console: half-disc in front of the lap
  const con = new THREE.Mesh(new THREE.CylinderGeometry(0.72, 0.72, 0.09, 40, 1, false, Math.PI / 2, Math.PI), metal);
  con.position.set(0, 0.74, -0.38); con.name = 'console'; cockpit.add(con);
  const conBase = new THREE.Mesh(new THREE.CylinderGeometry(0.6, 0.45, 0.6, 24, 1, false, Math.PI / 2, Math.PI), shell);
  conBase.position.set(0, 0.4, -0.42); cockpit.add(conBase);
  for (const sx of [-1, 1]) {
    const scr = box(0.32, 0.01, 0.2, glow(0x10303a, 0.6), [0.26 * sx, 0.79, -0.72]);
    cockpit.add(scr);
  }
  o.buttons = [];
  [[-0.42, C.cyan], [-0.3, C.magenta], [0.3, C.cyan], [0.42, C.magenta]].forEach(([x, col], i) => {
    const b = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.03, 12), glow(col, 1.2));
    b.position.set(x, 0.8, -0.5); b.name = 'button' + i; cockpit.add(b); o.buttons.push(b);
  });
  o.approve = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.065, 0.04, 20), glow(C.orange, 1.2));
  o.approve.position.set(0, 0.8, -0.62); o.approve.name = 'approve'; cockpit.add(o.approve);
  o.toggles = [];
  for (let i = 0; i < 6; i++) {
    const t = box(0.025, 0.06, 0.025, mat(0xdddddd), [-0.16 + i * 0.064, 0.82, -0.48]);
    t.name = 'toggle' + i; cockpit.add(t); o.toggles.push(t);
  }
  o.slot = box(0.16, 0.02, 0.04, mat(0x111111), [0.17, 0.79, -0.42]); cockpit.add(o.slot);
  // stick (right) and throttle (left)
  o.stick = new THREE.Group(); o.stick.name = 'stick'; o.stick.position.set(0.32, 0.47, -0.3);
  o.stick.add(box(0.035, 0.26, 0.035, mat(C.dark), [0, 0.13, 0]), box(0.06, 0.1, 0.06, mat(C.black), [0, 0.3, 0]));
  cockpit.add(o.stick);
  o.throttle = new THREE.Group(); o.throttle.name = 'throttle'; o.throttle.position.set(-0.33, 0.52, -0.25);
  o.throttle.add(box(0.03, 0.22, 0.03, mat(C.dark), [0, 0.11, 0]), box(0.09, 0.05, 0.05, mat(C.red), [0, 0.24, 0]));
  cockpit.add(o.throttle);
  ink(cockpit);

  // canopy: front half of a dome + ribs
  const CC = new THREE.Vector3(0, 0.95, -0.15), CR = 1.45;
  const glass = new THREE.Mesh(new THREE.SphereGeometry(CR, 40, 20, Math.PI, Math.PI, 0, Math.PI / 2),
    new THREE.MeshStandardMaterial({ color: 0x9fd8ff, transparent: true, opacity: 0.08, roughness: 0.05, side: THREE.DoubleSide, depthWrite: false }));
  glass.position.copy(CC); glass.name = 'canopy'; s.add(glass);
  const ribM = mat(0x4a4f5c);
  for (const ry of [-0.9, 0, 0.9]) {
    const rib = new THREE.Mesh(new THREE.TorusGeometry(CR, 0.035, 6, 30, Math.PI), ribM);
    rib.position.copy(CC); rib.rotation.set(0, Math.PI / 2 + ry, 0); s.add(rib);
  }
  const rim = new THREE.Mesh(new THREE.TorusGeometry(CR, 0.05, 6, 40, Math.PI), ribM);
  rim.position.copy(CC); rim.rotation.set(Math.PI / 2, 0, Math.PI); s.add(rim);

  // spiderweb crack: upper right of the canopy (the hero's scar from h01 to the end)
  const cn = new THREE.Vector3(0.45, 0.55, -0.7).normalize();
  o.crackPoint = CC.clone().addScaledVector(cn, CR - 0.01);
  o.crack = new THREE.Group(); o.crack.name = 'crack'; o.crack.position.copy(o.crackPoint);
  o.crack.lookAt(CC);
  const pts = [];
  const spokes = 11;
  for (let i = 0; i < spokes; i++) {
    const a = (i / spokes) * Math.PI * 2 + Math.random() * 0.3, L = 0.25 + Math.random() * 0.3;
    pts.push(new THREE.Vector3(0, 0, 0), new THREE.Vector3(Math.cos(a) * L, Math.sin(a) * L, 0));
  }
  for (const r of [0.07, 0.15, 0.24]) for (let i = 0; i < spokes; i++) {
    const a0 = (i / spokes) * Math.PI * 2, a1 = ((i + 1) / spokes) * Math.PI * 2;
    pts.push(new THREE.Vector3(Math.cos(a0) * r, Math.sin(a0) * r, 0), new THREE.Vector3(Math.cos(a1) * r * 0.9, Math.sin(a1) * r * 0.9, 0));
  }
  o.crack.add(lines(pts, 0xffffff));
  s.add(o.crack);

  // 50 popup windows on the glass (v11)
  o.popups = new THREE.Group(); o.popups.name = 'popups'; s.add(o.popups);
  for (let i = 0; i < 50; i++) {
    const az = Math.PI + 0.35 + Math.random() * (Math.PI - 0.7), el = 0.15 + Math.random() * 1.0;
    const n = new THREE.Vector3(-Math.cos(az) * Math.cos(el), Math.sin(el), Math.sin(az) * Math.cos(el));
    const p = labelPlane('ERROR 503', { w: 0.32, h: 0.2, bg: 'rgba(200,20,40,0.92)', font: 'bold 70px system-ui' });
    p.position.copy(CC).addScaledVector(n, CR - 0.05 - i * 0.0006);
    p.lookAt(CC);
    o.popups.add(p);
  }
  // HUD: red 503 card, agent HUD, shot plan cards, approve shockwave
  o.card503 = labelPlane('PROVIDER 503', { w: 0.42, h: 0.16, bg: 'rgba(220,20,40,0.9)' });
  o.card503.position.set(0.3, 1.12, -0.85); o.card503.lookAt(0.3, 1.12, -3); s.add(o.card503);
  o.plan = new THREE.Group(); o.plan.name = 'shotPlan'; s.add(o.plan);
  ['SHOT PLAN · 36', 'seedance · kling · veo', '≈ 1 650 credits', 'APPROVE'].forEach((t, i) => {
    const p = labelPlane(t, { w: 0.28, h: 0.065, bg: i === 3 ? 'rgba(255,83,21,0.95)' : 'rgba(255,83,21,0.45)' });
    p.position.set(i % 2 ? 0.2 : -0.2, 1.5 - i * 0.09, -0.7); p.lookAt(p.position.x * 0.5, 1.3, -3); o.plan.add(p);
  });
  o.agentRing = makeRing(C.orange, 0.12); o.agentRing.position.set(0, 0.97, -0.62); s.add(o.agentRing);
  o.shock = makeRing(C.orange, 0.08); o.shock.rotation.x = -Math.PI / 2; o.shock.position.set(0, 0.83, -0.62); s.add(o.shock);

  // props in hand
  o.keycard = box(0.09, 0.005, 0.13, glow(C.cyan, 1.5), [0, 0, 0], 'keycard'); s.add(o.keycard);
  o.brief = box(0.15, 0.004, 0.2, glow(C.orange, 0.8), [0, 0, 0], 'briefCard'); s.add(o.brief);
  const dg = new THREE.BufferGeometry(); const dp = new Float32Array(300 * 3);
  dg.setAttribute('position', new THREE.BufferAttribute(dp, 3));
  o.dust = new THREE.Points(dg, new THREE.PointsMaterial({ color: C.red, size: 0.012 })); o.dust.name = 'pixelDust';
  o.dust.userData.dirs = Array.from({ length: 300 }, () => new THREE.Vector3().randomDirection().multiplyScalar(0.3 + Math.random()));
  s.add(o.dust);

  o.orb = makeOrb(0.035); o.orb.position.set(0, 0.97, -0.62); s.add(o.orb);
  o.pilot = makePilot(); o.pilot.position.set(0, 0.58, 0.12); s.add(o.pilot);
  o.drone = makeDrone(0.55); s.add(o.drone);
  // the 503's passing shadow (v12): a huge dark disc sweeping outside the glass
  o.shadow = new THREE.Mesh(new THREE.CircleGeometry(3, 32), basic(0x000000, { transparent: true, opacity: 0.85, depthWrite: false }));
  o.shadow.rotation.x = Math.PI / 2; s.add(o.shadow);

  const set = {
    id: 'cockpit', title: 'Cockpit', scene: s, o, helperFar: 0.35,
    reset() {
      pose(o.pilot, [['sit', 1], ['stickAndThrottle', 1]]);
      o.pilot.position.set(0, 0.58, 0.12);
      o.pilot.userData.j.head.scale.set(1, 1, 1);
      o.pilot.getObjectByName('eyeR').scale.set(1, 1, 1);
      o.pilot.getObjectByName('mouth').scale.set(1, 1, 1);
      o.crack.visible = true; o.crack.scale.setScalar(1);
      o.popups.children.forEach(p => (p.visible = false));
      o.card503.visible = false; o.plan.visible = false; o.plan.children.forEach(p => (p.visible = true));
      o.agentRing.visible = false; o.shock.visible = false;
      o.keycard.visible = false; o.brief.visible = false; o.dust.visible = false; o.drone.visible = false; o.shadow.visible = false;
      o.stick.rotation.set(0, 0, 0); o.throttle.rotation.set(0, 0, 0);
      o.toggles.forEach(t => t.rotation.set(0, 0, 0));
      o.approve.position.y = 0.8;
      o.orb.scale.setScalar(1); o.orb.getObjectByName('light').intensity = 0.6;
      setMood(this, 'red');
    },
  };
  return set;
}

// Moods: red alarm (act I), orange agent (from c16), calm blue (outro).
export function setMood(set, mood, k = 1) {
  const o = set.o;
  const M = {
    red: { key: C.red, keyI: 7, fill: 0x401020, hemi: 0x5a3040 },
    orange: { key: C.orange, keyI: 6, fill: 0x603018, hemi: 0x6a4a40 },
    calm: { key: 0x6a8cff, keyI: 3, fill: 0x2040a0, hemi: 0x6070a0 },
  };
  const m = M[mood];
  const lerpC = (light, hex) => light.color.lerp(new THREE.Color(hex), k);
  if (k >= 1) { o.key.color.setHex(m.key); o.fill.color.setHex(m.fill); o.hemi.color.setHex(m.hemi); o.key.intensity = m.keyI; }
  else { lerpC(o.key, m.key); lerpC(o.fill, m.fill); lerpC(o.hemi, m.hemi); o.key.intensity += (m.keyI - o.key.intensity) * k; }
}

// ================================================================ SPACE (scenes B, E + x27)
function buildSpace() {
  const s = scene(0x050818);
  const o = {};
  o.stars = starfield(2500, 900, 1.6); s.add(o.stars);
  for (const [c, sz, x, y, z] of [[C.magenta, 700, -300, 100, -800], [C.cyan, 600, 250, -60, -700], [C.violet, 900, 0, 250, -900], [C.cyan, 400, -200, -200, -500]]) {
    const b = blob(c, sz, 0.28); b.position.set(x, y, z); s.add(b);
  }
  s.add(new THREE.HemisphereLight(0x9aa8ff, 0x201030, 0.9));
  const sun = new THREE.DirectionalLight(0xffffff, 2.2); sun.position.set(5, 10, 6); s.add(sun);
  o.redLight = new THREE.PointLight(C.red, 0, 400, 1); o.redLight.position.set(0, 60, -200); s.add(o.redLight);

  o.ship = makeShip({ name: 'hero' }); s.add(o.ship);
  o.shipOrb = makeOrb(0.18); o.shipOrb.position.set(0, 0.55, -1.2); o.ship.add(o.shipOrb);
  o.the503 = make503(110); s.add(o.the503);
  // noise wall that parts to reveal the 503 (v08)
  const nt = noiseTex();
  o.noiseL = new THREE.Mesh(new THREE.PlaneGeometry(300, 260), new THREE.MeshBasicMaterial({ map: nt, transparent: true, opacity: 0.9 }));
  o.noiseR = o.noiseL.clone(); s.add(o.noiseL, o.noiseR);

  o.drones = new THREE.Group(); o.drones.name = 'swarm'; s.add(o.drones);
  for (let i = 0; i < 80; i++) {
    const d = makeDrone(0.7);
    d.userData.base = new THREE.Vector3((Math.random() - 0.5) * 90, (Math.random() - 0.5) * 50, -15 - Math.random() * 140);
    d.userData.phase = Math.random() * Math.PI * 2;
    o.drones.add(d);
  }
  o.trailsRed = new THREE.Group(); s.add(o.trailsRed);
  for (let i = 0; i < 10; i++) o.trailsRed.add(helixTrail([(Math.random() - 0.5) * 30, (Math.random() - 0.5) * 20, -60 - Math.random() * 40], [0, 0, 6], { turns: 2 + Math.random() * 2, radius: 4 + Math.random() * 4, color: C.red, phase: i }));
  o.trailsOrange = new THREE.Group(); s.add(o.trailsOrange);
  // squadron of "models": fighters with service badges
  o.squad = [];
  const slots = [[-9, 1, 5], [9, 1, 5], [-17, 2.5, 11], [17, 2.5, 11], [0, 4, 14]];
  ['Kling', 'fal', 'Veo', 'Runway', 'Seedance'].forEach((nm, i) => {
    const f = makeShip({ name: 'wing_' + nm });
    f.position.set(...slots[i]); f.userData.slot = new THREE.Vector3(...slots[i]);
    const b = labelPlane(nm, { w: 2.6, h: 0.72 }); b.position.set(0, 3.2, 0); b.userData.billboard = true; f.add(b);
    s.add(f); o.squad.push(f);
  });
  o.replacement = makeShip({ name: 'wing_Replicate' });
  const rb = labelPlane('Replicate', { w: 2.6, h: 0.72 }); rb.position.set(0, 3.2, 0); rb.userData.billboard = true; o.replacement.add(rb);
  s.add(o.replacement);
  for (let i = 0; i < 40; i++) {
    const f = o.squad[i % 5].userData.slot;
    o.trailsOrange.add(helixTrail([f.x, f.y, f.z - 3], [(Math.random() - 0.5) * 80, (Math.random() - 0.5) * 40, -40 - Math.random() * 100], { turns: 1.5 + Math.random() * 2, radius: 3 + Math.random() * 5, color: C.orange, phase: i }));
  }
  o.slideTrail = new THREE.Mesh(new THREE.PlaneGeometry(1, 1.2), basic(C.orange, { transparent: true, opacity: 0.7, side: THREE.DoubleSide, depthWrite: false }));
  o.slideTrail.rotation.x = -Math.PI / 2; s.add(o.slideTrail);
  o.burstFal = makeBurst(C.red, 2.2); s.add(o.burstFal);
  o.bursts = Array.from({ length: 24 }, () => { const b = makeBurst(C.red, 2); s.add(b); return b; });
  o.boltC = new THREE.Mesh(new THREE.CapsuleGeometry(0.6, 10, 4, 8), glow(C.cyan, 3)); o.boltC.rotation.x = Math.PI / 2;
  o.boltM = new THREE.Mesh(new THREE.CapsuleGeometry(0.6, 10, 4, 8), glow(C.magenta, 3)); o.boltM.rotation.x = Math.PI / 2;
  s.add(o.boltC, o.boltM);
  o.antennaLoose = o.ship.getObjectByName('antenna');
  o.biter = makeDrone(0.7); s.add(o.biter);
  const sg = new THREE.BufferGeometry(); sg.setAttribute('position', new THREE.BufferAttribute(new Float32Array(120 * 3), 3));
  o.sparks = new THREE.Points(sg, new THREE.PointsMaterial({ color: 0xffd080, size: 3, sizeAttenuation: false }));
  o.sparks.userData.dirs = Array.from({ length: 120 }, () => new THREE.Vector3().randomDirection().multiplyScalar(1 + Math.random() * 3));
  s.add(o.sparks);
  // hyperspace streaks
  const hp = [];
  for (let i = 0; i < 700; i++) {
    const a = Math.random() * Math.PI * 2, r = 8 + Math.random() * 60, z = -Math.random() * 600 + 100, L = 10 + Math.random() * 30;
    hp.push(new THREE.Vector3(Math.cos(a) * r, Math.sin(a) * r, z), new THREE.Vector3(Math.cos(a) * r, Math.sin(a) * r, z - L));
  }
  o.hyper = lines(hp, 0xbfe8ff, 'hyperspace'); s.add(o.hyper);
  o.dark = blackout(); s.add(o.dark);
  o.orbGlow = blob(C.orange, 6, 0.9); o.orbGlow.material.depthTest = false; o.orbGlow.renderOrder = 11; s.add(o.orbGlow);

  // Assault on THE 503 (c24–c26): five fighters hit it from five sides, the hero dives into the mouth.
  // In these shots the monster sits at P503 with its mouth facing the hero's flight line.
  o.P503 = new THREE.Vector3(0, 0, -260);
  o.assault = [
    { station: [-175, 25, -100], hit: [-118, 35, -222] },  // left
    { station: [175, 30, -100], hit: [118, 35, -222] },    // right
    { station: [10, 175, -110], hit: [0, 105, -215] },     // top
    { station: [-10, -140, -90], hit: [0, -62, -195] },    // under the jaw
    { station: [125, 115, -120], hit: [80, 85, -212] },    // upper right
  ].map(a => {
    const st = new THREE.Vector3(...a.station), hit = new THREE.Vector3(...a.hit);
    const trails = new THREE.Group(); s.add(trails);
    for (let i = 0; i < 12; i++) trails.add(helixTrail(a.station, a.hit, { turns: 2 + Math.random() * 2, radius: 6 + Math.random() * 8, color: C.orange, phase: i * 1.1 }));
    const burst = makeBurst(C.orange, 24); s.add(burst);
    return { station: st, hit, trails, burst };
  });

  return {
    id: 'space', title: 'Space · swarm / battle', scene: s, o, helperFar: 3,
    reset() {
      o.ship.position.set(0, 0, 0); o.ship.rotation.set(0, 0, 0); o.ship.visible = true;
      for (const n of ['engineL', 'engineR']) o.ship.getObjectByName(n).material.color.setHex(C.orange);
      o.ship.getObjectByName('flameL').scale.set(1, 1, 1); o.ship.getObjectByName('flameR').scale.set(1, 1, 1);
      o.antennaLoose.position.set(0, 0.75, 2.0); o.antennaLoose.rotation.set(0, 0, 0);
      if (o.antennaLoose.parent !== o.ship) o.ship.add(o.antennaLoose);
      o.the503.position.set(0, 40, -380); o.the503.scale.setScalar(1); o.the503.visible = true; o.the503.rotation.set(0, 0, 0);
      o.the503.getObjectByName('jawUpper').rotation.x = 0; o.the503.getObjectByName('jawLower').rotation.x = 0;
      o.the503.getObjectByName('lid').visible = false;
      o.noiseL.visible = o.noiseR.visible = false;
      o.drones.visible = true;
      o.drones.children.forEach(d => { d.visible = true; d.position.copy(d.userData.base); d.scale.setScalar(1); d.rotation.set(0, 0, 0); });
      o.trailsRed.visible = false; o.trailsOrange.visible = false;
      o.squad.forEach(f => { f.visible = false; f.position.copy(f.userData.slot); f.rotation.set(0, 0, 0); });
      o.replacement.visible = false; o.slideTrail.visible = false;
      o.burstFal.visible = false; o.bursts.forEach(b => (b.visible = false));
      o.boltC.visible = o.boltM.visible = false;
      o.biter.visible = false; o.sparks.visible = false;
      o.hyper.visible = false; o.stars.visible = true;
      o.dark.material.opacity = 0; o.dark.visible = false; o.orbGlow.visible = false;
      o.assault.forEach(a => { a.trails.visible = false; a.burst.visible = false; });
      o.redLight.intensity = 0;
      o.shipOrb.scale.setScalar(1);
    },
  };
}

// ================================================================ CARRIER DECK (scene C)
function buildCarrier() {
  const s = scene(gradientTex([[0, '#1a0b3d'], [0.55, '#5a1a6e'], [0.8, '#d0367a'], [1, '#ff8a3d']]), new THREE.Fog(0x5a1a6e, 120, 600));
  const o = {};
  s.add(new THREE.HemisphereLight(0xc0a0ff, 0x301040, 1.2));
  const back = new THREE.DirectionalLight(0xff70c0, 2.5); back.position.set(0, 20, -60); s.add(back);
  const front = new THREE.DirectionalLight(0x8090ff, 1.0); front.position.set(10, 15, 30); s.add(front);
  // synthwave sun
  const c = document.createElement('canvas'); c.width = c.height = 256;
  const x = c.getContext('2d'), g = x.createLinearGradient(0, 0, 0, 256);
  g.addColorStop(0, '#ffd23d'); g.addColorStop(1, '#ff2a8a');
  x.fillStyle = g; x.beginPath(); x.arc(128, 128, 126, 0, Math.PI * 2); x.fill();
  x.globalCompositeOperation = 'destination-out';
  for (let i = 0; i < 8; i++) x.fillRect(0, 150 + i * 14, 256, 3 + i * 1.2);
  const st = new THREE.CanvasTexture(c); st.colorSpace = THREE.SRGBColorSpace;
  o.sun = new THREE.Mesh(new THREE.PlaneGeometry(260, 260), new THREE.MeshBasicMaterial({ map: st, transparent: true, fog: false }));
  o.sun.position.set(0, 70, -520); s.add(o.sun);
  const sg = blob(0xff60a0, 600, 0.35); sg.position.set(0, 70, -530); s.add(sg);
  const grid = new THREE.GridHelper(2000, 80, C.magenta, 0x8a2aa0); grid.position.y = -25; s.add(grid);

  const deck = new THREE.Group(); deck.name = 'deck'; s.add(deck);
  deck.add(box(40, 3, 240, mat(0x2b2440), [0, -1.5, -60]));
  for (const sx of [-1, 1]) deck.add(box(0.25, 0.08, 240, glow(C.cyan, 2), [19.5 * sx, 0.04, -60]));
  for (let i = 0; i < 6; i++) {
    const lx = -12.5 + i * 5;
    deck.add(box(0.5, 0.04, 70, glow(C.orange, 0.7), [lx, 0.03, -25]));
  }
  for (let z = 30; z > -170; z -= 12) deck.add(box(0.3, 0.04, 6, glow(C.magenta, 1.2), [0, 0.03, z]));
  deck.add(box(8, 14, 30, mat(0x3a3350), [-24, 7, -40])); // island
  ink(deck);
  o.parked = [];
  for (let i = 0; i < 6; i++) for (const sx of [-1, 1]) {
    const f = makeShip({ name: 'parked' }); f.position.set(16.5 * sx, 1.1, -5 - i * 16); f.rotation.y = sx * 1.1; f.scale.setScalar(0.9);
    s.add(f); o.parked.push(f);
  }
  o.launch = [];
  for (let i = 0; i < 6; i++) {
    const f = makeShip({ name: 'launch' + i }); f.userData.base = new THREE.Vector3(-12.5 + i * 5, 1.1, 18);
    const tr = new THREE.Mesh(new THREE.PlaneGeometry(1.2, 1), basic(C.orange, { transparent: true, opacity: 0.6, side: THREE.DoubleSide, depthWrite: false }));
    tr.rotation.x = -Math.PI / 2; tr.name = 'trail'; s.add(tr); f.userData.trail = tr;
    s.add(f); o.launch.push(f);
  }
  // squadron of "models" walking abreast
  o.models = [];
  const hairs = [0x2a1f4a, 0x6a3a8a, 0xc06a40, 0x2a1f4a, 0xd8b060];
  for (let i = 0; i < 5; i++) {
    const m = makePilot({ female: true, suit: 0xf4f6fa, pants: 0xe8ebf0, hair: hairs[i], helmetInHand: true });
    m.rotation.y = Math.PI; // walk toward +Z (camera)
    m.userData.x = (i - 2) * 1.0; m.userData.back = Math.abs(i - 2) * 1.1; // V formation, lead in front
    m.userData.badges = SERVICES.map((t, k) => {
      const b = labelPlane(t, { w: 0.9, h: 0.26, bg: 'rgba(20,20,30,0.85)', fg: '#fff', font: 'bold 56px system-ui' });
      b.position.set(0, 1.02, 0); b.userData.billboard = true; m.add(b); b.userData.k = k; return b;
    });
    const more = labelPlane('+100 more', { w: 0.9, h: 0.26 });
    more.position.set(0, 1.02, 0); more.userData.billboard = true; m.add(more); m.userData.more = more;
    s.add(m); o.models.push(m);
  }
  o.lead = o.models[2];

  return {
    id: 'carrier', title: 'Carrier deck', scene: s, o, helperFar: 2.5,
    reset() {
      o.models.forEach((m, i) => {
        m.visible = true; m.position.set(m.userData.x, 0.95, -6); m.rotation.set(0, Math.PI, 0);
        pose(m, [['stand', 1]]);
        m.userData.badges.forEach(b => (b.visible = b.userData.k === (i * 2) % SERVICES.length));
        m.userData.more.visible = false;
        m.userData.j.helmet.position.set(0.02, -0.08, -0.06);
        if (m.userData.j.helmet.parent !== m.userData.j.handL) m.userData.j.handL.add(m.userData.j.helmet);
      });
      o.launch.forEach(f => { f.position.copy(f.userData.base); f.rotation.set(0, 0, 0); f.visible = true; f.userData.trail.visible = false; });
    },
  };
}

// ================================================================ INSIDE THE BEAST (scene F)
function buildBeast() {
  const s = scene(0x1a0306, new THREE.Fog(0x2a0508, 40, 260));
  const o = {};
  s.add(new THREE.HemisphereLight(0xff8080, 0x200004, 1.1));
  o.redKey = new THREE.PointLight(C.red, 30, 120, 1.2); o.redKey.position.set(0, 6, -60); s.add(o.redKey);
  o.top = new THREE.DirectionalLight(0xffc0c0, 1.2); o.top.position.set(2, 10, 6); s.add(o.top);
  o.white = new THREE.PointLight(0xffffff, 0, 400, 0.6); o.white.position.set(0, 8, -100); s.add(o.white);

  const R = 14, SP = 8;
  const tube = o.tube = new THREE.Mesh(new THREE.CylinderGeometry(R, R, 600, 8, 1, true), mat(0x7a1418, { side: THREE.BackSide }));
  tube.rotation.set(Math.PI / 2, Math.PI / 8, 0); tube.position.z = -200; s.add(tube);
  o.scroll = new THREE.Group(); o.scroll.name = 'tunnelScroll'; s.add(o.scroll);
  const panelGeo = new THREE.BoxGeometry(5.8, 4.6, 0.3);
  const n = 80 * 8;
  const panels = new THREE.InstancedMesh(panelGeo, mat(0xa8adb5, { emissive: 0x555a60, emissiveIntensity: 0.5 }), n);
  const ribs = new THREE.InstancedMesh(new THREE.BoxGeometry(11, 0.7, 0.9), mat(0x3a0a0e), n);
  const strips = new THREE.InstancedMesh(new THREE.BoxGeometry(0.35, 4.5, 0.12), basic(0xffffff), 80 * 4);
  // Octagon faces sit at angles f·45° (tube rotated by 22.5° to match). A dummy with up = tunnel
  // axis, looking at the axis, gives each wall element: x across the face, y along the tunnel.
  const dummy = new THREE.Object3D(); dummy.up.set(0, 0, 1);
  const apo = R * Math.cos(Math.PI / 8);
  const place = (ang, r, z, inst, idx) => {
    dummy.position.set(Math.cos(ang) * r, Math.sin(ang) * r, z);
    dummy.lookAt(0, 0, z); dummy.updateMatrix(); inst.setMatrixAt(idx, dummy.matrix);
  };
  let k = 0, ks = 0;
  for (let i = 0; i < 80; i++) {
    const z = 40 - i * SP;
    for (let f = 0; f < 8; f++) {
      const a = (f / 8) * Math.PI * 2;
      if (f !== 6) place(a, apo - 0.2, z, panels, k); else place(a, apo + 5, z, panels, k); // keep the floor clear
      place(a, apo - 0.3, z + SP / 2, ribs, k);
      k++;
    }
    for (const [ang, col] of [[-Math.PI / 2 - 0.3, C.cyan], [-Math.PI / 2 + 0.3, C.cyan], [0.42, C.magenta], [Math.PI - 0.42, C.magenta]]) {
      place(ang, apo - 0.45, z, strips, ks); strips.setColorAt(ks, new THREE.Color(col)); ks++;
    }
  }
  o.scroll.add(panels, ribs, strips);
  o.SP = SP;
  // core: the giant red eye at the end of the throat
  o.core = new THREE.Group(); o.core.name = 'core'; o.core.position.set(0, 4, -115); s.add(o.core);
  o.core.add(new THREE.Mesh(new THREE.SphereGeometry(13, 24, 16), mat(0x1a1a20)));
  const iris = new THREE.Mesh(new THREE.TorusGeometry(8, 1.8, 8, 32), glow(C.red, 3)); iris.position.z = 11.5; o.core.add(iris);
  o.pupil = new THREE.Mesh(new THREE.CircleGeometry(5.5, 24), glow(C.red, 4)); o.pupil.position.z = 12.6; o.core.add(o.pupil);
  ink(o.core);
  o.cracks = new THREE.Group(); o.cracks.position.z = 13; o.core.add(o.cracks);
  const cp = [];
  for (let i = 0; i < 16; i++) {
    let p = new THREE.Vector3(0, 0, 0);
    let a = Math.random() * Math.PI * 2;
    for (let j = 0; j < 6; j++) {
      a += (Math.random() - 0.5) * 0.9;
      const nq = p.clone().add(new THREE.Vector3(Math.cos(a), Math.sin(a), 0).multiplyScalar(2 + Math.random() * 3));
      cp.push(p, nq); p = nq;
    }
  }
  o.cracks.add(lines(cp, 0xffffff));
  o.laser = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.35, 1, 8), glow(C.red, 5)); s.add(o.laser);
  o.flash = new THREE.Mesh(new THREE.SphereGeometry(80, 16, 12), basic(0xffffff, { side: THREE.BackSide, transparent: true, opacity: 0, depthWrite: false, fog: false }));
  o.flash.renderOrder = 10; s.add(o.flash);
  o.dark = blackout(); s.add(o.dark);
  o.orbGlow = blob(C.orange, 1.6, 0.95); o.orbGlow.material.depthTest = false; o.orbGlow.renderOrder = 11; s.add(o.orbGlow);
  // slit-scan stargate walls (2001)
  o.stargate = new THREE.Group(); s.add(o.stargate);
  const tex = stripeTex(['#ff3df2', '#2ee6ff', '#ffd23d', '#7a4dff', '#ff5315', '#ffffff']);
  tex.repeat.set(6, 1);
  for (const sx of [-1, 1]) {
    const w = new THREE.Mesh(new THREE.PlaneGeometry(500, 60), new THREE.MeshBasicMaterial({ map: tex, side: THREE.DoubleSide, fog: false }));
    w.rotation.set(0, Math.PI / 2, 0); w.position.set(9 * sx, 0, -200); o.stargate.add(w);
  }
  o.stargateTex = tex;

  o.ship = makeShip({ name: 'hero' }); s.add(o.ship);
  o.shipOrb = makeOrb(0.22); o.shipOrb.position.set(0, 0.6, -1.4); o.ship.add(o.shipOrb);
  o.pilot = makePilot(); s.add(o.pilot);
  o.sax = makeSax(); o.sax.position.set(0.02, 0.2, -0.24); o.sax.rotation.set(0.15, 0, -0.25); o.pilot.userData.j.spine.add(o.sax);
  o.drones = new THREE.Group(); s.add(o.drones);
  for (let i = 0; i < 26; i++) {
    const d = makeDrone(0.8);
    d.userData.base = new THREE.Vector3((Math.random() - 0.5) * 18, (Math.random() - 0.5) * 12 + 1, -14 - i * 4.5);
    o.drones.add(d);
  }
  o.rings = Array.from({ length: 8 }, (_, i) => { const r = makeRing(i % 2 ? C.cyan : C.orange, 1); s.add(r); return r; });
  o.bursts = Array.from({ length: 12 }, () => { const b = makeBurst(C.red, 1.6); s.add(b); return b; });

  return {
    id: 'beast', title: 'Inside the beast', scene: s, o, helperFar: 1.5,
    reset() {
      o.ship.position.set(0, 0, 0); o.ship.rotation.set(0, 0, 0);
      for (const n of ['engineL', 'engineR']) o.ship.getObjectByName(n).material.color.setHex(C.orange);
      o.ship.getObjectByName('flameL').scale.set(1, 1, 1); o.ship.getObjectByName('flameR').scale.set(1, 1, 1);
      o.ship.getObjectByName('flameL').visible = o.ship.getObjectByName('flameR').visible = true;
      o.pilot.position.set(0, 1.95, 0.6); o.pilot.rotation.set(0, 0, 0);
      pose(o.pilot, [['stand', 1], ['sax', 1]]);
      o.sax.visible = true;
      o.scroll.position.z = 0;
      o.drones.visible = true;
      o.drones.children.forEach(d => { d.visible = true; d.position.copy(d.userData.base); d.scale.setScalar(1); });
      o.rings.forEach(r => (r.visible = false)); o.bursts.forEach(b => (b.visible = false));
      o.laser.visible = false; o.cracks.visible = false; o.flash.material.opacity = 0; o.flash.visible = false;
      o.dark.visible = false; o.orbGlow.visible = false;
      o.white.intensity = 0; o.redKey.intensity = 30; o.stargate.visible = false;
      o.tube.visible = o.scroll.visible = o.core.visible = o.ship.visible = o.pilot.visible = true;
      s.fog.color.setHex(0x2a0508); s.background.setHex(0x1a0306);
      o.pupil.material.color.setHex(C.red); o.pupil.material.emissive.setHex(C.red);
    },
  };
}

// ================================================================ ODYSSEY (reuse: x32, x34, x35)
function buildOdyssey() {
  const s = scene(0x03040a);
  const o = {};
  s.add(starfield(2000, 700));
  s.add(new THREE.HemisphereLight(0x8090c0, 0x101020, 0.5));
  // A: the eye close-up (x32) at origin
  o.pilot = makePilot(); o.pilot.position.set(0, 0.58, 0); pose(o.pilot, [['sit', 1]]); s.add(o.pilot);
  o.eyeLight = new THREE.PointLight(C.red, 4, 3, 1); o.eyeLight.position.set(0, 1.3, -0.6); s.add(o.eyeLight);
  // B: worlds wall (x34) at x = 200
  o.worlds = new THREE.Group(); o.worlds.position.set(200, 0, 0); s.add(o.worlds);
  const cols = [0xff5315, 0x2ee6ff, 0xff3df2, 0x7a4dff, 0xffd23d, 0x3dff9a, 0xff2a3d, 0x9fd8ff, 0xf2f4f8];
  o.tiles = cols.map((c, i) => {
    const t = labelPlane(['one idea', 'anime', 'noir', 'claymation', 'desert', 'jungle', 'neon city', 'ocean', 'paper'][i], { w: 1, h: 1, bg: '#' + c.toString(16).padStart(6, '0'), fg: '#111', font: 'bold 60px system-ui' });
    o.worlds.add(t); return t;
  });
  const tex = stripeTex(['#ff3df2', '#2ee6ff', '#ffd23d', '#7a4dff', '#ffffff']);
  tex.repeat.set(8, 1);
  o.slitTex = tex;
  for (const sy of [-1, 1]) {
    const w = new THREE.Mesh(new THREE.PlaneGeometry(400, 40), new THREE.MeshBasicMaterial({ map: tex, side: THREE.DoubleSide }));
    w.rotation.set(Math.PI / 2, 0, Math.PI / 2); w.position.set(0, 6 * sy, -150); o.worlds.add(w);
  }
  // C: nebula re-form (x35) at x = 600
  o.neb = new THREE.Group(); o.neb.position.set(600, 0, 0); s.add(o.neb);
  for (const [c, sz, x, y, z] of [[C.magenta, 300, -60, 30, -200], [C.cyan, 260, 70, -20, -180], [C.violet, 400, 0, 60, -260], [C.orange, 180, 20, 10, -150]]) {
    const b = blob(c, sz, 0.4); b.position.set(x, y, z); o.neb.add(b);
  }
  const dl = new THREE.DirectionalLight(0xffffff, 2); dl.position.set(600 + 5, 10, 8); s.add(dl);
  o.ship = makeShip({ name: 'hero' }); o.neb.add(o.ship);
  o.wing = [[-9, 1, 5], [9, 1, 5], [-17, 2.5, 11], [17, 2.5, 11], [0, 4, 14]].map((p, i) => {
    const f = makeShip({ name: 'wing' + i }); f.userData.slot = new THREE.Vector3(...p);
    f.userData.from = new THREE.Vector3(p[0] * 6, p[1] + (i - 2) * 15, p[2] - 120); o.neb.add(f); return f;
  });
  return {
    id: 'odyssey', title: 'Odyssey (reuse)', scene: s, o, helperFar: 2,
    reset() {
      o.eyeLight.color.setHex(C.red); o.eyeLight.intensity = 4;
      o.tiles.forEach(t => (t.visible = false));
      o.wing.forEach(f => { f.position.copy(f.userData.slot); });
    },
  };
}

export function buildSets() {
  const sets = { cockpit: buildCockpit(), space: buildSpace(), carrier: buildCarrier(), beast: buildBeast(), odyssey: buildOdyssey() };
  for (const s of Object.values(sets)) s.reset();
  return sets;
}
