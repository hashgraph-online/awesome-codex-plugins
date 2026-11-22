# Oil painting and impasto

Also called: oil paint, impasto.

Family: Drawn and painted. Cadence: steps 12 times a second. Usual tool: HyperFrames (canvas).

Thick oil paint laid in visible, directional brush strokes: colour mixed on the canvas, strokes that follow the shape of the thing, and raised light ridges where the paint is heaped up.

Oil painting binds pigment in a drying oil. The oldest known oil paintings are 7th-century Buddhist works in Afghanistan, and by the height of the Renaissance oil had almost replaced egg tempera for panel painting in most of Europe. Impasto is paint laid on thickly enough that brush or painting-knife strokes show.

## What makes it read as this

- Visible brush strokes that follow the form: curved round a sun, straight along water
- Each stroke has a light ridge on one side and a darker edge on the other, so the paint looks thick
- Rich, mixed colour with small variations from stroke to stroke
- Thick light daubs (impasto) on the brightest spots
- A first blocked-in wash under the strokes

## Timing

A first wash blocks the colour in, then strokes cover the canvas over about 3 seconds, the brightest daubs last. The picture steps about 12 times a second, like a timelapse of a painter.

## How to build it

- Draw each stroke as a short thick line with round caps, three times: a dark copy offset down and right, the colour, and a thin lighter copy offset up and left (`brush()` in `looks-painted.js`)
- Choose each stroke's angle from a flow field: tangent to circles round a focus, level over water
- Choose colour from position with a seeded jitter per stroke so no two match
- Reveal each stroke from a seeded start time so the canvas fills at random places

## Assets

All in code. Three.js can use a normal map from the stroke ridges for a real impasto light, but the 2D version reads well. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Brush on canvas, a slow room tone, a calm piano or strings bed. Practice note.

## What makes it look wrong

- Strokes all the same angle, which reads as a filter
- Smooth gradients inside the strokes
- No ridge highlights, which makes the paint look flat and digital

## Tested demo

This is the look from `art-forms/looks-painted.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=oil-painting` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'oil-painting': { kind: '2d', fps: 12, draw(g, t, W, H) {
    // a sun over a bay in directional daubs: each carries a shadow side, a bristle streak and a light ridge; thick cream daubs sit on top as impasto
    const ts = held(t, 12), cell = 21, hz = H * 0.64; g.lineCap = 'round';
    bg(g, W, H, '#22204a');
    g.filter = 'blur(20px)';
    for (let y = -54; y < H + 54; y += 54) for (let x = -54; x < W + 54; x += 54) { g.fillStyle = rgba(oilColour(x + 27, y + 27, W, H).map((v) => v * 0.78), easeOut(prog(ts, 0, 0.7))); g.fillRect(x, y, 55, 55); }   // the first wash blocks the colours in
    g.filter = 'none';
    for (let j = -1; j <= H / cell; j++) for (let i = -1; i <= W / cell; i++) {
      const x = (i + 0.5 + (hash(i, j, 1) - 0.5) * 0.8) * cell, y = (j + 0.5 + (hash(i, j, 2) - 0.5) * 0.8) * cell, k = easeOut(prog(ts, hash(i, j, 3) * 2.3 + (y / H) * 0.4, 0.35));
      if (k <= 0) continue;
      const col = oilColour(x, y, W, H).map((v, c) => v + (hash(i, j, 4 + c) - 0.5) * 34), a = oilAngle(x, y, W, H) + (hash(i, j, 8) - 0.5) * 0.5;
      brush(g, x, y, a, 44, 13, col, k, y > hz ? 0.3 : 0.38);
    }
    for (let i = 0; i < 60; i++) {   // impasto: thick, light daubs around the sun and along the reflection
      const onSun = i < 34, a = hash(i, 5) * TAU, r = hash(i, 6) * 96, x = onSun ? W * 0.64 + Math.cos(a) * r : W * 0.64 + (hash(i, 7) - 0.5) * 80, y = onSun ? H * 0.4 + Math.sin(a) * r * 0.9 : hz + 14 + hash(i, 8) * (H - hz - 30);
      const k = easeOut(prog(ts, 1.6 + hash(i, 9) * 1.4, 0.3)); if (k > 0) brush(g, x, y, onSun ? a + Math.PI / 2 : Math.PI / 2, 28, 15, onSun ? [255, 246, 190] : [255, 214, 120], k, 0.85);
    }
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Oil_painting>
- <https://en.wikipedia.org/wiki/Impasto>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
