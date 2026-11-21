# Tilted card word pops

One uppercase word at a time springs in on a slightly rotated sticker-like card, alternating white and lime. Hooks, ad openers, meme edits and music-beat promos in 9:16; one word per beat, 5-20 s.

Fonts: Anton (OFL-1.1), Archivo Black (OFL-1.1), Bebas Neue (OFL-1.1). Formats: 9:16, 1:1.

## How the pros do it
- Single-word display pins the eye on the text and costs comprehension; keep it to hooks and short clips [14][30].
- Use a condensed caps face so long words still fit one card; condensed display caps are a short-form staple [37][38].
- Card contrast: #0A0A0A on white is 19.8:1, on lime #C6FF3D 16.8:1 [8].
- Spring in with GSAP back.out (default overshoot 1.70158) over 7-9 frames [19].
- Code-built short-form recipes use a tilted sticker carrying a big condensed title as an overlay; reuse that idea per word [41].
- Fire each card at onset minus 2 frames so the overshoot peaks on the word [15].
- Merge words shorter than 8 frames into one card [4].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `tilted-card-word-pop.white-lime-alt` | Anton caps on cards tilted -4° / +3°, colours alternate every word | Anton 140 px (7.3% H), card pad .08em .3em radius .12em, rotate cycle [-4°,+3°,-2°,+4°], colours [#FFFFFF,#C6FF3D], scale .6→1 back.out(1.7) 8 f, centre y 55% H [8][15][19] |
| `tilted-card-word-pop.sticker-shadow` | Adds a hard offset shadow and a thin black border | box-shadow 8px 8px 0 #0A0A0A, border 4 px #0A0A0A  |
| `tilted-card-word-pop.calm-tilt` | Less bounce for brand-safe ads | scale .9→1 power3.out 6 f, rotation ±2° [19] |

## Timing and numbers
- Rotation is a fixed per-card value from a short cycle, not random per render, so re-renders are identical (seek-safe).
- Card colour alternates every word or every phrase, never randomly; change on sentence boundaries if the clip is longer than 10 s.
- Overshoot peak lands ~4 frames after start; with a 2-frame lead it peaks about 2 frames after the onset [15][19].
- Shared baseline for every caption look:
  - Frame maths at 30 fps: 1 frame = 33 ms; 4 f = 133 ms; 6 f = 200 ms; 8 f = 267 ms; 12 f = 400 ms.
  - Reading baseline: 160-180 wpm = 0.33-0.375 s per word; adult ceiling 20 characters/s [1][4]. At 180 wpm a word lasts ~10 frames, so any per-word animation must finish inside ~6 frames.
  - Sync: change the active word 1-2 frames before its audio onset. Picture-early is undetectable up to ~125 ms, picture-late is detectable from ~45 ms (ITU-R BT.1359) [15]. Caption blocks go up on the first audio frame or within 1-2 frames [3].
  - 9:16 safe box (1080x1920), worst case of the platforms' ad specs: top 288 px (15%), bottom 672 px (35%), left 120 px, right 192 px; keep the caption block inside x 120-888, y 288-1248. Centred captions: max width 696 px (64% W) so both edges clear 192 px [10][11][13]. TikTok sizes its zone by ratio and ad-caption length, so treat these as minimums [12]. Organic-only posts can go lower: nothing important in the bottom 20% or right 15% [39].
  - 16:9: keep captions inside the central 90% vertically and 75% horizontally; a line is at most 68% of the width [4].
  - Contrast: >= 4.5:1 for text and its immediate background; 3:1 is the floor only for large text [8].
  - Final check: watch a render on a phone at arm's length; if you have to focus to read, go bigger. Keep >= 60 px from the frame edges [44].

## Build it
1. One absolutely centred card element; on each token: set text, set colour/rotation from the cycle, `tl.fromTo(card,{scale:.6},{scale:1,duration:8/30,ease:'back.out(1.7)'}, start-2/30)` [19].
2. Auto-fit: if text width > 760 px at 140 px, scale font down to fit (min 96 px) before animation, measured once per word.
3. Pair with a 1-frame camera punch-in (scale 1.02) on the footage for hits; never on every word.

## Mistakes that look amateur
- Random rotation per frame or per render → jitter and non-reproducible renders.
- Lime card with white text → 1.2:1, unreadable; dark text only [8].
- Using one-word cards for prices, names or steps → show a 2-3-word chunk instead [14].
- Back.out overshoot of 3+ → rubbery; 1.7 is enough [19].

## Sources
[1] Netflix (Netflix partner help (style guide owner)) — English (USA) Timed Text Style Guide — https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-USA-Timed-Text-Style-Guide — 42 characters per line, max 2 lines, 20 cps adults / 17 cps children, line-break rules, italics rules
[3] Netflix (Netflix partner help) — Timed Text Style Guide: Subtitle Timing Guidelines — https://partnerhelp.netflixstudios.com/hc/en-us/articles/360051554394-Timed-Text-Style-Guide-Subtitle-Timing-Guidelines — in-time on the first audio frame or within 1-2 frames, 2-frame minimum gap, close gaps under 0.5 s, out-time 0.5 s after audio, shot-change rules
[4] BBC (BBC accessibility team (UK public broadcaster)) — BBC Subtitle Guidelines — https://www.bbc.co.uk/accessibility/forproducts/guides/subtitles/ — 160-180 wpm (0.33-0.375 s/word), line height 7-8% of height (16:9) and 3.9-4.5% (9:16), font ~3.5% of height for 9:16, 68%/90% line width, 2 lines (3 for 9:16), per-line background with 0.5 em padding, white/yellow/cyan/green on black, 9:16 captions a little higher in the lower third, sync and lag limits, lyrics rules
[8] W3C WAI (World Wide Web Consortium accessibility standard) — Understanding WCAG 2.2 SC 1.4.3 Contrast (Minimum) — https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html — 4.5:1 normal text, 3:1 large text (18 pt / 14 pt bold); ratios are not rounded. We used its formula to compute every colour pair in the presets
[10] Meta (Meta Ads Guide (platform spec)) — Instagram Reels video ad specs — https://www.facebook.com/business/ads-guide/update/video/instagram-reels — keep 14% top, 35% bottom and 6% each side free of text
[11] Socialync (safe-zone tool that compiles the platforms' published ad margins) — Social media safe zones — https://www.socialync.io/tools/safe-zones — 1080x1920 margins: TikTok 240/660/120/120, Reels 269/672/65/65, Shorts 288/672/48/192 (top/bottom/left/right), all ad specs
[12] TikTok (TikTok Ads help (platform spec)) — TikTok Auction In-Feed Ads — https://ads.tiktok.com/help/article/tiktok-auction-in-feed-ads?lang=en — safe zone depends on ratio, ad caption length and extra formats; published as downloadable files
[13] Google (Google Ads help (platform spec)) — Safe zones for vertical video ads on YouTube — https://support.google.com/google-ads/answer/9128498?hl=en — 1080x1920 safe-zone image with pixel margins (values read via [11])
[14] Pablo Romero-Fresco (subtitling researcher (Universidade de Vigo / Roehampton), eye-tracking studies of live subtitles) — Standing on quicksand: viewers' comprehension and reading patterns of respoken subtitles for the news (2010) — https://bibbase.org/network/publication/romerofresco-standingonquicksandviewerscomprehensionandreadingpatternsofrespokensubtitlesforthenews-2010 — word-for-word display: viewers spent ~90% of the time on the subtitles and ~10% on the image, and comprehension fell
[15] Randy Hoffner / ITU-R BT.1359 (broadcast engineering columnist, TV Technology) — AV synchronization: how bad is bad? — https://www.tvtechnology.com/opinions/av-synchronization-how-bad-is-bad — ITU-R BT.1359 detectability about +45 ms (sound early) to -125 ms (sound late); people tolerate picture-before-sound far more than sound-before-picture
[19] GreenSock (GSAP) (GSAP docs and source) — Eases docs + gsap-core.js 3.12.5 — https://gsap.com/docs/v3/Eases/ — default ease power1.out; back overshoot default 1.70158; elastic.out default amplitude 1, period 0.3 (source: https://unpkg.com/gsap@3.12.5/src/gsap-core.js)
[30] @merylkevans (Meryl Evans) (deaf accessibility advocate) — Reply: single-word captions — https://x.com/merylkevans/status/1643731008229875713 — single-word captions are too fast for most viewers
[37] @mws (Muaaz) (YouTube/short-form creator; font list post had 1,252 likes and 1,602 bookmarks) — Best fonts for subtitles on TikTok/Shorts/Reels — https://x.com/mws/status/1872411175826403825 — heavy geometric sans (Montserrat Black), condensed display (Bebas Neue) and rounded comic faces dominate short-form captions
[38] @yt_igm (igorm) (YouTube Shorts creator; post had 1,949 likes and 2,220 bookmarks) — Best YouTube Shorts subtitle fonts — https://x.com/yt_igm/status/2031339804680478802 — Montserrat, Kanit, Bebas Neue among the common Shorts caption faces
[39] @wayofzorro (Zorro) (Shorts channel operator; checklist post had 6.4k likes, 8.6k bookmarks) — Shorts production checklist — https://x.com/wayofzorro/status/2105523352261542050 — large word-by-word captions inside the safe zone; nothing important in the bottom 20% or right 15%; captions perfectly synced; lock fonts and layout in a master project
[41] @finnardley (Finn) (AI video creator publishing code-built shorts recipes) — Stickman thriller recipe — https://x.com/finnardley/status/2115786060231770351 — chunky captions of 1-3 words with key words in an accent colour; snap each word to its real audio start and check voice is under every caption within ~120 ms
[44] Derek Coleman (OpusClip) (senior growth marketer at a short-form clipping company) — Video caption design and placement — https://www.opus.pro/blog/video-caption-design-placement — middle 80% of width, at least 60 px from edges, accent backgrounds at 70-80% opacity, 2-frame gaps, test on a phone at arm's length

_TikTok, YouTube, Instagram and Meta are named only to describe their published safe zones; their names, logos and interfaces are trademarks of their owners. Fonts are OFL-1.1 (free for commercial video, no attribution needed) [27]._
