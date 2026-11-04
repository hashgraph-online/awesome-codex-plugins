// Look blockout (optional): put reference pictures and generated matte paintings on the grey set, so a
// still per shot can be compared with its reference before anything is animated or paid for.
// OFF by default. On only with ?look=1 (review UI or ?export=1&look=1) or `bun tools/capture.ts --look`.
// The geometry, cameras and blocking stay exactly the same; only materials change.
// Never send a look render to Seedance as the greyscale @video1: that stays the plain grey export.
//
// One entry per image. Images live in this folder (e.g. assets/look/) and load before the first frame.
//   backdrop  a new unlit plane (no fog, no light): a matte painting behind a window, a sky, a far street.
//             size [w, h] in metres, pos [x, y, z], optional rot [x, y, z] in radians. Faces +Z unless rotated.
//   surface   an existing set element by name (S.o key or mesh/group .name, e.g. 'floor', 'counter',
//             'pillar'): every mesh under it gets the image as its colour map. repeat [u, v] tiles it.
//             lit: false shows the picture's own colours, unaffected by the set lights.
//   hide      optional, on any entry: names of grey stand-ins the picture replaces (the demo's 'street'
//             blocks sit in front of a skyline matte). Hidden in look mode only.
import * as THREE from 'three';

export const LOOK = [
  // { backdrop: 'skyline', url: 'assets/look/street_matte.jpg', size: [24, 10], pos: [0, 3, -12], hide: ['street'] },
  // { surface: 'floor', url: 'assets/look/floor_planks.jpg', repeat: [4, 4] },
];

// Loads every image, then applies it. Resolves when the set is ready to render (the contract: nothing
// loads at seek time). A missing file rejects with its url instead of rendering a silent grey frame.
export async function applyLook(set, entries = LOOK) {
  const loader = new THREE.TextureLoader();
  const textures = await Promise.all(entries.map(e => loader.loadAsync(e.url).catch(() => {
    throw new Error(`look: cannot load ${e.url}`);
  })));
  entries.forEach((e, i) => {
    for (const name of e.hide || []) {
      const h = set.o[name] || set.scene.getObjectByName(name);
      if (!h) throw new Error(`look: no set element named "${name}" to hide`);
      h.visible = false;
    }
    const tex = textures[i];
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = 4;
    if (e.repeat) { tex.wrapS = tex.wrapT = THREE.RepeatWrapping; tex.repeat.set(...e.repeat); }
    if (e.backdrop) {
      const [w, h] = e.size || [20, 10];
      const plane = new THREE.Mesh(new THREE.PlaneGeometry(w, h),
        new THREE.MeshBasicMaterial({ map: tex, fog: false, toneMapped: false }));
      plane.name = e.backdrop;
      plane.position.set(...(e.pos || [0, h / 2, -12]));
      if (e.rot) plane.rotation.set(...e.rot);
      plane.raycast = () => {}; // not a blocker for the shot checks
      set.scene.add(plane);
      return;
    }
    const target = set.o[e.surface] || set.scene.getObjectByName(e.surface);
    if (!target) throw new Error(`look: no set element named "${e.surface}"`);
    target.traverse(m => {
      if (!m.isMesh) return;
      // clone: set materials are shared (all walls use one), a surface entry changes only its target
      m.material = e.lit === false
        ? new THREE.MeshBasicMaterial({ map: tex, toneMapped: false })
        : Object.assign(m.material.clone(), { map: tex, flatShading: false });
      if (e.lit !== false) m.material.color.set(0xffffff);
      m.material.needsUpdate = true;
    });
  });
}
