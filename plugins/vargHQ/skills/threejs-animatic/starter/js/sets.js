// One master set per location. Every shot of this location is framed inside the same set,
// so wide and close coverage share one geography (who sits where, where the window is).
// A set is { id, title, scene, o, mapView, reset() }:
//   o        named objects the story touches (S.o.a, S.o.drone ...), so blocking stays one-liners
//   mapView  centre + half-size of the top-down map, in metres
//   reset()  neutral state; the blocking function then poses everything from time only
import * as THREE from 'three';
import { C, mat, mesh, ink, rng, makeMannequin, makeTable, makeChair, makeCup, makePlant, makeDrone, labelSprite, pose } from './props.js';

export function buildCafe() {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x15171d);
  scene.fog = new THREE.Fog(0x15171d, 14, 30);
  const o = {};

  // light: a hemisphere fill so no surface goes pure black, plus one key from the window side
  scene.add(new THREE.HemisphereLight(0xdfe6f2, 0x30343c, 1.6));
  const key = new THREE.DirectionalLight(0xffffff, 2.2);
  key.position.set(-3, 5, -2);
  scene.add(key);

  // room: 8 x 8 m floor, back wall with a window at z = -3.5, a pillar for depth cues
  const room = new THREE.Group(); room.name = 'room'; scene.add(room);
  room.add(mesh(new THREE.BoxGeometry(8, 0.05, 8), mat(C.floor), [0, -0.025, 0], null, 'floor'));
  const wall = mat(C.wall);
  room.add(mesh(new THREE.BoxGeometry(8, 0.9, 0.15), wall, [0, 0.45, -3.5]));        // sill
  room.add(mesh(new THREE.BoxGeometry(8, 0.5, 0.15), wall, [0, 2.75, -3.5]));        // lintel
  for (const x of [-4, -1.3, 1.3, 4]) room.add(mesh(new THREE.BoxGeometry(0.25, 3, 0.15), wall, [x, 1.5, -3.5]));
  room.add(mesh(new THREE.BoxGeometry(0.15, 3, 8), wall, [-4, 1.5, 0], null, 'wallL'));  // left wall
  room.add(mesh(new THREE.BoxGeometry(0.15, 3, 8), wall, [4, 1.5, 0], null, 'wallR'));   // right wall
  room.add(mesh(new THREE.CylinderGeometry(0.18, 0.18, 3, 12), wall, [2.6, 1.5, 1.4], null, 'pillar'));
  // counter + shelves on the right wall: the background of every shot that looks toward +X
  const counter = new THREE.Group(); counter.name = 'counter'; room.add(counter);
  counter.add(mesh(new THREE.BoxGeometry(0.6, 1.05, 3.2), mat(C.wood), [3.3, 0.525, -0.6]));
  for (const y of [1.45, 1.9, 2.35]) counter.add(mesh(new THREE.BoxGeometry(0.3, 0.04, 3.2), mat(C.dark), [3.8, y, -0.6]));
  for (let i = 0; i < 12; i++) counter.add(mesh(new THREE.CylinderGeometry(0.04, 0.045, 0.24, 8), mat(i % 3 ? 0x6f7a86 : 0xd9dde4), [3.8, 1.59 + 0.45 * (i % 3), -2 + (i * 0.23) % 2.8]));
  ink(room);
  // outside the window: a few blocks at seeded positions (the street the drone comes from)
  const street = new THREE.Group(); street.name = 'street'; room.add(street);
  const r = rng(7);
  for (let i = 0; i < 9; i++) {
    const h = 2 + r() * 6;
    street.add(ink(mesh(new THREE.BoxGeometry(1.5 + r() * 2, h, 1.5), mat(0x5c616c), [-7 + i * 1.9, h / 2 - 1, -9 - r() * 4])));
  }
  for (const [x, z] of [[-3.3, -2.8], [3.3, -2.8], [-3.3, 2.6]]) { const p = makePlant(); p.position.set(x, 0, z); room.add(p); }

  // table at the origin; A sits at -X facing +X, B sits at +X facing -X
  o.table = makeTable(); scene.add(o.table);
  const SEAT = 0.72;
  o.chairA = makeChair(); o.chairA.position.set(-SEAT, 0, 0); o.chairA.rotation.y = -Math.PI / 2; scene.add(o.chairA);
  o.chairB = makeChair(); o.chairB.position.set(SEAT, 0, 0); o.chairB.rotation.y = Math.PI / 2; scene.add(o.chairB);
  o.a = makeMannequin({ name: 'A', top: C.a, pants: C.aPants });
  o.b = makeMannequin({ name: 'B', top: C.b, pants: C.bPants });
  for (const [m, x, ry] of [[o.a, -SEAT, -Math.PI / 2], [o.b, SEAT, Math.PI / 2]]) {
    m.userData.home = { x, ry };
    scene.add(m);
    const tag = labelSprite(m.name, { color: m === o.a ? '#ffd2a6' : '#8fe0f0' });
    tag.position.set(0, 0.95, 0);
    m.add(tag);
  }
  o.cupA = makeCup(); o.cupA.position.set(-0.22, 0.758, 0.12); scene.add(o.cupA);
  o.cupB = makeCup(); o.cupB.position.set(0.24, 0.758, -0.1); scene.add(o.cupB);
  o.drone = makeDrone(); scene.add(o.drone);
  const dtag = labelSprite('DRONE', { color: '#ff9a8f' }); dtag.position.set(0, 0.25, 0); o.drone.add(dtag);

  return {
    id: 'cafe', title: 'Cafe, two at a table', scene, o,
    mapView: { center: [0, 0], half: 4.5 },
    reset() {
      for (const m of [o.a, o.b]) {
        m.position.set(m.userData.home.x, 0.52, 0);
        m.rotation.set(0, m.userData.home.ry, 0);
        pose(m, [['sit', 1]]);
      }
      o.drone.position.set(0, -10, 0);
      o.drone.rotation.set(0, 0, 0);
      o.cupA.position.set(-0.22, 0.758, 0.12);
    },
  };
}
