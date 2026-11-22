# Low-poly 3D

Family: Geometry, pixels and 3D. Cadence: smooth, full frame rate. Usual tool: Three.js inside HyperFrames.

Meshes with few polygons, each face lit as one flat facet. A hardware limit that became a style.

From the era of early 3D consoles; chosen on purpose since about 2013.

## What makes it read as this

- Visible facets, flat shaded
- A limited, saturated palette
- Simple lighting and a gradient or flat sky
- Chunky silhouettes

## Timing

Clean, so smooth: slow eased orbits and dollies at the full frame rate.

## How to build it

- Low segment counts and `flatShading: true` on `MeshStandardMaterial`
- Displace a plane's vertices with a seeded hash for terrain, then `computeVertexNormals()`
- A hemisphere light plus one directional key; fog in the sky colour for depth
- Camera position from `t` directly

Use Blender for modelling and baked light.

## Assets

Geometry in code for landscapes and props. Characters need modelling. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Calm, spacious. Practice note.

## What makes it look wrong

- Smooth normals, which erase the facets
- Detailed textures that fight the flat colour

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=low-poly` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'low-poly': { kind: '3d', fps: null, setup(THREE, scene, camera) {
    // few polygons, each lit as one flat facet. Clean, so the camera move is smooth, not stepped.
    scene.background = new THREE.Color('#bfe3f2'); scene.fog = new THREE.Fog('#bfe3f2', 9, 22);
    const geo = new THREE.PlaneGeometry(26, 26, 22, 22); geo.rotateX(-Math.PI / 2); const p = geo.attributes.position;
    for (let i = 0; i < p.count; i++) { const x = p.getX(i), z = p.getZ(i), d = Math.hypot(x, z); p.setY(i, Math.max(0, 3.2 - d * 0.42) * (0.6 + hash(i, 9) * 0.9) + hash(i, 4) * 0.25); }
    geo.computeVertexNormals(); const land = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: '#5fa36a', flatShading: true, roughness: 0.9 }));
    const sunBall = new THREE.Mesh(new THREE.IcosahedronGeometry(0.9, 1), new THREE.MeshBasicMaterial({ color: '#ffd166' })); sunBall.position.set(-5, 5.5, -8);
    const trees = new THREE.Group(); for (let i = 0; i < 22; i++) { const a = hash(i, 1) * TAU, r = 3.6 + hash(i, 2) * 5, tr = new THREE.Mesh(new THREE.ConeGeometry(0.34, 1.1, 5), new THREE.MeshStandardMaterial({ color: '#2f6b4f', flatShading: true })); tr.position.set(Math.cos(a) * r, 0.75, Math.sin(a) * r); trees.add(tr); }
    scene.add(land, sunBall, trees, new THREE.HemisphereLight('#ffffff', '#4a6a4a', 1.4)); const key = new THREE.DirectionalLight('#fff0d0', 2.4); key.position.set(-5, 6, 2); scene.add(key);
    return { camera };
  }, draw(s, t) { const a = 0.5 + t * 0.22; s.camera.position.set(Math.sin(a) * 11, 4.6, Math.cos(a) * 11); s.camera.lookAt(0, 1.4, 0); } },
  voxel: { kind: '3d', fps: 12, setup(THREE, scene, camera) {
    // every cube the same size, on a grid, in one instanced mesh. The model builds layer by layer, on twos.
    scene.background = new THREE.Color('#1c2333');
    const cells = []; for (let y = 0; y < 9; y++) for (let x = -4; x <= 4; x++) for (let z = -4; z <= 4; z++) { const d = Math.hypot(x, z); const trunk = y < 4 && d < 1.2, leaves = y >= 3 && Math.hypot(x, (y - 6) * 1.25, z) < 3.6 && hash(x + 9, y, z + 9) > 0.12; if (trunk || leaves) cells.push([x, y, z, trunk && y < 4 && !leaves ? '#7a4f2a' : hash(x, y, z) > 0.5 ? '#3f9b57' : '#2f7d47']); }
    const mesh = new THREE.InstancedMesh(new THREE.BoxGeometry(0.96, 0.96, 0.96), new THREE.MeshLambertMaterial(), cells.length), col = new THREE.Color();
    cells.forEach((c, i) => mesh.setColorAt(i, col.set(c[3]))); scene.add(mesh, new THREE.HemisphereLight('#ffffff', '#33405a', 1.6)); const key = new THREE.DirectionalLight('#ffffff', 2); key.position.set(6, 9, 4); scene.add(key);
    return { mesh, cells, m: new THREE.Matrix4(), camera };
  }, draw(s, t) {
    const ts = held(t, 12), shown = Math.floor(clamp(ts / 2.2) * 9.99);
    s.cells.forEach(([x, y, z], i) => { const on = y <= shown; s.m.makeScale(on ? 1 : 0.0001, on ? 1 : 0.0001, on ? 1 : 0.0001); s.m.setPosition(x, y - 4, z); s.mesh.setMatrixAt(i, s.m); });
    s.mesh.instanceMatrix.needsUpdate = true; const a = 0.7 + ts * 0.35; s.camera.position.set(Math.sin(a) * 15, 6, Math.cos(a) * 15); s.camera.lookAt(0, 0, 0);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Low_poly>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
