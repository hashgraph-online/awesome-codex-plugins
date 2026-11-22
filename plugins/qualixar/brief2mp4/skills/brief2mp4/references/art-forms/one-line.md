# One continuous line

Also called: single line drawing, one line drawing, continuous line drawing.

Family: Drawn and painted. Cadence: smooth, full frame rate. Usual tool: HyperFrames (SVG or canvas).

A whole subject drawn by one unbroken line on a flat colour: the pen never lifts, crosses itself where it must, and the finished drawing is a single curve.

In a continuous-line drawing the artist looks at both the subject and the paper, moving the medium over the paper to create a silhouette of the object. It belongs to the contour-drawing family, and line art in general is made of distinct lines placed against a plain background.

## What makes it read as this

- One line, constant width, round ends, that never breaks
- A flat single-colour ground and a single ink colour
- The line crosses itself and doubles back rather than lifting
- A pen dot at the tip while it draws
- Plenty of empty space round the subject

## Timing

The line draws on at an even speed over about 3.5 seconds, eased at the start and the end, then the drawing holds. Full frame rate: a clean ink line should not step.

## How to build it

- Build the path as a smooth spline through hand-placed points (`spline()` in `looks-painted.js`)
- Resample it to points evenly spaced by length, so the pen moves at a steady speed
- Draw it to a fraction `k` of its length with `strokePart()`; round caps and joins
- Put a filled dot at the point where the line currently ends
- SVG route: `stroke-dashoffset` on a single path

## Assets

All in code. Place the control points on a sketch of the subject first. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A pen on paper under the draw-on, then silence. A single sustained note or a gentle piano. Practice note.

## What makes it look wrong

- Lifting the pen: a second path makes it a normal line drawing
- Jitter or boil, which fights the idea of one smooth line
- Too much detail: the form must read from the outline alone

## Tested demo

This is the look from `art-forms/looks-painted.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=one-line` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'one-line': { kind: '2d', fps: null, draw(g, t, W, H) {
    // a swan drawn by a single line that never lifts: a ripple, up the breast and neck, round the head and beak, down the back to the tail, back along the belly, a wing, and out as a ripple
    bg(g, W, H, '#f2c14e');
    const path = swanLine(), k = easeInOut(prog(t, 0.15, 3.3));
    g.strokeStyle = '#17233f'; g.lineWidth = 4.6; g.lineCap = 'round'; g.lineJoin = 'round'; strokePart(g, path, k);
    if (k > 0 && k < 1) { const [x, y] = at(path, k); g.fillStyle = '#17233f'; g.beginPath(); g.arc(x, y, 7, 0, TAU); g.fill(); }
    g.fillStyle = '#17233f'; g.beginPath(); g.arc(352, 122, 4.8 * prog(t, 1.9, 0.2), 0, TAU); g.fill();
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Contour_drawing>
- <https://en.wikipedia.org/wiki/Line_art>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
