# Claymation

Also called: clay animation, plasticine animation.

Family: Craft and handmade. Cadence: steps 12 times a second. Usual tool: Three.js inside HyperFrames.

Figures of clay or plasticine, posed and photographed one frame at a time. Soft, lumpy, a little uneven, and never perfectly smooth in motion.

Plasticine dates from 1897. Art Clokey (Gumby) and Aardman, founded in 1972, made the look famous.

## What makes it read as this

- Rounded volumes with small lumps and dents, never a perfect sphere
- Matte, high-roughness surfaces under soft light
- Saturated colour, few of them
- Small asymmetries; a silhouette that changes slightly between poses
- A miniature set: a floor, a backdrop, shallow depth

## Timing

Shot on doubles: about 12 pose changes a second inside a 24 frames-a-second film. Each held pose sits a hair differently from the last.

## How to build it

- Three.js: `MeshStandardMaterial` with roughness about 0.9, metalness 0, and a noise canvas as `bumpMap`
- Push each vertex in or out by a few percent with a seeded hash, then `computeVertexNormals()`
- Pose from stepped time: `held(t, 12)`
- Add a seeded nudge per drawing to position and rotation (about 2% of the size)
- A hemisphere light plus one soft key; no hard specular highlights

Use Blender when the clay needs real subsurface scattering, soft area-light shadows or sculpted detail.

## Assets

Geometry in code (spheres, capsules, lathes) for simple characters. Fingerprint or noise detail as a generated bump texture. A real character needs modelling. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Close foley on pose changes (soft thuds, squelches), light percussion. Practice note.

## What makes it look wrong

- Smooth 24 or 30 frames-a-second motion: it reads as CG, not clay
- Glossy plastic highlights
- Perfect symmetry and clean edges

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=claymation` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  claymation: { kind: '3d', fps: 12, setup(THREE, scene, camera) {
    // rough, lumpy, matte spheres under soft light. Poses change 12 times a second and wobble a little between holds.
    scene.background = new THREE.Color('#e9d9c4');
    const tex = new THREE.CanvasTexture(grain(256, 256, 31, 255, [128, 128, 128])); tex.wrapS = tex.wrapT = THREE.RepeatWrapping; tex.repeat.set(3, 3);
    const clay = (col) => new THREE.MeshStandardMaterial({ color: col, roughness: 0.92, metalness: 0, bumpMap: tex, bumpScale: 2.2 });
    const lump = (r, seed, mat) => { const geo = new THREE.SphereGeometry(r, 40, 28), p = geo.attributes.position; for (let i = 0; i < p.count; i++) { const k = 1 + (hash(i, seed) - 0.5) * 0.045; p.setXYZ(i, p.getX(i) * k, p.getY(i) * k, p.getZ(i) * k); } geo.computeVertexNormals(); return new THREE.Mesh(geo, mat); };
    const body = lump(1, 1, clay('#d2603f')), head = lump(0.62, 2, clay('#e9b88f')), eyes = [-1, 1].map((s) => { const e = lump(0.1, 3, clay('#1c1c1c')); e.position.set(s * 0.22, 0.12, 0.56); head.add(e); return e; });
    const floor = new THREE.Mesh(new THREE.CircleGeometry(6, 48), clay('#b99b78')); floor.rotation.x = -Math.PI / 2; floor.position.y = -1;
    scene.add(body, head, floor, new THREE.HemisphereLight('#fff6ea', '#7a6048', 1.5)); const key = new THREE.DirectionalLight('#fff2dd', 2.2); key.position.set(3, 5, 4); scene.add(key);
    camera.position.set(0, 1.2, 7.2); camera.lookAt(0, 0.5, 0);
    return { body, head, eyes };
  }, draw(s, t) {
    const f = frameOf(t, 12), ts = held(t, 12), hop = Math.abs(Math.sin(ts * Math.PI * 1.2)), sq = 1 - 0.18 * (1 - hop);
    s.body.position.set(jit(f, 1, 0.02), hop * 0.9 + jit(f, 2, 0.015), 0); s.body.scale.set(1 / Math.sqrt(sq), sq, 1 / Math.sqrt(sq)); s.body.rotation.z = jit(f, 3, 0.03);
    s.head.position.set(jit(f, 4, 0.02), 1.42 * sq + hop * 0.9, 0.1); s.head.rotation.set(jit(f, 5, 0.04), Math.sin(ts * 2) * 0.4, jit(f, 6, 0.04));
    s.eyes.forEach((e) => e.scale.setScalar(f % 30 === 14 ? 0.15 : 1));     // a blink that lasts one drawing
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Clay_animation>
- <https://en.wikipedia.org/wiki/Stop_motion>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
