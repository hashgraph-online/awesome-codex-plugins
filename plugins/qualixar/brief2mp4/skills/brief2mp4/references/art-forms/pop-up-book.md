# Pop-up book

Also called: pop up book, popup book, paper engineering, movable book.

Family: Craft and handmade. Cadence: smooth, full frame rate. Usual tool: HyperFrames (canvas), Blender for real folded paper.

An open book seen at an angle: the pages swing open and layered card pieces stand up off them, each with a fold shadow, a visible card edge and a shadow on the page.

A pop-up book is any book with three-dimensional pages, often with elements that pop up as a page is turned; designing them is sometimes called paper engineering. The first known movable in a book was made by the Benedictine monk Matthew Paris, whose Chronica Majora, covering a period beginning in 1240, had volvelles attached to some pages.

## What makes it read as this

- A book at an angle with a spine shadow and a cover edge
- Card pieces that stand up from the pages in layers, near and far
- A thin offset edge and a fold shadow where each piece meets the page
- A shadow on the page under each piece
- Bright, flat, paper-craft colours

## Timing

The right page swings open over about 1.2 seconds, then each piece pops up in turn with a slight overshoot. Smooth motion.

## How to build it

- Map page space to the screen with a perspective-like function: width narrows toward the back, and `cos(pi (1 - open))` swings the right page
- Each piece: a draw function in its own local coordinates, scaled vertically by an overshooting `k`
- Draw the piece twice: a dark copy offset sideways as the card edge, then the front
- A small ellipse shadow and a gradient fold shadow at the base
- Sort pieces back to front

## Assets

All in code. For a real pop-up, build it in Blender with folded geometry. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A page turn, a paper pop and a music-box bed. Practice note.

## What makes it look wrong

- Pieces that float: each needs a base on the page and a shadow
- No overshoot on the pop
- A flat book with no angle

## Tested demo

This is the look from `art-forms/looks-toon.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=pop-up-book` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'pop-up-book': { kind: '2d', fps: null, draw(g, t, W, H) {
    // an open book seen at an angle: the right page swings open, then layered card pieces stand up off the pages, each with a fold shadow, a card edge and a shadow on the page
    const open = easeInOut(prog(t, 0, 1.2)), X0 = 480, FW = 400, BW = 340;
    const P = (side, u, v, ox = 1) => [X0 + side * u * (FW - (FW - BW) * v) * ox, 472 - v * 270];
    g.fillStyle = '#cdb48a'; g.fillRect(0, 0, W, H); const wood = g.createLinearGradient(0, 0, 0, H); wood.addColorStop(0, 'rgba(255,255,255,.18)'); wood.addColorStop(1, 'rgba(90,60,20,.2)'); g.fillStyle = wood; g.fillRect(0, 0, W, H);
    ell(g, 480, 490, 470, 36, 'rgba(60,35,10,.3)');
    polyFill(g, [[X0 - FW - 16, 484], [X0 + FW + 16, 484], [X0 + BW + 20, 188], [X0 - BW - 20, 188]], '#7a1f2b', '#4a1019', 3);
    const rx = Math.cos(Math.PI * (1 - open)), page = (side, ox) => polyFill(g, [P(side, 1, 0, ox), P(side, 0, 0), P(side, 0, 1), P(side, 1, 1, ox)], '#f6efdc', '#b8a97f', 2);
    page(-1, 1); page(1, rx);
    const sp = g.createLinearGradient(X0 - 50, 0, X0 + 50, 0); sp.addColorStop(0, 'rgba(60,40,20,0)'); sp.addColorStop(0.5, 'rgba(60,40,20,.38)'); sp.addColorStop(1, 'rgba(60,40,20,0)'); g.fillStyle = sp; g.fillRect(X0 - 50, 200, 100, 276);
    const pieces = [
      [1, 0.5, 0.96, 330, 150, 1.0, (w, h) => { polyFill(g, [[-w / 2, 0], [-w / 2, -h * 0.55], [-w * 0.25, -h * 0.9], [0, -h * 0.7], [w * 0.25, -h], [w / 2, -h * 0.6], [w / 2, 0]], '#7cc576', '#3f7a45', 3); }],
      [-1, 0.5, 0.96, 120, 190, 1.1, (w, h) => { ell(g, 0, -h * 0.6, w / 2, w / 2, '#ffd23f', '#c99a0f', 3); g.strokeStyle = '#c99a0f'; g.lineWidth = 3; path(g, [[0, -h * 0.1], [0, 0]], false); g.stroke(); }],
      [1, 0.45, 0.62, 160, 150, 1.5, (w, h) => { polyFill(g, [[-w / 2, 0], [-w / 2, -h * 0.7], [w / 2, -h * 0.7], [w / 2, 0]], '#e8a0a0', '#9a5a5a', 3); for (const d of [-1, 1]) { polyFill(g, [[d * w * 0.5 - 22, -h * 0.7], [d * w * 0.5 - 22, -h], [d * w * 0.5 + 22, -h], [d * w * 0.5 + 22, -h * 0.7]], '#d98a8a', '#9a5a5a', 3); polyFill(g, [[d * w * 0.5 - 28, -h], [d * w * 0.5, -h * 1.28], [d * w * 0.5 + 28, -h]], '#4a5fb5', '#26346d', 3); } for (let i = -3; i <= 3; i++) g.fillRect(i * 18 - 6, -h * 0.7 - 9, 12, 9); polyFill(g, [[-18, 0], [-18, -h * 0.38], [0, -h * 0.5], [18, -h * 0.38], [18, 0]], '#5a2f1a', '#2a140a', 3); }],
      [-1, 0.5, 0.5, 130, 120, 1.8, (w, h) => { polyFill(g, [[-w / 2, 0], [-w / 2, -h * 0.6], [w / 2, -h * 0.6], [w / 2, 0]], '#f4e3b0', '#a89458', 3); polyFill(g, [[-w * 0.62, -h * 0.6], [0, -h * 1.05], [w * 0.62, -h * 0.6]], '#c0392b', '#7a1f18', 3); polyFill(g, [[-10, 0], [-10, -h * 0.34], [10, -h * 0.34], [10, 0]], '#5a2f1a'); }],
      [1, 0.8, 0.34, 70, 130, 2.1, (w, h) => { g.fillStyle = '#8a5a2b'; g.fillRect(-7, -h * 0.5, 14, h * 0.5); ell(g, 0, -h * 0.72, w * 0.55, h * 0.3, '#2e9b4f', '#1b6b32', 3); }],
      [-1, 0.25, 0.12, 60, 80, 2.4, (w, h) => { g.strokeStyle = '#2e9b4f'; g.lineWidth = 4; path(g, [[0, 0], [0, -h * 0.7]], false); g.stroke(); ell(g, 0, -h * 0.8, 16, 16, '#ff6b8a', '#a8334f', 2); }],
      [1, 0.3, 0.1, 60, 90, 2.6, (w, h) => { g.strokeStyle = '#2e9b4f'; g.lineWidth = 4; path(g, [[0, 0], [0, -h * 0.7]], false); g.stroke(); ell(g, 0, -h * 0.8, 16, 16, '#ffd23f', '#a87f0f', 2); }],
    ];
    pieces.sort((a, b) => b[2] - a[2]).forEach(([side, u, v, w, h, st, draw]) => {
      const k = clamp(overshootK(prog(t, st, 0.55))); if (k <= 0.001 || open < 0.6) return;
      const [px, py] = P(side, u, v), sc = 1 - 0.15 * v; g.save(); g.translate(px, py);
      ell(g, 8 * k, 2, w * 0.5 * sc, 7 * k * sc, 'rgba(50,30,10,.28)'); g.save(); g.scale(sc, sc * k); g.translate(5, 0); g.globalAlpha = 0.5; g.fillStyle = '#000'; draw(w, h); g.restore();   // the card edge, offset to one side
      g.save(); g.scale(sc, sc * k); draw(w, h); g.restore();
      const fold = g.createLinearGradient(0, 0, 0, -14); fold.addColorStop(0, 'rgba(40,20,0,.35)'); fold.addColorStop(1, 'rgba(40,20,0,0)'); g.fillStyle = fold; g.fillRect(-w * 0.5 * sc, -14 * k, w * sc, 14 * k); g.restore();
    });
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Pop-up_book>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
