# Line-hugging rounded box captions

Bold dark text on a white box whose rounded corners follow each line's own width, the native look of in-app text on vertical platforms. Suits talking heads, UGC ads and how-to clips in 9:16 and 1:1; 2-6 words per screen, a few seconds each.

Fonts: Plus Jakarta Sans (OFL-1.1), Inter (OFL-1.1). Formats: 9:16, 1:1, 16:9.

## How the pros do it
- Give each line its own background box sized to that line, with 0.5 em side padding and no gap between lines [4].
- Implement it with an inline span plus box-decoration-break: clone so every wrapped line gets its own padding, radius and shadow [21].
- Near-black text on white is 18.9:1; that is the point of the look, so keep the box fully opaque [8].
- Mixed case reads faster than caps; reserve caps for one stressed word [4][6][36].
- In 9:16, three short lines is the maximum; keep the block in the lower third but above the platform UI [4][10][11].
- Break lines by grammar, not by width: phrase-level breaks make text easier to process [1][4].
- Use one colour for the text; if you mark a keyword, change one word at most [28][41].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `line-hug-box-captions.white-box-classic` | #111 text on white per-line boxes with 0.28 em radius | Plus Jakarta Sans 800, 80 px (4.2% H), line-height 1.22, box #FFF, pad .14em .42em, radius .28em, 2-6 words, <=3 lines [4][8][18][21] |
| `line-hug-box-captions.black-box-inverse` | White text on black per-line boxes for bright footage | box #111 at 100%, text #FFF (18.9:1), same radius/padding [8][21] |
| `line-hug-box-captions.navy-pill-rise` | Spaced caps in translucent navy pills; each line rises through a clip | caps, tracking 3-6 px, pill rgb(6,20,40) at 62% (5.2:1 over a white frame), line rises 1.3x its height through overflow clip, ease-out-quint cubic-bezier(0.22,1,0.36,1), 10 f [8][42] |
| `line-hug-box-captions.brand-tint` | Box in the brand colour, text auto-picked for >= 4.5:1 | box = brand hex; text #111 or #FFF, whichever gives >= 4.5:1; drop shadow 0 6px 18px rgba(0,0,0,.28) [8] |

## Timing and numbers
- Box geometry at 80 px type: padding 11 px top/bottom and 34 px left/right, radius 22 px; line-height 1.22 makes the boxes of consecutive lines touch (no light strip between them) [4].
- Entrance (optional): box scaleX 0.92 to 1 from the centre over 6 frames (200 ms, Material short4) with emphasized-decelerate cubic-bezier(0.05,0.7,0.1,1); text cuts in with the box [18].
- Page length: about 1.2 s per group of words, the Remotion example value [16].
- Shared baseline for every caption look:
  - Frame maths at 30 fps: 1 frame = 33 ms; 4 f = 133 ms; 6 f = 200 ms; 8 f = 267 ms; 12 f = 400 ms.
  - Reading baseline: 160-180 wpm = 0.33-0.375 s per word; adult ceiling 20 characters/s [1][4]. At 180 wpm a word lasts ~10 frames, so any per-word animation must finish inside ~6 frames.
  - Sync: change the active word 1-2 frames before its audio onset. Picture-early is undetectable up to ~125 ms, picture-late is detectable from ~45 ms (ITU-R BT.1359) [15]. Caption blocks go up on the first audio frame or within 1-2 frames [3].
  - 9:16 safe box (1080x1920), worst case of the platforms' ad specs: top 288 px (15%), bottom 672 px (35%), left 120 px, right 192 px; keep the caption block inside x 120-888, y 288-1248. Centred captions: max width 696 px (64% W) so both edges clear 192 px [10][11][13]. TikTok sizes its zone by ratio and ad-caption length, so treat these as minimums [12]. Organic-only posts can go lower: nothing important in the bottom 20% or right 15% [39].
  - 16:9: keep captions inside the central 90% vertically and 75% horizontally; a line is at most 68% of the width [4].
  - Contrast: >= 4.5:1 for text and its immediate background; 3:1 is the floor only for large text [8].
  - Final check: watch a render on a phone at arm's length; if you have to focus to read, go bigger. Keep >= 60 px from the frame edges [44].

## Build it
1. Wrap the caption in `<span class=box>`; CSS: `background:#fff; color:#111; padding:.14em .42em; border-radius:.28em; -webkit-box-decoration-break:clone; box-decoration-break:clone; line-height:1.22` [21].
2. For merged 'gooey' inner corners (where a short line meets a long one), duplicate the boxes in an SVG layer and apply an feGaussianBlur (stdDeviation ~8 at 80 px type) followed by an feColorMatrix alpha threshold; keep the text in a separate unfiltered layer.
3. Group words into pages with Remotion `createTikTokStyleCaptions({combineTokensWithinMilliseconds: 1200})` or the same rule in GSAP [16].
4. Animate only transform and opacity on the box layer; never animate padding or font-size (reflow jitters between frames).

## Mistakes that look amateur
- Line boxes with a thin gap of video between them → raise line-height or padding until the boxes touch [4].
- Using `display:inline-block` for the box → only the outer box is rounded; use inline + clone [21].
- White box with no shadow on a white wall → add a soft 0 6px 18px 28% shadow or switch to the inverse preset.
- All-caps paragraphs in the box → sentence case [6][36].
- Box radius bigger than half the line height → the box turns into a pill and the corners collide; keep radius <= 0.3 em.

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
[28] Meryl K. Evans (deaf accessibility advocate and CPACC, writes caption guides) — Why captioned videos are important — https://meryl.net/why-captioned-videos-are-important/ — one colour, no word highlighting, no 1-2 word captions, 1-2 lines (~60 chars), off-black #242424 box with off-white text, bottom placement, sentence case, minimal motion
[36] @digitalMakerCIC (Digital Maker CIC) (UK digital inclusion social enterprise) — Reply: ALL CAPS — https://x.com/digitalMakerCIC/status/1643577323210326016 — ALL CAPS loses word shapes and is hard for dyslexic readers
[39] @wayofzorro (Zorro) (Shorts channel operator; checklist post had 6.4k likes, 8.6k bookmarks) — Shorts production checklist — https://x.com/wayofzorro/status/2105523352261542050 — large word-by-word captions inside the safe zone; nothing important in the bottom 20% or right 15%; captions perfectly synced; lock fonts and layout in a master project
[41] @finnardley (Finn) (AI video creator publishing code-built shorts recipes) — Stickman thriller recipe — https://x.com/finnardley/status/2115786060231770351 — chunky captions of 1-3 words with key words in an accent colour; snap each word to its real audio start and check voice is under every caption within ~120 ms
[42] @finnardley (Finn) (AI video creator) — Space explainer recipe — https://x.com/finnardley/status/2114305886420086817 — caps captions with 3-6 px tracking in rounded pills of rgb(6,20,40) at 62%; each line rises 1.3x its height through a clip on an ease-out-quint
[44] Derek Coleman (OpusClip) (senior growth marketer at a short-form clipping company) — Video caption design and placement — https://www.opus.pro/blog/video-caption-design-placement — middle 80% of width, at least 60 px from edges, accent backgrounds at 70-80% opacity, 2-frame gaps, test on a phone at arm's length

_TikTok, YouTube, Instagram and Meta are named only to describe their published safe zones; their names, logos and interfaces are trademarks of their owners. Fonts are OFL-1.1 (free for commercial video, no attribution needed) [27]._
