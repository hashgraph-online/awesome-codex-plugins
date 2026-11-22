# Gouache storybook

Also called: gouache, picture book illustration, matte opaque paint.

Family: Drawn and painted. Cadence: steps 8 times a second. Usual tool: HyperFrames (canvas or SVG).

Flat, matte, opaque layers of paint with hand-cut edges and faint brush streaks: the look of a printed picture book. Each colour is laid over the last, with no gradients and no transparency.

Gouache is an opaque water-medium paint of pigment, water and a binder such as gum arabic, with a high ratio of pigment to binder. It has been used for at least twelve centuries, dries to a matte finish, and is used by commercial artists for posters, illustrations and comics.

## What makes it read as this

- Flat, fully opaque shapes in a small palette
- Matte finish: no gloss and no shading gradients
- Hand-cut edges, slightly uneven, never a perfect curve
- Faint horizontal brush streaks inside each shape
- Back to front: sky, far hills, near hills, then the subject, then small bright details

## Timing

Layers go on one after another, each over about half a second: back to front over about 3 seconds, with small things such as stars and smoke last. The picture steps about 8 times a second.

## How to build it

- One filled path per colour, built with `cut()` (corners nudged by a seed) or `blob()`
- Clip to the path and draw 20 to 30 faint light and dark streaks across it (`flatShape()` in `looks-painted.js`)
- Reveal each layer with a clip that grows: up from the bottom for ground, across for objects
- Add paper tooth last at low strength
- Glow from a window is two or three flat circles of falling opacity, not a gradient

## Assets

All in code. Real gouache scans make a stronger texture if the user owns them. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Soft acoustic guitar or a music box, a wooden or paper foley on each layer. A storybook narration suits it. Practice note.

## What makes it look wrong

- Gradients or soft shadows, which turn it into a digital illustration
- Black outlines round every shape: gouache is edge to edge colour
- Too many colours: a storybook palette is five or six

## Tested demo

This is the look from `art-forms/looks-painted.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=gouache` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  gouache: { kind: '2d', fps: 8, draw(g, t, W, H) {
    // a storybook night in flat, matte, opaque layers: each colour laid in turn with a hand-cut edge, faint brush streaks, no gradients
    const ts = held(t, 8), f = frameOf(t, 8);
    const layer = (start, dir, body) => { const k = easeOut(prog(ts, start, 0.5)); if (k <= 0) return; g.save(); g.beginPath(); if (dir === 'up') g.rect(0, H * (1 - k), W, H * k); else g.rect(0, 0, W * k, H); g.clip(); body(); g.restore(); };
    const shape = (pts, col, seed) => flatShape(g, () => cut(g, pts, seed, 2.2), col, seed, bounds(pts));
    const pine = (x, base, h, seed) => { shape([[x - 10, base + 4], [x + 10, base + 4], [x + 10, base - h * 0.2], [x - 10, base - h * 0.2]], '#4b2f24', seed); for (let i = 0; i < 3; i++) { const w = (60 - i * 14) * (h / 170), yb = base - h * 0.14 - i * h * 0.27; shape([[x - w, yb], [x + w, yb], [x, yb - h * 0.42]], '#2b5a35', seed + i + 1); } };
    layer(0, 'up', () => { bg(g, W, H, '#273672'); shape([[0, 240], [960, 220], [960, 420], [0, 440]], '#2f4284', 3); });
    layer(0.25, 'right', () => { flatShape(g, () => blob(g, 700, 150, 70, 5, 0.02), '#f3e5a4', 5, [630, 80, 770, 220]); [[675, 130, 17], [722, 172, 12], [706, 118, 8]].forEach(([x, y, r], i) => flatShape(g, () => blob(g, x, y, r, 6 + i, 0.05), '#e3cf88', 6 + i, [x - r, y - r, x + r, y + r])); });
    for (let i = 0; i < 26; i++) { const x = hash(i, 1) * W, y = hash(i, 2) * 230; if (Math.hypot(x - 700, y - 150) > 96 && prog(ts, 2.8 + hash(i, 3) * 0.8, 0.1) > 0) { g.fillStyle = (f + i) % 7 === 0 ? 'rgba(243,229,164,.45)' : '#f3e5a4'; g.beginPath(); g.arc(x, y, 1.6 + hash(i, 4) * 1.8, 0, TAU); g.fill(); } }
    layer(0.6, 'up', () => shape([[0, 380], [140, 322], [300, 362], [470, 306], [640, 354], [800, 316], [960, 350], [960, 540], [0, 540]], '#40509a', 11));
    layer(1.0, 'up', () => { shape([[0, 440], [200, 392], [420, 424], [640, 384], [960, 430], [960, 540], [0, 540]], '#3f7440', 12); shape([[322, 408], [354, 408], [430, 470], [520, 540], [290, 540], [350, 470]], '#e8d29c', 13); });
    layer(1.5, 'right', () => { shape([[250, 336], [430, 336], [430, 414], [250, 414]], '#e9b676', 14); shape([[392, 270], [416, 270], [416, 320], [392, 320]], '#8f3c32', 15); });
    layer(1.9, 'right', () => shape([[226, 340], [340, 262], [454, 340]], '#b8463a', 16));
    layer(2.3, 'right', () => { flatShape(g, () => blob(g, 284, 368, 36, 19, 0.04), '#f3cc78', 19, [248, 332, 320, 404]); shape([[318, 366], [356, 366], [356, 414], [318, 414]], '#6a3b2b', 17); shape([[266, 350], [302, 350], [302, 386], [266, 386]], '#ffd45e', 18); g.strokeStyle = '#a0622f'; g.lineWidth = 3; g.beginPath(); g.moveTo(284, 350); g.lineTo(284, 386); g.moveTo(266, 368); g.lineTo(302, 368); g.stroke(); });
    [[560, 428, 150], [640, 436, 196], [738, 422, 142], [868, 436, 176]].forEach(([x, b, h], i) => layer(2.4 + i * 0.22, 'up', () => pine(x, b, h, 30 + i * 5)));
    for (let i = 0; i < 3; i++) { const s = prog(ts, 2.9, 1.2), y = 262 - ((s * 3 + i * 0.9) % 2.6) * 34; if (s > 0) { g.fillStyle = 'rgba(232,226,208,.8)'; g.beginPath(); g.arc(404 + Math.sin(f * 0.7 + i) * 4 + i * 4, y, 7 + i * 3, 0, TAU); g.fill(); } }
    paper(g, W, H, 4, 16);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Gouache>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
