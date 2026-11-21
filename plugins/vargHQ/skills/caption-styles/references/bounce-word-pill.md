# Bouncing single-word pill

One uppercase word at a time bounces up inside a coloured pill (purple by default) near the centre of the frame. Hooks, fast ad openers, music-driven promos and 10-20 s clips in 9:16; one word per beat.

Fonts: Montserrat (OFL-1.1), Archivo Black (OFL-1.1). Formats: 9:16, 1:1.

## How the pros do it
- One word at a time is the hardest caption to read: in word-for-word display viewers spent ~90% of their time on the text and missed the picture [14].
- Caption-dependent viewers call single-word captions too fast; use this look for hooks and short clips, not for whole talks [30][43].
- Give every word enough screen time: if a word lasts under ~8 frames, merge it with its neighbour into one pill [4].
- Caps are acceptable here because each card holds one word; caps remain the convention for stressed or shouted words [4].
- Bounce with a spring: Remotion defaults (mass 1, damping 10, stiffness 100) overshoot visibly; raise damping to calm it [17].
- Purple #6D28D9 with white text is 7.1:1; #7C3AED is 5.7:1 [8].
- Fire each pill at onset minus 1-2 frames [15].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `bounce-word-pill.purple-spring` | White caps word in a #6D28D9 pill, springs up from below | Montserrat 900 caps, 120 px (6.25% H), tracking .02em, pill #6D28D9 pad .12em .45em radius 999, y +.6em→0 spring {1,10,100} 12 f, scale .85→1, centre y 58% H [8][15][17] |
| `bounce-word-pill.lime-spring` | Black word on a lime pill | pill #C6FF3D, text #0A0A0A (16.8:1) [8] |
| `bounce-word-pill.soft-rise` | Calmer rise for brand and wellness | spring damping 200 or overshootClamping true; 8 f; y +.3em→0 [17] |

## Timing and numbers
- At 180 wpm a word lasts ~10 frames: 12-frame spring entrances overlap the next word, so start the spring 2 frames early and let the exit be a 2-frame cut/fade [4].
- GSAP equivalent of the default spring: `y` from 0.6 em with `elastic.out(1, 0.45)` over 0.4 s, or `back.out(2.2)` over 0.27 s for a single overshoot [19].
- Keep the pill centre fixed between words; only width changes (animate width 3 frames, power2.out) so the eye stays in one spot.
- Shared baseline for every caption look:
  - Frame maths at 30 fps: 1 frame = 33 ms; 4 f = 133 ms; 6 f = 200 ms; 8 f = 267 ms; 12 f = 400 ms.
  - Reading baseline: 160-180 wpm = 0.33-0.375 s per word; adult ceiling 20 characters/s [1][4]. At 180 wpm a word lasts ~10 frames, so any per-word animation must finish inside ~6 frames.
  - Sync: change the active word 1-2 frames before its audio onset. Picture-early is undetectable up to ~125 ms, picture-late is detectable from ~45 ms (ITU-R BT.1359) [15]. Caption blocks go up on the first audio frame or within 1-2 frames [3].
  - 9:16 safe box (1080x1920), worst case of the platforms' ad specs: top 288 px (15%), bottom 672 px (35%), left 120 px, right 192 px; keep the caption block inside x 120-888, y 288-1248. Centred captions: max width 696 px (64% W) so both edges clear 192 px [10][11][13]. TikTok sizes its zone by ratio and ad-caption length, so treat these as minimums [12]. Organic-only posts can go lower: nothing important in the bottom 20% or right 15% [39].
  - 16:9: keep captions inside the central 90% vertically and 75% horizontally; a line is at most 68% of the width [4].
  - Contrast: >= 4.5:1 for text and its immediate background; 3:1 is the floor only for large text [8].
  - Final check: watch a render on a phone at arm's length; if you have to focus to read, go bigger. Keep >= 60 px from the frame edges [44].

## Build it
1. Start from HyperFrames `caption-kinetic-slam` (single-word display) and replace its alternating entrances with one consistent spring [45].
2. Remotion: `const s = spring({frame: frame - start + 2, fps, config:{mass:1, damping:10, stiffness:100}, durationInFrames:12})`; `translateY = interpolate(s,[0,1],[0.6*fontSize,0])` [17].
3. Merge rule before layout: walk tokens; if `toMs - fromMs < 267` (8 frames) join with the next token into one pill.
4. Never put numbers, names or prices in one-word mode; show them as a 2-3-word chunk.

## Mistakes that look amateur
- Whole 60 s talk in one-word pills → viewers stare at the centre and miss the speaker; switch to a phrase look after the hook [14][30].
- Pills jumping to a new position each word → eye chases; fixed centre.
- Every word bouncing with a different direction or tilt → pick one motion.
- Very short words flashing for 3-4 frames → merge [4].

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
[17] Remotion (Remotion docs) — spring() — https://www.remotion.dev/docs/spring — defaults mass 1, damping 10, stiffness 100, overshootClamping false; raise damping to remove bounce; durationInFrames, delay
[19] GreenSock (GSAP) (GSAP docs and source) — Eases docs + gsap-core.js 3.12.5 — https://gsap.com/docs/v3/Eases/ — default ease power1.out; back overshoot default 1.70158; elastic.out default amplitude 1, period 0.3 (source: https://unpkg.com/gsap@3.12.5/src/gsap-core.js)
[30] @merylkevans (Meryl Evans) (deaf accessibility advocate) — Reply: single-word captions — https://x.com/merylkevans/status/1643731008229875713 — single-word captions are too fast for most viewers
[39] @wayofzorro (Zorro) (Shorts channel operator; checklist post had 6.4k likes, 8.6k bookmarks) — Shorts production checklist — https://x.com/wayofzorro/status/2105523352261542050 — large word-by-word captions inside the safe zone; nothing important in the bottom 20% or right 15%; captions perfectly synced; lock fonts and layout in a master project
[43] @cjkc_life09 (Connie Jo) (viewer who is 85% deaf, replying to a large podcast account) — Reply: captions too fast — https://x.com/cjkc_life09/status/2113417635056488558 — fast-moving short-form captions cannot be read in full by people who rely on them
[44] Derek Coleman (OpusClip) (senior growth marketer at a short-form clipping company) — Video caption design and placement — https://www.opus.pro/blog/video-caption-design-placement — middle 80% of width, at least 60 px from edges, accent backgrounds at 70-80% opacity, 2-frame gaps, test on a phone at arm's length
[45] HeyGen HyperFrames registry (open-source HTML-to-video framework) — Caption components (registry-item.json descriptions) — https://github.com/heygen-com/hyperframes/tree/main/registry/components — ready blocks: caption-highlight, caption-pill-karaoke, caption-gradient-fill, caption-neon-glow, caption-editorial-emphasis, caption-weight-shift, caption-kinetic-slam, caption-clip-wipe, per-word-rise, per-word-crossfade

_TikTok, YouTube, Instagram and Meta are named only to describe their published safe zones; their names, logos and interfaces are trademarks of their owners. Fonts are OFL-1.1 (free for commercial video, no attribution needed) [27]._
