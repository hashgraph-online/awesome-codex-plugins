# Pixel art

Also called: 8-bit.

Family: Geometry, pixels and 3D. Cadence: steps 8 times a second. Usual tool: HyperFrames (canvas).

A tiny picture placed pixel by pixel and scaled up with hard edges: a few colours, no blur, sprites that step.

From early video games; the term dates from 1982.

## What makes it read as this

- A small canvas scaled by a whole number
- A limited palette, often 8 to 32 colours
- No anti-aliasing, no soft gradients
- Sprites animate in a few frames

## Timing

Walk cycles of 4 to 8 frames at about 8 a second. Scrolling moves in whole pixels.

## How to build it

- Draw on a small canvas (160 by 90), then `drawImage` it up with `imageSmoothingEnabled = false`
- CSS: `image-rendering: pixelated` on an upscaled canvas
- Sprites as arrays of palette indexes
- Three.js: `RenderPixelatedPass` renders a 3D scene to low resolution with nearest filtering

## Assets

Sprites as data in code, or drawn in a pixel editor. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Chiptune. Practice note.

## What makes it look wrong

- Scaling by a fraction
- Mixed pixel sizes on one screen
- Smooth vector edges or too many colours

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=pixel-art` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of that file. Take the technique, not the picture.

```js
  'pixel-art': { kind: '2d', fps: 8, draw(g, t, W, H) {
    // drawn on a 160 x 90 canvas with a six-colour palette, then scaled up six times with no smoothing. The walk cycle has four frames.
    const lw = 160, lh = 90, c = new OffscreenCanvas(lw, lh), p = c.getContext('2d'), f = frameOf(t, 8), PAL = ['#1b1f3b', '#3b4a8c', '#f4d35e', '#ee6c4d', '#f7f3e8', '#2e7d5b'];
    p.fillStyle = PAL[1]; p.fillRect(0, 0, lw, lh); p.fillStyle = PAL[0]; p.fillRect(0, 62, lw, 28);
    for (let i = 0; i < 26; i++) { p.fillStyle = PAL[4]; if (hash(i, 3) > 0.5 || f % 4 !== i % 4) p.fillRect((hash(i) * lw) | 0, (hash(i, 1) * 44) | 0, 1, 1); }
    p.fillStyle = PAL[2]; p.fillRect(124, 10, 12, 12);
    for (let x = 0; x < lw; x += 8) { p.fillStyle = PAL[5]; p.fillRect(((x - f * 2) % lw + lw) % lw, 62, 4, 2); }   // the ground scrolls two pixels a frame
    const SPR = ['..3333..', '.333333.', '.34343..', '.344443.', '..2222..', '.222222.', '.2.22.2.', '..1..1..'], legs = [['..1..1..', '.11..11.'], ['..11.1..', '..1..11.'], ['..1..1..', '.11..11.'], ['..1.11..', '.11..1..']][f % 4];
    const rows = [...SPR.slice(0, 7), ...legs], bx = 72, by = 62 - rows.length * 2 - (f % 2);
    rows.forEach((row, y) => [...row].forEach((ch, x) => { if (ch !== '.') { p.fillStyle = PAL[+ch]; p.fillRect(bx + x * 2, by + y * 2, 2, 2); } }));
    g.imageSmoothingEnabled = false; g.globalCompositeOperation = 'source-over'; g.drawImage(c, 0, 0, W, H); g.imageSmoothingEnabled = true;
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Pixel_art>
- <https://developer.mozilla.org/en-US/docs/Web/CSS/image-rendering>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
