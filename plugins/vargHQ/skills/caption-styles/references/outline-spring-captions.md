# Outlined spring-word captions

White words with a thick black outline; the spoken word turns cyan and springs up a few pixels, then settles. Gaming, commentary, reaction and creator clips in 9:16; 2-4 words per page.

Fonts: Montserrat (OFL-1.1), Anton (OFL-1.1). Formats: 9:16, 1:1.

## How the pros do it
- Put the stroke behind the fill (paint-order: stroke fill) so a thick outline grows outward and does not eat the glyph [24].
- Outline width is a pixel value in subtitle tools (\bord); scale it with type size, about 0.1-0.14 em [20].
- Cyan on black is 16.8:1 and is one of the four standard caption colours [4][8].
- Spring the active word upward with a Remotion spring; defaults (damping 10) bounce, damping 14-18 settles faster [17].
- Outlined white text without a box is weaker than a box for caption-dependent viewers; add a hard drop shadow to thicken it [28].
- Switch at onset minus 1 frame [15].
- Heavy sans (Montserrat Black) or condensed (Anton) are the common short-form choices [37][38].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `outline-spring-captions.cyan-spring` | Montserrat Black, 12 px outline, active cyan rising 0.12 em | 88 px (4.6% H), stroke 12 px #000 (paint-order stroke fill), drop 0 5px 0 rgba(0,0,0,.6); active #00FFFF, y 0→-0.12em spring {mass 1, damping 14, stiffness 180}, back to 0 on next word in 4 f [4][8][17][24] |
| `outline-spring-captions.gaming-condensed` | Anton caps, thicker outline, bigger rise | Anton caps 110 px, stroke 16 px, active rise 0.18 em, damping 10 (default bounce) [17][37] |
| `outline-spring-captions.clean-outline` | Thinner outline, no rise, colour change only | stroke 8 px, no drop shadow, active #00FFFF instant [24] |

## Timing and numbers
- Spring settles in ~8 frames with damping 14 / stiffness 180 (house value); default {1,10,100} rings for ~15+ frames, too long for ~10-frame words [17].
- Release: previous word drops back to baseline over 4 frames with power2.out while the new word rises.
- Shared baseline for every caption look:
  - Frame maths at 30 fps: 1 frame = 33 ms; 4 f = 133 ms; 6 f = 200 ms; 8 f = 267 ms; 12 f = 400 ms.
  - Reading baseline: 160-180 wpm = 0.33-0.375 s per word; adult ceiling 20 characters/s [1][4]. At 180 wpm a word lasts ~10 frames, so any per-word animation must finish inside ~6 frames.
  - Sync: change the active word 1-2 frames before its audio onset. Picture-early is undetectable up to ~125 ms, picture-late is detectable from ~45 ms (ITU-R BT.1359) [15]. Caption blocks go up on the first audio frame or within 1-2 frames [3].
  - 9:16 safe box (1080x1920), worst case of the platforms' ad specs: top 288 px (15%), bottom 672 px (35%), left 120 px, right 192 px; keep the caption block inside x 120-888, y 288-1248. Centred captions: max width 696 px (64% W) so both edges clear 192 px [10][11][13]. TikTok sizes its zone by ratio and ad-caption length, so treat these as minimums [12]. Organic-only posts can go lower: nothing important in the bottom 20% or right 15% [39].
  - 16:9: keep captions inside the central 90% vertically and 75% horizontally; a line is at most 68% of the width [4].
  - Contrast: >= 4.5:1 for text and its immediate background; 3:1 is the floor only for large text [8].
  - Final check: watch a render on a phone at arm's length; if you have to focus to read, go bigger. Keep >= 60 px from the frame edges [44].

## Build it
1. CSS: `-webkit-text-stroke:12px #000; paint-order:stroke fill; text-shadow:0 5px 0 rgba(0,0,0,.6)` [24].
2. Remotion: per word `const s = spring({frame: frame - (startFrame-1), fps, config:{damping:14, stiffness:180}})`; `translateY = -0.12*fontSize*s` while active [17].
3. ASS/ffmpeg: Style `Outline=6, Shadow=2` in script px; active word `{\1c&HFFFF00&\t(0,120,\frz0)}`; ASS cannot spring, so pre-render via HTML for the rise [20].

## Mistakes that look amateur
- Stroke drawn on top of the fill (default) → 12 px outline swallows the counters of a, e, o [24].
- Outline in px fixed at 1080 when rendering 4K → hairline; size relative to font.
- Default bouncy spring on every word → the line vibrates; damp it [17].
- Cyan active word with no outline on a sky shot → near-invisible; outline stays on all words.

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
[17] Remotion (Remotion docs) — spring() — https://www.remotion.dev/docs/spring — defaults mass 1, damping 10, stiffness 100, overshootClamping false; raise damping to remove bounce; durationInFrames, delay
[20] Aegisub (the standard open-source subtitle/karaoke editor) — ASS override tags — https://aegisub.org/docs/latest/ass_tags/ — \k instant fill, \kf sweep fill over the syllable duration (centiseconds), \ko outline reveal, \bord/\shad in px, \blur, animate \fscx/\fscy with \t instead of \fs
[24] MDN (Mozilla web docs) — paint-order — https://developer.mozilla.org/en-US/docs/Web/CSS/paint-order — paint-order: stroke fill puts -webkit-text-stroke behind the glyph so only the outer half shows; Baseline since 2024
[28] Meryl K. Evans (deaf accessibility advocate and CPACC, writes caption guides) — Why captioned videos are important — https://meryl.net/why-captioned-videos-are-important/ — one colour, no word highlighting, no 1-2 word captions, 1-2 lines (~60 chars), off-black #242424 box with off-white text, bottom placement, sentence case, minimal motion
[37] @mws (Muaaz) (YouTube/short-form creator; font list post had 1,252 likes and 1,602 bookmarks) — Best fonts for subtitles on TikTok/Shorts/Reels — https://x.com/mws/status/1872411175826403825 — heavy geometric sans (Montserrat Black), condensed display (Bebas Neue) and rounded comic faces dominate short-form captions
[38] @yt_igm (igorm) (YouTube Shorts creator; post had 1,949 likes and 2,220 bookmarks) — Best YouTube Shorts subtitle fonts — https://x.com/yt_igm/status/2031339804680478802 — Montserrat, Kanit, Bebas Neue among the common Shorts caption faces
[39] @wayofzorro (Zorro) (Shorts channel operator; checklist post had 6.4k likes, 8.6k bookmarks) — Shorts production checklist — https://x.com/wayofzorro/status/2105523352261542050 — large word-by-word captions inside the safe zone; nothing important in the bottom 20% or right 15%; captions perfectly synced; lock fonts and layout in a master project
[44] Derek Coleman (OpusClip) (senior growth marketer at a short-form clipping company) — Video caption design and placement — https://www.opus.pro/blog/video-caption-design-placement — middle 80% of width, at least 60 px from edges, accent backgrounds at 70-80% opacity, 2-frame gaps, test on a phone at arm's length

_TikTok, YouTube, Instagram and Meta are named only to describe their published safe zones; their names, logos and interfaces are trademarks of their owners. Fonts are OFL-1.1 (free for commercial video, no attribution needed) [27]._
