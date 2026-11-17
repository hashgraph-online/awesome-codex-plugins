# Isometric

Family: Geometry, pixels and 3D. Cadence: smooth, full frame rate. Usual tool: HyperFrames (canvas, SVG) or Three.js.

A parallel projection seen from above at an angle: no perspective, three visible faces per block, a tidy model world.

A technical drawing projection. Games use a 2:1 pixel slope, about 26.6 degrees, which is strictly dimetric.

## What makes it read as this

- No perspective: parallel lines stay parallel
- Three tones per object: top lightest, one side mid, one side darkest
- One light direction for everything
- A grid floor

## Timing

The camera does not orbit. Objects drop, stack and slide along the three axes, staggered by grid position.

## How to build it

- 2D: `x = (gx - gy) * s`, `y = (gx + gy) * s / 2 - gz * s`; draw the two side faces, then the top
- Sort by `gx + gy`, then by height, so nearer cubes cover farther ones
- Three.js: an `OrthographicCamera` placed at equal x, y and z looking at the origin
- CSS: `rotateX(60deg) rotateZ(-45deg)` on a flat layer

Use Blender for bevelled, ambient-occluded isometric scenes.

## Assets

All in code. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Soft clicks as pieces land. Practice note.

## What makes it look wrong

- A perspective camera by accident
- Shadows that disagree with the light
- Uneven block heights

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=isometric` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of that file. Take the technique, not the picture.

```js
  isometric: { kind: '2d', fps: null, draw(g, t, W, H) {
    // a parallel projection: no perspective, three tones per cube, one light. Cubes drop in, staggered by grid position.
    bg(g, W, H, '#eaf0f6');
    const s = 44, ox = W / 2, oy = H * 0.34, iso = (x, y, z) => [ox + (x - y) * s, oy + (x + y) * s * 0.5 - z * s];
    const quad = (pts, col) => { g.beginPath(); pts.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.closePath(); fill(g, col); };
    for (let y = 0; y < 5; y++) for (let x = 0; x < 5; x++) quad([iso(x, y, 0), iso(x + 1, y, 0), iso(x + 1, y + 1, 0), iso(x, y + 1, 0)], (x + y) % 2 ? '#d5dfea' : '#dfe7f0');
    const towers = [[0, 0, 2], [1, 3, 1], [2, 1, 3], [3, 3, 2], [4, 0, 1], [3, 1, 1], [1, 1, 1], [4, 4, 3]];
    towers.sort((a, b) => a[0] + a[1] - (b[0] + b[1]));
    for (const [x, y, h] of towers) for (let z = 0; z < h; z++) {
      const k = prog(t, 0.2 + (x + y) * 0.12 + z * 0.14, 0.5); if (k <= 0) continue; const zz = z + (1 - bounce(k)) * 7, hue = 216 + (x * 7 + y * 13) % 40;
      quad([iso(x, y + 1, zz + 1), iso(x + 1, y + 1, zz + 1), iso(x + 1, y + 1, zz), iso(x, y + 1, zz)], `hsl(${hue} 52% 42%)`);
      quad([iso(x + 1, y, zz + 1), iso(x + 1, y + 1, zz + 1), iso(x + 1, y + 1, zz), iso(x + 1, y, zz)], `hsl(${hue} 52% 54%)`);
      quad([iso(x, y, zz + 1), iso(x + 1, y, zz + 1), iso(x + 1, y + 1, zz + 1), iso(x, y + 1, zz + 1)], `hsl(${hue} 60% 70%)`);
    }
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Isometric_video_game_graphics>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
