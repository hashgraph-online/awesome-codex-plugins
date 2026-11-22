# Rubber-hose cartoon

Family: Drawn and painted. Cadence: steps 12 times a second. Usual tool: HyperFrames (canvas, SVG).

The 1920s cartoon: limbs like hoses with no elbows or knees, round bodies that bounce to the music, black and white film.

Credited to Bill Nolan on Felix the Cat. The Fleischer studio kept it longest; Cuphead revived it.

## What makes it read as this

- Curved tubular limbs
- Round forms
- Black and white or sepia, high contrast
- Film grain, scratches and a frame that weaves slightly
- Everything moves to the beat

## Timing

Bouncy loops locked to the music, on twos, with squash and stretch.

## How to build it

- A limb is a quadratic curve between two points; move the control point to bend it
- Squash and stretch: scale the body on one axis by the inverse of the other
- Grain: cycle a few noise tiles by frame; gate weave: shift the whole picture by a seeded pixel or two
- Sepia with `feColorMatrix` if wanted

## Assets

All in code. Original characters only. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Hot jazz, slide whistles, effects on every bounce. Practice note.

## What makes it look wrong

- Stiff jointed limbs
- Clean modern gradients
- Copying characters that are still under copyright

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=rubber-hose` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'rubber-hose': { kind: '2d', fps: 12, draw(g, t, W, H) {
    // limbs are curves with no elbows or knees; the body squashes and stretches on the beat; film grain and a weaving gate
    const f = frameOf(t, 12), ts = onTwos(t), beat = Math.abs(Math.sin(ts * Math.PI * 2)), sq = 1 + 0.16 * (beat - 0.5);
    bg(g, W, H, '#d9d2c0');
    g.save(); g.translate(jit(f, 1, 1.5), jit(f, 2, 1.5));                  // gate weave
    const x = W / 2, y = H * 0.56 - beat * 26;
    g.fillStyle = 'rgba(0,0,0,.25)'; g.beginPath(); g.ellipse(x, H * 0.84, 90 - beat * 20, 12, 0, 0, TAU); g.fill();
    g.strokeStyle = '#111'; g.lineWidth = 15; g.lineCap = 'round';
    const hose = (x0, y0, x1, y1, bend) => { g.beginPath(); g.moveTo(x0, y0); g.quadraticCurveTo((x0 + x1) / 2 + bend, (y0 + y1) / 2 + Math.abs(bend) * 0.4, x1, y1); g.stroke(); };
    hose(x - 30, y + 60, x - 62, H * 0.83, -40 * beat); hose(x + 30, y + 60, x + 62, H * 0.83, 40 * beat);
    hose(x - 62, y - 10, x - 150, y - 60 - beat * 50, -50 + beat * 70); hose(x + 62, y - 10, x + 150, y - 60 - (1 - beat) * 50, 50 - beat * 70);
    g.fillStyle = '#111'; g.beginPath(); g.ellipse(x, y, 78 / sq, 84 * sq, 0, 0, TAU); g.fill();
    g.fillStyle = '#f4efe2'; g.beginPath(); g.ellipse(x, y - 8, 54 / sq, 56 * sq, 0, 0, TAU); g.fill();
    for (const s of [-1, 1]) { g.fillStyle = '#111'; g.beginPath(); g.ellipse(x + s * 20, y - 22, 9, 15 * sq, 0, 0, TAU); g.fill(); g.fillStyle = '#f4efe2'; g.beginPath(); g.moveTo(x + s * 20, y - 22); g.arc(x + s * 20, y - 22, 9, -0.9, -0.3); g.fill(); }
    g.strokeStyle = '#111'; g.lineWidth = 5; g.beginPath(); g.arc(x, y + 6, 26, 0.15 * Math.PI, 0.85 * Math.PI); g.stroke();
    for (const s of [-1, 1]) { g.fillStyle = '#f4efe2'; g.strokeStyle = '#111'; g.lineWidth = 5; g.beginPath(); g.arc(x + s * 150, y - 60 - (s < 0 ? beat : 1 - beat) * 50, 22, 0, TAU); g.fill(); g.stroke(); g.fillStyle = '#111'; g.beginPath(); g.ellipse(x + s * 62, H * 0.84, 34, 15, 0, 0, TAU); g.fill(); }
    g.restore(); g.drawImage(grain(W, H, 20 + (f % 5), 50, [20, 20, 20]), 0, 0);
    g.fillStyle = `rgba(0,0,0,${0.5 * hash(f, 9)})`; g.fillRect(hash(f, 3) * W, 0, 1.5, H);   // a scratch
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Rubber_hose_animation>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
