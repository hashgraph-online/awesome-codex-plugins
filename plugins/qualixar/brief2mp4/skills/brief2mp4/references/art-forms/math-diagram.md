# Maths diagram

Also called: math diagram, maths explainer, equation animation.

Family: Type, data and retro. Cadence: smooth, full frame rate. Usual tool: HyperFrames (canvas), or Manim for real maths.

A chalk-on-navy maths explainer: an equation builds term by term, each term in its own colour with its own curve on the plot, then the sum curve draws on and a tangent line slides along it with its slope read out.

A tangent line to a curve at a point is the straight line that just touches the curve there; for a curve y = f(x) it passes through (c, f(c)) with slope f'(c), where f' is the derivative. Chalk on a dark board is the classic surface for showing such working.

## What makes it read as this

- One colour per term, used in the equation and again for that term's curve
- Axes and a faint grid, a bright sum curve, a gold tangent with a dot at the point of tangency
- Terms appear one at a time, in the order the plot is built
- Few words: the equation, a derivative line and a slope readout
- A navy board with a light chalk dust

## Timing

Terms appear at 0.3, 1.2 and 2.1 seconds, the sum curve draws from 2.8 to 4 seconds, and the tangent then slides back and forth. Smooth, full frame rate.

## How to build it

- Map maths coordinates to the screen with two small functions (`X(x)`, `Y(y)`) and draw each curve as a polyline up to a fraction `k` of its length
- Measure each piece of the equation with `measureText` so that the next piece starts where the last ended
- Tangent: `y0 + m (x - x0)` drawn over `x0 +- 2.2`, with `m = f'(x0)` read out in text
- Real route for real maths: Manim (a Python library for mathematical animation) renders the same scene with exact `Axes`, `Tex` and `ValueTracker` objects, then HyperFrames or ffmpeg joins the clip
- Add a speckle of white dust over the board colour

## Assets

All in code here. For typeset equations in a real film, use Manim's LaTeX support. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Chalk taps as each term lands, a calm piano and a clear voice. Practice note.

## What makes it look wrong

- Every term in the same colour
- A wall of text or a crowded plot
- A curve that appears all at once, with no build

## Tested demo

This is the look from `art-forms/looks-abstract.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=math-diagram` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'math-diagram': { kind: '2d', fps: null, draw(g, t, W, H) {
    // chalk on navy: an equation builds term by term, each term in its own colour with its own curve on the plot, the sum curve draws on, then a tangent line slides along it and its slope is read out
    g.fillStyle = '#10213f'; g.fillRect(0, 0, W, H); g.lineCap = 'round'; g.lineJoin = 'round'; g.textBaseline = 'alphabetic';
    const X = (x) => 500 + ((x + 3) / 8) * 420, Y = (y) => 470 - ((y + 3) / 11) * 380, f = (x) => 0.5 * x * x - x - 1, AMB = '#ffb43a', PNK = '#ff6fa8', BLU = '#6aa8ff', GLD = '#ffe066';
    g.strokeStyle = 'rgba(255,255,255,.1)'; g.lineWidth = 1; g.beginPath(); for (let x = -3; x <= 5; x++) { g.moveTo(X(x), Y(-3)); g.lineTo(X(x), Y(8)); } for (let y = -3; y <= 8; y++) { g.moveTo(X(-3), Y(y)); g.lineTo(X(5), Y(y)); } g.stroke();
    g.strokeStyle = 'rgba(255,255,255,.75)'; g.lineWidth = 2.4; g.beginPath(); g.moveTo(X(-3), Y(0)); g.lineTo(X(5), Y(0)); g.moveTo(X(0), Y(-3)); g.lineTo(X(0), Y(8)); g.stroke();
    const k = [prog(t, 0.3, 0.8), prog(t, 1.2, 0.8), prog(t, 2.1, 0.7)], curve = (fn, x0, x1, kk, col, lw) => { if (kk <= 0) return; g.strokeStyle = col; g.lineWidth = lw; g.beginPath(); const n = 60; for (let i = 0; i <= n * kk; i++) { const x = lerp(x0, x1, i / n), y = fn(x); i ? g.lineTo(X(x), Y(y)) : g.moveTo(X(x), Y(y)); } g.stroke(); };
    curve((x) => 0.5 * x * x, -3, 3.99, k[0], AMB, 2.6); curve((x) => -x, -3, 5, k[1], PNK, 2.6); curve(() => -1, -3, 5, k[2], BLU, 2.6); curve(f, -3, 5, easeInOut(prog(t, 2.8, 1.2)), '#fff', 4.4);
    let x = 46; const y = 190; x += word(g, 'f(x) = ', x, y, 60, '#fff', prog(t, 0, 0.4)); x += word(g, '½x²', x, y, 60, AMB, k[0]); x += word(g, ' − x', x, y, 60, PNK, k[1]); word(g, ' − 1', x, y, 60, BLU, k[2]);
    const tk = prog(t, 3.6, 0.5); if (tk > 0) {
      const x0 = 1 + 3.2 * Math.sin((t - 3.6) * 1.1 + 0.4), m = x0 - 1, y0 = f(x0); g.strokeStyle = GLD; g.lineWidth = 3.4; g.beginPath(); g.moveTo(X(x0 - 2.2), Y(y0 - 2.2 * m)); g.lineTo(X(x0 + 2.2), Y(y0 + 2.2 * m)); g.stroke(); g.fillStyle = GLD; g.beginPath(); g.arc(X(x0), Y(y0), 8, 0, TAU); g.fill();
      let tx = 46; tx += word(g, 'f′(x) = ', tx, 300, 48, '#fff', tk); tx += word(g, 'x − 1', tx, 300, 48, GLD, tk); word(g, ` = ${m.toFixed(1)}`, tx, 300, 48, '#fff', tk);
    }
    speckle(g, W, H, 3, 28, [255, 255, 255]);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Tangent>
- <https://en.wikipedia.org/wiki/Chalkboard>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
