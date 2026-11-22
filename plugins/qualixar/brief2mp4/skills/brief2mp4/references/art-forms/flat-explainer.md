# 2D flat vector explainer

Also called: motion graphics explainer.

Family: Drawn and painted. Cadence: smooth, full frame rate. Usual tool: HyperFrames (DOM, SVG).

The plain explainer look: flat fills, a few colours, simple shapes and icons, smooth eased motion.

Flat design comes from Swiss style and modernism; in animation its ancestor is the stylised, limited look of the UPA studio.

## What makes it read as this

- Flat fills, three to five colours, one accent
- Geometric shapes with one stroke width
- Plenty of space; one idea per frame
- Clean sans type

## Timing

Smooth ease-out moves of 0.4 to 0.8 seconds, staggered, with holds long enough to read.

## How to build it

- HTML or SVG with GSAP: this is what HyperFrames is best at
- Stagger related items 0.15 to 0.25 seconds apart
- Draw check marks and connectors on with `stroke-dashoffset`
- Move a highlight instead of cutting

## Assets

All in code. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Soft interface blips, a light bed, voice-led pacing. Practice note.

## What makes it look wrong

- A grid of identical cards
- Gradients and shadows creeping in
- Too much on screen at once

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=flat-explainer` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'flat-explainer': { kind: '2d', fps: null, draw(g, t, W, H) {
    // the explainer look: flat fills, one accent, smooth ease-out moves, a stagger, and a hold at the end
    bg(g, W, H, '#f5f7fb');
    const labels = ['Brief', 'Build', 'Check'];
    for (let i = 0; i < 3; i++) {
      const k = easeOut(prog(t, 0.2 + i * 0.22, 0.6)), x = W * (0.22 + i * 0.28), y = lerp(H * 0.62, H * 0.46, k);
      g.globalAlpha = k; g.fillStyle = i === 2 ? '#ff5a1f' : '#1f2a44'; g.beginPath(); g.roundRect(x - 92, y - 62, 184, 124, 22); g.fill();
      g.fillStyle = '#fff'; g.font = `700 30px ${FONT}`; g.textAlign = 'center'; g.fillText(labels[i], x, y + 10);
      if (i < 2) { const a = easeOut(prog(t, 0.9 + i * 0.25, 0.4)); g.globalAlpha = a; g.strokeStyle = '#1f2a44'; g.lineWidth = 5; g.lineCap = 'round'; g.beginPath(); g.moveTo(x + 104, H * 0.46); g.lineTo(x + 104 + 60 * a, H * 0.46); g.stroke(); }
    }
    g.globalAlpha = 1; g.textAlign = 'left';
    const c = prog(t, 1.7, 0.45); g.strokeStyle = '#fff'; g.lineWidth = 9; g.lineCap = 'round'; g.lineJoin = 'round';
    strokePart(g, [[W * 0.78 - 22, H * 0.46 - 44], [W * 0.78 - 8, H * 0.46 - 30], [W * 0.78 + 22, H * 0.46 - 60]], easeOut(c));
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Flat_design>
- <https://en.wikipedia.org/wiki/United_Productions_of_America>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
