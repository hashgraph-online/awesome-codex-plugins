# Ukiyo-e woodblock

Also called: ukiyo-e, ukiyoe, japanese woodblock print, floating world print.

Family: Folk and print traditions. Cadence: steps 8 times a second. Usual tool: HyperFrames (canvas or SVG).

A Japanese woodblock print: flat areas of colour, fine ink outlines, a great curling wave of deep blue with claw-like fingers of foam, a pale banded sky, a small distant mountain and a red seal.

Ukiyo-e is a genre of Japanese art that flourished from the 17th through 19th centuries, with woodblock prints and paintings; the term means "pictures of the floating world". By the 1740s artists were using several blocks to print areas of colour, and Hokusai's The Great Wave off Kanagawa is one of the best-known works of Japanese art.

Sourcing note: Wikipedia's ukiyo-e article does not describe Prussian blue, wave contour lines or claw-like foam; those rules are a practice summary from looking at the genre, not sourced facts.

## What makes it read as this

- Flat colour areas, no gradients except a soft band at the top of the sky
- Fine ink outlines round every shape
- A deep Prussian-style blue for water, with darker contour lines that follow the wave
- Foam as claw-like white fingers curling from the crest, with a few spray dots
- A small mountain far away, a red seal, a thin border, paper grain

## Timing

The wave rises and the foam fingers grow over about 2 seconds; the sea and boats bob gently. The picture steps about 8 times a second.

## How to build it

- Wave: a closed spline through hand-placed points (`closed()`), filled and outlined
- Contour lines: scale the same outline about its centre several times and clip them to the wave
- Foam fingers: tapering bands along short curves (`ribbon()`), one per crest point, growing in turn
- Sea: a polyline whose height follows a sine of stepped time
- Add paper grain with `speckle()`

## Assets

All in code. Public-domain scans of historic prints are a better source for real prints; check the museum's terms. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A shamisen and a taiko, the sound of surf. Practice note.

## What makes it look wrong

- Smooth shading and gradients on the water
- Thick or uneven outlines: the lines are fine
- Copying an existing print: the demo is an original study

## Tested demo

This is the look from `art-forms/looks-toon.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=ukiyo-e` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'ukiyo-e': { kind: '2d', fps: 8, draw(g, t, W, H) {
    // a woodblock print: flat colour areas and fine ink outlines, a great curling wave of Prussian blue with claw-like fingers of foam, a pale banded sky, a small mountain, and a red seal
    const ts = held(t, 8), INKB = '#14203a', BLUE = '#1f4a86', DEEP = '#16345f'; bg(g, W, H, '#efe3c6');
    ['#d8c79c', '#e3d3ab'].forEach((c, i) => { g.fillStyle = c; g.fillRect(0, i * 34, W, 34 + (i ? 0 : 1)); });
    for (const [cx, cy, w] of [[700, 120, 230], [860, 196, 190], [300, 70, 180]]) { g.fillStyle = '#e8dcc0'; g.beginPath(); g.roundRect(cx - w / 2, cy - 10, w, 20, 10); g.fill(); }
    const mk = easeOut(prog(ts, 0.2, 0.6)); polyFill(g, [[600, 456], [690, 346], [718, 330], [742, 346], [870, 456]], '#3c6aa3', INKB, 2); polyFill(g, [[690, 346], [718, 330], [742, 346], [724, 356], [716, 346], [706, 362], [696, 352]], '#f4efe0', INKB, 1.6);
    const sea = Array.from({ length: 30 }, (_, i) => [i * 34, 466 + Math.sin(i * 0.9 + ts * 1.6) * 7]); polyFill(g, [...sea, [W, H], [0, H]], BLUE, INKB, 2);
    for (let r = 0; r < 5; r++) { g.strokeStyle = 'rgba(240,235,210,.55)'; g.lineWidth = 1.6; path(g, Array.from({ length: 24 }, (_, i) => [40 + i * 40 + r * 14, 484 + r * 11 + Math.sin(i + r + ts * 1.6) * 3]), false); g.stroke(); }
    const ctrl = [[-30, 560], [-30, 330], [40, 250], [130, 170], [240, 112], [350, 92], [440, 108], [500, 150], [512, 205], [478, 225], [446, 200], [418, 178], [392, 198], [410, 246], [470, 310], [560, 388], [660, 450], [760, 500], [800, 560]];
    const wk = prog(ts, 0.1, 1.2), wave = closed(ctrl, 8); g.save(); g.translate(0, (1 - easeOut(wk)) * 120);
    polyFill(g, wave, BLUE, INKB, 3);
    g.save(); path(g, wave); g.clip(); for (let i = 1; i <= 7; i++) { g.strokeStyle = i % 2 ? DEEP : '#2b5c9e'; g.lineWidth = 2.4; path(g, scaleAbout(wave, 1 - i * 0.07).map(([x, y]) => [x + i * 7, y + i * 5]), false); g.stroke(); } g.restore();
    const crest = spline([[170, 150], [240, 112], [350, 92], [440, 108], [500, 150], [512, 205]], 12), n = 10;
    for (let i = 0; i < n; i++) {   // foam fingers: curved, tapering claws that reach out and down from the crest
      const k = easeOut(prog(ts, 0.8 + i * 0.1, 0.5)); if (k <= 0) continue; const [bx, by] = crest[Math.floor((i / n) * (crest.length - 4)) + 2], L = 24 + 6 * Math.sin(i * 1.7);
      polyFill(g, ribbon([[bx, by], [bx + L * 0.7 * k, by - 8 * k], [bx + L * 1.3 * k, by + 8 * k], [bx + L * 1.5 * k, by + 30 * k]], 8, 1.2), '#f6f2e4', INKB, 1.6);
    }
    for (let i = 0; i < 46; i++) { const k = prog(ts, 1.2 + hash(i, 1) * 1.6, 0.3); if (k > 0) disc(g, 250 + hash(i, 2) * 300 + k * 12, 90 + hash(i, 3) * 130 + (i % 3) * 8, 1.6 + hash(i, 4) * 3, '#f6f2e4'); }
    g.restore();
    for (const [bx, ph] of [[640, 0], [790, 2]]) { const by = 492 + Math.sin(ts * 2 + ph) * 4; polyFill(g, [[bx - 50, by], [bx + 50, by], [bx + 36, by + 9], [bx - 38, by + 9]], '#8a5a2b', INKB, 1.6); for (let i = 0; i < 4; i++) disc(g, bx - 24 + i * 16, by - 4, 3.4, '#e9d9b0'); }
    g.strokeStyle = INKB; g.lineWidth = 3; g.strokeRect(14, 14, W - 28, H - 28); g.fillStyle = '#c8322a'; g.fillRect(878, 30, 40, 58); g.fillStyle = '#efe3c6'; g.fillRect(886, 40, 24, 5); g.fillRect(886, 52, 24, 5); g.fillRect(896, 62, 5, 18);
    speckle(g, W, H, 3, 50, [110, 80, 40]);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Ukiyo-e>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
