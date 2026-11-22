# ASCII art

Also called: ascii, text art.

Family: Screens and cinema. Cadence: steps 12 times a second. Usual tool: HyperFrames (canvas).

A scene drawn only from monospaced text characters chosen by brightness: a sunrise over a sea and a headland, with waves, glitter and birds that move.

ASCII art is a graphic design technique of pictures pieced together from the 95 printable characters of the ASCII standard of 1963. Among the oldest examples are works by Kenneth Knowlton from around 1966, and it was invented in large part because early printers lacked graphics ability.

## What makes it read as this

- Only characters from one monospaced font: no lines, no shapes
- Brightness maps to a ramp of characters from sparse to dense: space, dot, colon, plus, hash, at-sign
- A tight grid: about 120 columns and 45 rows
- One or two colours on a near-black ground, brighter for denser characters
- Motion comes from the character values changing, not from moving glyphs

## Timing

The picture is recomputed 12 times a second; waves and glitter change on each step.

## How to build it

- Choose a grid (`cols`, `rows`) and compute a brightness function `lum(u, v, t)` for each cell
- Map brightness to a ramp: `RAMP[Math.floor(L * (RAMP.length - 0.01))]`
- Draw a row as a few strings, one per brightness bucket, with spaces where another bucket has the character, so that monospace alignment holds and a row costs a few `fillText` calls
- Scale horizontally so that the columns fill the frame
- For a real image, sample a downscaled copy of it instead of the function

## Assets

All in code. For video, sample frames and map their luminance. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A dial-up modem, key clicks, a slow arpeggio. Practice note.

## What makes it look wrong

- A proportional font: the grid breaks
- Too few columns: the picture does not read
- Too much contrast between neighbouring characters

## Tested demo

This is the look from `art-forms/looks-screen.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=ascii` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  ascii: { kind: '2d', fps: 12, draw(g, t, W, H) {
    // a sunrise over a sea and a headland, drawn only from big monospaced characters picked by brightness from " .:-=+*#%@", in a colour per region: a violet-to-orange sky, a golden sun, a brown headland, a blue sea with glitter
    const ts = held(t, 12), cols = 96, rows = 34, RAMP = ' .:-=+*#%@'; g.fillStyle = '#080508'; g.fillRect(0, 0, W, H); g.font = '17px "Courier New", Courier, monospace'; g.textBaseline = 'top';
    const cw = g.measureText('M').width, sx = W / (cols * cw), rh = H / rows;
    const PAL = { sky: ['#5a4a9a', '#8a5aa8', '#c86aa0', '#ff8f6a', '#ffd9a0'], sun: ['#ffb347', '#ffc65a', '#ffd97a', '#fff0a8', '#ffffff'], land: ['#6a4a2a', '#8a5e34', '#a8743c', '#c88a48', '#e0a45a'], sea: ['#2a5fd0', '#3f86e0', '#6aa8ff', '#a8d0ff', '#e6f4ff'] };
    const cell = (u, v) => {
      const dx = (u - 0.64) * 1.78, dy = v - (0.4 - 0.015 * Math.sin(ts)), d = Math.hypot(dx, dy), ridge = 0.52 - 0.1 * vnoise(u * 6, 0, 3) - 0.05 * Math.abs(Math.sin(u * 7));
      if (v >= 0.64) { const k = v - 0.64; let L = 0.14 + 0.28 * Math.max(0, Math.sin(u * 40 + ts * 3.2 + k * 60)) ** 1.5; if (Math.abs(u - 0.64) < 0.05 + k * 0.45) L += 0.6 * Math.max(0, Math.sin(k * 110 + ts * 5)) ** 2 * (1 - k * 2.2); return [clamp(L), 'sea']; }
      if (d < 0.19) return [clamp(0.62 + 0.38 * (1 - d / 0.19)), 'sun'];
      if (u < 0.4 && v > ridge) return [0.46 + 0.3 * vnoise(u * 40, v * 40, 5), 'land'];
      return [clamp(0.04 + 0.3 * Math.max(0, 0.64 - v) ** 1.4 + 0.65 * Math.exp(-d * 5) + (v > 0.18 && v < 0.28 && Math.sin(u * 20 + ts * 0.5 + v * 30) > 0.8 ? 0.22 : 0)), 'sky'];
    };
    g.save(); g.scale(sx, 1);
    for (let r = 0; r < rows; r++) { const rowsTxt = {}; for (let c = 0; c < cols; c++) { const [L, cls] = cell(c / cols, r / rows), ch = RAMP[Math.floor(L * 9.99)]; if (ch === ' ') continue; const b = Math.min(4, Math.floor(L * 5)), key = cls + b; (rowsTxt[key] = rowsTxt[key] || { cls, b, s: Array(cols).fill(' ') }).s[c] = ch; } for (const k of Object.keys(rowsTxt)) { const o = rowsTxt[k]; g.fillStyle = PAL[o.cls][o.b]; g.fillText(o.s.join(''), 0, r * rh); } }
    for (let i = 0; i < 4; i++) { const bx = (ts * 7 + i * 24) % cols, by = 5 + i * 2 + Math.round(Math.sin(ts * 2 + i)); g.fillStyle = '#ffe9c0'; g.fillText(Math.floor(ts * 4 + i) % 2 ? 'v' : '^', bx * cw, by * rh); }
    g.restore(); scanlines(g, W, H, 0.08, 4);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/ASCII_art>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
