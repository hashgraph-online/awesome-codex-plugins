# Indian miniature (Mughal and Rajput)

Also called: mughal painting, rajput painting, mughal miniature, pahari painting.

Family: Folk and print traditions. Cadence: steps 8 times a second. Usual tool: HyperFrames (canvas or SVG).

A small, richly detailed court painting in jewel tones: a flat, stacked space with no deep perspective, a gold border with a floral margin, fine ornament on every surface, and figures in profile. It is a living tradition with working artists; the demo here is a code study of its visual rules, not the craft itself, and a film should credit the tradition and, where it can, commission or license work from the artists.

Mughal painting is a style of miniature painting, used for book illustrations and album pages, that developed at the Mughal court between the 16th and 19th centuries; its portraits are normally in profile. Rajput painting is the painting of the regional Hindu courts during the Mughal era, from about the end of the 16th to the middle of the 19th century, and its conservative idioms keep bright colour, flatness and abstract form.

## What makes it read as this

- Flat, stacked space: sky, palace, terrace and garden as bands, no deep perspective
- Jewel tones: ruby, emerald, lapis, saffron and gold
- A gold border with a floral margin, drawn as part of the painting
- Figures in profile, small and seated, with turbans and robes
- Fine ornament: domes, arches, flower beds, water channels

## Timing

The border, the sky and the palace draw in over about 2 seconds, then the garden, water and figures. Birds drift and the fountain rises. The picture steps about 8 times a second.

## How to build it

- Paint bands from back to front, each a flat fill with a thin dark line
- Border: a ruby frame between gold lines with a row of small flowers (`rosette()`)
- Domes: half-ellipses with ribs, a finial and a small disc
- Figures: a robe polygon, a profile head with a nose notch, a turban ellipse and one arm to a cup
- Animate only small things: birds, the fountain, the cloud ribbons

## Assets

All in code. For real pages use public-domain scans from museum collections and say so in REPORT.md. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Sitar or santoor, a quiet fountain, birdsong. Practice note.

## What makes it look wrong

- Deep one-point perspective and cast shadows
- Photorealistic faces
- Presenting a machine-made picture as authentic Mughal or Rajput work

## Tested demo

This is the look from `art-forms/looks-folk.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=indian-miniature` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'indian-miniature': { kind: '2d', fps: 8, draw(g, t, W, H) {
    // a palace terrace in flat colour and jewel tones: a gold border with a floral margin, a pavilion with domes, a garden and a channel seen from above, two figures in profile on a rug
    const ts = held(t, 8), RUBY = '#a81f35', EMER = '#1f6a4a', LAP = '#27408b', GOLD = '#d6a21f', PINK = '#e7a79c', CREAM = '#f4e4c1';
    bg(g, W, H, GOLD); const k0 = easeOut(prog(ts, 0, 0.6)); g.lineJoin = 'round'; g.lineCap = 'round';
    g.fillStyle = RUBY; g.fillRect(24, 24, W - 48, H - 48); g.strokeStyle = INK; g.lineWidth = 1.6; g.strokeRect(24, 24, W - 48, H - 48); g.strokeRect(58, 58, W - 116, H - 116);
    for (let i = 0; i < 36 * k0; i++) { const x = 40 + i * ((W - 80) / 35); for (const y of [41, H - 41]) { rosette(g, x, y, 11, 5, GOLD, CREAM, i); g.fillStyle = EMER; g.beginPath(); g.ellipse(x + 13, y, 6, 2.6, 0, 0, TAU); g.fill(); } }
    for (let i = 0; i < 18 * k0; i++) { const y = 70 + i * ((H - 140) / 17); for (const x of [41, W - 41]) rosette(g, x, y, 11, 5, GOLD, CREAM, i); }
    g.save(); g.beginPath(); g.rect(62, 62, W - 124, H - 124); g.clip(); g.fillStyle = CREAM; g.fillRect(62, 62, W - 124, H - 124);
    const sk = g.createLinearGradient(0, 62, 0, 210); sk.addColorStop(0, '#f2c98a'); sk.addColorStop(1, '#fbecd0'); g.fillStyle = sk; g.fillRect(62, 62, W - 124, 150);
    for (let i = 0; i < 3; i++) { g.strokeStyle = i % 2 ? GOLD : '#fff'; g.lineWidth = 4; strokePart(g, Array.from({ length: 30 }, (_, j) => [62 + j * 31, 90 + i * 34 + Math.sin(j * 0.7 + i * 2 + ts * 0.8) * 7]), prog(ts, 0.4 + i * 0.1, 0.5)); }   // gold cloud ribbons, drifting
    disc(g, 150, 126, 24, GOLD, 1.6); for (let i = 0; i < 12; i++) { const a = (i / 12) * TAU; g.strokeStyle = GOLD; g.lineWidth = 3; g.beginPath(); g.moveTo(150 + Math.cos(a) * 32, 126 + Math.sin(a) * 32); g.lineTo(150 + Math.cos(a) * 44, 126 + Math.sin(a) * 44); g.stroke(); }
    const pk = prog(ts, 0.8, 1.0);
    if (pk > 0) {
      g.fillStyle = PINK; g.fillRect(62, 205, W - 124, 98); g.fillStyle = '#d9867c'; for (let x = 62; x < W - 62; x += 22) g.fillRect(x, 193, 12, 13);
      g.fillStyle = LAP; for (let x = 80; x < W - 80; x += 56) { g.beginPath(); g.moveTo(x - 12, 280); g.lineTo(x - 12, 244); g.arc(x, 244, 12, Math.PI, 0); g.lineTo(x + 12, 280); g.fill(); }
      g.fillStyle = '#e0a090'; g.fillRect(330, 150, 300, 154); g.strokeStyle = GOLD; g.lineWidth = 4; g.strokeRect(330, 150, 300, 154);
      for (const x of [400, 480, 560]) { g.fillStyle = LAP; g.beginPath(); g.moveTo(x - 30, 300); g.lineTo(x - 30, 215); g.arc(x, 215, 30, Math.PI, 0); g.lineTo(x + 30, 300); g.fill(); g.stroke(); g.fillStyle = RUBY; g.fillRect(x - 12, 262, 24, 38); }
      for (const [dx, dy, rx, ry, st] of [[480, 148, 76, 58, 1.0], [250, 152, 40, 32, 1.3], [710, 152, 40, 32, 1.3]]) { if (prog(ts, st, 0.5) <= 0) continue; g.fillStyle = GOLD; g.beginPath(); g.ellipse(dx, dy, rx, ry, 0, Math.PI, TAU); g.fill(); g.strokeStyle = INK; g.lineWidth = 1.6; g.stroke(); g.beginPath(); for (let i = -2; i <= 2; i++) { g.moveTo(dx, dy - ry); g.quadraticCurveTo(dx + i * rx * 0.55, dy - ry * 0.6, dx + i * rx * 0.45, dy); } g.stroke(); g.beginPath(); g.moveTo(dx, dy - ry); g.lineTo(dx, dy - ry - 22); g.stroke(); disc(g, dx, dy - ry - 22, 4, RUBY, 1.4); }
      for (const x of [250, 710]) { g.fillStyle = GOLD; g.fillRect(x - 40, 183, 80, 10); g.strokeStyle = INK; g.lineWidth = 3; g.beginPath(); for (const dx of [-30, -10, 10, 30]) { g.moveTo(x + dx, 183); g.lineTo(x + dx, 152); } g.stroke(); }
    }
    const gk = prog(ts, 1.8, 0.8);
    if (gk > 0) {
      g.fillStyle = EMER; g.fillRect(62, 303, W - 124, H - 365); g.strokeStyle = GOLD; g.lineWidth = 3; g.strokeRect(62, 303, W - 124, 4);
      for (let r = 0; r < 4; r++) for (let c = 0; c < 6; c++) { const x = 90 + c * 64 + (c > 2 ? 360 : 0), y = 320 + r * 36; if (c > 2 && r < 1) continue; g.fillStyle = '#2f8a5a'; g.fillRect(x, y, 54, 28); g.strokeStyle = GOLD; g.lineWidth = 1.4; g.strokeRect(x, y, 54, 28); for (let i = 0; i < 5; i++) disc(g, x + 8 + i * 9.5, y + 14 + (i % 2) * 5 - 2, 2.6, [RUBY, '#f0b429', '#f4e4c1'][(i + r + c) % 3]); }
    }
    if (prog(ts, 2.4, 0.6) > 0) { g.fillStyle = LAP; polyFill(g, [[440, 304], [520, 304], [570, H - 62], [390, H - 62]]); g.strokeStyle = '#fff'; g.lineWidth = 1.6; for (let i = 0; i < 6; i++) strokePart(g, Array.from({ length: 12 }, (_, j) => [412 + j * 12 + i * 4, 320 + i * 26 + Math.sin(j * 1.3 + ts * 2) * 3]), 1); for (let i = 0; i < 9; i++) disc(g, 480 + Math.sin(i * 2) * 8, 400 - ((ts * 40 + i * 14) % 90), 2, '#dff0ff'); }   // the channel, with a fountain
    for (const [x, y, st] of [[120, 380, 2.6], [190, 395, 2.7], [860, 385, 2.8]]) { if (prog(ts, st, 0.4) <= 0) continue; g.fillStyle = '#14472f'; g.beginPath(); g.moveTo(x, y - 110); g.quadraticCurveTo(x + 30, y - 30, x + 20, y); g.lineTo(x - 20, y); g.quadraticCurveTo(x - 30, y - 30, x, y - 110); g.fill(); dots(g, [x - 14, y - 90, x + 14, y - 4], 11, 1.6, GOLD); g.fillStyle = '#5b3a1e'; g.fillRect(x - 3, y, 6, 14); }
    if (prog(ts, 3.0, 0.5) > 0) {
      g.fillStyle = RUBY; g.fillRect(600, 384, 240, 66); g.strokeStyle = GOLD; g.lineWidth = 4; g.strokeRect(604, 388, 232, 58); dots(g, [612, 396, 828, 440], 18, 2.2, GOLD);
      const seated = (x, y, dir, robe, turb) => { g.fillStyle = robe; polyFill(g, [[x - 34, y], [x + 34, y], [x + 26, y - 30], [x + 14, y - 62], [x - 14, y - 62], [x - 26, y - 30]]); g.strokeStyle = INK; g.lineWidth = 1.6; g.stroke(); g.fillStyle = GOLD; g.fillRect(x - 24, y - 34, 48, 5); disc(g, x + dir * 4, y - 78, 13, '#e8b98a', 1.6); polyFill(g, [[x + dir * 16, y - 80], [x + dir * 24, y - 75], [x + dir * 16, y - 72]]); g.fillStyle = turb; g.beginPath(); g.ellipse(x + dir * 2, y - 92, 18, 10, 0, 0, TAU); g.fill(); g.stroke(); disc(g, x + dir * 9, y - 80, 2.2, INK); g.strokeStyle = INK; g.lineWidth = 3; strokePart(g, [[x + dir * 8, y - 56], [x + dir * 34, y - 44]], 1); disc(g, x + dir * 38, y - 44, 5, GOLD, 1.4); };
      seated(680, 424, 1, EMER, '#f0b429'); seated(770, 424, -1, LAP, RUBY);
    }
    for (let i = 0; i < 3; i++) { const x = 90 + ((ts * 38 + i * 260) % (W - 200)), y = 96 + i * 26 + Math.sin(ts * 2 + i) * 6; g.strokeStyle = INK; g.lineWidth = 2.2; strokePart(g, [[x - 10, y - 5], [x, y], [x + 10, y - 5]], prog(ts, 3.4, 0.3)); }
    g.restore(); speckle(g, W, H, 3, 34, [110, 70, 30]);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Mughal_painting>
- <https://en.wikipedia.org/wiki/Rajput_painting>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
