# Modern TV cartoon

Also called: tv cartoon, flat tv cartoon, saturday morning cartoon.

Family: Drawn and painted. Cadence: steps 12 times a second. Usual tool: HyperFrames (canvas or SVG).

Thick, even outlines and flat, bright colour on simple geometric characters: squares, circles and triangles with big eyes, bouncing on twos against a plain, flat background.

In the animation sense a cartoon is a motion picture that relies on a sequence of illustrations. Limited animation reuses frames of character animation to save time and money, and in the late 1990s web animators using cutout and limited animation produced clean, vector-graphic pictures at small file sizes.

## What makes it read as this

- One thick outline weight round everything, in a near-black
- Flat, saturated colour with no shading or only one flat shadow
- Characters built from simple shapes: squares, circles, triangles
- Big round eyes with a small pupil; a simple wide mouth
- Plain, flat backgrounds: a hill, a cloud, a sun, a tree

## Timing

Drawn on twos, 12 changes a second, with holds, bounces and a blink every couple of seconds.

## How to build it

- Draw each shape with a fill and an 8 px outline of the same dark colour (`ell()` and `polyFill()` in `looks-toon.js`)
- Bounce: a parabola from the cycle phase, with a squash of a few percent at landing
- Blink: replace the eye with a line for 0.15 seconds
- Limbs are single thick strokes with a circle at the end
- Keep the palette to six or seven colours

## Assets

All in code. Original characters only. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A quick jazz or brass bed with a boing on each bounce. Practice note.

## What makes it look wrong

- Gradients, textures and thin outlines
- Realistic proportions
- Copying a recognisable show's characters

## Tested demo

This is the look from `art-forms/looks-toon.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=tv-cartoon` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'tv-cartoon': { kind: '2d', fps: 12, draw(g, t, W, H) {
    // a modern TV cartoon: thick even outlines, flat bright colour, simple geometric characters, drawn on twos with a squash and a blink
    const ts = held(t, 12), f = frameOf(t, 12), O = OUT; g.lineJoin = 'round'; g.lineCap = 'round';
    bg(g, W, H, '#8fd0ff'); ell(g, 780, 110, 54, 54, '#ffe14d', O, 8); for (let i = 0; i < 8; i++) { const a = (i / 8) * TAU + ts * 0.5; g.lineWidth = 8; g.strokeStyle = O; path(g, [[780 + Math.cos(a) * 72, 110 + Math.sin(a) * 72], [780 + Math.cos(a) * 92, 110 + Math.sin(a) * 92]], false); g.stroke(); }
    for (const [cx, cy, s] of [[200, 100, 1], [520, 70, 0.8]]) { const dx = Math.sin(ts * 0.5 + cx) * 14; g.beginPath(); g.arc(cx + dx - 40 * s, cy, 34 * s, Math.PI * 0.5, Math.PI * 1.5); g.arc(cx + dx, cy - 22 * s, 40 * s, Math.PI, 0); g.arc(cx + dx + 44 * s, cy, 34 * s, Math.PI * 1.5, Math.PI * 0.5); g.closePath(); g.fillStyle = '#fff'; g.fill(); g.strokeStyle = O; g.lineWidth = 8; g.stroke(); }
    polyFill(g, [[0, 410], [180, 350], [380, 400], [560, 340], [760, 400], [960, 360], [960, 540], [0, 540]], '#5fcf62', O, 8);
    ell(g, 860, 330, 54, 54, '#3fb34f', O, 8); g.fillStyle = '#b5782f'; g.strokeStyle = O; g.lineWidth = 8; g.fillRect(846, 370, 28, 60); g.strokeRect(846, 370, 28, 60);
    const hop = (ph) => { const u = (ts * 1.4 + ph) % 1, air = 4 * u * (1 - u), land = u < 0.12 ? (0.12 - u) / 0.12 : 0; return [air * 80, 1 + land * 0.2 - air * 0.06]; };
    const [h1, s1] = hop(0), blink = (ts % 2.2) < 0.15;   // the square one
    g.save(); g.translate(300, 470 - h1); g.scale(1 / s1, s1);
    for (const d of [-1, 1]) { g.lineWidth = 14; g.strokeStyle = O; path(g, [[d * 30, -10], [d * 34, 24 - h1 * 0.1]], false); g.stroke(); ell(g, d * 36, 26 - h1 * 0.1, 22, 12, '#e8433a', O, 8); }
    for (const d of [-1, 1]) { g.lineWidth = 14; g.strokeStyle = O; path(g, [[d * 62, -86], [d * (96 + h1 * 0.3), -120 - h1 * 0.4]], false); g.stroke(); ell(g, d * (100 + h1 * 0.3), -124 - h1 * 0.4, 14, 14, '#fff', O, 7); }
    g.beginPath(); g.roundRect(-64, -150, 128, 140, 26); g.fillStyle = '#ffcc19'; g.fill(); g.strokeStyle = O; g.lineWidth = 8; g.stroke();
    for (const d of [-1, 1]) { if (blink) { g.lineWidth = 7; path(g, [[d * 28 - 16, -100], [d * 28 + 16, -100]], false); g.stroke(); } else { ell(g, d * 28, -102, 18, 22, '#fff', O, 7); disc(g, d * 28 + 5, -98, 8, O); } }
    g.beginPath(); g.moveTo(-30, -66); g.quadraticCurveTo(0, -30, 30, -66); g.closePath(); g.fillStyle = '#7a1f2b'; g.fill(); g.stroke(); g.fillStyle = '#fff'; g.fillRect(-10, -66, 20, 10); g.restore();
    const [h2] = hop(0.5); g.save(); g.translate(600, 470 - h2);   // the round one
    for (const d of [-1, 1]) { g.lineWidth = 14; g.strokeStyle = O; path(g, [[d * 22, -6], [d * 26, 22]], false); g.stroke(); ell(g, d * 30, 24, 20, 11, '#3c67e0', O, 8); }
    ell(g, 0, -80, 74, 74, '#ff8bc2', O, 8); path(g, [[-48, -140], [-62, -190], [-20, -150]]); g.fillStyle = '#ff8bc2'; g.fill(); g.stroke(); path(g, [[48, -140], [62, -190], [20, -150]]); g.fill(); g.stroke();
    ell(g, 0, -92, 28, 32, '#fff', O, 7); disc(g, 6 + Math.sin(ts * 2) * 4, -90, 12, O); g.beginPath(); g.arc(0, -52, 24, 0.15, Math.PI - 0.15); g.lineWidth = 7; g.stroke();
    g.lineWidth = 14; path(g, [[-68, -70], [-110, -110 + Math.sin(ts * 9) * 14]], false); g.stroke(); g.restore();
    if (prog(ts % 0.7143, 0, 0.1) > 0 && ((ts * 1.4) % 1) < 0.1) for (let i = 0; i < 6; i++) polyFill(g, star(300 + Math.cos(i) * 90, 440 + Math.sin(i * 2) * 20, 12, 5, 4, 0.78), '#fff', O, 4);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Cartoon>
- <https://en.wikipedia.org/wiki/Limited_animation>
- <https://en.wikipedia.org/wiki/Flash_animation>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
