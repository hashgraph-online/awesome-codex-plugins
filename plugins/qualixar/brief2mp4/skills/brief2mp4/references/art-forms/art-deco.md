# Art deco

Also called: art déco, jazz age deco.

Family: Folk and print traditions. Cadence: smooth, full frame rate. Usual tool: HyperFrames (canvas or SVG).

Gold lines, sunbursts and stepped, symmetric geometry on a deep ground: fans and arcs, a tower in steps, zigzag borders and small stars, in gold on navy and burgundy.

Art Deco first appeared in Paris in the 1910s, just before the First World War, and flourished internationally in the 1920s and early 1930s; the name came into use after the 1925 Paris exhibition of decorative and industrial arts. It has its origin in the bold geometric forms of the Vienna Secession and Cubism, and in New York the Empire State and Chrysler Buildings are monuments to the style.

## What makes it read as this

- Strict symmetry about a vertical axis
- Gold or light-gold lines on a deep ground: black, navy, burgundy or emerald
- Sunburst rays, fans and concentric arcs
- Stepped shapes: towers and frames in steps
- Zigzag borders, chevrons and small star sparkles

## Timing

Rays and arcs grow out from the centre over about 3 seconds, then the tower rises in steps. Smooth, full frame rate, with a slow twinkle.

## How to build it

- Sunburst: wedges that alternate fill and ground, each edge a gold line drawn to a growing radius
- Arcs: `ctx.arc` from pi to a growing angle at several radii
- Tower: nested rectangles of falling width, each rising in turn
- Mirror the side decoration with `ctx.scale(-1, 1)` so it is exactly symmetric
- Sparkles: eight-point stars whose size follows a sine of time

## Assets

All in code. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Brass and muted trumpet, a swing bed. Practice note.

## What makes it look wrong

- Asymmetry
- Soft gradients and rounded shapes
- Using teal or mint: this skill leaves them out

## Tested demo

This is the look from `art-forms/looks-folk.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=art-deco` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'art-deco': { kind: '2d', fps: null, draw(g, t, W, H) {
    // symmetric and stepped: a gold sunburst over burgundy wedges, fan arcs, a stepped tower with a spire, and zigzag borders, on a deep navy ground
    const GOLD = '#d9ad4f', LIGHT = '#f3dc92', WINE = '#5e1426', NAVY = '#0b1226', cx = 480, cy = 530; bg(g, W, H, NAVY); g.lineCap = 'round'; g.lineJoin = 'miter';
    const n = 28; for (let i = 0; i < n; i++) {   // the sunburst: wedges alternate burgundy and navy, each edge a gold line that grows out from the centre
      const a0 = Math.PI + (i * Math.PI) / n, a1 = a0 + Math.PI / n, r = 900 * easeOut(prog(t, 0.1 + i * 0.03, 0.9));
      if (i % 2) { g.fillStyle = WINE; g.beginPath(); g.moveTo(cx, cy); g.arc(cx, cy, r, a0, a1); g.closePath(); g.fill(); }
      g.strokeStyle = GOLD; g.lineWidth = 2.2; g.beginPath(); g.moveTo(cx, cy); g.lineTo(cx + Math.cos(a0) * r, cy + Math.sin(a0) * r); g.stroke();
    }
    for (const [r, w] of [[130, 4], [200, 2.4], [280, 2.4], [360, 4], [440, 2.4]]) { g.strokeStyle = r === 130 || r === 360 ? LIGHT : GOLD; g.lineWidth = w; g.beginPath(); g.arc(cx, cy, r, Math.PI, Math.PI + Math.PI * easeInOut(prog(t, 0.5 + r / 500, 1.2))); g.stroke(); }
    g.strokeStyle = GOLD; g.lineWidth = 1.6; for (let ring = 0; ring < 3; ring++) for (let i = 0; i < 9 - ring; i++) { const r = 165 + ring * 40, a = Math.PI + ((i + 0.5) / (9 - ring)) * Math.PI; if (prog(t, 1.4 + ring * 0.2, 0.8) > i / 9) { g.beginPath(); g.arc(cx + Math.cos(a) * r, cy + Math.sin(a) * r, 18, a - 1.57, a + 1.57); g.stroke(); } }   // fan scallops
    const tk = easeOut(prog(t, 1.2, 1.3));   // the tower rises in steps, symmetric about the middle
    const steps = [[84, 520], [66, 440], [48, 370], [32, 310], [16, 250], [5, 196]]; g.fillStyle = NAVY; g.strokeStyle = LIGHT; g.lineWidth = 3;
    steps.forEach(([hw, top], i) => { const y = lerp(H, top, tk); g.fillRect(cx - hw, y, hw * 2, H - y); g.strokeRect(cx - hw, y, hw * 2, H - y); });
    g.strokeStyle = GOLD; g.lineWidth = 1.6; for (const dx of [-60, -36, -12, 12, 36, 60]) { g.beginPath(); g.moveTo(cx + dx, H); g.lineTo(cx + dx, lerp(H, 470, tk)); g.stroke(); }
    for (const side of [-1, 1]) { g.save(); g.translate(cx, 0); g.scale(side, 1); const k = prog(t, 0.3, 1.5);   // zigzag borders and stepped side frames, mirrored
      g.strokeStyle = GOLD; g.lineWidth = 2.4; strokePart(g, Array.from({ length: 24 }, (_, i) => [i * 20, 24 + (i % 2) * 18]), k); strokePart(g, Array.from({ length: 24 }, (_, i) => [i * 20, H - 24 - (i % 2) * 18]), k);
      for (let i = 0; i < 4; i++) strokePart(g, [[400 - i * 26, H], [400 - i * 26, 120 + i * 40], [374 - i * 26, 120 + i * 40]], prog(t, 0.6 + i * 0.2, 0.8));
      g.restore(); }
    for (let i = 0; i < 6; i++) { const x = 60 + i * 168 + (i % 2) * 20, y = 90 + (i % 3) * 40, k = (Math.sin(t * 2.4 + i * 1.7) + 1) / 2, r = 5 + 8 * k; g.fillStyle = LIGHT; g.beginPath(); g.moveTo(x, y - r); g.lineTo(x + r * 0.28, y - r * 0.28); g.lineTo(x + r, y); g.lineTo(x + r * 0.28, y + r * 0.28); g.lineTo(x, y + r); g.lineTo(x - r * 0.28, y + r * 0.28); g.lineTo(x - r, y); g.lineTo(x - r * 0.28, y - r * 0.28); g.closePath(); g.fill(); }
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Art_Deco>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
