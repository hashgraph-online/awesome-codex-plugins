# Felt and fabric craft

Also called: needle felt, fabric craft.

Family: Craft and handmade. Cadence: steps 12 times a second. Usual tool: HyperFrames (canvas or SVG).

Shapes that look needle-felted or sewn: a fuzzy edge of loose fibres, a matte mottled surface, visible stitches.

Needle felting tangles wool fibres with barbed needles to make flat pictures and soft figures.

Sourcing note: The craft is well documented; its use in animation is a practice note, not sourced.

## What makes it read as this

- A halo of short fibres along every edge
- Matte, slightly mottled colour
- Stitches: a dashed line just inside the edge
- Chunky, simple forms in wool colours

## Timing

Stop-motion cadence, on twos. Gentle bobbing and nudging.

## How to build it

- Draw the shape, then several hundred short strokes outward from its edge, each angled by a seeded hash
- Stitches: `setLineDash([9, 7])` on a path just inside the edge (SVG: `stroke-dasharray`)
- Mottle: a grain texture clipped to the shape with `multiply`
- SVG route: high-frequency `feTurbulence` (0.8 to 1.2) with displacement scale 3 to 6 on the edge

Use Blender hair or fur for real fibre fuzz on 3D figures.

## Assets

Procedural. A felt texture from an image model helps for close-ups. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Soft, warm, acoustic. Practice note.

## What makes it look wrong

- Crisp vector edges
- Flat plastic colour
- No fibre fuzz

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=felt` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  felt: { kind: '2d', fps: 12, draw(g, t, W, H) {
    // soft shapes with a halo of fibres along the edge and a row of stitches; everything bobs on twos
    const ts = onTwos(t);
    bg(g, W, H, '#d8cdb8');
    const fuzzy = (x, y, r, col, seed) => {
      blob(g, x, y, r, seed, 0.06); fill(g, col);
      g.strokeStyle = col; g.lineWidth = 1.1; g.globalAlpha = 0.75;
      for (let i = 0; i < 520; i++) { const a = hash(i, seed) * TAU, rr = r * (0.97 + hash(i, seed, 1) * 0.07), l = 3 + hash(i, seed, 2) * 7, tw = a + (hash(i, seed, 3) - 0.5) * 1.6; g.beginPath(); g.moveTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr); g.lineTo(x + Math.cos(a) * rr + Math.cos(tw) * l, y + Math.sin(a) * rr + Math.sin(tw) * l); g.stroke(); }
      g.globalAlpha = 1; g.setLineDash([9, 7]); g.strokeStyle = 'rgba(255,250,235,.85)'; g.lineWidth = 2.4; g.beginPath(); g.arc(x, y, r * 0.8, 0, TAU); g.stroke(); g.setLineDash([]);
      g.save(); g.globalCompositeOperation = 'multiply'; g.beginPath(); g.arc(x, y, r, 0, TAU); g.clip(); g.drawImage(grain(W, H, seed, 60, [40, 30, 30]), 0, 0); g.restore();
    };
    fuzzy(W * 0.3, H * 0.52 + Math.sin(ts * 2.4) * 10, 108, '#c85a54', 21);
    fuzzy(W * 0.56, H * 0.46 + Math.sin(ts * 2.4 + 1.3) * 12, 84, '#e2b23f', 22);
    fuzzy(W * 0.76, H * 0.56 + Math.sin(ts * 2.4 + 2.6) * 9, 66, '#5d8a72', 23);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Needle_felting>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
