# Blueprint and technical drawing

Family: Type, data and retro. Cadence: smooth, full frame rate. Usual tool: HyperFrames (SVG, canvas).

White lines on blue: a grid, an object drawn in outline, centre lines, dimensions and a title block.

The blueprint is a cyanotype copy of an engineering drawing, introduced in 1842: white lines on blue.

## What makes it read as this

- White or pale lines on a deep blue
- A faint grid
- Dashed centre lines, dimension lines with end ticks
- A title block in a monospace face

## Timing

Steady: lines draw on, then dimensions and labels fade in. No bounce.

## How to build it

- Grid: thin lines every 30 px at low opacity (CSS: `repeating-linear-gradient`)
- Draw-on with `stroke-dashoffset` or a partial polyline
- Dashed centre lines with `setLineDash`
- Dimension lines: a line, two end ticks and a centred label

## Assets

All in code. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A pen plotter, a pencil. Practice note.

## What makes it look wrong

- A neon blue
- Labels that say nothing
- Perspective in the drawing

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=blueprint` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  blueprint: { kind: '2d', fps: null, draw(g, t, W, H) {
    // white lines on blue, a grid, then the drawing itself, then its dimensions. Steady, with no bounce.
    bg(g, W, H, '#1d4f91');
    g.strokeStyle = 'rgba(255,255,255,.12)'; g.lineWidth = 1; g.beginPath(); for (let x = 0; x <= W; x += 30) { g.moveTo(x, 0); g.lineTo(x, H); } for (let y = 0; y <= H; y += 30) { g.moveTo(0, y); g.lineTo(W, y); } g.stroke();
    g.strokeStyle = '#eaf2ff'; g.lineWidth = 2.5; g.lineCap = 'round'; g.lineJoin = 'round';
    const cx = W * 0.42, cy = H * 0.52, gear = Array.from({ length: 97 }, (_, i) => { const a = (i / 96) * TAU, r = 120 + (Math.floor(i / 4) % 2 ? 22 : 0); return [cx + Math.cos(a) * r, cy + Math.sin(a) * r]; });
    strokePart(g, gear, prog(t, 0.1, 1.2)); strokePart(g, circlePts(cx, cy, 44, 40), prog(t, 1.1, 0.4));
    g.setLineDash([10, 6]); g.lineWidth = 1.4; strokePart(g, [[cx - 170, cy], [cx + 170, cy]], prog(t, 1.4, 0.3)); strokePart(g, [[cx, cy - 170], [cx, cy + 170]], prog(t, 1.5, 0.3)); g.setLineDash([]);
    const k = prog(t, 1.9, 0.4); if (k > 0) {
      g.globalAlpha = k; g.lineWidth = 1.6; const y = cy + 176; g.beginPath(); g.moveTo(cx - 142, y); g.lineTo(cx + 142, y); g.moveTo(cx - 142, y - 8); g.lineTo(cx - 142, y + 8); g.moveTo(cx + 142, y - 8); g.lineTo(cx + 142, y + 8); g.stroke();
      g.fillStyle = '#eaf2ff'; g.font = `500 20px ui-monospace, Menlo, monospace`; g.textAlign = 'center'; g.fillText('Ø 284', cx, y + 28); g.textAlign = 'left';
      g.strokeRect(W * 0.68, H * 0.66, W * 0.26, H * 0.22); g.fillText('GEAR  12 T', W * 0.68 + 14, H * 0.66 + 32); g.fillText('SCALE 1:1', W * 0.68 + 14, H * 0.66 + 62); g.fillText('DRG  B2M-01', W * 0.68 + 14, H * 0.66 + 92); g.globalAlpha = 1;
    }
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Blueprint>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
