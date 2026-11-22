# Pencil sketch

Also called: graphite drawing, pencil drawing.

Family: Drawn and painted. Cadence: steps 8 times a second. Usual tool: HyperFrames (canvas or SVG).

Graphite lines on toothed paper: thin hatching that builds tone, a doubled and searching outline, and a thumb-smudged shadow. It looks drawn by hand because no two lines are quite the same.

Pencil marks are made by abrasion, a trail of graphite left on the paper. A large, very pure graphite deposit was found at Borrowdale in Cumbria, England, in 1565 (some sources say as early as 1500). Hatching, tone from closely spaced parallel lines, originated in the Middle Ages and developed into cross-hatching, notably in fifteenth-century prints.

## What makes it read as this

- Thin grey lines with a slight wobble, and an outline drawn twice, a little differently each time
- Tone comes only from line density: one set of hatching for light, a second set across it for shadow
- A faint construction shape under the outline, as a sketcher would lay in first
- A smudge where a thumb rubbed the shadow
- Paper grain that breaks every line into specks

## Timing

Lines appear in drawing order over about 3 seconds: construction line, outline, then each hatching layer, then the smudge. The picture steps about 8 times a second and each step re-seeds the wobble, like a stop-motion sketch.

## How to build it

- Outline twice: two polylines with different seeded nudges of 1 to 2 px, keyed to `frameOf(t, 8)`, at different opacity
- Hatching: parallel lines clipped to the shape with `ctx.clip(path)`; later layers use an even-odd clip so that they land only on the shadow side
- Reveal each line from a fraction `k` of its length so the hatching sweeps on in order
- Smudge: a radial gradient squashed to an ellipse and drawn with `multiply`
- Tooth: specks in the paper colour drawn over the lines (`tooth()` in `looks-painted.js`)

## Assets

All in code. A scanned sheet of cartridge paper makes a better ground if the user has one. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A pencil scratch under each hatching pass, quiet room tone. Practice note.

## What makes it look wrong

- Hard black vector lines with no wobble
- Perfectly even hatching that never re-seeds, which looks ruled by a machine
- Shadow as a smooth gradient instead of lines

## Tested demo

This is the look from `art-forms/looks-painted.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=pencil-sketch` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'pencil-sketch': { kind: '2d', fps: 8, draw(g, t, W, H) {
    // an apple in graphite: a faint construction circle, a doubled outline, three layers of hatching that thicken toward the shadow, a rubbed smudge, and paper tooth over it all
    const f = frameOf(t, 8), ts = held(t, 8), cx = W * 0.47, cy = H * 0.5, R = 150, body = poly(applePts(cx, cy, R));
    bg(g, W, H, '#eee8da'); g.lineCap = 'round'; g.lineJoin = 'round';
    g.strokeStyle = 'rgba(70,72,80,.22)'; g.lineWidth = 1; strokePart(g, circlePts(cx, cy, R * 1.12, 48), prog(ts, 0, 0.5), f, 2);
    const clips = (...extra) => [[body, 'nonzero'], ...extra];
    hatch(g, clips([outside(W, H, ellipsePath(cx - 0.42 * R, cy - 0.45 * R, 0.3 * R, 0.2 * R, -0.6)), 'evenodd']), { cx, cy, ang: -0.9, sp: 9, L: 260, start: 0.9, gap: 0.02, a: 0.5, w: 1.5 }, ts, f);
    hatch(g, clips([outside(W, H, ellipsePath(cx - 0.3 * R, cy - 0.35 * R, 1.05 * R, 1.05 * R)), 'evenodd']), { cx, cy, ang: 0.8, sp: 8, L: 260, start: 1.7, gap: 0.02, a: 0.46, w: 1.4 }, ts, f);
    hatch(g, clips([outside(W, H, ellipsePath(cx - 0.12 * R, cy - 0.16 * R, 1.22 * R, 1.22 * R)), 'evenodd']), { cx, cy, ang: -0.45, sp: 5, L: 260, start: 2.5, gap: 0.015, a: 0.5, w: 1.4 }, ts, f);
    hatch(g, [[ellipsePath(cx + 0.1 * R, cy + 0.93 * R, 1.15 * R, 0.17 * R), 'nonzero'], [outside(W, H, body), 'evenodd']], { cx, cy: cy + 0.93 * R, ang: 0.1, sp: 5, L: 220, start: 2.6, gap: 0.02, a: 0.45, w: 1.5 }, ts, f);
    g.strokeStyle = 'rgba(46,48,56,.5)'; g.lineWidth = 1.5; strokePart(g, applePts(cx, cy, R * 1.01), prog(ts, 0.1, 0.9), f, 2.2);
    g.strokeStyle = 'rgba(40,42,50,.75)'; g.lineWidth = 2; strokePart(g, applePts(cx + 1, cy - 1, R), prog(ts, 0.3, 0.9), f + 17, 1.2);
    g.strokeStyle = 'rgba(40,42,50,.85)'; g.lineWidth = 4.5; strokePart(g, spline([[cx, cy - 0.7 * R], [cx + 5, cy - 0.88 * R], [cx + 16, cy - 1.06 * R]], 6), prog(ts, 1.0, 0.3), f, 0.8);
    g.lineWidth = 1.8; g.strokeStyle = 'rgba(40,42,50,.8)'; strokePart(g, spline([[cx + 8, cy - 0.98 * R], [cx + 48, cy - 1.22 * R], [cx + 105, cy - 1.2 * R], [cx + 70, cy - 1.0 * R], [cx + 8, cy - 0.98 * R]], 6), prog(ts, 1.2, 0.5), f, 1);
    strokePart(g, [[cx + 14, cy - 1.0 * R], [cx + 60, cy - 1.1 * R], [cx + 92, cy - 1.17 * R]], prog(ts, 1.6, 0.3), f, 0.8);
    const k = prog(ts, 3.0, 0.8); g.save(); g.globalCompositeOperation = 'multiply'; g.translate(cx + 0.5 * R, cy + 0.55 * R); g.rotate(-0.6); g.scale(1, 0.4);   // a thumb rubbed through the shadow
    const sm = g.createRadialGradient(0, 0, 4, 0, 0, 0.9 * R); sm.addColorStop(0, `rgba(80,82,92,${0.3 * k})`); sm.addColorStop(1, 'rgba(80,82,92,0)'); g.fillStyle = sm; g.fillRect(-R, -R, 2 * R, 2 * R); g.restore();
    paper(g, W, H, 3, 24); g.drawImage(grain(W, H, 9, 80, [250, 246, 236]), 0, 0);   // the tooth of the paper breaks every line
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Pencil>
- <https://en.wikipedia.org/wiki/Hatching>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
