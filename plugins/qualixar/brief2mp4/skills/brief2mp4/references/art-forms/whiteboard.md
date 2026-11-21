# Whiteboard and doodle

Also called: video scribing, chalkboard.

Family: Drawn and painted. Cadence: steps 10 times a second. Usual tool: HyperFrames (canvas or SVG).

Marker lines that draw themselves on a white board, in the order someone would draw them. The chalkboard is the same recipe, inverted.

Also called video scribing. A 2016 study found little evidence that it teaches better than other formats, so use it for its tone, not as a learning trick.

## What makes it read as this

- Black marker lines with a slight wobble
- Strokes appear in drawing order
- One or two accent colours
- Chalk variant: a dark board, dusty broken strokes, a little smudge

## Timing

Each element draws on over 0.3 to 1.5 seconds, paced to the narration. The line boils at about 10 changes a second.

## How to build it

- Draw-on: a polyline drawn up to a fraction of its length (SVG: `stroke-dashoffset`)
- Boil: nudge every point by a seeded amount keyed to `frameOf(t, 10)`
- Chalk: three thin passes of the same stroke with different dash patterns at half opacity, over a speckled board
- rough.js (MIT) generates sketchy shapes and hatching to animate afterwards

## Assets

All in code. A marker or chalk typeface if the system has one. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Marker squeak, voice-led. Practice note.

## What makes it look wrong

- Perfect vector lines
- A hand that covers the drawing
- Paragraphs of text

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=whiteboard` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of that file. Take the technique, not the picture.

```js
  whiteboard: { kind: '2d', fps: 10, draw(g, t, W, H) {
    // marker strokes that draw on in order, with a slight boil: the points are re-nudged ten times a second
    const f = frameOf(t, 10);
    bg(g, W, H, '#fbfbf8'); g.lineCap = 'round'; g.lineJoin = 'round'; g.strokeStyle = '#17202b'; g.lineWidth = 5;
    const bulb = circlePts(W * 0.3, H * 0.42, 78, 36, Math.PI * 0.72, Math.PI * 2.28);
    strokePart(g, bulb, prog(t, 0.1, 0.8), f, 1.6);
    strokePart(g, [[W * 0.3 - 34, H * 0.42 + 72], [W * 0.3 - 34, H * 0.42 + 112], [W * 0.3 + 34, H * 0.42 + 112], [W * 0.3 + 34, H * 0.42 + 72]], prog(t, 0.9, 0.35), f, 1.6);
    g.strokeStyle = '#e0532f'; for (let i = 0; i < 5; i++) { const a = -Math.PI * (0.15 + i * 0.175); strokePart(g, [[W * 0.3 + Math.cos(a) * 100, H * 0.42 + Math.sin(a) * 100], [W * 0.3 + Math.cos(a) * 132, H * 0.42 + Math.sin(a) * 132]], prog(t, 1.25 + i * 0.07, 0.15), f, 1.2); }
    g.strokeStyle = '#17202b'; strokePart(g, [[W * 0.45, H * 0.44], [W * 0.6, H * 0.44], [W * 0.57, H * 0.4], [W * 0.6, H * 0.44], [W * 0.57, H * 0.48]], prog(t, 1.6, 0.4), f, 1.6);
    strokePart(g, [[W * 0.65, H * 0.3], [W * 0.88, H * 0.3], [W * 0.88, H * 0.58], [W * 0.65, H * 0.58], [W * 0.65, H * 0.3]], prog(t, 2.0, 0.5), f, 1.6);
    const k = prog(t, 2.5, 0.3); if (k > 0) { g.globalAlpha = k; g.fillStyle = '#17202b'; g.font = `italic 600 34px "Marker Felt", "Comic Sans MS", ${FONT}`; g.fillText('idea → plan', W * 0.665, H * 0.46); g.globalAlpha = 1; }
  } }
```

```js
  chalkboard: { kind: '2d', fps: 10, draw(g, t, W, H) {
    // the whiteboard recipe on a dark board: dusty, broken strokes (three thin passes) and a smudge of chalk dust
    const f = frameOf(t, 10);
    bg(g, W, H, '#24382f'); g.drawImage(grain(W, H, 12, 34, [230, 240, 235]), 0, 0);
    g.lineCap = 'round'; g.lineJoin = 'round';
    const chalk = (pts, k, col = '#f2f0e6') => { for (let p = 0; p < 3; p++) { g.strokeStyle = col; g.globalAlpha = 0.5; g.lineWidth = 3; g.setLineDash([14 + p * 5, 3 + p]); g.lineDashOffset = p * 7; strokePart(g, pts.map(([x, y]) => [x + p - 1, y + (p - 1) * 1.4]), k, f + p * 31, 1.3); } g.setLineDash([]); g.globalAlpha = 1; };
    chalk([[W * 0.16, H * 0.72], [W * 0.84, H * 0.72]], prog(t, 0.1, 0.5));
    chalk([[W * 0.16, H * 0.72], [W * 0.16, H * 0.2]], prog(t, 0.4, 0.5));
    chalk(Array.from({ length: 40 }, (_, i) => [W * (0.16 + 0.66 * i / 39), H * (0.72 - 0.46 * (i / 39) ** 2)]), prog(t, 0.9, 1.0), '#ffd966');
    const k = prog(t, 2.0, 0.4); if (k > 0) { g.globalAlpha = k * 0.9; g.fillStyle = '#f2f0e6'; g.font = `600 36px "Chalkduster", "Marker Felt", ${FONT}`; g.fillText('y = x²', W * 0.56, H * 0.34); g.globalAlpha = 1; }
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Whiteboard_animation>
- <https://github.com/rough-stuff/rough>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
