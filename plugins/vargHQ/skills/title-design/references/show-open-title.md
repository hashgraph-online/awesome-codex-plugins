# Show open title

A show's opening title for a podcast or recurring video series: the show name cuts in word by word on the beat, a
side panel slides in and types the guest(s) onto plates, then everything slides away into the episode. 16:9 first
(podcast video), 9:16 cut-down; 5–10 s.

## How the pros do it
- Keep the branded open short: under ~8 s for a standard YouTube intro, bumpers 2–3 s; 30 s is too long [20]. Use the
  10 s version for long episodes and the 5 s version for clips.
- Word-by-word cuts are the quick-cut tradition: Pablo Ferro cut stills and type so fast they read as motion and changed
  color on the beat of the music [31]. Hard cuts, no easing, every change on a beat.
- Put sync markers on beats and land each word on its marker; if it feels late, move it 2–3 frames earlier [17].
- The guest plate is information: it must hold for two reads (3 s minimum) even inside a fast open [14][13].
- Type the guest line at a speed faster than reading (≥ 20 chars/s [4]) so the typing never makes the viewer wait.
- Viewers decide within 1–2 seconds — the show name must be readable by the second beat [35].
- Long main titles can run ~45 s on TV, but that is a series-opening luxury; web shows earn attention first [29][20].
- Keep everything in graphics-safe (5% per edge) and design the 16:9 so a vertical cut still holds the name [1][34].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `show-open-title.standard-10s` | Name on beats → panel with typed guest plates → slide away | 120 BPM; 1 word / beat (15 f); panel in 0.45 s; type 30 chars/s; plate hold 4.2 s; panel out 0.3 s |
| `show-open-title.cold-5s` | Clip version: name in 4 beats, single guest plate, quick exit | 128 BPM (14 f beats); plate hold 3.0 s; total 5 s |
| `show-open-title.vertical` | 9:16 cut-down: name stacked one word per line, plate under it | name 11% W, stacked; plate at 58–62% H; ends before 7 s |

## Timing and numbers
- Standard 10 s at 30 fps, 120 BPM (beat = 0.5 s = 15 f):
  - 0.0–2.5 s: show name, one word per beat on frames 0, 15, 30, 45 (hard cut in; optional 1.03→1 scale settle over 4 f);
    on the 5th beat the name locks into its final layout (0.3 s `cubic-bezier(0.2,0,0,1)`) [10].
  - 3.0–3.45 s: panel slides in from the right (x 100%→0), `cubic-bezier(0.05,0.7,0.1,1)` [10].
  - 3.5–4.5 s: guest plates type on at 30 chars/s (1 char per frame), caret blinks 0.5 s on / 0.5 s off via `steps(1)` [11].
  - 4.5–8.7 s: hold (two guests × "Name — Role" ≈ 6 words each → 4.3 s) [6].
  - 8.7–9.0 s: panel exits right, `cubic-bezier(0.3,0,0.8,0.15)`, 9 f [10]; 9.0–10.0 s name scales to a corner bug or cuts out on the downbeat.
- Sizes 16:9: show name 12–14% H (Anton or Archivo Black, caps +0.02em); panel 34% W wide, right-aligned at 5% safe;
  plate names 44 px Inter 700, roles 28 px Inter 400 α 0.75; plate gap 16 px.
- Palette: name #F5F1E8 on #0B0B0C; panel #16161A α 0.92; accent #FF5A1F (one hue).
- 9:16: stack the name one word per line at 11% W, plates between 52% and 64% H, clear of the right rail [3].

## Build it
- HyperFrames: name — `kinetic-type` / `text-stagger`; panel — `panel-reveal` or `lt-stack-bars`; typing — `typewriter`
  (deterministic caret); stagger groups — `stagger-cascade`. Each part in its own sub-composition; beat times from the
  music (detect beats once, store as data, place words at those times).
- GSAP: words as separate spans, `tl.set(word, {autoAlpha: 1}, beatTime[i])` (a cut is a `set`, not a tween); typing via
  a tween on `{n: 0}` → `onUpdate` writes `text.slice(0, Math.round(n))`, `duration = chars / 30`, `ease: 'none'`.
- Remotion: `const shown = Math.min(text.length, Math.max(0, frame - startFrame))` gives 1 char per frame at 30 fps.
- Audio: one hit per word, a soft key click per 2–3 characters (not every one), a whoosh on the panel exit.

## Mistakes that look amateur
- Words that fade in on soft eases → hard cuts on beats [31].
- Words off the beat by 3–4 frames → snap to markers, nudge 2–3 frames early [17].
- Guest plate gone after 1.5 s → hold ≥ 3 s / two reads [14].
- Typing at 8 chars/s with a click on every letter → ≥ 30 chars/s, sparse clicks [4].
- A 20–30 s open on a web show → ≤ 10 s, 5 s for clips [20].
- Name too small to read by the second beat → 12–14% H display size [35].

## Sources
[1] EBU R 095 — Safe areas for 16:9 television production (European Broadcasting Union technical recommendation) — https://tech.ebu.ch/publications/r095 — Action-safe 3.5% and graphics-safe 5% per edge.
[3] HopperHQ — Instagram Reel size: dimensions, aspect ratio and safe zones (Social scheduling company blog relaying Meta's percentage safe zones) — https://www.hopperhq.com/blog/instagram-reel-size/ — 9:16 safe zones: 14% top, 35% bottom, 6% sides, bottom-right 40% rail.
[4] Netflix — English (USA) Timed Text Style Guide (Netflix Partner Help, subtitle delivery spec) — https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-USA-Timed-Text-Style-Guide — 20 chars/s adult reading speed, 42 characters per line, 2 lines max.
[6] Clevercast — BBC Subtitling Guidelines (summary) (Video platform company summarizing the BBC subtitle guidelines) — https://clevercast.com/bbc-subtitling-guidelines — 160-180 wpm = 0.33-0.375 s per word; line max 68% of a 16:9 frame.
[10] Material Design 3 motion tokens (material-web) (Google Material Design system source tokens) — https://github.com/material-components/material-web/blob/main/tokens/versions/v0_192/_md-sys-motion.scss — Emphasized decelerate/accelerate cubic-beziers and the 50-1000 ms duration scale.
[11] GSAP docs — SteppedEase (GreenSock animation platform documentation) — https://gsap.com/docs/v3/Eases/SteppedEase — steps(n) ease syntax for ticking properties.
[13] Chris Salters — Sports lower thirds (School of Motion) (Motion designer writing for School of Motion) — https://schoolofmotion.com/blog/sports-lower-thirds — 3-6 s on screen, read twice, define purpose (identify vs context), flexible widths, ProRes 4444 alpha.
[14] Jason Boone — How to make lower third titles that don't suck (Frame.io Insider) (Editor and doc filmmaker (National Geographic, Current TV), Premiere/AE educator) — https://blog.frame.io/2017/12/04/create-lower-thirds-titles-that-dont-suck/ — Read every word twice, plates for separation, avoid mouth/edges, consistency, simple animation.
[17] Joey Korenman — Kinetic typography in After Effects, part 1 (School of Motion) (Founder of School of Motion) — https://schoolofmotion.com/blog/kinetic-typography-after-effects-part-1 — Sync markers, ghost copies 50% two frames early, nudge 2-3 frames earlier, lingering ease-out.
[20] Hadiyah Woods — How long should a YouTube intro be? (Marmoset) (Marmoset music licensing journal) — https://www.marmosetmusic.com/journal/how-long-should-a-youtube-intro-be/ — Intro under 8 s (5-15 s range), bumper 2-3 s, 30 s too long.
[29] Art of the Title — Stranger Things (Imaginary Forces; Michelle Dougherty) (Emmy-winning main title; interview with creative director Michelle Dougherty) — https://www.artofthetitle.com/title/stranger-things/ — Typeface as actor, rejected snapping lock-in, fluid jitter-free drift, film grain, ~45 s sweet spot.
[31] Art of the Title — Pablo Ferro: a career retrospective, part 1 (Retrospective of the title designer of Dr. Strangelove and The Thomas Crown Affair) — http://www.artofthetitle.com/feature/pablo-ferro-a-career-retrospective-part-1/ — Quick-cut technique; color and image changes on the beat of the music.
[34] @YouTubeInsider (YouTube Creator Insider) (Official YouTube team account for creators) — https://x.com/YouTubeInsider/status/1560995909089067010 — Place lower thirds so they survive editing a horizontal video into a Short.
[35] @sallyshin (Sally Shin) (CNBC EVP Growth & Partnerships, former network news executive) — https://x.com/sallyshin/status/2046419371396833446 — 1-2 s to capture a viewer; lower-third context synced to guest commentary is an editorial skill.
