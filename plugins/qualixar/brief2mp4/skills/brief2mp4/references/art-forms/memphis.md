# Memphis design

Also called: memphis style, 80s memphis, memphis pattern.

Family: Type, data and retro. Cadence: steps 12 times a second. Usual tool: HyperFrames (canvas or SVG).

Scattered, playful confetti in the manner of 1980s Memphis design: squiggles and zigzags, triangles, circles and half-circles in red, yellow, blue and pink, black-and-white checks, stripes and dots.

The Memphis Group, also called Memphis Milano, was an Italian design and architecture group founded by Ettore Sottsass and active from 1980 to 1987. Its postmodern work often used plastic laminate and terrazzo and was characterised by colourful, abstract decoration and asymmetrical shapes; the look became a ubiquitous aesthetic of the mid-1980s to mid-1990s.

## What makes it read as this

- Bold primary colours with pink and black: red, yellow, blue and pink
- Confetti shapes: triangles, circles, half-circles, squiggles and zigzags
- Black-and-white patterns: checks, stripes and dots inside shapes
- Thick black outlines and asymmetrical, overlapping placement
- A pale peach or pink ground, with tiny terrazzo flecks

## Timing

Shapes pop in over the first 1.6 seconds, then drift and turn slowly. Drawn at 12 changes a second.

## How to build it

- Place each shape from a hash of its index: type, size, position, colour and spin
- Patterns: a 4 by 4 checkerboard, a circle clipped to black stripes, a grid of dots
- Squiggle: a sine polyline with a thick round-capped stroke
- Pop-in with `overshoot(prog(...))`; drift with a sine of stepped time

## Assets

All in code. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A bouncy synth-pop bed with clicks and pops. Practice note.

## What makes it look wrong

- Gradients and soft shadows
- Neat alignment: Memphis is deliberately off-kilter
- Muted colours
- Copying a specific designer's piece

## Tested demo

This is the look from `art-forms/looks-abstract.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=memphis` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  memphis: { kind: '2d', fps: 12, draw(g, t, W, H) {
    // 1980s Memphis design: squiggles and zigzags, confetti shapes in red, yellow, blue and pink, black-and-white checks, stripes and dots, scattered and drifting on twos over a peach ground
    const ts = held(t, 12), PAL = ['#ff3b30', '#ffd60a', '#1e6bff', '#ff6bb5', '#14101a'], O = '#14101a'; g.fillStyle = '#ffe8d6'; g.fillRect(0, 0, W, H); g.lineCap = 'round'; g.lineJoin = 'round';
    for (let i = 0; i < 150; i++) { g.fillStyle = PAL[Math.floor(hash(i, 1) * 5)]; g.save(); g.translate(hash(i, 2) * W, hash(i, 3) * H); g.rotate(hash(i, 4) * TAU); g.fillRect(-6, -1.5, 12, 3); g.restore(); }
    for (let i = 0; i < 40; i++) {
      const st = hash(i, 5) * 1.6, k = overshoot(prog(ts, st, 0.45)); if (k <= 0.01) continue; const kind = Math.floor(hash(i, 6) * 8), sz = 38 + hash(i, 7) * 62, x = 60 + hash(i, 8) * (W - 120), y = 50 + hash(i, 9) * (H - 100) + Math.sin(ts * 0.8 + i) * 12, col = PAL[Math.floor(hash(i, 10) * 4)];
      g.save(); g.translate(x, y); g.rotate(hash(i, 11) * TAU + ts * 0.5 * (i % 2 ? 1 : -1) * 0.4); g.scale(k, k); g.lineWidth = 5; g.strokeStyle = O; g.fillStyle = col;
      if (kind === 0) { polyFill(g, [[0, -sz / 2], [sz / 2, sz / 2], [-sz / 2, sz / 2]], col, O, 5); }
      else if (kind === 1) { ell(g, 0, 0, sz / 2, sz / 2, col, O, 5); }
      else if (kind === 2) { g.beginPath(); g.arc(0, 0, sz / 2, Math.PI, TAU); g.closePath(); g.fill(); g.stroke(); }
      else if (kind === 3) { g.lineWidth = 11; g.strokeStyle = col; g.beginPath(); for (let j = 0; j <= 20; j++) { const px = -sz + j * (sz / 10), py = Math.sin(j * 1.1) * 11; j ? g.lineTo(px, py) : g.moveTo(px, py); } g.stroke(); }
      else if (kind === 4) { g.lineWidth = 9; g.strokeStyle = O; g.beginPath(); for (let j = 0; j <= 6; j++) { const px = -sz + j * (sz / 3), py = (j % 2 ? 14 : -14); j ? g.lineTo(px, py) : g.moveTo(px, py); } g.stroke(); }
      else if (kind === 5) { g.fillStyle = '#fff'; g.fillRect(-sz / 2, -sz / 2, sz, sz); g.fillStyle = O; for (let a = 0; a < 4; a++) for (let b = 0; b < 4; b++) if ((a + b) % 2 === 0) g.fillRect(-sz / 2 + a * sz / 4, -sz / 2 + b * sz / 4, sz / 4, sz / 4); g.strokeRect(-sz / 2, -sz / 2, sz, sz); }
      else if (kind === 6) { g.save(); g.beginPath(); g.arc(0, 0, sz / 2, 0, TAU); g.clip(); g.fillStyle = '#fff'; g.fillRect(-sz, -sz, 2 * sz, 2 * sz); g.fillStyle = O; for (let a = -sz; a < sz; a += 14) g.fillRect(a, -sz, 6, 2 * sz); g.restore(); g.beginPath(); g.arc(0, 0, sz / 2, 0, TAU); g.stroke(); }
      else { g.fillStyle = col; g.fillRect(-sz / 2, -sz / 2, sz, sz); g.fillStyle = O; for (let a = 0; a < 4; a++) for (let b = 0; b < 4; b++) { g.beginPath(); g.arc(-sz * 0.375 + a * sz / 4, -sz * 0.375 + b * sz / 4, 3.4, 0, TAU); g.fill(); } g.strokeRect(-sz / 2, -sz / 2, sz, sz); }
      g.restore();
    }
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Memphis_Group>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
