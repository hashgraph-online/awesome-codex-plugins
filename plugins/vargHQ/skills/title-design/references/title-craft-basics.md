# Title craft basics (shared by every title template)

The numbers every title, plate and lower third in this family uses: safe areas, how long to hold text, sizes,
tracking, easing, plate contrast and stepped time. Each template file only lists what is special about it.

## Safe areas

| Frame | Keep text inside | Pixels |
|---|---|---|
| 16:9 1920×1080, broadcast-grade | EBU R95 graphics-safe: 5% in from every edge (action-safe 3.5%) [1] | x 96–1824, y 54–1026 (action: x 67–1853, y 38–1042) |
| 16:9, legacy/conservative | SMPTE-style title-safe 80% of frame (10% per edge) [2] | x 192–1728, y 108–972 |
| 16:9 on YouTube | Keep text out of the bottom 8% (player UI) [2] | y ≤ 994 |
| 9:16 1080×1920 (Reels/TikTok/Shorts) | Meta Reels zones: 14% top, 35% bottom, 6% each side clear; the like/comment rail covers the bottom-right 40% (rightmost ~21%) [3] | x 65–1015, y 269–1248; right edge ≤ 850 px below y≈1150 |
| One master for both 16:9 and 9:16 | Centered 864×1200 zone survives both [2]; YouTube also warns that lower thirds get cut when a horizontal video is edited into a Short [34] | — |

Rule: lower thirds in 16:9 start at x = 144 px (7.5% W) and their bottom edge sits at 86–88% of frame height.
In 9:16 they start at x = 72 px and their bottom edge sits at 60–64% of frame height (above the 35% bottom zone).

## How long text stays up (hold)

- Reading rate: 160–180 words per minute, i.e. 0.33–0.375 s per word (BBC guidance via [6]); adults read up to
  20 characters per second (Netflix English) [4]. Any text event: at least 5/6 s (25 frames at 30 fps), at most 7 s [5].
- Lower thirds: long enough to read every word twice [13][14]; some editors use 2–2.5 reads [15]; the usual
  range is 3–6 s [13][15].
- Formula used by every preset: `hold_s = clamp(2 × max(words × 0.36, chars / 20), 3.0, 7.0)`; above 7 s, split
  the text. The hold starts after the entrance finishes and ends when the exit starts.

| Words / characters | Hold | Frames @30 | Frames @24 |
|---|---|---|---|
| 1–4 words / ≤ 30 chars | 3.0 s | 90 | 72 |
| 5 words / 30 chars | 3.6 s | 108 | 86 |
| 7 words / 42 chars | 5.0 s | 151 | 121 |
| 9 words / 55 chars | 6.5 s | 194 | 156 |
| 10+ words | 7.0 s max, then split | 210 | 168 |

A display title (one to three words, no information to read) can hold 1.5–2.5 s; this rule is for information.

## Type scale (percent of frame height H at 16:9; percent of width W at 9:16)

Derived from subtitle sizing: Netflix sizes subtitles so 42 characters fit across [4] and BBC caps a line at 68% of a
16:9 frame [6], which puts a comfortable sans at about 5.5% of H (≈60 px at 1080p). Information text sits at or below
that, display text well above.

| Role | 16:9 (H = 1080) | 9:16 (W = 1080) |
|---|---|---|
| Display title | 9–14% H (100–150 px) | 9–12% W |
| Chapter / section title | 6–8% H (65–86 px) | 7–9% W |
| Lower-third name / place | 4.5–5.5% H (49–59 px) | 5.5–6.5% W (60–70 px) |
| Role, coordinates, date | 60–70% of the name size (3–3.5% H) | 60–70% of the name |
| Kicker / label (caps, mono) | 1.8–2.4% H (20–26 px) | 2.2–2.8% W |
| Never smaller than | 2% H (22 px) | 2.2% W (24 px) |

## Tracking and figures

- All caps and small caps: add 5–12% letterspacing, CSS `letter-spacing: 0.05em–0.12em`; lowercase needs none and
  big headlines may need it removed [7]. Presets use +0.08em for caps kickers, 0 for sentence case, −0.01 to −0.02em
  for display sizes above 8% H.
- Numbers that change or stack in columns (timecodes, coordinates, scores): tabular figures
  (`font-variant-numeric: tabular-nums`); with all caps use lining figures, never oldstyle [8].

## Easing and durations

- Material 3 tokens [10]: enter with emphasized-decelerate `cubic-bezier(0.05, 0.7, 0.1, 1)`, exit with
  emphasized-accelerate `cubic-bezier(0.3, 0, 0.8, 0.15)`, move on screen with emphasized/standard `cubic-bezier(0.2, 0, 0, 1)`.
  Durations: short 50–200 ms, medium 250–400 ms, long 450–600 ms, extra-long 700–1000 ms.
- House defaults for titles: plate/bar entrance 0.45 s (14 f @30), text entrance 0.35–0.5 s starting 0.1 s after the plate,
  exit 0.25–0.3 s (8–9 f) — exits about 35% faster than entrances. GSAP stand-ins: `expo.out` / `power3.out` in,
  `power2.in` out.
- Stagger (GSAP SplitText examples): 0.05 s per character, 0.15 s per word, 0.25 s per line [12]. Split by words or lines,
  not characters alone, to avoid odd line breaks [12].
- Ease so motion starts fast and lands slowly; let the last key's ease-out linger [17]. When animation reads late
  against the audio, move it 2–3 frames earlier [17].
- Do not use one curve for everything: a motion designer's main complaint about AI motion is "flat, fast pacing
  and repeated easing" at 60 fps [33]. Titles render at 24/25/30 fps.

## Plates and contrast

- WCAG: at least 4.5:1 for normal text, 3:1 for large text (≥ 24 px, or ≥ 18.5 px bold) [9].
- Derived from the WCAG formula [9]: white text on a black plate at opacity α over a pure-white background gives
  4.0:1 at α = 0.50 (fails), 4.7:1 at 0.55, 5.7:1 at 0.60, 10.4:1 at 0.75. **Dark plates: α ≥ 0.6, default 0.75.**
  Light plates (white, α ≥ 0.85) with #111 text stay above 13:1 on any background.
- Cardless type over footage needs a soft shadow instead (house default `0 2px 12px rgba(0,0,0,.45)`), and only on
  footage that is not busy behind the text [14][16].
- A plate exists to separate text from the picture [14]; keep it compact (2–4 lines), don't fill the whole lower area like
  a news bar unless it is a news package [16].

## Stepped time ("on twos")

- On twos = each pose held for 2 frames: at 24 fps that is 12 new images per second [41][32]. Twos change smoothness,
  not timing — a move takes the same seconds on ones or twos [42].
- 30 fps timeline: true twos = 15 images/s (hold 2). A "12 fps look" on a 30 fps timeline holds 3,2,3,2 frames — render
  the stepped piece at 24 fps when you can.
- Spider-Verse practice: animate on ones, then keep every second key and step it; no motion blur — stepped echoes
  replace it; hair/cloth simulations stay on ones [32].
- Implement by quantizing time once for the whole stepped layer: `tq = Math.floor(t * 12) / 12` and feed `tq` to
  every tween (HyperFrames block `stop-motion-cadence` does exactly this), not by giving each tween its own `steps()` ease.
  Use GSAP `steps(n)` [11] only for single properties that should tick (counters, cursor blinks).

## Seek-safe build (HyperFrames / Remotion)

- Every style is a pure function of timeline time: one paused GSAP timeline per scene (HyperFrames) or
  `useCurrentFrame()` + `interpolate()` (Remotion). No CSS transitions, no timers, no `Math.random()` at render time —
  seed randomness by frame number [44].
- Motion blur for smooth moves: render subframes and blend (ffmpeg `tmix`) [44][22]; for stepped pieces, no blur [32].
- Fonts in this family (all SIL OFL 1.1, Google Fonts): Inter, Instrument Serif, Fraunces, Space Grotesk, IBM Plex Sans,
  IBM Plex Mono, JetBrains Mono, Space Mono, VT323, Anton, Archivo / Archivo Black, Bebas Neue, Unbounded, DM Serif Display.

## Sources

Numbers match the family list in `../sources.md`.

[1] EBU R 095 — Safe areas for 16:9 television production (European Broadcasting Union technical recommendation) — https://tech.ebu.ch/publications/r095 — Action-safe 3.5% and graphics-safe 5% per edge.
[2] UtilityLab — How to calculate title-safe and action-safe margins for video (Developer guide (dev.to) with pixel tables) — https://dev.to/utilitylab/how-to-calculate-title-safe-and-action-safe-margins-for-video-1ifj — Legacy 90/80% safe areas in px for 1080p and 1080x1920; YouTube bottom 8%; 864x1200 dual-format zone.
[3] HopperHQ — Instagram Reel size: dimensions, aspect ratio and safe zones (Social scheduling company blog relaying Meta's percentage safe zones) — https://www.hopperhq.com/blog/instagram-reel-size/ — 9:16 safe zones: 14% top, 35% bottom, 6% sides, bottom-right 40% rail.
[4] Netflix — English (USA) Timed Text Style Guide (Netflix Partner Help, subtitle delivery spec) — https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-USA-Timed-Text-Style-Guide — 20 chars/s adult reading speed, 42 characters per line, 2 lines max.
[5] Netflix — Timed Text Style Guide: General Requirements (Netflix Partner Help) — https://partnerhelp.netflixstudios.com/hc/en-us/articles/215758617 — Minimum 5/6 s and maximum 7 s per text event.
[6] Clevercast — BBC Subtitling Guidelines (summary) (Video platform company summarizing the BBC subtitle guidelines) — https://clevercast.com/bbc-subtitling-guidelines — 160-180 wpm = 0.33-0.375 s per word; line max 68% of a 16:9 frame.
[7] Matthew Butterick — Practical Typography: Letterspacing (Typographer and author of Practical Typography) — https://practicaltypography.com/letterspacing.html — Caps +5-12% letterspacing (0.05-0.12em); no letterspacing on lowercase.
[8] Matthew Butterick — Practical Typography: Alternate figures (Typographer and author of Practical Typography) — https://practicaltypography.com/alternate-figures.html — Tabular figures for aligned/changing numbers; lining figures with caps.
[9] W3C — Understanding WCAG 2.1 SC 1.4.3 Contrast (Minimum) (W3C Web Accessibility Initiative) — https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html — 4.5:1 / 3:1 contrast and the luminance formula used to derive plate opacity minimums.
[10] Material Design 3 motion tokens (material-web) (Google Material Design system source tokens) — https://github.com/material-components/material-web/blob/main/tokens/versions/v0_192/_md-sys-motion.scss — Emphasized decelerate/accelerate cubic-beziers and the 50-1000 ms duration scale.
[11] GSAP docs — SteppedEase (GreenSock animation platform documentation) — https://gsap.com/docs/v3/Eases/SteppedEase — steps(n) ease syntax for ticking properties.
[12] GSAP docs — SplitText (GreenSock animation platform documentation) — https://gsap.com/docs/v3/Plugins/SplitText/ — Split types, mask option, aria, onSplit; example staggers 0.05/0.15/0.25 s.
[13] Chris Salters — Sports lower thirds (School of Motion) (Motion designer writing for School of Motion) — https://schoolofmotion.com/blog/sports-lower-thirds — 3-6 s on screen, read twice, define purpose (identify vs context), flexible widths, ProRes 4444 alpha.
[14] Jason Boone — How to make lower third titles that don't suck (Frame.io Insider) (Editor and doc filmmaker (National Geographic, Current TV), Premiere/AE educator) — https://blog.frame.io/2017/12/04/create-lower-thirds-titles-that-dont-suck/ — Read every word twice, plates for separation, avoid mouth/edges, consistency, simple animation.
[15] Alec Chillingworth — How to get the best lower thirds (Epidemic Sound) (Epidemic Sound blog writer) — https://www.epidemicsound.com/blog/lower-thirds/ — 3-6 s, read 2-2.5 times, move it up when the bottom is busy, avoid the eyeline.
[16] Mackenzie Scott — A documentarian's guide to lower thirds (Soundstripe) (Soundstripe blog, documentary production) — https://www.soundstripe.com/blogs/a-documentarians-guide-to-lower-thirds — Compact 2-4 lines, don't fill the bottom like news, discreet animation, legible size.
[17] Joey Korenman — Kinetic typography in After Effects, part 1 (School of Motion) (Founder of School of Motion) — https://schoolofmotion.com/blog/kinetic-typography-after-effects-part-1 — Sync markers, ghost copies 50% two frames early, nudge 2-3 frames earlier, lingering ease-out.
[22] FFmpeg Filters Documentation (FFmpeg project) — https://ffmpeg.org/ffmpeg-filters.html — rgbashift, chromashift, noise, gblur, geq, tmix, lagfun options.
[32] CG Spectrum — Spider-Man: Into the Spider-Verse, how they got that look (Interviews with supervising animator Jeff Panko and lead lighting/comp artist Geeta Basantani) — https://cgspectrum.com/blog/spider-man-into-the-spider-verse-how-they-got-that-mind-blowing-look — Animate on ones then step to twos; no motion blur, stepped echoes; sims on ones.
[33] @jakeinmotion (Jake Bartlett) (Motion designer and kinetic-type instructor (Skillshare), maker of the AE tools Type Jazz and Railcut) — https://x.com/jakeinmotion/status/2104022458865218019 — AI motion fails with 60 fps, flat fast pacing and repeated easing.
[34] @YouTubeInsider (YouTube Creator Insider) (Official YouTube team account for creators) — https://x.com/YouTubeInsider/status/1560995909089067010 — Place lower thirds so they survive editing a horizontal video into a Short.
[41] @TrevElViz (Trev El. Viz) (Frame-by-frame animator) — https://x.com/TrevElViz/status/1833544353991516503 — On twos = 12 fps, each drawing held 2 frames at 24 fps.
[42] @HoodyPisDed (HoodyP) (Animator; post with 100k views and 250 bookmarks) — https://x.com/HoodyPisDed/status/2099406048742588424 — Twos/threes change smoothness, not timing.
[44] @twoclipping (Creator of a code-only motion design prompt template (1.1M views)) — https://x.com/twoclipping/status/2103273003555402193 — Every style computed from time in seek(t); subframes blended with ffmpeg tmix for motion blur.
