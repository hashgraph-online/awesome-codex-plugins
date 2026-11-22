# Papercut and sanjhi (lace-cut paper)

Also called: papercutting, sanjhi, kirigami, lace-cut paper.

Family: Craft and handmade. Cadence: steps 8 times a second. Usual tool: HyperFrames (canvas or SVG).

One colour of cut paper on a plain ground: a scalloped medallion and corner pieces full of symmetrical cut-outs, with a soft shadow that shows the paper is a layer above the page. It is a living tradition with working artists; the demo here is a code study of its visual rules, not the craft itself.

Papercutting is the art of making designs cut from a single sheet of paper, which has developed in many cultures; the oldest surviving paper cutout, a symmetrical circle from the 6th century, was found in Xinjiang, China. Japanese paper cutting is called kirigami.

Sourcing note: The sources do not cover sanjhi, the Indian stencil papercutting tradition: it is named here only as an alias. Add a primary or museum source for it before a film makes claims about it.

## What makes it read as this

- One paper colour only: red on cream, or white on a dark ground
- Symmetry: radial for a medallion, mirrored for corners
- Cut-outs in rings: leaves, drops, round holes, fine dots
- A scalloped or pointed edge and thin bridges between the holes
- A slight drop shadow and a trace of sway

## Timing

The rings open one after another over about 3 seconds, and the paper trembles a fraction of a degree. The picture steps about 8 times a second.

## How to build it

- One `Path2D`: the outline plus every hole as a subpath, filled with the even-odd rule (`holesPath()` in `looks-toon.js`)
- Rings of holes by `laceRing()`: leaf, drop and dot shapes at equal angles, scaled up from nothing to open them
- Shadow: `shadowBlur`, `shadowOffsetX` and `shadowOffsetY` on the fill
- Mirror a corner piece four ways with `ctx.scale(+-1, +-1)`

## Assets

All in code. A scanned sheet of cream paper helps if the user has one. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A scissors snip as each ring opens, a soft drone. Practice note.

## What makes it look wrong

- Two or more colours: that is collage, not a single sheet
- Holes with no bridges, which would fall apart
- Presenting a machine-made picture as authentic sanjhi work

## Tested demo

This is the look from `art-forms/looks-toon.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=papercut` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  papercut: { kind: '2d', fps: 8, draw(g, t, W, H) {
    // one colour of lace-cut paper, red on cream: a scalloped medallion and four corner pieces, symmetrical cut patterns that open ring by ring, a drop shadow under the paper
    const ts = held(t, 8), f = frameOf(t, 8), RED = '#c8281f', cx = 480, cy = 270; bg(g, W, H, '#f2e8d2'); speckle(g, W, H, 2, 34, [150, 120, 70]);
    const kk = (i) => easeOut(prog(ts, 0.2 + i * 0.45, 0.6)), sway = jit(f, 1, 0.004);
    const rings = [[16, 46, 12, 8, 'leaf'], [76, 40, 9, 16, 'leaf'], [124, 20, 9, 16, 'dot'], [150, 34, 8, 24, 'drop'], [190, 22, 3.6, 48, 'dot'], [208, 16, 5, 36, 'drop']];
    const outer = Array.from({ length: 360 }, (_, i) => { const a = (i / 360) * TAU, r = 240 + 8 * Math.abs(Math.cos(a * 18)); return [cx + Math.cos(a) * r, cy + Math.sin(a) * r]; });
    const holes = rings.flatMap(([r0, len, wid, n, kind], i) => laceRing(cx, cy, r0, len, wid, n, kind, 0, TAU, kk(i)));
    holes.push(...laceRing(cx, cy, 0, 0, 8 * kk(0), 1, 'dot'));
    g.save(); g.translate(cx, cy); g.rotate(sway); g.translate(-cx, -cy); g.shadowColor = 'rgba(70,20,10,.45)'; g.shadowBlur = 9; g.shadowOffsetX = 4 + jit(f, 2, 1); g.shadowOffsetY = 6; g.fillStyle = RED; g.fill(holesPath(outer, holes), 'evenodd'); g.restore();
    for (const [sx, sy] of [[1, 1], [-1, 1], [1, -1], [-1, -1]]) {   // corner lace, mirrored four ways
      const q = []; for (let i = 0; i <= 40; i++) { const a = (i / 40) * Math.PI / 2, r = 150 + 6 * Math.abs(Math.cos(a * 16)); q.push([Math.cos(a) * r, Math.sin(a) * r]); }
      const ch = [[0, 34, 9, 6, 'leaf'], [66, 26, 7, 9, 'drop'], [112, 14, 4.6, 14, 'dot']].flatMap(([r0, len, wid, n, kind], i) => laceRing(0, 0, r0, len, wid, n, kind, 0.12, Math.PI / 2 - 0.12, kk(i + 1)));
      g.save(); g.translate(sx > 0 ? 0 : W, sy > 0 ? 0 : H); g.scale(sx, sy); g.shadowColor = 'rgba(70,20,10,.45)'; g.shadowBlur = 8; g.shadowOffsetX = 3; g.shadowOffsetY = 5; g.fillStyle = RED; g.fill(holesPath([[0, 0], ...q], ch.map((h) => h)), 'evenodd'); g.restore();
    }
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Papercutting>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
