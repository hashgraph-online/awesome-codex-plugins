# Anime and cel shading

Also called: anime, toon shading.

Family: Drawn and painted. Cadence: steps 12 times a second. Usual tool: Three.js inside HyperFrames.

Light broken into two or three flat tones with a hard edge between them, and an ink outline around every form.

Named after the celluloid sheets of hand-drawn animation. In 3D it became toon shading, as in Jet Set Radio and The Wind Waker.

## What makes it read as this

- Two or three tone bands with hard edges
- Shadows tinted with colour, not black
- A clean outline
- Flat, detailed backgrounds behind simpler characters
- Limited animation: holds, then sudden moves

## Timing

On twos as the baseline, ones for key action, threes and holds for dialogue.

## How to build it

- Three.js `MeshToonMaterial` with a `gradientMap`: a three-texel `DataTexture` with `NearestFilter`, so light snaps to bands
- Outline by inverted hull: a second copy of each mesh, slightly larger, drawn back faces only in black
- `OutlineEffect` and `SobelOperatorShader` in the three.js examples are the two other routes
- Step the pose time: `held(t, 12)`
- 2D: flat SVG shapes, a thick outline, `steps()` timing

Use Blender for Freestyle line art and shader-to-RGB ramps on real characters.

## Assets

The gradient map is three bytes. Characters need modelling or generated models. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Whoosh and impact effects on key poses. Practice note.

## What makes it look wrong

- Smooth interpolation at 24 frames a second
- More than three bands
- Shadows that are only a darker grey

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=cel-shaded` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'cel-shaded': { kind: '3d', fps: 12, setup(THREE, scene, camera) {
    // light in three hard bands (a tiny gradient texture with no smoothing) and an outline made from a second, inside-out copy
    scene.background = new THREE.Color('#ffd9a8');
    const ramp = new THREE.DataTexture(new Uint8Array([70, 150, 255]), 3, 1, THREE.RedFormat); ramp.minFilter = ramp.magFilter = THREE.NearestFilter; ramp.needsUpdate = true;
    const group = new THREE.Group(), ink = new THREE.MeshBasicMaterial({ color: '#17131c', side: THREE.BackSide });
    const add = (geo, col, x, y, z) => { const m = new THREE.Mesh(geo, new THREE.MeshToonMaterial({ color: col, gradientMap: ramp })); m.position.set(x, y, z); const o = new THREE.Mesh(geo, ink); o.scale.setScalar(1.06); m.add(o); group.add(m); return m; };
    add(new THREE.SphereGeometry(1, 48, 32), '#3f7fd6', 0, 0, 0); add(new THREE.ConeGeometry(0.7, 1.5, 40), '#ff5a5f', 0, 1.5, 0); add(new THREE.TorusGeometry(1.5, 0.16, 20, 80), '#ffd23f', 0, 0, 0).rotation.x = 1.2;
    scene.add(group); const sun = new THREE.DirectionalLight('#ffffff', 3); sun.position.set(4, 5, 5); scene.add(sun, new THREE.AmbientLight('#8a7fb5', 0.9));
    camera.position.set(0, 1, 7.5); camera.lookAt(0, 0.4, 0);
    return { group };
  }, draw(s, t) { const ts = held(t, 12); s.group.rotation.y = ts * 1.4; s.group.rotation.z = Math.sin(ts * 2) * 0.12; s.group.position.y = Math.sin(ts * 2.5) * 0.25; } },
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

- <https://en.wikipedia.org/wiki/Cel_shading>
- <https://en.wikipedia.org/wiki/Limited_animation>
- <https://github.com/mrdoob/three.js>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
