# Flow-field generative

Also called: flow field, generative art, noise field.

Family: Abstract and generative. Cadence: smooth, full frame rate. Usual tool: HyperFrames (canvas).

Thousands of short strokes follow a drifting noise field and gather into an orb of swirling lines, in warm and violet inks on a dark ground.

Perlin noise is a type of gradient noise developed by Ken Perlin in 1983, used for procedurally generating terrain and textures. Generative art is art made in whole or in part with an autonomous system that independently determines features of the artwork.

Sourcing note: The demo uses value noise for the field, which is cheaper than Perlin noise and looks similar; the build recipe notes the swap.

## What makes it read as this

- Many thin, semi-transparent strokes, each following the field
- The field is smooth noise, so neighbouring strokes run together in streams
- A form built from where the strokes start: here a disc, thinning to sparse strokes outside it
- A small palette of warm and violet inks on near-black
- The field drifts slowly, so the form flows

## Timing

About 3,400 strokes appear over 3.4 seconds, and the field drifts continuously. Smooth, full frame rate.

## How to build it

- A field `angle(x, y) = noise(x / 150, y / 150 + time) * 2 pi`, from value noise (`vnoise()` in `looks-painted.js`); real route: Perlin or simplex noise
- Each stroke: a seeded start inside a disc, then 14 steps of 5 px along the angle
- Colour each from a five-ink palette with an opacity that falls toward the edge
- Draw with `lineCap = "round"` and a width of 1 to 2.4 px

## Assets

All in code. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

An ambient drone and a slow, evolving pad. Practice note.

## What makes it look wrong

- Opaque, thick strokes: the form turns to mush
- A noise field with too much high-frequency detail
- Every stroke the same colour and length

## Tested demo

This is the look from `art-forms/looks-abstract.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=flow-field` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'flow-field': { kind: '2d', fps: null, draw(g, t, W, H) {
    // about three thousand short strokes follow a drifting noise field: they are laid down inside a circle so that an orb of swirling lines builds up, in warm and violet inks on a dark ground
    g.fillStyle = '#0d0f1c'; g.fillRect(0, 0, W, H); g.lineCap = 'round'; const N = 3400, shown = Math.floor(N * easeOut(prog(t, 0, 3.4))), PAL = [[255, 122, 89], [255, 193, 90], [246, 242, 235], [138, 123, 255], [255, 77, 154]];
    const ang = (x, y) => (vnoise(x / 150, y / 150 + t * 0.08, 7) * 2 + vnoise(x / 60, y / 60, 9) * 0.6) * TAU;
    for (let i = 0; i < shown; i++) {
      const r = (hash(i, 1) ** 0.6) * 215, th = hash(i, 2) * TAU, outside = hash(i, 3) > 0.9, rr = outside ? 215 + hash(i, 4) * 150 : r; let x = 480 + Math.cos(th) * rr, y = 270 + Math.sin(th) * rr * 0.9; const col = PAL[Math.floor(hash(i, 5) * 5)], a = outside ? 0.22 : 0.45 + 0.3 * (1 - r / 215);
      g.strokeStyle = rgba(col, a); g.lineWidth = 1.2 + hash(i, 6) * 1.2; g.beginPath(); g.moveTo(x, y);
      for (let s = 0; s < 14; s++) { const an = ang(x, y); x += Math.cos(an) * 5; y += Math.sin(an) * 5; g.lineTo(x, y); } g.stroke();
    }
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Perlin_noise>
- <https://en.wikipedia.org/wiki/Generative_art>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
