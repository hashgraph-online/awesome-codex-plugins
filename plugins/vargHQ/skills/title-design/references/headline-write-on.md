# Headline write-on

A headline that writes on letter by letter (or word by word, or line by line) and then holds: opening titles,
chapter cards, section breaks, thumbnails-in-motion. Four looks: Display, Editorial, Chapter card and Kinetic.
16:9, 9:16 and 1:1; about 4 s.

## How the pros do it
- Pick the split by the job: characters for one to three display words, words for a sentence, lines for an editorial
  deck. Splitting by characters alone can cause odd line breaks; split words + chars together [12].
- Reference staggers: 0.05 s per character, 0.15 s per word, 0.25 s per line [12]; reveal lines through a mask
  (`mask: "lines"`) for the editorial line-rise look [12].
- Ease so each letter starts fast and lands slowly; give the last key a long ease-out so the type settles instead of
  stopping [17]. Separate the motion from the hold — the reading happens when nothing moves.
- Choose the face like casting an actor; the Emmy-winning Stranger Things team rebuilt its animation after switching
  typeface late [29]. Simple, purely typographic titles are "the hardest" to get right [29].
- Period feel comes from motion as much as from the font: that team rejected letters snapping into place as wrong for
  the era and used slow drifting assembly with fluid, jitter-free movement plus grain and a few imperfections [29].
- Type can be deliberately subordinate: a left-aligned sans with a thin rule above it, distinctive but quiet [30].
- For kinetic, beat-driven type: lead the beat with ghost copies (50% opacity, 2 frames early) before the solid word
  lands [17]; on word swaps, stretch letters along the motion and cut on the fastest frame, easing ~90% at both ends [18].
- Big display sizes need negative or zero tracking; caps kickers need +0.05–0.12em [7].
- Don't make it fast, flat and evenly eased — vary timing and let it breathe [33].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `headline-write-on.display` | Big sans, per-character rise + fade, tight tracking | Inter 800, 12% H, −0.02em, chars y 60%→0 + opacity, 0.55 s each `expo.out`, stagger 0.04 s, hold ≥ 1.8 s |
| `headline-write-on.editorial` | Serif deck, masked line rise | Instrument Serif 400 8% H, lines `mask:'lines'` yPercent 105→0, 0.8 s `power3.out`, stagger 0.18 s |
| `headline-write-on.chapter` | Mono kicker + title + hairline that draws | kicker JetBrains Mono 500 2.2% H caps +0.12em; title Fraunces 600 7% H fade + 8 px rise 0.7 s; rule 1 px draws 0.6 s; 1.5% scale drift during hold |
| `headline-write-on.kinetic` | Word slams on the beat with ghosts and smear | Anton 400 14% H caps +0.02em; ghost 50% at −2 f; slam scale 1.12→1 in 6 f `expo.out`; exit smear 6 f |

## Timing and numbers
- Display (30 fps, 4 s): 0.2 s lead-in; letters 0.2–1.3 s (stagger 0.04 s × ~12 chars + 0.55 s); hold 1.3–3.5 s;
  exit 3.5–3.8 s: letters drop out with `power2.in`, stagger 0.02 s (exits faster than entries) [10].
- Editorial: 3 lines × 0.18 s stagger + 0.8 s = 1.16 s build; hold ≥ 2 × reading time (0.36 s/word) [6].
- Chapter card: kicker 0–0.4 s; title 0.25–0.95 s; rule 0.5–1.1 s; hold to 3.4 s; whole card fades 0.35 s.
- Kinetic at 120 BPM: one word per beat (15 f at 30 fps); ghost copies at −2 and −1 frames, 50% opacity; slam lands
  on the beat frame; words longer than 8 letters get 2 beats.
- Sizes: display 10–14% H (16:9) or 10–12% W (9:16); editorial 7–9% H; chapter title 6–8% H; max line length
  ≈ 68% of the frame width [6].
- Colors: on black #0A0A0A use #F2F2F2 (not pure white) for long holds; accent one hue only.
- Fonts (OFL): Inter, Instrument Serif, Fraunces, JetBrains Mono, Anton.

## Build it
- HyperFrames: `text-stagger` (enter/shimmer/exit words), `staggered-fade-up`, `titlecard-calm` / `titlecard-lockup`
  (chapter card), `kinetic-type`, `hw-write-title` (handwritten true write-on), `typewriter` (caret version).
- GSAP: `SplitText.create(el, {type: 'words,chars', mask: 'lines', aria: 'auto'})` [12]; build the tweens inside
  `onSplit` so re-splits after font load stay in sync; add them to the scene's paused timeline. Wait for
  `document.fonts.ready` before the first split.
- Remotion: split the string yourself into spans; per-char progress
  `interpolate(frame - i * 1.2, [0, 16], [0, 1], {easing: Easing.bezier(0.16, 1, 0.3, 1), extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})`.
- Grain for the chapter look: HyperFrames `grain-overlay` at 6–8% opacity.

## Mistakes that look amateur
- Letters snapping into place with a bounce on a nostalgic or serious title → slow fluid assembly [29].
- Same 0.3 s ease-in-out on every element → decelerate in, accelerate out, varied durations [33][10].
- Splitting by characters only, breaking words across lines → split words+chars, mask lines [12].
- Pure white #FFFFFF display type on pure black for 4 s → #F2F2F2 or a subtle grain.
- Kinetic words landing late on the beat → shift 2–3 frames earlier [17].
- Headline wider than ~68% of the frame → break into two lines [6].

## Sources
[6] Clevercast — BBC Subtitling Guidelines (summary) (Video platform company summarizing the BBC subtitle guidelines) — https://clevercast.com/bbc-subtitling-guidelines — 160-180 wpm = 0.33-0.375 s per word; line max 68% of a 16:9 frame.
[7] Matthew Butterick — Practical Typography: Letterspacing (Typographer and author of Practical Typography) — https://practicaltypography.com/letterspacing.html — Caps +5-12% letterspacing (0.05-0.12em); no letterspacing on lowercase.
[10] Material Design 3 motion tokens (material-web) (Google Material Design system source tokens) — https://github.com/material-components/material-web/blob/main/tokens/versions/v0_192/_md-sys-motion.scss — Emphasized decelerate/accelerate cubic-beziers and the 50-1000 ms duration scale.
[12] GSAP docs — SplitText (GreenSock animation platform documentation) — https://gsap.com/docs/v3/Plugins/SplitText/ — Split types, mask option, aria, onSplit; example staggers 0.05/0.15/0.25 s.
[17] Joey Korenman — Kinetic typography in After Effects, part 1 (School of Motion) (Founder of School of Motion) — https://schoolofmotion.com/blog/kinetic-typography-after-effects-part-1 — Sync markers, ghost copies 50% two frames early, nudge 2-3 frames earlier, lingering ease-out.
[18] Nol Honig — How to stretch and smear text (School of Motion) (Motion designer and School of Motion instructor) — https://schoolofmotion.com/blog/stretch-and-smear-text-tutorial — Smear peaks at the fastest frame, ~90% eases, cut on the fastest frame, 2-frame overlaps.
[29] Art of the Title — Stranger Things (Imaginary Forces; Michelle Dougherty) (Emmy-winning main title; interview with creative director Michelle Dougherty) — https://www.artofthetitle.com/title/stranger-things/ — Typeface as actor, rejected snapping lock-in, fluid jitter-free drift, film grain, ~45 s sweet spot.
[30] Art of the Title — Severance (Oliver Latta, Teddy Blanks) (Emmy-winning main title; typography by Teddy Blanks) — https://www.artofthetitle.com/title/severance/ — Left-aligned sans with a thin rule above; type subordinate to the image.
[33] @jakeinmotion (Jake Bartlett) (Motion designer and kinetic-type instructor (Skillshare), maker of the AE tools Type Jazz and Railcut) — https://x.com/jakeinmotion/status/2104022458865218019 — AI motion fails with 60 fps, flat fast pacing and repeated easing.
