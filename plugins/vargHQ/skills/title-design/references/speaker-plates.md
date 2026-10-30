# Speaker plates

A set of on-camera graphics for talking-head videos: a two-line plate, a ticker, a caption bar, a full title card and a
corner tag, each in light or dark. Use it when someone talks to camera for minutes and the edit needs identity,
context, a key line on screen and a persistent show tag. 16:9 and 9:16; each element 3–7 s (the tag can stay).

## How the pros do it
- Each plate has one job: identify (name, title, handle), give context (location, chapter, what's next) or brand
  (show tag) [13]. Don't mix jobs in one plate.
- Information on screen needs time: every word read twice, 3–6 s, and a text event never longer than 7 s [14][13][5].
- Caption bars follow subtitle rules: ≤ 42 characters per line, at most 2 lines, adults read ≤ 20 characters per
  second [4]; at 16:9 a line should not run wider than 68% of the frame [6].
- Viewers decide in 1–2 seconds whether to stay; on-screen context that tracks what the guest is saying is an editorial
  skill, not decoration [35].
- Keep plates compact; filling the whole lower area like a news broadcast is the documentary mistake [16]. A full
  news ticker is the exception — it is a deliberate news-package look.
- Light vs dark: choose by footage. Dark plate α ≥ 0.6 (≥ 4.5:1 with white text); light plate α ≥ 0.85 with #111 text [9].
- In 9:16 everything that must be read lives between 14% from the top and 35% from the bottom, and clear of the right
  rail; plan horizontal masters so plates survive a vertical crop [3][34].
- Keep animation subtle and consistent across every plate type so the system reads as one show [16][14].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `speaker-plates.two-line` | Name + role plate, light or dark | see `name-lower-third.boxed`; dark #0E0F12 α 0.85 / light #FFFFFF α 0.92 + #111 text |
| `speaker-plates.ticker` | Label block + crawling text at the very bottom | bar height 6.5% H, label caps +0.1em, crawl speed 420 px/s at 1080p (≈ 20 chars/s at 38 px), linear ease |
| `speaker-plates.caption-bar` | Key quote / summary line on a bar | ≤ 42 chars × 2 lines, Inter 600 46 px, bar α 0.8, line width ≤ 68% W, hold = chars/20 × 2 clamp 3–7 s |
| `speaker-plates.title-card` | Full-frame or half-frame topic card between segments | kicker mono caps 24 px +0.12em, title 7% H, hold 2.5–3.5 s, in 0.6 s / out 0.35 s |
| `speaker-plates.corner-tag` | Small persistent show/episode tag | top-left inside 5% safe (x 96, y 54 at 1080p), 22–26 px caps +0.08em, α 0.9, in 0.4 s, stays or leaves with segment |

## Timing and numbers
- Two-line plate: as in `name-lower-third.md` — in 0.45 s, hold by formula, out 0.28 s.
- Ticker crawl: a crawl readable at 20 chars/s [4] moves at `20 × average glyph advance`. Inter at 38 px ≈ 21 px per
  glyph → ~420 px/s (14 px/frame at 30 fps). Constant velocity (linear), never eased mid-crawl; the bar wipes in 0.4 s
  before the text starts. Separator: `•` or `/` with 1.5 em spaces. Bar: label block 18% of bar width, accent fill; text
  area #0E0F12 α 0.9.
- Caption bar: center or left-aligned at 80–84% H (16:9); in 9:16 at 58–62% H; 2 lines max [4]; plate padding 0.4 em.
- Title card: 16:9 title 72–86 px (6.7–8% H), kicker 24 px; centred; hairline 1 px draws 0.6 s; hold 2.5–3.5 s
  (display text with few words, not information).
- Corner tag: 22–26 px, `letter-spacing: 0.08em` caps [7]; in 9:16 keep it below the 14% top zone (y ≥ 270 px) [3].
- Light theme: plate #FFFFFF α 0.92, text #111111, accent #2B59FF. Dark theme: plate #0E0F12 α 0.85, text #FFFFFF, accent #FFD23F.

## Build it
- HyperFrames: `lt-clean-bar` / `lt-dark-card` (two-line), `news-ticker` (label + headline ribbon + scrolling crawl),
  `ticker-takeover`, `lt-soft-pill` (light pill), `titlecard-calm` / `titlecard-lockup` (title card), `lower-third-bild`
  (hard news style). Put each plate type in its own sub-composition and on its own track.
- Ticker in GSAP: measure the strip width `w`, then `tl.fromTo(strip, {x: W}, {x: -w, duration: (W + w) / 420, ease: 'none'})`.
  Seamless loop: duplicate the strip and wrap with `gsap.utils.wrap`.
- Remotion: ticker `x = W - (frame / fps) * 420`; caption bar holds use `Sequence` with `durationInFrames = Math.round(hold*fps)`.
- Corner tag stays on its own track for the whole segment; fade only at segment boundaries.

## Mistakes that look amateur
- Five different plate styles in one video → one system: same font, same accent, same in/out [14][16].
- Caption bar with three lines of 60 characters → ≤ 42 chars, ≤ 2 lines, split into two events [4].
- Ticker that eases or stutters → linear, constant px/s, readable at 20 chars/s [4].
- Corner tag hiding under the platform UI in vertical → y ≥ 14% from the top [3].
- Light plate on bright footage with grey text → #111 text, α ≥ 0.85 [9].
- Plates that cover the face in close-ups → shrink or drop the plate [14].

## Sources
[3] HopperHQ — Instagram Reel size: dimensions, aspect ratio and safe zones (Social scheduling company blog relaying Meta's percentage safe zones) — https://www.hopperhq.com/blog/instagram-reel-size/ — 9:16 safe zones: 14% top, 35% bottom, 6% sides, bottom-right 40% rail.
[4] Netflix — English (USA) Timed Text Style Guide (Netflix Partner Help, subtitle delivery spec) — https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-USA-Timed-Text-Style-Guide — 20 chars/s adult reading speed, 42 characters per line, 2 lines max.
[5] Netflix — Timed Text Style Guide: General Requirements (Netflix Partner Help) — https://partnerhelp.netflixstudios.com/hc/en-us/articles/215758617 — Minimum 5/6 s and maximum 7 s per text event.
[6] Clevercast — BBC Subtitling Guidelines (summary) (Video platform company summarizing the BBC subtitle guidelines) — https://clevercast.com/bbc-subtitling-guidelines — 160-180 wpm = 0.33-0.375 s per word; line max 68% of a 16:9 frame.
[7] Matthew Butterick — Practical Typography: Letterspacing (Typographer and author of Practical Typography) — https://practicaltypography.com/letterspacing.html — Caps +5-12% letterspacing (0.05-0.12em); no letterspacing on lowercase.
[9] W3C — Understanding WCAG 2.1 SC 1.4.3 Contrast (Minimum) (W3C Web Accessibility Initiative) — https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html — 4.5:1 / 3:1 contrast and the luminance formula used to derive plate opacity minimums.
[13] Chris Salters — Sports lower thirds (School of Motion) (Motion designer writing for School of Motion) — https://schoolofmotion.com/blog/sports-lower-thirds — 3-6 s on screen, read twice, define purpose (identify vs context), flexible widths, ProRes 4444 alpha.
[14] Jason Boone — How to make lower third titles that don't suck (Frame.io Insider) (Editor and doc filmmaker (National Geographic, Current TV), Premiere/AE educator) — https://blog.frame.io/2017/12/04/create-lower-thirds-titles-that-dont-suck/ — Read every word twice, plates for separation, avoid mouth/edges, consistency, simple animation.
[16] Mackenzie Scott — A documentarian's guide to lower thirds (Soundstripe) (Soundstripe blog, documentary production) — https://www.soundstripe.com/blogs/a-documentarians-guide-to-lower-thirds — Compact 2-4 lines, don't fill the bottom like news, discreet animation, legible size.
[34] @YouTubeInsider (YouTube Creator Insider) (Official YouTube team account for creators) — https://x.com/YouTubeInsider/status/1560995909089067010 — Place lower thirds so they survive editing a horizontal video into a Short.
[35] @sallyshin (Sally Shin) (CNBC EVP Growth & Partnerships, former network news executive) — https://x.com/sallyshin/status/2046419371396833446 — 1-2 s to capture a viewer; lower-third context synced to guest commentary is an editorial skill.
