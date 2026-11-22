# Psychedelic

Also called: psychedelia, 60s poster, acid poster.

Family: Abstract and generative. Cadence: smooth, full frame rate. Usual tool: HyperFrames (canvas or WebGL shader).

A 1960s concert-poster look: concentric rings warped by slow waves in a cycling run of warm, saturated colours, with black ink lines over rays that turn behind them.

Psychedelic art is art, graphics or visual displays related to or inspired by psychedelic experiences; in common use it refers to the art movement of the late 1960s and early 1970s counterculture, with highly distorted or surreal visuals, bright colours and full spectrums.

## What makes it read as this

- Concentric rings warped by sine waves: they breathe and ripple
- Saturated, warm, hot colours: orange, yellow, hot pink, violet, red
- Black outline between every band
- Colours that cycle through the rings over time
- Rays or stripes behind the pattern, turning slowly

## Timing

The colours cycle at about 2.2 bands a second; the warps drift continuously. Smooth, full frame rate.

## How to build it

- Each ring is a closed polyline with `r + A sin(5 a + t + k) + B sin(3 a - t + k)` for radius; draw rings from the outside in
- Colour each by a palette index offset by a time shift, cross-faded with the next entry
- Outline each with a 3.4 px near-black stroke
- Back layer: 36 wedges that alternate two colours and rotate slowly
- Keep to warm colours: no teal and no mint

## Assets

All in code. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A wah-guitar, a Hammond organ and a spinning-tape echo. Practice note.

## What makes it look wrong

- Cool teal or mint colours
- Thin, polite outlines or no outline
- Static rings: the ripple and the colour cycle are the look

## Tested demo

This is the look from `art-forms/looks-abstract.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=psychedelic` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  psychedelic: { kind: '2d', fps: null, draw(g, t, W, H) {
    // a 1960s concert poster: concentric rings warped by slow waves, filled in a cycling run of warm saturated colours with black ink lines, over rays that turn behind them
    const PAL = [[255, 77, 28], [255, 158, 27], [255, 213, 31], [255, 61, 143], [138, 43, 217], [255, 107, 107], [255, 179, 198]], cx = 480, cy = 270, sh = t * 2.2, base = Math.floor(sh), fr = sh - base;
    const colAt = (k) => rgba(mix(PAL[(k + base) % 7], PAL[(k + base + 1) % 7], fr)); g.lineJoin = 'round';
    for (let i = 0; i < 36; i++) { const a0 = (i / 36) * TAU + t * 0.12, a1 = a0 + TAU / 36; g.fillStyle = i % 2 ? '#ffb347' : '#ff4d8f'; g.beginPath(); g.moveTo(cx, cy); g.lineTo(cx + Math.cos(a0) * 900, cy + Math.sin(a0) * 900); g.lineTo(cx + Math.cos(a1) * 900, cy + Math.sin(a1) * 900); g.closePath(); g.fill(); }
    for (let k = 17; k >= 0; k--) {
      g.beginPath(); for (let j = 0; j <= 120; j++) { const a = (j / 120) * TAU, r = 28 + k * 25 + Math.sin(a * 5 + t * 1.3 + k * 0.35) * (6 + k * 1.6) + Math.sin(a * 3 - t * 0.9 + k * 0.2) * (4 + k * 1.1); j ? g.lineTo(cx + Math.cos(a) * r, cy + Math.sin(a) * r * 0.92) : g.moveTo(cx + Math.cos(a) * r, cy + Math.sin(a) * r * 0.92); }
      g.closePath(); g.fillStyle = colAt(k); g.fill(); g.strokeStyle = '#1a0a24'; g.lineWidth = 3.4; g.stroke();
    }
    g.fillStyle = '#1a0a24'; g.beginPath(); g.arc(cx, cy, 16, 0, TAU); g.fill();
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Psychedelic_art>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
