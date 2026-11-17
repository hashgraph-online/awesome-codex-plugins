# Origami

Family: Craft and handmade. Cadence: smooth, full frame rate. Usual tool: HyperFrames (canvas or SVG), or Three.js.

Paper folded from a flat sheet: sharp creases, flat facets, each fold a clean move followed by a pause.

Japanese paper folding. Modern computational origami works from crease patterns.

## What makes it read as this

- Sharp mountain and valley creases
- Flat facets, each shaded as one plane
- Paper coloured on one side, white on the other
- Soft, even light so the creases read

## Timing

Folds are eased moves of about 0.8 seconds with a short hold after each. Smooth, not stepped.

## How to build it

- 2D: a fold is a point travelling across the crease; draw the moving flap from the crease to that point
- Shade the flap by its angle, and swap to the paper's other colour past 90 degrees
- 3D: flat-shaded polygons, child groups rotating about the crease axis
- An orthographic camera gives a diagram-clean view

Use Blender when the paper has to bend or show thickness.

## Assets

Geometry in code. A faint paper grain. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Light paper crinkle on each fold, soft piano or music box. Practice note.

## What makes it look wrong

- Faces passing through each other
- Folding with no hold, so the eye cannot follow
- Light that hides the creases

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=origami` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of that file. Take the technique, not the picture.

```js
  origami: { kind: '2d', fps: null, draw(g, t, W, H) {
    // a square folds corner to corner, holds, then folds again. Each fold is an eased move with a hold after it.
    bg(g, W, H, '#eef0ee');
    const cx = W / 2, cy = H / 2 + 20, s = 150;
    const f1 = easeInOut(prog(t, 0.3, 0.8)), f2 = easeInOut(prog(t, 1.5, 0.8));
    const face = (pts, col) => { g.beginPath(); pts.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.closePath(); fill(g, col); g.strokeStyle = 'rgba(40,50,60,.45)'; g.lineWidth = 1.2; g.stroke(); };
    g.save(); g.translate(cx, cy);
    g.fillStyle = 'rgba(30,40,50,.12)'; g.beginPath(); g.ellipse(0, s * 0.95, s * 1.05, 16, 0, 0, TAU); g.fill();
    // the fixed lower-left triangle, then the upper-right triangle swinging over the diagonal crease
    const a1 = f1 * Math.PI, k1 = Math.cos(a1);                         // 1 flat, -1 folded over
    face([[-s, -s], [s, s], [-s, s]], '#f7f7f4');
    const tip = [lerp(s, -s, (1 - k1) / 2), lerp(-s, s, (1 - k1) / 2)];
    face([[-s, -s], [s, s], tip], k1 > 0 ? `hsl(8 70% ${58 - (1 - k1) * 16}%)` : `hsl(0 0% ${90 - (1 + k1) * 6}%)`);
    if (f1 >= 1) {                                                       // second fold: the bottom-right corner comes up
      const k2 = Math.cos(f2 * Math.PI), tip2 = [lerp(s, 0, (1 - k2) / 2), lerp(s, 0, (1 - k2) / 2)];
      face([[0, 0], [0, s], [s, s], [0, 0]].slice(0, 3).map((p, i) => (i === 2 ? tip2 : p)), k2 > 0 ? '#e8e8e4' : '#d8553f');
    }
    g.setLineDash([6, 6]); g.strokeStyle = 'rgba(40,50,60,.5)'; g.beginPath(); g.moveTo(-s, -s); g.lineTo(s, s); g.stroke(); g.setLineDash([]);
    g.restore(); paper(g, W, H, 8, 12);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Origami>
- <https://github.com/amandaghassaei/OrigamiSimulator>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
