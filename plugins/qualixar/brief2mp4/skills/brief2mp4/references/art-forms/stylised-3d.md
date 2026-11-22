# Stylised 3D cartoon

Also called: soft 3d cartoon, 3d cartoon character, rounded 3d character.

Family: Geometry, pixels and 3D. Cadence: smooth, full frame rate. Usual tool: Three.js inside HyperFrames, or Blender.

A soft, rounded 3D cartoon character or prop with a big readable face: smooth forms, a soft key light, a cool rim light and warm light that seems to pass through the skin. The demo is drawn in 2D, so it renders with no WebGL; the Three.js recipe below is how to build the real thing.

Three-point lighting is a standard method in film, photography and 3D graphics: the key light is the principal illuminator, usually 30 to 45 degrees to one side of the camera and elevated about as much. Subsurface scattering is light travelling into a translucent surface and out again at another point; without it a material can look like plastic or metal.

Sourcing note: The two sources cover the lighting and shading ideas; the face and softness rules are a practice summary.

## What makes it read as this

- Smooth, rounded forms with no hard edges: spheres, capsules and soft boxes
- A big, readable face: large eyes with a gradient and two highlights, clear brows, a wide mouth
- A soft key light from the upper left, a cool rim light on the far edge, and a soft specular highlight
- A warm glow at the shadow edge, as light bleeds through the skin
- A shallow-depth background of blurred lights and a soft contact shadow

## Timing

Smooth, full frame rate: a slow breath, a bounce, a blink every three seconds and a wave. The squash and stretch are small and soft.

## How to build it

- Three.js: `MeshPhysicalMaterial` with `sheen`, a low `clearcoat`, and `transmission` or a warm emissive rim for the subsurface look
- Lights: a `DirectionalLight` key at about 40 degrees, a cool back `DirectionalLight` for the rim, a `HemisphereLight` fill, and `ACESFilmicToneMapping`
- Add `OutputPass` and a gentle `UnrealBloomPass`; soft `PCFSoftShadowMap` shadows
- Add a shallow depth of field with `BokehPass`
- In the 2D demo: `ball()` builds each form from an offset radial gradient, a warm inner gradient, a rim arc and a soft highlight

## Assets

All in code here. For a real character, model it in Blender and export a glTF. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Soft foley, a light orchestral bed and a spring on each bounce. Practice note.

## What makes it look wrong

- Hard black outlines: they turn it into toon 3D
- Plastic highlights and no warm bleed at the shadow edge
- A small face: the face must be readable at a glance
- Copying a recognisable studio character

## Tested demo

This is the look from `art-forms/looks-3d.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=stylised-3d` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'stylised-3d': { kind: '2d', fps: null, draw(g, t, W, H) {
    // a soft, rounded 3D cartoon chef: a tomato with a big readable face, a soft key light from the upper left, a cool rim light on the right, warm light bleeding through the skin, and a contact shadow
    const breath = Math.sin(t * 2.2) * 0.012, bob = Math.abs(Math.sin(t * 1.6)) * 10, blink = (t % 3.1) < 0.12, wave = Math.sin(t * 5) * 0.35;
    const wall = g.createLinearGradient(0, 0, 0, H); wall.addColorStop(0, '#ffe9cf'); wall.addColorStop(1, '#f2b97a'); g.fillStyle = wall; g.fillRect(0, 0, W, H);
    for (let i = 0; i < 12; i++) { const x = hash(i, 1) * W, y = hash(i, 2) * 300, r = 18 + hash(i, 3) * 40; g.fillStyle = `rgba(255,255,255,${0.05 + hash(i, 4) * 0.12})`; g.beginPath(); g.arc(x, y, r, 0, TAU); g.fill(); }   // out-of-focus kitchen lights
    g.fillStyle = '#c98a52'; g.fillRect(0, 440, W, 100); g.fillStyle = 'rgba(255,255,255,.2)'; g.fillRect(0, 440, W, 6);
    const sh = g.createRadialGradient(480, 468, 10, 480, 468, 170); sh.addColorStop(0, `rgba(70,30,10,${0.5 - bob * 0.02})`); sh.addColorStop(1, 'rgba(70,30,10,0)'); g.save(); g.translate(0, 468); g.scale(1, 0.18); g.translate(0, -468); g.fillStyle = sh; g.fillRect(280, 280, 400, 400); g.restore();
    g.save(); g.translate(480, 440 - bob); g.scale(1 + breath, 1 - breath); g.translate(-480, -440);
    for (const d of [-1, 1]) { ball(g, 480 + d * 52, 428, 36, 24, [74, 44, 36], { warm: false }); g.strokeStyle = '#f4e8d8'; g.lineWidth = 16; g.lineCap = 'round'; g.beginPath(); g.moveTo(480 + d * 52, 420); g.lineTo(480 + d * 50, 386); g.stroke(); }   // legs and shoes
    g.lineCap = 'round'; g.lineWidth = 34; g.strokeStyle = '#c93a2a'; g.beginPath(); g.moveTo(340, 330); g.quadraticCurveTo(300, 360, 306, 396); g.stroke(); g.lineWidth = 12; g.strokeStyle = 'rgba(255,190,150,.5)'; g.beginPath(); g.moveTo(334, 322); g.quadraticCurveTo(292, 354, 298, 392); g.stroke(); ball(g, 306, 402, 28, 26, [250, 246, 238]);
    g.save(); g.translate(620, 312); g.rotate(-0.5 - wave); g.lineWidth = 34; g.strokeStyle = '#c93a2a'; g.beginPath(); g.moveTo(0, 0); g.quadraticCurveTo(50, -10, 76, -52); g.stroke(); g.lineWidth = 12; g.strokeStyle = 'rgba(255,190,150,.5)'; g.beginPath(); g.moveTo(0, -8); g.quadraticCurveTo(48, -18, 70, -58); g.stroke(); ball(g, 80, -60, 30, 28, [250, 246, 238]); g.restore();   // the waving arm
    ball(g, 480, 300, 158, 142, [226, 56, 40]);
    polyFill(g, star(480, 168, 58, 22, 7, -1.57, 0.3, 4), '#4f9a3a'); g.fillStyle = 'rgba(255,255,255,.25)'; g.beginPath(); g.ellipse(466, 160, 16, 6, -0.4, 0, TAU); g.fill();
    for (const [x, y, r] of [[420, 112, 40], [480, 92, 48], [542, 112, 40]]) ball(g, x, y, r, r * 0.92, [252, 250, 244], { warm: false }); g.fillStyle = '#f4efe6'; g.beginPath(); g.roundRect(424, 124, 112, 40, 12); g.fill(); g.fillStyle = 'rgba(0,0,0,.12)'; g.fillRect(424, 150, 112, 14);   // the chef's hat
    for (const d of [-1, 1]) {
      const ex = 480 + d * 52, ey = 292;
      if (blink) { g.strokeStyle = '#3a1a14'; g.lineWidth = 7; g.lineCap = 'round'; g.beginPath(); g.arc(ex, ey + 6, 22, 0.15 * Math.PI, 0.85 * Math.PI); g.stroke(); continue; }
      ball(g, ex, ey, 31, 36, [255, 255, 255], { warm: false }); ball(g, ex + d * -1 + 4, ey + 4, 17, 20, [58, 30, 24], { warm: false, rim: false }); ell(g, ex - 2, ey - 3, 6, 7, '#fff'); ell(g, ex + 8, ey + 10, 3, 3, 'rgba(255,255,255,.8)');
      g.strokeStyle = '#3a1a14'; g.lineWidth = 8; g.lineCap = 'round'; g.beginPath(); g.moveTo(ex - d * 24, ey - 46 + d * 4); g.quadraticCurveTo(ex, ey - 62, ex + d * 28, ey - 44 - d * 6); g.stroke();
    }
    for (const d of [-1, 1]) { g.fillStyle = 'rgba(255,120,110,.4)'; g.beginPath(); g.ellipse(480 + d * 100, 340, 22, 13, 0, 0, TAU); g.fill(); }
    g.fillStyle = '#4a1a1a'; g.beginPath(); g.moveTo(436, 350); g.quadraticCurveTo(480, 410, 524, 350); g.quadraticCurveTo(480, 366, 436, 350); g.fill(); g.fillStyle = '#fffaf0'; g.fillRect(452, 352, 56, 9);
    g.restore();
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Subsurface_scattering>
- <https://en.wikipedia.org/wiki/Three-point_lighting>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
