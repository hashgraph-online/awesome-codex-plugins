// cell.js: the subject. An animal cell built from procedural geometry, one part per beat.
// Units: 1 = 1 µm. Sizes and simplifications come from factsheet.md (S1-S7).
// build(ctx) -> { anchors, update(t) }. update(t) is a pure function of t (see lib/explainer.js).
import * as THREE from 'three';
import { shell, solid, glow, bokeh, setU } from './lib/materials.js';
import { cameraPath } from './lib/explainer.js';

export async function build(ctx) {
  const { scene, story, rng, clamp, lerp, smooth, ease, win, env } = ctx;
  const P = story.palette;
  const T = story.timing; // entrance windows per part, seconds
  const R = 10;           // cell radius (20 µm cell, F10)
  const Y = new THREE.Vector3(0, 1, 0);
  const V = (x, y, z) => new THREE.Vector3(x, y, z);
  const rand = rng(20261110);
  const hash = (i) => { const r = rng(9973 * (i + 1)); r(); return r(); };
  const tmp = new THREE.Object3D();

  // ---------- layout (µm). Heroes are the parts the camera visits; everything else is scattered around them ----------
  const Cn = V(-1.7, 0.6, -0.8), rn = 4.3;                       // nucleus 8.6 µm
  const No = V(-0.3, 0.55, -0.15);                               // nucleolus, local to the nucleus
  const dirG = V(0.75, -0.25, 0.6).normalize();
  const G = Cn.clone().addScaledVector(dirG, rn + 2.2);          // Golgi beside the nucleus...
  const Cc = Cn.clone().addScaledVector(dirG, rn + 0.8);         // ...at the centrosome
  const M0 = V(5.2, 2.6, 3.2);                                   // hero mitochondrion
  const R0 = M0.clone().add(V(-1.25, -0.55, 0.95));              // hero polysome
  const L0 = V(1.4, 0.2, 6.4);                                   // hero lysosome cluster
  const erPole = V(-0.7, 0.45, 0.55).normalize();                // rough ER wraps the nucleus on this side
  const camEnd = story.camera[story.camera.length - 1];
  const wd = V(camEnd.pos[0] - Cn.x, 0, camEnd.pos[2] - Cn.z).normalize().applyAxisAngle(Y, THREE.MathUtils.degToRad(story.cutTurn ?? 0)); // the final wedge opens here

  // ---------- membrane: a lumpy sphere, radius as a function of direction ----------
  const memR = (d) => R * (1 + 0.035 * Math.sin(2.1 * d.x + 0.6) * Math.cos(1.7 * d.y - 0.3) + 0.03 * Math.sin(2.7 * d.z + 1.1 * d.y + 0.4) + 0.018 * Math.sin(4.1 * d.x - 3.3 * d.z));
  const insideCell = (p, margin = 0) => p.length() < memR(p.clone().normalize()) - margin;
  const memGeo = new THREE.IcosahedronGeometry(1, 64);
  { const a = memGeo.attributes.position, d = new THREE.Vector3(); for (let i = 0; i < a.count; i++) { d.fromBufferAttribute(a, i).normalize(); a.setXYZ(i, ...d.multiplyScalar(memR(d)).toArray()); } memGeo.computeVertexNormals(); }
  const memMat = shell({ color: P.membrane, rim: P.membraneRim, edge: P.orange, opacity: 0.16, rimPower: 2.4, rimStrength: 1.5, noise: 0.32, speck: 0.8, specular: 0.16, revealNoise: 0.018, edgeWidth: 0.02, axis: V(-0.2, -1, -0.1).normalize(), range: [-R * 1.05, R * 1.05] });
  const membrane = new THREE.Mesh(memGeo, memMat); membrane.renderOrder = 5; membrane.userData.noDepth = true;
  scene.add(membrane);

  // ---------- nucleus: envelope with pores, chromatin, nucleolus ----------
  const nucleus = new THREE.Group(); nucleus.position.copy(Cn); scene.add(nucleus);
  const envMat = shell({ color: P.nucleus, rim: P.nucleusRim, edge: P.orange, opacity: 0.9, rimPower: 2.2, rimStrength: 1.0, noise: 0.8, speck: 0.6, specular: 0.25, range: [-rn * 1.2, rn * 1.2] });
  const envelope = new THREE.Mesh(new THREE.IcosahedronGeometry(rn, 40), envMat); envelope.renderOrder = 3; envelope.userData.noDepth = true;
  nucleus.add(envelope);
  const NPORE = 140, poreMat = solid({ color: P.pore, rim: P.nucleusRim, rimStrength: 0.4, spec: 0.1, cap: P.pore });
  const pores = new THREE.InstancedMesh(new THREE.TorusGeometry(0.095, 0.032, 8, 20), poreMat, NPORE); nucleus.add(pores);
  const poreDirs = []; for (let i = 0; i < NPORE; i++) { const y = 1 - (2 * (i + 0.5)) / NPORE, r = Math.sqrt(1 - y * y), th = i * 2.399963; poreDirs.push(V(Math.cos(th) * r, y, Math.sin(th) * r)); }
  const chromMat = glow({ color: P.chromatin, strength: 0.24 });
  const chromatin = new THREE.Group(); nucleus.add(chromatin);
  for (let c = 0; c < 26; c++) {
    const pts = []; let p = V(rand() - 0.5, rand() - 0.5, rand() - 0.5).multiplyScalar(5); const dir = V(rand() - 0.5, rand() - 0.5, rand() - 0.5).normalize();
    for (let k = 0; k < 16; k++) { dir.add(V(rand() - 0.5, rand() - 0.5, rand() - 0.5).multiplyScalar(1.1)).normalize(); p = p.clone().addScaledVector(dir, 0.55); if (p.length() > rn - 0.4) p.multiplyScalar((rn - 0.4) / p.length()); if (p.distanceTo(No) < 1.3) p.add(p.clone().sub(No).setLength(0.6)); pts.push(p); }
    chromatin.add(new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 140, 0.024, 5), chromMat));
  }
  const nolGeo = new THREE.IcosahedronGeometry(1.1, 6);
  { const a = nolGeo.attributes.position, d = new THREE.Vector3(); for (let i = 0; i < a.count; i++) { d.fromBufferAttribute(a, i).normalize(); const k = 1 + 0.05 * Math.sin(5 * d.x + 1) * Math.sin(4 * d.y + 2) + 0.035 * Math.sin(7 * d.z + 3 * d.x); a.setXYZ(i, ...d.multiplyScalar(1.1 * k).toArray()); } nolGeo.computeVertexNormals(); }
  const nolMat = solid({ color: P.nucleolus, emissive: P.nucleolusGlow, rim: '#ffd9b0', rimStrength: 0.7, grain: 0.45, spec: 0.25, cap: P.nucleolus });
  const nucleolus = new THREE.Mesh(nolGeo, nolMat); nucleolus.position.copy(No); nucleus.add(nucleolus);
  nolMat.transparent = true; nucleolus.renderOrder = 6; chromatin.children.forEach(c => (c.renderOrder = 6)); // drawn after the cut faces

  // ---------- rough ER: wavy sheets wrapped around the nucleus, joined to it, studded with ribosomes ----------
  const erU = new THREE.Vector3().crossVectors(erPole, Y).normalize(), erW = new THREE.Vector3().crossVectors(erPole, erU);
  const erLayers = [0, 1, 2, 3].map(k => ({ r: rn + 0.55 + 0.5 * k, th0: 0.1 + 0.06 * k, th1: 1.55 - 0.16 * k, ph0: 0.5 * k + 0.2, ph1: 0.5 * k + 0.2 + 5.0 - 0.3 * k, k }));
  const erPoint = (L, u, v, out = 0) => { // u, v in 0..1 over the layer patch
    const th = lerp(L.th0, L.th1, v), ph = lerp(L.ph0, L.ph1, u);
    const dir = erPole.clone().multiplyScalar(Math.cos(th)).addScaledVector(erU, Math.sin(th) * Math.cos(ph)).addScaledVector(erW, Math.sin(th) * Math.sin(ph));
    const r = L.r + 0.12 * Math.sin(5 * ph + 1.7 * L.k) * Math.sin(3.0 * th + L.k) + 0.05 * Math.sin(11 * ph + 4 * th) + out;
    return dir.multiplyScalar(r).add(Cn);
  };
  const erMat = shell({ color: P.er, rim: P.erRim, edge: P.erEdge, opacity: 0.16, rimPower: 1.8, rimStrength: 1.3, noise: 1.1, speck: 0.5, specular: 0.2, revealNoise: 0.05, edgeWidth: 0.025, edgeFade: 0.05, mode: 1, origin: Cn, range: [rn, rn + 2.6] });
  const er = new THREE.Group(); scene.add(er);
  for (const L of erLayers) {
    const NU = 180, NV = 44, g = new THREE.BufferGeometry(), pos = [], uv = [], idx = [];
    for (let j = 0; j <= NV; j++) for (let i = 0; i <= NU; i++) { pos.push(...erPoint(L, i / NU, j / NV).toArray()); uv.push(i / NU, j / NV); }
    for (let j = 0; j < NV; j++) for (let i = 0; i < NU; i++) { const a = j * (NU + 1) + i, b = a + 1, c = a + NU + 1, d = c + 1; idx.push(a, c, b, b, c, d); }
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); g.setIndex(idx); g.computeVertexNormals();
    const m = new THREE.Mesh(g, erMat); m.renderOrder = 2; m.userData.noDepth = true; er.add(m);
  }
  for (let b = 0; b < 7; b++) { // the ER membrane is continuous with the outer nuclear membrane (F4a)
    const p1 = erPoint(erLayers[0], 0.1 + 0.12 * b, 0.25 + 0.08 * (b % 3)), d = p1.clone().sub(Cn).normalize(), p0 = Cn.clone().addScaledVector(d, rn - 0.05);
    const m = new THREE.Mesh(new THREE.TubeGeometry(new THREE.LineCurve3(p0, p1), 4, 0.14, 12), erMat); m.renderOrder = 2; m.userData.noDepth = true; er.add(m);
  }

  // ---------- Golgi: one stack of 5 bent cisternae with swollen rims, plus vesicles ----------
  const golgi = new THREE.Group(); golgi.position.copy(G); golgi.quaternion.setFromUnitVectors(Y, dirG); scene.add(golgi);
  const golgiMat = solid({ color: P.golgi, rim: '#c8fff4', rimStrength: 0.9, spec: 0.35, uvShade: 0.8, cap: P.golgi });
  const cisternae = [];
  for (let k = 0; k < 5; k++) { // a flat sac with a swollen rim, elliptical, bent like a shallow banana
    const a = 1.4 - 0.13 * Math.abs(k - 1.4), h = 0.03, b = 0.07, prof = [];
    prof.push(new THREE.Vector2(0.001, h)); for (let i = 1; i <= 10; i++) prof.push(new THREE.Vector2((a - b) * i / 10, h));
    for (let i = 0; i <= 12; i++) { const an = Math.PI / 2 - (Math.PI * i) / 12; prof.push(new THREE.Vector2(a - b + b * 1.3 * Math.cos(an), b * 1.1 * Math.sin(an))); }
    for (let i = 10; i >= 1; i--) prof.push(new THREE.Vector2((a - b) * i / 10, -h)); prof.push(new THREE.Vector2(0.001, -h));
    prof.reverse(); // LatheGeometry wants the profile bottom -> top, or every face is a back face (flat cut-cap colour)
    const g = new THREE.LatheGeometry(prof, 80), p = g.attributes.position;
    for (let i = 0; i < p.count; i++) { const x = p.getX(i), z = p.getZ(i) * 0.5; p.setXYZ(i, x, p.getY(i) - x * x * 0.22 - z * z * 0.1, z); }
    g.computeVertexNormals();
    const mat = k === 4 ? golgiMat : solid({ color: new THREE.Color(P.golgiCis).lerp(new THREE.Color(P.golgi), k / 4), rim: '#c8fff4', rimStrength: 0.9, spec: 0.35, uvShade: 0.8, cap: P.golgi }); // cis (nucleus side) to trans
    const m = new THREE.Mesh(g, mat); m.userData.y = (k - 2) * 0.3; golgi.add(m); cisternae.push(m);
  }
  const vesicles = [], vesMat = solid({ color: P.golgi, rim: '#c8fff4', rimStrength: 0.9, spec: 0.35, cap: P.golgi });
  for (let v = 0; v < 12; v++) {
    const ang = rand() * Math.PI * 2, rr = 1.05 + rand() * 0.55, s = 0.08 + rand() * 0.06;
    const m = new THREE.Mesh(new THREE.IcosahedronGeometry(s, 3), vesMat); const x = Math.cos(ang) * rr; m.position.set(x, 0.75 + rand() * 0.45 - x * x * 0.22, Math.sin(ang) * rr * 0.45); golgi.add(m); vesicles.push(m);
  }

  // ---------- centrosome + microtubules (the cytoskeleton hint) ----------
  const centMat = solid({ color: P.orange, emissive: '#4a1000', rimStrength: 0.4 });
  const centrosome = new THREE.Group(); centrosome.position.copy(Cc); scene.add(centrosome);
  for (const r of [[0, 0, 0], [Math.PI / 2, 0, 0.4]]) { const m = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 0.45, 18), centMat); m.rotation.set(...r); centrosome.add(m); }
  const mtMat = glow({ color: P.cyto, strength: 0.24 });
  const microtubules = [];
  for (let i = 0, tries = 0; microtubules.length < 36 && tries < 4000; tries++) {
    const d = V(rand() - 0.5, rand() - 0.5, rand() - 0.5).normalize(), end = d.clone().multiplyScalar(memR(d) * 0.93);
    const seg = new THREE.Line3(Cc, end), q = new THREE.Vector3(); seg.closestPointToPoint(Cn, true, q);
    if (q.distanceTo(Cn) < rn + 0.35 || end.distanceTo(Cc) < 5) continue;
    const mid = Cc.clone().lerp(end, 0.5).add(V(rand() - 0.5, rand() - 0.5, rand() - 0.5).multiplyScalar(0.9));
    if (!insideCell(mid, 0.6)) continue;
    const g = new THREE.TubeGeometry(new THREE.QuadraticBezierCurve3(Cc.clone(), mid, end), 90, 0.04, 5);
    const m = new THREE.Mesh(g, mtMat); m.userData.full = g.index.count; m.userData.h = hash(i++); scene.add(m); microtubules.push(m);
  }

  // ---------- anchors for labels and camera keys ----------
  const memDir = V(-0.85, 0.35, 0.4).normalize();
  const anchors = {
    cell: V(0, 0, 0), nucleus: Cn.clone(), nucleolusC: Cn.clone().add(No), centrosome: Cc.clone(), golgi: G.clone(), mito: M0.clone(), lyso: L0.clone(),
    ribo: R0.clone().add(V(Math.cos(3) * 0.2, 0, Math.sin(3) * 0.2)), // the 5th ribosome of the polysome
    membrane: memDir.clone().multiplyScalar(memR(memDir)),
    nucleusSurf: Cn.clone().addScaledVector(V(0.35, 0.62, 0.7).normalize(), rn),
    nucleolus: Cn.clone().add(No).add(V(0.25, 0.75, 0.6)),
    er: erPoint(erLayers[3], 0.5, 0.42, 0.05),
    erLook: Cn.clone().addScaledVector(erPole, rn + 1.0),
    golgiCam: G.clone().add(V(0, 0, 1).applyQuaternion(golgi.quaternion).multiplyScalar(story.golgiCamDist ?? 4.6)).addScaledVector(dirG, 0.9),
    nucleusCut: null, nucleolusCut: null,
    mt: (() => { // a point 2.2 µm out along the microtubule that points most toward the cytoskeleton shot's camera
      const toCam = V(12, 10, 36).sub(Cc).normalize(); let best = null, bd = -2;
      for (const m of microtubules) { const a = m.geometry.attributes.position; for (let i = 0; i < a.count; i += 6) { const q = new THREE.Vector3().fromBufferAttribute(a, i); if (Math.abs(q.distanceTo(Cc) - 2.2) < 0.15) { const d = q.clone().sub(Cc).normalize().dot(toCam); if (d > bd) { bd = d; best = q; } break; } } }
      return best || Cc.clone(); })(),
  };

  { // anchors on the cut faces of the final wedge (the face that turns toward the camera)
    const a = THREE.MathUtils.degToRad(story.cutDegrees) / 2, e1 = wd.clone().applyAxisAngle(Y, a), e2 = wd.clone().applyAxisAngle(Y, -a);
    const ce = V(camEnd.pos[0] - Cn.x, 0, camEnd.pos[2] - Cn.z).normalize(), face = Math.abs(e1.dot(ce)) < Math.abs(e2.dot(ce)) ? e1 : e2;
    anchors.nucleusCut = Cn.clone().addScaledVector(face, rn * 0.72).addScaledVector(Y, rn * 0.42);
    anchors.nucleolusCut = Cn.clone().add(No).addScaledVector(face, 0.55);
  }

  // keep the camera path clear: scattered parts placed later must not sit within a few µm of the lens
  const camAt = cameraPath(story.camera, anchors), path = [];
  for (let t = 0; t <= story.duration; t += 1 / 30) path.push(new THREE.Vector3(...camAt(t).pos));
  const nearPath = (p, r) => path.some(c => c.distanceTo(p) < r);

  // ---------- placement: heroes first, then scatter with clearance ----------
  const placed = [{ p: R0, r: 0.6 }];
  const clear = (p, r) => !nearPath(p, r + 1.0) && placed.every(o => o.p.distanceTo(p) > o.r + r) && p.distanceTo(Cn) > rn + 2.4 + r * 0.2 && p.distanceTo(G) > 2.0 + r && insideCell(p, 1.0 + r) && p.distanceTo(Cc) > 0.8 + r;
  const randIn = () => V(rand() * 2 - 1, rand() * 2 - 1, rand() * 2 - 1).multiplyScalar(R);

  // lysosomes: a translucent membrane sac holding dense enzyme granules (hero cluster of 3, then 9 scattered)
  const lysoMat = shell({ color: P.lyso, rim: P.lysoRim, edge: P.orange, opacity: 0.32, rimPower: 1.8, rimStrength: 1.4, noise: 3.0, speck: 0.4, specular: 0.3 });
  const granMat = solid({ color: P.lysoGranule, rim: '#ffe2c0', rimStrength: 0.4, spec: 0.2, emissive: P.lysoGlow });
  const lysos = [], granules = [];
  const heroL = [[L0, 0.42], [L0.clone().add(V(0.95, -0.55, -0.6)), 0.3], [L0.clone().add(V(-0.55, -0.75, -1.1)), 0.34]];
  for (let i = 0, tries = 0; lysos.length < 12 && tries < 5000; tries++) {
    const h = heroL[lysos.length]; const p = h ? h[0] : randIn(), r = h ? h[1] : 0.25 + rand() * 0.15;
    if (!h && !clear(p, r + 0.2)) continue;
    const m = new THREE.Mesh(new THREE.IcosahedronGeometry(r, 5), lysoMat); m.position.copy(p); m.renderOrder = 1; m.userData.noDepth = true; m.userData.h = hash(300 + i++);
    for (let j = 0; j < 14; j++) { const q = V(rand() - 0.5, rand() - 0.5, rand() - 0.5).normalize().multiplyScalar(r * 0.62 * Math.cbrt(rand())); granules.push({ l: lysos.length, p: q, s: r * (0.1 + 0.08 * rand()) }); }
    scene.add(m); lysos.push(m); placed.push({ p, r: r + 0.2 });
  }
  lysos.forEach((m, i) => (anchors[`lyso${i}`] = m.position.clone())); // every lysosome can anchor a label
  const gran = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1, 2), granMat, granules.length); scene.add(gran);

  // mitochondria: bent capsules with cristae lines (hero first)
  const mitoMat = solid({ color: P.mito, rim: '#ffc9a8', rimStrength: 0.75, stripes: 0.8, stripeFreq: 17, spec: 0.35, cap: P.mitoCap, emissive: '#160400' });
  const mitos = [];
  const makeMito = (len, bend) => { const g = new THREE.CapsuleGeometry(0.35, len - 0.7, 12, 28), a = g.attributes.position; for (let i = 0; i < a.count; i++) { const y = a.getY(i); a.setX(i, a.getX(i) + bend * y * y); } g.computeVertexNormals(); return g; };
  for (let i = 0, tries = 0; mitos.length < 18 && tries < 6000; tries++) {
    const hero = mitos.length === 0; const p = hero ? M0 : randIn(), len = hero ? 2.6 : 1.6 + rand() * 1.2;
    if (!hero && !clear(p, len / 2 + 0.3)) continue;
    const m = new THREE.Mesh(makeMito(len, hero ? 0.12 : (rand() - 0.5) * 0.35), mitoMat);
    m.position.copy(p); hero ? m.rotation.set(0.3, 0.2, 1.25) : m.rotation.set(rand() * 6.28, rand() * 6.28, rand() * 6.28);
    m.userData.q0 = m.quaternion.clone(); m.userData.h = hash(100 + i++);
    scene.add(m); mitos.push(m); placed.push({ p, r: len / 2 + 0.25 });
  }

  // ribosomes: free (one polysome = several ribosomes on one mRNA), on the ER and on the outer nuclear membrane
  const riboMat = solid({ color: P.ribo, rim: '#fff4e0', rimStrength: 0.2, spec: 0.08, cap: P.ribo });
  const riboERMat = solid({ color: P.ribo, rim: '#fff4e0', rimStrength: 0.2, spec: 0.08, cap: P.ribo });
  const riboGeo = new THREE.IcosahedronGeometry(0.06, 2);
  const freeP = [];
  for (let k = 0; k < 9; k++) { const a = k * 0.75; freeP.push(R0.clone().add(V(Math.cos(a) * 0.2, (k - 4) * 0.105, Math.sin(a) * 0.2))); }
  const mrna = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(Array.from({ length: 40 }, (_, j) => { const k = j / 39 * 9.6 - 0.3, a = k * 0.75; return R0.clone().add(V(Math.cos(a) * 0.13, (k - 4) * 0.105, Math.sin(a) * 0.13)); })), 200, 0.012, 5), glow({ color: P.orange, strength: 0.9 }));
  scene.add(mrna);
  for (let tries = 0; freeP.length < 1700 && tries < 40000; tries++) {
    const p = randIn(); if (!insideCell(p, 0.35) || p.distanceTo(Cn) < rn + 0.25 || p.distanceTo(G) < 1.7 || p.distanceTo(R0) < 0.7 || nearPath(p, 0.45)) continue;
    if (mitos.some(m => m.position.distanceTo(p) < 1.6) || lysos.some(l => l.position.distanceTo(p) < 0.6)) continue;
    freeP.push(p);
  }
  const erP = [];
  for (let i = 0; i < 950; i++) { const L = erLayers[Math.floor(rand() * 4)]; const side = rand() < 0.5 ? 1 : -1; erP.push(erPoint(L, 0.02 + rand() * 0.96, 0.04 + rand() * 0.9, side * 0.08)); }
  for (let i = 0; i < 170; i++) { const d = V(rand() - 0.5, rand() - 0.5, rand() - 0.5).normalize(); erP.push(Cn.clone().addScaledVector(d, rn + 0.08)); }
  const ribosFree = new THREE.InstancedMesh(riboGeo, riboMat, freeP.length); scene.add(ribosFree);
  const ribosER = new THREE.InstancedMesh(riboGeo, riboERMat, erP.length); scene.add(ribosER);
  const freeH = freeP.map((_, i) => (i < 9 ? 0.05 * i : hash(1000 + i))), erH = erP.map((p, i) => (p.distanceTo(Cn) - rn) / 2.4 + 0.08 * hash(5000 + i));

  // ---------- depth: soft out-of-focus specks outside and a faint haze inside ----------
  const mkPoints = (n, f) => { const pos = [], size = [], color = []; for (let i = 0; i < n; i++) { const o = f(i); pos.push(...o.p.toArray()); size.push(o.s); color.push(...o.c.toArray()); } const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('aSize', new THREE.Float32BufferAttribute(size, 1)); g.setAttribute('aColor', new THREE.Float32BufferAttribute(color, 3)); return g; };
  const teal = new THREE.Color(P.membraneRim), org = new THREE.Color(P.orange), wht = new THREE.Color('#cfe9e6');
  scene.add(new THREE.Points(mkPoints(260, () => { const d = V(rand() - 0.5, rand() - 0.5, rand() - 0.5).normalize(); const c = [teal, org, wht][Math.floor(rand() * 3)].clone().multiplyScalar(0.04 + rand() * 0.09); return { p: d.multiplyScalar(24 + rand() * 70), s: 0.5 + rand() * 1.6, c }; }), bokeh({ scale: 900, ring: 0.4 })));
  const haze = new THREE.Points(mkPoints(700, () => { let p; do p = randIn(); while (!insideCell(p, 0.3)); return { p, s: 0.03 + rand() * 0.05, c: wht.clone().multiplyScalar(0.08 + rand() * 0.1) }; }), bokeh({ scale: 600, ring: 0.0 }));
  scene.add(haze);

  // ---------- the cutaway: a wedge removed from the containers (membrane, nucleus, ER); parts stay whole ----------
  const wedge = [new THREE.Plane(), new THREE.Plane()];
  [memMat, envMat, poreMat, chromMat, nolMat, erMat, riboERMat].forEach(m => { m.clippingPlanes = wedge; m.clipIntersection = true; });
  const faceMat = (o) => new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, side: THREE.DoubleSide,
    uniforms: { uFill: { value: new THREE.Color(o.fill) }, uLine: { value: new THREE.Color(o.line) }, uA: { value: o.alpha }, uFade: { value: 0 }, uW: { value: o.w } },
    vertexShader: 'attribute float aDist; varying float vD; void main(){ vD = aDist; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
    fragmentShader: `uniform vec3 uFill, uLine; uniform float uA, uFade, uW; varying float vD;
      void main(){ float l1 = 1.0 - smoothstep(uW * 0.8, uW, vD); float l2 = smoothstep(uW * 1.6, uW * 1.8, vD) * (1.0 - smoothstep(uW * 2.6, uW * 2.8, vD));
        float line = max(l1, l2); float inner = smoothstep(uW * 3.0, uW * 30.0, vD);
        vec3 c = mix(uLine * 2.0, uFill * (1.0 + 0.6 * (1.0 - inner)), 1.0 - line); gl_FragColor = vec4(c, mix(uA, 1.0, line) * uFade); }`,
  });
  const memFaceMat = faceMat({ fill: P.cutFill, line: P.orange, alpha: 0.82, w: 0.09 });
  const nucFaceMat = faceMat({ fill: P.nucCutFill, line: P.nucleusRim, alpha: 0.9, w: 0.07 });
  const faces = [0, 1].map(() => { const a = new THREE.Mesh(new THREE.BufferGeometry(), memFaceMat), b = new THREE.Mesh(new THREE.BufferGeometry(), nucFaceMat); a.renderOrder = 4; b.renderOrder = 3; a.userData.noDepth = b.userData.noDepth = true; scene.add(a, b); return [a, b]; });
  const NS = 96;
  const rayToMembrane = (o, dir) => { let lo = 0, hi = 30; for (let i = 0; i < 30; i++) { const mid = (lo + hi) / 2; insideCell(o.clone().addScaledVector(dir, mid)) ? (lo = mid) : (hi = mid); } return lo; };
  function setFace(mesh, e, inner, outer) { // half-plane spanned by Y and e through Cn, between radius inner and the surface; aDist = distance from the cut edge
    const pos = [], dist = [], idx = [];
    for (let i = 0; i <= NS; i++) {
      const s = (Math.PI * i) / NS, dir = Y.clone().multiplyScalar(Math.cos(s)).addScaledVector(e, Math.sin(s));
      const r1 = outer ?? rayToMembrane(Cn, dir), r0 = inner;
      pos.push(...Cn.clone().addScaledVector(dir, r1).toArray(), ...Cn.clone().addScaledVector(dir, r0).toArray()); dist.push(0, r1 - r0);
      if (i < NS) { const a = 2 * i; idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); }
    }
    const g = mesh.geometry; g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('aDist', new THREE.Float32BufferAttribute(dist, 1)); g.setIndex(idx); g.computeBoundingSphere();
  }
  let lastAlpha = -1;
  function setWedge(alpha) { // clipIntersection: only points on the negative side of BOTH planes are removed
    const e1 = wd.clone().applyAxisAngle(Y, alpha / 2), e2 = wd.clone().applyAxisAngle(Y, -alpha / 2);
    wedge[0].setFromNormalAndCoplanarPoint(new THREE.Vector3().crossVectors(e1, Y).normalize(), Cn);
    wedge[1].setFromNormalAndCoplanarPoint(new THREE.Vector3().crossVectors(Y, e2).normalize(), Cn);
    for (const pl of wedge) if (pl.normal.dot(wd) > 0) pl.negate();
    if (alpha > 0 && Math.abs(alpha - lastAlpha) > 1e-6) { setFace(faces[0][0], e1, rn); setFace(faces[1][0], e2, rn); setFace(faces[0][1], e1, 0, rn); setFace(faces[1][1], e2, 0, rn); }
    lastAlpha = alpha;
  }

  // ---------- update(t): pose everything from t ----------
  const beats = story.labels.filter(l => !l.small);
  const focusOf = (t) => { let part = null, f = 0; for (const b of beats) { const a = env(t, b.in - 0.3, b.out, 0.4, 0.4); if (a > f && b.part && b.part !== 'membrane') { f = a; part = b.part; } } return { part, f }; };
  const dimFor = (name, F, base = 0.45) => (F.part && F.part !== name ? lerp(1, base, F.f) : 1);
  const pop = (k) => Math.max(1e-3, ease.outBack(k));

  function update(t) {
    const F = focusOf(t);
    const cut = ease.inOutCubic(win(t, T.cut[0], T.cut[1]));
    setWedge(cut * THREE.MathUtils.degToRad(story.cutDegrees));
    faces.forEach(([a, b]) => { a.visible = b.visible = cut > 0.002; a.material.uniforms.uFade.value = smooth(cut * 2.5); b.material.uniforms.uFade.value = smooth(cut * 2.5); });

    // membrane: sweeps in, milky while we are outside, x-ray once we dive in, milky again for the cutaway
    memMat.uniforms.uReveal.value = ease.inOutSine(win(t, ...T.membrane));
    const xray = smooth(win(t, ...T.xray)) * (1 - smooth(win(t, T.cut[0], T.cut[1])));
    memMat.uniforms.uOpacity.value = lerp(0.16, 0.02, xray) + 0.22 * cut;
    memMat.uniforms.uRimStrength.value = lerp(1.5, 0.55, xray);
    memMat.uniforms.uSpecular.value = lerp(0.16, 0.05, xray);
    setU(memMat, 'uDim', dimFor('membrane', F, 0.6));
    membrane.scale.setScalar(lerp(0.94, 1, ease.outCubic(win(t, ...T.membrane))));

    // nucleus: grows in, pores pop, then turns x-ray to show the nucleolus, then half back
    const kn = win(t, ...T.nucleus); nucleus.visible = kn > 0;
    nucleus.scale.setScalar(pop(kn));
    const nx = smooth(win(t, ...T.nucleusXray)), back = smooth(win(t, T.nucleusXray[1] + 1.4, T.nucleusXray[1] + 2.4));
    envMat.uniforms.uOpacity.value = lerp(0.88, 0.08, nx) + 0.3 * back;
    setU(envMat, 'uDim', dimFor('nucleus', F)); setU(poreMat, 'uDim', dimFor('nucleus', F));
    for (let i = 0; i < NPORE; i++) { const k = pop(win(t, T.nucleus[0] + 0.35 + 0.6 * hash(i), T.nucleus[0] + 0.65 + 0.6 * hash(i))); tmp.position.copy(poreDirs[i]).multiplyScalar(rn + 0.01); tmp.quaternion.setFromUnitVectors(V(0, 0, 1), poreDirs[i]); tmp.scale.setScalar(k); tmp.updateMatrix(); pores.setMatrixAt(i, tmp.matrix); }
    pores.instanceMatrix.needsUpdate = true;
    chromMat.uniforms.uFade.value = smooth(win(t, T.nucleusXray[0], T.nucleusXray[1] + 0.3)) * (1 - 0.5 * back) + 0.4 * cut;
    setU(chromMat, 'uDim', dimFor('nucleolus', F, 0.6));
    const kno = win(t, ...T.nucleolus); nucleolus.visible = kno > 0; nucleolus.scale.setScalar(pop(kno));
    setU(nolMat, 'uDim', dimFor('nucleolus', F, 0.55));

    // ER grows outward from the nuclear envelope; its ribosomes land as the front passes
    const ke = win(t, ...T.er); er.visible = ke > 0;
    erMat.uniforms.uReveal.value = ease.inOutSine(ke);
    setU(erMat, 'uDim', dimFor('er', F)); setU(riboERMat, 'uDim', dimFor('er', F, 0.5));
    const front = ease.inOutSine(ke) * 1.3 - 0.15;
    for (let i = 0; i < erP.length; i++) { const k = pop(clamp((front - erH[i]) / 0.12)); tmp.position.copy(erP[i]); tmp.quaternion.identity(); tmp.scale.setScalar(k); tmp.updateMatrix(); ribosER.setMatrixAt(i, tmp.matrix); }
    ribosER.instanceMatrix.needsUpdate = true; ribosER.visible = ke > 0;

    // Golgi: cisternae slide in one by one, then vesicles bud
    golgi.visible = t >= T.golgi[0];
    cisternae.forEach((m, k) => { const kk = ease.outCubic(win(t, T.golgi[0] + 0.12 * k, T.golgi[0] + 0.55 + 0.12 * k)); m.position.y = m.userData.y + (1 - kk) * 2.2; m.scale.setScalar(Math.max(1e-3, lerp(0.4, 1, kk))); m.visible = kk > 0; });
    vesicles.forEach((m, j) => { const kk = pop(win(t, T.golgi[1] - 0.3 + 0.03 * j, T.golgi[1] + 0.03 * j)); m.scale.setScalar(kk); m.visible = kk > 0.002; });
    setU(golgi, 'uDim', dimFor('golgi', F));

    // centrosome and microtubules draw outward
    const kc = pop(win(t, T.cyto[0] - 0.2, T.cyto[0] + 0.3)); centrosome.visible = t > T.cyto[0] - 0.2; centrosome.scale.setScalar(kc);
    microtubules.forEach(m => { const k = ease.outCubic(win(t, T.cyto[0] + 0.35 * m.userData.h, T.cyto[1] + 0.35 * m.userData.h)); m.visible = k > 0; m.geometry.setDrawRange(0, Math.floor((k * m.userData.full) / 6) * 6); });
    setU(mtMat, 'uDim', dimFor('cyto', F, 0.5) * (1 - 0.55 * cut)); setU(centMat, 'uDim', dimFor('cyto', F, 0.5));

    // mitochondria pop in with a small settle spin
    mitos.forEach(m => { const k = win(t, T.mito[0] + 0.5 * m.userData.h, T.mito[0] + 0.5 + 0.5 * m.userData.h); m.visible = k > 0; m.scale.setScalar(pop(k)); m.quaternion.copy(m.userData.q0).multiply(new THREE.Quaternion().setFromAxisAngle(Y, (1 - ease.outCubic(k)) * 1.2)); });
    setU(mitoMat, 'uDim', dimFor('mito', F));

    // free ribosomes sprinkle in (the polysome first); lysosomes pop
    for (let i = 0; i < freeP.length; i++) { const k = pop(win(t, T.ribo[0] + 0.8 * freeH[i], T.ribo[0] + 0.25 + 0.8 * freeH[i])); tmp.position.copy(freeP[i]); tmp.quaternion.identity(); tmp.scale.setScalar(k); tmp.updateMatrix(); ribosFree.setMatrixAt(i, tmp.matrix); }
    ribosFree.instanceMatrix.needsUpdate = true; ribosFree.visible = t >= T.ribo[0];
    mrna.visible = t >= T.ribo[0]; mrna.material.uniforms.uFade.value = smooth(win(t, T.ribo[0], T.ribo[0] + 0.5)) * dimFor('ribo', F, 0.5);
    setU(riboMat, 'uDim', dimFor('ribo', F, 0.5));
    const lk = lysos.map(m => pop(win(t, T.lyso[0] + 0.45 * m.userData.h, T.lyso[0] + 0.4 + 0.45 * m.userData.h)));
    lysos.forEach((m, i) => { m.visible = lk[i] > 0.002; m.scale.setScalar(lk[i]); });
    granules.forEach((g, j) => { const k = lk[g.l]; tmp.position.copy(g.p).multiplyScalar(k).add(lysos[g.l].position); tmp.quaternion.identity(); tmp.scale.setScalar(Math.max(1e-3, g.s * k)); tmp.updateMatrix(); gran.setMatrixAt(j, tmp.matrix); });
    gran.instanceMatrix.needsUpdate = true; gran.visible = t >= T.lyso[0];
    setU(lysoMat, 'uDim', dimFor('lyso', F)); setU(granMat, 'uDim', dimFor('lyso', F));

    haze.material.uniforms.uFade.value = smooth(win(t, ...T.membrane)) * (1 - 0.6 * cut);
  }

  update(0);
  return { anchors, update };
}
