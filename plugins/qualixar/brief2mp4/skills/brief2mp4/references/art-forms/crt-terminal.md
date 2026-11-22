# CRT terminal

Also called: amber terminal, phosphor terminal, retro terminal.

Family: Screens and cinema. Cadence: steps 24 times a second. Usual tool: HyperFrames (canvas).

An amber phosphor terminal: text typed one character at a time, a block cursor, scanlines, glow, a slow rolling bar, and a screen that bulges at the middle.

A computer terminal is a device for entering data into, and displaying data from, a computer. Teleprinters were used as early hard-copy terminals and predated computer screens by decades; with inexpensive video displays terminals improved. A cathode-ray tube is the vacuum tube with a fluorescent screen that such displays used.

Sourcing note: The sources describe terminals and cathode-ray tubes; scanlines, glow and curvature are practice rules for the look.

## What makes it read as this

- One phosphor colour on near-black: amber or green
- Text in a monospaced face with a soft glow
- Scanlines: dark lines every few pixels
- A screen that bulges, with darker corners and a reflection
- A blinking block cursor and typed text; a faint flicker and a rolling bar

## Timing

Characters type at about 36 a second; the cursor blinks twice a second; the picture flickers each frame at 24 changes a second.

## How to build it

- Draw the screen to an off-screen canvas: black, glowing text with `shadowBlur`, scanlines, a rolling band
- Curvature: copy the canvas to the main canvas in 3 px slices, each slightly narrower toward the top and bottom
- Type text by slicing each line to the number of characters typed so far; place the cursor at the end of that slice
- Add a vignette, a faint highlight arc and a rounded bezel mask

## Assets

All in code. Use a monospaced font that the system has. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Key clicks and a low mains hum. Practice note.

## What makes it look wrong

- Straight, flat screen edges
- Clean text with no glow
- Colour: one phosphor only

## Tested demo

This is the look from `art-forms/looks-screen.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=crt-terminal` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'crt-terminal': { kind: '2d', fps: 24, draw(g, t, W, H) {
    // an amber phosphor terminal: text typed one character at a time, a block cursor, scanlines, glow, a slow rolling bar, and a screen that bulges at the middle
    const f = frameOf(t, 24), sc = new OffscreenCanvas(W, H), c = sc.getContext('2d'), AMB = '#ffb000', script = ['> route brief.md', 'art form: crt terminal', 'cadence: smooth, full frame rate', '', '> render --fps 24', 'frames 0001 .. 0096 ok', 'checking delivery ... pass', '', '> done'], typed = Math.floor(t < 0.25 ? t * 66 : 16 + (t - 0.25) * 36);   // the first prompt is typed by 0.25 s
    c.fillStyle = '#0a0600'; c.fillRect(0, 0, W, H); c.font = '700 26px "Courier New", Courier, monospace'; c.textBaseline = 'top'; c.shadowColor = AMB; c.shadowBlur = 14; c.fillStyle = AMB;
    c.fillText('BRIEF2MP4 TERMINAL', 70, 56); let left = typed, cur = null; for (let i = 0; i < script.length && !cur; i++) { const line = script[i], n = clamp(left, 0, line.length); c.fillText(line.slice(0, n), 70, 56 + (i + 2) * 38); if (left <= line.length) cur = [i, n]; left -= line.length + 2; }
    if (cur && Math.floor(t * 2) % 2 === 0) c.fillRect(70 + cur[1] * 15.6, 56 + (cur[0] + 2) * 38, 14, 26);   // a blinking block cursor at the end of what has been typed
    c.shadowBlur = 0; scanlines(c, W, H, 0.22, 3); const bar = ((t * 0.18) % 1.3) * (H + 120) - 120; const bg2 = c.createLinearGradient(0, bar, 0, bar + 120); bg2.addColorStop(0, 'rgba(255,176,0,0)'); bg2.addColorStop(0.5, 'rgba(255,176,0,.1)'); bg2.addColorStop(1, 'rgba(255,176,0,0)'); c.fillStyle = bg2; c.fillRect(0, bar, W, 120);
    g.fillStyle = '#050403'; g.fillRect(0, 0, W, H); const flick = 0.94 + 0.06 * hash(f, 3); g.globalAlpha = flick;
    for (let y = 0; y < H; y += 3) { const k = ((y - H / 2) / (H / 2)) ** 2, sw = W * (1 - 0.07 * k), dh = 3; g.drawImage(sc, 0, y, W, dh, (W - sw) / 2, y, sw, dh); }
    g.globalAlpha = 1; vignette(g, W, H, 0.7, 0.35); g.strokeStyle = 'rgba(255,255,255,.07)'; g.lineWidth = 4; g.beginPath(); g.ellipse(300, 90, 160, 28, -0.2, Math.PI * 1.1, Math.PI * 1.7); g.stroke();
    g.fillStyle = '#050403'; g.beginPath(); g.rect(0, 0, W, H); g.roundRect(14, 14, W - 28, H - 28, 46); g.fill('evenodd');
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Computer_terminal>
- <https://en.wikipedia.org/wiki/Cathode-ray_tube>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
