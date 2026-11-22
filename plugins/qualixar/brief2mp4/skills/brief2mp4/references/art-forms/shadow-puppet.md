# Shadow puppetry

Also called: shadow play, Ravana Chhaya, wayang kulit, silhouette animation.

Family: Craft and handmade. Cadence: steps 12 times a second. Usual tool: HyperFrames (canvas or SVG).

Flat figures held between a lamp and a cloth screen: dark silhouettes with punched patterns on a warm, glowing field.

An old tradition across Asia. Ravana Chhaya of Odisha uses uncoloured deerskin puppets with no joints; wayang kulit of Java and Bali was recognised by UNESCO in 2003. Lotte Reiniger brought silhouettes to film.

## What makes it read as this

- Black silhouettes on a warm lit screen, never on white
- Interior detail made of perforations: rows of holes and cut patterns
- A lamp that flickers
- The shadow softens and grows as the puppet moves away from the screen
- Rods visible below the figures

## Timing

Live puppets move continuously on rods; film versions are stop-motion, so use twos. Stiff, deliberate moves; no squash and stretch.

## How to build it

- One path per puppet filled with the even-odd rule, so holes are part of the figure
- Screen: a radial gradient from warm yellow to deep brown
- Flicker: scale the lamp brightness by a seeded value per drawing
- Distance from the screen: `filter: blur()` growing with distance, and lower opacity
- Ravana Chhaya style: no joints, move and tilt the whole puppet. Wayang style: hinge the arms

Use Blender for real light through translucent coloured leather.

## Assets

Simple figures in code. Ornate traditional figures need drawing or tracing with care. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Narrator, singers and percussion in the tradition: cymbals and drums for Ravana Chhaya, gamelan for wayang.

## What makes it look wrong

- Black on white, which loses the lamp
- Smooth modern vector motion
- Careless drawings of sacred figures: check the iconography with a source

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=shadow-puppet` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'shadow-puppet': { kind: '2d', fps: 12, draw(g, t, W, H) {
    // a lamp-lit screen and jointless leather figures with punched patterns, moved whole on their rods (the Ravana Chhaya way)
    const f = frameOf(t, 12), ts = onTwos(t), flick = 1 + jit(f, 0, 0.05);
    bg(g, W, H, '#1a0d05');
    const lamp = g.createRadialGradient(W / 2, H * 0.55, 30, W / 2, H * 0.55, W * 0.62);
    lamp.addColorStop(0, `rgba(255,${196 * flick},110,1)`); lamp.addColorStop(0.55, `rgba(214,${120 * flick},48,1)`); lamp.addColorStop(1, 'rgba(60,24,8,1)');
    g.fillStyle = lamp; g.fillRect(24, 24, W - 48, H - 48);
    const puppet = (x, y, s, lean, far) => {
      g.save(); g.translate(x, y); g.rotate(lean); g.scale(s, s); g.filter = `blur(${far * 5}px)`; g.fillStyle = `rgba(18,8,2,${1 - far * 0.35})`;
      g.beginPath();   // one path, even-odd: the holes are part of the figure
      g.moveTo(-34, 150); g.lineTo(-44, 20); g.lineTo(-70, -30); g.lineTo(-40, -44); g.lineTo(-26, -96); g.lineTo(-44, -150); g.lineTo(0, -196); g.lineTo(44, -150); g.lineTo(26, -96); g.lineTo(40, -44); g.lineTo(84, -70); g.lineTo(92, -44); g.lineTo(44, 20); g.lineTo(34, 150); g.closePath();
      for (let i = 0; i < 5; i++) { g.moveTo(8, -20 + i * 30); g.arc(0, -20 + i * 30, 8, 0, TAU); }
      for (let i = 0; i < 7; i++) { const a = (i / 7) * TAU; g.moveTo(Math.cos(a) * 22 + 4, -140 + Math.sin(a) * 22); g.arc(Math.cos(a) * 22, -140 + Math.sin(a) * 22, 4, 0, TAU); }
      g.fill('evenodd'); g.filter = 'none'; g.fillRect(-3, 150, 6, 260); g.restore();
    };
    puppet(W * 0.34 + Math.sin(ts * 1.6) * 26, H * 0.62, 0.95, Math.sin(ts * 1.6) * 0.06, 0);
    puppet(W * 0.68 - Math.sin(ts * 1.3) * 34, H * 0.66, 0.8, -Math.sin(ts * 1.3) * 0.08, (Math.sin(ts * 0.9) + 1) / 2);
    g.globalCompositeOperation = 'multiply'; g.drawImage(grain(W, H, 6, 40, [80, 40, 10]), 0, 0); g.globalCompositeOperation = 'source-over';
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Shadow_play>
- <https://en.wikipedia.org/wiki/Ravana_Chhaya>
- <https://en.wikipedia.org/wiki/Lotte_Reiniger>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
