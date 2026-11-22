# Risograph and halftone print

Also called: riso, halftone print.

Family: Craft and handmade. Cadence: steps 8 times a second. Usual tool: HyperFrames (canvas or DOM).

The look of a cheap stencil print: two to four bright inks laid over each other, visible grain, dot screens, and layers that never quite line up.

The Risograph duplicator dates from 1980: one ink per drum, so each colour is a separate pass. Halftone dots go back to the 1860s.

## What makes it read as this

- Two to four spot colours, often pink, blue and yellow
- Inks overprint to make new colours (multiply)
- Each layer sits a pixel or two off register
- Grain and dot screens; no smooth gradients
- Off-white paper

## Timing

Print is still. Animate by re-rolling the misregistration and swapping the grain 8 to 12 times a second.

## How to build it

- Each ink is its own layer drawn with `mix-blend-mode: multiply` (canvas: `globalCompositeOperation`)
- Offset each layer by a seeded amount per drawing: `jit(frameOf(t, 8), layer, 3)`
- Tone as dots: a staggered grid of circles whose radius follows the tone
- Grain: several pre-made noise tiles, cycled by frame number
- Three.js `HalftonePass` exists for 3D scenes; SVG `feColorMatrix` separates a photo into one ink

## Assets

All procedural. A chunky sans or slab typeface. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Lo-fi, tape hiss. Practice note.

## What makes it look wrong

- Gradients
- Perfect registration
- More than four colours

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=risograph` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  risograph: { kind: '2d', fps: 8, draw(g, t, W, H) {
    // three ink layers printed with multiply. Each layer slips a pixel or two per frame (misregistration), with grain on top.
    const f = frameOf(t, 8);
    bg(g, W, H, '#f4efe2'); g.globalCompositeOperation = 'multiply';
    const off = (i) => [jit(f, i, 3), jit(f, i + 10, 3)];
    let [x, y] = off(1); g.fillStyle = '#ff48a0'; g.beginPath(); g.arc(W * 0.42 + x, H * 0.48 + y, 150, 0, TAU); g.fill();
    [x, y] = off(2); g.fillStyle = '#2a5cff'; g.beginPath(); g.moveTo(W * 0.5 + x, H * 0.2 + y); g.lineTo(W * 0.78 + x, H * 0.76 + y); g.lineTo(W * 0.3 + x, H * 0.76 + y); g.closePath(); g.fill();
    [x, y] = off(3); g.fillStyle = '#ffd400';                              // the yellow layer is a halftone: dots that grow left to right
    for (let py = H * 0.2; py < H * 0.82; py += 12) for (let px = W * 0.5; px < W * 0.86; px += 12) { g.beginPath(); g.arc(px + x + ((py / 12) % 2 | 0) * 6, py + y, 0.8 + 5 * ((px - W * 0.5) / (W * 0.36)), 0, TAU); g.fill(); }
    g.drawImage(grain(W, H, 10 + (f % 4), 46, [30, 30, 40]), 0, 0); g.globalCompositeOperation = 'source-over';
    g.fillStyle = '#2a5cff'; g.font = `800 34px ${FONT}`; g.fillText('3 INKS', 40, H - 40);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Risograph>
- <https://en.wikipedia.org/wiki/Halftone>
- <https://developer.mozilla.org/en-US/docs/Web/CSS/mix-blend-mode>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
