# Madhubani (Mithila)

Also called: mithila art, mithila painting, madhubani art.

Family: Folk and print traditions. Cadence: steps 8 times a second. Usual tool: HyperFrames (canvas or SVG).

Double black outlines round bright flat fills, with every gap packed with hatching, dots or small motifs: fish, peacocks and lotuses inside a decorated border, with no empty space. It is a living tradition with working artists; the demo here is a code study of its visual rules, not the craft itself, and a film should credit the tradition and, where it can, commission or license work from the artists.

Madhubani art, also called Mithila art, is a style of painting practised in the Mithila region of Nepal and Bihar. It was traditionally created by women of various communities on freshly plastered mud walls and floors of huts, and is now also done on cloth, handmade paper and canvas, with natural dyes and pigments.

Sourcing note: Wikipedia marks its line that no space is left empty, with the gaps filled by flowers, animals, birds and geometric designs, as needing a citation; confirm it against a museum or scholarly source before quoting it.

## What makes it read as this

- Double black outlines: a bold line with a thin one inside it
- Bright, flat colour: red, yellow, green and indigo, with black line work
- Every gap is filled with hatching, dots, flowers, leaves or geometric marks: no empty space
- Motifs from nature: fish, peacocks, lotus, the sun and moon, plants
- A decorated border of triangles and flowers, drawn as part of the painting

## Timing

Elements are drawn on in order over about 4 seconds: border, ground motifs, then the large figures. The picture steps about 8 times a second.

## How to build it

- Build each figure as a smooth closed spline (`closed()` in `looks-folk.js`) and draw it with `folkShape()`: the outline draws round, the fill comes in, a pattern fills it, then an inner line follows
- Patterns clipped to the shape: parallel lines, dot grids and scale arcs (`lines()`, `dots()`, `scales()`)
- Fill the ground first with a grid of small motifs, each chosen by a hash of its cell, so the gaps are never blank
- Draw the border as a loop of triangles with a flower in each corner

## Assets

All in code. Real work is done on handmade paper or cloth: a scanned paper texture helps if the user has one. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Soft folk percussion or a flute drone, a gentle brush sound as each figure draws on. Practice note.

## What makes it look wrong

- Empty space: the form is defined by filling it
- Single thin outlines and gradients
- Presenting a machine-made picture as authentic Madhubani art

## Tested demo

This is the look from `art-forms/looks-folk.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=madhubani` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  madhubani: { kind: '2d', fps: 8, draw(g, t, W, H) {
    // fish, a peacock and a lotus in double black outlines, every gap filled with dots, hatching and small motifs, inside a decorated border: no empty paper
    const ts = held(t, 8), f = frameOf(t, 8), RED = '#c8312b', YEL = '#f0b429', GRN = '#2e8b57', IND = '#2b3a8c';
    bg(g, W, H, '#f3e2bd'); g.lineCap = 'round'; g.lineJoin = 'round';
    const k0 = easeOut(prog(ts, 0, 0.7));
    g.strokeStyle = INK; for (const [ins, w] of [[14, 5], [21, 2], [64, 2], [71, 5]]) { g.lineWidth = w; strokePart(g, [[ins, ins], [W - ins, ins], [W - ins, H - ins], [ins, H - ins], [ins, ins]], k0); }
    borderTriangles(g, W, H, [RED, YEL, IND], (i) => prog(ts, 0.1 + hash(i, 1) * 0.6, 0.1) > 0);
    for (const [x, y] of [[43, 43], [W - 43, 43], [43, H - 43], [W - 43, H - 43]]) if (k0 > 0.6) rosette(g, x, y, 15, 8, RED, YEL);
    g.save(); g.globalAlpha = k0; g.beginPath(); g.rect(72, 72, W - 144, H - 144); g.clip(); lines(g, [72, 72, W - 72, H - 72], 0.75, 9, 1, 'rgba(150,100,40,.28)'); g.restore();   // even the paper is hatched
    for (let y = 86, r = 0; y < H - 76; y += 27, r++) for (let x = 86 + (r % 2) * 14; x < W - 76; x += 28) {   // the ground: a small motif in every gap, chosen and placed by a hash
      const c = Math.floor(x / 28) + r * 40, k = prog(ts, 0.3 + hash(c, 2) * 2.4, 0.1), kind = Math.floor(hash(c, 3) * 4); if (k <= 0) continue;
      const jx = x + jit(c, 4, 4), jy = y + jit(c, 5, 4); g.strokeStyle = INK; g.lineWidth = 1.6;
      if (kind === 0) rosette(g, jx, jy, 12, 4, hash(c, 6) > 0.5 ? RED : IND, YEL, hash(c, 7));
      else if (kind === 1) { g.fillStyle = GRN; for (const s of [-1, 1]) { g.beginPath(); g.ellipse(jx + s * 6, jy, 9, 3.6, s * 0.7, 0, TAU); g.fill(); } }
      else if (kind === 2) { for (let d = 0; d < 3; d++) disc(g, jx - 8 + d * 8, jy + (d % 2) * 4, 2.4, d === 1 ? RED : INK); }
      else { g.beginPath(); g.moveTo(jx - 9, jy + 4); g.lineTo(jx - 3, jy - 4); g.lineTo(jx + 3, jy + 4); g.lineTo(jx + 9, jy - 4); g.stroke(); }
    }
    for (let i = 0; i < 11; i++) {   // the peacock's tail: eleven feathers, each with an eye
      const a = -Math.PI * (0.96 - i * 0.092), col = [GRN, IND, RED][i % 3], L = 168, p = leaf(480, 266, L, 30, a);
      folkShape(g, p, { start: 0.7 + i * 0.07, dur: 0.5, fill: col, lw: 3.4, inner: 0.9, pattern: (c, bb) => lines(c, bb, a + 0.5, 6, 1.4, 'rgba(250,235,190,.7)') }, ts);
      if (prog(ts, 1.2 + i * 0.07, 0.2) > 0.5) { const ex = 480 + Math.cos(a) * L * 0.72, ey = 266 + Math.sin(a) * L * 0.72; disc(g, ex, ey, 16, YEL, 2); disc(g, ex, ey, 10, RED); disc(g, ex, ey, 5, IND); }
    }
    folkShape(g, leaf(480, 266, 140, 30, -Math.PI / 2), { start: 1.5, dur: 0.5, fill: IND, lw: 3.6, inner: 0.9, pattern: (c, bb) => dots(c, bb, 9, 1.8, YEL) }, ts);
    if (prog(ts, 1.9, 0.3) > 0.3) { disc(g, 480, 118, 18, IND, 3); g.strokeStyle = INK; g.lineWidth = 2.4; for (const s of [-1, 0, 1]) { g.beginPath(); g.moveTo(480 + s * 5, 101); g.lineTo(480 + s * 13, 84); g.stroke(); disc(g, 480 + s * 13, 82, 3.4, RED); } disc(g, 472, 116, 3.4, '#fff'); }
    for (const [i, L, col, st] of [[0, 150, RED, 2.0], [1, 114, YEL, 2.25], [2, 76, GRN, 2.5]]) {   // the lotus: three rings of petals
      const n = 7 - i * 2; for (let j = 0; j < n; j++) { const a = -Math.PI * (0.94 - (j + 0.5 * (i % 2)) * (0.88 / (n - 1 + (i % 2) * 0.01))); folkShape(g, leaf(480, 464, L, 26 - i * 4, a), { start: st + j * 0.05, dur: 0.45, fill: col, lw: 3.4, inner: 0.88, pattern: (c, bb) => lines(c, bb, a, 5, 1.4, i === 1 ? RED : INK) }, ts); }
    }
    for (const [cx, dir, col, col2, st] of [[232, 1, RED, YEL, 2.6], [728, -1, YEL, RED, 2.9]]) {
      folkShape(g, leaf(cx - 40 * dir, 318, 70, 16, dir > 0 ? -1.0 : -2.14), { start: st, dur: 0.4, fill: GRN, lw: 3, pattern: (c, bb) => lines(c, bb, 0.9, 5, 1.2, INK) }, ts);
      for (let w = 0; w < 3; w++) { g.strokeStyle = IND; g.lineWidth = 3; strokePart(g, Array.from({ length: 20 }, (_, i) => [cx - 150 + i * 15.8, 418 + w * 14 + Math.sin(i * 1.2 + w) * 4]), prog(ts, st + 0.4, 0.5), 0, 0); }   // water under the fish
      folkShape(g, fish(cx, 348, 140, 76, dir), { start: st, dur: 0.7, fill: col, lw: 4.4, inner: 0.9, pattern: (c, bb) => { scales(c, bb, 11, col2, 2.4); dots(c, bb, 16, 1.6, INK); } }, ts);
      if (prog(ts, st + 0.6, 0.3) > 0.4) { disc(g, cx + 76 * dir, 340, 14, '#fff', 3); disc(g, cx + 76 * dir, 340, 6.5, INK); }
    }
    for (const [x, c1, st] of [[170, RED, 3.2], [790, IND, 3.4]]) {   // two big flowers on stems, with leaves, fill the upper corners
      if (prog(ts, st, 0.3) > 0) { g.strokeStyle = INK; g.lineWidth = 3; strokePart(g, [[x, 232], [x + 4, 270], [x - 2, 310]], 1); for (const s of [-1, 1]) folkShape(g, leaf(x, 262, 60, 13, s > 0 ? 0.5 : Math.PI - 0.5), { start: st, dur: 0.3, fill: GRN, lw: 3, pattern: (c, bb) => lines(c, bb, 0, 5, 1.2, INK) }, ts); rosette(g, x, 175, 56, 8, c1, YEL, 0.2); }
    }
    speckle(g, W, H, 9, 40, [120, 80, 40]);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Madhubani_art>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
