# Crayon and oil pastel

Also called: wax crayon, oil pastel, crayon drawing.

Family: Drawn and painted. Cadence: steps 8 times a second. Usual tool: HyperFrames (canvas).

Waxy, broken strokes of bright colour on toothed paper, scribbled in one slanted direction with fat outlines pushed past the edges. It looks like a child's drawing with real pressure in it.

A crayon is a stick of pigmented wax, in the modern English-speaking world mostly paraffin. In 1924 two Japanese teachers set out to make a high-viscosity crayon, the oil pastel, which binds pigment in wax and non-drying oil, so that children could draw freely in colour.

## What makes it read as this

- Scribbled fills in one slanted direction, each pass with its own pressure
- Paper tooth shows through the wax as speckles of paper colour
- Fat outlines in a darker shade of the fill, pushed a little past the edge
- Bright, simple, saturated colour: red roof, blue door, green grass
- Simple subjects drawn the way a child would: sun with rays, house, tree

## Timing

Each area is scribbled in over 0.3 to 0.9 seconds, sky and grass first, the subject after, small details last, about 4 seconds in all. The picture steps about 8 times a second.

## How to build it

- Scribble: near-parallel passes inside a rotated box, each stroke its own opacity and width (`scribble()` in `looks-painted.js`), clipped to the shape
- A second, lighter, dashed pass at another angle across the first
- Outlines: a fat, darker stroke with a seeded wobble that is re-seeded on each step
- Tooth: coarse specks in the paper colour drawn over everything (`tooth()` with scale 2)

## Assets

All in code. A scan of cream sugar paper helps if the user has one. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A waxy scratching sound under each scribble, a ukulele or xylophone bed. Practice note.

## What makes it look wrong

- Clean flat fills with no stroke direction
- Thin precise outlines
- Tooth specks so fine that they read as film noise

## Tested demo

This is the look from `art-forms/looks-painted.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=crayon` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  crayon: { kind: '2d', fps: 8, draw(g, t, W, H) {
    // a child's picture in wax: scribbled fills laid from the top down, fat outlines past the edges, and paper tooth showing through every stroke
    const ts = held(t, 8), f = frameOf(t, 8); bg(g, W, H, '#f6f0e0'); g.lineCap = 'round';
    const fillIn = (clip, bb, col, start, dur, seed, w) => { g.save(); g.clip(clip); scribble(g, bb, col, prog(ts, start, dur), f, seed, w); g.restore(); };
    const outline = (pts, col, start, dur) => { g.strokeStyle = rgba(col, 0.9); g.lineWidth = 6; g.lineJoin = 'round'; strokePart(g, pts, prog(ts, start, dur), f + 5, 1.8); };
    fillIn(poly([[0, 0], [W, 0], [W, 392], [0, 392]]), [0, 0, W, 392], [120, 190, 235], 0, 0.9, 1, 14);
    [[470, 96, 1], [760, 70, 0.8]].forEach(([x, y, k], i) => { const c = cloudPts(x, y, k); fillIn(poly(c), [x - 90 * k, y - 60 * k, x + 90 * k, y + 40 * k], [252, 252, 250], 0.9 + i * 0.2, 0.4, 40 + i, 11); outline(c, [110, 160, 215], 1.0 + i * 0.2, 0.4); });   // clouds: puffed outlines scribbled white
    const sun = circlePts(170, 130, 62, 28); fillIn(poly(sun), [100, 60, 240, 200], [250, 205, 40], 0.6, 0.5, 2, 10); outline(sun, [235, 150, 30], 0.7, 0.4);
    for (let i = 0; i < 10; i++) { const a = (i / 10) * TAU; g.strokeStyle = rgba([240, 140, 30], 0.9); g.lineWidth = 7; strokePart(g, [[170 + Math.cos(a) * 80, 130 + Math.sin(a) * 80], [170 + Math.cos(a) * 112, 130 + Math.sin(a) * 112]], prog(ts, 1.1 + i * 0.03, 0.15), f, 1.5); }
    fillIn(poly([[0, 372], [W, 372], [W, H], [0, H]]), [0, 372, W, H], [70, 170, 60], 1.3, 0.7, 3, 11);
    const walls = [[360, 270], [600, 270], [600, 420], [360, 420]]; fillIn(poly(walls), [360, 270, 600, 420], [225, 130, 55], 1.9, 0.5, 4, 10); outline([...walls, walls[0]], [150, 80, 30], 2.0, 0.5);
    const roof = [[335, 276], [480, 168], [625, 276]]; fillIn(poly(roof), [335, 168, 625, 276], [214, 56, 46], 2.5, 0.4, 5, 10); outline([...roof, roof[0]], [140, 30, 30], 2.6, 0.35);
    fillIn(poly([[455, 330], [505, 330], [505, 420], [455, 420]]), [455, 330, 505, 420], [46, 95, 181], 2.9, 0.3, 6, 9);
    fillIn(poly([[385, 300], [430, 300], [430, 345], [385, 345]]), [385, 300, 430, 345], [252, 215, 60], 3.0, 0.2, 7, 9);
    g.strokeStyle = rgba([140, 80, 30], 0.9); g.lineWidth = 4; strokePart(g, [[407, 300], [407, 345]], prog(ts, 3.2, 0.1), f, 1); strokePart(g, [[385, 322], [430, 322]], prog(ts, 3.25, 0.1), f, 1);
    fillIn(poly([[722, 300], [752, 300], [752, 420], [722, 420]]), [722, 300, 752, 420], [125, 76, 40], 3.2, 0.3, 8, 9);
    const crown = circlePts(737, 250, 78, 28); fillIn(poly(crown), [655, 170, 820, 330], [60, 150, 58], 3.4, 0.5, 9, 10); outline(crown, [30, 100, 40], 3.5, 0.5);
    for (let i = 0; i < 9; i++) { const x = 40 + hash(i, 1) * 880, y = 430 + hash(i, 2) * 90, k = prog(ts, 3.8 + i * 0.06, 0.15); g.strokeStyle = rgba([40, 120, 40], 0.9); g.lineWidth = 4; strokePart(g, [[x, y + 26], [x + 2, y]], k, f, 1); g.fillStyle = rgba(i % 2 ? [225, 60, 110] : [255, 235, 70], 0.95); if (k > 0.9) { g.beginPath(); g.arc(x + 2, y - 4, 9, 0, TAU); g.fill(); } }
    speckle(g, W, H, 21, 190, [248, 243, 230], 2); paper(g, W, H, 22, 12);   // the tooth: paper-coloured specks over wax
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Crayon>
- <https://en.wikipedia.org/wiki/Oil_pastel>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
