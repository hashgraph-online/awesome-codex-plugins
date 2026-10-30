# Place and date lower third

A place name over its coordinates, a date or a time — the "where and when" card for travel films, documentaries,
vlogs, case studies and event recaps. 16:9, 9:16 and 1:1; 4–6 s, shown on the first shot of a new location.

## How the pros do it
- Lower thirds that give context (location, chapter, what's next) are a distinct job from naming a person; decide the
  job first and keep only what serves it [13]. Documentaries use them to state the time and place [16].
- Two levels only: the place (the thing to read) and one supporting line (coordinates, date or local time) at 60–70%
  of its size [16][14].
- Coordinates, dates and times are numbers that sit in a fixed slot: set them in lining, tabular figures so digits do
  not jitter or misalign while they count or swap [8].
- Caps lines (country, region, kicker) get +0.05–0.12em tracking; never letterspace lowercase [7].
- Hold for two reads; a place + coordinates line is usually 3–4.5 s [14][13][6].
- Place it where the shot is calm: if the bottom is busy, centre it or raise it — a location title need not sit low [15][14].
- Simple or no animation is acceptable and often better; a typed or counting coordinate line is the one allowed flourish [14][16].
- Keep inside 5% graphics-safe at 16:9 [1] and the Meta zones in 9:16 [3]; place horizontal cards so they survive
  a horizontal video being edited into a Short (YouTube's own tip for lower thirds) [34].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `place-lower-third.clean` | Cardless: place name rises, coordinates count up beneath | Inter 700 56 px; coords IBM Plex Mono 400 26 px tabular, α 0.8; count 0.6 s `power3.out`; shadow |
| `place-lower-third.boxed` | Dark plate with a thin accent tab; date line in caps | plate #0E0F12 α 0.8, tab 6×(block height) accent #3FA9F5, date Inter 600 caps 22 px +0.12em, wipe 0.45 s |
| `place-lower-third.editorial` | Serif place, italic region, hairline, coordinates small | Fraunces 500 64 px, Instrument Serif italic 32 px, 1 px rule draws 0.5 s, coords 22 px α 0.7 |
| `place-lower-third.centered` | Centered title card in the middle-low third for wide establishing shots | centred at 72% H (16:9) / 58% H (9:16), place 72 px, kicker caps 22 px +0.14em, fade+2% scale drift over hold |

## Timing and numbers
- 30 fps, place "Lisbon" + "38.7223° N, 9.1393° W": plate/rule 0–0.45 s (14 f); place 0.10–0.55 s; coordinate
  line types or counts 0.30–0.90 s (18 f); hold until 4.2 s; exit 0.28 s (8 f) [10].
- Counting coordinates: interpolate the number with `power3.out` over 0.6 s and print with a fixed number of decimals
  (4 decimals = ~11 m precision) so the width never changes; tabular figures [8].
- Format: `38.7223° N · 9.1393° W` (degree sign, thin spaces, middle dot); dates `12 MAR 2026` or `2026-03-12`; times `07:42 LOCAL`.
- Sizes 16:9: place 56 px (5.2% H), support 26–30 px (≈ 50–55% of the place in mono, which reads larger per px);
  left x 144 px, block bottom 945 px. 9:16: place 68 px, support 32 px, left 72 px, bottom 1200 px [3]. 1:1: place 54 px.
- Colors: text #FFFFFF; support line α 0.75–0.85; plate #0E0F12 α ≥ 0.6 [9]; one accent (#3FA9F5 sky, #FF6A3D warm).

## Build it
- HyperFrames: start from `lt-side-rule` (vertical accent bar + condensed name + mono line), `lt-kicker-name` (kicker tag +
  heavy name + drawn baseline) or `lt-accent-underline`; for the centered card use `titlecard-calm`. Typing line:
  the `typewriter` component (deterministic cursor).
- Counting digits: a GSAP tween on a plain object `{v:0}` → `onUpdate` writes `v.toFixed(4)`; driven by the paused
  timeline so it scrubs. Set `font-variant-numeric: tabular-nums lining-nums`.
- Remotion: `const lat = interpolate(frame, [9, 27], [0, 38.7223], {easing: Easing.out(Easing.cubic), extrapolateRight: 'clamp'})`.
- ffmpeg on footage (no alpha render): `drawbox=x=144:y=868:w=520:h=92:color=0x0E0F12@0.8:t=fill:enable='between(t,1,5.2)',
  drawtext=fontfile=Inter-Bold.ttf:text='Lisbon':x=172:y=880:fontsize=56:fontcolor=white:enable='between(t,1.1,5.2)'`
  (fades need `alpha` expressions or a pre-rendered overlay).

## Mistakes that look amateur
- Proportional digits that jump while counting → tabular lining figures, fixed decimals [8].
- Coordinates as big as the place name → support line 50–70% of the place size [16].
- Letterspaced lowercase place names → track caps only [7].
- Location card on every cut inside the same place → once per new location.
- Card over a busy street at the bottom → raise or centre it [15].
- Flashy typewriter with sound on every character for a calm film → a 0.6 s count or a plain fade [14].

## Sources
[1] EBU R 095 — Safe areas for 16:9 television production (European Broadcasting Union technical recommendation) — https://tech.ebu.ch/publications/r095 — Action-safe 3.5% and graphics-safe 5% per edge.
[3] HopperHQ — Instagram Reel size: dimensions, aspect ratio and safe zones (Social scheduling company blog relaying Meta's percentage safe zones) — https://www.hopperhq.com/blog/instagram-reel-size/ — 9:16 safe zones: 14% top, 35% bottom, 6% sides, bottom-right 40% rail.
[6] Clevercast — BBC Subtitling Guidelines (summary) (Video platform company summarizing the BBC subtitle guidelines) — https://clevercast.com/bbc-subtitling-guidelines — 160-180 wpm = 0.33-0.375 s per word; line max 68% of a 16:9 frame.
[7] Matthew Butterick — Practical Typography: Letterspacing (Typographer and author of Practical Typography) — https://practicaltypography.com/letterspacing.html — Caps +5-12% letterspacing (0.05-0.12em); no letterspacing on lowercase.
[8] Matthew Butterick — Practical Typography: Alternate figures (Typographer and author of Practical Typography) — https://practicaltypography.com/alternate-figures.html — Tabular figures for aligned/changing numbers; lining figures with caps.
[9] W3C — Understanding WCAG 2.1 SC 1.4.3 Contrast (Minimum) (W3C Web Accessibility Initiative) — https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html — 4.5:1 / 3:1 contrast and the luminance formula used to derive plate opacity minimums.
[10] Material Design 3 motion tokens (material-web) (Google Material Design system source tokens) — https://github.com/material-components/material-web/blob/main/tokens/versions/v0_192/_md-sys-motion.scss — Emphasized decelerate/accelerate cubic-beziers and the 50-1000 ms duration scale.
[13] Chris Salters — Sports lower thirds (School of Motion) (Motion designer writing for School of Motion) — https://schoolofmotion.com/blog/sports-lower-thirds — 3-6 s on screen, read twice, define purpose (identify vs context), flexible widths, ProRes 4444 alpha.
[14] Jason Boone — How to make lower third titles that don't suck (Frame.io Insider) (Editor and doc filmmaker (National Geographic, Current TV), Premiere/AE educator) — https://blog.frame.io/2017/12/04/create-lower-thirds-titles-that-dont-suck/ — Read every word twice, plates for separation, avoid mouth/edges, consistency, simple animation.
[15] Alec Chillingworth — How to get the best lower thirds (Epidemic Sound) (Epidemic Sound blog writer) — https://www.epidemicsound.com/blog/lower-thirds/ — 3-6 s, read 2-2.5 times, move it up when the bottom is busy, avoid the eyeline.
[16] Mackenzie Scott — A documentarian's guide to lower thirds (Soundstripe) (Soundstripe blog, documentary production) — https://www.soundstripe.com/blogs/a-documentarians-guide-to-lower-thirds — Compact 2-4 lines, don't fill the bottom like news, discreet animation, legible size.
[34] @YouTubeInsider (YouTube Creator Insider) (Official YouTube team account for creators) — https://x.com/YouTubeInsider/status/1560995909089067010 — Place lower thirds so they survive editing a horizontal video into a Short.
