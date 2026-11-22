# Sand animation

Also called: sand art, sand drawing, sand painting animation.

Family: Drawn and painted. Cadence: steps 12 times a second. Usual tool: HyperFrames (canvas).

A light table seen from above: a warm glowing backlight, sand as dark sepia masses, and light showing through wherever the sand is thin, with soft graded edges. The picture is made of filled shapes, and one shape is pushed into the next.

A form of stop motion in which sand is shaped under a camera, often lit from behind by a lightbox so that the thickness of the sand gives shading and lines. Sand art is older than film: Navajo, Aboriginal Australian and Tibetan cultures made it, and the Japanese bonseki has been practised since at least the 7th century. Swiss animators Gisèle and Nag Ansorge and the American Caroline Leaf took it up for films in the 1960s.

## What makes it read as this

- A bright, warm backlight, strongest at the centre and falling off at the edges
- Sand is dark sepia to near-black where it is thick; bright where there is no sand; amber and soft where it is thin
- Filled masses with soft, graded edges, never outlines
- One form flows into the next as a hand sweeps the sand: sun to flower to bird
- Loose grains: dark specks on the light, bright pinholes in the dark masses

## Timing

A figure grows in over about a second, then each change of form takes about 1.3 seconds. The picture steps about 12 times a second.

## How to build it

- Paint the table as a radial gradient from pale cream to amber to brown
- Describe each figure as the same number of soft ellipses (position, size, angle); blend two figures number by number with `easeInOut` to morph (`SAND_SUN`, `SAND_FLOWER`, `SAND_BIRD` in `looks-painted.js`)
- Draw each mass three times with `filter: blur()`: a wide amber halo, a mid brown body, a dark core (`sandMass()`)
- Heap a few dark grains at the edge while a shape is moving
- Finish with dark and light speckle and a multiplied vignette

## Assets

All in code. Real sand photographed on a light table makes a good grain layer. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A soft, dry, whispering rub as the sand moves, a slow music bed that suits a story. Practice note.

## What makes it look wrong

- Bright outlines drawn on a dark ground: that reads as lines scratched in beach sand, not as sand on a light table
- A flat brown background with no backlight glow
- Hard-edged vector shapes: the edges of sand are soft and graded

## Tested demo

This is the look from `art-forms/looks-painted.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=sand-art` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'sand-art': { kind: '2d', fps: 12, draw(g, t, W, H) {
    // a light table seen from above: a warm backlight, sand as dark sepia masses with soft graded edges, light coming through where it is thin. A sun is pushed into a flower, then the flower into a bird
    const ts = held(t, 12), f = frameOf(t, 12), m1 = easeInOut(prog(ts, 1.0, 1.3)), m2 = easeInOut(prog(ts, 2.6, 1.3)), R = 104 * easeOut(prog(ts, 0.05, 0.8)), cx = W / 2, cy = H * 0.44;
    bg(g, W, H, '#fff0c4'); const lamp = g.createRadialGradient(W / 2, H * 0.45, 30, W / 2, H * 0.45, W * 0.62); lamp.addColorStop(0, '#fff6d2'); lamp.addColorStop(0.6, '#f6c25e'); lamp.addColorStop(1, '#b8661c'); g.fillStyle = lamp; g.fillRect(0, 0, W, H);
    const gy = lerp(H * 1.06, H * 0.86, easeOut(prog(ts, 0.05, 1)));   // a bank of sand along the bottom
    for (const [blur, style, dy] of [[22, 'rgba(120,58,12,.3)', -14], [10, 'rgba(60,28,6,.6)', -4], [4, 'rgba(26,11,3,.95)', 0]]) { g.filter = `blur(${blur}px)`; g.fillStyle = style; g.beginPath(); g.moveTo(-40, H + 40); g.lineTo(-40, gy + dy); g.bezierCurveTo(W * 0.25, gy + dy - 26, W * 0.4, gy + dy + 14, W * 0.55, gy + dy - 6); g.bezierCurveTo(W * 0.72, gy + dy - 24, W * 0.88, gy + dy + 10, W + 40, gy + dy - 8); g.lineTo(W + 40, H + 40); g.fill(); }
    g.filter = 'none';
    g.save(); g.translate(cx, cy);
    sandMass(g, blendShapes(blendShapes(SAND_SUN, SAND_FLOWER, m1), SAND_BIRD, m2), R);
    const stem = easeOut(prog(m1, 0.2, 0.8)) * (1 - m2), top = R * 0.95, bottom = gy - cy + 20;   // the stem and leaves grow with the flower and are swept away for the bird
    if (stem > 0.01) { g.filter = 'blur(4px)'; g.strokeStyle = 'rgba(26,11,3,.95)'; g.lineWidth = 13; g.lineCap = 'round'; g.beginPath(); g.moveTo(0, top); g.quadraticCurveTo(-8, lerp(top, bottom, 0.5), 3, lerp(top, bottom, stem)); g.stroke(); g.fillStyle = 'rgba(26,11,3,.95)'; for (const s of [-1, 1]) { g.beginPath(); g.ellipse(s * 52 * stem, lerp(top, bottom, 0.55) - 18 * stem, 52 * stem, 15 * stem, -s * 0.5, 0, TAU); g.fill(); } g.filter = 'none'; }
    const eye = m1 * (1 - m2); if (eye > 0.02) { g.filter = 'blur(3px)'; g.fillStyle = `rgba(255,236,170,${0.9 * eye})`; g.beginPath(); g.arc(0, 0, 0.2 * R, 0, TAU); g.fill(); g.filter = 'none'; }   // the flower's core is thin sand: light shows through
    const push = 4 * (m1 * (1 - m1) + m2 * (1 - m2));   // grains heaped along the edge while the sand is being swept
    for (let i = 0; i < 46 * push; i++) { const a = hash(i, f) * TAU, r = R * (0.9 + hash(i, f, 1) * 0.6); g.fillStyle = `rgba(30,13,4,${0.4 + hash(i, 2) * 0.5})`; g.beginPath(); g.arc(Math.cos(a) * r, Math.sin(a) * r * 0.85, 1.4 + hash(i, f, 3) * 2.4, 0, TAU); g.fill(); }
    g.restore();
    speckle(g, W, H, 41, 70, [50, 24, 6]); speckle(g, W, H, 42, 90, [255, 226, 150]);   // loose grains: dark on the light, bright pinholes in the dark
    g.save(); g.globalCompositeOperation = 'multiply'; const v = g.createRadialGradient(W / 2, H / 2, H * 0.32, W / 2, H / 2, H * 0.98); v.addColorStop(0, 'rgba(255,255,255,0)'); v.addColorStop(1, 'rgba(70,32,0,.5)'); g.fillStyle = v; g.fillRect(0, 0, W, H); g.restore();
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Sand_animation>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
