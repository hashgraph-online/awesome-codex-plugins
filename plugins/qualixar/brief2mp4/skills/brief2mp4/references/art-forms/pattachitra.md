# Pattachitra

Also called: patachitra, pattachitra painting, odisha scroll painting.

Family: Folk and print traditions. Cadence: steps 8 times a second. Usual tool: HyperFrames (canvas or SVG).

Bold black outlines and flat colour on a prepared ground: a thick ornamental border, an almond eye in profile, scale and fin patterns, and flowers and tendrils packed round the subject. It is a living tradition with working artists; the demo here is a code study of its visual rules, not the craft itself, and a film should credit the tradition and, where it can, commission or license work from the artists.

Patachitra or Pattachitra is a traditional cloth-based scroll painting of the eastern Indian states of Odisha and West Bengal; the name comes from the Sanskrit patta, cloth, and chitra, picture. The Odisha tradition originated at Puri, is painted in natural colours on cloth coated with chalk and gum, and has bold, clean lines with no landscape or perspective.

Sourcing note: The fish in the demo is a decorative study of the border, outline, eye and fill rules; the tradition itself mostly depicts Hindu deities and stories, which Wikipedia describes.

## What makes it read as this

- A thick, ornamental border in red, yellow and black, with dots and zigzags
- Bold, clean outlines and flat colour
- Eyes in profile, drawn as an almond with a dark pupil
- Dense floral fill: rosettes, leaves and spiral tendrils
- Patterns inside the shapes: scales, fan lines, bands

## Timing

The ground motifs fill in over about 3 seconds, the main figure draws on over about 1.5 seconds. The picture steps about 8 times a second.

## How to build it

- Draw the border as flat bands with dots and zigzags (`strokeRect`, dot loops)
- Fill the ground with rosettes (`rosette()`) and spiral tendrils (`curl()`) on an offset grid
- The figure is a closed spline drawn with `folkShape()`, a heavy 8 px outline and a scale pattern
- An almond eye: a closed four-point spline with a dark disc inside

## Assets

All in code. A scan of cloth or tea-stained paper helps if the user has one. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Drone and temple-bell texture, a rhythmic percussion under the border. Practice note.

## What makes it look wrong

- Thin outlines, gradients and perspective: the tradition is flat
- Drawing deity faces from memory: the demo uses a fish for that reason
- Presenting a machine-made picture as authentic Pattachitra

## Tested demo

This is the look from `art-forms/looks-folk.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=pattachitra` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  pattachitra: { kind: '2d', fps: 8, draw(g, t, W, H) {
    // a flat ochre ground, a thick ornamental border, bold black outlines, a fish with an almond eye in profile, and flowers and tendrils packed in round it
    const ts = held(t, 8), f = frameOf(t, 8), RED = '#a8281f', CRM = '#f7e8c6', GRN = '#2f7d3b', k0 = easeOut(prog(ts, 0, 0.8));
    bg(g, W, H, '#e8ad44'); g.lineCap = 'round'; g.lineJoin = 'round';
    for (let y = 90, r = 0; y < H - 80; y += 62, r++) for (let x = 96 + (r % 2) * 40; x < W - 80; x += 80) {   // the ground: rosettes, leaf pairs and tendrils on a grid, offset every other row
      const c = r * 20 + Math.floor(x / 80), k = prog(ts, 0.4 + hash(c, 1) * 2.4, 0.15); if (k <= 0) continue; g.strokeStyle = INK; g.lineWidth = 2.4;
      if (hash(c, 2) > 0.45) { rosette(g, x, y, 26, 6, hash(c, 3) > 0.5 ? RED : CRM, '#f6d160', hash(c, 4)); g.beginPath(); g.arc(x, y, 26 * 0.9, 0, TAU); g.stroke(); }
      else { strokePart(g, curl(x, y, 22, 2.2, hash(c, 5) > 0.5 ? 1 : -1), 1); for (const d of [-1, 1]) { g.fillStyle = GRN; g.beginPath(); g.ellipse(x + d * 26, y + 18, 16, 6, d * -0.5, 0, TAU); g.fill(); g.stroke(); } }
    }
    g.fillStyle = RED; g.beginPath(); g.rect(0, 0, W, H); g.rect(46, 46, W - 92, H - 92); g.globalAlpha = k0; g.fill('evenodd'); g.globalAlpha = 1;   // the thick red border
    g.fillStyle = '#f6d160'; g.beginPath(); g.rect(46, 46, W - 92, H - 92); g.rect(68, 68, W - 136, H - 136); g.globalAlpha = k0; g.fill('evenodd'); g.globalAlpha = 1;
    g.strokeStyle = INK; for (const [ins, w] of [[3, 3], [46, 5], [68, 5]]) { g.lineWidth = w; g.strokeRect(ins, ins, W - 2 * ins, H - 2 * ins); }
    for (let i = 0; i < 80 * k0; i++) { const per = 2 * (W - 40) + 2 * (H - 40), d = (i / 80) * per, side = d < W - 40 ? 0 : d < W - 40 + H - 40 ? 1 : d < 2 * (W - 40) + H - 40 ? 2 : 3; let x, y; if (side === 0) { x = 20 + d; y = 24; } else if (side === 1) { x = W - 24; y = 20 + d - (W - 40); } else if (side === 2) { x = W - 20 - (d - (W - 40) - (H - 40)); y = H - 24; } else { x = 24; y = H - 20 - (d - 2 * (W - 40) - (H - 40)); } disc(g, x, y, 6, CRM, 2); }
    g.strokeStyle = INK; g.lineWidth = 2.4; for (let i = 0; i < 60 * k0; i++) { const x = 90 + i * ((W - 180) / 60); strokePart(g, [[x, 52], [x + 7, 62], [x + 14, 52]], 1); strokePart(g, [[x, H - 52], [x + 7, H - 62], [x + 14, H - 52]], 1); }
    const A = -0.1, cx = 480, cy = 282, fp = fish(cx, cy, 238, 120, 1, A);
    folkShape(g, closed([[-0.6, 0.08], [-0.45, -0.5], [-0.05, -0.95], [0.4, -0.75], [0.72, -0.3], [0.7, 0.1]], 6).map(([x, y]) => [cx + x * 120 - 20, cy - 52 + y * 105]), { start: 1.5, dur: 0.5, fill: RED, lw: 6, pattern: (c, bb) => lines(c, bb, Math.PI / 2 + 0.3, 8, 2.4, INK) }, ts);   // dorsal fin
    folkShape(g, closed([[0, 0], [-0.35, 0.65], [0.3, 1], [0.7, 0.35]], 6).map(([x, y]) => [cx - 10 + x * 90, cy + 40 + y * 80]), { start: 1.7, dur: 0.4, fill: GRN, lw: 6, pattern: (c, bb) => lines(c, bb, 1.2, 8, 2.4, INK) }, ts);   // pectoral fin
    folkShape(g, fp, { start: 0.9, dur: 1.2, fill: CRM, lw: 8, pattern: (c, bb) => { scales(c, bb, 20, RED, 3.6); lines(c, [bb[0], bb[1], bb[0] + 100, bb[3]], Math.PI / 2, 10, 4, RED); dots(c, [bb[0] + 110, cy - 34, bb[2] - 40, cy + 34], 14, 2.6, INK); } }, ts);
    if (prog(ts, 2.4, 0.4) > 0.4) {
      const ex = cx + 140, ey = cy - 18, eye = closed([[-1, 0], [0, -0.6], [1, 0], [0, 0.6]], 6).map(([x, y]) => [ex + x * 38, ey + y * 24]);
      g.fillStyle = '#fff'; g.beginPath(); eye.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.fill(); g.strokeStyle = INK; g.lineWidth = 5; g.stroke(); disc(g, ex + 4, ey, 11, INK);
      g.lineWidth = 4; strokePart(g, spline([[cx + 70, cy - 70], [cx + 95, cy], [cx + 70, cy + 70]], 8), 1); strokePart(g, spline([[cx + 40, cy - 66], [cx + 62, cy], [cx + 40, cy + 66]], 8), 1);   // the gill lines
    }
    speckle(g, W, H, 6, 45, [110, 70, 20]);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Pattachitra>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
