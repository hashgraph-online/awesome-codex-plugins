# Gond

Also called: gond painting, gond art, gondi art, jangarh kalam.

Family: Folk and print traditions. Cadence: steps 8 times a second. Usual tool: HyperFrames (canvas or SVG).

Animals and trees in thin black outline, filled with bold flat colour in bands, each band carrying fine repeated marks of one colour: dots, dashes, parallel lines or fish-scale arcs. A plain light ground, a bold crest and a decorated eye. It is a living tradition with working artists; the demo here is a code study of its visual rules, not the craft itself, and a film should credit the tradition and, where it can, commission or license work from the artists.

The Gond, or Gondi, people are an ethnolinguistic group spread across central and eastern India, including Madhya Pradesh, Maharashtra and Chhattisgarh. The artist Jangarh Singh Shyam, born into a Pardhan Gond family in Patangarh, Mandla district, Madhya Pradesh, is credited with starting the school called Jangarh Kalam; he used lines of coloured dots, inspired by Gond tattoos, with bands of dots, dense cross-hatching and comb-lines, and painted animals such as tigers and deer.

Sourcing note: Wikipedia has no standalone Gond painting article, so the sources are the Gond people article and the article on Jangarh Singh Shyam, the artist most closely tied to the modern style. Confirm the wider tradition against a museum source before making claims in a film.

## What makes it read as this

- Thin black outlines round animals, birds and trees
- Saturated flat colour: deep red, saffron, cobalt, leaf green and black
- Each body is filled in bands; each band is a solid base colour with marks of ONE contrasting colour, never a rainbow inside a stripe
- Mark types alternate band by band: rows of dots, short dashes, fine parallel lines, fish-scale arcs
- Bold, decorated details: a crest, an eye with rings and dots, branches that curl in toward the animal

## Timing

Parts draw on one after another over about 3 seconds, outline first, then the bands fill. The picture steps about 8 times a second.

## How to build it

- Draw each part with `folkShape()` and a black fill under the bands
- Bands: rotate to the shape's long axis, fill a 14 px strip with the base colour, then draw one mark type in the paired colour (`gondBands()` and the `GOND` colour pairs in `looks-folk.js`)
- Trunks and branches: a tapering band along a spline (`ribbon()`), ending in a curl
- Eye: a pale ring, a red ring, a dark pupil and a ring of small dots
- Keep the ground plain; add only a dotted border

## Assets

All in code. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Drums and a stringed drone, a rhythmic tapping as each band fills. Practice note.

## What makes it look wrong

- Pastel stripes or a rainbow inside each band: the colours are saturated and each band has one mark colour
- Gradients and shading
- Presenting a machine-made picture as authentic Gond art

## Tested demo

This is the look from `art-forms/looks-folk.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=gond` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  gond: { kind: '2d', fps: 8, draw(g, t, W, H) {
    // a bold bird and a tree on a plain light ground: every part is solid colour in bands, each band carrying one colour of fine marks, the tree's branches curling in toward the bird
    const ts = held(t, 8); bg(g, W, H, '#f6ecd0'); g.lineCap = 'round'; g.lineJoin = 'round';
    const k0 = prog(ts, 0, 0.8); g.strokeStyle = INK; g.lineWidth = 3; strokePart(g, [[16, 16], [W - 16, 16], [W - 16, H - 16], [16, H - 16], [16, 16]], k0); g.lineWidth = 1.6; strokePart(g, [[24, 24], [W - 24, 24], [W - 24, H - 24], [24, H - 24], [24, 24]], k0);
    g.fillStyle = INK; for (let i = 0; i < 60 * k0; i++) { const x = 40 + i * ((W - 80) / 60); for (const y of [34, H - 34]) { g.beginPath(); g.arc(x, y, 2.4, 0, TAU); g.fill(); } }
    const shape = (pts, st, ang, seed, lw = 3.4) => folkShape(g, pts, { start: st, dur: 0.6, fill: INK, lw, pattern: (c, bb) => gondBands(c, bb, ang, seed) }, ts);
    for (let i = 0; i < 3; i++) shape(leaf(470, 305, 200, 36, -0.4 + i * 0.4), 1.0 + i * 0.12, -0.4 + i * 0.4, i + 1);   // tail
    shape(ellipseLine(340, 308, 170, 98, -0.1), 0.2, -0.1, 0);   // body
    shape(leaf(250, 292, 130, 38, -2.45), 0.7, -2.45, 2);   // neck
    shape(ellipseLine(205, 205, 42, 38), 0.9, 0.4, 5);   // head
    for (let i = 0; i < 5; i++) { const a = -1.57 + (i - 2) * 0.34; shape(leaf(205 + (i - 2) * 6, 172, 58 - Math.abs(i - 2) * 6, 11, a), 1.4 + i * 0.05, a, i + 1, 3); }   // a bold crest
    shape(closed([[0, 0], [1, 0.25], [0, 0.5]], 4).map(([x, y]) => [172 - x * 64, 200 + y * 24]), 1.4, 0, 3, 3);   // beak
    if (prog(ts, 1.6, 0.2) > 0.5) { disc(g, 208, 198, 13, '#f6f0dc', 2.6); disc(g, 208, 198, 9, '#b3182a', 1.6); disc(g, 208, 198, 4.4, INK); g.fillStyle = INK; for (let i = 0; i < 10; i++) { const a = (i / 10) * TAU; g.beginPath(); g.arc(208 + Math.cos(a) * 18, 198 + Math.sin(a) * 18, 1.8, 0, TAU); g.fill(); } }   // a decorated eye
    for (const [x, st] of [[300, 1.8], [372, 1.9]]) { g.strokeStyle = INK; g.lineWidth = 5; strokePart(g, [[x, 395], [x - 8, 440], [x - 24, 478]], prog(ts, st, 0.4)); g.fillStyle = '#b3182a'; for (let i = 0; i < 6 * prog(ts, st + 0.2, 0.4); i++) { g.beginPath(); g.arc(x + 10 - i * 4.4, 414 + i * 11, 2.6, 0, TAU); g.fill(); } }
    shape(ribbon([[822, 492], [812, 410], [826, 310], [812, 215]], 24, 9), 1.9, -1.57, 6);   // the trunk
    shape(ribbon([[816, 340], [750, 318], [690, 282], [640, 262], [600, 268], [588, 292], [608, 306], [626, 292]], 13, 4), 2.3, -0.5, 1);   // a branch that curls in over the tail
    shape(ribbon([[820, 425], [750, 424], [680, 408], [630, 392], [596, 404], [596, 428], [618, 430]], 12, 4), 2.5, -0.2, 4);   // and one that curls in under it
    for (const [x, y, a, st] of [[820, 250, -2.3, 2.7], [820, 250, -0.8, 2.75], [815, 330, -2.2, 2.8], [822, 380, -0.9, 2.85], [800, 215, -1.57, 2.9]]) shape(leaf(x, y, 80, 16, a), st, a, (x + y) % 5, 3);
    const sun = prog(ts, 0.1, 0.8); shape(ellipseLine(112, 100, 40, 40), 0.1, 0.3, 3);
    g.fillStyle = INK; for (const r of [54, 64]) for (let i = 0; i < 16 * sun; i++) { const a = (i / 16) * TAU + (r > 58 ? 0.2 : 0); g.beginPath(); g.arc(112 + Math.cos(a) * r, 100 + Math.sin(a) * r, 2.8, 0, TAU); g.fill(); }
    speckle(g, W, H, 8, 40, [140, 100, 60]);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Gond_people>
- <https://en.wikipedia.org/wiki/Jangarh_Singh_Shyam>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
