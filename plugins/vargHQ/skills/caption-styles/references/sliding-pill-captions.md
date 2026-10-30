# Sliding pill word tracker

A coloured pill slides from word to word behind white outlined text, marking the word being spoken while the text stays still. Short-form talking heads, podcasts clips and explainers in 9:16 or 1:1; 3-5 words per page, a few seconds each.

Fonts: Montserrat (OFL-1.1), Poppins (OFL-1.1). Formats: 9:16, 1:1, 16:9.

## How the pros do it
- Move the pill at the word's audio onset or 1-2 frames before; a highlight that arrives 45 ms late is noticeable, one 125 ms early is not [15].
- Snap each word to its real audio start and check that voice is under every caption within ~120 ms [41].
- Keep 3-5 words per page by grouping tokens over about 1.2 s and breaking on silences [16].
- Only the pill moves; the words stay put. Motion on the text itself costs readability [28][29].
- White text on the pill needs >= 4.5:1: #FFFFFF on #1F5BFF is 5.25:1, on #2F6BFF only 4.5:1 [8].
- Outside the pill, white text needs an outline or shadow; draw the stroke behind the fill so letters do not thin out [6][24].
- Ease the slide with Material emphasized cubic-bezier(0.2,0,0,1) over 4-6 frames (133-200 ms) [18].
- Word-tracking styles are chosen for attention and speech rhythm, not access: they amplify body language but cost some viewers the message [35]. Viewers who rely on captions find moving highlights distracting; offer a no-pill export for accessibility deliverables [31][32].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `sliding-pill-captions.electric-blue` | Blue pill under white Montserrat with black outline | Montserrat 900, 84 px (4.4% H), stroke 9 px #000 behind fill, pill #1F5BFF, pill pad .06em .22em, radius .5em, slide 5 f cubic-bezier(.2,0,0,1), lead 1 f [8][15][16][18][24] |
| `sliding-pill-captions.brand-pill` | Pill in the brand colour, text colour chosen for >= 4.5:1 | pill = brand hex; active text #FFF or #111 by contrast; 6 f slide [8] |
| `sliding-pill-captions.soft-pill` | Smaller, 85% opacity pill and a slower slide for calm podcasts | pill rgba(31,91,255,.85), pad .04em .16em, slide 7 f emphasized, 4-6 words per page [18] |

## Timing and numbers
- At 30 fps: slide 4-6 frames; at 180 wpm a word lasts ~10 frames, so the pill rests >= 4 frames on every word. If a word is shorter than 6 frames, jump (2 frames) instead of sliding [4][18].
- Line change inside a page: do not slide diagonally across the block; fade the pill out on the old line over 2 frames and scale it in (0.8 to 1) on the new one over 4 frames.
- Page change: cut the old page, then the pill appears on word 1 already in place.
- Shared baseline for every caption look:
  - Frame maths at 30 fps: 1 frame = 33 ms; 4 f = 133 ms; 6 f = 200 ms; 8 f = 267 ms; 12 f = 400 ms.
  - Reading baseline: 160-180 wpm = 0.33-0.375 s per word; adult ceiling 20 characters/s [1][4]. At 180 wpm a word lasts ~10 frames, so any per-word animation must finish inside ~6 frames.
  - Sync: change the active word 1-2 frames before its audio onset. Picture-early is undetectable up to ~125 ms, picture-late is detectable from ~45 ms (ITU-R BT.1359) [15]. Caption blocks go up on the first audio frame or within 1-2 frames [3].
  - 9:16 safe box (1080x1920), worst case of the platforms' ad specs: top 288 px (15%), bottom 672 px (35%), left 120 px, right 192 px; keep the caption block inside x 120-888, y 288-1248. Centred captions: max width 696 px (64% W) so both edges clear 192 px [10][11][13]. TikTok sizes its zone by ratio and ad-caption length, so treat these as minimums [12]. Organic-only posts can go lower: nothing important in the bottom 20% or right 15% [39].
  - 16:9: keep captions inside the central 90% vertically and 75% horizontally; a line is at most 68% of the width [4].
  - Contrast: >= 4.5:1 for text and its immediate background; 3:1 is the floor only for large text [8].
  - Final check: watch a render on a phone at arm's length; if you have to focus to read, go bigger. Keep >= 60 px from the frame edges [44].

## Build it
1. Start from the HyperFrames `caption-pill-karaoke` or `caption-highlight` component (`npx hyperframes add caption-highlight`) [45].
2. Layout once per page: render words as inline spans, read each span's offsetLeft/offsetTop/offsetWidth after fonts load, store the rects; never measure inside the per-frame update.
3. Put a single absolutely positioned pill div behind the words (z-index below text). For each word: `tl.to(pill,{x:r.left-pad, y:r.top, width:r.width+2*pad, duration:5/30, ease:'power3.out'}, word.start - 1/30)` (or CustomEase from cubic-bezier(0.2,0,0,1)) [18][19].
4. Remotion: compute the active token from `useCurrentFrame()`, then interpolate pill x/width between previous and current word rects over 5 frames with `Easing.bezier(0.2,0,0,1)`.
5. Text outline: `-webkit-text-stroke: 9px #000; paint-order: stroke fill;` so the visible outline is ~4.5 px outside the glyph [24].

## Mistakes that look amateur
- Pill late by 3-4 frames → it reads as lagging the voice; lead by 1 frame [15].
- Pill drawn above the text (covering it) → pill below, text above.
- Re-measuring layout every frame → jitter and slow renders; measure once per page.
- Mid-blue pill (#2563EB) with white text over busy footage → 5.2:1 is fine but add the outline; darker #1F5BFF if the brand allows [8].
- Pill sliding diagonally between lines → fade and re-appear on the new line.
- Seven or more words per page → the pill races across a wall of text; keep 3-5 [16].

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
[19] GreenSock (GSAP) (GSAP docs and source) — Eases docs + gsap-core.js 3.12.5 — https://gsap.com/docs/v3/Eases/ — default ease power1.out; back overshoot default 1.70158; elastic.out default amplitude 1, period 0.3 (source: https://unpkg.com/gsap@3.12.5/src/gsap-core.js)
[24] MDN (Mozilla web docs) — paint-order — https://developer.mozilla.org/en-US/docs/Web/CSS/paint-order — paint-order: stroke fill puts -webkit-text-stroke behind the glyph so only the outer half shows; Baseline since 2024
[28] Meryl K. Evans (deaf accessibility advocate and CPACC, writes caption guides) — Why captioned videos are important — https://meryl.net/why-captioned-videos-are-important/ — one colour, no word highlighting, no 1-2 word captions, 1-2 lines (~60 chars), off-black #242424 box with off-white text, bottom placement, sentence case, minimal motion
[29] @merylkevans (Meryl Evans) (deaf accessibility advocate, CPACC; post had 500 likes, 112k views) — Side-by-side: best-practice captions vs styled short-form captions — https://x.com/merylkevans/status/1643366339409584132 — most replies preferred the plain best-practice side; motion and colour changes made some viewers lose the message
[31] @merylkevans (Meryl Evans) (deaf accessibility advocate) — Reply: karaoke-style captions — https://x.com/merylkevans/status/1821233367712711088 — eyes follow the highlighted word instead of comprehending the text
[32] @merylkevans (Meryl Evans) (deaf accessibility advocate) — Post: highlighted current word — https://x.com/merylkevans/status/1556278998405103617 — word highlights took over her eyes and she lost the message
[35] @JoshuaGilmer (Josh, Luau) (product/marketing designer replying in the side-by-side thread) — Reply: attention vs accessibility — https://x.com/JoshuaGilmer/status/1643406838111645696 — word-timed styled captions amplify body language and rhythm, a real conflict between attention and accessibility
[39] @wayofzorro (Zorro) (Shorts channel operator; checklist post had 6.4k likes, 8.6k bookmarks) — Shorts production checklist — https://x.com/wayofzorro/status/2105523352261542050 — large word-by-word captions inside the safe zone; nothing important in the bottom 20% or right 15%; captions perfectly synced; lock fonts and layout in a master project
[41] @finnardley (Finn) (AI video creator publishing code-built shorts recipes) — Stickman thriller recipe — https://x.com/finnardley/status/2115786060231770351 — chunky captions of 1-3 words with key words in an accent colour; snap each word to its real audio start and check voice is under every caption within ~120 ms
[44] Derek Coleman (OpusClip) (senior growth marketer at a short-form clipping company) — Video caption design and placement — https://www.opus.pro/blog/video-caption-design-placement — middle 80% of width, at least 60 px from edges, accent backgrounds at 70-80% opacity, 2-frame gaps, test on a phone at arm's length
[45] HeyGen HyperFrames registry (open-source HTML-to-video framework) — Caption components (registry-item.json descriptions) — https://github.com/heygen-com/hyperframes/tree/main/registry/components — ready blocks: caption-highlight, caption-pill-karaoke, caption-gradient-fill, caption-neon-glow, caption-editorial-emphasis, caption-weight-shift, caption-kinetic-slam, caption-clip-wipe, per-word-rise, per-word-crossfade

_TikTok, YouTube, Instagram and Meta are named only to describe their published safe zones; their names, logos and interfaces are trademarks of their owners. Fonts are OFL-1.1 (free for commercial video, no attribution needed) [27]._
