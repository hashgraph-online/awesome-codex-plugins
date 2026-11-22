# Silent film

Also called: silent movie, silent era, intertitle.

Family: Screens and cinema. Cadence: steps 18 times a second. Usual tool: HyperFrames (canvas), or ffmpeg filters on real footage.

Black and white at about 18 frames a second: grain, scratches, a wandering gate, flicker, an iris that opens and closes on a street scene, and an intertitle card with a framed title.

A silent film is a film without synchronised recorded sound, whose plot or key lines are conveyed by intertitles when necessary. The silent era ran from the 1890s to the 1920s in most countries, and films were almost always accompanied by live music from a pianist, an organist or an orchestra.

## What makes it read as this

- Black and white only, with a soft vignette
- A slow frame rate: about 18 changes a second
- Gate weave: the frame wanders a few pixels, with now and then a jump
- Flicker, grain, vertical scratches and dust specks
- An iris in and out, and a framed intertitle card in a serif capital face

## Timing

The iris opens in 0.6 seconds, the scene plays, the iris closes at about 2.1 seconds, and the intertitle holds. Drawn at 18 changes a second.

## How to build it

- Quantise time with `frameOf(t, 18)`; translate the whole frame by a seeded jitter
- Iris: clip to a circle whose radius grows or shrinks with `easeOut` and `easeInOut`
- Film damage keyed to the frame: scratches that last two frames, dust, hairs and flicker (`filmDamage()` in `looks-screen.js`)
- Intertitle: black card, a double white border and a serif title
- Draw only in greys

## Assets

All in code. Real footage can be graded with a black-and-white filter and given the same damage. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A piano or a small orchestra improvising, a projector whirr. Practice note.

## What makes it look wrong

- Smooth 24 frames-a-second motion
- A clean, steady picture
- Sound effects: the era was accompanied by music

## Tested demo

This is the look from `art-forms/looks-screen.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=silent-film` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'silent-film': { kind: '2d', fps: 18, draw(g, t, W, H) {
    // black and white at 18 frames a second: an iris opens on a man in a bowler hat walking past a street lamp, the gate wanders, the light flickers and the print is scratched; then an iris closes and an intertitle card appears
    const f = frameOf(t, 18), ts = f / 18; g.fillStyle = '#000'; g.fillRect(0, 0, W, H);
    if (ts < 2.75) {
      const R = 660 * easeOut(prog(ts, 0, 0.6)) * (1 - easeInOut(prog(ts, 2.1, 0.6))); g.save(); g.translate(jit(f, 1, 2.6), jit(f, 2, 2) + (hash(f >> 2, 3) > 0.97 ? 7 : 0));
      g.beginPath(); g.arc(480, 270, Math.max(0, R), 0, TAU); g.clip(); const sky = g.createLinearGradient(0, 0, 0, 400); sky.addColorStop(0, gray(215)); sky.addColorStop(1, gray(150)); g.fillStyle = sky; g.fillRect(0, 0, W, H);
      for (let i = 0; i < 12; i++) { const x = i * 90 - 20, hh = 120 + hash(i, 1) * 160; g.fillStyle = gray(110); g.fillRect(x, 400 - hh, 76, hh); } for (let i = 0; i < 9; i++) { const x = i * 120 + 10, hh = 170 + hash(i, 2) * 120; g.fillStyle = gray(52); g.fillRect(x, 410 - hh, 100, hh); for (let wy = 410 - hh + 14; wy < 390; wy += 26) for (let wx = x + 12; wx < x + 88; wx += 24) { g.fillStyle = hash(wx | 0, wy | 0, 3) > 0.5 ? gray(225) : gray(30); g.fillRect(wx, wy, 11, 15); } }
      g.fillStyle = gray(38); g.fillRect(0, 400, W, 140); g.fillStyle = gray(70); for (let i = 0; i < 14; i++) g.fillRect(i * 80 - ((ts * 60) % 80), 470, 46, 6);
      g.fillStyle = '#111'; g.fillRect(768, 150, 8, 260); ell(g, 772, 144, 18, 14, gray(250)); const wx = lerp(-40, 1000, ts / 2.6), wk = Math.sin(f * 0.95), by = 350 - Math.abs(wk) * 6;
      g.strokeStyle = '#050505'; g.lineWidth = 15; g.lineCap = 'round'; for (const d of [-1, 1]) { g.beginPath(); g.moveTo(wx + d * 6, by + 26); g.lineTo(wx + d * 6 + d * wk * 24, by + 100); g.stroke(); } g.fillStyle = '#050505'; g.beginPath(); g.moveTo(wx - 24, by + 34); g.lineTo(wx + 24, by + 34); g.lineTo(wx + 20, by - 40); g.lineTo(wx - 20, by - 40); g.fill();
      g.lineWidth = 10; g.beginPath(); g.moveTo(wx + 18, by - 30); g.lineTo(wx + 40 - wk * 8, by + 10); g.stroke(); g.lineWidth = 4; g.beginPath(); g.moveTo(wx + 40 - wk * 8, by + 10); g.lineTo(wx + 56, by + 100); g.stroke(); ell(g, wx, by - 62, 17, 19, gray(235)); ell(g, wx, by - 82, 22, 6, '#050505'); g.fillRect(wx - 14, by - 100, 28, 20); g.fillStyle = '#111'; g.fillRect(wx - 7, by - 52, 14, 3);
      g.restore();
    } else {
      g.fillStyle = '#0a0a0a'; g.fillRect(0, 0, W, H); g.strokeStyle = gray(235); g.lineWidth = 6; g.strokeRect(46, 46, W - 92, H - 92); g.lineWidth = 2; g.strokeRect(64, 64, W - 128, H - 128); for (const [x, y] of [[80, 80], [W - 80, 80], [80, H - 80], [W - 80, H - 80]]) { g.beginPath(); g.arc(x, y, 14, 0, TAU); g.stroke(); }
      g.fillStyle = gray(240); g.textAlign = 'center'; g.font = '700 58px Georgia, "Times New Roman", serif'; g.fillText('AND SO, ONE FINE', W / 2, 240); g.fillText('MORNING . . .', W / 2, 316); g.fillRect(380, 350, 200, 3); g.textAlign = 'left';
    }
    vignette(g, W, H, 0.55, 0.4); filmDamage(g, W, H, f, { grain: 52 }); g.fillStyle = `rgba(0,0,0,${0.08 * hash(f, 20)})`; g.fillRect(0, 0, W, H);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Silent_film>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
