# 3D product render

Family: Geometry, pixels and 3D. Cadence: smooth, full frame rate. Usual tool: Three.js, the 3D pack, or Blender.

A studio shot of an object: a seamless backdrop, soft key, fill and rim lights, controlled reflections, a slow turn.

Product photography lighting, done in 3D.

Sourcing note: The lighting source is about photography; applying it to rendering is a practice note.

## What makes it read as this

- A seamless backdrop
- Key light to one side and above, a softer fill opposite, a rim light behind
- A contact shadow under the object
- True materials: gloss, metal, glass
- One slow move

## Timing

Smooth and slow at the full frame rate. The opposite of the handmade looks.

## How to build it

- `MeshPhysicalMaterial` with `clearcoat` for lacquer, `metalness: 1` for metal
- Three directional lights in the key, fill and rim positions, plus a hemisphere light
- Contact shadow: a plane with a radial-gradient texture, `depthWrite: false`
- Rotation from `t` directly; ease the camera, not the turntable

Use Blender when the brief asks for photoreal glass, caustics or depth of field.

## Assets

A model of the product: built in code, made with the 3D pack, or supplied. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Minimal: a low bed and one accent on the reveal. Practice note.

## What makes it look wrong

- No reflections, so it looks like plastic
- One harsh light
- An object floating with no shadow

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=product-render` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'product-render': { kind: '3d', fps: null, setup(THREE, scene, camera) {
    // a studio shot: a seamless backdrop, a key, a fill and a rim light, a contact shadow, a slow smooth turntable
    scene.background = new THREE.Color('#dfe3e8');
    const bottle = new THREE.Group(), glass = new THREE.MeshPhysicalMaterial({ color: '#b5462c', roughness: 0.18, metalness: 0, clearcoat: 1, clearcoatRoughness: 0.06 }), metal = new THREE.MeshStandardMaterial({ color: '#c9a25a', roughness: 0.28, metalness: 1 });
    const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.8, 1.5, 12, 40), glass), cap = new THREE.Mesh(new THREE.CylinderGeometry(0.34, 0.34, 0.5, 40), metal), band = new THREE.Mesh(new THREE.TorusGeometry(0.81, 0.04, 12, 60), metal);
    cap.position.y = 1.78; band.rotation.x = Math.PI / 2; band.position.y = 0.3; bottle.add(body, cap, band);
    const sh = new OffscreenCanvas(256, 256), sg = sh.getContext('2d'), rg = sg.createRadialGradient(128, 128, 0, 128, 128, 128); rg.addColorStop(0, 'rgba(20,24,34,.6)'); rg.addColorStop(1, 'rgba(20,24,34,0)'); sg.fillStyle = rg; sg.fillRect(0, 0, 256, 256);
    const shadow = new THREE.Mesh(new THREE.PlaneGeometry(4.4, 4.4), new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(sh), transparent: true, depthWrite: false })); shadow.rotation.x = -Math.PI / 2; shadow.position.y = -1.55;
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), new THREE.MeshStandardMaterial({ color: '#dfe3e8', roughness: 1 })); floor.rotation.x = -Math.PI / 2; floor.position.y = -1.56;
    const key = new THREE.DirectionalLight('#ffffff', 3.2); key.position.set(4, 5, 4); const fillL = new THREE.DirectionalLight('#cfe0ff', 1.1); fillL.position.set(-5, 2, 3); const rim = new THREE.DirectionalLight('#ffe2c0', 2.6); rim.position.set(-2, 4, -6);
    scene.add(floor, shadow, bottle, key, fillL, rim, new THREE.HemisphereLight('#ffffff', '#b0b6c0', 1.1)); camera.position.set(0, 0.9, 7.4); camera.lookAt(0, 0.2, 0);
    return { bottle };
  }, draw(s, t) { s.bottle.rotation.y = t * 0.7; } },
};
export const IDS = Object.keys(LOOKS);

```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Three-point_lighting>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
