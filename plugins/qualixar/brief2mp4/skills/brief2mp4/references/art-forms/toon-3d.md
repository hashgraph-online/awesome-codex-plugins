# Toon 3D (cel-shaded, comic-book)

Also called: cel shaded 3d, comic book 3d, toon shaded 3d, painterly 3d.

Family: Geometry, pixels and 3D. Cadence: smooth, full frame rate. Usual tool: Three.js inside HyperFrames, or Blender (Freestyle).

3D forms cut into two or three flat shading bands, with a thick ink outline on every silhouette and a printed, painterly comic-book feel. The demo is drawn in 2D, so it renders with no WebGL; the Three.js recipe below is how to build the real thing.

Cel shading, or toon shading, is a type of non-photorealistic rendering that makes 3D graphics look flat and hand-drawn: conventional smooth lighting values are quantised to a few discrete shades, so that shadows and highlights appear as blocks of colour. Black ink outlines can be made by first rendering a slightly larger black copy of the object with its back faces drawn.

## What makes it read as this

- Two or three flat bands of colour: a light, a base and a shadow, with hard edges
- A thick ink outline round the silhouette
- The shadow band tinted toward purple or blue, not just darker
- Print texture: halftone dots, hatching lines and paper grain
- A hard highlight spot and a hard-edged ground shadow

## Timing

Smooth rotation and bounce at the full frame rate; or stepped on twos for a hand-drawn feel.

## How to build it

- Three.js: `MeshToonMaterial` with a `gradientMap` of 3 texels (`DataTexture` with `NearestFilter`), so that lighting steps in three bands
- Outlines: `OutlineEffect` from the examples, or draw a back-face copy scaled by 1.03 in black
- Add a `HalftonePass`, or a halftone texture multiplied into the shadow band
- Tint the shadow band in the gradient map toward purple
- In the 2D demo: `turn()` rotates vertices, face normals pick one of three bands (`band3()`), and a thick ink stroke outlines each face

## Assets

All in code here. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Brush-stroke whooshes and a drum loop. Practice note.

## What makes it look wrong

- Smooth gradients inside the bands
- Thin or uneven outlines
- More than three bands: it starts to look like normal shading

## Tested demo

This is the look from `art-forms/looks-3d.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=toon-3d` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'toon-3d': { kind: '2d', fps: null, draw(g, t, W, H) {
    // solid forms lit from the upper left and cut into three flat shading bands, with a thick ink line round every silhouette and a printed-comic feel: halftone shadow, hatching, paper grain
    const L = norm3([-0.5, 0.7, 0.6]), tilt = 0.5, back = g.createLinearGradient(0, 0, 0, H); back.addColorStop(0, '#ffd9a0'); back.addColorStop(0.55, '#ffe8c2'); back.addColorStop(0.55, '#f2d3a0'); back.addColorStop(1, '#e8bd84'); g.fillStyle = back; g.fillRect(0, 0, W, H);
    g.fillStyle = 'rgba(214,120,90,.35)'; halftoneDots(g, [0, 0, W, 150], 9, (x, y) => 1 - y / 150);
    g.lineJoin = 'round'; g.lineCap = 'round';
    const shadow = (x, y, rx) => { g.fillStyle = 'rgba(90,50,110,.45)'; g.beginPath(); g.ellipse(x + rx * 0.35, y, rx, rx * 0.28, 0, 0, TAU); g.fill(); };
    const solid = (verts, faces, base, cx, cy, S, a) => {
      const pts = verts.map((v) => turn(v, a, tilt)), out = faces.map((f) => { const n = turn(f.n, a, tilt), p = f.v.map((i) => pts[i]); return { n, p, d: p.reduce((s, q) => s + q[2], 0) }; }).filter((f) => f.n[2] > 0).sort((u, v) => u.d - v.d);
      for (const f of out) { const v = dot3(f.n, L), scr = f.p.map(([x, y]) => [cx + x * S, cy - y * S]); polyFill(g, scr, band3(base, v), INK, 5.5); if (v <= 0.1) { g.save(); path(g, scr); g.clip(); g.globalAlpha = 0.35; lines(g, [cx - S * 2, cy - S * 2, cx + S * 2, cy + S * 2], 0.8, 7, 1.6, INK); g.restore(); } }
    };
    const cube = [[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1], [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], cf = [{ v: [4, 5, 6, 7], n: [0, 0, 1] }, { v: [1, 0, 3, 2], n: [0, 0, -1] }, { v: [5, 1, 2, 6], n: [1, 0, 0] }, { v: [0, 4, 7, 3], n: [-1, 0, 0] }, { v: [7, 6, 2, 3], n: [0, 1, 0] }, { v: [0, 1, 5, 4], n: [0, -1, 0] }];
    const pyr = [[-1, -1, -1], [1, -1, -1], [1, -1, 1], [-1, -1, 1], [0, 1.3, 0]], pf = [{ v: [3, 2, 4], n: norm3([0, 0.5, 1]) }, { v: [2, 1, 4], n: norm3([1, 0.5, 0]) }, { v: [1, 0, 4], n: norm3([0, 0.5, -1]) }, { v: [0, 3, 4], n: norm3([-1, 0.5, 0]) }];
    shadow(250, 420, 110); solid(cube, cf, [226, 70, 52], 250, 330, 78, t * 0.8);
    shadow(700, 430, 100); solid(pyr, pf, [246, 200, 50], 700, 350, 86, -t * 0.6 + 0.4);
    const by = 330 - Math.abs(Math.sin(t * 2.2)) * 60, R = 92, bx = 480; shadow(bx, 440, 80 - (330 - by) * 0.2);
    g.save(); g.beginPath(); g.arc(bx, by, R, 0, TAU); g.clip(); g.fillStyle = band3([52, 112, 224], -1); g.fillRect(bx - R, by - R, 2 * R, 2 * R); g.fillStyle = band3([52, 112, 224], 0.3); g.beginPath(); g.arc(bx - 0.28 * R, by - 0.3 * R, 0.94 * R, 0, TAU); g.fill(); g.fillStyle = band3([52, 112, 224], 0.9); g.beginPath(); g.arc(bx - 0.4 * R, by - 0.42 * R, 0.6 * R, 0, TAU); g.fill();
    g.globalAlpha = 0.4; g.fillStyle = INK; halftoneDots(g, [bx - R, by - R, bx + R, by + R], 7, (x, y) => clamp(((x - bx) + (y - by)) / (1.4 * R))); g.restore();
    g.fillStyle = '#fff'; g.beginPath(); g.ellipse(bx - 0.46 * R, by - 0.5 * R, 0.16 * R, 0.09 * R, -0.7, 0, TAU); g.fill();
    g.strokeStyle = INK; g.lineWidth = 6.5; g.beginPath(); g.arc(bx, by, R, 0, TAU); g.stroke();
    speckle(g, W, H, 4, 36, [120, 80, 50]);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Cel_shading>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
