# Infographic and data animation

Also called: data-viz animation.

Family: Type, data and retro. Cadence: smooth, full frame rate. Usual tool: HyperFrames (SVG, canvas).

A chart that builds in a sensible order: axes, then the data from an honest baseline, then the exact values.

From Playfair's first charts in 1786 to animated infographics in music videos in 2002.

## What makes it read as this

- One chart type that fits the data
- Direct labels, not a legend
- An honest axis: bars start at zero
- One colour for the point being made

## Timing

Axes in about half a second, each series over 0.8 to 1.5 seconds with an ease-out, then a hold to read.

## How to build it

- Drive the chart from one time value; never use a chart library's own transitions
- Bars grow from the baseline; counters show the rounded value as it grows and end on the exact figure
- SVG or canvas with scale maths; D3 scales are enough
- Every number needs a source in the brief

## Assets

The data, with its source. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A tick or tone per value, a bed that stays out of the way. Practice note.

## What makes it look wrong

- Numbers that were not checked
- 3D bars
- An axis cut off to exaggerate a difference

## Tested demo

This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=infographic` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of that file. Take the technique, not the picture.

```js
  infographic: { kind: '2d', fps: null, draw(g, t, W, H) {
    // axes first, then the bars from a zero baseline, then the exact values. The numbers here are sample data.
    bg(g, W, H, '#fbfaf6');
    const data = [['2021', 12], ['2022', 19], ['2023', 31], ['2024', 44], ['2025', 62]], x0 = 130, y0 = H - 100, cw = (W - 220) / data.length, max = 70;
    g.strokeStyle = '#1b1e22'; g.lineWidth = 3; g.lineCap = 'round'; strokePart(g, [[x0, 70], [x0, y0], [W - 70, y0]], easeOut(prog(t, 0.1, 0.6)));
    g.font = `600 22px ${FONT}`; g.textAlign = 'center';
    data.forEach(([label, v], i) => {
      const k = easeOut(prog(t, 0.6 + i * 0.16, 0.8)), h = (v / max) * (y0 - 90) * k, x = x0 + 26 + i * cw;
      g.fillStyle = i === data.length - 1 ? '#c4271d' : '#9aa3ad'; g.fillRect(x, y0 - h, cw - 52, h);
      g.fillStyle = '#555b63'; g.globalAlpha = clamp(prog(t, 0.4, 0.4)); g.fillText(label, x + (cw - 52) / 2, y0 + 34);
      g.globalAlpha = clamp(k * 2); g.fillStyle = '#1b1e22'; g.fillText(String(Math.round(v * k)), x + (cw - 52) / 2, y0 - h - 14); g.globalAlpha = 1;
    });
    g.textAlign = 'left'; g.fillStyle = '#1b1e22'; g.font = `800 30px ${FONT}`; g.globalAlpha = clamp(prog(t, 0.1, 0.4)); g.fillText('Sample data: units per year', x0, 50); g.globalAlpha = 1;
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Infographic>

Facts checked on 2026-11-17. Lines marked "practice note" are working advice, not sourced facts.
