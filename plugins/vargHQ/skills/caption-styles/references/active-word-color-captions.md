# Active word colour captions

White outlined text, a few words at a time, where only the colour of the spoken word changes: no scale, no box. The calmer cousin of the pop look for podcasts, interviews and explainers in 9:16 and 1:1.

Fonts: Montserrat (OFL-1.1), Poppins (OFL-1.1), Inter (OFL-1.1). Formats: 9:16, 1:1, 16:9.

## How the pros do it
- Pages of 3-5 words built from word timestamps: combine tokens over ~1-1.4 s and break on silences [16].
- Colour switches at onset minus 1-2 frames; visual-early is tolerated up to ~125 ms, visual-late is detected at ~45 ms [15].
- Use high-contrast active colours on a black outline: yellow #FFE600 (16.6:1) or light blue #4DA3FF (8:1); the BBC's caption palette is white, yellow, cyan, green on black [4][8].
- Mixed case by default; caps paragraphs lose word shapes [6][36].
- Line breaks follow grammar, even inside 3-5-word pages [1][4].
- Deaf and hard-of-hearing viewers report highlights pulling their eyes off the meaning; keep a plain version ready [28][31][32].
- Short-form editors key one or two accent words, not every word, when the clip is long [41].
- Word-timed reveal protects jokes and suspense that block captions spoil by showing the punchline before it is said [34].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `active-word-color-captions.blue-outline` | Montserrat 800 white with black stroke, spoken word #4DA3FF | 84 px (4.4% H), stroke 9 px behind fill, active #4DA3FF, switch 1 f early, 3-5 words/page, page ~1.2 s [8][15][16][24] |
| `active-word-color-captions.yellow-outline` | Classic yellow active word for maximum legibility | active #FFE600 (16.6:1 vs black), shadow 0 3px 0 rgba(0,0,0,.55) [4][8] |
| `active-word-color-captions.calm-phrase` | No highlight: same page grouping, all white | active_color = text_color; pages 5-8 words, 2 lines; use for accessibility deliverables [28][31] |

## Timing and numbers
- Colour transition: instant (cut) or at most 2 frames (67 ms, Material short2 is 100 ms); longer fades blur which word is current [18].
- Silence break: if the gap between words exceeds 400 ms, end the page; Remotion supports this as breakOnSilenceAfterMilliseconds [16].
- Last word of a page: keep it highlighted until the page ends instead of reverting to white for a few frames.
- Shared baseline for every caption look:
  - Frame maths at 30 fps: 1 frame = 33 ms; 4 f = 133 ms; 6 f = 200 ms; 8 f = 267 ms; 12 f = 400 ms.
  - Reading baseline: 160-180 wpm = 0.33-0.375 s per word; adult ceiling 20 characters/s [1][4]. At 180 wpm a word lasts ~10 frames, so any per-word animation must finish inside ~6 frames.
  - Sync: change the active word 1-2 frames before its audio onset. Picture-early is undetectable up to ~125 ms, picture-late is detectable from ~45 ms (ITU-R BT.1359) [15]. Caption blocks go up on the first audio frame or within 1-2 frames [3].
  - 9:16 safe box (1080x1920), worst case of the platforms' ad specs: top 288 px (15%), bottom 672 px (35%), left 120 px, right 192 px; keep the caption block inside x 120-888, y 288-1248. Centred captions: max width 696 px (64% W) so both edges clear 192 px [10][11][13]. TikTok sizes its zone by ratio and ad-caption length, so treat these as minimums [12]. Organic-only posts can go lower: nothing important in the bottom 20% or right 15% [39].
  - 16:9: keep captions inside the central 90% vertically and 75% horizontally; a line is at most 68% of the width [4].
  - Contrast: >= 4.5:1 for text and its immediate background; 3:1 is the floor only for large text [8].
  - Final check: watch a render on a phone at arm's length; if you have to focus to read, go bigger. Keep >= 60 px from the frame edges [44].

## Build it
1. Remotion: `const {pages} = createTikTokStyleCaptions({captions, combineTokensWithinMilliseconds:1200, breakOnSilenceAfterMilliseconds:400})`; in each page, a token is active when `frameMs >= token.fromMs - 33 && frameMs < token.toMs`; container `white-space: pre` [16].
2. HyperFrames/GSAP: one `tl.set(word,{color:active}, start-1/30)` and `tl.set(word,{color:'#fff'}, next.start-1/30)` per token; no tweens needed.
3. ffmpeg/ASS: one Dialogue line per page, `\k` tags per word with `SecondaryColour` = white and `PrimaryColour` = active (instant fill) [20].

## Mistakes that look amateur
- Highlight keyed to the end of each word → whole caption feels late [15].
- Every page a single word → that is a different, harder-to-read look; keep 3-5 [14][30].
- Active colour close to the base (pale yellow on white) → nobody sees the change; use a saturated hue with >= 4.5:1 on the outline [8].
- Highlight left on after the page cuts → reset on every page change.
- Words that change colour AND size AND rotate → pick one signal.

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
[14] Pablo Romero-Fresco (subtitling researcher (Universidade de Vigo / Roehampton), eye-tracking studies of live subtitles) — Standing on quicksand: viewers' comprehension and reading patterns of respoken subtitles for the news (2010) — https://bibbase.org/network/publication/romerofresco-standingonquicksandviewerscomprehensionandreadingpatternsofrespokensubtitlesforthenews-2010 — word-for-word display: viewers spent ~90% of the time on the subtitles and ~10% on the image, and comprehension fell
[15] Randy Hoffner / ITU-R BT.1359 (broadcast engineering columnist, TV Technology) — AV synchronization: how bad is bad? — https://www.tvtechnology.com/opinions/av-synchronization-how-bad-is-bad — ITU-R BT.1359 detectability about +45 ms (sound early) to -125 ms (sound late); people tolerate picture-before-sound far more than sound-before-picture
[16] Remotion (Remotion docs (React video framework)) — createTikTokStyleCaptions() — https://www.remotion.dev/docs/captions/create-tiktok-style-captions — combineTokensWithinMilliseconds (example 1200), breakOnSilenceAfterMilliseconds, token fromMs/toMs, white-space: pre
[18] Google Material Design 3 (Material motion tokens, Apache-2.0 source) — md-sys-motion tokens (material-web) — https://github.com/material-components/material-web/blob/main/tokens/versions/v0_192/_md-sys-motion.scss — durations short1-4 = 50/100/150/200 ms, medium1-4 = 250-400 ms; emphasized cubic-bezier(0.2,0,0,1), emphasized-decelerate (0.05,0.7,0.1,1), emphasized-accelerate (0.3,0,0.8,0.15)
[20] Aegisub (the standard open-source subtitle/karaoke editor) — ASS override tags — https://aegisub.org/docs/latest/ass_tags/ — \k instant fill, \kf sweep fill over the syllable duration (centiseconds), \ko outline reveal, \bord/\shad in px, \blur, animate \fscx/\fscy with \t instead of \fs
[24] MDN (Mozilla web docs) — paint-order — https://developer.mozilla.org/en-US/docs/Web/CSS/paint-order — paint-order: stroke fill puts -webkit-text-stroke behind the glyph so only the outer half shows; Baseline since 2024
[28] Meryl K. Evans (deaf accessibility advocate and CPACC, writes caption guides) — Why captioned videos are important — https://meryl.net/why-captioned-videos-are-important/ — one colour, no word highlighting, no 1-2 word captions, 1-2 lines (~60 chars), off-black #242424 box with off-white text, bottom placement, sentence case, minimal motion
[30] @merylkevans (Meryl Evans) (deaf accessibility advocate) — Reply: single-word captions — https://x.com/merylkevans/status/1643731008229875713 — single-word captions are too fast for most viewers
[31] @merylkevans (Meryl Evans) (deaf accessibility advocate) — Reply: karaoke-style captions — https://x.com/merylkevans/status/1821233367712711088 — eyes follow the highlighted word instead of comprehending the text
[32] @merylkevans (Meryl Evans) (deaf accessibility advocate) — Post: highlighted current word — https://x.com/merylkevans/status/1556278998405103617 — word highlights took over her eyes and she lost the message
[34] @2e0rtb (Richard Banks) (viewer reply in the side-by-side thread) — Reply: styled vs traditional captions by genre — https://x.com/2e0rtb/status/1643531650725208067 — traditional block captions that run ahead of dialogue ruin jokes and suspense; styled captions suit clip-type videos
[36] @digitalMakerCIC (Digital Maker CIC) (UK digital inclusion social enterprise) — Reply: ALL CAPS — https://x.com/digitalMakerCIC/status/1643577323210326016 — ALL CAPS loses word shapes and is hard for dyslexic readers
[39] @wayofzorro (Zorro) (Shorts channel operator; checklist post had 6.4k likes, 8.6k bookmarks) — Shorts production checklist — https://x.com/wayofzorro/status/2105523352261542050 — large word-by-word captions inside the safe zone; nothing important in the bottom 20% or right 15%; captions perfectly synced; lock fonts and layout in a master project
[41] @finnardley (Finn) (AI video creator publishing code-built shorts recipes) — Stickman thriller recipe — https://x.com/finnardley/status/2115786060231770351 — chunky captions of 1-3 words with key words in an accent colour; snap each word to its real audio start and check voice is under every caption within ~120 ms
[44] Derek Coleman (OpusClip) (senior growth marketer at a short-form clipping company) — Video caption design and placement — https://www.opus.pro/blog/video-caption-design-placement — middle 80% of width, at least 60 px from edges, accent backgrounds at 70-80% opacity, 2-frame gaps, test on a phone at arm's length

_TikTok, YouTube, Instagram and Meta are named only to describe their published safe zones; their names, logos and interfaces are trademarks of their owners. Fonts are OFL-1.1 (free for commercial video, no attribution needed) [27]._
