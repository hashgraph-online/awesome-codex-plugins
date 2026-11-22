# Archive documentary: pan and zoom over stills

Also called: ken burns, ken burns effect, archive documentary, photo documentary.

Family: Screens and cinema. Cadence: smooth, full frame rate. Usual tool: HyperFrames (canvas or CSS transforms).

A slow pan and zoom over still photographs laid on a desk, each with a white border and a shadow, with a lower-third caption and date that slide in for each picture, over film grain.

The Ken Burns effect is a panning and zooming technique used in film and video from still images, named for the American documentarian Ken Burns. It is principally used when film or video material is not available, giving action to stills by slowly zooming in on subjects of interest and panning from one to another.

## What makes it read as this

- A slow, eased camera: zoom in on one photograph, then pan to the next
- Photographs with white borders, slight tilts and drop shadows
- A lower-third caption and date that slide in for each picture
- Film grain, a vignette and a dark desk
- Aged photographs: sepia tones and a darkened edge

## Timing

The camera moves between keyframes with `easeInOut`; a picture is held for 3 to 4 seconds. Smooth, full frame rate.

## How to build it

- Keyframe the camera as (time, centre x, centre y, zoom) and interpolate with `easeInOut`
- Draw the world with `translate(W / 2, H / 2)`, `scale(zoom)`, `translate(-cx, -cy)`
- Each photograph: a rotated white frame with `shadowBlur`, a clipped picture, and a radial darkening
- Captions slide in from the left with `easeOut` when the camera reaches a new photograph
- Real route: animate the position and scale of image layers in HyperFrames

## Assets

Use only photographs the user owns or may reuse; the pictures here are drawn shapes. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A piano, a cello, an archive-style narrator and room tone. Practice note.

## What makes it look wrong

- A fast or jerky camera
- No border, shadow or desk: the stills must look like objects
- Presenting invented pictures as real archive

## Tested demo

This is the look from `art-forms/looks-screen.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=archive-documentary` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'archive-documentary': { kind: '2d', fps: null, draw(g, t, W, H) {
    // a slow pan and zoom over three still photographs laid on a desk, each with a white border and a shadow, then a lower-third caption and date that slide in for each picture, over film grain
    const KF = [[0, 300, 260, 1.2], [2.6, 330, 250, 1.7], [4.6, 860, 210, 1.5], [7, 870, 200, 1.9], [9, 1380, 320, 1.4]], seg = Math.max(0, KF.findIndex((k, i) => i < KF.length - 1 && t < KF[i + 1][0])), a = KF[seg], b = KF[Math.min(seg + 1, KF.length - 1)], k = t >= KF[KF.length - 1][0] ? 1 : easeInOut(clamp((t - a[0]) / (b[0] - a[0])));
    const cx = lerp(a[1], b[1], k), cy = lerp(a[2], b[2], k), sc = lerp(a[3], b[3], k); g.fillStyle = '#17120e'; g.fillRect(0, 0, W, H);
    g.save(); g.translate(W / 2, H / 2); g.scale(sc, sc); g.translate(-cx, -cy);
    for (let i = 0; i < 80; i++) { g.fillStyle = `rgba(255,240,210,${0.02 + hash(i, 1) * 0.03})`; g.fillRect(hash(i, 2) * 1800 - 200, hash(i, 3) * 800 - 100, 60 + hash(i, 4) * 200, 2); }
    const photo = (x, y, w, h, a2, kind) => {
      g.save(); g.translate(x, y); g.rotate(a2); g.shadowColor = 'rgba(0,0,0,.6)'; g.shadowBlur = 28; g.shadowOffsetX = 8; g.shadowOffsetY = 12; g.fillStyle = '#efe6d2'; g.fillRect(-w / 2 - 14, -h / 2 - 14, w + 28, h + 28); g.shadowColor = 'transparent';
      g.save(); g.beginPath(); g.rect(-w / 2, -h / 2, w, h); g.clip(); const sky = g.createLinearGradient(0, -h / 2, 0, h / 2); sky.addColorStop(0, sepia(0.88)); sky.addColorStop(1, sepia(0.55)); g.fillStyle = sky; g.fillRect(-w / 2, -h / 2, w, h);
      if (kind === 0) { g.fillStyle = sepia(0.32); g.fillRect(-w / 2, 20, w, h / 2); g.fillStyle = sepia(0.08); g.fillRect(-120, -10, 220, 40); g.fillRect(-60, -60, 14, 60); g.fillRect(10, -90, 10, 90); g.beginPath(); g.moveTo(-130, 30); g.lineTo(120, 30); g.lineTo(90, 52); g.lineTo(-100, 52); g.fill(); for (let i = 0; i < 4; i++) { g.fillRect(-w / 2 + 30 + i * 28, -20, 5, 60); } }
      else if (kind === 1) { for (let i = 0; i < 6; i++) { g.fillStyle = sepia(0.12 + i * 0.05); const hx = -w / 2 + i * (w / 6), hh = 90 + hash(i, 5) * 50; g.fillRect(hx, 40 - hh, w / 6 - 6, hh + 70); g.beginPath(); g.moveTo(hx - 4, 40 - hh); g.lineTo(hx + w / 12 - 3, 10 - hh); g.lineTo(hx + w / 6 - 2, 40 - hh); g.fill(); } g.fillStyle = sepia(0.3); g.beginPath(); g.moveTo(-w / 2, h / 2); g.lineTo(-30, 60); g.lineTo(30, 60); g.lineTo(w / 2, h / 2); g.fill(); }
      else { g.fillStyle = sepia(0.3); g.beginPath(); g.moveTo(-w / 2, 70); g.lineTo(-90, -80); g.lineTo(-30, -10); g.lineTo(60, -110); g.lineTo(150, 20); g.lineTo(w / 2, 70); g.lineTo(w / 2, h / 2); g.lineTo(-w / 2, h / 2); g.fill(); g.fillStyle = sepia(0.9); g.beginPath(); g.moveTo(40, -80); g.lineTo(60, -110); g.lineTo(82, -76); g.lineTo(60, -86); g.fill(); }
      const v = g.createRadialGradient(0, 0, h * 0.3, 0, 0, w * 0.62); v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(30,18,6,.55)'); g.fillStyle = v; g.fillRect(-w / 2, -h / 2, w, h); g.restore(); g.restore();
    };
    photo(300, 260, 440, 300, -0.02, 0); photo(860, 200, 400, 280, 0.025, 1); photo(1380, 320, 420, 300, -0.015, 2); g.restore();
    const idx = t < 3.3 ? 0 : t < 7.3 ? 1 : 2, st = [0, 3.3, 7.3][idx], slide = easeOut(prog(t, st, 0.5)), caps = [['HARBOUR AT DAWN', 'MARCH 1931'], ['MARKET STREET', 'JUNE 1934'], ['THE MOUNTAIN ROAD', 'OCTOBER 1937']][idx];
    g.save(); g.translate(lerp(-520, 0, slide), 0); g.fillStyle = 'rgba(12,10,8,.82)'; g.fillRect(40, 418, 470, 82); g.fillStyle = '#d6a21f'; g.fillRect(40, 418, 6, 82); g.fillStyle = '#f4ead4'; g.font = `700 30px ${FONT}`; g.fillText(caps[0], 62, 456); g.fillStyle = '#c9b88e'; g.font = `400 20px ${FONT}`; g.fillText(caps[1], 62, 486); g.restore();
    vignette(g, W, H, 0.55, 0.4); speckle(g, W, H, 70 + (Math.floor(t * 12) % 8), 34, [255, 245, 220]);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Ken_Burns_effect>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
