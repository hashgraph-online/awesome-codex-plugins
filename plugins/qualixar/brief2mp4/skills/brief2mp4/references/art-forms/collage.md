# Collage and mixed media

Also called: photomontage, mixed media.

Family: Craft and handmade. Cadence: steps 8 times a second. Usual tool: HyperFrames (canvas or DOM).

Pieces of different papers, photographs and print stuck together: mismatched scale and texture, torn edges, hard shadows.

From the French coller, to glue. Braque and Picasso brought it into modern art around 1912; Dada followed with photomontage.

## What makes it read as this

- Torn or cut edges
- Mixed materials: flat colour, halftone photograph, tape
- Overlap with a hard, offset shadow
- Mismatched scale on purpose
- One palette holding it together

## Timing

On twos or threes. Pieces pop into place on the beat with a small rotation, then hold.

## How to build it

- Torn edge: walk the outline of a rectangle and nudge every point with a seeded hash
- Hard shadow: `shadowBlur: 0` with an offset of 5 to 6 px
- Halftone a photo: dots on a staggered grid sized by brightness
- Entrance: scale from 1.25 to 1 with a quarter-turn of rotation over a quarter of a second

## Assets

Paper textures in code. Photo fragments need images you own, or generated ones. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Bright percussive music, staccato effects on each pop. Practice note.

## What makes it look wrong

- Everything neatly aligned
- No shadows
- Too many unrelated colours and typefaces

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=collage` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  collage: { kind: '2d', fps: 8, draw(g, t, W, H) {
    // torn paper, a halftone "photo", tape. Pieces pop in on threes with a hard shadow, slightly rotated.
    const f = frameOf(t, 8), ts = held(t, 8);
    bg(g, W, H, '#e9e2d0');
    const torn = (x, y, w, h, col, seed, start, rot) => {
      const k = prog(ts, start, 0.25); if (k <= 0) return;
      g.save(); g.translate(x, y); g.rotate(rot + (1 - k) * 0.25); g.scale(lerp(1.25, 1, k), lerp(1.25, 1, k));
      g.shadowColor = 'rgba(20,10,0,.45)'; g.shadowOffsetX = 5; g.shadowOffsetY = 6; g.shadowBlur = 0;
      g.beginPath(); const n = 26; for (let i = 0; i < n; i++) { const e = i / n, px = e < 0.25 ? lerp(-w, w, e * 4) : e < 0.5 ? w : e < 0.75 ? lerp(w, -w, (e - 0.5) * 4) : -w, py = e < 0.25 ? -h : e < 0.5 ? lerp(-h, h, (e - 0.25) * 4) : e < 0.75 ? h : lerp(h, -h, (e - 0.75) * 4); const jx = jit(seed, i, 7), jy = jit(seed, i + 50, 7); i ? g.lineTo(px + jx, py + jy) : g.moveTo(px + jx, py + jy); } g.closePath(); fill(g, col);
      g.restore();
    };
    torn(W * 0.3, H * 0.42, 190, 130, '#2e4a7d', 41, 0.2, -0.08);
    torn(W * 0.62, H * 0.56, 210, 110, '#d94f30', 42, 0.6, 0.06);
    torn(W * 0.5, H * 0.3, 120, 70, '#f1c84b', 43, 1.0, -0.14);
    const k = prog(ts, 1.4, 0.25);
    if (k > 0) {                                                          // the halftone disc: dots sized by a gradient
      g.save(); g.translate(W * 0.47, H * 0.52); g.scale(lerp(1.3, 1, k), lerp(1.3, 1, k)); g.fillStyle = '#111';
      for (let y = -110; y <= 110; y += 11) for (let x = -110; x <= 110; x += 11) { const d = Math.hypot(x, y); if (d > 110) continue; g.beginPath(); g.arc(x + ((y / 11) % 2) * 5.5, y, 1 + 4.2 * (1 - (x + 110) / 220), 0, TAU); g.fill(); }
      g.restore();
    }
    const tk = prog(ts, 1.9, 0.2); if (tk > 0) { g.save(); g.translate(W * 0.47, H * 0.3); g.rotate(-0.2); g.fillStyle = 'rgba(240,225,170,.8)'; g.fillRect(-60 * tk, -14, 120 * tk, 28); g.restore(); }
    paper(g, W, H, 9, 32 + jit(f, 1, 3));
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Collage>
- <https://en.wikipedia.org/wiki/Cutout_animation>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
