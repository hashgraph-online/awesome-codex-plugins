# Tilt-shift miniature diorama

Also called: tilt-shift, miniature town, miniature diorama, toy town.

Family: Geometry, pixels and 3D. Cadence: smooth, full frame rate. Usual tool: Three.js inside HyperFrames, or Blender.

A tiny town seen from a high camera: saturated toy colours, little cars looping round the roads, and a blur that grows toward the top and bottom of the frame, so that it looks like a model. The demo is drawn in 2D, so it renders with no WebGL; the Three.js recipe below is how to build the real thing.

Tilt-shift photography uses camera movements that change the orientation or position of the lens relative to the sensor; the term is also used when a shallow depth of field is simulated in post-processing. A diorama is a replica of a scene, typically a three-dimensional model, miniature or full-size.

## What makes it read as this

- A high camera looking down at an angle
- A sharp band across the middle, with blur growing toward the top and bottom edges
- Saturated, toy-like colours and simple blocky buildings
- Tiny moving things: cars, boats or people
- Soft, slightly raised contrast and a light vignette

## Timing

Smooth: cars loop round the roads at different speeds, and the camera is still.

## How to build it

- Three.js: an `OrthographicCamera` or a narrow-FOV `PerspectiveCamera` placed high, and `InstancedMesh` buildings
- Tilt-shift: render to a target and blur it with a vertical mask, as in the `HorizontalTiltShiftShader` and `VerticalTiltShiftShader` examples, or use `BokehPass` with a focal band
- Raise saturation and add a soft vignette with an `OutputPass` and a colour-grade pass
- In the 2D demo: draw the town to an off-screen canvas, then draw it again through several clipped bands with increasing `blur()` (`diorama`)

## Assets

All in code here. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A light ukulele bed and distant traffic noise. Practice note.

## What makes it look wrong

- Blur across the whole frame, which reads as out of focus
- Muted, realistic colours
- A low camera: the miniature look needs a high angle

## Tested demo

This is the look from `art-forms/looks-3d.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=diorama` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  diorama: { kind: '2d', fps: null, draw(g, t, W, H) {
    // a tiny town seen from a high camera: saturated toy colours, little cars looping round the roads, and a tilt-shift blur that grows toward the top and the bottom of the frame
    const sc = new OffscreenCanvas(W, H), c = sc.getContext('2d'), cx = 480, cy = 46, cw = 31, ch = 15.5, bh = 22, iso = (x, y, z) => [cx + (x - y) * cw, cy + (x + y) * ch - z * bh];
    const sky = c.createLinearGradient(0, 0, 0, H); sky.addColorStop(0, '#bfe3ff'); sky.addColorStop(1, '#fff3d6'); c.fillStyle = sky; c.fillRect(0, 0, W, H); c.lineJoin = 'round';
    const slab = (z0, z1, x0, y0, x1, y1, col, top = col) => { polyFill(c, [iso(x0, y1, z1), iso(x1, y1, z1), iso(x1, y1, z0), iso(x0, y1, z0)], shadeHex(col, 0.8)); polyFill(c, [iso(x1, y0, z1), iso(x1, y1, z1), iso(x1, y1, z0), iso(x1, y0, z0)], shadeHex(col, 0.62)); polyFill(c, [iso(x0, y0, z1), iso(x1, y0, z1), iso(x1, y1, z1), iso(x0, y1, z1)], top); };
    slab(-0.6, 0, 0, 0, 14, 14, '#8a5a2b', '#7bc74e');
    c.fillStyle = '#59606b'; polyFill(c, [iso(0, 6, 0.02), iso(14, 6, 0.02), iso(14, 8, 0.02), iso(0, 8, 0.02)], '#59606b'); polyFill(c, [iso(6, 0, 0.02), iso(8, 0, 0.02), iso(8, 14, 0.02), iso(6, 14, 0.02)], '#59606b');
    c.strokeStyle = '#f5d742'; c.lineWidth = 2; c.setLineDash([9, 9]); for (const [a, b] of [[iso(0, 7, 0.03), iso(14, 7, 0.03)], [iso(7, 0, 0.03), iso(7, 14, 0.03)]]) { c.beginPath(); c.moveTo(...a); c.lineTo(...b); c.stroke(); } c.setLineDash([]);
    const objs = [], PAL = [[226, 70, 52], [245, 197, 24], [47, 111, 223], [244, 241, 234], [236, 110, 170], [64, 168, 92]];
    for (const [qx, qy] of [[0.4, 0.4], [8.4, 0.4], [0.4, 8.4], [8.4, 8.4]]) for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) {
      const h = hash(qx * 7 + i, qy * 5 + j, 3), x = qx + i * 1.85, y = qy + j * 1.85, col = PAL[Math.floor(hash(qx + i, qy + j, 9) * 6)];
      if (h < 0.22) objs.push({ k: x + y + 1, draw: () => { slab(0, 0.35 + h * 2, x + 0.5, y + 0.5, x + 1.3, y + 1.3, '#2e7a3a', '#3f9b4f'); } });   // a tree: a green block
      else objs.push({ k: x + y + 1.6, draw: () => { const ht = 0.9 + h * 3.2; slab(0, ht, x, y, x + 1.55, y + 1.55, hexOf(col), hexOf(mix(col, [255, 255, 255], 0.18))); for (let w = 0; w < ht - 0.5; w++) polyFill(c, [iso(x + 1.55, y + 0.3, w + 0.8), iso(x + 1.55, y + 0.6, w + 0.8), iso(x + 1.55, y + 0.6, w + 0.45), iso(x + 1.55, y + 0.3, w + 0.45)], 'rgba(255,240,170,.85)'); } });
    }
    const CARS = ['#e24634', '#2f6fdf', '#f5c518', '#f4f1ea', '#40a85c'];
    for (let i = 0; i < 8; i++) {
      const lane = i % 4, u = ((t * (1.6 + (i % 3) * 0.3) + i * 3.3) % 16) - 1, vert = lane > 1, fixed = lane % 2 ? 7.45 : 6.55, x = vert ? fixed : (lane % 2 ? 14 - u : u), y = vert ? (lane % 2 ? 14 - u : u) : fixed;
      objs.push({ k: x + y + 0.6, draw: () => slab(0.02, 0.45, x - (vert ? 0.25 : 0.45), y - (vert ? 0.45 : 0.25), x + (vert ? 0.25 : 0.45), y + (vert ? 0.45 : 0.25), CARS[i % 5], CARS[i % 5]) });
    }
    objs.sort((a, b) => a.k - b.k).forEach((o) => o.draw());
    g.drawImage(sc, 0, 0);
    for (const [y0, y1, px] of [[0, 40, 8], [40, 80, 5], [80, 120, 3], [120, 150, 1.5], [390, 420, 1.5], [420, 460, 3], [460, 500, 5], [500, 540, 8]]) { g.save(); g.beginPath(); g.rect(0, y0, W, y1 - y0); g.clip(); g.filter = `blur(${px}px)`; g.drawImage(sc, 0, 0); g.restore(); }
    g.filter = 'none'; const vg = g.createRadialGradient(480, 270, 250, 480, 270, 620); vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(40,20,0,.25)'); g.fillStyle = vg; g.fillRect(0, 0, W, H);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Tilt%E2%80%93shift_photography>
- <https://en.wikipedia.org/wiki/Diorama>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
