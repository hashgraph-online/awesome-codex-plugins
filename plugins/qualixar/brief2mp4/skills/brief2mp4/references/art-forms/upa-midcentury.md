# UPA and mid-century modern

Also called: mid-century modern, limited animation.

Family: Drawn and painted. Cadence: steps 8 times a second. Usual tool: HyperFrames (canvas, SVG).

Flat, stylised design from 1950s cartoons: geometric characters, abstract backgrounds, colour printed slightly off its outline, and very few drawings.

United Productions of America turned away from Disney realism and made limited animation a style. Gerald McBoing-Boing won an Academy Award in 1950.

## What makes it read as this

- Characters built from triangles, circles and lines
- Flat colour blocks that do not meet their outlines
- Abstract backgrounds: a few shapes, no perspective
- A warm, muted palette

## Timing

Limited animation: a pose is held, then pops to the next. Eight or fewer changes a second.

## How to build it

- Flat shapes; draw the outline 6 to 9 px away from the fill
- Two or three poses, switched on a frame count with no in-betweens
- Paper grain with `multiply`

## Assets

All in code. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Jazz combo, sound effects as music. Practice note.

## What makes it look wrong

- Smooth, fluid motion
- Gradients and realistic light

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=upa-midcentury` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of that file. Take the technique, not the picture.

```js
  'upa-midcentury': { kind: '2d', fps: 8, draw(g, t, W, H) {
    // limited animation: flat geometric shapes, colour printed slightly off its outline, held poses that pop on threes
    const pose = frameOf(t, 8) % 12 < 6 ? 0 : 1, f = frameOf(t, 8);
    bg(g, W, H, '#e8dcc0');
    g.fillStyle = '#d98c3a'; g.fillRect(W * 0.08, H * 0.16, W * 0.3, H * 0.62); g.fillStyle = '#5a6fa5'; g.beginPath(); g.arc(W * 0.78, H * 0.28, 70, 0, TAU); g.fill();
    g.strokeStyle = '#1c1c1c'; g.lineWidth = 3; g.strokeRect(W * 0.08 + 9, H * 0.16 - 8, W * 0.3, H * 0.62); g.beginPath(); g.arc(W * 0.78 - 8, H * 0.28 + 6, 70, 0, TAU); g.stroke();
    const x = W * 0.55, y = H * 0.74, lean = pose ? 0.14 : -0.1;
    g.save(); g.translate(x, y); g.rotate(lean);
    g.fillStyle = '#c8452f'; g.beginPath(); g.moveTo(-70, 0); g.lineTo(70, 0); g.lineTo(0, -210); g.closePath(); g.fill();
    g.strokeStyle = '#1c1c1c'; g.beginPath(); g.moveTo(-64, -8); g.lineTo(76, -8); g.lineTo(6, -218); g.closePath(); g.stroke();
    g.fillStyle = '#f3e9d2'; g.beginPath(); g.arc(0, -236, 34, 0, TAU); g.fill(); g.stroke();
    g.lineWidth = 5; g.lineCap = 'round'; g.beginPath(); g.moveTo(-30, -130); g.lineTo(-96, pose ? -206 : -100); g.moveTo(30, -130); g.lineTo(100, pose ? -110 : -196); g.stroke();
    g.fillStyle = '#1c1c1c'; g.beginPath(); g.arc(pose ? 10 : -8, -240, 4, 0, TAU); g.fill(); g.restore();
    paper(g, W, H, 17, 26 + jit(f, 1, 2));
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/United_Productions_of_America>
- <https://en.wikipedia.org/wiki/Limited_animation>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
