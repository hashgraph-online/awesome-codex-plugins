# Liquid metaball (blobs that merge)

Also called: metaball, metaballs, liquid blobs, gooey blobs.

Family: Abstract and generative. Cadence: smooth, full frame rate. Usual tool: HyperFrames (canvas or WebGL shader).

Glossy liquid blobs that drift, merge and split: a smooth colour gradient from warm to violet, a bright rim, and a soft highlight on each blob.

Metaballs, also known as blobby objects, are organic-looking n-dimensional isosurfaces characterised by their ability to meld together when in close proximity to create single, contiguous objects.

## What makes it read as this

- Round blobs that join with smooth necks and part again
- A glossy surface: a bright highlight, a rim of light, and a darker side
- A smooth colour gradient across the blobs, warm to violet
- A dark, simple ground
- Slow, floating motion on overlapping paths

## Timing

Seven blobs drift on sine paths; merges and splits happen as they pass. Smooth, full frame rate.

## How to build it

- Sum a field `F = sum(r^2 / d^2)` over a low-resolution grid (240 by 135) and treat `F > 1` as inside
- Smooth the edge with `clamp((F - 0.92) / 0.16)` and light the surface from the gradient of a saturating copy of `F` (`tanh`)
- Colour: a mix across x and y; add a diffuse term, a specular term (power 40) and an environment rim
- Upscale with smoothing. Real route: a fragment shader doing the same sum per pixel, or `MarchingCubes` in Three.js

## Assets

All in code. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Soft bubbling and a smooth pad. Practice note.

## What makes it look wrong

- Hard-edged circles with no merging
- Flat colour: the gloss is the look
- Too many blobs: they turn into one mass

## Tested demo

This is the look from `art-forms/looks-abstract.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=liquid-metaball` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'liquid-metaball': { kind: '2d', fps: null, draw(g, t, W, H) {
    // glossy liquid blobs that drift, merge and split: a field is summed from seven soft circles, thresholded, and lit with a rim, a highlight and a smooth warm-to-violet colour gradient
    const w = 240, h = 135, F = new Float32Array(w * h), img = new ImageData(w, h), B = [];
    for (let i = 0; i < 7; i++) B.push([w * (0.5 + 0.34 * Math.sin(t * (0.5 + i * 0.13) + i * 1.7)), h * (0.5 + 0.34 * Math.cos(t * (0.42 + i * 0.11) + i * 2.3)), 15 + (i % 3) * 5]);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { let s = 0; for (const [bx, by, r] of B) s += (r * r) / ((x - bx) ** 2 + (y - by) ** 2 + 1); F[y * w + x] = s; }
    const G = F.map((v) => Math.tanh(v * 0.55) * 2.4);   // a saturating copy for the surface normal: the field spikes at each blob's centre, and this keeps the tops round, not pitted
    const Lg = [-0.5, -0.6, 0.62];
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const i = y * w + x, bgk = y / h, a = clamp((F[i] - 0.92) / 0.16); let r = lerp(18, 44, bgk), gg = lerp(10, 14, bgk), b = lerp(42, 90, bgk);
      if (a > 0) {
        const gx = (G[i + 1] ?? G[i]) - (G[i - 1] ?? G[i]), gy = (G[i + w] ?? G[i]) - (G[i - w] ?? G[i]), nl = Math.hypot(gx, gy, 0.35), nx = -gx / nl, ny = -gy / nl, nz = 0.35 / nl, diff = Math.max(0, nx * Lg[0] + ny * Lg[1] + nz * Lg[2]), hx = nx * Lg[0] + ny * Lg[1] + nz * (Lg[2] + 1), spec = Math.max(0, hx / (Math.hypot(...Lg.map((v, k) => v + (k === 2 ? 1 : 0))) || 1)) ** 40, rim = (1 - nz) ** 2;
        const base = mix(mix([255, 61, 129], [255, 159, 28], x / w), [122, 92, 255], y / h), env = 0.35 + 0.65 * Math.max(0, ny) ** 0.8;
        r = lerp(r, base[0] * (0.25 + 0.75 * diff) + 120 * rim * env + 255 * spec, a); gg = lerp(gg, base[1] * (0.25 + 0.75 * diff) + 90 * rim * env + 255 * spec, a); b = lerp(b, base[2] * (0.25 + 0.75 * diff) + 160 * rim * env + 255 * spec, a);
      }
      img.data[i * 4] = r; img.data[i * 4 + 1] = gg; img.data[i * 4 + 2] = b; img.data[i * 4 + 3] = 255;
    }
    const sc = new OffscreenCanvas(w, h); sc.getContext('2d').putImageData(img, 0, 0); g.imageSmoothingEnabled = true; g.drawImage(sc, 0, 0, W, H);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Metaballs>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
