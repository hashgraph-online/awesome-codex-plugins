# VHS and glitch

Also called: glitch, retro VHS.

Family: Type, data and retro. Cadence: steps 30 times a second. Usual tool: HyperFrames (canvas) or Three.js post-processing.

The damage of old tape and broken data: colour that bleeds sideways, scan lines, a band of noise at the bottom, sudden torn slices.

VHS records colour at far lower resolution than brightness, which is why colour smears. Glitch art uses such errors on purpose.

## What makes it read as this

- Colour offset from brightness by a few pixels and softer
- Scan lines
- A tracking band of noise near the bottom
- A date stamp in a blocky face
- Glitch: slices displaced sideways, in short bursts

## Timing

Full frame rate, with bursts of a fifth of a second. Seeds come from the frame number so every render matches.

## How to build it

- Draw the clean frame to its own canvas first, then the damage on top
- Redraw it in thin horizontal strips with a per-strip offset; large offsets only during a burst
- Chroma bleed: a blurred copy drawn again a few pixels to the side with `screen`
- Scan lines: a dark row every third pixel
- Three.js: `FilmPass`, `RGBShiftShader` and `GlitchPass` exist; `GlitchPass` picks its own random timing, so check it repeats before relying on it

## Assets

All in code. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Tape hiss, hum, a click on each burst. Practice note.

## What makes it look wrong

- Constant glitching, which tires the eye
- Glitching text the viewer has to read
- Unseeded randomness, so two renders differ

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=vhs-glitch` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of that file. Take the technique, not the picture.

```js
  'vhs-glitch': { kind: '2d', fps: 30, draw(g, t, W, H) {
    // a clean frame first, then the damage on top: colour that bleeds sideways, scan lines, a tracking band, a seeded burst
    const f = frameOf(t, 30), c = new OffscreenCanvas(W, H), s = c.getContext('2d');
    s.fillStyle = '#0b1020'; s.fillRect(0, 0, W, H);
    ['#c0c0c0', '#c0c000', '#00c0c0', '#00c000', '#c000c0', '#c00000', '#0000c0'].forEach((col, i) => { s.fillStyle = col; s.fillRect(i * W / 7, H * 0.52, W / 7 + 1, H * 0.3); });
    s.fillStyle = '#fff'; s.font = `800 96px ${FONT}`; s.fillText('PLAY ▶', 60, 170); s.font = `600 34px ui-monospace, Menlo, monospace`; s.fillText('SP   0:00:' + String(Math.floor(t)).padStart(2, '0'), 60, H - 44); s.fillText('NOV 18 1994', W - 300, H - 44);
    bg(g, W, H, '#000');
    const burst = hash(Math.floor(f / 6), 5) < 0.22;                         // roughly one burst in five, 0.2 s long, the same every render
    for (let y = 0; y < H; y += 6) { const shift = (burst && hash(f, y) < 0.3 ? jit(f, y, 46) : 0) + Math.sin(y * 0.05 + f * 0.4) * 1.5; g.drawImage(c, 0, y, W, 6, shift, y, W, 6); }
    g.globalCompositeOperation = 'screen'; g.globalAlpha = 0.5; g.filter = 'blur(2px)'; g.drawImage(c, 7, 0); g.filter = 'none'; g.globalAlpha = 1;   // chroma is softer than brightness and sits a few pixels off
    g.globalCompositeOperation = 'source-over'; g.fillStyle = 'rgba(0,0,0,.22)'; for (let y = 0; y < H; y += 3) g.fillRect(0, y, W, 1);
    const band = H - 46 + Math.sin(f * 0.3) * 6; for (let i = 0; i < 260; i++) { g.fillStyle = `rgba(255,255,255,${hash(f, i) * 0.8})`; g.fillRect(hash(f, i, 1) * W, band + hash(f, i, 2) * 34, 4 + hash(f, i, 3) * 60, 2); }
    g.globalAlpha = 0.5; g.drawImage(grain(W, H, 30 + (f % 6), 40, [255, 255, 255]), 0, 0); g.globalAlpha = 1;
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/VHS>
- <https://en.wikipedia.org/wiki/Glitch_art>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
