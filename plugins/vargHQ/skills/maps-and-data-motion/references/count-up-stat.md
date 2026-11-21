# Count-up statistic

One big number counts from zero (or a start value) to its final value over footage or a plain background, lands
with a small pulse, and holds with a short label ("2.4M users", "+38% revenue"). Use it as a hook, a proof point in
ads, a chapter beat in explainers. Formats 16:9, 9:16 and 1:1; typical length 3–5 s (preset default 4 s).

## How the pros do it
- **Ease out, hard.** The de-facto web counter (CountUp.js) defaults to 2 s with easeOutExpo, so the number races
  early and settles slowly where the eye reads it. CSS equivalent: `cubic-bezier(0.16, 1, 0.3, 1)`. [49][53]
- **For big numbers, run linear then ease only the end.** CountUp's "smart easing": above 999, count linearly to
  within 333 of the target, then ease the last 333 — otherwise easeOutExpo spends most of the time on unreadable
  millions. [49]
- **Use tabular figures.** `font-variant-numeric: tabular-nums` makes every digit the same width, so the number does not
  shuffle left and right while counting. [50]
- **Format for reading, not for precision.** Compact notation (988M, $1.2B) with 2–3 significant digits; signed
  deltas with `signDisplay:"exceptZero"` (+55%, −12%). Count with the same decimals as the final value. [51]
- **Keep the move short and simple.** Simple transitions around 1 s read best (Heer & Robertson); Material's longest
  motion tokens top out at 1000 ms. The count itself may run longer because it is the content, but the entrance should
  sit in the 250–600 ms band. [46][52]
- **Land it, then let it sit.** Give the final value a small pulse (≤ 6% scale) and hold it long enough to read with
  its label; heavy pulsing makes text unreadable (HyperFrames: 3–6% scale for text). [71]
- **Standard beats clever.** A plain big number with a clear label is understood by more people than an ornate
  infographic. [4]
- **Contrast over footage:** text ≥ 4.5:1 against what is behind it, so add a scrim or plate. [43]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `count-up-stat.center-hero` | Huge centred number, label below, subtle scrim over footage | number 22% of frame height (16:9) / 11% (9:16) / 18% (1:1), Inter 800 tnum, label 3.2% Inter 500, scrim radial 0→55% black |
| `count-up-stat.corner-tag` | Compact number + label in a rounded plate in the top-left | plate rgba(10,12,16,0.72), radius 18 px, padding 20/28 px, number 9% frame height, offset 5% from edges |
| `count-up-stat.lower-band` | Number on a lower-third band, slides in from the left | band height 16% of frame, bottom at 78% of height (9:16) / 88% (16:9), accent bar 8 px |
| `count-up-stat.split-compare` | Two stats side by side (before/after or A/B) counting together, the winner highlighted | gap 8% width, both count in sync, loser → 55% opacity at landing, winner accent colour |

## Timing and numbers
Default 4 s = 120 frames at 30 fps.

| Beat | Time (s) | Frames | Motion | Ease |
|---|---|---|---|---|
| Enter | 0.0–0.4 | 0–12 | number + label fade, rise 24 px, scale 0.96→1 | emphasized-decelerate `cubic-bezier(0.05,0.7,0.1,1)` [52] |
| Count | 0.3–2.1 | 9–63 | value 0→N (duration by size, table below) | easeOutExpo `cubic-bezier(0.16,1,0.3,1)` [49][53] |
| Land | 2.1–2.35 | 63–70 | scale 1→1.05→1, accent underline draws 0.3 s | `power2.out` |
| Hold | 2.35–4.0 | 70–120 | still (≥ 1.5 s readable hold) | — |

Count duration by size of the final number (house rule built on CountUp's 2 s default and smart easing, and Heer &
Robertson's ~1 s for simple changes) [46][49]:

| Final value | Count duration | Notes |
|---|---|---|
| 1–2 digits (7, 42, 98%) | 0.8–1.0 s (24–30 f) | easeOutExpo; integers only |
| 3 digits (250) | 1.1–1.3 s | easeOutExpo |
| 4 digits (1,250) | 1.4–1.6 s | smart easing: linear to N−333, ease the rest |
| 5–6 digits (48,000 / 250,000) | 1.6–1.9 s | smart easing; thousands separators on |
| ≥ 7 digits | 1.8 s | switch to compact: count 0→2.4 with one decimal and a fixed "M" suffix |
| Decimals (3.7×, 4.25%) | 1.0–1.4 s | count with final decimals; never show more decimals than the final |

- Number size: 18–24% of frame height for hero (16:9), 9–11% for corner/lower; in 9:16 keep the number ≤ 80% of the
  frame width at its widest value (measure the final string with tabular figures).
- Label: 22–30% of the number's size; letter-spacing +0.01em; max 4 words.
- Prefix/suffix (`$`, `%`, `×`, `M`) at 60–70% of the number size, baseline-aligned, never animated.
- 9:16 placement: centre band between 30% and 62% of height; corner preset 6% from top/left (house defaults).
- Scrim behind number over footage: 45–60% black (or brand dark) so text contrast ≥ 4.5:1 [43].

## Build it
1. Start from the HyperFrames `count-up` component (token-native counter with a restrained landing pulse), `number-wheel`
   (rolling digits for prices/scoreboards), `number-pop-in` (blur + lift reveal), or `mk-progress-stat` (big numeral
   with a progress track); varg card `big-stat-count-up`.
2. Tween a proxy `{v:0}` on the paused timeline; on update write `fmt(v)` where
   `fmt = new Intl.NumberFormat(locale, {maximumFractionDigits: d, notation: big ? "compact" : "standard"})`. [51]
3. Smart easing as two tweens: linear `0 → N−333` over 55% of the duration, then easeOutExpo `N−333 → N` for the rest. [49]
4. Lock the layout: set `font-variant-numeric: tabular-nums` and reserve the width of the final string (`min-width` or
   a hidden sizer) so the label never shifts. [50]
5. Rolling-digit variant: one column per digit with 0–9 stacked, `yPercent` per column; the leftmost column moves
   least. Over footage, add the scrim as its own clip under the number.

## Mistakes that look amateur
- Digits jittering sideways while counting → tabular figures + fixed width. [50]
- 2,847,193.62 flickering through every cent → compact notation, final precision only. [51]
- Linear count that crawls into the final value → easeOutExpo, or smart easing for large numbers. [49]
- Number lands and the video cuts within 0.5 s → hold ≥ 1.5 s with the label.
- Big bounce/elastic on the landing → ≤ 6% scale pulse. [71]
- White number on bright sky footage → scrim/plate to reach 4.5:1. [43]
- Counting a number that is not a quantity (a year, a phone number) → show it, don't count it.

## Sources
[4] John Burn-Murdoch — novelty vs understanding — https://x.com/jburnmurdoch/status/1419917498225512448
[43] Lisa Charlotte Muth — colours in style guides — https://www.datawrapper.de/blog/colors-for-data-vis-style-guides — 4.5:1 text
[46] Heer & Robertson 2007 — https://idl.cs.washington.edu/files/2007-AnimatedTransitions-InfoVis.pdf — ~1 s transitions
[49] CountUp.js (Jamie Perkins) — https://github.com/inorganik/countUp.js — 2 s, easeOutExpo, smart easing 999/333
[50] MDN — font-variant-numeric — https://developer.mozilla.org/en-US/docs/Web/CSS/font-variant-numeric
[51] MDN — Intl.NumberFormat — https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat/NumberFormat
[52] Material 3 motion tokens — https://github.com/material-components/material-web/blob/main/tokens/versions/v0_192/_md-sys-motion.scss
[53] easings.net — https://github.com/ai/easings.net/blob/master/src/easings.yml
[71] HyperFrames — hyperframes-creative audio-reactive reference — https://github.com/heygen-com/hyperframes — 3–6% scale for text
