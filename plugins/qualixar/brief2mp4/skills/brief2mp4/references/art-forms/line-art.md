# Line art

Also called: minimal line.

Family: Drawn and painted. Cadence: steps 10 times a second. Usual tool: HyperFrames (SVG or canvas).

One weight of line on a plain ground, no shading: the drawing draws itself, then quivers slightly as if redrawn each frame.

Drawing with line alone, where tone comes only from hatching or stippling.

## What makes it read as this

- A constant or tapered stroke with round ends
- No fills, or one flat tone
- Plenty of empty space
- One accent colour at most

## Timing

Draw-on over 1 to 2 seconds, then a boil at 8 to 12 changes a second.

## How to build it

- Draw-on with `stroke-dashoffset` (canvas: a polyline to a fraction of its length)
- Boil: a seeded nudge of 1 to 2 px per point, keyed to the frame number
- SVG route: `feTurbulence` with `seed` set from the frame number, into `feDisplacementMap` (scale 1.5 to 3)
- `vector-effect: non-scaling-stroke` keeps the weight when scaled

## Assets

All in code. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A pencil or pen sound under the draw-on. Practice note.

## What makes it look wrong

- Jitter so strong the line turns to noise
- Filters that re-run on a large area every frame and slow the render

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=line-art` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'line-art': { kind: '2d', fps: 10, draw(g, t, W, H) {
    // one continuous line that draws a cup and its steam, then keeps quivering
    const f = frameOf(t, 10);
    bg(g, W, H, '#fffdf8'); g.strokeStyle = '#151515'; g.lineWidth = 3.2; g.lineCap = 'round'; g.lineJoin = 'round';
    const cup = [[W * 0.62, H * 0.5], [W * 0.36, H * 0.5], [W * 0.38, H * 0.7], [W * 0.42, H * 0.76], [W * 0.56, H * 0.76], [W * 0.6, H * 0.7], [W * 0.62, H * 0.5], ...circlePts(W * 0.625, H * 0.6, 44, 16, -Math.PI * 0.5, Math.PI * 0.5)];
    strokePart(g, cup, easeInOut(prog(t, 0.1, 1.5)), f, 1.3);
    for (let i = 0; i < 3; i++) strokePart(g, Array.from({ length: 24 }, (_, j) => [W * (0.43 + i * 0.06) + Math.sin(j * 0.6 + i) * 9, H * 0.45 - j * 6]), easeOut(prog(t, 1.5 + i * 0.2, 0.7)), f, 1.3);
    g.fillStyle = '#e0532f'; const k = easeOut(prog(t, 2.3, 0.3)); g.beginPath(); g.arc(W * 0.3, H * 0.8, 9 * k, 0, TAU); g.fill();
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Line_art>
- <https://camillovisini.com/coding/simulating-hand-drawn-motion-with-svg-filters>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
