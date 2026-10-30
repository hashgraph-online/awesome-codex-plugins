# Gradient-fill word captions

The spoken word fills with a two-colour gradient (blue to pink by default) inside a dark rounded box while the other words stay white. Music promos, creator brands, product launches; 9:16 and 1:1; 2-4 words per page.

Fonts: Poppins (OFL-1.1), Outfit (OFL-1.1). Formats: 9:16, 1:1.

## How the pros do it
- Make gradient text with background-clip: text, color: transparent and text-shadow: none, plus a solid fallback colour [23].
- Apply the gradient per word span, not per line: with box-decoration-break clone a gradient restarts on every line fragment [21].
- Both gradient ends must pass contrast on the box: #5AA9FF is 8.0:1 and #FF5EDB 7.4:1 on #0B0B12; mid-blue #3B82F6 drops to 5.7:1 [8].
- Dark box at >= 80% opacity so the gradient never sits on raw footage [8].
- Switch at onset minus 1 frame [15].
- If you shimmer the gradient, keep luminance swings small and slow; never more than 3 flashes per second [9].
- The HyperFrames gradient caption ships with an elastic bounce entrance; use it for page entrances, not per word [45].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `gradient-word-captions.blue-pink-box` | Active word gradient #5AA9FF→#FF5EDB at 100deg, box #0B0B12 at 82% | Poppins 800, 84 px, box rgba(11,11,18,.82) pad .18em .4em radius .36em, inactive #FFF, active gradient 100deg, switch 1 f early [8][15][23] |
| `gradient-word-captions.sunset` | Warm gradient for lifestyle and food | #FFB347→#FF5E62 (11.0:1 and 6.6:1 on #0B0B12) [8] |
| `gradient-word-captions.sweep-fill` | Gradient wipes left to right across the word over its duration | background-size 200% → position sweep from 100% to 0% over word duration, linear; inactive part #FFF [20][23] |

## Timing and numbers
- Page entrance: box scale 0.9 to 1 over 8 frames with elastic.out(1, 0.6) (a damped version of GSAP's default period 0.3) [19].
- Optional shimmer: animate background-position across 200% width over 2 s per cycle, ease none; luminance change stays well under the 10% flash threshold [9].
- Shared baseline for every caption look:
  - Frame maths at 30 fps: 1 frame = 33 ms; 4 f = 133 ms; 6 f = 200 ms; 8 f = 267 ms; 12 f = 400 ms.
  - Reading baseline: 160-180 wpm = 0.33-0.375 s per word; adult ceiling 20 characters/s [1][4]. At 180 wpm a word lasts ~10 frames, so any per-word animation must finish inside ~6 frames.
  - Sync: change the active word 1-2 frames before its audio onset. Picture-early is undetectable up to ~125 ms, picture-late is detectable from ~45 ms (ITU-R BT.1359) [15]. Caption blocks go up on the first audio frame or within 1-2 frames [3].
  - 9:16 safe box (1080x1920), worst case of the platforms' ad specs: top 288 px (15%), bottom 672 px (35%), left 120 px, right 192 px; keep the caption block inside x 120-888, y 288-1248. Centred captions: max width 696 px (64% W) so both edges clear 192 px [10][11][13]. TikTok sizes its zone by ratio and ad-caption length, so treat these as minimums [12]. Organic-only posts can go lower: nothing important in the bottom 20% or right 15% [39].
  - 16:9: keep captions inside the central 90% vertically and 75% horizontally; a line is at most 68% of the width [4].
  - Contrast: >= 4.5:1 for text and its immediate background; 3:1 is the floor only for large text [8].
  - Final check: watch a render on a phone at arm's length; if you have to focus to read, go bigger. Keep >= 60 px from the frame edges [44].

## Build it
1. Start from HyperFrames `caption-gradient-fill` for the page entrance [45].
2. Word span CSS when active: `background:linear-gradient(100deg,#5AA9FF,#FF5EDB); -webkit-background-clip:text; background-clip:text; color:transparent; text-shadow:none` [23].
3. Toggle the active class (or set the four properties) with `tl.set` at word.start - 1/30; never transition `color` to transparent (it fades through grey).
4. For the sweep preset, tween `backgroundPosition` from '100% 0' to '0% 0' over the word's duration with ease 'none'.

## Mistakes that look amateur
- Gradient on the whole line → colours restart per line and look broken [21].
- Gradient text with a text-shadow → the shadow shows through the transparent glyph [23].
- Dark-to-dark gradient ends (navy→purple) → fails contrast on the dark box [8].
- Fast rainbow cycling → flashing risk and noise [9].

## Sources
[1] Netflix (Netflix partner help (style guide owner)) — English (USA) Timed Text Style Guide — https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-USA-Timed-Text-Style-Guide — 42 characters per line, max 2 lines, 20 cps adults / 17 cps children, line-break rules, italics rules
[3] Netflix (Netflix partner help) — Timed Text Style Guide: Subtitle Timing Guidelines — https://partnerhelp.netflixstudios.com/hc/en-us/articles/360051554394-Timed-Text-Style-Guide-Subtitle-Timing-Guidelines — in-time on the first audio frame or within 1-2 frames, 2-frame minimum gap, close gaps under 0.5 s, out-time 0.5 s after audio, shot-change rules
[4] BBC (BBC accessibility team (UK public broadcaster)) — BBC Subtitle Guidelines — https://www.bbc.co.uk/accessibility/forproducts/guides/subtitles/ — 160-180 wpm (0.33-0.375 s/word), line height 7-8% of height (16:9) and 3.9-4.5% (9:16), font ~3.5% of height for 9:16, 68%/90% line width, 2 lines (3 for 9:16), per-line background with 0.5 em padding, white/yellow/cyan/green on black, 9:16 captions a little higher in the lower third, sync and lag limits, lyrics rules
[8] W3C WAI (World Wide Web Consortium accessibility standard) — Understanding WCAG 2.2 SC 1.4.3 Contrast (Minimum) — https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html — 4.5:1 normal text, 3:1 large text (18 pt / 14 pt bold); ratios are not rounded. We used its formula to compute every colour pair in the presets
[9] W3C WAI (World Wide Web Consortium) — Understanding WCAG 2.2 SC 2.3.1 Three Flashes or Below Threshold — https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html — no more than 3 flashes in any 1 s; a flash is a 10% relative-luminance swing
[10] Meta (Meta Ads Guide (platform spec)) — Instagram Reels video ad specs — https://www.facebook.com/business/ads-guide/update/video/instagram-reels — keep 14% top, 35% bottom and 6% each side free of text
[11] Socialync (safe-zone tool that compiles the platforms' published ad margins) — Social media safe zones — https://www.socialync.io/tools/safe-zones — 1080x1920 margins: TikTok 240/660/120/120, Reels 269/672/65/65, Shorts 288/672/48/192 (top/bottom/left/right), all ad specs
[12] TikTok (TikTok Ads help (platform spec)) — TikTok Auction In-Feed Ads — https://ads.tiktok.com/help/article/tiktok-auction-in-feed-ads?lang=en — safe zone depends on ratio, ad caption length and extra formats; published as downloadable files
[13] Google (Google Ads help (platform spec)) — Safe zones for vertical video ads on YouTube — https://support.google.com/google-ads/answer/9128498?hl=en — 1080x1920 safe-zone image with pixel margins (values read via [11])
[15] Randy Hoffner / ITU-R BT.1359 (broadcast engineering columnist, TV Technology) — AV synchronization: how bad is bad? — https://www.tvtechnology.com/opinions/av-synchronization-how-bad-is-bad — ITU-R BT.1359 detectability about +45 ms (sound early) to -125 ms (sound late); people tolerate picture-before-sound far more than sound-before-picture
[19] GreenSock (GSAP) (GSAP docs and source) — Eases docs + gsap-core.js 3.12.5 — https://gsap.com/docs/v3/Eases/ — default ease power1.out; back overshoot default 1.70158; elastic.out default amplitude 1, period 0.3 (source: https://unpkg.com/gsap@3.12.5/src/gsap-core.js)
[20] Aegisub (the standard open-source subtitle/karaoke editor) — ASS override tags — https://aegisub.org/docs/latest/ass_tags/ — \k instant fill, \kf sweep fill over the syllable duration (centiseconds), \ko outline reveal, \bord/\shad in px, \blur, animate \fscx/\fscy with \t instead of \fs
[21] MDN (Mozilla web docs) — box-decoration-break — https://developer.mozilla.org/en-US/docs/Web/CSS/box-decoration-break — clone gives every wrapped line its own padding, radius, shadow and background
[23] MDN (Mozilla web docs) — background-clip — https://developer.mozilla.org/en-US/docs/Web/CSS/background-clip — background-clip: text + color: transparent + text-shadow: none for gradient text, with a solid-colour fallback
[39] @wayofzorro (Zorro) (Shorts channel operator; checklist post had 6.4k likes, 8.6k bookmarks) — Shorts production checklist — https://x.com/wayofzorro/status/2105523352261542050 — large word-by-word captions inside the safe zone; nothing important in the bottom 20% or right 15%; captions perfectly synced; lock fonts and layout in a master project
[44] Derek Coleman (OpusClip) (senior growth marketer at a short-form clipping company) — Video caption design and placement — https://www.opus.pro/blog/video-caption-design-placement — middle 80% of width, at least 60 px from edges, accent backgrounds at 70-80% opacity, 2-frame gaps, test on a phone at arm's length
[45] HeyGen HyperFrames registry (open-source HTML-to-video framework) — Caption components (registry-item.json descriptions) — https://github.com/heygen-com/hyperframes/tree/main/registry/components — ready blocks: caption-highlight, caption-pill-karaoke, caption-gradient-fill, caption-neon-glow, caption-editorial-emphasis, caption-weight-shift, caption-kinetic-slam, caption-clip-wipe, per-word-rise, per-word-crossfade

_TikTok, YouTube, Instagram and Meta are named only to describe their published safe zones; their names, logos and interfaces are trademarks of their owners. Fonts are OFL-1.1 (free for commercial video, no attribution needed) [27]._
