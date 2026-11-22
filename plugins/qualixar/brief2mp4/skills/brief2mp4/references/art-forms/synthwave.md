# Synthwave and outrun

Also called: outrun, retrowave, synthwave.

Family: Screens and cinema. Cadence: smooth, full frame rate. Usual tool: HyperFrames (canvas or Three.js).

A neon night in magenta and cyan on deep purple: a striped sun sinking behind wireframe mountains, and a glowing grid floor that streams toward the horizon.

Synthwave, also called retrowave or futuresynth, is an electronic music microgenre based mainly on the music of action, science-fiction and horror film soundtracks of the 1970s and 1980s, and drawing on the decade's art and video games; it developed in the mid-to-late 2000s.

Sourcing note: The source describes the music genre; the neon grid and striped sun are the visual conventions that go with it, described here as practice.

## What makes it read as this

- A deep purple sky graded to hot pink at the horizon
- A big sun with horizontal slits, in yellow to orange to magenta
- A neon grid floor: lines that converge to a vanishing point and rows that bunch toward the horizon
- Wireframe mountains outlined in cyan
- Glow on every line, a bright horizon line, and a field of stars

## Timing

The grid rows stream toward the camera continuously and the sun's slits creep down; smooth, full frame rate.

## How to build it

- Floor rows: `y = horizon + (H - horizon) * ((k + phase) / n) ** 2.3`, with `phase` from time so the rows flow; columns are straight lines from the vanishing point
- Glow: stroke twice with `shadowBlur`, a wide coloured pass and a thin white core (`neon()` in `looks-screen.js`)
- Sun: a clipped disc with a vertical gradient and bars of the sky colour whose thickness grows toward the bottom
- Use magenta and cyan only for lines: no mint

## Assets

All in code. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A pulsing analogue synth bass, gated reverb drums and an arpeggio. Practice note.

## What makes it look wrong

- Mint or teal in place of cyan
- A flat, unlit grid with no glow
- Rows that do not bunch toward the horizon

## Tested demo

This is the look from `art-forms/looks-screen.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=synthwave` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  synthwave: { kind: '2d', fps: null, draw(g, t, W, H) {
    // an outrun night: a striped sun sinking behind wireframe mountains, and a neon grid that streams toward the horizon, in magenta and cyan on deep purple
    const hz = 300, sky = g.createLinearGradient(0, 0, 0, hz); sky.addColorStop(0, '#12062e'); sky.addColorStop(0.6, '#3a0a6a'); sky.addColorStop(0.92, '#c2188f'); sky.addColorStop(1, '#ff5f9e'); g.fillStyle = sky; g.fillRect(0, 0, W, hz);
    for (let i = 0; i < 60; i++) { g.fillStyle = `rgba(255,255,255,${0.3 + 0.6 * ((Math.sin(t * 2 + i) + 1) / 2)})`; g.fillRect(hash(i, 1) * W, hash(i, 2) * 200, 1.6, 1.6); }
    g.save(); g.beginPath(); g.rect(0, 0, W, hz); g.clip(); const sy = hz - 60, sun = g.createLinearGradient(0, sy - 140, 0, sy + 140); sun.addColorStop(0, '#fff25e'); sun.addColorStop(0.5, '#ff7a3a'); sun.addColorStop(1, '#ff2bd6'); g.fillStyle = sun; g.beginPath(); g.arc(480, sy, 140, 0, TAU); g.fill();
    g.fillStyle = '#c2188f'; const ph = (t * 0.3) % 1; for (let k = 0; k < 7; k++) g.fillRect(300, sy + 6 + (k + ph) * 17, 360, 2 + k * 2.3); g.restore();
    for (const [x0, x1, pk, hh] of [[0, 380, 130, 120], [600, 960, 840, 150]]) { const pts = [[x0, hz], [lerp(x0, x1, 0.2), hz - hh * 0.5], [pk, hz - hh], [lerp(x0, x1, 0.62), hz - hh * 0.4], [lerp(x0, x1, 0.8), hz - hh * 0.7], [x1, hz]]; polyFill(g, pts, '#1a0840'); neon(g, '#2ad4ff', 2, () => path(g, pts, false)); }
    const fl = g.createLinearGradient(0, hz, 0, H); fl.addColorStop(0, '#2a0a52'); fl.addColorStop(1, '#0d0320'); g.fillStyle = fl; g.fillRect(0, hz, W, H - hz);
    const glow = g.createLinearGradient(0, hz - 20, 0, hz + 70); glow.addColorStop(0, 'rgba(255,60,200,0)'); glow.addColorStop(0.3, 'rgba(255,60,200,.55)'); glow.addColorStop(1, 'rgba(255,60,200,0)'); g.fillStyle = glow; g.fillRect(0, hz - 20, W, 90);
    g.save(); g.beginPath(); g.rect(0, hz, W, H - hz); g.clip(); const ph2 = (t * 0.7) % 1;
    neon(g, '#ff2bd6', 2.4, () => { g.beginPath(); for (let i = -24; i <= 24; i++) { g.moveTo(480 + i * 16, hz); g.lineTo(480 + i * 190, H); } for (let k = 0; k < 16; k++) { const y = hz + (H - hz) * ((k + ph2) / 16) ** 2.3; g.moveTo(0, y); g.lineTo(W, y); } });
    g.restore(); neon(g, '#2ad4ff', 2.4, () => { g.beginPath(); g.moveTo(0, hz); g.lineTo(W, hz); });
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Synthwave>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
