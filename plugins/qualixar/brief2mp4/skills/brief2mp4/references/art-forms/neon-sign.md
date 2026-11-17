# Neon sign

Family: Type, data and retro. Cadence: steps 24 times a second. Usual tool: HyperFrames (canvas, SVG).

Glass tubes bent into letters and lit: a bright core, a coloured glow, a dark wall, tubes that light one by one and sometimes flicker.

Glass tubing filled with gas and lit by electrodes; sections can be switched in sequence.

## What makes it read as this

- One continuous line per letter, one width
- A white-hot core inside a coloured halo
- A dark wall behind
- Letters light in sequence

## Timing

Tubes come on in order with a short stutter each; now and then one dims for a frame.

## How to build it

- Each tube is drawn three times: a wide faint stroke, a medium one, a thin white core, all with `shadowBlur`
- Add them with the `lighter` blend (CSS: `mix-blend-mode: plus-lighter` or `screen`)
- Flicker from `hash(frame, tube)`, never from a random call
- Three.js: `UnrealBloomPass` for bloom on emissive geometry

## Assets

Letter paths in code. A brick or plaster texture can be drawn. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A low electrical hum, a tick as each tube lights. Practice note.

## What makes it look wrong

- A glow so wide the word cannot be read
- Filled letters instead of a single tube
- Flicker that differs between renders

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=neon-sign` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of that file. Take the technique, not the picture.

```js
  'neon-sign': { kind: '2d', fps: 24, draw(g, t, W, H) {
    // one continuous tube per letter, a bright core with a coloured halo, lit letter by letter, with a seeded flicker
    const f = frameOf(t, 24);
    bg(g, W, H, '#120a16'); g.fillStyle = 'rgba(255,255,255,.035)'; for (let y = 0; y < H; y += 34) for (let x = (y / 34) % 2 ? 0 : 45; x < W; x += 90) g.fillRect(x, y, 86, 30);
    const L = { O: circlePts(0, 0, 54, 30), P: [[-40, 60], [-40, -56], [10, -56], ...circlePts(10, -22, 34, 12, -Math.PI / 2, Math.PI / 2), [-40, 12]], E: [[40, -56], [-40, -56], [-40, 0], [20, 0], [-40, 0], [-40, 60], [40, 60]], N: [[-40, 60], [-40, -56], [40, 60], [40, -56]] };
    g.lineCap = 'round'; g.lineJoin = 'round'; g.globalCompositeOperation = 'lighter';
    [...'OPEN'].forEach((ch, i) => {
      const on = t > 0.3 + i * 0.35, stutter = on && t < 0.3 + i * 0.35 + 0.25 && hash(f, i) < 0.45, dim = i === 2 && hash(f, 44) < 0.06;   // a start-up stutter, and one tired tube
      const a = !on || stutter ? 0.08 : dim ? 0.35 : 1, pts = L[ch].map(([x, y]) => [W * (0.2 + i * 0.2) + x, H * 0.5 + y]), col = i % 2 ? '80,220,255' : '255,60,170';
      for (const [w, alpha, blur] of [[26, 0.16, 26], [12, 0.4, 12], [5, 1, 0]]) { g.strokeStyle = blur ? `rgba(${col},${alpha * a})` : `rgba(255,255,255,${a})`; g.shadowColor = `rgba(${col},${a})`; g.shadowBlur = blur; g.lineWidth = w; strokePart(g, pts, 1); }
    });
    g.shadowBlur = 0; g.globalCompositeOperation = 'source-over';
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Neon_sign>
- <https://developer.mozilla.org/en-US/docs/Web/CSS/mix-blend-mode>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
