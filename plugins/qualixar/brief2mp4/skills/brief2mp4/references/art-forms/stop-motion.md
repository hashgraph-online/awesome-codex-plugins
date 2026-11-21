# Stop-motion look

Family: Craft and handmade. Cadence: steps 12 times a second. Usual tool: HyperFrames (canvas or DOM) or Three.js.

Any real object moved and photographed a pose at a time. On screen it shows as stepped motion, tiny position errors and light that flickers a little.

As old as film: stop tricks appear in the 1890s. Pixilation, cut-out and puppet animation are all forms of it.

## What makes it read as this

- Real materials: wood, card, cloth, plastic
- Position jitter of a pixel or two between drawings
- Lighting that varies slightly frame to frame
- Hard cuts between poses, no in-between blur

## Timing

On twos (12 changes a second) is the usual cadence; action sometimes on ones, held moments on threes or more.

## How to build it

- Quantise time before anything else: `const ts = held(t, 12)`
- GSAP: `ease: "steps(12)"` on a one-second tween does the same for a tween
- Jitter and flicker keyed to the frame number: `jit(frameOf(t, 12), i, 1.2)`
- Keep the camera and background steady: step the subject, not the world

## Assets

None needed. Everything is procedural. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Foley that lands on pose changes. A bed that is not too smooth. Practice note.

## What makes it look wrong

- Stepping the camera and background together, so everything strobes
- Easing between held poses, which defeats the look
- Jitter so large the object vibrates

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=stop-motion` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of that file. Take the technique, not the picture.

```js
  'stop-motion': { kind: '2d', fps: 12, draw(g, t, W, H) {
    // blocks stack one by one. Time is held on twos, every pose is nudged a pixel, and the light flickers per frame.
    const f = frameOf(t, 12), ts = held(t, 12);
    bg(g, W, H, `hsl(34 30% ${86 + jit(f, 1, 1.2)}%)`);
    g.fillStyle = '#c9b48f'; g.fillRect(0, H * 0.74, W, H * 0.26);
    const cols = ['#c0392b', '#e0a526', '#2f6f8f', '#3d8b5a', '#7a4fa0'];
    for (let i = 0; i < 5; i++) {
      const k = bounce(prog(ts, 0.25 + i * 0.42, 0.5)); if (prog(ts, 0.25 + i * 0.42, 0.5) <= 0) continue;
      const x = W / 2 - 70 + (i % 2) * 34 + jit(f, i, 1.2), y = lerp(-90, H * 0.74 - 62 - i * 62, k) + jit(f, i + 9, 1.2);
      g.save(); g.translate(x + 60, y + 31); g.rotate(jit(f, i + 20, 0.012) + (i % 2 ? 0.03 : -0.02));
      g.shadowColor = 'rgba(60,40,10,.35)'; g.shadowBlur = 10; g.shadowOffsetY = 6; g.fillStyle = cols[i]; g.fillRect(-60, -31, 120, 62);
      g.shadowColor = 'transparent'; g.fillStyle = 'rgba(255,255,255,.14)'; g.fillRect(-60, -31, 120, 12); g.restore();
    }
    paper(g, W, H, 5, 18);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Stop_motion>
- <https://en.wikipedia.org/wiki/Clay_animation>
- <https://gsap.com/docs/v3/Eases/SteppedEase/>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
