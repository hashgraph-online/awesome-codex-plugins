# Sticker explainer

Also called: sticker style, die-cut stickers, sticker animation.

Family: Type, data and retro. Cadence: smooth, full frame rate. Usual tool: HyperFrames (canvas or SVG).

Die-cut stickers with a thick white border and a drop shadow pop onto a desk with a bounce: icons and bold word stickers, each tilted a little and swaying.

A sticker is a label of plastic, vinyl or another material with a pressure-sensitive adhesive on one side, used for decoration or for function, in many shapes, sizes and colours.

Sourcing note: The source describes stickers as objects; the die-cut explainer look is a practice summary.

## What makes it read as this

- A thick white border follows each shape, with rounded corners: the die-cut line
- A soft drop shadow lifts each sticker off the surface
- Bold, saturated flat colour with a thin darker edge
- Big, heavy word stickers: one word each
- Each tilted a few degrees, and none perfectly aligned

## Timing

Each sticker pops in over about half a second with an overshoot, one every 0.3 seconds, then sways slightly. Smooth, full frame rate.

## How to build it

- Describe each silhouette as a `Path2D`; draw it first with a 22 px white stroke and a white fill, with `shadowBlur` for the shadow, then fill the colour on top
- Pop-in: scale by `overshoot(prog(t, start, 0.55))`, with a small rise from below
- Sway: rotate by a sine of time scaled by how long the sticker has been there
- Word stickers: a rounded rectangle with `900` weight text centred in it

## Assets

All in code. Real icon sets should be ones the user owns or may reuse. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A peel-and-stick pop and a cheerful bouncy bed. Practice note.

## What makes it look wrong

- A white border of uneven width
- No shadow: the stickers look printed on the page
- Pop-ins with no overshoot
- Too many stickers at once

## Tested demo

This is the look from `art-forms/looks-abstract.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=sticker-explainer` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'sticker-explainer': { kind: '2d', fps: null, draw(g, t, W, H) {
    // die-cut stickers with a thick white border and a drop shadow, popping onto a desk with a bounce and then swaying a little; bold word stickers beside icons
    g.fillStyle = '#f2ede2'; g.fillRect(0, 0, W, H); g.fillStyle = 'rgba(0,0,0,.07)'; for (let y = 20; y < H; y += 30) for (let x = 20; x < W; x += 30) g.fillRect(x, y, 2, 2);
    const P = (fn) => { const p = new Path2D(); fn(p); return p; }, burst = P((p) => star(0, 0, 92, 68, 12, 0).forEach(([x, y], i) => (i ? p.lineTo(x, y) : p.moveTo(x, y)))), bulb = P((p) => { p.arc(0, -16, 56, 0, TAU); p.roundRect(-26, 28, 52, 40, 8); }), heart = P((p) => { p.moveTo(0, 60); p.bezierCurveTo(-110, -10, -50, -90, 0, -34); p.bezierCurveTo(50, -90, 110, -10, 0, 60); }), pill = P((p) => p.roundRect(-112, -42, 224, 84, 42)), badge = P((p) => p.arc(0, 0, 72, 0, TAU)), arrow = P((p) => { [[-90, -26], [20, -26], [20, -62], [92, 0], [20, 62], [20, 26], [-90, 26]].forEach(([x, y], i) => (i ? p.lineTo(x, y) : p.moveTo(x, y))); p.closePath(); }), speech = P((p) => { p.roundRect(-96, -56, 192, 104, 36); p.moveTo(-40, 46); p.lineTo(-62, 84); p.lineTo(-8, 46); });
    const text = (s, col, size) => { g.font = `900 ${size}px ${BAUD}`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillStyle = col; g.fillText(s, 0, 4); };
    const S = [[190, 140, -0.1, 0.2, burst, '#ffd23f', () => text('WOW!', BLK, 40)], [480, 130, 0.06, 0.5, bulb, '#ffe14d', () => { g.strokeStyle = BLK; g.lineWidth = 5; g.beginPath(); g.moveTo(-14, -16); g.lineTo(-6, 6); g.lineTo(6, -10); g.lineTo(14, 6); g.stroke(); g.fillStyle = '#9aa0ad'; g.fillRect(-20, 38, 40, 8); }], [770, 150, 0.1, 0.8, heart, '#ff4d6d', () => { g.fillStyle = 'rgba(255,255,255,.5)'; g.beginPath(); g.ellipse(-40, -30, 14, 8, -0.7, 0, TAU); g.fill(); }],
      [200, 320, 0.08, 1.1, pill, '#ff5a8a', () => text('SIMPLE', '#fff', 46)], [480, 320, -0.05, 1.4, arrow, '#3d7bff', () => {}], [760, 320, 0.05, 1.7, badge, '#35b868', () => text('100%', '#fff', 38)], [300, 460, -0.06, 2.0, pill, '#ffb02e', () => text('FAST', BLK, 52)], [650, 460, 0.07, 2.3, speech, '#fff', () => text('HI!', BLK, 54)]];
    for (const [x, y, rot, st, shape, col, paint] of S) {
      const k = overshoot(prog(t, st, 0.55)); if (k <= 0.001) continue; g.save(); g.translate(x, y + (1 - clamp(k)) * 30); g.rotate(rot + Math.sin(t * 2 + x) * 0.025 * clamp(t - st)); g.scale(k, k);
      g.shadowColor = 'rgba(40,30,20,.35)'; g.shadowBlur = 16; g.shadowOffsetX = 4; g.shadowOffsetY = 9; g.fillStyle = '#fff'; g.strokeStyle = '#fff'; g.lineWidth = 22; g.lineJoin = 'round'; g.stroke(shape); g.fill(shape); g.shadowColor = 'transparent'; g.fillStyle = col; g.fill(shape); g.lineWidth = 3; g.strokeStyle = 'rgba(0,0,0,.18)'; g.lineJoin = 'round'; g.stroke(shape); paint(); g.restore();
    }
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Sticker>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
