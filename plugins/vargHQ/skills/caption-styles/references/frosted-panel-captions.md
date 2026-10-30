# Frosted panel captions

White text on a blurred, frosted-glass panel; inactive words are dimmed and the spoken word is full white. Tech, product, lifestyle and app-launch videos over rich footage; 9:16, 1:1, 16:9; 3-6 words per panel.

Fonts: Inter (OFL-1.1), Manrope (OFL-1.1). Formats: 9:16, 1:1, 16:9.

## How the pros do it
- backdrop-filter only shows through a translucent background; pair blur() with a semi-transparent fill [22].
- Ancestors with opacity < 1, filter, mask, clip-path or blend modes cut off what the glass can see; keep the panel's parents plain [22].
- Use the thicker/regular material when the element carries text; thicker materials give better contrast [25].
- Over bright media, add a dark dimming layer of about 35% [25].
- 35% is not enough for 4.5:1 over a white frame: white on 12% white tint + 55% dim is only 3.8:1, so add a text shadow and push the dim to 55-65% over bright shots (computed with [8]).
- Dim inactive words with opacity, not grey colour: white at 70-80% on a #1A1A1A panel still gives 9:1 or more; over bright mid-tones a 45% tint drops to about 4:1, so raise the tint or use the thick preset [8].
- Change the active word at onset minus 1 frame [15].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `frosted-panel-captions.clear-dim` | Blur 20 px, dark 45% tint, white text with soft shadow | panel rgba(18,18,22,.45) + backdrop blur(20px) saturate(140%), border 1px rgba(255,255,255,.22), radius 28 px, pad .4em .6em; inactive white 80%, active 100%, max width 696 px (over bright footage use `thick-bright-footage`) + glow 0 0 18px rgba(255,255,255,.35) [8][15][22][25] |
| `frosted-panel-captions.thick-bright-footage` | Stronger dim and blur for snow, sky, white rooms | panel rgba(12,12,16,.62) + blur(28px) saturate(120%); inactive 75% [8][25] |
| `frosted-panel-captions.light-glass` | Dark text on milky glass for bright, airy brands | panel rgba(255,255,255,.62) + blur(24px); text #0A0A0A; inactive 55% [22][25] |

## Timing and numbers
- Panel entrance: opacity 0→1, scale 0.96→1 and backdrop blur 0→20 px over 8 frames (267 ms) with emphasized-decelerate [18].
- Active word: opacity 0.8→1 over 2 frames; no scale (the panel is already decorative).
- Panel width animates only between pages (6 frames, emphasized), never per word.
- Shared baseline for every caption look:
  - Frame maths at 30 fps: 1 frame = 33 ms; 4 f = 133 ms; 6 f = 200 ms; 8 f = 267 ms; 12 f = 400 ms.
  - Reading baseline: 160-180 wpm = 0.33-0.375 s per word; adult ceiling 20 characters/s [1][4]. At 180 wpm a word lasts ~10 frames, so any per-word animation must finish inside ~6 frames.
  - Sync: change the active word 1-2 frames before its audio onset. Picture-early is undetectable up to ~125 ms, picture-late is detectable from ~45 ms (ITU-R BT.1359) [15]. Caption blocks go up on the first audio frame or within 1-2 frames [3].
  - 9:16 safe box (1080x1920), worst case of the platforms' ad specs: top 288 px (15%), bottom 672 px (35%), left 120 px, right 192 px; keep the caption block inside x 120-888, y 288-1248. Centred captions: max width 696 px (64% W) so both edges clear 192 px [10][11][13]. TikTok sizes its zone by ratio and ad-caption length, so treat these as minimums [12]. Organic-only posts can go lower: nothing important in the bottom 20% or right 15% [39].
  - 16:9: keep captions inside the central 90% vertically and 75% horizontally; a line is at most 68% of the width [4].
  - Contrast: >= 4.5:1 for text and its immediate background; 3:1 is the floor only for large text [8].
  - Final check: watch a render on a phone at arm's length; if you have to focus to read, go bigger. Keep >= 60 px from the frame edges [44].

## Build it
1. HTML: `<div class=panel>` with words; CSS `background:rgba(18,18,22,.45); backdrop-filter:blur(20px) saturate(140%); -webkit-backdrop-filter:...; border:1px solid rgba(255,255,255,.22); border-radius:28px` [22].
2. Keep the panel in a layer without opacity/filter ancestors; animate the panel's own opacity, not its parent's [22].
3. Headless Chrome renders backdrop-filter; test one frame before a full render.
4. ffmpeg path over real footage: `[0:v]crop=W:H:X:Y,boxblur=20:2,eq=brightness=-0.12[glass];[0:v][glass]overlay=X:Y` then draw the rounded mask with `alphamerge` from a PNG panel, then the text.

## Mistakes that look amateur
- Fully opaque panel with backdrop-filter → no glass visible [22].
- Glass with only 15-20% tint over a sunny sky → text washes out; use the thick preset [25].
- Parent wrapper faded with opacity → backdrop blur disappears [22].
- Inactive words in mid-grey #808080 → muddy on glass; use white with opacity [8].

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
[18] Google Material Design 3 (Material motion tokens, Apache-2.0 source) — md-sys-motion tokens (material-web) — https://github.com/material-components/material-web/blob/main/tokens/versions/v0_192/_md-sys-motion.scss — durations short1-4 = 50/100/150/200 ms, medium1-4 = 250-400 ms; emphasized cubic-bezier(0.2,0,0,1), emphasized-decelerate (0.05,0.7,0.1,1), emphasized-accelerate (0.3,0,0.8,0.15)
[22] MDN (Mozilla web docs) — backdrop-filter — https://developer.mozilla.org/en-US/docs/Web/CSS/backdrop-filter — needs a translucent background; blur()/saturate()/brightness(); ancestors with opacity, filter, mask or blend mode cut off the backdrop
[25] Apple (Apple Human Interface Guidelines) — Materials — https://developer.apple.com/design/human-interface-guidelines/materials — regular (thicker) glass for text-heavy elements; clear glass over bright media needs a ~35% dark dimming layer; thicker materials give better contrast
[39] @wayofzorro (Zorro) (Shorts channel operator; checklist post had 6.4k likes, 8.6k bookmarks) — Shorts production checklist — https://x.com/wayofzorro/status/2105523352261542050 — large word-by-word captions inside the safe zone; nothing important in the bottom 20% or right 15%; captions perfectly synced; lock fonts and layout in a master project
[44] Derek Coleman (OpusClip) (senior growth marketer at a short-form clipping company) — Video caption design and placement — https://www.opus.pro/blog/video-caption-design-placement — middle 80% of width, at least 60 px from edges, accent backgrounds at 70-80% opacity, 2-frame gaps, test on a phone at arm's length

_TikTok, YouTube, Instagram and Meta are named only to describe their published safe zones; their names, logos and interfaces are trademarks of their owners. Fonts are OFL-1.1 (free for commercial video, no attribution needed) [27]._
