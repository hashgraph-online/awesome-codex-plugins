# Grow-in highlight box captions

White words inside a dark rounded box; the spoken word turns yellow and grows into place while the box adjusts its width. Business podcasts, coaching and talking-head ads in 9:16 and 1:1; 2-4 words per page.

Fonts: Montserrat (OFL-1.1), Poppins (OFL-1.1). Formats: 9:16, 1:1.

## How the pros do it
- Dark box at >= 75% so every word sits on >= 4.5:1 background regardless of footage [8].
- Yellow #FFD400 on near-black is 13.8:1 [8].
- Grow the word with transform scale from ~0.9 to 1.0 (not font-size) and animate the box width separately to avoid reflow [20].
- Box width change: 4-6 frames with Material emphasized cubic-bezier(0.2,0,0,1) [18].
- Switch colour at onset minus 1 frame; the grow completes within 4 frames [15].
- 2-4 words per page; key at most one or two accent words per sentence in long clips [16][41].
- Offer a non-highlight export for accessibility deliverables [28][31].
- This look is the most copied trend style; swap in the brand font and accent colour instead of the stock yellow when the account has an identity [40].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `grow-highlight-captions.yellow-grow` | Dark rounded box, active word yellow, grows 0.9→1 | Montserrat 900 86 px; box rgba(10,10,10,.78) pad .2em .45em radius .4em; active #FFD400, scale .9→1.0 in 4 f power3.out (from 1 f early); box width tween 5 f cubic-bezier(.2,0,0,1) [8][15][18] |
| `grow-highlight-captions.green-grow` | Money/finance green accent | active #3DFF8A (15.0:1 on #0A0A0A) [8] |
| `grow-highlight-captions.reveal-grow` | Words appear only as spoken, box grows to fit | unspoken words hidden; each word fades in 2 f + scale .9→1 4 f; box width follows [18] |

## Timing and numbers
- At 180 wpm (~10 frames per word) the 4-frame grow plus 1-frame lead leaves ~5 frames of still text per word [4].
- Box width animates only when the page's text width changes (reveal mode); with full pages the box is static.
- Shared baseline for every caption look:
  - Frame maths at 30 fps: 1 frame = 33 ms; 4 f = 133 ms; 6 f = 200 ms; 8 f = 267 ms; 12 f = 400 ms.
  - Reading baseline: 160-180 wpm = 0.33-0.375 s per word; adult ceiling 20 characters/s [1][4]. At 180 wpm a word lasts ~10 frames, so any per-word animation must finish inside ~6 frames.
  - Sync: change the active word 1-2 frames before its audio onset. Picture-early is undetectable up to ~125 ms, picture-late is detectable from ~45 ms (ITU-R BT.1359) [15]. Caption blocks go up on the first audio frame or within 1-2 frames [3].
  - 9:16 safe box (1080x1920), worst case of the platforms' ad specs: top 288 px (15%), bottom 672 px (35%), left 120 px, right 192 px; keep the caption block inside x 120-888, y 288-1248. Centred captions: max width 696 px (64% W) so both edges clear 192 px [10][11][13]. TikTok sizes its zone by ratio and ad-caption length, so treat these as minimums [12]. Organic-only posts can go lower: nothing important in the bottom 20% or right 15% [39].
  - 16:9: keep captions inside the central 90% vertically and 75% horizontally; a line is at most 68% of the width [4].
  - Contrast: >= 4.5:1 for text and its immediate background; 3:1 is the floor only for large text [8].
  - Final check: watch a render on a phone at arm's length; if you have to focus to read, go bigger. Keep >= 60 px from the frame edges [44].

## Build it
1. Start from HyperFrames `caption-highlight` (background sweep behind the active word) and change the sweep into colour + grow [45].
2. Pre-layout the page at final size, store word rects; for the reveal preset, tween the box width to the right edge of the last revealed word.
3. Remotion: `scale = interpolate(frame, [s-1, s+3], [0.9, 1], {easing: Easing.out(Easing.cubic), extrapolateLeft:'clamp', extrapolateRight:'clamp'})` for the active token.

## Mistakes that look amateur
- Growing via font-size → the box and line jitter every frame [20].
- Yellow on a light-grey box → contrast collapses; keep the box near-black at >= 75% [8].
- Word grows from 0.5 → reads as popping out of nowhere; 0.9 is enough.
- Every word yellow by the end of the page (no reset) → reset or use the reveal preset deliberately.

## Sources
[1] Netflix (Netflix partner help (style guide owner)) — English (USA) Timed Text Style Guide — https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-USA-Timed-Text-Style-Guide — 42 characters per line, max 2 lines, 20 cps adults / 17 cps children, line-break rules, italics rules
[3] Netflix (Netflix partner help) — Timed Text Style Guide: Subtitle Timing Guidelines — https://partnerhelp.netflixstudios.com/hc/en-us/articles/360051554394-Timed-Text-Style-Guide-Subtitle-Timing-Guidelines — in-time on the first audio frame or within 1-2 frames, 2-frame minimum gap, close gaps under 0.5 s, out-time 0.5 s after audio, shot-change rules
[4] BBC (BBC accessibility team (UK public broadcaster)) — BBC Subtitle Guidelines — https://www.bbc.co.uk/accessibility/forproducts/guides/subtitles/ — 160-180 wpm (0.33-0.375 s/word), line height 7-8% of height (16:9) and 3.9-4.5% (9:16), font ~3.5% of height for 9:16, 68%/90% line width, 2 lines (3 for 9:16), per-line background with 0.5 em padding, white/yellow/cyan/green on black, 9:16 captions a little higher in the lower third, sync and lag limits, lyrics rules
[8] W3C WAI (World Wide Web Consortium accessibility standard) — Understanding WCAG 2.2 SC 1.4.3 Contrast (Minimum) — https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html — 4.5:1 normal text, 3:1 large text (18 pt / 14 pt bold); ratios are not rounded. We used its formula to compute every colour pair in the presets
[10] Meta (Meta Ads Guide (platform spec)) — Instagram Reels video ad specs — https://www.facebook.com/business/ads-guide/update/video/instagram-reels — keep 14% top, 35% bottom and 6% each side free of text
[11] Socialync (safe-zone tool that compiles the platforms' published ad margins) — Social media safe zones — https://www.socialync.io/tools/safe-zones — 1080x1920 margins: TikTok 240/660/120/120, Reels 269/672/65/65, Shorts 288/672/48/192 (top/bottom/left/right), all ad specs
[12] TikTok (TikTok Ads help (platform spec)) — TikTok Auction In-Feed Ads — https://ads.tiktok.com/help/article/tiktok-auction-in-feed-ads?lang=en — safe zone depends on ratio, ad caption length and extra formats; published as downloadable files
[13] Google (Google Ads help (platform spec)) — Safe zones for vertical video ads on YouTube — https://support.google.com/google-ads/answer/9128498?hl=en — 1080x1920 safe-zone image with pixel margins (values read via [11])
[15] Randy Hoffner / ITU-R BT.1359 (broadcast engineering columnist, TV Technology) — AV synchronization: how bad is bad? — https://www.tvtechnology.com/opinions/av-synchronization-how-bad-is-bad — ITU-R BT.1359 detectability about +45 ms (sound early) to -125 ms (sound late); people tolerate picture-before-sound far more than sound-before-picture
[16] Remotion (Remotion docs (React video framework)) — createTikTokStyleCaptions() — https://www.remotion.dev/docs/captions/create-tiktok-style-captions — combineTokensWithinMilliseconds (example 1200), breakOnSilenceAfterMilliseconds, token fromMs/toMs, white-space: pre
[18] Google Material Design 3 (Material motion tokens, Apache-2.0 source) — md-sys-motion tokens (material-web) — https://github.com/material-components/material-web/blob/main/tokens/versions/v0_192/_md-sys-motion.scss — durations short1-4 = 50/100/150/200 ms, medium1-4 = 250-400 ms; emphasized cubic-bezier(0.2,0,0,1), emphasized-decelerate (0.05,0.7,0.1,1), emphasized-accelerate (0.3,0,0.8,0.15)
[20] Aegisub (the standard open-source subtitle/karaoke editor) — ASS override tags — https://aegisub.org/docs/latest/ass_tags/ — \k instant fill, \kf sweep fill over the syllable duration (centiseconds), \ko outline reveal, \bord/\shad in px, \blur, animate \fscx/\fscy with \t instead of \fs
[28] Meryl K. Evans (deaf accessibility advocate and CPACC, writes caption guides) — Why captioned videos are important — https://meryl.net/why-captioned-videos-are-important/ — one colour, no word highlighting, no 1-2 word captions, 1-2 lines (~60 chars), off-black #242424 box with off-white text, bottom placement, sentence case, minimal motion
[31] @merylkevans (Meryl Evans) (deaf accessibility advocate) — Reply: karaoke-style captions — https://x.com/merylkevans/status/1821233367712711088 — eyes follow the highlighted word instead of comprehending the text
[39] @wayofzorro (Zorro) (Shorts channel operator; checklist post had 6.4k likes, 8.6k bookmarks) — Shorts production checklist — https://x.com/wayofzorro/status/2105523352261542050 — large word-by-word captions inside the safe zone; nothing important in the bottom 20% or right 15%; captions perfectly synced; lock fonts and layout in a master project
[40] @tigerjvideo (Tiger J) (short-form video producer for founders) — Thread: organic video framework — https://x.com/tigerjvideo/status/1634633758656671744 — do not blindly copy the trend caption style; apply your own brand identity
[41] @finnardley (Finn) (AI video creator publishing code-built shorts recipes) — Stickman thriller recipe — https://x.com/finnardley/status/2115786060231770351 — chunky captions of 1-3 words with key words in an accent colour; snap each word to its real audio start and check voice is under every caption within ~120 ms
[44] Derek Coleman (OpusClip) (senior growth marketer at a short-form clipping company) — Video caption design and placement — https://www.opus.pro/blog/video-caption-design-placement — middle 80% of width, at least 60 px from edges, accent backgrounds at 70-80% opacity, 2-frame gaps, test on a phone at arm's length
[45] HeyGen HyperFrames registry (open-source HTML-to-video framework) — Caption components (registry-item.json descriptions) — https://github.com/heygen-com/hyperframes/tree/main/registry/components — ready blocks: caption-highlight, caption-pill-karaoke, caption-gradient-fill, caption-neon-glow, caption-editorial-emphasis, caption-weight-shift, caption-kinetic-slam, caption-clip-wipe, per-word-rise, per-word-crossfade

_TikTok, YouTube, Instagram and Meta are named only to describe their published safe zones; their names, logos and interfaces are trademarks of their owners. Fonts are OFL-1.1 (free for commercial video, no attribution needed) [27]._
