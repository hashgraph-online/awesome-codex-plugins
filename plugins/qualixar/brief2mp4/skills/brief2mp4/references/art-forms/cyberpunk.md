# Cyberpunk night city

Also called: cyberpunk, neon noir city.

Family: Screens and cinema. Cadence: steps 12 times a second. Usual tool: HyperFrames (canvas or Three.js).

A rainy night street in purple and amber: towers hung with flickering neon signs, a wet road that mirrors them, rain and ripples, and a lone figure under an umbrella.

Cyberpunk is a subgenre of science fiction set in a dystopian future, characterised by a focus on "lowlife and high tech". William Gibson's 1984 novel Neuromancer helped solidify the genre, and the 1982 film Blade Runner is among its early films.

Sourcing note: Wikipedia describes the genre in fiction; the look rules (rain, wet reflections, signs) are a practice summary of how it is usually pictured.

## What makes it read as this

- Night, rain and haze, in purple with amber windows and neon accents
- Neon signs on towers: bars, arrows and rings in magenta, amber and violet, with glow
- A wet road that reflects the lights, softened by a blur
- Rain streaks and ripples on the ground
- Signs that flicker now and then, keyed to the frame number

## Timing

Drawn on twos, 12 changes a second: rain falls, signs flicker and ripples spread.

## How to build it

- Draw the city to an off-screen canvas, then draw it again flipped below the horizon with `globalAlpha` 0.4 and `blur()` for the reflection
- Signs: a stroked shape with `shadowBlur`, hidden on a few frames from a modulo of `frameOf(t, 12)`
- Rain: slanted short lines with seeded positions and speeds; ripples: ellipses that grow and fade
- Add a haze gradient near the horizon and a vignette

## Assets

All in code. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A low synth drone, rain, distant traffic and a hum from the signs. Practice note.

## What makes it look wrong

- Daylight or flat lighting
- A dry road with no reflection
- Teal and orange only: this skill leaves teal out; keep to purple, amber and magenta

## Tested demo

This is the look from `art-forms/looks-screen.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=cyberpunk` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  cyberpunk: { kind: '2d', fps: 12, draw(g, t, W, H) {
    // a rainy night street in purple and amber: towers hung with flickering neon signs, a wet road that mirrors them, and a figure under an umbrella
    const ts = held(t, 12), f = frameOf(t, 12), sc = new OffscreenCanvas(W, H), c = sc.getContext('2d'), sky = c.createLinearGradient(0, 0, 0, 380); sky.addColorStop(0, '#14061f'); sky.addColorStop(1, '#4a1a66'); c.fillStyle = sky; c.fillRect(0, 0, W, H);
    const tower = (x, w, top, col, win, seed) => { c.fillStyle = col; c.fillRect(x, top, w, 400 - top); for (let wy = top + 14; wy < 380; wy += 18) for (let wx = x + 8; wx < x + w - 8; wx += 14) if (hash(wx | 0, wy | 0, seed) > 0.55) { c.fillStyle = hash(wx | 0, wy | 0, seed + 1) > 0.7 ? '#a855f7' : win; c.fillRect(wx, wy, 6, 9); } };
    for (let x = 250; x < 720; x += 46) tower(x, 40, 150 + hash(x, 1) * 120, '#2a0f45', '#ffb347', 3);
    tower(120, 130, 90, '#150a24', '#ffb347', 5); tower(650, 160, 70, '#150a24', '#ffb347', 6); tower(0, 150, 20, '#0d0616', '#ffb347', 7); tower(810, 150, 40, '#0d0616', '#ffb347', 8);
    const sign = (i, x, y, w, h, col, kind) => { if ((f + i * 7) % 23 < 2) return; c.save(); c.strokeStyle = col; c.shadowColor = col; c.shadowBlur = 18; c.lineWidth = 5; c.lineJoin = 'round'; if (kind === 0) { c.strokeRect(x, y, w, h); for (let k = 1; k < 5; k++) { c.beginPath(); c.moveTo(x + 6, y + k * h / 5); c.lineTo(x + w - 6 - (k % 2) * 12, y + k * h / 5); c.stroke(); } } else if (kind === 1) { c.beginPath(); c.arc(x + w / 2, y + w / 2, w / 2, 0, TAU); c.stroke(); c.beginPath(); c.moveTo(x + w * 0.25, y + w / 2); c.lineTo(x + w * 0.75, y + w / 2); c.stroke(); } else { c.beginPath(); c.moveTo(x, y + h / 2); c.lineTo(x + w * 0.65, y + h / 2); c.lineTo(x + w * 0.65, y); c.lineTo(x + w, y + h / 2); c.lineTo(x + w * 0.65, y + h); c.lineTo(x + w * 0.65, y + h / 2); c.stroke(); } c.restore(); };
    sign(0, 40, 120, 46, 230, '#ff2e97', 0); sign(1, 170, 300, 120, 50, '#ffb02e', 2); sign(2, 880, 160, 44, 200, '#9b5cff', 0); sign(3, 690, 250, 80, 80, '#ff2e97', 1); sign(4, 300, 120, 90, 36, '#ffb02e', 2);
    g.drawImage(sc, 0, 0);
    g.fillStyle = '#0f0a18'; g.beginPath(); g.moveTo(0, 400); g.lineTo(W, 400); g.lineTo(W, H); g.lineTo(0, H); g.fill();
    g.save(); g.beginPath(); g.rect(0, 400, W, H - 400); g.clip(); g.globalAlpha = 0.42; g.filter = 'blur(3px)'; g.translate(0, 800); g.scale(1, -1); g.drawImage(sc, 0, 60, W, 340, 0, 60, W, 340); g.restore(); g.filter = 'none';
    const wet = g.createLinearGradient(0, 400, 0, H); wet.addColorStop(0, 'rgba(10,5,20,0)'); wet.addColorStop(1, 'rgba(10,5,20,.7)'); g.fillStyle = wet; g.fillRect(0, 400, W, H - 400);
    g.fillStyle = '#05030a'; g.beginPath(); g.ellipse(520, 470, 30, 8, 0, 0, TAU); g.fill(); g.beginPath(); g.moveTo(502, 470); g.lineTo(506, 410); g.lineTo(534, 410); g.lineTo(538, 470); g.fill(); ell(g, 520, 402, 14, 14, '#05030a'); g.beginPath(); g.ellipse(520, 372, 66, 34, 0, Math.PI, 0); g.fill(); g.strokeStyle = '#ffb347'; g.lineWidth = 2; g.beginPath(); g.ellipse(520, 372, 66, 34, 0, Math.PI * 1.1, Math.PI * 1.9); g.stroke(); g.lineWidth = 3; g.beginPath(); g.moveTo(520, 372); g.lineTo(520, 410); g.stroke();   // the umbrella and the figure
    for (let i = 0; i < 150; i++) { const x = (hash(i, 1) * W + ts * 60) % W, y = (hash(i, 2) * H + ts * 1100 * (0.7 + hash(i, 3) * 0.6)) % H; g.strokeStyle = `rgba(210,190,255,${0.15 + hash(i, 4) * 0.25})`; g.lineWidth = 1.2; g.beginPath(); g.moveTo(x, y); g.lineTo(x - 5, y + 26); g.stroke(); }
    for (let i = 0; i < 9; i++) { const r = ((ts * 1.6 + hash(i, 5)) % 1); g.strokeStyle = `rgba(255,200,140,${0.4 * (1 - r)})`; g.lineWidth = 1.4; g.beginPath(); g.ellipse(100 + hash(i, 6) * 760, 430 + hash(i, 7) * 100, r * 26, r * 7, 0, 0, TAU); g.stroke(); }
    const haze = g.createLinearGradient(0, 330, 0, 420); haze.addColorStop(0, 'rgba(160,70,210,0)'); haze.addColorStop(1, 'rgba(160,70,210,.28)'); g.fillStyle = haze; g.fillRect(0, 330, W, 90); vignette(g, W, H, 0.5);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Cyberpunk>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
