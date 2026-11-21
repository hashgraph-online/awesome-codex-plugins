# Self-drawing bar and line chart

A chart that builds itself from the user's numbers: bars grow from the baseline in a stagger, or a line draws left to
right with its value riding the pen tip, then one bar or point is highlighted with a callout. Use it in explainers,
investor and product updates, social posts with one number story. Formats 16:9, 9:16 and 1:1; typical length 5–8 s
(preset default 6 s).

## How the pros do it
- **Bars start at zero, always.** The FT Visual Vocabulary: columns "must always start at 0"; Datawrapper refuses
  truncated bar axes because they exaggerate differences (Pandey et al. 2015). If the differences are small, switch to a
  dot plot, a line, or plot the differences. [40][41]
- **Lines don't have to.** Line charts need not start at zero; add a zero line when values approach it. Burn-Murdoch:
  extending a line chart's y-axis to zero can add no clarity; set the lower extent so it does not read as a hard floor
  and use light gridlines instead of a dark baseline. [1][2][42]
- **One highlighted series, the rest grey.** Use grey for context and your strongest colour for the one series that
  carries the story; thicker line for the key series. [42][43]
- **Label directly; skip the legend.** Direct labels replace keys, and line charts are the easiest to label directly;
  match label colour to the line. Put units in the title/subtitle and append the unit to the first tick instead of an
  axis title. Burn-Murdoch's "narrative legend" puts the key's symbols into the subtitle sentence. [3][44][45]
- **About one second per transition, slow-in slow-out, staged.** Heer & Robertson: ~1 s transitions work best, ease in
  and out, stage complex changes (axes rescale first, then values), and stagger marks so they do not overlap. [46]
- **Keep each mark's identity across changes** (key the data join by category, not by index), and animate only when
  the motion explains something; otherwise cut or cross-fade. [47]
- **Reveal in steps.** Flourish: break a data story into steps and add annotations at the moments that matter, rather
  than everything at once. [48]
- **Standard forms beat novel ones.** Burn-Murdoch: novel designs impress few and are understood by fewer. Bars for
  comparing categories, lines for change over time. [4][40][42]
- **Contrast and figures:** marks ≥ 3:1 against their neighbours, text ≥ 4.5:1; tabular figures for every value label
  so numbers do not jitter while counting. [43][50]
- **Format numbers for reading:** compact notation for big values (988M), signs on changes (+55%). [51]
- **Plain curves.** Use straight segments or a monotone curve; Datawrapper recommends its plain "Curved" option over
  natural/cardinal splines, which overshoot the data. [42]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `self-drawing-chart.bars` | Vertical bars rise from a zero baseline in a stagger; one bar recolours to accent with a callout | bar width 62% of slot, corner radius 4 px (top only), grey #C9CED6, accent #2F6BFF, stagger 0.07 s, grow 0.7 s ease-out, values on top in Inter 600 tnum |
| `self-drawing-chart.line` | One accent line draws left→right with the value riding the tip; context lines in grey; end dot + big label | key line 6 px #E4572E, context lines 2.5 px #BFC5CC, draw 3.0 s sine.inOut, end dot 14 px, label 5% frame height |
| `self-drawing-chart.editorial` | Print-editorial look: off-white paper, serif title, hairline grid | bg #FBF8F2, grid #E4DED3 1 px, title Source Serif 4 700, accent #B23A48, labels Inter 500 |

## Timing and numbers
Default 6 s = 180 frames at 30 fps.

**Bars**
| Beat | Time (s) | Frames | Motion | Ease |
|---|---|---|---|---|
| Title + subtitle | 0.0–0.5 | 0–15 | fade + rise 16 px | emphasized-decelerate `cubic-bezier(0.05,0.7,0.1,1)` [52] |
| Axis + grid | 0.3–0.8 | 9–24 | gridlines fade to 100%, baseline draws | `power2.out` |
| Bars grow | 0.8–2.6 | 24–78 | each bar 0.7 s, stagger 0.07 s (≤ 12 bars) | easeOutCubic `cubic-bezier(0.33,1,0.68,1)` [53] |
| Values | 1.2–3.0 | 36–90 | each label counts up with its bar, fades in over last 40% | same as bar |
| Highlight | 3.2–3.9 | 96–117 | others → grey #C9CED6, key bar → accent, callout in | `power2.inOut` 0.6 s |
| Hold | 3.9–6.0 | 117–180 | still | — |

**Line**
| Beat | Time (s) | Frames | Motion | Ease |
|---|---|---|---|---|
| Title + axes | 0.0–0.6 | 0–18 | as above | as above |
| Context lines | 0.4–0.9 | 12–27 | grey lines fade in (not drawn) | `power1.out` |
| Key line draws | 0.8–3.8 | 24–114 | DrawSVG 0→100%, value label rides the tip, counting | easeInOutSine `cubic-bezier(0.37,0,0.63,1)` [53] |
| End dot + label | 3.8–4.4 | 114–132 | dot pops 0→1.15→1, big value + delta (+55%) | `back.out(1.7)` |
| Hold | 4.4–6.0 | 132–180 | still | — |

- Transitions: 0.6–1.2 s each (Heer & Robertson ~1 s) [46]; any axis rescale gets its own 0.6 s stage before values move.
- Stagger: 0.05–0.08 s per bar; cap total stagger at 0.8 s (≥ 12 bars → group or sort, don't stagger longer).
- Sizes at 1080p: title 5.5–6.5% of frame height; tick labels 2.2–2.6%; value labels 2.6–3%; line 5–6 px key / 2–3 px
  context; gridlines 1 px at #E3E6EA (light) or #2A2F37 (dark), lighter than tick labels [43].
- Chart area: 16:9 → 80% width × 62% height; 9:16 → 88% width × 46% height in the middle band (title above, never in
  the bottom 22%); 1:1 → 84% × 60% (house defaults).
- Max categories: 12 bars in 16:9, 7 bars in 9:16 (rotate to horizontal bars beyond that); max 5 lines, 1 highlighted.
- Number format: `Intl.NumberFormat(locale,{notation:"compact", maximumSignificantDigits:3})`; deltas with
  `signDisplay:"exceptZero"`; `font-variant-numeric: tabular-nums` everywhere [50][51].

## Build it
1. Start from the HyperFrames registry: `chart-story` (bars/line/donut/progress from data with an accented callout),
   `data-chart` (bar + line, NYT-style type), `mk-line-graph` (one or two series with labels riding the draw front),
   `animated-bar-chart`; for racing ranks `bar-chart-race`. varg cards: `bars-grow-with-labels`,
   `line-draws-riding-label`, `ranked-bar-race`.
2. Build scales with d3 (`scaleBand` + `scaleLinear().domain([0, max]).nice()` for bars; for lines a domain that
   includes zero only if values come near it) [41][42].
3. Bars: animate `scaleY` from 0 with `transform-origin: bottom` (or the `height`/`y` attributes in SVG), one tween per
   bar keyed by category; value labels tween a proxy number and write `fmt(v)` on update.
4. Line: `d3.line().curve(d3.curveMonotoneX)` → path; `drawSVG` 0→100%; for the riding label, sample
   `path.getPointAtLength(p·L)` on update and invert x to the data index to show the interpolated value. [34]
5. Everything on one paused timeline; labels and numbers come only from timeline progress (seek-safe).

## Mistakes that look amateur
- Truncated bar axis that makes a 3% gain look like a doubling → zero baseline, or switch to dots/line. [40][41]
- Rainbow categorical colours with a legend → grey everything, one accent, direct labels. [43][44]
- Bars all popping in together, or a 3 s stagger → 0.05–0.08 s stagger, ≤ 0.8 s total. [46]
- Axis rescales while bars move → stage the rescale first. [46]
- Jittering numbers (proportional figures) and over-precise decimals → tabular figures, 2–3 significant digits. [50][51]
- Spline that overshoots the data (natural/cardinal) → monotone curve. [42]
- Axis title "Revenue (USD millions)" rotated 90° → unit in the subtitle or appended to the first tick. [45]

## Sources
[1] John Burn-Murdoch (FT) — design details reply — https://x.com/jburnmurdoch/status/1369657097227546626 — gradual context, light gridlines
[2] John Burn-Murdoch — y-axis to zero reply — https://x.com/jburnmurdoch/status/1369657055494238215
[3] John Burn-Murdoch — narrative legend — https://x.com/jburnmurdoch/status/1256313195095977986
[4] John Burn-Murdoch — novelty vs understanding — https://x.com/jburnmurdoch/status/1419917498225512448
[34] GSAP — DrawSVGPlugin — https://gsap.com/docs/v3/Plugins/DrawSVGPlugin/
[40] FT Visual Vocabulary — https://github.com/Financial-Times/chart-doctor/tree/main/visual-vocabulary
[41] Datawrapper Academy — bars start at zero — https://www.datawrapper.de/academy/why-our-column-and-bar-charts-start-at-zero
[42] Datawrapper Academy — line charts — https://www.datawrapper.de/academy/what-to-consider-when-creating-line-charts
[43] Lisa Charlotte Muth — colours in style guides — https://www.datawrapper.de/blog/colors-for-data-vis-style-guides
[44] Lisa Charlotte Muth — colour keys — https://www.datawrapper.de/blog/color-keys-for-data-visualizations
[45] Datawrapper Academy — axis labels — https://www.datawrapper.de/academy/why-datawrapper-does-not-include-axis-labels-for-many-charts
[46] Heer & Robertson 2007 — https://idl.cs.washington.edu/files/2007-AnimatedTransitions-InfoVis.pdf
[47] Mike Bostock — Object Constancy — https://bost.ocks.org/mike/constancy/
[48] Flourish — animated charts — https://flourish.studio/blog/animated-charts/
[50] MDN — font-variant-numeric — https://developer.mozilla.org/en-US/docs/Web/CSS/font-variant-numeric
[51] MDN — Intl.NumberFormat — https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat/NumberFormat
[52] Material 3 motion tokens — https://github.com/material-components/material-web/blob/main/tokens/versions/v0_192/_md-sys-motion.scss
[53] easings.net — https://github.com/ai/easings.net/blob/master/src/easings.yml
