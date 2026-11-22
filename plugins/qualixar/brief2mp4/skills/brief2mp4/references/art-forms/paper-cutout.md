# Paper cut-out

Also called: papercraft, cutout animation.

Family: Craft and handmade. Cadence: steps 12 times a second. Usual tool: HyperFrames (canvas, SVG or DOM).

Flat shapes cut from paper or card, layered, and moved a pose at a time. Parts hinge at joints; nothing bends.

Lotte Reiniger's The Adventures of Prince Achmed (1926) is the oldest surviving animated feature. Terry Gilliam's Monty Python animations and the South Park pilot used cut paper.

## What makes it read as this

- Flat fills with hard, slightly uneven cut edges
- Layers stacked with a small, tight shadow under each
- Rigid parts that rotate about a pivot
- Paper grain over everything
- A limited, slightly muted palette

## Timing

Stop-motion cadence, usually on twos. Motion is rotation about joints and sliding, with pops and holds.

## How to build it

- Each part is its own shape; nudge the corners with a seeded hash so edges look cut by hand
- Canvas: `shadowOffsetY` 3 to 4 px with `shadowBlur` 4 to 5 px per layer. DOM: `filter: drop-shadow()`
- Joints: rotate about a pivot (`transformOrigin` in GSAP, `translate` then `rotate` on a canvas)
- Paper grain: a noise texture drawn once and laid over with `multiply`
- SVG route: `feTurbulence` into `feDisplacementMap` (scale 2 to 4) roughens an edge

Use Blender for real folded paper with thickness and light passing through it.

## Assets

Shapes drawn in code or as SVG. Photo cut-outs need images you own, or generated ones. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Paper rustle, snips, soft ticks on pose changes. Practice note.

## What makes it look wrong

- Smooth vector motion with no stepping
- Perfect edges
- Large soft shadows, which look like interface cards, not paper

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=paper-cutout` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'paper-cutout': { kind: '2d', fps: 12, draw(g, t, W, H) {
    // flat layers with scissor-cut edges and small shadows; the bird's wings hinge at the shoulder, on twos
    const ts = onTwos(t), f = frameOf(t, 12);
    bg(g, W, H, '#f3e6c8');
    const layer = (pts, col, seed, dy) => { g.save(); g.shadowColor = 'rgba(70,40,10,.38)'; g.shadowBlur = 5; g.shadowOffsetX = 3; g.shadowOffsetY = 4; cut(g, pts.map(([x, y]) => [x, y + dy]), seed, 3); fill(g, col); g.restore(); };
    g.save(); g.shadowColor = 'rgba(70,40,10,.3)'; g.shadowBlur = 4; g.shadowOffsetY = 3; blob(g, W * 0.76, H * 0.26, 62, 4, 0.03); fill(g, '#e9763b'); g.restore();
    layer([[0, 330], [170, 250], [330, 300], [520, 230], [720, 290], [960, 240], [960, 540], [0, 540]], '#7fa27a', 11, Math.sin(ts * 1.2) * 3);
    layer([[0, 400], [210, 340], [400, 390], [610, 330], [800, 380], [960, 350], [960, 540], [0, 540]], '#4f7d67', 12, Math.sin(ts * 1.2 + 1) * 4);
    layer([[0, 470], [250, 430], [500, 470], [760, 430], [960, 460], [960, 540], [0, 540]], '#2f5a52', 13, 0);
    const bx = lerp(-80, W + 80, (ts / 3) % 1), by = 150 + Math.sin(ts * 3) * 22, flap = Math.sin(ts * 14) * 0.7;
    g.save(); g.translate(bx, by); g.shadowColor = 'rgba(70,40,10,.4)'; g.shadowBlur = 4; g.shadowOffsetY = 4;
    for (const s of [-1, 1]) { g.save(); g.rotate(s * flap); cut(g, [[0, 0], [s * 58, -20], [s * 46, 12]], 30 + s, 1.5); fill(g, '#f7f1e3'); g.restore(); }
    cut(g, [[-26, -9], [30, -5], [44, 4], [26, 12], [-30, 9]], 33, 1.5); fill(g, '#fffaf0'); g.restore();
    paper(g, W, H, 2, 30 + jit(f, 3, 2));
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Cutout_animation>
- <https://en.wikipedia.org/wiki/Lotte_Reiniger>
- <https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/feDisplacementMap>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
