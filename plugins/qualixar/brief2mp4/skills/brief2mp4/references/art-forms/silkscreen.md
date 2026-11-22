# Silkscreen poster

Also called: silkscreen, screen print, screen printing, serigraph.

Family: Folk and print traditions. Cadence: steps 8 times a second. Usual tool: HyperFrames (canvas).

A poster printed in a few flat inks that overprint, each a little out of register, with coarse halftone dots for tone: flat shapes, big blocks, and colours that mix where they overlap.

Screen printing, also silkscreening or serigraphy, transfers ink through a mesh onto a surface except where a stencil blocks it; traditionally the mesh was silk. It is widely used for posters and other graphics.

## What makes it read as this

- Two to four flat inks, never more
- Inks overprint with multiply, so overlaps make new colours
- Each ink is a little off register, differently on each drawing
- Halftone dots at an angle for gradients and glows
- Bold flat shapes and block bars where type would go
- Paper grain showing through

## Timing

Each ink prints in turn, sliding into register over about 0.7 seconds, one every second. The picture steps about 8 times a second and each step re-seeds the misregistration.

## How to build it

- One draw function per ink, drawn with `globalCompositeOperation = 'multiply'` (`inkLayer()` in `looks-folk.js`)
- Offset each layer by a few pixels plus a seeded jitter keyed to `frameOf(t, 8)`
- Halftone: a rotated grid of dots whose radius is `pitch * 0.72 * sqrt(value)` (`halftone()`)
- Slide each layer in from off-register and settle it at its offset

## Assets

All in code. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A press clunk and a squeegee sweep as each ink lands, an upbeat drum loop. Practice note.

## What makes it look wrong

- Perfect register and soft gradients: that reads as digital
- Too many colours
- Transparency that does not multiply

## Tested demo

This is the look from `art-forms/looks-folk.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=silkscreen` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  silkscreen: { kind: '2d', fps: 8, draw(g, t, W, H) {
    // a poster in three flat inks that overprint: yellow, red and blue, each a little out of register, with halftone dots for the sky and the glow
    const ts = held(t, 8), f = frameOf(t, 8); bg(g, W, H, '#f3ecd9');
    inkLayer(g, '#f7c600', 0.2, ts, f, [0, 0, 0, -40], () => { g.beginPath(); g.arc(480, 250, 132, 0, TAU); g.fill(); halftone(g, [0, 0, W, 300], 9, 0.26, (x, y) => (y / 300) * 0.95); });
    inkLayer(g, '#e5314f', 1.2, ts, f, [4, -3, -40, 0], () => { halftone(g, [250, 70, 710, 430], 8, 0.78, (x, y) => { const d = Math.hypot(x - 480, y - 250); return d < 140 ? 0 : 1 - (d - 140) / 70; }); polyFill(g, [[0, 440], [0, 250], [150, 170], [310, 340], [400, 440]]); g.fillRect(0, H - 58, W, 16); });
    inkLayer(g, '#1d3b8f', 2.2, ts, f, [-3, 4, 40, 0], () => {
      polyFill(g, [[300, H], [560, 300], [700, 236], [960, 372], [960, H]]); for (const [x, y, w] of [[50, 60, 210], [50, 86, 140], [50, 112, 180]]) g.fillRect(x, y, w, 15);
      g.lineWidth = 7; g.lineCap = 'round'; g.strokeStyle = '#1d3b8f'; for (const [bx, by, sc] of [[700, 120, 1], [770, 90, 0.6], [640, 70, 0.5]]) { g.beginPath(); g.moveTo(bx - 40 * sc, by + 14 * sc); g.quadraticCurveTo(bx - 18 * sc, by - 18 * sc, bx, by + 4 * sc); g.quadraticCurveTo(bx + 18 * sc, by - 18 * sc, bx + 40 * sc, by + 14 * sc); g.stroke(); }
    });
    speckle(g, W, H, 7, 70, [90, 70, 40]);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Screen_printing>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
