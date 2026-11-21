# Motion comic

Family: Drawn and painted. Cadence: smooth, full frame rate. Usual tool: HyperFrames (DOM or canvas).

Comic panels brought to life: layers inside a panel slide at different speeds under a slow camera move, then a hard cut to the next panel.

Watchmen: Motion Comic (2008) is the usual first example.

Sourcing note: Pan-and-zoom staging is a practice note; the source describes the format, not the technique.

## What makes it read as this

- Ink outlines, flat colour, halftone shading
- A panel border
- Foreground, figure and background on separate layers
- Bursts and lettering as graphic elements

## Timing

Slow pushes and pans of 2 to 4 seconds, hard cuts between panels, a pop for a burst.

## How to build it

- Layers in a clipped panel; move far layers less than near ones
- A slow scale from 1 to about 1.07 on the whole panel
- Halftone shading: dots that shrink across the tone
- Cut to the next panel by switching the scene at a time, not by cross-fading

## Assets

Drawn panels in layers. Artwork needs an illustrator or generated images cut into layers. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Voice, music and effects carry it. Practice note.

## What makes it look wrong

- A slow zoom on one flat image, which reads as a slideshow
- No separation between figure and background

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=motion-comic` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of that file. Take the technique, not the picture.

```js
  'motion-comic': { kind: '2d', fps: null, draw(g, t, W, H) {
    // two panels and a hard cut. Inside each: layers that move at different speeds under a slow push-in, with halftone shading.
    bg(g, W, H, '#f0ead8');
    const second = t >= 1.6, k = second ? prog(t, 1.6, 1.4) : prog(t, 0, 1.6), z = 1 + 0.07 * k;
    g.save(); g.beginPath(); g.rect(40, 40, W - 80, H - 80); g.clip();
    g.translate(W / 2, H / 2); g.scale(z, z); g.translate(-W / 2, -H / 2);
    g.fillStyle = second ? '#ffcf4a' : '#27335c'; g.fillRect(0, 0, W, H);
    g.fillStyle = second ? '#e9772b' : '#141b36';                           // far layer: slow
    for (let i = 0; i < 9; i++) { const h = 120 + hash(i, second ? 5 : 3) * 190; g.fillRect(i * 120 - 40 - k * 18, H - 120 - h, 96, h + 200); }
    g.fillStyle = 'rgba(0,0,0,.28)';                                        // halftone shade, dots shrink to the right
    for (let y = 60; y < H; y += 14) for (let x = 60; x < W * 0.5; x += 14) { g.beginPath(); g.arc(x + ((y / 14) % 2 | 0) * 7, y, 4.5 * (1 - x / (W * 0.5)), 0, TAU); g.fill(); }
    g.save(); g.translate(W * (second ? 0.62 : 0.4) + k * 46, H * 0.66);   // near layer: fast
    g.fillStyle = '#101010'; g.beginPath(); g.moveTo(-70, 220); g.lineTo(-52, -40); g.lineTo(-20, -70); g.arc(0, -108, 44, Math.PI * 0.7, Math.PI * 2.3); g.lineTo(52, -40); g.lineTo(70, 220); g.closePath(); g.fill(); g.restore();
    if (second) { const b = overshoot(prog(t, 1.75, 0.35)); g.save(); g.translate(W * 0.3, H * 0.34); g.scale(b, b); g.fillStyle = '#fff'; g.strokeStyle = '#101010'; g.lineWidth = 5; g.beginPath(); for (let i = 0; i < 20; i++) { const a = (i / 20) * TAU, r = i % 2 ? 62 : 104; i ? g.lineTo(Math.cos(a) * r, Math.sin(a) * r) : g.moveTo(Math.cos(a) * r, Math.sin(a) * r); } g.closePath(); g.fill(); g.stroke(); g.fillStyle = '#101010'; g.font = `900 46px ${FONT}`; g.textAlign = 'center'; g.fillText('NOW!', 0, 16); g.textAlign = 'left'; g.restore(); }
    g.restore(); g.strokeStyle = '#101010'; g.lineWidth = 8; g.strokeRect(40, 40, W - 80, H - 80);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Motion_comic>
- <https://en.wikipedia.org/wiki/Limited_animation>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
