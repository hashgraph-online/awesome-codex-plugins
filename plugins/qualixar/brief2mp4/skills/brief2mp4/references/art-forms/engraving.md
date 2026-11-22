# Engraving and banknote hatching

Also called: banknote engraving, copperplate engraving, line engraving.

Family: Folk and print traditions. Cadence: smooth, full frame rate. Usual tool: HyperFrames (canvas).

Fine lines cut like a burin: hatching that follows the form and swells in the shadow, cross-hatching where it is darkest, a vignette of waves, and a woven guilloche frame, in one or two inks on cream paper.

Engraving is the practice of incising a design on a hard surface with a burin; the grooves can make an intaglio plate for printing. In traditional engraving, which is a purely linear medium, half-tones are made by many thin parallel lines, hatching, and two crossing sets of them are cross-hatching. Guilloché is a precise, repetitive pattern engraved by engine turning, and modern banknotes are almost always engraved.

## What makes it read as this

- Tone from line only: thin lines in the light, thick lines in the shadow
- Lines follow the form: curved round a sphere, not straight across it
- Cross-hatching only in the deepest shade
- A guilloche frame of interwoven waves and rosettes
- One or two inks: a dark brown-black and a burgundy on cream paper

## Timing

Lines are cut one after another from top to bottom over about 3 seconds, then the cross-hatching and frame. Full frame rate: an engraved line should not step.

## How to build it

- Sphere: sample points with latitude, longitude and a tilt, and a brightness from a light direction (`spherePoint()` in `looks-folk.js`)
- Stroke each short segment with a width of about `0.35 + 3.3 * (1 - brightness) ** 1.7`
- Cross-hatch: a second family of lines drawn only where brightness is under 0.4
- Guilloche: six sine waves in different phases across each side, and a rose curve at each corner
- Background vignette: horizontal wavy lines whose width grows toward the edge, clipped to an ellipse

## Assets

All in code. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A fine scratch under the line work, a quiet low tone. Practice note.

## What makes it look wrong

- Lines of one width: the swelling is the engraving
- Smooth gradients
- Straight hatching that ignores the form

## Tested demo

This is the look from `art-forms/looks-folk.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=engraving` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  engraving: { kind: '2d', fps: null, draw(g, t, W, H) {
    // a banknote-style engraving: a sphere cut in fine lines that follow its form and swell in the shadow, cross-hatched where it is darkest, in a vignette of waves inside a woven guilloche frame; two inks on cream
    const PAPER = '#f1ead6', I1 = '#20170e', I2 = '#7d1d2c', cx = 480, cy = 276, R = 120, tilt = 0.38; bg(g, W, H, PAPER); g.lineCap = 'butt'; g.lineJoin = 'round';
    g.save(); g.beginPath(); g.ellipse(cx, cy, 332, 208, 0, 0, TAU); g.clip(); g.strokeStyle = I2;
    for (let y = cy - 212, i = 0; y < cy + 212; y += 4.4, i++) { const e = (y - cy) / 208; g.lineWidth = 0.5 + 1.9 * e * e; strokePart(g, Array.from({ length: 58 }, (_, j) => [cx - 340 + j * 12, y + 2.6 * Math.sin(j * 0.26 + y / 23)]), prog(t, i * 0.005, 0.7)); }
    g.restore();
    g.strokeStyle = I1; g.lineWidth = 0.8; g.save(); g.beginPath(); g.ellipse(cx + 40, cy + R * 0.96, 150, 20, 0, 0, TAU); g.clip(); for (let y = cy + R * 0.7; y < cy + R * 1.3; y += 3) { g.beginPath(); g.moveTo(cx - 140, y); g.lineTo(cx + 230, y); g.stroke(); } g.restore();   // the cast shadow, ruled
    g.fillStyle = PAPER; g.beginPath(); g.arc(cx, cy, R + 4, 0, TAU); g.fill();
    const N = 30, M = 48;
    for (let i = 0; i < N; i++) {   // lines of latitude, drawn one after another; each segment is wider the darker the sphere is there
      const phi = -Math.PI / 2 + ((i + 0.5) / N) * Math.PI, shown = Math.floor(M * prog(t, 0.25 + i * 0.045, 0.5));
      for (let j = 0; j < shown; j++) { const a = spherePoint(phi, -Math.PI / 2 + (j / M) * Math.PI, R, cx, cy, tilt), b = spherePoint(phi, -Math.PI / 2 + ((j + 1) / M) * Math.PI, R, cx, cy, tilt); if (!a.vis || !b.vis) continue; g.lineWidth = 0.35 + 3.3 * (1 - (a.shade + b.shade) / 2) ** 1.7; g.beginPath(); g.moveTo(a.x, a.y); g.lineTo(b.x, b.y); g.stroke(); }
    }
    g.globalAlpha = prog(t, 2.6, 1); g.lineWidth = 0.7;
    for (let j = 0; j < 28; j++) { const lam = -Math.PI / 2 + ((j + 0.5) / 28) * Math.PI; for (let i = 0; i < 40; i++) { const a = spherePoint(-Math.PI / 2 + (i / 40) * Math.PI, lam, R, cx, cy, tilt), b = spherePoint(-Math.PI / 2 + ((i + 1) / 40) * Math.PI, lam, R, cx, cy, tilt); if (a.vis && b.vis && a.shade < 0.4 && b.shade < 0.4) { g.beginPath(); g.moveTo(a.x, a.y); g.lineTo(b.x, b.y); g.stroke(); } } }   // cross-hatching in the deepest shade
    g.globalAlpha = 1; g.lineCap = 'round';
    const kf = prog(t, 0.2, 1.4); g.strokeStyle = I2; for (const [ins, w] of [[12, 2.6], [18, 0.8], [54, 0.8], [60, 2.6]]) { g.lineWidth = w; strokePart(g, [[ins, ins], [W - ins, ins], [W - ins, H - ins], [ins, H - ins], [ins, ins]], kf); }
    g.lineWidth = 0.9;
    for (let p = 0; p < 6; p++) { const ph = (p * TAU) / 6; strokePart(g, Array.from({ length: 150 }, (_, i) => [74 + i * ((W - 148) / 149), 36 + 9 * Math.sin(i * 0.3 + ph)]), kf); strokePart(g, Array.from({ length: 150 }, (_, i) => [74 + i * ((W - 148) / 149), H - 36 + 9 * Math.sin(i * 0.3 + ph)]), kf); strokePart(g, Array.from({ length: 80 }, (_, i) => [36 + 9 * Math.sin(i * 0.3 + ph), 74 + i * ((H - 148) / 79)]), kf); strokePart(g, Array.from({ length: 80 }, (_, i) => [W - 36 + 9 * Math.sin(i * 0.3 + ph), 74 + i * ((H - 148) / 79)]), kf); }
    for (const [x, y] of [[36, 36], [W - 36, 36], [36, H - 36], [W - 36, H - 36]]) for (let c = 0; c < 4; c++) { g.strokeStyle = c % 2 ? I1 : I2; strokePart(g, Array.from({ length: 80 }, (_, i) => { const a = (i / 79) * TAU, r = 21 * (0.55 + 0.45 * Math.cos(7 * a + c * 0.45)); return [x + Math.cos(a + c * 0.2) * r, y + Math.sin(a + c * 0.2) * r]; }), kf); }
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Engraving>
- <https://en.wikipedia.org/wiki/Guilloch%C3%A9>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
