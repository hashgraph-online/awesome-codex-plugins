# Film noir

Also called: noir, black and white noir.

Family: Screens and cinema. Cadence: smooth, full frame rate. Usual tool: HyperFrames (canvas), or Blender for a lit 3D scene.

High-contrast black and white: a wall striped by light through venetian blinds, a man in a fedora and trench coat under a street lamp, rain slanting through the lamp's cone, and a wet pavement.

Film noir is a Hollywood crime drama that emphasises cynical attitudes and motivations; the classic period is the 1940s and 1950s, with a low-key black-and-white visual style whose roots lie in German expressionist cinematography. The French critic Nino Frank first applied the term to Hollywood films in 1946.

## What makes it read as this

- Black and white with deep blacks and bright highlights
- Low-key light: most of the frame in shadow
- Venetian-blind stripes of light across walls and people
- A figure in a hat and long coat, lit from the side
- Rain, mist and smoke, lit where a lamp shines

## Timing

The blind stripes drift slowly, the rain falls, smoke curls and ripples spread; smooth, full frame rate.

## How to build it

- Stripes: parallelograms drawn with `lighter` at low opacity, drifting with time
- A lamp cone: a triangle with a vertical gradient; rain lines brighter inside it
- Silhouette the figure first, then add rim lines on the lit edge
- Add a vignette and fine grain

## Assets

All in code. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A muted trumpet, a slow saxophone, rain and distant footsteps. Practice note.

## What makes it look wrong

- Mid-grey lighting: noir needs black
- Colour
- Stripes with no direction or drift

## Tested demo

This is the look from `art-forms/looks-screen.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=film-noir` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'film-noir': { kind: '2d', fps: null, draw(g, t, W, H) {
    // high-contrast black and white: a wall striped with light through venetian blinds, a man in a fedora and trench coat under a street lamp, rain slanting through the lamp's cone, and a wet pavement
    g.fillStyle = '#030303'; g.fillRect(0, 0, W, H); const wall = g.createLinearGradient(0, 0, W, 0); wall.addColorStop(0, gray(60)); wall.addColorStop(1, gray(14)); g.fillStyle = wall; g.fillRect(0, 0, W, 390);
    g.fillStyle = gray(22); g.fillRect(0, 390, W, 150); const ref = g.createLinearGradient(760, 390, 760, H); ref.addColorStop(0, 'rgba(255,255,255,.35)'); ref.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = ref; g.fillRect(730, 390, 60, 150);
    const lamp = g.createLinearGradient(0, 100, 0, 400); lamp.addColorStop(0, 'rgba(255,255,255,.7)'); lamp.addColorStop(1, 'rgba(255,255,255,.1)'); g.fillStyle = lamp; g.beginPath(); g.moveTo(752, 110); g.lineTo(792, 110); g.lineTo(940, 410); g.lineTo(610, 410); g.closePath(); g.fill();
    g.fillStyle = gray(200); g.fillRect(768, 118, 8, 296); g.fillStyle = '#050505'; g.beginPath(); g.moveTo(742, 112); g.lineTo(800, 112); g.lineTo(784, 94); g.lineTo(758, 94); g.fill(); ell(g, 772, 120, 14, 8, gray(255));
    const wg = g.createRadialGradient(772, 170, 20, 772, 170, 300); wg.addColorStop(0, 'rgba(255,255,255,.5)'); wg.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = wg; g.fillRect(480, 0, 480, 410);
    g.save(); g.translate(640, 410); g.scale(1.3, 1.3); const K = '#040404', rim = gray(215), blk = (pts) => { path(g, pts); g.fillStyle = K; g.fill(); }, edge = (pts, w = 2, col = rim) => { path(g, pts, false); g.strokeStyle = col; g.lineWidth = w; g.stroke(); };
    blk([[-22, -84], [-4, -84], [-6, 0], [-28, 0]]); blk([[4, -84], [22, -84], [28, 0], [6, 0]]); ell(g, -20, 0, 16, 5, K); ell(g, 20, 0, 16, 5, K);   // trousers and shoes
    g.strokeStyle = K; g.lineCap = 'round'; g.lineWidth = 17; path(g, [[-48, -212], [-62, -158], [-58, -108]], false); g.stroke(); ell(g, -58, -100, 9, 9, K);   // the hanging arm
    blk([[-50, -214], [-36, -232], [36, -232], [50, -214], [58, -130], [64, -78], [0, -70], [-64, -78], [-58, -130]]);   // the trench coat
    blk([[-36, -232], [-24, -256], [-6, -230]]); blk([[36, -232], [24, -256], [6, -230]]);   // the collar, turned up
    g.fillStyle = gray(70); g.fillRect(-58, -136, 116, 11); g.fillStyle = gray(160); g.fillRect(-7, -138, 14, 15); g.strokeStyle = gray(70); g.lineWidth = 2; path(g, [[-34, -232], [0, -176], [34, -232]], false); g.stroke(); path(g, [[0, -176], [0, -138]], false); g.stroke(); path(g, [[-56, -126], [-62, -78]], false); g.stroke();   // belt, buckle, lapels
    g.strokeStyle = K; g.lineWidth = 15; path(g, [[44, -212], [68, -176], [28, -246]], false); g.stroke(); ell(g, 25, -248, 8, 8, K);   // the arm raised to the mouth
    ell(g, 0, -252, 16, 21, gray(46)); ell(g, 7, -252, 6, 18, gray(120));   // the face, mostly in shadow, with a sliver of light on the cheek
    blk([[-27, -270], [-24, -298], [-6, -304], [0, -297], [6, -304], [24, -298], [27, -270]]); g.fillStyle = gray(80); g.fillRect(-26, -280, 52, 7); ell(g, 0, -270, 53, 9, K);   // a fedora: pinched crown, band and a wide brim
    g.strokeStyle = gray(235); g.lineWidth = 2.4; path(g, [[4, -244], [19, -247]], false); g.stroke(); ell(g, 21, -247, 2.6, 2.6, '#fff');   // the cigarette and its ember
    edge([[50, -214], [58, -130], [64, -78]]); edge([[36, -232], [24, -256]]); edge([[53, -270], [40, -268]], 2); edge([[24, -298], [27, -272]], 1.6);
    g.restore();
    g.strokeStyle = 'rgba(255,255,255,.5)'; g.lineWidth = 2; g.beginPath(); for (let i = 0; i < 16; i++) g.lineTo(669 + Math.sin(t * 2 + i * 0.55) * (3 + i * 1.5), 90 - i * 11); g.stroke();   // a curl of smoke
    g.save(); g.globalCompositeOperation = 'lighter'; const drift = (t * 7) % 52; g.fillStyle = 'rgba(235,235,235,.3)'; for (let i = -2; i < 14; i++) { const y = i * 52 + drift; g.beginPath(); g.moveTo(0, y); g.lineTo(540, y + 96); g.lineTo(540, y + 126); g.lineTo(0, y + 30); g.closePath(); g.fill(); } g.restore();
    for (let i = 0; i < 220; i++) { const x = (hash(i, 1) * W + t * 40) % W, y = (hash(i, 2) * H + t * 1000 * (0.7 + hash(i, 3) * 0.5)) % H, inCone = y > 110 && Math.abs(x - 772) < (y - 110) * 0.55 + 20; g.strokeStyle = `rgba(255,255,255,${inCone ? 0.7 : 0.14})`; g.lineWidth = 1.2; g.beginPath(); g.moveTo(x, y); g.lineTo(x - 6, y + 28); g.stroke(); }
    for (let i = 0; i < 6; i++) { const r = ((t * 1.4 + hash(i, 5)) % 1); g.strokeStyle = `rgba(255,255,255,${0.5 * (1 - r)})`; g.lineWidth = 1.4; g.beginPath(); g.ellipse(680 + hash(i, 6) * 220, 430 + hash(i, 7) * 80, r * 30, r * 7, 0, 0, TAU); g.stroke(); }
    vignette(g, W, H, 0.7, 0.4); speckle(g, W, H, 77, 30, [255, 255, 255]);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Film_noir>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
