# Brick toy

Also called: toy brick, plastic brick, building brick, brick built.

Family: Craft and handmade. Cadence: steps 12 times a second. Usual tool: HyperFrames (canvas), Blender for glossy plastic.

Everything built from studded plastic bricks on a green baseplate: visible studs, a glossy edge, flat bright colours, and bricks that drop in one at a time on twos.

Brick toys are a kind of construction set: a standardised assortment of pieces for building models, most often marketed as toys.

Sourcing note: The source describes construction sets in general. Brand names appear only in the router keywords, so that the router understands a request; they are never used in a name, a rule or a picture.

## What makes it read as this

- Every object is made of rectangular bricks on a stud grid
- A baseplate with a stud on every cell
- Flat, bright primary colours with a lighter top and darker sides
- A bright edge and a glossy highlight on the studs
- Models built layer by layer, brick by brick

## Timing

Bricks drop in one at a time over about 4 seconds, each falling about six layers and settling. Drawn on twos, 12 changes a second.

## How to build it

- An isometric projection: `sx = cx + (x - y) * cw`, `sy = cy + (x + y) * ch - z * bh` (`iso()` in `looks-toon.js`)
- Each brick: a top and two sides in three shades of one colour, then a stud on each cell (`brick()`, `stud()`)
- Sort bricks by `x + y` then by height so that nearer bricks cover farther ones
- Drop each brick with `easeOut` from above and fade it in

## Assets

All in code. No logos, no brand names, no printed lettering on the studs. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Click and clack of plastic, a cheerful ukulele bed. Practice note.

## What makes it look wrong

- Smooth sloped surfaces: only bricks and plates
- No studs
- Any brand name or logo

## Tested demo

This is the look from `art-forms/looks-toon.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=brick-toy` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'brick-toy': { kind: '2d', fps: 12, draw(g, t, W, H) {
    // everything built from studded plastic bricks on a baseplate: bricks drop in one at a time, each with its studs, a bright edge and a glossy highlight, drawn on twos
    const ts = held(t, 12), sky = g.createLinearGradient(0, 0, 0, H); sky.addColorStop(0, '#dbe9fb'); sky.addColorStop(1, '#f6f9ff'); g.fillStyle = sky; g.fillRect(0, 0, W, H); g.lineJoin = 'round';
    const base = [iso(0, 0, 0), iso(12, 0, 0), iso(12, 10, 0), iso(0, 10, 0)];
    polyFill(g, [iso(0, 10, 0), iso(12, 10, 0), iso(12, 10, -0.35), iso(0, 10, -0.35)], '#1f7a3c', 'rgba(0,0,0,.35)', 1.2); polyFill(g, [iso(12, 0, 0), iso(12, 10, 0), iso(12, 10, -0.35), iso(12, 0, -0.35)], '#17602f', 'rgba(0,0,0,.35)', 1.2); polyFill(g, base, '#2e9b4f', 'rgba(0,0,0,.35)', 1.2);
    for (let i = 0; i < 12; i++) for (let j = 0; j < 10; j++) stud(g, i + 0.5, j + 0.5, 0, '#2e9b4f', 0.4);
    const WH = '#f4f1ea', CR = '#f2d9a0', RD = '#d6342a', BL = '#2f6fdf', YL = '#f5c518', BR = '#7a4a22', GR = '#2e9b4f', DK = '#2a2a33', list = [];
    for (let z = 0; z < 4; z++) { const c = z % 2 ? CR : WH; for (const x of [2, 4, 6]) { list.push([x, 6, z, 2, 1, z < 3 && x === 4 ? BR : (z === 1 || z === 2) && x === 6 ? BL : c]); list.push([x, 3, z, 2, 1, c]); } list.push([2, 4, z, 1, 2, c], [7, 4, z, 1, 2, c]); }
    for (const x of [2, 4, 6]) list.push([x, 3, 4, 2, 4, RD]); for (const x of [3, 5]) list.push([x, 3, 5, 2, 4, RD]); list.push([4, 3, 6, 2, 4, RD], [6, 3, 5, 1, 1, YL], [6, 3, 6, 1, 1, YL]);
    for (let z = 0; z < 3; z++) list.push([10, 1, z, 1, 1, BR]); list.push([9, 0, 3, 3, 3, GR], [9, 1, 4, 2, 2, GR], [9, 1, 5, 1, 1, GR]);
    list.push([1, 8, 0, 1, 1, YL], [1, 8, 1, 1, 1, RD], [1, 8, 2, 1, 1, YL], [1, 8, 3, 1, 1, DK], [3, 8, 0, 2, 1, BL], [3, 8, 1, 1, 1, YL]);
    list.map((b, i) => ({ b, i, st: 0.1 + i * 0.075 })).sort((a, b) => (a.b[0] + a.b[3] + a.b[1] + a.b[4]) - (b.b[0] + b.b[3] + b.b[1] + b.b[4]) || a.b[2] - b.b[2]).forEach(({ b, st }) => {
      const k = prog(ts, st, 0.4); if (k <= 0) return; const drop = (1 - easeOut(k)) * 6, [gx, gy, gz, w, d, col] = b;
      g.save(); g.translate(0, -drop * ISO.bh); g.globalAlpha = clamp(k * 3); brick(g, gx, gy, gz, w, d, col); g.restore();
    });
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Brick_toys>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
