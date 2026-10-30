# Versus timeline (two numbers diverging over the years)

Two values side by side move in opposite directions while a year counter ticks forward: prices up and wages flat,
users up and costs down, one country rising and another falling. Two lines draw on a shared axis, each with its
current value riding the line tip, and the gap is called out at the end. Formats 16:9, 9:16 and 1:1; typical length
6–10 s (preset default 8 s).

## How the pros do it
- **Same axis, same scale, one chart.** Two series that are compared must share the y scale so the gap is honest;
  for a change-over-time comparison the FT Visual Vocabulary points to lines, slopes, or line + column. Choose the time
  window deliberately; it decides the story. [40]
- **Index when units differ.** If the two series have different units (price vs wage), plot both as % change or
  "index = 100 in the first year" rather than a second y-axis (house rule). Lines need not start at zero, but add a
  zero/100 line when values come near it. [2][42]
- **Reveal context gradually and use light gridlines.** Burn-Murdoch's FT charts build context step by step and avoid
  a heavy baseline that reads as a floor. [1]
- **Label the lines at their tips; no legend.** Direct labels, colour-matched; or write the key into the subtitle
  ("**Rent** vs **wages**", each word in its line colour) — a narrative legend. [3][44]
- **Two hues that differ in lightness, not red vs green.** Pick two colours with clearly different lightness so the
  pair survives colour-blindness and greyscale; avoid red/green of similar lightness. [36][43]
- **The year counter steps; values glide.** Advance years at a constant rate (linear), show integer years only, and
  interpolate the values linearly between yearly data points, so equal time on screen means equal years (house rule).
  Keep slow-in slow-out for the entry and the final settle, where Heer & Robertson's easing advice applies. [46]
- **Stage it.** Axis rescale (if any) is its own stage before the lines move; final annotation only after motion
  stops. About 1 s per simple transition; in Heer & Robertson's study staged sequences ran 2 s. [46]
- **Count the values with tabular figures** and signed formatting for the final gap (+212%, −18%). [50][51]
- **Animate only if the change over time is the point;** otherwise a static slope chart says it in one frame. [47][48]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `versus-timeline.light-paper` | Warm paper, black ink type, two lines (deep blue rising, orange falling) | bg #F6F1E7, text #1A1A1A, grid #E2DBCD 1 px, A #1F4E9A, B #E07A1F, lines 6 px, year Source Serif 4 700 at 9% height |
| `versus-timeline.dark-ink` | Near-black background, bright pair, big ghosted year behind the chart | bg #0E0F12, text #F2F2F2, grid #24272E, A #4FD1C5, B #F6AD55, year 28% height at 8% opacity behind plot |
| `versus-timeline.footage-overlay` | Over b-roll: scrim, white type, the two numbers large with mini lines below | scrim 55% #000, numbers 10% height Inter 800 tnum, mini chart 30% height, A #7CC4FF, B #FFB86B |

## Timing and numbers
Default 8 s = 240 frames at 30 fps.

| Beat | Time (s) | Frames | Motion | Ease |
|---|---|---|---|---|
| Title + labels | 0.0–0.6 | 0–18 | title, start values, start year in | emphasized-decelerate `cubic-bezier(0.05,0.7,0.1,1)` [52] |
| Run | 0.6–6.4 | 18–192 | year steps linearly; both lines draw; values ride tips | linear for time; first/last 0.3 s eased with `power1` |
| Settle | 6.4–6.8 | 192–204 | end dots pop, values lock | `back.out(1.5)` |
| Gap callout | 6.8–7.4 | 204–222 | bracket draws between the two ends, "+212% vs −18%" appears | `power2.out` |
| Hold | 7.4–8.0 | 222–240 | still | — |

- Year rate: 3–6 years per second (25 years in ~5.8 s ≈ 4.3/s); faster than 8/s is unreadable; slower than 2/s drags
  (house defaults).
- Year counter: integers only, `tabular-nums`, 7–9% of frame height (light/footage) or a 25–30% ghosted backdrop (dark).
- Values: 4.5–6% of frame height at the line tips; 2–3 significant digits; final gap with `signDisplay:"exceptZero"` [51].
- Lines: 5–6 px each at 1080p, round joins; end dots 14 px; context gridlines 1 px, lighter than labels [43].
- Lightness gap between the two series ≥ 0.2 in OKLCH lightness (house threshold) so they separate in greyscale;
  the principle (lightness carries the signal, avoid same-lightness red/green) is from [36].
- 9:16: stack the two current values above the chart (A left, B right), chart in the middle band 34–70% of height.

## Build it
1. Starting blocks: HyperFrames `mk-line-graph` (one or two series drawn with labels riding the draw front) and
   `count-up` / `number-wheel` for the values; `decline-chart` for the falling side's mood (background darkens with the
   value). varg cards: `pain-metric-falls`, `line-draws-riding-label`.
2. Data → yearly arrays `A[y]`, `B[y]` (indexed to 100 if units differ). Scales: x = years, y = shared domain with
   `.nice()`; include 0/100 only if a series nears it. [42]
3. One proxy `{t:0}` tweened linearly 0→1 over the run. On update: `yf = y0 + t·(y1−y0)`; `year = Math.floor(yf)`;
   value = linear interpolation between `A[year]` and `A[year+1]` by `yf − year`; draw each path up to `yf` (clip-path
   rect or DrawSVG at the matching fraction); place the riding labels at the tip. [34]
4. Keep labels from colliding: when the two tips are closer than 1.2× label height, push them apart vertically with a
   leader line.
5. Gap callout: a bracket path drawn with DrawSVG after the lines stop, then the delta text.

## Mistakes that look amateur
- Dual y-axes that make any two lines cross wherever you like → shared scale or index to 100 (house rule).
- Eased year counter that slows at the end so the last years "take longer" → linear time, eased only at the edges.
- Fractional years (2017.4) on screen → integer years; values may glide. 
- Red vs green pair of the same lightness → two hues far apart in lightness. [36]
- Legend box in a corner → labels at the line tips or a narrative legend in the subtitle. [3][44]
- Gap number appears while lines still move → callout only after motion stops. [46]

## Sources
[1] John Burn-Murdoch (FT) — design details — https://x.com/jburnmurdoch/status/1369657097227546626
[2] John Burn-Murdoch — y-axis to zero — https://x.com/jburnmurdoch/status/1369657055494238215
[3] John Burn-Murdoch — narrative legend — https://x.com/jburnmurdoch/status/1256313195095977986
[34] GSAP — DrawSVGPlugin — https://gsap.com/docs/v3/Plugins/DrawSVGPlugin/
[36] Joshua Stevens — Introducing Phosphor — https://www.joshuastevens.net/blog/introducing-phosphor/ — lightness, red/green
[40] FT Visual Vocabulary — https://github.com/Financial-Times/chart-doctor/tree/main/visual-vocabulary
[42] Datawrapper Academy — line charts — https://www.datawrapper.de/academy/what-to-consider-when-creating-line-charts
[43] Lisa Charlotte Muth — colours in style guides — https://www.datawrapper.de/blog/colors-for-data-vis-style-guides
[44] Lisa Charlotte Muth — colour keys — https://www.datawrapper.de/blog/color-keys-for-data-visualizations
[46] Heer & Robertson 2007 — https://idl.cs.washington.edu/files/2007-AnimatedTransitions-InfoVis.pdf
[47] Mike Bostock — Object Constancy — https://bost.ocks.org/mike/constancy/
[48] Flourish — animated charts — https://flourish.studio/blog/animated-charts/
[50] MDN — font-variant-numeric — https://developer.mozilla.org/en-US/docs/Web/CSS/font-variant-numeric
[51] MDN — Intl.NumberFormat — https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat/NumberFormat
[52] Material 3 motion tokens — https://github.com/material-components/material-web/blob/main/tokens/versions/v0_192/_md-sys-motion.scss
