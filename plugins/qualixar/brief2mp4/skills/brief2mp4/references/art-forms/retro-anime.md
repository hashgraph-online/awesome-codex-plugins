# Retro anime (80s and 90s)

Also called: 80s anime, 90s anime, retro cel anime.

Family: Drawn and painted. Cadence: steps 8 times a second. Usual tool: HyperFrames (canvas), or Blender with a toon material for 3D.

A hand-painted television look: hard two-tone shading, banded sunset skies, a striped sun, a lit skyline, a figure from behind with hair and scarf in the wind, a little film grain and a soft glow.

Anime is animation originating from Japan; a characteristic art style emerged in the 1960s and spread in the following decades. Traditional animation paints the characters on transparent cels laid over a static painted background, a process generally credited to Earl Hurd, who patented it in 1914.

## What makes it read as this

- Hard-edged two-tone shading: one base colour and one shadow colour, no soft gradients on the characters
- Banded, graded skies in stepped colour: violet to magenta to orange to cream
- A big sun with horizontal slits, a lit skyline, a rim of warm light on the edges
- Characters seen from behind or in profile, hair and scarf moving in the wind
- Film grain, and a soft bloom around bright areas

## Timing

Drawn on threes: about 8 changes a second inside a 24 frames-a-second film. The sun rises slowly, windows twinkle and hair streams.

## How to build it

- Quantise time with `held(t, 8)` and key every flicker to `frameOf(t, 8)`
- Sky: eight flat bands from `fillRect`; the sun is a clipped disc with a hard shadow tone and slits cut across it
- Shade a character with a base polygon and a second polygon of the shadow colour on one side
- Bloom: a radial gradient drawn with `lighter` over the picture; grain: a speckle with a seed from `frameOf(t, 8) % 6`

## Assets

All in code. For real character art, paint on layers and keep the shadow tone as its own layer. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A synth pad and a drum machine, city ambience, wind on the rooftop. Practice note.

## What makes it look wrong

- Smooth gradients on the figures: the shading is hard-edged
- Smooth 24 frames-a-second motion on every layer, which loses the television feel
- Copying a recognisable character

## Tested demo

This is the look from `art-forms/looks-toon.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=retro-anime` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'retro-anime': { kind: '2d', fps: 8, draw(g, t, W, H) {
    // an 80s or 90s cel look: hard two-tone shading, banded sunset sky and a striped sun, a lit skyline, a figure from behind with hair and scarf in the wind, film grain and a soft bloom
    const ts = held(t, 8), f = frameOf(t, 8), sunY = lerp(440, 255, easeOut(prog(ts, 0, 3.2)));
    bg(g, W, H, '#ffe9a0');   // every pixel is repainted each frame, so the same time always gives the same picture
    ['#1d0b3d', '#3b1366', '#6a1b8a', '#b3237f', '#e8505b', '#ff8a3d', '#ffc15a', '#ffe9a0'].forEach((c, i) => { g.fillStyle = c; g.fillRect(0, i * 54, W, 56); });
    for (let i = 0; i < 26; i++) if ((f + i) % 5) { const x = hash(i, 1) * W, y = hash(i, 2) * 160, r = 1.5 + hash(i, 3) * 2; g.fillStyle = '#fff6d8'; g.fillRect(x - r, y - 0.5, 2 * r, 1); g.fillRect(x - 0.5, y - r, 1, 2 * r); }
    g.save(); g.beginPath(); g.arc(480, sunY, 140, 0, TAU); g.clip(); g.fillStyle = '#ffe27a'; g.fillRect(0, 0, W, H); g.fillStyle = '#ffb347'; g.fillRect(0, sunY + 12, W, H);   // the sun: a hard shadow tone below
    for (let k = 0; k < 7; k++) { g.fillStyle = '#ff8a3d'; g.fillRect(0, sunY + 24 + k * 19, W, 2.5 + k * 2.4); } g.restore();   // slits of sky cut across it
    const city = (base, minH, maxH, col, win, seed, step) => { for (let x = -10, i = 0; x < W; x += step * (0.7 + hash(i, seed) * 0.8), i++) { const w = 34 + hash(i, seed + 1) * 52, h = minH + hash(i, seed + 2) * (maxH - minH); g.fillStyle = col; g.fillRect(x, base - h, w, h + 60); if (hash(i, seed + 3) > 0.6) g.fillRect(x + w / 2 - 1, base - h - 26, 2, 26); if (win) for (let wy = base - h + 10; wy < base - 8; wy += 15) for (let wx = x + 7; wx < x + w - 8; wx += 12) if (hash(wx | 0, wy | 0, seed) > 0.5 && (f + wx) % 13 !== 0) { g.fillStyle = '#ffd35a'; g.fillRect(wx, wy, 5, 7); g.fillStyle = col; } } };
    city(430, 40, 120, '#4a1a6e', true, 11, 58); city(470, 28, 78, '#1b0b2e', true, 21, 70);
    g.fillStyle = '#0f0620'; g.fillRect(0, 462, W, 80); g.fillStyle = '#ff8a3d'; g.fillRect(0, 462, W, 3);   // the rooftop, with a rim of sunset light
    const bloom = g.createRadialGradient(480, sunY, 20, 480, sunY, 330); bloom.addColorStop(0, 'rgba(255,220,130,.5)'); bloom.addColorStop(1, 'rgba(255,160,90,0)'); g.save(); g.globalCompositeOperation = 'lighter'; g.fillStyle = bloom; g.fillRect(0, 0, W, H); g.restore();
    const sway = Math.sin(ts * 3.2) * 5, wave = (i, k) => Math.sin(ts * 4.5 + i * 0.8 + k) ;
    g.save(); g.translate(330, 472); g.scale(1.0, 1.0);   // a figure from behind in a jacket, standing on the roof edge: about 45% of the frame's height
    for (const [d, ax, ay] of [[-1, -22, -100], [1, 22, -100]]) { const kx = d * 24; celPart(g, [[ax - 15, ay], [ax + 15, ay], [kx + 12, -4], [kx - 12, -4]], '#2a3068', '#171b40', '#ff9a63', 0.55); celPart(g, [[kx - 16, -6], [kx + 16, -6], [kx + 22 * d, 8], [kx - 14 * d, 8]], '#12122e', '#0a0a1c', '#ff9a63', 0.5); }   // legs and shoes
    celPart(g, [[-50, -178], [50, -178], [42, -98], [46, -88], [-46, -88], [-42, -98]], '#2f4bb5', '#1d2d78', '#ffb36b', 0.52);   // the jacket, wider at the shoulders and flared at the hem
    celPart(g, [[-28, -178], [-18, -204], [18, -204], [28, -178], [0, -170]], '#27408f', '#17265a', '#ffb36b', 0.5);   // a raised collar
    celPart(g, taper([[-46, -172], [-62, -132], [-40, -98]], 12, 10), '#2f4bb5', '#1d2d78', '#ffb36b', 0.55); celPart(g, [[-48, -106], [-34, -92], [-30, -104], [-44, -114]], '#e2a381', '#a8704f', '#ffb36b', 0.5);   // the left arm, hand in a pocket
    celPart(g, taper([[48, -172], [66, -132], [60, -92]], 12, 10), '#2f4bb5', '#1d2d78', '#ffb36b', 0.3); disc(g, 60, -86, 9, '#e2a381');   // the right arm hanging, a fist
    celPart(g, [[-10, -204], [10, -204], [12, -190], [-12, -190]], '#e2a381', '#a8704f', '#ffb36b', 0.5);   // the neck
    for (let i = 0; i < 2; i++) {   // the scarf: a wrap at the collar and two tails streaming to the right
      const tail = Array.from({ length: 9 }, (_, j) => [14 + j * 21, -192 + i * 8 + wave(j, i * 1.4) * (4 + j * 1.6) + j * 1.5]);
      celPart(g, taper(tail, 9 - i * 2, 3), i ? '#c92b36' : '#e8363f', '#8f1c28', '#ffc08a', 0.0);
    }
    celPart(g, [[-30, -196], [30, -196], [28, -182], [-28, -182]], '#e8363f', '#a8202e', '#ffc08a', 0.5);
    const head = ellipseLine(0, -224, 29, 31); celPart(g, head, '#1b1b3a', '#0e0e24', '#ffb36b', 0.5);
    for (let i = 0; i < 8; i++) {   // spiky hair streaming to the right, each lock a tapering blade that waves on twos
      const a = -2.5 + i * 0.36, bx = Math.cos(a) * 24, by = -224 + Math.sin(a) * 26, len = 44 + (i % 3) * 14, w = wave(i, 0) * 11;
      celPart(g, [[bx - 9, by + 6], [bx + len * 0.6 + sway, by - 8 + w - i * 1.5], [bx + len + sway * 1.4, by + 6 + w * 1.4 + i * 2], [bx + 9, by + 13]], '#1b1b3a', '#0e0e24', '#ffb36b', 0.35 + (i % 2) * 0.1);
    }
    g.fillStyle = '#4a56a0'; g.beginPath(); g.arc(0, -224, 30, Math.PI * 1.22, Math.PI * 1.7); g.arc(0, -214, 22, Math.PI * 1.7, Math.PI * 1.22, true); g.fill();   // a hard highlight band on the hair
    celPart(g, [[22, -222], [30, -214], [26, -204], [20, -210]], '#e2a381', '#a8704f', '#ffb36b', 0.4);   // an ear
    g.restore();
    speckle(g, W, H, 40 + (f % 6), 55, [255, 240, 220]);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Anime>
- <https://en.wikipedia.org/wiki/Cel>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
