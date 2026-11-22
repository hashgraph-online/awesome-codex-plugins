# Kinetic typography

Also called: motion typography.

Family: Type, data and retro. Cadence: smooth, full frame rate. Usual tool: HyperFrames (DOM).

Moving words as the whole picture: scale, weight and timing carry the meaning.

Saul Bass's title sequences for North by Northwest (1959) and Psycho (1960) made it a form.

## What makes it read as this

- Type is the image; nothing competes with it
- Strong contrast of size and weight
- Words arrive in reading order, on the beat
- One idea per frame

## Timing

Each word lands in 0.3 to 0.5 seconds with a small overshoot, then the line holds long enough to read.

## How to build it

- HyperFrames: split text into inline-block spans and stagger with GSAP
- Canvas: `fillText` with a transform per word
- Timing from the narration: one start time per word
- Hold for (words / 3) + 0.5 seconds before the next line

## Assets

A typeface with enough weights. No pictures. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Cut to the voice or the beat. Practice note.

## What makes it look wrong

- Words faster than they can be read
- Effects that add no meaning
- Everything moving at once

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=kinetic-type` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'kinetic-type': { kind: '2d', fps: null, draw(g, t, W, H) {
    // the words are the picture: each one lands with an overshoot, in reading order, then the line holds still
    bg(g, W, H, '#101319'); g.textAlign = 'center'; g.textBaseline = 'middle';
    const words = [['MAKE', '#f4f1ea', 0.15, H * 0.3, 118], ['IT', '#ff5a1f', 0.6, H * 0.52, 150], ['MOVE.', '#f4f1ea', 1.05, H * 0.76, 118]];
    for (const [w, col, start, y, size] of words) {
      const k = prog(t, start, 0.5); if (k <= 0) continue; const s = overshoot(k);
      g.save(); g.translate(W / 2, y + (1 - easeOut(k)) * 40); g.scale(s, s); g.globalAlpha = clamp(k * 3); g.fillStyle = col; g.font = `900 ${size}px ${FONT}`; g.fillText(w, 0, 0); g.restore();
    }
    const u = easeOut(prog(t, 1.7, 0.5)); g.fillStyle = '#ff5a1f'; g.fillRect(W / 2 - 190 * u, H * 0.9, 380 * u, 8);
    g.textAlign = 'left'; g.textBaseline = 'alphabetic';
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Kinetic_typography>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
