# Paint-on-glass

Also called: paint on glass animation, oil on glass, glass painting animation.

Family: Drawn and painted. Cadence: steps 12 times a second. Usual tool: HyperFrames (canvas).

Oil paint smeared on a lit sheet of glass: translucent colour that glows against the light, deeper where it is thick, finger streaks dragged behind, and shapes that melt from one thing into the next.

A technique for animated films made by manipulating slow-drying oil paints on sheets of glass; gouache mixed with glycerine is sometimes used instead. The best-known practitioner is the Russian animator Aleksandr Petrov, who has used it in seven films, all of which have won awards.

## What makes it read as this

- Translucent colour over a bright backlight: paint multiplies, so overlaps go darker
- A thicker, darker rim round each daub
- Finger streaks trailing behind moving shapes
- Lines scratched through the paint that let the light through
- One shape morphs into another instead of cutting

## Timing

One frame at a time, about 12 changes a second. The picture is smeared and re-pushed on each step, so streaks and edges move a little every frame.

## How to build it

- Draw the lamp as a radial gradient, then paint everything with `globalCompositeOperation = 'multiply'`
- Each daub: a filled shape, a darker rim stroke, and a dozen gradient-faded streaks (`daub()` in `looks-painted.js`), with streak lengths re-seeded on each step
- Morph by interpolating the shape parameters (size, angle, colour) with `easeInOut`
- Scratches: switch to `source-over` and draw thin cream lines clipped to the shape

## Assets

All in code. Real glass-paint scans work as a texture layer over the lamp. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A wet, squelching foley on every move, a slow and dreamy bed. Practice note.

## What makes it look wrong

- Opaque colour, which loses the glow
- Sharp vector outlines round the shapes
- Cuts between forms: the look depends on continuous morphing

## Tested demo

This is the look from `art-forms/looks-painted.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=paint-on-glass` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'paint-on-glass': { kind: '2d', fps: 12, draw(g, t, W, H) {
    // oil paint smeared on a lit sheet of glass: colour that glows against the lamp, deeper at the rims, finger streaks dragged behind, a fish that melts into a bird
    const ts = held(t, 12), f = frameOf(t, 12), m = easeInOut(prog(ts, 1.2, 2.2)), x = lerp(W * 0.38, W * 0.58, easeInOut(prog(ts, 0, 4.5))), y = H * 0.56 - m * 70 + Math.sin(ts * 3) * 7;
    bg(g, W, H, '#2a1a10'); const lamp = g.createRadialGradient(W / 2, H / 2, 40, W / 2, H / 2, W * 0.62); lamp.addColorStop(0, '#fff6d6'); lamp.addColorStop(0.62, '#f6c96c'); lamp.addColorStop(1, '#7a4514'); g.fillStyle = lamp; g.fillRect(0, 0, W, H);
    g.globalCompositeOperation = 'multiply';
    [[W * 0.25, H * 0.95, 380, [40, 80, 190]], [W * 0.85, H * 0.1, 330, [215, 70, 120]]].forEach(([wx, wy, r, c]) => { const wash = g.createRadialGradient(wx, wy, 10, wx, wy, r); wash.addColorStop(0, rgba(c, 0.5)); wash.addColorStop(1, rgba(c, 0)); g.fillStyle = wash; g.fillRect(0, 0, W, H); });
    for (let j = 0; j < 7; j++) { const ly = 60 + j * 70 + jit(f, j, 4); g.strokeStyle = rgba([60, 90, 200], 0.07); g.lineWidth = 12 + hash(j, 2) * 14; g.beginPath(); g.moveTo(-20, ly); g.quadraticCurveTo(W / 2, ly + jit(f, j + 9, 14) + 24, W + 20, ly - 20); g.stroke(); }
    g.translate(x, y); g.rotate(-m * 0.28);
    daub(g, () => { g.beginPath(); for (const s of [-1, 1]) g.ellipse(168, s * 36 * (1 - m * 0.55), 66, 25, s * (0.75 - 0.4 * m), 0, TAU); }, [214, 50, 112], [120, -60, 230, 60], f, 5, 0.72);   // tail: a fork that folds into a fan
    daub(g, () => { g.beginPath(); g.ellipse(0, 0, 132, 58, 0, 0, TAU); }, mix([238, 128, 28], [44, 92, 214], m), [-120, -50, 110, 50], f, 3);
    daub(g, () => { g.beginPath(); g.ellipse(14 + m * 20, -50 - m * 40, 62 + m * 46, 22 + m * 12, lerp(-0.25, -0.9, m) + Math.sin(ts * 8) * 0.28 * m, 0, TAU); }, mix([246, 200, 42], [130, 60, 208], m), [-50, -130, 90, -40], f, 7, 0.7);   // fin, then a flapping wing
    daub(g, () => { g.beginPath(); g.ellipse(-8, 44, 40, 14, 0.5, 0, TAU); }, [224, 70, 120], [-50, 30, 30, 60], f, 9, 0.6);
    if (m > 0.05) daub(g, () => { g.beginPath(); g.moveTo(-126, -14); g.lineTo(-126 - 58 * m, 2); g.lineTo(-126, 18); g.closePath(); }, [240, 150, 30], [-190, -10, -126, 14], f, 11, 0.85);   // a beak grows
    g.globalCompositeOperation = 'source-over'; g.fillStyle = 'rgba(30,14,6,.9)'; g.beginPath(); g.arc(-100, -14, 8, 0, TAU); g.fill(); g.fillStyle = 'rgba(255,248,225,.9)'; g.beginPath(); g.arc(-97, -17, 2.6, 0, TAU); g.fill();
    g.save(); g.beginPath(); g.ellipse(0, 0, 130, 56, 0, 0, TAU); g.clip(); g.strokeStyle = 'rgba(255,244,205,.8)'; g.lineWidth = 2.2; g.lineCap = 'round';   // lines scratched through the paint: scales, then feathers
    for (let i = 0; i < 8; i++) { const x0 = -92 + i * 28, k = prog(ts, 0.5 + i * 0.1, 0.3); if (k > 0) { g.beginPath(); g.moveTo(x0, -54); g.quadraticCurveTo(x0 + 20 + m * 16, -4, x0 + 4 + m * 30, 56 * k); g.stroke(); } }
    g.strokeStyle = 'rgba(255,255,255,.38)'; g.lineWidth = 8; g.beginPath(); g.ellipse(0, 0, 112, 40, 0, Math.PI * 1.12, Math.PI * 1.55); g.stroke(); g.restore();
    g.setTransform(1, 0, 0, 1, 0, 0); g.strokeStyle = 'rgba(255,245,210,.7)'; g.lineWidth = 2.5;
    for (let i = 0; i < 4; i++) { const bx = x - 180 - i * 46 + Math.sin(ts * 2 + i) * 6, by = y - 40 - ((ts * 28 + i * 40) % 160) * (1 - m * 0.4); g.beginPath(); g.arc(bx, by, 7 + i * 3, 0, TAU); g.stroke(); }
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Paint-on-glass_animation>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
