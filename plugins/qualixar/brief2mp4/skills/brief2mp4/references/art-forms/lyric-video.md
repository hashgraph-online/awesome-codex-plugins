# Lyric video

Family: Type, data and retro. Cadence: smooth, full frame rate. Usual tool: HyperFrames (DOM, canvas).

The words of a song as the main image, each line timed to the vocal and the active word lit.

Lyric text appears in music videos from the 1980s; the format took off on video sites in the 2010s.

## What makes it read as this

- Three to eight words on screen
- The word being sung is brighter or larger
- A background that never fights the text
- One typographic system for the whole song

## Timing

Locked to the music. A word changes exactly on its beat; a few frames late is visible.

## How to build it

- Word start times from forced alignment or a beat grid
- Compute the active line and word from `t`
- A pulse from the beat phase: `1 - (beat % 1)` drives scale and background
- Measure words first so the line is centred

## Assets

The audio, with the right to use it, and its word timings. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

The song.

## What makes it look wrong

- Timing that drifts
- Text over a busy background
- Music you have no licence for

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=lyric-video` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of that file. Take the technique, not the picture.

```js
  'lyric-video': { kind: '2d', fps: null, draw(g, t, W, H) {
    // one line at a time, and the word being sung is lit. Timing comes from a beat grid (here 120 beats a minute).
    const beat = t / 0.5, pulse = 1 - (beat % 1);
    const grad = g.createLinearGradient(0, 0, W, H); grad.addColorStop(0, `hsl(${258 + pulse * 8} 60% ${16 + pulse * 5}%)`); grad.addColorStop(1, 'hsl(320 60% 22%)');
    g.globalCompositeOperation = 'source-over'; g.fillStyle = grad; g.fillRect(0, 0, W, H);
    const lines = [['say', 'it', 'once'], ['and', 'let', 'it', 'move']], li = Math.min(1, Math.floor(beat / 3)), line = lines[li], wi = Math.min(line.length - 1, Math.floor(beat - li * 3));
    g.font = `800 84px ${FONT}`; g.textBaseline = 'middle';
    const widths = line.map((w) => g.measureText(w + ' ').width), total = widths.reduce((a, b) => a + b, 0); let x = (W - total) / 2;
    const enter = easeOut(prog(beat - li * 3, 0, 0.5));
    line.forEach((w, i) => {
      const active = i === wi, done = i < wi, s = active ? 1 + 0.08 * pulse : 1;
      g.save(); g.translate(x + widths[i] / 2, H / 2 + (1 - enter) * 30); g.scale(s, s); g.globalAlpha = enter * (active ? 1 : done ? 0.85 : 0.35);
      g.fillStyle = active ? '#ffd166' : '#ffffff'; g.textAlign = 'center'; g.fillText(w, 0, 0); g.restore(); x += widths[i];
    });
    g.textAlign = 'left'; g.textBaseline = 'alphabetic';
    for (let i = 0; i < 6; i++) { g.fillStyle = i <= beat % 6 ? '#ffd166' : 'rgba(255,255,255,.25)'; g.fillRect(W / 2 - 96 + i * 34, H - 70, 22, 6); }
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Lyric_video>
- <https://en.wikipedia.org/wiki/Kinetic_typography>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
