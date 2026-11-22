# Bauhaus geometric

Also called: bauhaus, bauhaus style, geometric poster.

Family: Abstract and generative. Cadence: steps 12 times a second. Usual tool: HyperFrames (canvas or SVG).

A poster of primary-colour circles, squares and triangles with black bars on a grid of cream and black lines, where every piece jumps from cell to cell in clean steps.

The Staatliches Bauhaus was a German art school, operating from 1919 to 1933, that combined crafts and the fine arts; it was founded by the architect Walter Gropius in Weimar, and became famous for an approach to design that emphasised function and tried to unify individual artistic vision with mass production.

## What makes it read as this

- Primary colours only: red, yellow and blue, with black and off-white
- Basic shapes: circle, square, triangle and their halves
- Black bars and a visible grid
- Flat fills, no gradients, no texture beyond paper
- Asymmetric, balanced composition; motion in whole grid steps

## Timing

Every piece moves to its next cell about every 0.6 seconds, the move settling in 0.3 seconds. Drawn at 12 changes a second.

## How to build it

- Lay out shapes on an 80 px grid; each piece has a short route of cells that it cycles through
- Step with `Math.floor(time * rate)` and ease the move with `easeOut(fraction / 0.3)`
- Draw with `arc`, `fillRect` and `lineTo` fills and thick black outlines
- Add faint grid lines and a light paper speckle

## Assets

All in code. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A clicking rhythm and a dry, minimal marimba. Practice note.

## What makes it look wrong

- Gradients and soft shadows
- Curved, ornamental decoration
- Smooth sliding between positions, which loses the stepped feel

## Tested demo

This is the look from `art-forms/looks-abstract.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=bauhaus` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  bauhaus: { kind: '2d', fps: 12, draw(g, t, W, H) {
    // a poster of primary-colour circles, squares and triangles with black bars on a grid of cream and black lines; every piece jumps cell by cell in clean steps, and each step settles quickly
    const ts = held(t, 12), CELL = 80, RED = '#d62828', YEL = '#f7b32b', BLU = '#1d4ea1', K = '#111', step = ts * 1.6, si = Math.floor(step), fr = step - si, e = easeOut(clamp(fr / 0.3));
    g.fillStyle = '#f0e6d0'; g.fillRect(0, 0, W, H); g.strokeStyle = 'rgba(17,17,17,.22)'; g.lineWidth = 1; g.beginPath(); for (let x = 0; x <= W; x += CELL) { g.moveTo(x, 0); g.lineTo(x, H); } for (let y = 0; y <= H; y += CELL) { g.moveTo(0, y); g.lineTo(W, y); } g.stroke();
    const at = (route) => { const a = route[si % route.length], b = route[(si + 1) % route.length]; return [lerp(a[0], b[0], e) * CELL, lerp(a[1], b[1], e) * CELL]; };
    const bar = (route, w, h) => { const [x, y] = at(route); g.fillStyle = K; g.fillRect(x, y, w * CELL, h * CELL); };
    bar([[0, 5], [0, 4], [1, 4], [0, 4]], 6, 0.35); bar([[8, 0], [9, 0], [9, 1], [8, 1]], 0.35, 5); bar([[5, 2], [5, 3], [4, 3], [5, 3]], 5, 0.25);
    { const [x, y] = at([[1, 1], [3, 1], [3, 3], [1, 3]]); g.fillStyle = YEL; g.fillRect(x, y, 2 * CELL, 2 * CELL); g.strokeStyle = K; g.lineWidth = 4; g.strokeRect(x, y, 2 * CELL, 2 * CELL); }
    { const [x, y] = at([[6, 2], [6, 4], [8, 4], [8, 2]]); g.fillStyle = RED; g.beginPath(); g.arc(x + CELL, y + CELL, CELL * 1.5, 0, TAU); g.fill(); g.fillStyle = K; g.beginPath(); g.arc(x + CELL, y + CELL, CELL * 0.45, 0, TAU); g.fill(); }
    { const [x, y] = at([[2, 4], [2, 5], [0, 5], [0, 4]]); g.fillStyle = BLU; g.beginPath(); g.moveTo(x, y + 2 * CELL); g.lineTo(x + 2 * CELL, y + 2 * CELL); g.lineTo(x + CELL, y); g.closePath(); g.fill(); }
    { const [x, y] = at([[9, 4], [10, 4], [10, 2], [9, 2]]); g.fillStyle = BLU; g.beginPath(); g.arc(x + CELL, y + CELL, CELL, Math.PI, TAU); g.closePath(); g.fill(); g.fillStyle = YEL; g.beginPath(); g.arc(x + CELL, y + CELL, CELL * 0.5, Math.PI, TAU); g.closePath(); g.fill(); }
    { const [x, y] = at([[4, 0], [4, 1], [5, 1], [6, 0]]); g.fillStyle = K; g.beginPath(); g.arc(x + CELL / 2, y + CELL / 2, CELL / 2, 0, TAU); g.fill(); }
    { const [x, y] = at([[3, 5], [4, 5], [4, 4], [3, 4]]); g.fillStyle = RED; g.fillRect(x, y, CELL, CELL); g.fillStyle = '#f0e6d0'; g.beginPath(); g.arc(x + CELL, y + CELL, CELL * 0.8, Math.PI, Math.PI * 1.5); g.lineTo(x + CELL, y + CELL); g.fill(); }
    { const [x, y] = at([[10, 5], [10, 6], [9, 6], [9, 5]]); g.fillStyle = YEL; g.beginPath(); g.moveTo(x, y + CELL); g.lineTo(x + CELL, y); g.lineTo(x + CELL, y + CELL); g.closePath(); g.fill(); }
    speckle(g, W, H, 5, 20, [90, 70, 40]);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Bauhaus>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
