# Word tile captions

Every word sits on its own dark rounded tile; the spoken word's tile turns orange. Listicles, tech and finance explainers, product tips and gaming; 9:16 and 1:1; 3-4 words per page.

Fonts: Archivo Black (OFL-1.1), Inter (OFL-1.1). Formats: 9:16, 1:1, 16:9.

## How the pros do it
- Per-word backgrounds need their own padding and radius; inline-block tiles with a fixed gap keep each word separate [21].
- Active tile orange with dark text: #141414 on #FF7A1A is 7.1:1; white on that orange is only 2.6:1 and fails [8].
- Inactive tiles near-black at ~90% so text sits on a box, not on footage [6][8].
- Stagger tiles in by 2 frames per word with an emphasized-decelerate scale-up, 6 frames each [18].
- Switch the active tile at onset minus 1 frame [15].
- 3-4 words per page and grammar-aware breaks [1][16].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `word-tile-captions.orange-active` | Dark tiles, white words; active tile #FF7A1A with dark text | Archivo Black 78 px; tile #141414 at 90%, pad .1em .26em, radius .18em, gap .16em; active tile #FF7A1A text #141414; switch 1 f early [8][15][21] |
| `word-tile-captions.stagger-in` | Tiles pop in left to right as the page appears | each tile scale .85→1 + opacity 0→1, 6 f, cubic-bezier(.05,.7,.1,1), stagger 2 f [18] |
| `word-tile-captions.mono-tiles` | White tiles, black text, active tile black with white text | tile #FFFFFF text #0A0A0A (19.8:1); active tile #0A0A0A text #FFFFFF [8] |

## Timing and numbers
- Active tile colour: cut or 2-frame crossfade; a 1-frame scale bump to 1.04 is optional.
- Stagger total for 4 words: 6 + 3×2 = 12 frames (0.4 s); the first word must be readable when its audio starts, so begin the stagger 6-8 frames before word 1 [3].
- Shared baseline for every caption look:
  - Frame maths at 30 fps: 1 frame = 33 ms; 4 f = 133 ms; 6 f = 200 ms; 8 f = 267 ms; 12 f = 400 ms.
  - Reading baseline: 160-180 wpm = 0.33-0.375 s per word; adult ceiling 20 characters/s [1][4]. At 180 wpm a word lasts ~10 frames, so any per-word animation must finish inside ~6 frames.
  - Sync: change the active word 1-2 frames before its audio onset. Picture-early is undetectable up to ~125 ms, picture-late is detectable from ~45 ms (ITU-R BT.1359) [15]. Caption blocks go up on the first audio frame or within 1-2 frames [3].
  - 9:16 safe box (1080x1920), worst case of the platforms' ad specs: top 288 px (15%), bottom 672 px (35%), left 120 px, right 192 px; keep the caption block inside x 120-888, y 288-1248. Centred captions: max width 696 px (64% W) so both edges clear 192 px [10][11][13]. TikTok sizes its zone by ratio and ad-caption length, so treat these as minimums [12]. Organic-only posts can go lower: nothing important in the bottom 20% or right 15% [39].
  - 16:9: keep captions inside the central 90% vertically and 75% horizontally; a line is at most 68% of the width [4].
  - Contrast: >= 4.5:1 for text and its immediate background; 3:1 is the floor only for large text [8].
  - Final check: watch a render on a phone at arm's length; if you have to focus to read, go bigger. Keep >= 60 px from the frame edges [44].

## Build it
1. Words as `display:inline-block` spans with background, padding and radius; a flex row with `gap:.16em` and `flex-wrap:wrap` centred.
2. HyperFrames has `wordmark-tiles` and `lt-soft-pill` blocks to borrow tile styling from [45].
3. Active state via `tl.set(tile,{backgroundColor:'#FF7A1A', color:'#141414'}, start-1/30)`.

## Mistakes that look amateur
- White text on the orange active tile → 2.6:1, fails [8].
- Tiles with different heights because of descenders → fix tile height with line-height 1 and vertical padding.
- Gap smaller than padding → tiles read as one bar; gap >= 0.14 em.
- Stagger starting at word-1 onset → the first word is still invisible when spoken; start early [3].

## Sources
[1] Netflix (Netflix partner help (style guide owner)) — English (USA) Timed Text Style Guide — https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-USA-Timed-Text-Style-Guide — 42 characters per line, max 2 lines, 20 cps adults / 17 cps children, line-break rules, italics rules
[3] Netflix (Netflix partner help) — Timed Text Style Guide: Subtitle Timing Guidelines — https://partnerhelp.netflixstudios.com/hc/en-us/articles/360051554394-Timed-Text-Style-Guide-Subtitle-Timing-Guidelines — in-time on the first audio frame or within 1-2 frames, 2-frame minimum gap, close gaps under 0.5 s, out-time 0.5 s after audio, shot-change rules
[4] BBC (BBC accessibility team (UK public broadcaster)) — BBC Subtitle Guidelines — https://www.bbc.co.uk/accessibility/forproducts/guides/subtitles/ — 160-180 wpm (0.33-0.375 s/word), line height 7-8% of height (16:9) and 3.9-4.5% (9:16), font ~3.5% of height for 9:16, 68%/90% line width, 2 lines (3 for 9:16), per-line background with 0.5 em padding, white/yellow/cyan/green on black, 9:16 captions a little higher in the lower third, sync and lag limits, lyrics rules
[6] DCMP (Described and Captioned Media Program) — Captioning Key: Text — https://dcmp.org/learn/597-captioning-key---text — medium-weight sans serif with drop or rim shadow, white, mixed case (caps only for shouting), translucent box, 2 lines, line division rules, move captions off faces and graphics, min 40 frames / max 6 s
[8] W3C WAI (World Wide Web Consortium accessibility standard) — Understanding WCAG 2.2 SC 1.4.3 Contrast (Minimum) — https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html — 4.5:1 normal text, 3:1 large text (18 pt / 14 pt bold); ratios are not rounded. We used its formula to compute every colour pair in the presets
[10] Meta (Meta Ads Guide (platform spec)) — Instagram Reels video ad specs — https://www.facebook.com/business/ads-guide/update/video/instagram-reels — keep 14% top, 35% bottom and 6% each side free of text
[11] Socialync (safe-zone tool that compiles the platforms' published ad margins) — Social media safe zones — https://www.socialync.io/tools/safe-zones — 1080x1920 margins: TikTok 240/660/120/120, Reels 269/672/65/65, Shorts 288/672/48/192 (top/bottom/left/right), all ad specs
[12] TikTok (TikTok Ads help (platform spec)) — TikTok Auction In-Feed Ads — https://ads.tiktok.com/help/article/tiktok-auction-in-feed-ads?lang=en — safe zone depends on ratio, ad caption length and extra formats; published as downloadable files
[13] Google (Google Ads help (platform spec)) — Safe zones for vertical video ads on YouTube — https://support.google.com/google-ads/answer/9128498?hl=en — 1080x1920 safe-zone image with pixel margins (values read via [11])
[15] Randy Hoffner / ITU-R BT.1359 (broadcast engineering columnist, TV Technology) — AV synchronization: how bad is bad? — https://www.tvtechnology.com/opinions/av-synchronization-how-bad-is-bad — ITU-R BT.1359 detectability about +45 ms (sound early) to -125 ms (sound late); people tolerate picture-before-sound far more than sound-before-picture
[16] Remotion (Remotion docs (React video framework)) — createTikTokStyleCaptions() — https://www.remotion.dev/docs/captions/create-tiktok-style-captions — combineTokensWithinMilliseconds (example 1200), breakOnSilenceAfterMilliseconds, token fromMs/toMs, white-space: pre
[18] Google Material Design 3 (Material motion tokens, Apache-2.0 source) — md-sys-motion tokens (material-web) — https://github.com/material-components/material-web/blob/main/tokens/versions/v0_192/_md-sys-motion.scss — durations short1-4 = 50/100/150/200 ms, medium1-4 = 250-400 ms; emphasized cubic-bezier(0.2,0,0,1), emphasized-decelerate (0.05,0.7,0.1,1), emphasized-accelerate (0.3,0,0.8,0.15)
[21] MDN (Mozilla web docs) — box-decoration-break — https://developer.mozilla.org/en-US/docs/Web/CSS/box-decoration-break — clone gives every wrapped line its own padding, radius, shadow and background
[39] @wayofzorro (Zorro) (Shorts channel operator; checklist post had 6.4k likes, 8.6k bookmarks) — Shorts production checklist — https://x.com/wayofzorro/status/2105523352261542050 — large word-by-word captions inside the safe zone; nothing important in the bottom 20% or right 15%; captions perfectly synced; lock fonts and layout in a master project
[44] Derek Coleman (OpusClip) (senior growth marketer at a short-form clipping company) — Video caption design and placement — https://www.opus.pro/blog/video-caption-design-placement — middle 80% of width, at least 60 px from edges, accent backgrounds at 70-80% opacity, 2-frame gaps, test on a phone at arm's length
[45] HeyGen HyperFrames registry (open-source HTML-to-video framework) — Caption components (registry-item.json descriptions) — https://github.com/heygen-com/hyperframes/tree/main/registry/components — ready blocks: caption-highlight, caption-pill-karaoke, caption-gradient-fill, caption-neon-glow, caption-editorial-emphasis, caption-weight-shift, caption-kinetic-slam, caption-clip-wipe, per-word-rise, per-word-crossfade

_TikTok, YouTube, Instagram and Meta are named only to describe their published safe zones; their names, logos and interfaces are trademarks of their owners. Fonts are OFL-1.1 (free for commercial video, no attribution needed) [27]._
