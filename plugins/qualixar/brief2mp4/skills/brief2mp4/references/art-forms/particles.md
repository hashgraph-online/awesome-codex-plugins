# Particles

Also called: particle system, particle animation, particle text.

Family: Abstract and generative. Cadence: smooth, full frame rate. Usual tool: HyperFrames (canvas) or Three.js.

Thousands of small glowing particles drift in from all over the frame and settle into a word, hold it, then burst apart and reform.

A particle system is a technique in game physics, motion graphics and computer graphics that uses many minute sprites, 3D models or other graphic objects to simulate "fuzzy" phenomena that are hard to reproduce with conventional rendering; it was introduced in the 1982 film Star Trek II: The Wrath of Khan for the Genesis effect.

## What makes it read as this

- Thousands of tiny points, each simple
- The shape appears only from the points' positions
- Glow: bright, additive points on a near-black ground
- Colour from position: a gradient across the shape
- Staggered motion: each particle starts and arrives at its own time

## Timing

Gathering takes 2.2 seconds, the word holds with a gentle shimmer, then bursts apart over 1.6 seconds; the cycle is 6.2 seconds. Smooth, full frame rate.

## How to build it

- Sample a target shape once: draw the word on a hidden canvas and keep the lit pixels every 4 px (`wordPoints()` in `looks-abstract.js`)
- Give each particle a seeded start and a target; interpolate with a per-particle delay and `easeOut`
- Burst: push each outward at a seeded angle with a slight curl
- Draw as small squares with `lighter` compositing
- Real route: Three.js `Points` with a position buffer you tween on the GPU, or a particle layer in HyperFrames

## Assets

All in code. Use your own icon or word: no existing logo. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A rising shimmer for the gather and a soft boom for the burst. Practice note.

## What makes it look wrong

- Too few particles: the shape does not read
- All particles moving in lockstep
- Using a real company's logo

## Tested demo

This is the look from `art-forms/looks-abstract.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=particles` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  particles: { kind: '2d', fps: null, draw(g, t, W, H) {
    // about three thousand particles drift in from all over the frame and settle into a word, hold it, then burst apart and reform; each is a small glowing dot coloured by where it lands
    g.fillStyle = '#070912'; g.fillRect(0, 0, W, H); const pts = wordPoints('MOTION', W, H, 190), N = 3200, cyc = t % 6.2, gather = easeInOut(clamp(cyc / 2.2)), burst = clamp((cyc - 3.4) / 1.6), hold = Math.sin(t * 3) * 1.2;
    g.globalCompositeOperation = 'lighter';
    for (let i = 0; i < N; i++) {
      const tg = pts[(i * 7) % pts.length], off = clamp(gather * 1.25 - hash(i, 1) * 0.25), e = easeOut(off), sx = hash(i, 2) * W, sy = hash(i, 3) * H, ang = hash(i, 4) * TAU, far = 200 + hash(i, 5) * 520;
      let x = lerp(sx, tg[0] + (hash(i, 6) - 0.5) * 3, e), y = lerp(sy, tg[1] + (hash(i, 7) - 0.5) * 3, e); if (e > 0.95) { x += Math.sin(t * 2 + i) * hold; y += Math.cos(t * 2.3 + i) * hold; }
      if (burst > 0) { const b = burst ** 1.8; x += Math.cos(ang + b * 1.5) * far * b; y += Math.sin(ang + b * 1.5) * far * b; }
      const u = tg[0] / W, col = u < 0.5 ? mix([255, 190, 70], [255, 80, 160], u * 2) : mix([255, 80, 160], [90, 150, 255], (u - 0.5) * 2), a = (0.4 + 0.5 * e) * (1 - burst * 0.5);
      g.fillStyle = rgba(col, a); g.fillRect(x - 1.4, y - 1.4, 2.8, 2.8);
    }
    g.globalCompositeOperation = 'source-over';
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Particle_system>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
