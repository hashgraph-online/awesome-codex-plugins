# Ink wash (sumi-e)

Also called: sumi-e, ink painting.

Family: Drawn and painted. Cadence: steps 12 times a second. Usual tool: HyperFrames (canvas or SVG).

Black ink in every shade from deep black to pale grey, laid down in tapered brush strokes on rice paper, with a great deal left empty.

Chinese ink wash painting from the Tang dynasty, carried to Japan by Zen monks. Shanghai Animation Film Studio made ink-wash films from 1960.

## What makes it read as this

- One ink, many dilutions
- Strokes that taper from thick to a point
- Empty paper as part of the picture
- One small red seal
- Soft grey washes behind sharp strokes

## Timing

Slow and fluid. A stroke accelerates and lifts. On twos.

## How to build it

- A stroke is a row of overlapping dots whose radius tapers along its length, drawn up to a fraction
- Vary each dot's opacity with a seeded hash for a dry-brush break
- Washes: soft radial gradients with `multiply`
- SVG route: variable-width filled paths revealed by a mask

## Assets

Procedural. Rice-paper grain. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Sparse: flute, single plucked notes, silence. Practice note.

## What makes it look wrong

- Pure black on pure white
- Uniform stroke width
- Filling the frame

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=ink-wash` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'ink-wash': { kind: '2d', fps: 12, draw(g, t, W, H) {
    // bamboo in ink: tapered strokes laid down segment by segment, grey washes, a red seal, a lot of empty paper
    const ts = onTwos(t);
    bg(g, W, H, '#f2ecdd');
    const stroke = (x0, y0, x1, y1, w0, w1, k, alpha = 0.92) => { const n = 60; for (let i = 0; i <= n * clamp(k); i++) { const e = i / n, r = lerp(w0, w1, e) * (0.85 + 0.3 * hash(i, x0 | 0)); g.fillStyle = `rgba(22,22,24,${alpha * (0.55 + 0.45 * hash(i, y0 | 0))})`; g.beginPath(); g.arc(lerp(x0, x1, e), lerp(y0, y1, e) + Math.sin(e * 3) * 3, r, 0, TAU); g.fill(); } };
    for (let s = 0; s < 4; s++) stroke(W * 0.3 + s * 3, H * 0.96 - s * 118, W * 0.3 + (s + 1) * 3, H * 0.96 - (s + 1) * 118 + 8, 13 - s, 12 - s, prog(ts, 0.1 + s * 0.3, 0.3));
    const leaf = (x, y, a, l, start) => stroke(x, y, x + Math.cos(a) * l, y + Math.sin(a) * l, 9, 0.6, easeOut(prog(ts, start, 0.3)), 0.85);
    leaf(W * 0.31, H * 0.5, -0.3, 150, 1.4); leaf(W * 0.31, H * 0.5, 0.25, 130, 1.6); leaf(W * 0.31, H * 0.3, -0.7, 120, 1.8); leaf(W * 0.31, H * 0.3, -0.05, 160, 2.0);
    g.globalCompositeOperation = 'multiply'; const m = g.createRadialGradient(W * 0.7, H * 0.72, 10, W * 0.7, H * 0.72, 220); m.addColorStop(0, `rgba(60,62,66,${0.35 * prog(ts, 0.4, 1.5)})`); m.addColorStop(1, 'rgba(60,62,66,0)'); g.fillStyle = m; g.fillRect(0, 0, W, H); g.globalCompositeOperation = 'source-over';
    const k = prog(ts, 2.3, 0.2); if (k > 0) { g.fillStyle = '#b3261e'; g.fillRect(W * 0.82, H * 0.74, 38 * k, 38); }
    paper(g, W, H, 15, 22);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Ink_wash_painting>
- <https://en.wikipedia.org/wiki/Shanghai_Animation_Film_Studio>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
