# Charcoal

Also called: charcoal drawing, vine charcoal.

Family: Drawn and painted. Cadence: steps 8 times a second. Usual tool: HyperFrames (canvas).

Soft black dust smeared and rubbed on rough paper: dark masses with crumbling edges, greys made by rubbing, and highlights lifted out with an eraser.

Charcoal was often a component of cave painting, with examples at least 28,000 years old. Artists use vine charcoal (wood burned in a kiln without air) or compressed charcoal held by a gum or wax binder; its marks are much less permanent than graphite, so lines are easily erased and blended.

## What makes it read as this

- Soft, uneven dark masses; never a clean line or a hard outline
- Edges crumble into specks and the paper grain shows through the black
- Greys come from rubbing, not from a colour
- Highlights are pale marks lifted out of the dark with an eraser: a sun, a glint on a trunk
- One warm paper grey and black, nothing else

## Timing

Marks are laid in order over about 3 seconds: broad rubbed sky first, then the dark mass, then the line work, then the lifted highlights. The picture steps about 8 times a second.

## How to build it

- Dabs: many overlapping low-opacity circles along a line, each with a seeded size and offset (`dabs()` in `looks-painted.js`); large dabs use a radial gradient so they stay soft
- Rubbed sky: long, uneven strokes of varying width at low opacity
- Eraser: paint pale strokes and a soft disc in the paper colour over the dark
- Finish with coarse specks in the paper colour (`tooth()` with scale 2) and a dark vignette

## Assets

All in code. A scan of grey sketching paper helps if the user has one. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Dry scratching and a soft smudging rub, room tone. Practice note.

## What makes it look wrong

- Smooth airbrushed gradients with no grain
- Crisp vector outlines on the tree or the figure
- Pure black on pure white: charcoal lives on a warm grey ground

## Tested demo

This is the look from `art-forms/looks-painted.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=charcoal` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  charcoal: { kind: '2d', fps: 8, draw(g, t, W, H) {
    // a lone tree on a hill under a low sun: soft smears, rough dabbed edges, a sun and highlights rubbed out with an eraser
    const ts = held(t, 8), P = [222, 216, 204], bx = W * 0.3, by = H * 0.8;
    bg(g, W, H, rgba(P));
    for (let i = 0; i < 6; i++) for (let j = 0; j < 12; j++) {   // the sky is rubbed in long, uneven sweeps of the side of a stick
      const y = 10 + i * 56 + hash(i, j, 1) * 60, k = prog(ts, 0.1 + i * 0.1, 0.6), x0 = -30 + hash(i, j, 2) * 300, x1 = x0 + 260 + hash(i, j, 3) * 700;
      g.strokeStyle = rgba([58, 56, 60], (0.22 - i * 0.025) * (0.4 + hash(i, j, 4))); g.lineWidth = 3 + hash(i, j, 5) * 16; g.lineCap = 'round'; strokePart(g, [[x0, y], [(x0 + x1) / 2, y + jit(i, j, 14)], [x1, y + jit(i, j + 9, 14)]], k);
    }
    const sun = g.createRadialGradient(W * 0.66, H * 0.34, 10, W * 0.66, H * 0.34, 150); sun.addColorStop(0, rgba(P, 1)); sun.addColorStop(0.45, rgba(P, 0.7)); sun.addColorStop(1, rgba(P, 0));
    g.fillStyle = sun; g.globalAlpha = easeOut(prog(ts, 0.3, 0.6)); g.fillRect(W * 0.4, 0, W * 0.6, H * 0.7);
    g.fillStyle = rgba(P, 0.95); blob(g, W * 0.66, H * 0.34, 50, 77, 0.07); g.fill(); g.globalAlpha = 1;   // the sun: a clean disc lifted out with a kneaded eraser
    for (let pass = 0; pass < 2; pass++) for (let c = 0; c <= 40; c++) {
      const x = (c * W) / 40, top = H * 0.78 + Math.sin(c * 0.33) * 22 + Math.sin(c * 0.11) * 18 + hash(c, 4) * 8;
      if (c / 40 < prog(ts, pass * 0.4, 0.7)) dabs(g, x, top, x + jit(c, 1, 8), H + 20, 48, 0.17, 100 + c + pass * 50, 1, [20, 19, 22]);
    }
    const limb = (x, y, a, len, w, depth, seed, start) => {
      const x1 = x + Math.cos(a) * len, y1 = y + Math.sin(a) * len; dabs(g, x, y, x1, y1, w, 0.55, seed, easeOut(prog(ts, start, 0.3)), [18, 17, 20]);
      if (!depth) return;
      for (let c = 0; c < 2 + (hash(seed, depth) > 0.5 ? 1 : 0); c++) limb(x1, y1, a + (c === 2 ? jit(seed, c, 0.25) : (c ? 1 : -1) * (0.34 + 0.34 * hash(seed, c, depth))), len * (0.7 + 0.1 * hash(seed, c)), w * 0.62, depth - 1, seed * 7 + c + 1, start + 0.2);
    };
    limb(bx, by + 6, -Math.PI / 2 + 0.1, 110, 24, 4, 3, 0);
    g.strokeStyle = rgba(P, 0.5); g.lineWidth = 5; g.lineCap = 'round'; strokePart(g, [[bx - 9, by - 2], [bx - 5, by - 50], [bx - 3, by - 96]], easeOut(prog(ts, 1.4, 0.4)), 0, 0.8);   // a highlight lifted off the trunk
    dabs(g, W * 0.52, H * 0.2, W * 0.92, H * 0.12, 11, 0.13, 22, prog(ts, 1.8, 0.5), P);
    for (let i = 0; i < 3; i++) { g.strokeStyle = 'rgba(30,29,32,.8)'; g.lineWidth = 3; g.lineCap = 'round'; strokePart(g, [[W * 0.74 + i * 34, H * 0.2 + i * 9], [W * 0.755 + i * 34, H * 0.2 + i * 9 - 8], [W * 0.77 + i * 34, H * 0.2 + i * 9]], prog(ts, 2.8 + i * 0.12, 0.2)); }
    dabs(g, bx, by + 14, bx + 150, by + 34, 28, 0.06, 23, prog(ts, 2.2, 0.6), [20, 19, 22]);
    speckle(g, W, H, 31, 150, P, 2);
    const v = g.createRadialGradient(W / 2, H / 2, H * 0.4, W / 2, H / 2, H * 0.95); v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(30,26,20,.32)'); g.fillStyle = v; g.fillRect(0, 0, W, H);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Charcoal_(art)>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
