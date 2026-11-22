# Thermal camera

Also called: thermal imaging, infrared camera, heat camera.

Family: Screens and cinema. Cadence: steps 12 times a second. Usual tool: HyperFrames (canvas).

A false-colour heat map through black, purple, red, orange, yellow and white: a hot head and hands, a warm mug, a cold window, a crosshair, a temperature readout and a colour scale.

Infrared thermography, also called thermal imaging, is a technique in which a thermal camera detects infrared radiation from the surface of objects. Warm objects stand out against cooler backgrounds, so that variations in temperature can be seen with or without visible light.

Sourcing note: The source describes the technique; the specific palette is the common black-purple-red-yellow-white ramp, described here as practice.

## What makes it read as this

- One heat value per pixel, shown through a fixed palette: black, purple, red, orange, yellow, white
- Warm objects are bright and soft-edged; cold ones are dark
- A hot head and hands, a warm torso, cooler limbs
- A crosshair with a temperature readout and a colour scale bar
- Sensor noise and fine scanlines

## Timing

The figure sways slightly and pulses; the readout changes a few times a second. Drawn at 12 changes a second.

## How to build it

- Draw a heat field in greys on a small canvas (240 by 135) with `blur(2px)`; hot shapes have bright greys
- Read it back with `getImageData` and map each grey through a 256-colour palette table
- Scale the result up with smoothing, then draw the HUD in white
- Add a little seeded noise to each pixel

## Assets

All in code. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A soft beep on each reading and a fan hum. Practice note.

## What makes it look wrong

- Natural colours: the picture is false colour
- Hard-edged shapes: heat is blurred
- A palette that is not monotonic in brightness

## Tested demo

This is the look from `art-forms/looks-screen.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=thermal` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  thermal: { kind: '2d', fps: 12, draw(g, t, W, H) {
    // a thermal-camera view: a heat field mapped through black, purple, red, orange, yellow and white, with a hot head and hands, a warm mug, a cold window, and a crosshair and a colour scale
    const ts = held(t, 12), w = 240, h = 135, c = new OffscreenCanvas(w, h).getContext('2d'), sway = Math.sin(ts * 1.2) * 2, pulse = 0.95 + 0.05 * Math.sin(ts * 3);
    c.fillStyle = gray(34); c.fillRect(0, 0, w, h); c.fillStyle = gray(58); c.fillRect(0, 100, w, 35); c.filter = 'blur(2px)'; c.fillStyle = gray(18); c.fillRect(186, 28, 44, 56);
    const blob = (x, y, rx, ry, v) => { c.fillStyle = gray(v * pulse); c.beginPath(); c.ellipse(x, y, rx, ry, 0, 0, TAU); c.fill(); }, limb = (x0, y0, x1, y1, lw, v) => { c.strokeStyle = gray(v * pulse); c.lineWidth = lw; c.lineCap = 'round'; c.beginPath(); c.moveTo(x0, y0); c.lineTo(x1, y1); c.stroke(); };
    blob(118, 128, 34, 5, 80); limb(108 + sway, 88, 106, 124, 12, 140); limb(130 + sway, 88, 132, 124, 12, 140); blob(120 + sway, 64, 21, 28, 190); limb(102 + sway, 48, 88, 78, 9, 165); limb(138 + sway, 48, 156, 82, 9, 165); blob(120 + sway, 46, 5, 8, 205);
    blob(120 + sway, 33, 11, 13, 238); blob(88, 80, 6, 6, 225); blob(157, 85, 6, 6, 225); blob(160, 82, 5, 5, 255); blob(30, 26, 9, 9, 255); blob(30, 26, 20, 20, 120);
    const d = c.getImageData(0, 0, w, h), out = new ImageData(w, h), STOPS = [[0, [0, 0, 8]], [0.18, [40, 0, 90]], [0.4, [170, 20, 60]], [0.62, [240, 90, 20]], [0.82, [255, 200, 40]], [1, [255, 255, 230]]];
    const ramp = (v) => { for (let i = 1; i < STOPS.length; i++) if (v <= STOPS[i][0]) { const a = STOPS[i - 1], b = STOPS[i], k = (v - a[0]) / (b[0] - a[0]); return mix(a[1], b[1], k); } return STOPS[STOPS.length - 1][1]; };
    const lut = Array.from({ length: 256 }, (_, i) => ramp(i / 255)); for (let i = 0; i < w * h; i++) { const col = lut[d.data[i * 4] | 0], n = (hash(i, ts * 12 | 0) - 0.5) * 8; out.data[i * 4] = col[0] + n; out.data[i * 4 + 1] = col[1] + n; out.data[i * 4 + 2] = col[2] + n; out.data[i * 4 + 3] = 255; }
    const fc = new OffscreenCanvas(w, h); fc.getContext('2d').putImageData(out, 0, 0); g.imageSmoothingEnabled = true; g.drawImage(fc, 0, 0, W, H);
    g.strokeStyle = '#fff'; g.fillStyle = '#fff'; g.lineWidth = 2; g.font = '700 16px "Courier New", monospace'; const hx = (120 + sway) * 4, hy = 33 * 4; g.beginPath(); g.arc(hx, hy, 34, 0, TAU); g.moveTo(hx - 50, hy); g.lineTo(hx - 20, hy); g.moveTo(hx + 20, hy); g.lineTo(hx + 50, hy); g.moveTo(hx, hy - 50); g.lineTo(hx, hy - 20); g.moveTo(hx, hy + 20); g.lineTo(hx, hy + 50); g.stroke(); g.fillText('36.' + (4 + Math.floor((Math.sin(ts * 2) + 1) * 2)) + ' C', hx + 40, hy - 36);
    const sc = g.createLinearGradient(0, 100, 0, 440); STOPS.slice().reverse().forEach(([k, col]) => sc.addColorStop(1 - k, rgba(col))); g.fillStyle = sc; g.fillRect(900, 100, 22, 340); g.strokeRect(900, 100, 22, 340); g.fillStyle = '#fff'; g.fillText('40', 928, 112); g.fillText('20', 928, 276); g.fillText('0', 928, 440);
    for (const [x, y, sx, sy] of [[28, 28, 1, 1], [W - 28, 28, -1, 1], [28, H - 28, 1, -1], [W - 28, H - 28, -1, -1]]) { g.beginPath(); g.moveTo(x, y + sy * 30); g.lineTo(x, y); g.lineTo(x + sx * 30, y); g.stroke(); }
    g.fillText('THERMAL  ' + String(Math.floor(t * 10) % 1000).padStart(3, '0'), 44, 60); scanlines(g, W, H, 0.1, 4);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Thermography>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
