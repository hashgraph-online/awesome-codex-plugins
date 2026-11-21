# Rotoscope look

Family: Drawn and painted. Cadence: steps 12 times a second. Usual tool: HyperFrames (canvas over video).

Real movement traced by hand: lifelike motion, flat colour fields that drift, and an outline that shimmers.

Max Fleischer built the rotoscope. A Scanner Darkly, Waking Life and the a-ha video for Take On Me are the well-known examples.

## What makes it read as this

- Motion with the timing of live action
- Flat or posterised colour fields
- Outlines that change slightly every drawing
- Colour that sits a little off the line

## Timing

Every frame or on twos. The boil is keyed to the drawing.

## How to build it

- From footage: draw each video frame to a canvas, posterise it, find edges (three.js has `SobelOperatorShader`), then nudge the edges per drawing
- From code: a figure built from joints, drawn twice: thick flat colour offset by a seeded amount, then a thin outline with its own nudge
- Re-encode source video with a keyframe on every frame so seeking is exact

Dedicated tools do true painterly rotoscoping better than a browser.

## Assets

Footage you own, or a figure built in code. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

The original scene audio, or music-led. Practice note.

## What makes it look wrong

- Edge noise that flickers out of control
- Losing the subject in the treatment
- Tracing footage you have no right to use

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=rotoscope` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of that file. Take the technique, not the picture.

```js
  rotoscope: { kind: '2d', fps: 12, draw(g, t, W, H) {
    // a walking figure traced on twos: flat colour fields that drift a little and an outline that never sits still
    const f = frameOf(t, 12), ts = onTwos(t), ph = ts * 5.5, x = W * 0.5, y = H * 0.58;
    bg(g, W, H, '#20263a'); g.fillStyle = '#2c3552'; g.fillRect(0, H * 0.8, W, H * 0.2);
    const limb = (x0, y0, a, l1, b, l2) => { const x1 = x0 + Math.sin(a) * l1, y1 = y0 + Math.cos(a) * l1; return [[x0, y0], [x1, y1], [x1 + Math.sin(a + b) * l2, y1 + Math.cos(a + b) * l2]]; };
    const parts = [limb(x, y, Math.sin(ph) * 0.6, 62, Math.max(0, -Math.sin(ph)) * 0.9, 62), limb(x, y, -Math.sin(ph) * 0.6, 62, Math.max(0, Math.sin(ph)) * 0.9, 62),
      limb(x, y - 112, -Math.sin(ph) * 0.7, 52, -0.5, 48), limb(x, y - 112, Math.sin(ph) * 0.7, 52, -0.5, 48)];
    const body = () => { g.beginPath(); g.moveTo(x - 26, y - 118); g.lineTo(x + 26, y - 118); g.lineTo(x + 18, y + 6); g.lineTo(x - 18, y + 6); g.closePath(); };
    for (let pass = 0; pass < 2; pass++) {
      g.lineCap = 'round'; g.lineJoin = 'round';
      const dx = pass ? 0 : jit(f, 1, 4), dy = pass ? 0 : jit(f, 2, 4);     // the colour field drifts off the line
      g.save(); g.translate(dx, dy);
      g.strokeStyle = pass ? '#f4f0e8' : '#e8643c'; g.lineWidth = pass ? 2.2 : 22;
      for (const [i, p] of parts.entries()) { g.beginPath(); p.forEach(([px, py], j) => { const qx = px + (pass ? jit(f, i * 9 + j, 2.2) : 0), qy = py + (pass ? jit(f, i * 9 + j + 40, 2.2) : 0); j ? g.lineTo(qx, qy) : g.moveTo(qx, qy); }); g.stroke(); }
      body(); pass ? g.stroke() : fill(g, '#f0b23c');
      g.beginPath(); g.arc(x + jit(f, 77, pass ? 1.5 : 0), y - 146 + Math.abs(Math.sin(ph)) * 5, 24, 0, TAU); pass ? g.stroke() : fill(g, '#f4d7b5');
      g.restore();
    }
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Rotoscoping>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
