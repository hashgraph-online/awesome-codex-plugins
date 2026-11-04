# Active word pop captions

White outlined words where the word being spoken turns blue and pops a little larger, then settles back. High-energy short-form: creator talking heads, podcast clips, ads; 9:16 first; 2-4 words per page.

Fonts: Montserrat (OFL-1.1), Poppins (OFL-1.1). Formats: 9:16, 1:1.

## How the pros do it
- Pop with transform: scale, never font-size, so the line does not reflow; subtitle editors animate scale tags rather than size for the same reason [20].
- Use GSAP back.out with its default 1.70158 overshoot (or a Remotion spring) for the pop, about 6 frames [17][19].
- Change colour at the word onset minus 1 frame; late highlights are noticed from ~45 ms [15].
- Choose a light blue that holds against the black outline: #4DA3FF is 8:1 on black, #2563EB only 4.1:1 [8].
- Only one active word at a time, and return it to white when the next starts; stacked highlights pull the eye off the message [31][32].
- 2-4 words per page, mixed case, heavy geometric sans like Montserrat Black, the short-form standard [37][38].
- Stroke behind the fill so heavy weights keep their counters open [24].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `active-word-pop-captions.blue-pop` | Montserrat Black, active word #4DA3FF at 112% with back.out | 88 px (4.6% H), stroke 10 px #000, active #4DA3FF, scale 1→1.12 in 4 f back.out(1.7), settle 1.12→1.06 by 8 f, colour switch 1 f early [8][15][19][24] |
| `active-word-pop-captions.subtle-pop` | Smaller pop for interviews and education | scale 1→1.06 in 4 f power2.out, no overshoot, active #7DD3FC (12.6:1 on black) [8][19] |
| `active-word-pop-captions.spring-pop` | Remotion spring for a rubbery hit on punchlines | spring {mass 1, damping 10, stiffness 100} mapped 1→1.14, durationInFrames 12 [17] |

## Timing and numbers
- Pop: 4 frames up (133 ms), 4 frames settle; total under the ~10 frames a word lasts at 180 wpm [4].
- Transform origin near the baseline (50% 80%) so the word grows upward and does not sink below the line.
- Leave 6-8% extra letter-space around words (word-spacing 0.28 em) so a 112% word does not collide with neighbours.
- Shared baseline for every caption look:
  - Frame maths at 30 fps: 1 frame = 33 ms; 4 f = 133 ms; 6 f = 200 ms; 8 f = 267 ms; 12 f = 400 ms.
  - Reading baseline: 160-180 wpm = 0.33-0.375 s per word; adult ceiling 20 characters/s [1][4]. At 180 wpm a word lasts ~10 frames, so any per-word animation must finish inside ~6 frames.
  - Sync: change the active word 1-2 frames before its audio onset. Picture-early is undetectable up to ~125 ms, picture-late is detectable from ~45 ms (ITU-R BT.1359) [15]. Caption blocks go up on the first audio frame or within 1-2 frames [3].
  - 9:16 safe box (1080x1920), worst case of the platforms' ad specs: top 288 px (15%), bottom 672 px (35%), left 120 px, right 192 px; keep the caption block inside x 120-888, y 288-1248. Centred captions: max width 696 px (64% W) so both edges clear 192 px [10][11][13]. TikTok sizes its zone by ratio and ad-caption length, so treat these as minimums [12]. Organic-only posts can go lower: nothing important in the bottom 20% or right 15% [39].
  - 16:9: keep captions inside the central 90% vertically and 75% horizontally; a line is at most 68% of the width [4].
  - Contrast: >= 4.5:1 for text and its immediate background; 3:1 is the floor only for large text [8].
  - Final check: watch a render on a phone at arm's length; if you have to focus to read, go bigger. Keep >= 60 px from the frame edges [44].

## Build it
1. Group tokens into pages of 2-4 words (Remotion createTikTokStyleCaptions with combineTokensWithinMilliseconds ~900) [16].
2. One span per word; per word: `tl.set(w,{color:'#4DA3FF'}, t-1/30).fromTo(w,{scale:1},{scale:1.12,duration:4/30,ease:'back.out(1.7)'}, t-1/30).to(w,{scale:1.06,duration:4/30,ease:'power2.out'})`, then reset on the next word [19].
3. HyperFrames: start from `caption-highlight` and swap its background sweep for colour + scale [45].
4. ASS/ffmpeg alternative: per word `{\t(0,130,\fscx112\fscy112)\t(130,260,\fscx106\fscy106)\1c&HFFA34D&}`, `\bord6 \shad0` (script px), burn with `subtitles=` [20].

## Mistakes that look amateur
- Animating font-size → whole line reflows each frame; scale with transform [20].
- Dark blue active word on black outline → disappears on dark footage; use #4DA3FF or lighter [8].
- Scale 1.3+ on every word → constant jitter; keep 1.06-1.15 and save big hits for punchlines.
- Two words highlighted at once because the previous never resets → reset at the next onset [32].
- Pop starting at the word's end time (wrong field) → use the start timestamp minus 1 frame [15].

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
[17] Remotion (Remotion docs) — spring() — https://www.remotion.dev/docs/spring — defaults mass 1, damping 10, stiffness 100, overshootClamping false; raise damping to remove bounce; durationInFrames, delay
[19] GreenSock (GSAP) (GSAP docs and source) — Eases docs + gsap-core.js 3.12.5 — https://gsap.com/docs/v3/Eases/ — default ease power1.out; back overshoot default 1.70158; elastic.out default amplitude 1, period 0.3 (source: https://unpkg.com/gsap@3.12.5/src/gsap-core.js)
[20] Aegisub (the standard open-source subtitle/karaoke editor) — ASS override tags — https://aegisub.org/docs/latest/ass_tags/ — \k instant fill, \kf sweep fill over the syllable duration (centiseconds), \ko outline reveal, \bord/\shad in px, \blur, animate \fscx/\fscy with \t instead of \fs
[24] MDN (Mozilla web docs) — paint-order — https://developer.mozilla.org/en-US/docs/Web/CSS/paint-order — paint-order: stroke fill puts -webkit-text-stroke behind the glyph so only the outer half shows; Baseline since 2024
[31] @merylkevans (Meryl Evans) (deaf accessibility advocate) — Reply: karaoke-style captions — https://x.com/merylkevans/status/1821233367712711088 — eyes follow the highlighted word instead of comprehending the text
[32] @merylkevans (Meryl Evans) (deaf accessibility advocate) — Post: highlighted current word — https://x.com/merylkevans/status/1556278998405103617 — word highlights took over her eyes and she lost the message
[37] @mws (Muaaz) (YouTube/short-form creator; font list post had 1,252 likes and 1,602 bookmarks) — Best fonts for subtitles on TikTok/Shorts/Reels — https://x.com/mws/status/1872411175826403825 — heavy geometric sans (Montserrat Black), condensed display (Bebas Neue) and rounded comic faces dominate short-form captions
[38] @yt_igm (igorm) (YouTube Shorts creator; post had 1,949 likes and 2,220 bookmarks) — Best YouTube Shorts subtitle fonts — https://x.com/yt_igm/status/2031339804680478802 — Montserrat, Kanit, Bebas Neue among the common Shorts caption faces
[39] @wayofzorro (Zorro) (Shorts channel operator; checklist post had 6.4k likes, 8.6k bookmarks) — Shorts production checklist — https://x.com/wayofzorro/status/2105523352261542050 — large word-by-word captions inside the safe zone; nothing important in the bottom 20% or right 15%; captions perfectly synced; lock fonts and layout in a master project
[44] Derek Coleman (OpusClip) (senior growth marketer at a short-form clipping company) — Video caption design and placement — https://www.opus.pro/blog/video-caption-design-placement — middle 80% of width, at least 60 px from edges, accent backgrounds at 70-80% opacity, 2-frame gaps, test on a phone at arm's length
[45] HeyGen HyperFrames registry (open-source HTML-to-video framework) — Caption components (registry-item.json descriptions) — https://github.com/heygen-com/hyperframes/tree/main/registry/components — ready blocks: caption-highlight, caption-pill-karaoke, caption-gradient-fill, caption-neon-glow, caption-editorial-emphasis, caption-weight-shift, caption-kinetic-slam, caption-clip-wipe, per-word-rise, per-word-crossfade

_TikTok, YouTube, Instagram and Meta are named only to describe their published safe zones; their names, logos and interfaces are trademarks of their owners. Fonts are OFL-1.1 (free for commercial video, no attribution needed) [27]._
