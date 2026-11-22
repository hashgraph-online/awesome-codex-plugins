# Manga (black and white with screentone)

Also called: manga style, black and white manga, manga panels.

Family: Drawn and painted. Cadence: steps 8 times a second. Usual tool: HyperFrames (canvas or SVG).

Black and white only: inked panels with thick borders, screentone dots for grey, speed lines and bursts, and one dramatic moment drawn large.

Manga are comics or graphic novels originating from Japan; most conform to a style developed in Japan in the late 19th century, with a long history in earlier Japanese art.

## What makes it read as this

- Pure black and pure white: no greys and no colour
- Panels with thick black borders and uneven sizes: one big panel for the moment, smaller ones around it
- Tone: halftone dots of one size per area, at a slant, for shadow and mood
- Speed lines that converge on the point of impact; a burst shape for the hit
- Bold line weights and spiky hair; faces in extreme close-up for emotion

## Timing

Panels slam in one after another, 0.1 to 2.2 seconds, and the speed lines re-roll about 8 times a second. Stepped, not smooth.

## How to build it

- Each panel: a clipped rectangle that scales from 1.12 to 1 with `easeOut` as it appears
- Speed lines: thin black wedges between two radii with a seeded length per line, re-seeded on each step (`speedLines()` in `looks-toon.js`)
- Screentone: a rotated dot grid whose radius follows a value function (`halftone()` in `looks-folk.js`)
- Draw figures from local coordinates and mirror them for the second fighter
- Use only `#000` and `#fff`: no antialiased greys except at edges

## Assets

All in code. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Sharp impact hits, a sword-ring or a drum, silence between panels. Practice note.

## What makes it look wrong

- Any grey or colour
- Panels that are all the same size
- Speed lines that do not converge on the action

## Tested demo

This is the look from `art-forms/looks-toon.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=manga` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  manga: { kind: '2d', fps: 8, draw(g, t, W, H) {
    // black and white only: three inked panels, screentone dots, speed lines, and one dramatic moment, two fighters meeting in a burst
    const ts = held(t, 8), f = frameOf(t, 8); bg(g, W, H, WHITE);
    const panel = (x, y, w, h, start, body) => {
      const k = easeOut(prog(ts, start, 0.25)); if (k <= 0) return; g.save(); g.translate(x + w / 2, y + h / 2); g.scale(lerp(1.12, 1, k), lerp(1.12, 1, k)); g.globalAlpha = k; g.translate(-x - w / 2, -y - h / 2);
      g.beginPath(); g.rect(x, y, w, h); g.fillStyle = WHITE; g.fill(); g.save(); g.clip(); body(); g.restore(); g.strokeStyle = BLACK; g.lineWidth = 6; g.strokeRect(x, y, w, h); g.restore();
    };
    panel(24, 24, 912, 300, 0.1, () => {
      speedLines(g, 480, 120, 70, 760, 110, f);
      fighter(g, 330, 214, 1.25, 1, 'black', f); fighter(g, 630, 214, 1.25, -1, 'tone', f);
      if (prog(ts, 0.8, 0.2) > 0) { const b = star(480, 118, 84 + (f % 2) * 8, 44, 14, 0.1, 0.5, f % 3); polyFill(g, b, WHITE, BLACK, 6); polyFill(g, star(480, 118, 40, 20, 9, 0.4, 0.3, 7), BLACK); }
    });
    panel(24, 340, 448, 176, 1.4, () => {
      tone(g, [24, 340, 472, 516], 6, (x, y) => (y - 340) / 176 * 0.9 + 0.08);
      g.save(); g.beginPath(); g.ellipse(248, 430, 150, 62, -0.08, 0, TAU); g.clip(); g.fillStyle = WHITE; g.fillRect(90, 360, 320, 140); g.restore();   // a huge eye
      g.beginPath(); g.ellipse(248, 430, 150, 62, -0.08, 0, TAU); g.lineWidth = 8; g.strokeStyle = BLACK; g.stroke(); disc(g, 260, 432, 52, BLACK); disc(g, 240, 412, 15, WHITE); disc(g, 276, 450, 7, WHITE);
      polyFill(g, [[96, 410], [250, 352], [412, 396], [404, 372], [250, 330], [90, 386]], BLACK); for (let i = 0; i < 4; i++) { g.lineWidth = 2.4; g.strokeStyle = BLACK; path(g, [[150 + i * 36, 496], [160 + i * 36, 480]], false); g.stroke(); }
      polyFill(g, [[400, 392], [412, 420], [400, 432], [388, 420]], WHITE, BLACK, 3);
    });
    panel(488, 340, 448, 176, 2.2, () => {
      for (let i = 0; i < 28; i++) { const y = 340 + hash(i, 1) * 176, x0 = 488 + hash(i, f % 3, 2) * 120; g.fillStyle = BLACK; path(g, [[x0, y], [936, y - 1.5 - hash(i, 3) * 2], [936, y + 1.5 + hash(i, 3) * 2]]); g.fill(); }
      const cx = 740 + (f % 2) * 4; polyFill(g, star(cx, 430, 74, 40, 12, 0.2, 0.5, 5), WHITE, BLACK, 6); g.save(); g.translate(cx, 430); g.rotate(-0.5); disc(g, 0, -22, 14, WHITE); g.lineWidth = 4; g.strokeStyle = BLACK; g.beginPath(); g.arc(0, -22, 14, 0, TAU); g.stroke(); g.lineWidth = 12; g.beginPath(); g.moveTo(0, -8); g.lineTo(0, 24); g.moveTo(0, 0); g.lineTo(-24, 14); g.moveTo(0, 0); g.lineTo(24, -4); g.moveTo(0, 24); g.lineTo(-14, 52); g.moveTo(0, 24); g.lineTo(18, 50); g.stroke(); g.restore();   // a figure thrown clear
    });
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Manga>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
