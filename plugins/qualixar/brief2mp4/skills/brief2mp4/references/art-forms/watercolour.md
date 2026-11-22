# Watercolour

Also called: watercolor.

Family: Drawn and painted. Cadence: steps 12 times a second. Usual tool: HyperFrames (canvas or SVG).

Transparent washes on textured paper: colour that spreads, pools darker at its edge, and lets the paper show through.

Pigment in water on paper. Wet-on-wet blends softly; wet-on-dry gives crisp edges.

Sourcing note: The edge-darkening rule is a practice note; the technique sources cover the filter, not the look.

## What makes it read as this

- Transparent colour; overlaps make new colours
- Darker pigment at the edge of each wash
- Irregular, soft outlines
- Paper grain visible everywhere
- Unpainted paper as the highlight

## Timing

Slow. A wash grows over 1 to 3 seconds with an ease-out. Hold drawings at 12 a second for a hand-painted feel.

## How to build it

- Each wash: an irregular closed outline, clipped, filled with a radial gradient that is darkest near the rim
- Layer washes with `multiply`
- Paper grain over everything with `multiply`
- SVG route: low-frequency `feTurbulence` (0.01 to 0.03) into `feDisplacementMap` (scale 10 to 25) for bleeding edges
- 3D: a Kuwahara filter as a custom pass gives a painterly result; three.js ships none

## Assets

Procedural. A scanned paper texture improves close-ups. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Slow, gentle, acoustic. Practice note.

## What makes it look wrong

- Opaque flat colour
- A uniform blur, which looks out of focus, not painted
- No paper texture

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=watercolour` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  watercolour: { kind: '2d', fps: 12, draw(g, t, W, H) {
    // transparent washes that spread, with pigment pooling at the edge and paper showing through
    const ts = onTwos(t);
    bg(g, W, H, '#f6f1e6'); g.globalCompositeOperation = 'multiply';
    const wash = (x, y, r, rgb, seed, start) => {
      const k = easeOut(prog(ts, start, 1.6)); if (k <= 0) return; const rr = r * (0.35 + 0.65 * k);
      g.save(); blob(g, x, y, rr, seed, 0.16); g.clip();
      const grad = g.createRadialGradient(x, y, rr * 0.1, x, y, rr * 1.12);
      grad.addColorStop(0, `rgba(${rgb},${0.28 * k})`); grad.addColorStop(0.72, `rgba(${rgb},${0.42 * k})`); grad.addColorStop(0.93, `rgba(${rgb},${0.8 * k})`); grad.addColorStop(1, `rgba(${rgb},${0.3 * k})`);
      g.fillStyle = grad; g.fillRect(x - rr * 1.3, y - rr * 1.3, rr * 2.6, rr * 2.6); g.restore();
    };
    wash(W * 0.36, H * 0.5, 170, '52,110,170', 51, 0.1);
    wash(W * 0.58, H * 0.44, 150, '214,84,96', 52, 0.6);
    wash(W * 0.5, H * 0.66, 120, '232,178,60', 53, 1.1);
    g.drawImage(grain(W, H, 14, 44, [70, 55, 40]), 0, 0); g.globalCompositeOperation = 'source-over';
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Watercolor_painting>
- <https://blog.maximeheckel.com/posts/on-crafting-painterly-shaders>
- <https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/feTurbulence>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
