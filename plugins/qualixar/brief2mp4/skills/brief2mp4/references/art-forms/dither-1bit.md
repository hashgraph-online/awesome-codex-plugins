# 1-bit dither

Also called: dithering, bayer dither, one bit.

Family: Screens and cinema. Cadence: steps 12 times a second. Usual tool: HyperFrames (canvas), or a Three.js post-process.

Two colours only, ink and paper: gradients and shaded forms turned into patterns of pure dots, in a window with a striped title bar, like an early desktop computer.

Ordered dithering applies a preset threshold map tiled across an image to display a continuous image with fewer colours; with the common Bayer map it leaves noticeable crosshatch patterns. A common use of dither is converting a grayscale image to black and white so that the density of black dots approximates the grey level.

## What makes it read as this

- Exactly two colours: near-black ink and warm paper white
- Grey is made only from the density of dots, in a regular crosshatch pattern
- Hard, unsmoothed pixels, scaled up by whole numbers
- Title bars with ruled stripes and square widgets
- No anti-aliasing and no half-tones

## Timing

Drawn on twos, 12 changes a second.

## How to build it

- Render a small buffer (480 by 270), compute a grey `L` for each pixel, and set it to ink or paper by `L > bayer(x, y)` (`bayer()` in `looks-screen.js`)
- Draw the buffer scaled by 2 with `imageSmoothingEnabled = false`
- Draw the window chrome after the dither, in pure ink and paper with square corners
- Real route: a `ShaderPass` that thresholds against an 8 by 8 Bayer matrix

## Assets

All in code. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A beeper, a floppy-drive whirr, simple square-wave notes. Practice note.

## What makes it look wrong

- Grey or colour anywhere
- Error-diffusion noise instead of an ordered pattern
- Smooth scaling that blurs the dots

## Tested demo

This is the look from `art-forms/looks-screen.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=dither-1bit` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'dither-1bit': { kind: '2d', fps: 12, draw(g, t, W, H) {
    // two colours only, ink and paper: a gradient sky and a bouncing ball turned into pure dots by an ordered dither, inside a window with a striped title bar, like an early desktop computer
    const ts = held(t, 12), w = 480, h = 270, img = new ImageData(w, h), INKc = [17, 17, 17], PAP = [241, 239, 228], by = 152 - Math.abs(Math.sin(ts * 2.6)) * 62, bx = 240 + Math.sin(ts * 1.3) * 90, R = 52, Lg = [-0.5, -0.6, 0.62];
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      let L = y < 170 ? 0.12 + 0.8 * (y / 170) ** 1.3 : 0.3 + 0.35 * ((y - 170) / 100); const dx = (x - bx) / R, dy = (y - by) / R, r2 = dx * dx + dy * dy;
      if (y >= 170) { const sd = ((x - bx - 24) / (R * 1.5)) ** 2 + ((y - 214) / 12) ** 2; if (sd < 1) L *= 0.35; if (((x >> 5) + ((y - 170) >> 3)) % 2 === 0) L += 0.07; }
      if (r2 < 1) { const nz = Math.sqrt(1 - r2); L = clamp(0.12 + 0.95 * Math.max(0, dx * Lg[0] + dy * Lg[1] + nz * Lg[2])); }
      const c = L > bayer(x, y) ? PAP : INKc, i = (y * w + x) * 4; img.data[i] = c[0]; img.data[i + 1] = c[1]; img.data[i + 2] = c[2]; img.data[i + 3] = 255;
    }
    const sc = new OffscreenCanvas(w, h); sc.getContext('2d').putImageData(img, 0, 0); g.fillStyle = '#f1efe4'; g.fillRect(0, 0, W, H); g.save(); g.imageSmoothingEnabled = false; g.drawImage(sc, 0, 0, w, h, 0, 0, W, H); g.restore();
    g.fillStyle = '#f1efe4'; g.fillRect(0, 0, W, 34); g.fillStyle = '#111'; g.fillRect(0, 34, W, 3); for (let y = 8; y < 28; y += 4) g.fillRect(70, y, W - 140, 2); g.fillStyle = '#f1efe4'; g.fillRect(W / 2 - 80, 4, 160, 26); g.fillStyle = '#111'; g.font = `700 16px ${FONT}`; g.textAlign = 'center'; g.fillText('One bit', W / 2, 23); g.textAlign = 'left'; g.fillRect(12, 8, 18, 18); g.fillStyle = '#f1efe4'; g.fillRect(15, 11, 12, 12);
    g.strokeStyle = '#111'; g.lineWidth = 6; g.strokeRect(3, 3, W - 6, H - 6);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Ordered_dithering>
- <https://en.wikipedia.org/wiki/Dither>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
