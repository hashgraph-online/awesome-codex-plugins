# Chibi

Also called: super deformed, sd character, chibi style.

Family: Drawn and painted. Cadence: steps 12 times a second. Usual tool: HyperFrames (canvas or SVG).

A character two or three heads tall: a huge head, a tiny body, big shiny eyes, rosy cheeks and a bounce with a real squash and stretch.

Chibi, also known as super deformation (SD), is an art style originating in Japan and common in anime and manga, where characters are drawn small and chubby with stubby limbs, oversized eyes and heads, tiny noses and bodies, and minimal detail. The word comes from chibi kyara, "tiny character".

## What makes it read as this

- The head is as wide as the body is tall: two to three heads high
- Big eyes with a gradient iris and two highlights; tiny nose and mouth
- Stubby limbs and minimal detail on the body
- Soft rounded outlines in a darker shade of the fill, not black
- Bounce with squash on landing and stretch in the air

## Timing

A bounce about once a second on twos (12 changes a second), with a blink every 2 to 3 seconds.

## How to build it

- Pose the whole character in local coordinates and apply `ctx.scale(1 + s, 1 - s)` about the feet, where `s` follows the landing and the air time
- Eyes: a white ellipse, a radial-gradient iris, a dark pupil, two white highlight discs and a heavy upper lash arc
- Twin tails swing by an angle that follows the bounce
- Floating star sparkles drift by stepped time

## Assets

All in code. Original characters only: do not trace an existing one. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A bright, bouncy pop track, a spring boing on each landing. Practice note.

## What makes it look wrong

- A body longer than the head
- Squash with no matching stretch
- Copying a recognisable character

## Tested demo

This is the look from `art-forms/looks-toon.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=chibi` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  chibi: { kind: '2d', fps: 12, draw(g, t, W, H) {
    // two heads tall: a huge head, a tiny body, big shiny eyes, and a bouncing squash and stretch with a soft landing
    const ts = held(t, 12), u = (ts * 1.1) % 1, air = 4 * u * (1 - u), land = u < 0.14 ? (0.14 - u) / 0.14 : u > 0.86 ? (u - 0.86) / 0.14 : 0, sq = land * 0.28 - air * 0.07, blink = (ts % 2.4) < 0.12;
    const sky = g.createLinearGradient(0, 0, 0, H); sky.addColorStop(0, '#ffe3f1'); sky.addColorStop(1, '#e4ecff'); g.fillStyle = sky; g.fillRect(0, 0, W, H);
    for (let i = 0; i < 16; i++) { const x = hash(i, 1) * W, y = (hash(i, 2) * H + ts * 14 * (1 + hash(i, 3))) % H, r = 6 + hash(i, 4) * 9; polyFill(g, star(x, y, r, r * 0.45, 4, 0.78), i % 2 ? '#fff6b0' : '#ffffff'); }
    g.fillStyle = '#f2d4ea'; g.fillRect(0, 470, W, 70); ell(g, 480, 472, 120 - air * 40, 16 - air * 5, 'rgba(120,70,110,.3)');
    g.save(); g.translate(480, 470 - air * 90); g.scale(1 + sq, 1 - sq); g.lineJoin = 'round'; g.lineCap = 'round';
    const tail = Math.sin(ts * 7) * 0.22 * (0.3 + air); for (const d of [-1, 1]) { g.save(); g.translate(d * 120, -250); g.rotate(d * (0.35 + tail)); ell(g, 0, 70, 36, 92, '#ff8fb8', '#a8446f', 5); g.restore(); }
    for (const d of [-1, 1]) { ell(g, d * 18, -16, 20, 14 + air * 4, '#f6f0ff', '#6b4b8a', 5); ell(g, d * 24 + d * 24 * (air), -30, 11, 26, '#b69cff', '#6b4b8a', 5, d * (0.2 + air * 0.3)); }
    polyFill(g, [[-34, -58], [34, -58], [44, -112], [-44, -112]], '#b69cff', '#6b4b8a', 5); polyFill(g, [[-14, -112], [14, -112], [0, -92]], '#ff4f6d', '#6b4b8a', 3);
    for (const d of [-1, 1]) { g.lineWidth = 14; g.strokeStyle = '#6b4b8a'; path(g, [[d * 40, -100], [d * (66 + air * 20), -78 - air * 40]], false); g.stroke(); g.lineWidth = 8; g.strokeStyle = '#ffe3d0'; g.stroke(); }
    ell(g, 0, -214, 112, 104, '#ffe3d0', '#6b4b8a', 5);   // the huge head
    path(g, [[-114, -214], [-96, -300], [0, -330], [96, -300], [114, -214], [86, -262], [66, -226], [40, -270], [14, -224], [-12, -272], [-38, -228], [-62, -268], [-86, -222]]); g.fillStyle = '#ff8fb8'; g.fill(); g.strokeStyle = '#a8446f'; g.lineWidth = 5; g.stroke();
    for (const d of [-1, 1]) {
      const ex = d * 44, ey = -200;
      if (blink) { g.lineWidth = 6; g.strokeStyle = '#4b2f6b'; g.beginPath(); g.arc(ex, ey, 22, 0.15 * Math.PI, 0.85 * Math.PI); g.stroke(); continue; }
      ell(g, ex, ey, 28, 36, '#fff', '#4b2f6b', 5); const iris = g.createRadialGradient(ex, ey + 8, 4, ex, ey + 4, 28); iris.addColorStop(0, '#9fd4ff'); iris.addColorStop(1, '#2a56c8'); g.fillStyle = iris; g.beginPath(); g.ellipse(ex + 2, ey + 4, 21, 28, 0, 0, TAU); g.fill(); ell(g, ex + 2, ey + 6, 10, 14, '#1b1b44'); disc(g, ex - 7, ey - 10, 8, WHITE); disc(g, ex + 9, ey + 14, 4, WHITE);
      g.lineWidth = 7; g.strokeStyle = '#4b2f6b'; g.beginPath(); g.arc(ex, ey + 4, 31, Math.PI * 1.08, Math.PI * 1.92); g.stroke();
    }
    ell(g, -66, -162, 20, 11, 'rgba(255,110,150,.55)'); ell(g, 66, -162, 20, 11, 'rgba(255,110,150,.55)');
    if (air > 0.35) ell(g, 0, -150, 9, 12 + air * 6, '#c2415a', '#6b4b8a', 3); else { g.lineWidth = 4; g.strokeStyle = '#6b4b8a'; g.beginPath(); g.arc(-6, -156, 6, 0.1, Math.PI - 0.1); g.arc(6, -156, 6, 0.1, Math.PI - 0.1); g.stroke(); }
    polyFill(g, star(-70, -284, 20, 9, 5, -1.57), '#fff6b0', '#d9a21f', 3);
    g.restore();
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Chibi_(slang)>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
