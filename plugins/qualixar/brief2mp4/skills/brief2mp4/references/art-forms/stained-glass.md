# Stained glass

Also called: stained glass window, leaded glass, church window.

Family: Folk and print traditions. Cadence: smooth, full frame rate. Usual tool: HyperFrames (canvas).

Coloured panes held by thick dark lead lines in an arched window: a rose at the top, a diamond lattice below, and light glowing through each pane.

Stained glass is glass coloured by adding metallic salts during its manufacture, arranged into windows of small pieces held together, traditionally, by strips of lead called cames. In Western Europe, together with illuminated manuscripts, such windows are a major form of medieval visual art that has survived.

## What makes it read as this

- Thick, dark, even lead lines round every pane
- Saturated, jewel-coloured panes: ruby, cobalt, emerald, amber, violet
- Each pane glows brighter at its centre, as light passes through
- A pointed or round arch, with a rose and a lattice
- A dark stone wall round it, so the glass is the light source

## Timing

The panes light up from the centre outward over about 2 seconds, then a soft beam of sun crosses the glass slowly. Smooth, full frame rate.

## How to build it

- Build each pane as a polygon; fill dark, then fill with its colour as it is lit, plus a radial glow with `lighter`
- Rose: annular sectors in three rings (`ring()` in the demo); lattice: a grid of diamonds clipped to the arch
- Stroke every pane with a 6 px dark line, `lineJoin = 'round'`
- The beam: a linear gradient band drawn with `lighter`, its position a function of time
- Wall: dark base colour and a block pattern

## Assets

All in code. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A choir pad, a long reverb, footsteps in a stone room. Practice note.

## What makes it look wrong

- Thin lead lines: they are part of the picture
- Flat panes with no glow
- Washed-out pastel colours: keep them saturated

## Tested demo

This is the look from `art-forms/looks-folk.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=stained-glass` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'stained-glass': { kind: '2d', fps: null, draw(g, t, W, H) {
    // a pointed window of coloured panes between thick lead lines, a rose at the top and a diamond lattice below, with light coming through and a slow beam of sun across the glass
    const COLS = ['#b3122b', '#1b3fa8', '#0a6a38', '#e8a317', '#6a2a9a', '#d9467a', '#e2641b'], x0 = 260, x1 = 700, yb = 512, ys = 250, cx = 480, cy = 236;
    bg(g, W, H, '#2a2622'); g.strokeStyle = 'rgba(0,0,0,.35)'; g.lineWidth = 2; g.beginPath(); for (let y = 20; y < H; y += 46) { g.moveTo(0, y); g.lineTo(W, y); for (let x = ((y / 46) % 2) * 40; x < W; x += 80) { g.moveTo(x, y); g.lineTo(x, y + 46); } } g.stroke();   // the stone wall
    const arch = () => { g.beginPath(); g.moveTo(x0, yb); g.lineTo(x0, ys); g.quadraticCurveTo(x0, 110, cx, 36); g.quadraticCurveTo(x1, 110, x1, ys); g.lineTo(x1, yb); g.closePath(); };
    const glow = g.createRadialGradient(cx, 260, 40, cx, 260, 360); glow.addColorStop(0, 'rgba(255,230,160,.35)'); glow.addColorStop(1, 'rgba(255,230,160,0)'); g.fillStyle = glow; g.fillRect(0, 0, W, H);
    g.save(); arch(); g.fillStyle = '#fff2c8'; g.fill(); g.clip();
    const panes = []; for (let row = -1; row < 7; row++) for (let c = -1; c < 7; c++) { const x = x0 + c * 74 + (row % 2 ? 37 : 0), y = 70 + row * 70; panes.push({ pts: [[x, y - 70], [x + 37, y], [x, y + 70], [x - 37, y]], x, y, col: COLS[Math.floor(hash(row + 9, c + 9, 1) * 7)] }); }
    const ring = (r0, r1, n, off, seed) => { for (let i = 0; i < n; i++) { const a0 = off + (i / n) * TAU, a1 = off + ((i + 1) / n) * TAU, am = (a0 + a1) / 2, pts = [[cx + Math.cos(a0) * r0, cy + Math.sin(a0) * r0], [cx + Math.cos(a0) * r1, cy + Math.sin(a0) * r1], [cx + Math.cos(am) * (r1 + 2), cy + Math.sin(am) * (r1 + 2)], [cx + Math.cos(a1) * r1, cy + Math.sin(a1) * r1], [cx + Math.cos(a1) * r0, cy + Math.sin(a1) * r0]]; panes.push({ pts, x: cx + Math.cos(am) * (r0 + r1) / 2, y: cy + Math.sin(am) * (r0 + r1) / 2, col: COLS[(i * 2 + seed + (i % 3)) % 7], round: true }); } };
    panes.push({ pts: circlePts(cx, cy, 134, 48), x: cx, y: cy, col: '#1a1620' }); ring(96, 134, 24, 0.1, 1); ring(62, 96, 16, 0, 3); ring(32, 62, 8, 0.2, 5); panes.push({ pts: circlePts(cx, cy, 32, 24), x: cx, y: cy, col: '#f5c518' });
    panes.forEach((p, i) => {
      const lit = prog(t, 0.1 + Math.hypot(p.x - cx, p.y - cy) / 900, 0.5); g.beginPath(); p.pts.forEach(([x, y], j) => (j ? g.lineTo(x, y) : g.moveTo(x, y))); g.closePath();
      g.fillStyle = lit < 1 ? '#1c1a22' : p.col; g.globalAlpha = 1; g.fill();
      if (lit > 0) { g.save(); g.clip(); g.globalAlpha = lit; g.fillStyle = p.col; g.fillRect(0, 0, W, H); const gl = g.createRadialGradient(p.x, p.y, 2, p.x, p.y, 52); gl.addColorStop(0, 'rgba(255,255,255,.1)'); gl.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gl; g.globalCompositeOperation = 'lighter'; g.fillRect(p.x - 60, p.y - 60, 120, 120); g.restore(); }
    });
    g.lineJoin = 'round'; g.strokeStyle = '#15131a'; g.lineWidth = 6; panes.forEach((p) => { g.beginPath(); p.pts.forEach(([x, y], j) => (j ? g.lineTo(x, y) : g.moveTo(x, y))); g.closePath(); g.stroke(); });
    const bx = lerp(x0 - 200, x1 + 200, (t * 0.18) % 1), bm = g.createLinearGradient(bx - 80, 0, bx + 80, 160); bm.addColorStop(0, 'rgba(255,240,190,0)'); bm.addColorStop(0.5, 'rgba(255,240,190,.38)'); bm.addColorStop(1, 'rgba(255,240,190,0)'); g.globalCompositeOperation = 'lighter'; g.fillStyle = bm; g.fillRect(x0, 0, x1 - x0, H); g.globalCompositeOperation = 'source-over';
    g.restore(); arch(); g.strokeStyle = '#3a342e'; g.lineWidth = 16; g.stroke(); g.strokeStyle = '#15131a'; g.lineWidth = 5; g.stroke();
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Stained_glass>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
