# Linocut and woodcut print

Family: Drawn and painted. Cadence: steps 8 times a second. Usual tool: HyperFrames (canvas, SVG).

A relief print: bold flat shapes in one to three inks, with white gouge marks where the block was carved.

Carved in linoleum or wood; the uncut surface prints. Each colour is a separate block.

Sourcing note: The source covers the technique; the visual rules are practice notes.

## What makes it read as this

- Bold shapes, no fine detail
- Short white cut marks inside the ink, all leaning one way
- One to three inks, laid slightly off register
- Paper showing at the edges

## Timing

Each colour arrives as a pull, top to bottom, then holds. On twos or slower.

## How to build it

- Draw each block to its own canvas, then cut marks out of it: short strokes with `destination-out`
- Print blocks over each other with `multiply`, the second one offset a few pixels
- Reveal a block by widening a clip from the top
- SVG route: `feTurbulence` through a hard threshold makes rough voids

## Assets

All in code. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A roller, a press, paper lifting. Practice note.

## What makes it look wrong

- Gradients
- Thin delicate lines
- Too many colours

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=linocut` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of that file. Take the technique, not the picture.

```js
  linocut: { kind: '2d', fps: 8, draw(g, t, W, H) {
    // two blocks, two inks. Bold shapes with white gouge marks cut out of them; the second colour lands a little off.
    const ts = held(t, 8);
    bg(g, W, H, '#efe7d3');
    const block = (col, k, dx, dy, shape, seed) => {
      if (k <= 0) return; const c = new OffscreenCanvas(W, H), b = c.getContext('2d');
      b.fillStyle = col; shape(b); b.globalCompositeOperation = 'destination-out'; b.strokeStyle = '#000'; b.lineCap = 'round';
      for (let i = 0; i < 230; i++) { const x = hash(i, seed) * W, y = hash(i, seed, 1) * H, a = -0.6 + hash(i, seed, 2) * 0.5, l = 14 + hash(i, seed, 3) * 38; b.lineWidth = 1.5 + hash(i, seed, 4) * 4; b.beginPath(); b.moveTo(x, y); b.lineTo(x + Math.cos(a) * l, y + Math.sin(a) * l); b.stroke(); }
      g.save(); g.globalCompositeOperation = 'multiply'; g.globalAlpha = 0.94; g.beginPath(); g.rect(0, 0, W, H * k); g.clip(); g.drawImage(c, dx, dy); g.restore();   // the print is "pulled" from the top
    };
    block('#1f3b57', prog(ts, 0.2, 0.9), 0, 0, (b) => { b.beginPath(); b.moveTo(0, H * 0.78); b.lineTo(W * 0.24, H * 0.4); b.lineTo(W * 0.42, H * 0.62); b.lineTo(W * 0.62, H * 0.26); b.lineTo(W, H * 0.7); b.lineTo(W, H); b.lineTo(0, H); b.closePath(); b.fill(); }, 61);
    block('#d6452b', prog(ts, 1.3, 0.9), 7, -5, (b) => { b.beginPath(); b.arc(W * 0.74, H * 0.26, 76, 0, TAU); b.fill(); b.fillRect(W * 0.1, H * 0.84, W * 0.8, 26); }, 62);
    paper(g, W, H, 19, 24);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Linocut>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
