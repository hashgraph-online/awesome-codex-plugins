# Gothic cartoon

Also called: spooky cartoon, macabre cartoon, gothic animation.

Family: Drawn and painted. Cadence: steps 8 times a second. Usual tool: HyperFrames (canvas or SVG).

Spindly, hollow-eyed figures and crooked houses with lit windows under a pale moon, curly trees and bats, in purple and black: a cartoon that is spooky and funny at once.

Gothic fiction is a literary aesthetic of fear and haunting; the name comes from the Renaissance use of "gothic" for the medieval and barbaric, and the first work labelled Gothic was Horace Walpole's 1764 novel The Castle of Otranto.

Sourcing note: No source on the page describes a gothic cartoon look; the rules are a practice summary. The origin line is only the root of the word.

## What makes it read as this

- Tall, thin figures with long limbs, big heads, hollow eyes and spiky hair
- Crooked houses and trees: nothing stands straight; roofs are tall and pointed
- A palette of purple and near-black with a pale moon and a few lit windows
- Curly, spiral branches and moon marks
- Bats, stars and a low fog, with everything swaying a little

## Timing

Everything sways on twos, about 8 changes a second: houses lean back and forth, trees swing, figures step and bats flap.

## How to build it

- Lean every house with `ctx.transform(1, 0, lean, 1, 0, 0)` where `lean` is a small sine of stepped time plus a fixed tilt
- Trees: a curved trunk with spiral ends from `curlPts()`
- Figures: thin rectangles and strokes in local coordinates, scaled for depth
- A fog gradient across the ground and a few flickering windows

## Assets

All in code. Original characters only. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A creaking harpsichord or a music box, a distant wolf, wind. Practice note.

## What makes it look wrong

- Straight lines and symmetric buildings
- Bright, cheerful colour
- Copying a recognisable character or a studio's house style

## Tested demo

This is the look from `art-forms/looks-toon.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=gothic-cartoon` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'gothic-cartoon': { kind: '2d', fps: 8, draw(g, t, W, H) {
    // purple and black: a pale moon, crooked houses with lit windows, curly trees, and spindly, hollow-eyed figures that sway; everything leans a little and nothing is straight
    const ts = held(t, 8), f = frameOf(t, 8), O = '#0d0716'; g.lineJoin = 'round'; g.lineCap = 'round'; bg(g, W, H, '#2b1646');
    for (let i = 0; i < 40; i++) { const tw = (f + i) % 6; disc(g, hash(i, 1) * W, hash(i, 2) * 300, tw ? 1.6 : 2.6, '#d9cfee'); }
    ell(g, 700, 150, 92, 92, '#ece6cc', O, 6); for (const [x, y, r] of [[670, 120, 16], [725, 178, 12], [738, 112, 8]]) ell(g, x, y, r, r * 0.8, '#d3cba8'); g.strokeStyle = '#c4bb96'; g.lineWidth = 3; path(g, curlPts(700, 150, 40, 1.6), false); g.stroke();
    polyFill(g, [[0, 430], [200, 400], [420, 440], [640, 400], [960, 430], [960, 540], [0, 540]], '#1a0d2b', O, 6); for (let i = 0; i < 14; i++) { g.strokeStyle = '#5b3394'; g.lineWidth = 5; path(g, [[i * 74, 470 + (i % 2) * 20], [i * 74 + 50, 500 + (i % 2) * 20]], false); g.stroke(); }
    const house = (x, base, w, h, ph) => { const lean = Math.sin(ts * 1.4 + ph) * 0.03 + (ph % 2 ? 0.07 : -0.06); g.save(); g.translate(x, base); g.transform(1, 0, lean, 1, 0, 0); polyFill(g, [[-w / 2, 0], [w / 2 + 6, 0], [w / 2 - 8, -h], [-w / 2 + 10, -h - 6]], '#17102a', O, 6); polyFill(g, [[-w / 2 - 14, -h - 2], [w / 2 + 6, -h + 4], [4, -h - w * 1.3]], '#2a1646', O, 6); for (const [wx, wy] of [[-w / 4, -h * 0.62], [w / 5, -h * 0.35]]) { g.save(); g.translate(wx, wy); g.rotate(wx * 0.004 + 0.1); polyFill(g, [[-12, -16], [12, -14], [10, 16], [-10, 18]], (f + ph) % 9 ? '#f2e08a' : '#8a7a3a', O, 4); g.restore(); } g.restore(); };
    house(140, 450, 100, 190, 1); house(330, 446, 84, 140, 2); house(840, 450, 110, 210, 3);
    const tree = (x, base, h, ph) => { const sway = Math.sin(ts * 1.6 + ph) * 8; g.strokeStyle = O; g.lineWidth = 12; path(g, [[x, base], [x + 8 + sway * 0.3, base - h * 0.5], [x - 10 + sway, base - h]], false); g.stroke(); g.lineWidth = 5; for (const d of [-1, 1]) { path(g, curlPts(x + d * 34 + sway, base - h * 0.78 - 10, 30, 2.1, d), false); g.stroke(); path(g, [[x + 4, base - h * 0.55], [x + d * 24 + sway * 0.5, base - h * 0.66]], false); g.stroke(); } path(g, curlPts(x - 10 + sway, base - h - 22, 24, 2.2), false); g.stroke(); };
    tree(250, 450, 190, 0); tree(640, 440, 220, 2); tree(940, 460, 160, 4);
    const figure = (x, base, sc, ph) => {
      const sw = Math.sin(ts * 3 + ph) * 0.5; g.save(); g.translate(x, base); g.scale(sc, sc); g.lineWidth = 10; g.strokeStyle = O;
      for (const d of [-1, 1]) { path(g, [[d * 8, -120], [d * 8 + Math.sin(sw * d) * 26, -60], [d * 12 + Math.sin(sw * d) * 40, -4]], false); g.stroke(); ell(g, d * 12 + Math.sin(sw * d) * 52, 0, 22, 8, O); }
      polyFill(g, [[-20, -230], [20, -230], [14, -118], [-14, -118]], '#17102a', O, 6); for (let i = 0; i < 4; i++) { g.fillStyle = '#6b3fa0'; g.fillRect(-18 + i * 2, -218 + i * 24, 36 - i * 4, 8); }
      for (const d of [-1, 1]) { path(g, [[d * 18, -218], [d * (38 + Math.sin(sw + d) * 16), -156], [d * (30 + Math.sin(sw + d) * 22), -100]], false); g.stroke(); disc(g, d * (30 + Math.sin(sw + d) * 22), -96, 8, '#e8e2c8', O, 3); }
      g.lineWidth = 6; path(g, [[0, -230], [0, -258]], false); g.stroke(); ell(g, 0, -290, 32, 38, '#e8e2c8', O, 6); ell(g, -12, -294, 8, 13, O); ell(g, 12, -294, 8, 13, O); path(g, [[-10, -268], [-4, -272], [2, -266], [8, -272], [12, -268]], false); g.stroke(); polyFill(g, [[-30, -300], [-24, -346], [-10, -312], [0, -354], [10, -314], [26, -348], [30, -300]], O); g.restore();
    };
    figure(520, 460, 1, 0); figure(430, 470, 0.7, 2);
    for (let i = 0; i < 4; i++) { const bx = 120 + ((ts * 60 + i * 240) % 840), by = 90 + i * 30 + Math.sin(ts * 3 + i) * 12, fl = Math.sin(ts * 12 + i) * 10; polyFill(g, [[bx, by], [bx - 18, by - 12 - fl], [bx - 28, by + 2], [bx - 10, by + 4], [bx, by + 10], [bx + 10, by + 4], [bx + 28, by + 2], [bx + 18, by - 12 - fl]], O); }
    const fog = g.createLinearGradient(0, 400, 0, 540); fog.addColorStop(0, 'rgba(120,90,170,0)'); fog.addColorStop(1, 'rgba(120,90,170,.35)'); g.fillStyle = fog; g.fillRect(0, 400, W, 140);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Gothic_fiction>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
