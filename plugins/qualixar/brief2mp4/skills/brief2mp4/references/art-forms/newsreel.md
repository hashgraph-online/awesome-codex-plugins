# Newsreel

Also called: news reel, 1940s newsreel, vintage newsreel.

Family: Screens and cinema. Cadence: steps 18 times a second. Usual tool: HyperFrames (canvas), or ffmpeg filters on real footage.

Sepia footage of the 1940s: a train racing past telegraph poles, a slanted headline banner, and a damaged print with scratches, hairs, dust, a burn flash and a jolt of the frame.

A newsreel is a short documentary film of news stories and items of topical interest, prevalent from the 1910s to the late 1960s and typically shown in cinemas before a feature; by the end of the 1960s television news had supplanted the format.

## What makes it read as this

- Sepia: a warm brown to cream palette, with no true black or white
- A slanted, bold headline banner in a heavy condensed face
- A moving subject with strong motion: a train, a parade, a ship
- Film damage: scratches, hairs, dust, burns and frame jumps
- A vignette and heavy grain

## Timing

Drawn at 18 changes a second; the train, poles and smoke move at constant speeds, and the damage re-rolls every frame.

## How to build it

- Build the palette with one function that maps 0..1 to a mix of dark brown and cream (`sepia()` in `looks-screen.js`)
- Parallax: poles and ties move at different speeds
- Banner: rotate the context by about -0.07 radians and draw a dark bar with cream text
- Burn flash: a radial gradient on a random frame; jolt: a few pixels of vertical shift on a few frames

## Assets

All in code. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A brass fanfare, a narrator's urgent cadence and a projector clatter. Practice note.

## What makes it look wrong

- Grey instead of sepia
- A steady, clean picture
- Presenting invented footage as a real archive: this is a style, not a document

## Tested demo

This is the look from `art-forms/looks-screen.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=newsreel` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  newsreel: { kind: '2d', fps: 18, draw(g, t, W, H) {
    // sepia 1940s newsreel footage: a steam train racing across the frame past telegraph poles, a slanted headline banner, and a damaged print: scratches, hairs, dust, a burn flash and a jolt of the frame
    const f = frameOf(t, 18), ts = f / 18; g.save(); g.translate(jit(f, 1, 2), jit(f, 2, 1.5) + (hash(f >> 1, 3) > 0.94 ? 9 : 0));
    const sky = g.createLinearGradient(0, 0, 0, 380); sky.addColorStop(0, sepia(0.86)); sky.addColorStop(1, sepia(0.6)); g.fillStyle = sky; g.fillRect(-20, -20, W + 40, 420);
    g.fillStyle = sepia(0.4); g.beginPath(); g.moveTo(-20, 360); for (let x = 0; x <= W + 20; x += 20) g.lineTo(x, 330 - 40 * vnoise((x + ts * 40) / 120, 0, 4)); g.lineTo(W + 20, 400); g.lineTo(-20, 400); g.fill();
    g.fillStyle = sepia(0.2); g.fillRect(-20, 392, W + 40, 160); g.fillStyle = sepia(0.12); for (let i = 0; i < 14; i++) g.fillRect(((i * 90 - ts * 420) % (W + 90) + W + 90) % (W + 90) - 40, 478, 44, 8);
    g.strokeStyle = sepia(0.08); g.lineWidth = 6; for (let i = 0; i < 5; i++) { const x = ((i * 230 - ts * 640) % (W + 230) + W + 230) % (W + 230) - 60; g.beginPath(); g.moveTo(x, 190); g.lineTo(x, 400); g.moveTo(x - 36, 214); g.lineTo(x + 36, 214); g.stroke(); }
    const ex = 380, ey = 360; g.fillStyle = sepia(0.07); g.fillRect(ex - 160, ey - 76, 250, 76); g.beginPath(); g.arc(ex - 160, ey - 38, 38, Math.PI / 2, Math.PI * 1.5); g.fill(); g.fillRect(ex - 170, ey - 120, 34, 52); g.fillRect(ex + 24, ey - 140, 104, 140); g.fillRect(ex + 10, ey - 150, 132, 14); g.fillStyle = sepia(0.5); g.fillRect(ex + 46, ey - 112, 56, 40);
    for (const wxp of [-120, -50, 20, 90]) { g.fillStyle = sepia(0.05); g.beginPath(); g.arc(ex + wxp, ey + 6, 30, 0, TAU); g.fill(); g.strokeStyle = sepia(0.6); g.lineWidth = 3; for (let sp = 0; sp < 4; sp++) { const a = f * 0.5 + (sp * Math.PI) / 4; g.beginPath(); g.moveTo(ex + wxp + Math.cos(a) * 26, ey + 6 + Math.sin(a) * 26); g.lineTo(ex + wxp - Math.cos(a) * 26, ey + 6 - Math.sin(a) * 26); g.stroke(); } }
    for (let i = 0; i < 7; i++) { const k = (ts * 1.2 + i / 7) % 1, x = ex - 150 - k * 320, y = ey - 150 - k * 150; g.fillStyle = `rgba(${240 - k * 40},${230 - k * 40},${210 - k * 40},${0.7 * (1 - k)})`; g.beginPath(); g.arc(x, y, 18 + k * 44, 0, TAU); g.fill(); }
    g.restore(); g.save(); g.translate(W / 2, 450); g.rotate(-0.07); g.fillStyle = sepia(0.06); g.fillRect(-380, -34, 760, 70); g.fillStyle = sepia(0.92); g.fillRect(-380, 36, 540, 26); g.fillStyle = sepia(0.95); g.font = '400 50px Impact, "Arial Black", sans-serif'; g.textAlign = 'center'; g.fillText('THE WORLD IN MOTION', 0, 18); g.fillStyle = sepia(0.08); g.font = '700 17px "Arial Narrow", Arial, sans-serif'; g.fillText('NEWS OF THE WEEK', -110, 56); g.restore();
    if (hash(f >> 1, 9) > 0.9) { const bx = hash(f, 10) * W, bg2 = g.createRadialGradient(bx, 200, 10, bx, 200, 300); bg2.addColorStop(0, 'rgba(255,240,200,.45)'); bg2.addColorStop(1, 'rgba(255,240,200,0)'); g.fillStyle = bg2; g.fillRect(0, 0, W, H); }
    vignette(g, W, H, 0.65, 0.35); filmDamage(g, W, H, f, { warm: true, grain: 56 });
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Newsreel>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
