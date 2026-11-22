# String puppet and kathputli

Also called: kathputli, marionette, string puppets, puppet on strings.

Family: Craft and handmade. Cadence: steps 8 times a second. Usual tool: HyperFrames (canvas or SVG).

Marionettes in bright Rajasthani dress: big painted wooden heads, turbans and ghagras, strings to a control bar at the top, jerky dangling motion, in a small theatre with red curtains and a gold valance. It is a living tradition with working artists; the demo here is a code study of its visual rules, not the craft itself.

Kathputli is a string puppet theatre native to Rajasthan, India, and the most popular form of Indian puppetry; the name means a wooden doll, and the puppets are made of wood, cotton cloth and metal wire. A marionette, or string puppet, is controlled from above using wires or strings and a controller; puppetry is recorded in Ancient Greece in the 5th century BC.

Sourcing note: Wikipedia describes the Kathputli as worked by a single string over the puppeteer; the demo uses a Western-style control bar, with strings to the head, hands and feet, so that the strings are easy to read. Check a real rig before a film shows one.

## What makes it read as this

- A large, painted head with big eyes, strong brows and a moustache for the king, a veil and nose ring for the dancer
- Bright costume: red turban and yellow tunic, a pink and orange gathered skirt with gold trim
- Strings run straight from a bar at the top to the head, hands and feet
- Jerky, swinging limbs, as if on strings, with the whole puppet swaying
- A small stage with red curtains, a gold valance and a plank floor

## Timing

The limbs swing on twos, about 8 changes a second, each with its own phase, and the bar tilts slowly.

## How to build it

- Compute each hand and foot from a swinging angle (`puppet()` in `looks-toon.js`), then draw the strings from the bar anchors to those points first
- Body parts as polygons and strokes in local coordinates, with an outline
- Stage: stripes, an arch, two curtain drapes with gold fringe and a scalloped valance
- Use stepped time `held(t, 8)` so the motion is jerky

## Assets

All in code. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Dholak and harmonium, folk song, the wooden clack of puppets. Practice note.

## What makes it look wrong

- Smooth, floaty limbs: marionettes swing and stop
- Strings that do not reach the limbs
- Presenting a machine-made picture as an authentic kathputli show

## Tested demo

This is the look from `art-forms/looks-toon.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=string-puppet` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'string-puppet': { kind: '2d', fps: 8, draw(g, t, W, H) {
    // kathputli marionettes in bright Rajasthani dress: a king and a dancer hang from a control bar by strings and swing jerkily, in a small theatre with red curtains and a gold valance
    const ts = held(t, 8), barY = 54, tilt = Math.sin(ts * 1.3) * 0.05; bg(g, W, H, '#e8b53a');
    g.fillStyle = '#d99a22'; for (let i = 0; i < 20; i++) g.fillRect(i * 50, 0, 25, H); polyFill(g, [[300, 470], [300, 200], [480, 100], [660, 200], [660, 470]], '#c0392b', '#7a1f18', 6); polyFill(g, [[330, 470], [330, 210], [480, 128], [630, 210], [630, 470]], '#f3d77a', '#c99a0f', 4);
    for (let i = 0; i < 12; i++) disc(g, 340 + i * 25, 470 - 8, 4, '#c0392b'); g.fillStyle = '#6b3b1f'; g.fillRect(0, 440, W, 100); g.fillStyle = '#8a4e28'; for (let i = 0; i < 8; i++) g.fillRect(i * 125, 440, 3, 100);
    g.save(); g.translate(480, barY); g.rotate(tilt); g.fillStyle = '#5b3a1e'; g.fillRect(-190, -7, 380, 14); disc(g, -190, 0, 9, '#8a5a2b'); disc(g, 190, 0, 9, '#8a5a2b'); g.restore();
    for (const [x, hy, kind, ph] of [[410, 172, 'king', 0], [570, 176, 'dancer', 2]]) { g.save(); g.translate(x, barY); g.scale(1.3, 1.3); g.translate(-x, -barY); puppet(g, x, hy, kind, ph, ts, barY); g.restore(); }
    for (const side of [-1, 1]) { g.save(); g.translate(side > 0 ? W : 0, 0); g.scale(side, 1); for (let i = 0; i < 6; i++) { polyFill(g, [[i * 40, 0], [i * 40 + 40, 0], [i * 40 + 34 - (5 - i) * 4, 480], [i * 40 + 4 - (5 - i) * 4, 480]], i % 2 ? '#8a1722' : '#a8222c'); } g.fillStyle = '#f5c542'; g.fillRect(0, 470, 240, 10); for (let i = 0; i < 24; i++) g.fillRect(i * 10 + 2, 480, 3, 14); g.restore(); }
    g.fillStyle = '#a8222c'; g.fillRect(0, 0, W, 34); for (let i = 0; i < 20; i++) { g.beginPath(); g.arc(i * 50 + 25, 34, 25, 0, Math.PI); g.fill(); g.strokeStyle = '#f5c542'; g.lineWidth = 4; g.stroke(); }
    g.fillStyle = '#f5c542'; g.fillRect(0, 28, W, 6);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Kathputli_(puppetry)>
- <https://en.wikipedia.org/wiki/Marionette>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
