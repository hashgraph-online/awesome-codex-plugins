# Chalkboard

Also called: blackboard, chalk drawing, chalk art.

Family: Drawn and painted. Cadence: steps 10 times a second. Usual tool: HyperFrames (canvas or SVG).

White and coloured chalk on a dark green-black board: dusty, broken lines that draw themselves, ghosts of old eraser swipes, and a stub of chalk at the tip of each line.

A blackboard or chalkboard is a reusable surface written on with chalk (calcium sulphate or calcium carbonate). Early boards were slate; later ones are often dark matte paint, black or dark green. The first attested use of chalk on a blackboard in the United States dates to 21 September 1801.

## What makes it read as this

- Dark green-black board with a soft lit patch and faint eraser swipes
- Dusty, broken chalk lines: three thin passes and a soft halo, never a solid line
- One or two chalk colours besides white
- A wooden ledge with fallen dust under the board
- Hand-lettered words, few and large

## Timing

Each line draws on over 0.3 to 0.8 seconds, in the order a teacher would draw it, about 4 seconds in all. The line boils at about 10 changes a second.

## How to build it

- Chalk: three passes of the same stroke with different dash patterns at half opacity plus a wide faint halo, each nudged by a seeded amount keyed to `frameOf(t, 10)` (`chalk()` in `looks-painted.js`)
- A rounded stub drawn at the tip while the line is still drawing
- Board: base colour, a radial light, grain, and a few big translucent ellipses for old swipes
- Specks in the board colour drawn over the chalk eat holes in it

## Assets

All in code. A chalk typeface if the system has one; the demo falls back to a handwriting face. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Chalk squeak and tap under each line, voice-led. Practice note.

## What makes it look wrong

- A pure black board and perfect white vector lines
- A hand that covers the drawing
- Paragraphs of text

## Tested demo

This is the look from `art-forms/looks-painted.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=chalkboard` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  chalkboard: { kind: '2d', fps: 10, draw(g, t, W, H) {
    // a green-black board with old eraser swipes, a ledge, and a right triangle drawn in dusty chalk with the chalk stub at the tip of each stroke
    const f = frameOf(t, 10), ts = held(t, 10);
    bg(g, W, H, '#1c2b25'); const lit = g.createRadialGradient(W * 0.45, H * 0.4, 40, W * 0.45, H * 0.45, W * 0.7); lit.addColorStop(0, 'rgba(70,98,84,.4)'); lit.addColorStop(1, 'rgba(70,98,84,0)'); g.fillStyle = lit; g.fillRect(0, 0, W, H);
    g.drawImage(grain(W, H, 12, 44, [205, 222, 212]), 0, 0);
    for (let i = 0; i < 6; i++) { g.save(); g.translate(120 + i * 150, 120 + hash(i, 1) * 260); g.rotate(-0.5 + hash(i, 2) * 0.5); g.fillStyle = `rgba(200,214,205,${0.045 + hash(i, 3) * 0.03})`; g.beginPath(); g.ellipse(0, 0, 120 + hash(i, 4) * 90, 26 + hash(i, 5) * 16, 0, 0, TAU); g.fill(); g.restore(); }
    g.fillStyle = '#5e4128'; g.fillRect(0, H - 40, W, 40); g.fillStyle = '#7a5833'; g.fillRect(0, H - 40, W, 7); g.fillStyle = 'rgba(235,238,230,.18)'; g.fillRect(0, H - 47, W, 7);   // the ledge, with a line of fallen dust
    const A = [150, 420], B = [500, 420], C = [500, 150];
    chalk(g, [A, B], prog(ts, 0.2, 0.55), f); chalk(g, [B, C], prog(ts, 0.8, 0.5), f); chalk(g, [C, A], prog(ts, 1.35, 0.6), f);
    chalk(g, [[472, 420], [472, 392], [500, 392]], prog(ts, 2.0, 0.2), f, '#f1eee4', 3);
    g.fillStyle = 'rgba(245,242,230,.92)'; g.font = `600 44px "Chalkduster", "Marker Felt", "Comic Sans MS", ${FONT}`;
    [['b', 316, 462, 2.1], ['a', 528, 296, 2.3], ['c', 290, 268, 2.5]].forEach(([s, x, y, st]) => { g.globalAlpha = prog(ts, st, 0.2); g.fillText(s, x, y); }); g.globalAlpha = 1;
    const k = prog(ts, 2.7, 0.9); g.save(); g.beginPath(); g.rect(556, 150, 400 * k, 140); g.clip(); g.fillStyle = 'rgba(255,224,120,.94)'; g.font = `600 52px "Chalkduster", "Marker Felt", "Comic Sans MS", ${FONT}`; g.fillText('a² + b² = c²', 566, 236); g.restore();
    chalk(g, [[566, 258], [740, 255], [900, 260]], prog(ts, 3.5, 0.3), f, '#ffe078', 3);
    const sunPts = circlePts(760, 360, 34, 20); chalk(g, sunPts, prog(ts, 3.4, 0.4), f, '#f6a9c4', 3);
    for (let i = 0; i < 8; i++) { const a = (i / 8) * TAU; chalk(g, [[760 + Math.cos(a) * 46, 360 + Math.sin(a) * 46], [760 + Math.cos(a) * 64, 360 + Math.sin(a) * 64]], prog(ts, 3.7 + i * 0.03, 0.12), f, '#f6a9c4', 3); }
    g.drawImage(grain(W, H, 17, 130, [28, 43, 37]), 0, 0);   // board-coloured specks eat into the chalk, so every line breaks up
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Blackboard>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
