# Name lower third

A speaker's name and role (or social handle) that appears the first time a person is on camera, holds long enough
to read twice, and leaves. Interviews, podcasts, talking-head explainers, event recaps. 16:9, 9:16 and 1:1; 4–7 s
per appearance.

## How the pros do it
- Show it the first time a person is introduced, then not again; documentaries often use a single plate at the
  subject's introduction [16]. Live and podcast shows put it up in sync with the guest's first words — on live
  formats viewers decide in 1–2 seconds, so context on the lower third matters [35].
- Hold it long enough to read every word twice [14][13]; 3–6 s is the working range [13][15]. Use the hold formula in
  `title-craft-basics.md` (`2 × max(words × 0.36, chars/20)`, clamped 3–7 s) [6][4][5].
- Two lines only: name (heavier, larger) over role or handle (lighter, 60–70% size). Keep it to 2–4 lines in any
  case and never fill the whole bottom of the frame like a news bar [16].
- One sans family, white or black depending on the footage; use the brand face if one exists and keep it identical
  across the whole video [14][16].
- Put a plate (rectangle) behind the type when the background is busy; cardless type only over calm footage [14].
  Dark plate opacity ≥ 0.6 keeps white text above 4.5:1 on any background (WCAG math) [9].
- Place it on the side opposite the subject's look direction, never over the mouth; in extreme close-ups shrink it
  or drop the plate [14]. If the bottom of the frame is busy, move it up — it does not have to sit in the lower third [15][14].
- Keep it inside graphics-safe: 5% from each edge at 16:9 (EBU R95) [1]; in 9:16 clear 14% top, 35% bottom and
  the right-hand button rail [3]. Design horizontals so they survive a crop to vertical [34].
- Animate in and out cleanly; a plain fade is often the best choice [13]. Animation must not pull focus from the
  speaker [16][14]. Exits run about 35% faster than entrances (Material accelerate vs decelerate) [10].
- Build for long names and special characters: the plate width must follow the text, not a fixed box [13].
- Handles and names in caps get +0.05–0.12em tracking; sentence case gets none [7].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `name-lower-third.clean` | Cardless name + role, thin accent rule draws under the name | Inter 700 / 400, name 54 px, role 34 px, rule 2 px × 0→120% name width in 0.4 s, text shadow, in 0.45 s / out 0.28 s |
| `name-lower-third.boxed` | Two stacked bars: dark name bar wipes from left, accent role bar follows | Inter 700 / 600, name 54 px, role 34 px, plate #0E0F12 α 0.85, role bar accent #FFD23F, padding 18/28 px, bar wipe 0.45 s `cubic-bezier(0.05,0.7,0.1,1)`, text +0.1 s |
| `name-lower-third.editorial` | Serif name, small caps role with tracking, hairline above | Instrument Serif 400 60 px, Inter 600 caps 22 px +0.1em, 1 px rule α 0.7, line mask rise 0.6 s stagger 0.12 s |
| `name-lower-third.handle` | Avatar dot + name + @handle pill for creators | pill radius 999 px, white α 0.92, #111 text, handle IBM Plex Mono 30 px, scale-pop 0.9→1 in 0.35 s with 0 overshoot |

## Timing and numbers
- Timeline at 30 fps for a 5-word name + role (≈30 chars): plate in 0–0.45 s (0–14 f); name 0.10–0.55 s; role
  0.20–0.65 s; hold to 4.25 s (3.6 s read time); exit 4.25–4.53 s (8 f) — all elements together, accelerate ease.
- Easing: in `cubic-bezier(0.05, 0.7, 0.1, 1)` (GSAP `expo.out`), out `cubic-bezier(0.3, 0, 0.8, 0.15)` (GSAP `power2.in`) [10].
- 16:9 1920×1080: left x = 144 px; block bottom y = 940–950 px (87–88% H); name 54 px (5% H), role 34 px (3.1% H);
  max width 40% W (768 px). 9:16 1080×1920: left x = 72 px, block bottom y = 1180–1230 px (61–64% H), name 66 px,
  role 42 px, max width 778 px (keeps clear of the right rail) [3]. 1:1 1080×1080: left 64 px, bottom 930 px, name 52 px.
- Tracking: name 0 to −0.01em; role sentence case 0; caps role or kicker +0.08em [7].
- Plate: dark #0E0F12 at α 0.75–0.85 (≥ 0.6 minimum) or light #FFFFFF at α 0.9 with #111 text [9]; corner radius 0 for
  news-style, 8–12 px for creator style; padding = 0.5× name size vertical, 0.6× horizontal.
- Accent: one color only, ≤ 10% of the plate area (a tab, rule or role bar).

## Build it
- Start from HyperFrames blocks `lt-clean-bar` (white card, clip-wipe), `lt-dark-card` (charcoal, drawn underline),
  `lt-stack-bars` (two wiping bars), `lt-accent-underline` / `lt-side-rule` / `lt-kicker-name` (cardless) and
  `yt-lower-third` (avatar + handle). `npx hyperframes add lt-stack-bars`.
- GSAP: one paused timeline. `tl.fromTo(plate, {clipPath:'inset(0 100% 0 0)'}, {clipPath:'inset(0 0% 0 0)', duration:.45, ease:'expo.out'}, 0)`;
  name and role `fromTo({yPercent:100, opacity:0},{yPercent:0, opacity:1, duration:.4, ease:'expo.out'})` at 0.10 and 0.20,
  inside an `overflow:hidden` line mask; exit all at `hold_end` with `duration:.28, ease:'power2.in'`.
- Compute hold from the text: `hold = clamp(2*max(words*0.36, chars/20), 3, 7)`.
- Remotion: `const p = interpolate(frame, [0, 14], [0, 1], {easing: Easing.bezier(0.05,0.7,0.1,1), extrapolateRight:'clamp'})`;
  measure the text with a hidden span (or `measureText`) so the plate width follows the name.
- Over real footage via ffmpeg: render the plate as ProRes 4444 / PNG sequence with alpha (as broadcast teams do [13]) and
  `overlay=enable='between(t,1.0,5.6)'`.

## Mistakes that look amateur
- Random fonts or colors not tied to the project → one family, one accent, consistent across every plate [14].
- Plate covering the mouth or hugging the frame edge → mirror to the open side, keep 5% safe margin [14][1].
- Up for 1.5 s → hold for two full reads, 3 s minimum [14][13].
- Bouncy overshoot and spinning letters → straight decelerate in, faster accelerate out [16][10].
- Same plate up every time the person speaks → only the first appearance (or after a long absence) [16].
- Fixed-width box that clips long names → width follows text, test with a 28-character name [13].
- Semi-transparent plate at 40% on bright footage → α ≥ 0.6 or switch to a light plate [9].

## Sources
[1] EBU R 095 — Safe areas for 16:9 television production (European Broadcasting Union technical recommendation) — https://tech.ebu.ch/publications/r095 — Action-safe 3.5% and graphics-safe 5% per edge.
[3] HopperHQ — Instagram Reel size: dimensions, aspect ratio and safe zones (Social scheduling company blog relaying Meta's percentage safe zones) — https://www.hopperhq.com/blog/instagram-reel-size/ — 9:16 safe zones: 14% top, 35% bottom, 6% sides, bottom-right 40% rail.
[4] Netflix — English (USA) Timed Text Style Guide (Netflix Partner Help, subtitle delivery spec) — https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-USA-Timed-Text-Style-Guide — 20 chars/s adult reading speed, 42 characters per line, 2 lines max.
[5] Netflix — Timed Text Style Guide: General Requirements (Netflix Partner Help) — https://partnerhelp.netflixstudios.com/hc/en-us/articles/215758617 — Minimum 5/6 s and maximum 7 s per text event.
[6] Clevercast — BBC Subtitling Guidelines (summary) (Video platform company summarizing the BBC subtitle guidelines) — https://clevercast.com/bbc-subtitling-guidelines — 160-180 wpm = 0.33-0.375 s per word; line max 68% of a 16:9 frame.
[7] Matthew Butterick — Practical Typography: Letterspacing (Typographer and author of Practical Typography) — https://practicaltypography.com/letterspacing.html — Caps +5-12% letterspacing (0.05-0.12em); no letterspacing on lowercase.
[9] W3C — Understanding WCAG 2.1 SC 1.4.3 Contrast (Minimum) (W3C Web Accessibility Initiative) — https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html — 4.5:1 / 3:1 contrast and the luminance formula used to derive plate opacity minimums.
[10] Material Design 3 motion tokens (material-web) (Google Material Design system source tokens) — https://github.com/material-components/material-web/blob/main/tokens/versions/v0_192/_md-sys-motion.scss — Emphasized decelerate/accelerate cubic-beziers and the 50-1000 ms duration scale.
[13] Chris Salters — Sports lower thirds (School of Motion) (Motion designer writing for School of Motion) — https://schoolofmotion.com/blog/sports-lower-thirds — 3-6 s on screen, read twice, define purpose (identify vs context), flexible widths, ProRes 4444 alpha.
[14] Jason Boone — How to make lower third titles that don't suck (Frame.io Insider) (Editor and doc filmmaker (National Geographic, Current TV), Premiere/AE educator) — https://blog.frame.io/2017/12/04/create-lower-thirds-titles-that-dont-suck/ — Read every word twice, plates for separation, avoid mouth/edges, consistency, simple animation.
[15] Alec Chillingworth — How to get the best lower thirds (Epidemic Sound) (Epidemic Sound blog writer) — https://www.epidemicsound.com/blog/lower-thirds/ — 3-6 s, read 2-2.5 times, move it up when the bottom is busy, avoid the eyeline.
[16] Mackenzie Scott — A documentarian's guide to lower thirds (Soundstripe) (Soundstripe blog, documentary production) — https://www.soundstripe.com/blogs/a-documentarians-guide-to-lower-thirds — Compact 2-4 lines, don't fill the bottom like news, discreet animation, legible size.
[34] @YouTubeInsider (YouTube Creator Insider) (Official YouTube team account for creators) — https://x.com/YouTubeInsider/status/1560995909089067010 — Place lower thirds so they survive editing a horizontal video into a Short.
[35] @sallyshin (Sally Shin) (CNBC EVP Growth & Partnerships, former network news executive) — https://x.com/sallyshin/status/2046419371396833446 — 1-2 s to capture a viewer; lower-third context synced to guest commentary is an editorial skill.
