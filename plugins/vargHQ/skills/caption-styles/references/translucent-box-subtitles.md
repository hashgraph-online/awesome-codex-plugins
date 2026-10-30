# Translucent box subtitles

Plain white sentence-case text on a semi-transparent dark box, one phrase or sentence at a time, cut on and cut off with no motion. The accessible default for interviews, documentaries, courses and podcasts in 16:9, 9:16 and 1:1; runs for the whole video, each caption 0.8-7 s.

Fonts: Inter (OFL-1.1), Atkinson Hyperlegible (OFL-1.1). Formats: 16:9, 9:16, 1:1.

## How the pros do it
- Show a phrase, not words: 1-2 lines in 16:9 and 1:1, up to 3 lines in 9:16; at most 42 characters per line in 16:9 [1][4].
- Time to reading speed: 160-180 wpm, about 0.33-0.375 s per word, never above 20 characters per second for adults or 17 for children [1][4].
- Each caption stays on screen 0.83 s (20 frames at 24 fps) to 7 s; DCMP is stricter at 40 frames to 6 s [2][3][6].
- In-time on the first frame of audio or within 1-2 frames; leave at least 2 frames between captions and close any gap under 0.5 s; hold the last caption about 0.5 s past the audio [3].
- Draw the box per line, not as one rectangle: each line gets its own background with 0.5 em padding on both sides and no gap between stacked lines [4].
- Break lines after punctuation and before conjunctions or prepositions; never split article+noun, name+surname, pronoun+verb or auxiliary+verb; prefer a bottom-heavy pyramid [1][4][6].
- Keep one style for the whole video and put each caption up at about the same time as its audio [7].
- Use a medium-weight sans serif, white, mixed case; caps only for shouting [6]. One colour for all text works best for people who rely on captions [28].
- Pop on, pop off. No scroll, slide or bounce: motion lowers readability for caption-dependent viewers [6][28].
- Bottom-centre by default; move up when the box would cover a mouth, a name super or on-screen text [2][4][6]. In 9:16 sit a little higher, still in the lower third, because faces live in the top half [4].
- Size by line height: 7-8% of frame height in 16:9 and 1:1, 3.9-4.5% in 9:16 (font about 3.5% of height) [4].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `translucent-box-subtitles.broadcast-16x9` | Inter 600 white on 75% black per-line box, bottom centre | font 67 px (6.25% H), line-height 1.2, box rgba(0,0,0,.75), pad 0 .5em, radius 0, max line 68% W (1306 px), 42 cpl, 2 lines, bottom 8% H [1][3][4][8] |
| `translucent-box-subtitles.vertical-9x16` | Same box, larger lines, sits at ~60% height inside the platform safe box | font 67-76 px (3.5-4% H), line-height 1.2, box rgba(0,0,0,.72), max width 696 px (64% W), ~20-25 cpl, 3 lines, block centre y 60% H [4][10][11] |
| `translucent-box-subtitles.soft-offblack` | Off-white on off-black, slightly rounded, for long podcasts | text #FFFFF0, box #242424 at 85%, radius 8 px, Atkinson Hyperlegible 700, 2 lines, ~60 chars per caption [28][8] |

## Timing and numbers
- Contrast: white on a pure-black box at 60% opacity stays at 5.7:1 even over a white background; at 50% it drops to 4.0:1 and fails 4.5:1. Keep opacity >= 0.6 (computed with the WCAG formula) [8].
- Optional softening: a 2-frame (67 ms) opacity fade is the most motion to add; anything longer reads as an animation [6][28].
- Shot changes: end a caption 2 frames before a cut, or extend it to the cut if it would end within 0.5 s of it [3].
- Shared baseline for every caption look:
  - Frame maths at 30 fps: 1 frame = 33 ms; 4 f = 133 ms; 6 f = 200 ms; 8 f = 267 ms; 12 f = 400 ms.
  - Reading baseline: 160-180 wpm = 0.33-0.375 s per word; adult ceiling 20 characters/s [1][4]. At 180 wpm a word lasts ~10 frames, so any per-word animation must finish inside ~6 frames.
  - Sync: change the active word 1-2 frames before its audio onset. Picture-early is undetectable up to ~125 ms, picture-late is detectable from ~45 ms (ITU-R BT.1359) [15]. Caption blocks go up on the first audio frame or within 1-2 frames [3].
  - 9:16 safe box (1080x1920), worst case of the platforms' ad specs: top 288 px (15%), bottom 672 px (35%), left 120 px, right 192 px; keep the caption block inside x 120-888, y 288-1248. Centred captions: max width 696 px (64% W) so both edges clear 192 px [10][11][13]. TikTok sizes its zone by ratio and ad-caption length, so treat these as minimums [12]. Organic-only posts can go lower: nothing important in the bottom 20% or right 15% [39].
  - 16:9: keep captions inside the central 90% vertically and 75% horizontally; a line is at most 68% of the width [4].
  - Contrast: >= 4.5:1 for text and its immediate background; 3:1 is the floor only for large text [8].
  - Final check: watch a render on a phone at arm's length; if you have to focus to read, go bigger. Keep >= 60 px from the frame edges [44].

## Build it
1. Get word timestamps (WhisperX or ElevenLabs Speech to Text), then group words into sentences/phrases by punctuation and pauses; target 0.33 s per word and split phrases longer than 2 lines.
2. Render each caption as a <p> with one <span> per line; style the span with `background`, `padding: 0 .5em`, `box-decoration-break: clone` so wrapped lines each get a box [4][21].
3. Insert line breaks yourself by the linguistic rules; do not trust auto-wrap [4].
4. Drive visibility from timeline time only (GSAP `tl.set(el,{autoAlpha:1}, start)` / `tl.set(el,{autoAlpha:0}, end)`), or in Remotion `<Sequence from={start} durationInFrames={dur}>`.
5. ffmpeg path for burn-in: write SRT/ASS and use `subtitles=captions.ass` with Style `BorderStyle=3` (opaque box), `BackColour=&H40000000` (about 75% black), `Outline=0`, `Fontname=Inter`, `Fontsize` in script pixels.

## Mistakes that look amateur
- Grey box at 40-50% over bright footage → contrast falls under 4:1; use black at >= 60% [8].
- One big rectangle behind two lines of different length → per-line boxes with 0.5 em padding [4].
- Auto-wrapped orphan word on line 1 → manual bottom-heavy breaks [1].
- Captions flashing for 8-10 frames on fast speech → merge until each caption is >= 0.83 s [2].
- Captions over the platform's caption/CTA area in 9:16 → keep the block above 1248 px on a 1920 px frame [11].
- Captions lingering 2-3 s after the speaker stops → end about 0.5 s after the audio [3].

## Sources
[1] Netflix (Netflix partner help (style guide owner)) — English (USA) Timed Text Style Guide — https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-USA-Timed-Text-Style-Guide — 42 characters per line, max 2 lines, 20 cps adults / 17 cps children, line-break rules, italics rules
[2] Netflix (Netflix partner help) — Timed Text Style Guide: General Requirements — https://partnerhelp.netflixstudios.com/hc/en-us/articles/215758617-Timed-Text-Style-Guide-General-Requirements — min 5/6 s and max 7 s per event, centred, top or bottom, move off on-screen text, % not px
[3] Netflix (Netflix partner help) — Timed Text Style Guide: Subtitle Timing Guidelines — https://partnerhelp.netflixstudios.com/hc/en-us/articles/360051554394-Timed-Text-Style-Guide-Subtitle-Timing-Guidelines — in-time on the first audio frame or within 1-2 frames, 2-frame minimum gap, close gaps under 0.5 s, out-time 0.5 s after audio, shot-change rules
[4] BBC (BBC accessibility team (UK public broadcaster)) — BBC Subtitle Guidelines — https://www.bbc.co.uk/accessibility/forproducts/guides/subtitles/ — 160-180 wpm (0.33-0.375 s/word), line height 7-8% of height (16:9) and 3.9-4.5% (9:16), font ~3.5% of height for 9:16, 68%/90% line width, 2 lines (3 for 9:16), per-line background with 0.5 em padding, white/yellow/cyan/green on black, 9:16 captions a little higher in the lower third, sync and lag limits, lyrics rules
[6] DCMP (Described and Captioned Media Program) — Captioning Key: Text — https://dcmp.org/learn/597-captioning-key---text — medium-weight sans serif with drop or rim shadow, white, mixed case (caps only for shouting), translucent box, 2 lines, line division rules, move captions off faces and graphics, min 40 frames / max 6 s
[7] DCMP (Described and Captioned Media Program) — Captioning Key: Elements of Quality Captioning — https://dcmp.org/learn/599-captioning-key---elements-of-quality-captioning — captions appear at about the same time as the audio, error-free, consistent style
[8] W3C WAI (World Wide Web Consortium accessibility standard) — Understanding WCAG 2.2 SC 1.4.3 Contrast (Minimum) — https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html — 4.5:1 normal text, 3:1 large text (18 pt / 14 pt bold); ratios are not rounded. We used its formula to compute every colour pair in the presets
[10] Meta (Meta Ads Guide (platform spec)) — Instagram Reels video ad specs — https://www.facebook.com/business/ads-guide/update/video/instagram-reels — keep 14% top, 35% bottom and 6% each side free of text
[11] Socialync (safe-zone tool that compiles the platforms' published ad margins) — Social media safe zones — https://www.socialync.io/tools/safe-zones — 1080x1920 margins: TikTok 240/660/120/120, Reels 269/672/65/65, Shorts 288/672/48/192 (top/bottom/left/right), all ad specs
[12] TikTok (TikTok Ads help (platform spec)) — TikTok Auction In-Feed Ads — https://ads.tiktok.com/help/article/tiktok-auction-in-feed-ads?lang=en — safe zone depends on ratio, ad caption length and extra formats; published as downloadable files
[13] Google (Google Ads help (platform spec)) — Safe zones for vertical video ads on YouTube — https://support.google.com/google-ads/answer/9128498?hl=en — 1080x1920 safe-zone image with pixel margins (values read via [11])
[15] Randy Hoffner / ITU-R BT.1359 (broadcast engineering columnist, TV Technology) — AV synchronization: how bad is bad? — https://www.tvtechnology.com/opinions/av-synchronization-how-bad-is-bad — ITU-R BT.1359 detectability about +45 ms (sound early) to -125 ms (sound late); people tolerate picture-before-sound far more than sound-before-picture
[21] MDN (Mozilla web docs) — box-decoration-break — https://developer.mozilla.org/en-US/docs/Web/CSS/box-decoration-break — clone gives every wrapped line its own padding, radius, shadow and background
[28] Meryl K. Evans (deaf accessibility advocate and CPACC, writes caption guides) — Why captioned videos are important — https://meryl.net/why-captioned-videos-are-important/ — one colour, no word highlighting, no 1-2 word captions, 1-2 lines (~60 chars), off-black #242424 box with off-white text, bottom placement, sentence case, minimal motion
[39] @wayofzorro (Zorro) (Shorts channel operator; checklist post had 6.4k likes, 8.6k bookmarks) — Shorts production checklist — https://x.com/wayofzorro/status/2105523352261542050 — large word-by-word captions inside the safe zone; nothing important in the bottom 20% or right 15%; captions perfectly synced; lock fonts and layout in a master project
[44] Derek Coleman (OpusClip) (senior growth marketer at a short-form clipping company) — Video caption design and placement — https://www.opus.pro/blog/video-caption-design-placement — middle 80% of width, at least 60 px from edges, accent backgrounds at 70-80% opacity, 2-frame gaps, test on a phone at arm's length

_TikTok, YouTube, Instagram and Meta are named only to describe their published safe zones; their names, logos and interfaces are trademarks of their owners. Fonts are OFL-1.1 (free for commercial video, no attribution needed) [27]._
