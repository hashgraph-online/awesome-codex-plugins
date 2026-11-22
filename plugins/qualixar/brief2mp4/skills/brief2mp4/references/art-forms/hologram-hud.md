# Hologram HUD

Also called: hologram, holographic interface, hud.

Family: Screens and cinema. Cadence: steps 24 times a second. Usual tool: HyperFrames (canvas or Three.js).

A cyan and blue wireframe turning in the dark, with readouts, bars, a dial, corner brackets, a scan band and a flicker with an occasional slipped strip.

A head-up display (HUD) is any transparent display that presents data without requiring users to look away from their usual viewpoints; HUDs were first developed for military aviation and are now used in commercial aircraft, cars and other applications.

Sourcing note: The source describes the real head-up display. The holographic wireframe look is a science-fiction convention, described here as practice.

## What makes it read as this

- A wireframe: latitude and longitude lines, a ring and a satellite
- Cyan and blue light on a near-black navy ground, with glow
- HUD furniture: corner brackets, bars with numbers, a dial with ticks
- A scan band sweeping down the frame and fine scanlines
- Flicker, and now and then a strip that slips sideways

## Timing

The wireframe turns slowly; the numbers change about every quarter of a second; the band sweeps in about 4 seconds. Drawn at 24 changes a second.

## How to build it

- Project points on a sphere with a turn and a tilt, and draw only the visible half
- Draw each wireframe twice: a blue copy shifted 3 px, then a cyan copy, each with a glow
- Bars and numbers from a hash of `Math.floor(frame / 6)` so that they tick
- Slip: copy a thin strip of the canvas back onto itself offset by 8 px on random frames

## Assets

All in code. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A soft electronic hum, data chirps and a low pulse. Practice note.

## What makes it look wrong

- Green or mint instead of cyan and blue
- A solid, shaded model: it should be lines only
- A steady, clean picture with no flicker

## Tested demo

This is the look from `art-forms/looks-screen.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=hologram-hud` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'hologram-hud': { kind: '2d', fps: 24, draw(g, t, W, H) {
    // a cyan and blue wireframe globe turning in the dark, with a ring and a satellite, HUD readouts, corner brackets, a scan band, and a flicker with an occasional slipped strip
    const f = frameOf(t, 24), CY = '#58e6ff', BL = '#2a7bff', a = t * 0.6, tilt = 0.4, flick = hash(f, 1) > 0.92 ? 0.45 : 0.9 + 0.1 * hash(f, 2); g.fillStyle = '#030a18'; g.fillRect(0, 0, W, H); const bgl = g.createRadialGradient(480, 280, 20, 480, 280, 400); bgl.addColorStop(0, 'rgba(40,120,255,.28)'); bgl.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = bgl; g.fillRect(0, 0, W, H);
    g.save(); g.globalAlpha = flick; const proj = (la, lo, R) => { const X = Math.cos(la) * Math.sin(lo + a), Y = Math.sin(la), Z = Math.cos(la) * Math.cos(lo + a), Yp = Y * Math.cos(tilt) - Z * Math.sin(tilt), Zp = Y * Math.sin(tilt) + Z * Math.cos(tilt); return [480 + R * X, 280 - R * Yp, Zp]; };
    const wire = (col, lw, shift) => neon(g, col, lw, () => { g.beginPath(); for (let i = -4; i <= 4; i++) { let pen = false; for (let k = 0; k <= 48; k++) { const p = proj((i / 5) * 1.35, (k / 48) * TAU, 150); if (p[2] > -0.1) { pen ? g.lineTo(p[0] + shift, p[1]) : g.moveTo(p[0] + shift, p[1]); pen = true; } else pen = false; } } for (let j = 0; j < 12; j++) { let pen = false; for (let k = 0; k <= 36; k++) { const p = proj(-1.5 + (k / 36) * 3, (j / 12) * TAU, 150); if (p[2] > -0.05) { pen ? g.lineTo(p[0] + shift, p[1]) : g.moveTo(p[0] + shift, p[1]); pen = true; } else pen = false; } } });
    wire(BL, 1.6, 3); wire(CY, 1.8, 0);
    neon(g, CY, 1.6, () => { g.beginPath(); for (let k = 0; k <= 80; k++) { const th = (k / 80) * TAU, x = Math.cos(th) * 230, y = Math.sin(th) * 52; k ? g.lineTo(480 + x, 280 + y * 1 - x * 0.2) : g.moveTo(480 + x, 280 + y - x * 0.2); } }); const sat = a * 1.7; disc2(g, 480 + Math.cos(sat) * 230, 280 + Math.sin(sat) * 52 - Math.cos(sat) * 46, 6, CY);
    g.restore();
    g.strokeStyle = CY; g.fillStyle = CY; g.font = '700 13px "Courier New", monospace'; g.lineWidth = 1.6;
    for (const [x, y, sx, sy] of [[28, 28, 1, 1], [W - 28, 28, -1, 1], [28, H - 28, 1, -1], [W - 28, H - 28, -1, -1]]) { g.beginPath(); g.moveTo(x, y + sy * 36); g.lineTo(x, y); g.lineTo(x + sx * 36, y); g.stroke(); }
    ['PWR', 'SYNC', 'LINK'].forEach((l, i) => { const v = 0.35 + 0.6 * hash(Math.floor(f / 6), i, 4); g.fillText(l, 50, 120 + i * 34); g.strokeRect(100, 109 + i * 34, 120, 12); g.fillRect(100, 109 + i * 34, 120 * v, 12); g.fillText(String(Math.round(v * 100)).padStart(3, '0'), 232, 120 + i * 34); });
    for (let i = 0; i < 9; i++) { const v = 0.2 + 0.8 * hash(Math.floor(f / 5), i, 6); g.fillRect(730 + i * 17, 230 - 90 * v, 10, 90 * v); }
    g.beginPath(); g.arc(800, 360, 54, 0, TAU); g.stroke(); for (let i = 0; i < 24; i++) { const an = (i / 24) * TAU + t * 0.8; g.beginPath(); g.moveTo(800 + Math.cos(an) * 54, 360 + Math.sin(an) * 54); g.lineTo(800 + Math.cos(an) * (i % 3 ? 62 : 70), 360 + Math.sin(an) * (i % 3 ? 62 : 70)); g.stroke(); }
    g.fillText('SCAN ' + String(Math.floor((t * 22) % 100)).padStart(3, '0') + '%', 50, 470); g.fillText('ALT 4' + String(120 + Math.floor(hash(Math.floor(f / 8), 9) * 80)), 50, 490);
    const bandY = (t * 150) % (H + 80) - 40, band = g.createLinearGradient(0, bandY - 40, 0, bandY + 40); band.addColorStop(0, 'rgba(88,230,255,0)'); band.addColorStop(0.5, 'rgba(88,230,255,.22)'); band.addColorStop(1, 'rgba(88,230,255,0)'); g.fillStyle = band; g.fillRect(0, bandY - 40, W, 80);
    scanlines(g, W, H, 0.18, 3); if (hash(f, 11) > 0.9) { const y = hash(f, 12) * H; g.drawImage(g.canvas, 0, y, W, 24, 8, y, W, 24); }
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Head-up_display>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
