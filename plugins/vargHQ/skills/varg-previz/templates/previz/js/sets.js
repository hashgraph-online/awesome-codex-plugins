// Master sets: ONE set per location. Every shot of a location is framed inside the same set, so geography stays
// consistent between wide and close coverage. Replace these starters with your project's locations.
//
// A set is { id, title, scene, o, subjects, helperFar, mapHome, ref?, reset() }:
//   scene     THREE.Scene with the location built from primitives (match the master plate's layout!)
//   o         named objects the story touches, so shot animations stay one-liners (S.o.hero, S.o.product…)
//   subjects  what a camera can frame: { name: object }. The first one is the default subject of auto cameras.
//   helperFar how long the camera frustums are drawn in the map view (metres; ~ typical camera distance)
//   mapHome   [[position], [target]] of the map camera (optional; derived from the set's bounds if missing)
//   ref       which config.scale entry shot sizes are judged against (default 'human')
//   reset()   restores the neutral state; a shot's anim() then poses the set for a given time (scrubbing is exact)
import * as THREE from 'three';
import {
  C, mat, glow, basic, box, ink, makePerson, pose, makeProduct, makeCar, makeTable, makeChair, blob, gradientTex,
} from './props.js';

function scene(bg, fog) {
  const s = new THREE.Scene();
  s.background = bg instanceof THREE.Texture ? bg : new THREE.Color(bg);
  if (fog) s.fog = fog;
  return s;
}

// ================================================================ STUDIO: product + presenter on a cyclorama
function buildStudio() {
  const s = scene(0x1a1c22);
  const o = {};
  o.hemi = new THREE.HemisphereLight(0xc8d0e0, 0x202024, 0.9); s.add(o.hemi);
  o.key = new THREE.DirectionalLight(0xffffff, 2.2); o.key.position.set(-2, 4, -3); s.add(o.key);
  o.rim = new THREE.PointLight(C.orange, 4, 8, 1.5); o.rim.position.set(1.5, 2.2, 1.5); s.add(o.rim);

  const cyc = new THREE.Group(); cyc.name = 'cyc'; s.add(cyc);
  const wall = mat(0x9aa0aa);
  cyc.add(box(8, 0.05, 6, wall, [0, -0.025, -1]));                                     // floor
  cyc.add(box(8, 4, 0.05, wall, [0, 2.5, 2.5]));                                        // back wall (+Z, behind the subjects)
  const cove = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.5, 8, 16, 1, true, 0, Math.PI / 2), mat(0x9aa0aa, { side: THREE.DoubleSide }));
  cove.rotation.z = Math.PI / 2; cove.position.set(0, 0.5, 2.0); cove.rotation.y = 0; cyc.add(cove);
  o.pedestal = box(0.5, 0.9, 0.5, mat(C.white), [0, 0.45, 0], 'pedestal'); s.add(o.pedestal);
  o.product = makeProduct({ kind: 'bottle', color: C.orange, h: 0.28 }); s.add(o.product);
  o.host = makePerson({ top: C.violet, bottom: C.dark, long: true, name: 'host' }); s.add(o.host);
  ink(cyc);
  return {
    id: 'studio', title: 'Studio · product + presenter', scene: s, o, helperFar: 0.8,
    subjects: { product: o.product, host: o.host },
    mapHome: [[3.2, 2.6, -4.2], [0.3, 1, 0]],
    reset() {
      o.product.position.set(0, 0.9, 0); o.product.rotation.set(0, 0, 0); o.product.visible = true;
      o.host.position.set(0.85, 0.95, 0.15); o.host.rotation.set(0, -0.25, 0);
      pose(o.host, [['stand', 1]]);
      o.host.getObjectByName('mouth').scale.y = 1;
      o.key.intensity = 2.2; o.rim.intensity = 4;
    },
  };
}

// ================================================================ ROOM: interior, two people at a table
// Floor 6 x 5 m, walls 2.8 m. Person A sits on the +Z side facing -Z (toward the window-less front wall),
// person B sits opposite facing +Z. Window on the back wall behind A, door on the left wall.
function buildRoom() {
  const s = scene(0x0d0f16);
  const o = {};
  o.hemi = new THREE.HemisphereLight(0xd8dcf0, 0x2a2420, 0.7); s.add(o.hemi);
  o.window = new THREE.DirectionalLight(0xfff0d8, 1.8); o.window.position.set(-1, 3, 4); s.add(o.window);
  o.lamp = new THREE.PointLight(0xffb070, 3, 5, 1.6); o.lamp.position.set(0, 2.2, 0); s.add(o.lamp);

  const room = new THREE.Group(); room.name = 'room'; s.add(room);
  const wallM = mat(0x5a5f6e), floorM = mat(0x3a3330);
  room.add(box(6, 0.05, 5, floorM, [0, -0.025, 0], 'floor'));
  room.add(box(6, 2.8, 0.1, wallM, [0, 1.4, 2.55], 'wallBack'));
  room.add(box(6, 2.8, 0.1, wallM, [0, 1.4, -2.55], 'wallFront'));
  room.add(box(0.1, 2.8, 5, wallM, [-3.05, 1.4, 0], 'wallLeft'));
  room.add(box(0.1, 2.8, 5, wallM, [3.05, 1.4, 0], 'wallRight'));
  const win = box(1.6, 1.2, 0.02, glow(0xbfd8ff, 0.9), [-1, 1.6, 2.49], 'windowPane'); win.userData.noInk = true; room.add(win);
  room.add(box(0.9, 2.0, 0.04, mat(C.wood), [-2.99, 1.0, -1.2], 'door'));
  o.table = makeTable({ w: 1.2, d: 0.8 }); s.add(o.table);
  o.chairA = makeChair(); o.chairA.position.set(0, 0, 0.7); s.add(o.chairA);
  o.chairB = makeChair(); o.chairB.position.set(0, 0, -0.7); o.chairB.rotation.y = Math.PI; s.add(o.chairB);
  o.cupA = makeProduct({ kind: 'cup', color: C.white, h: 0.1, name: 'cupA' }); s.add(o.cupA);
  o.cupB = makeProduct({ kind: 'cup', color: C.white, h: 0.1, name: 'cupB' }); s.add(o.cupB);
  o.phone = makeProduct({ kind: 'phone', h: 0.15, name: 'phone' }); s.add(o.phone);
  o.a = makePerson({ top: C.blue, name: 'personA' }); s.add(o.a);
  o.b = makePerson({ top: C.orange, long: true, name: 'personB' }); s.add(o.b);
  const shade = blob(0xffc080, 1.2, 0.5); shade.position.set(0, 2.2, 0); s.add(shade);
  ink(room);
  return {
    id: 'room', title: 'Room · two at a table', scene: s, o, helperFar: 0.9,
    subjects: { a: o.a, b: o.b, table: o.table },
    mapHome: [[4.5, 5.5, -5.5], [0, 0.6, 0]],
    reset() {
      for (const [p, z, ry] of [[o.a, 0.75, 0], [o.b, -0.75, Math.PI]]) {
        p.position.set(0, 0.5, z); p.rotation.set(0, ry, 0);
        pose(p, [['sit', 1], ['handsOnTable', 1]]);
        p.getObjectByName('mouth').scale.y = 1;
      }
      o.cupA.position.set(0.2, 0.775, 0.22); o.cupB.position.set(-0.2, 0.775, -0.22);
      o.phone.position.set(0.35, 0.78, 0.05); o.phone.rotation.set(-Math.PI / 2, 0, 0); o.phone.visible = true;
      o.lamp.intensity = 3; o.window.intensity = 1.8;
    },
  };
}

// ================================================================ STREET: exterior, a road, a car, a walker
// Road runs along Z; the car drives toward -Z. Buildings line both sides. Units are metres.
function buildStreet() {
  const s = scene(gradientTex([[0, '#1b2350'], [0.55, '#e0785a'], [1, '#2a1e30']]), new THREE.Fog(0x2a1e30, 60, 220));
  const o = {};
  o.hemi = new THREE.HemisphereLight(0xffd0b0, 0x202030, 1.0); s.add(o.hemi);
  o.sun = new THREE.DirectionalLight(0xffb080, 1.6); o.sun.position.set(30, 25, -80); s.add(o.sun);
  const st = new THREE.Group(); st.name = 'street'; s.add(st);
  st.add(box(400, 0.02, 400, mat(0x2a2a30), [0, -0.01, 0], 'ground'));
  st.add(box(8, 0.03, 400, mat(0x1c1c22), [0, 0.005, 0], 'road'));
  for (const sx of [-1, 1]) st.add(box(3, 0.15, 400, mat(0x55555f), [5.5 * sx, 0.075, 0], 'sidewalk'));
  const dash = new THREE.InstancedMesh(new THREE.BoxGeometry(0.15, 0.01, 2), basic(0xeeeeee), 60);
  const m4 = new THREE.Matrix4();
  for (let i = 0; i < 60; i++) { m4.makeTranslation(0, 0.03, -150 + i * 5); dash.setMatrixAt(i, m4); }
  st.add(dash);
  const bm = [mat(0x4a4f63), mat(0x3d3448), mat(0x5a5260)];
  let seed = 7; const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  for (const sx of [-1, 1]) for (let z = -150; z < 150; z += 12) {
    const h = 8 + rnd() * 30, w = 9 + rnd() * 4;
    st.add(box(w, h, 10, bm[Math.floor(rnd() * 3)], [sx * (7 + w / 2 + rnd() * 2), h / 2, z]));
  }
  for (const sx of [-1, 1]) for (let z = -120; z < 120; z += 20) {
    st.add(box(0.12, 5, 0.12, mat(C.dark), [sx * 4.4, 2.5, z]));
    const bulb = box(0.5, 0.12, 0.3, glow(0xffe0a0, 1.5), [sx * 4.1, 5, z]); bulb.userData.noInk = true; st.add(bulb);
  }
  o.car = makeCar({ color: C.orange }); s.add(o.car);
  o.walker = makePerson({ top: C.white, bottom: C.navy, name: 'walker' }); s.add(o.walker);
  const sun = blob(0xffc080, 60, 0.6); sun.position.set(0, 18, -190); s.add(sun);
  ink(st, 40);
  return {
    id: 'street', title: 'Street · car + walker', scene: s, o, helperFar: 3,
    subjects: { car: o.car, walker: o.walker }, ref: 'human',
    mapHome: [[0, 26, 24], [0, 0, -6]],   // above the road: the buildings start at |x| = 7
    reset() {
      o.car.position.set(-2, 0, 0); o.car.rotation.set(0, 0, 0);
      o.walker.position.set(5.2, 0.95 + 0.15, -1); o.walker.rotation.set(0, 0, 0);
      pose(o.walker, [['stand', 1]]);
    },
  };
}

export function buildSets() {
  const sets = Object.fromEntries([buildStudio(), buildRoom(), buildStreet()].map(s => [s.id, s]));
  for (const s of Object.values(sets)) s.reset();
  return sets;
}
