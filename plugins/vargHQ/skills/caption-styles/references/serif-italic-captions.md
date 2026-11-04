# Serif italic emphasis captions

Large serif text with a soft shadow and no box; the spoken word flips to italic. A magazine/editorial voice for documentaries, essays, luxury and fashion, narration-led reels; 16:9 and 9:16; short lines.

Fonts: Instrument Serif (OFL-1.1), Playfair Display (OFL-1.1), Fraunces (OFL-1.1). Formats: 16:9, 9:16, 1:1.

## How the pros do it
- Italics carry meaning in subtitling (narration, emphasis, off-screen voices), so the italic swap reads as emphasis; it fits narration and voice-over best [1].
- Italic is for a word or two, never whole paragraphs [33].
- Caption guides default to sans serif; serif captions need larger sizes and short lines to stay legible on phones [6][28].
- Without a box, add a drop or rim shadow so text survives bright frames [6].
- Serif roman and italic widths differ; animate the swap without reflow (stacked spans or reserved width) [20].
- Keep 1-2 lines and phrase-level breaks [1][4].
- Use OFL serifs with a true italic: Instrument Serif, Playfair Display and Fraunces all ship italics [27][46].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `serif-italic-captions.instrument-italic` | Instrument Serif 400, spoken word italic, soft shadow | 9:16: 96 px (5% H); 16:9: 72 px (6.7% H); shadow 0 2px 12px rgba(0,0,0,.55), 0 0 2px rgba(0,0,0,.6); 4-7 words, 2 lines; italic swap 3 f crossfade [1][6][15] |
| `serif-italic-captions.playfair-warm` | Playfair Display with warm ivory text for luxury | text #FFF8EC, italic active, line-height 1.1, tracking -0.01em [46] |
| `serif-italic-captions.fraunces-soft` | Fraunces with SOFT axis for a friendlier editorial voice | Fraunces opsz 72, SOFT 50, wght 400 → active italic wght 500 [46] |

## Timing and numbers
- Italic swap: crossfade roman→italic copies over 3 frames (100 ms); a hard cut also works for staccato edits [18].
- Page entrance (optional): per-word rise of 0.15 em with blur 4 px→0 over 8 frames, staggered 2 frames, the 'per-word-rise' pattern [45].
- Shadow scales with type: blur ~0.12 em, y offset ~0.02 em.
- Shared baseline for every caption look:
  - Frame maths at 30 fps: 1 frame = 33 ms; 4 f = 133 ms; 6 f = 200 ms; 8 f = 267 ms; 12 f = 400 ms.
  - Reading baseline: 160-180 wpm = 0.33-0.375 s per word; adult ceiling 20 characters/s [1][4]. At 180 wpm a word lasts ~10 frames, so any per-word animation must finish inside ~6 frames.
  - Sync: change the active word 1-2 frames before its audio onset. Picture-early is undetectable up to ~125 ms, picture-late is detectable from ~45 ms (ITU-R BT.1359) [15]. Caption blocks go up on the first audio frame or within 1-2 frames [3].
  - 9:16 safe box (1080x1920), worst case of the platforms' ad specs: top 288 px (15%), bottom 672 px (35%), left 120 px, right 192 px; keep the caption block inside x 120-888, y 288-1248. Centred captions: max width 696 px (64% W) so both edges clear 192 px [10][11][13]. TikTok sizes its zone by ratio and ad-caption length, so treat these as minimums [12]. Organic-only posts can go lower: nothing important in the bottom 20% or right 15% [39].
  - 16:9: keep captions inside the central 90% vertically and 75% horizontally; a line is at most 68% of the width [4].
  - Contrast: >= 4.5:1 for text and its immediate background; 3:1 is the floor only for large text [8].
  - Final check: watch a render on a phone at arm's length; if you have to focus to read, go bigger. Keep >= 60 px from the frame edges [44].

## Build it
1. Start from HyperFrames `caption-editorial-emphasis` (dual-font emphasis) or `caption-weight-shift` [45].
2. For each word render two absolutely stacked spans (roman, italic) inside a wrapper whose width is max(roman, italic) measured once; crossfade opacity on activation so neighbours never move.
3. Load the italic file explicitly (Google Fonts `ital@0;1`) and wait for `document.fonts.ready` before measuring.

## Mistakes that look amateur
- Faux italic (browser-slanted roman) because the italic file wasn't loaded → load ital=1 [46].
- Small serif (<4% H on 9:16) with thin hairlines over busy footage → bigger, or add a 35% gradient dim behind [25].
- Every word italic in turn on a 60 s clip → italics lose meaning; use on narration or on stressed words only [33].
- Reflow when the word turns italic → reserved-width stacked spans.

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
[18] Google Material Design 3 (Material motion tokens, Apache-2.0 source) — md-sys-motion tokens (material-web) — https://github.com/material-components/material-web/blob/main/tokens/versions/v0_192/_md-sys-motion.scss — durations short1-4 = 50/100/150/200 ms, medium1-4 = 250-400 ms; emphasized cubic-bezier(0.2,0,0,1), emphasized-decelerate (0.05,0.7,0.1,1), emphasized-accelerate (0.3,0,0.8,0.15)
[20] Aegisub (the standard open-source subtitle/karaoke editor) — ASS override tags — https://aegisub.org/docs/latest/ass_tags/ — \k instant fill, \kf sweep fill over the syllable duration (centiseconds), \ko outline reveal, \bord/\shad in px, \blur, animate \fscx/\fscy with \t instead of \fs
[25] Apple (Apple Human Interface Guidelines) — Materials — https://developer.apple.com/design/human-interface-guidelines/materials — regular (thicker) glass for text-heavy elements; clear glass over bright media needs a ~35% dark dimming layer; thicker materials give better contrast
[27] SIL Open Font License (OFL FAQ) — OFL-FAQ — https://openfontlicense.org/ofl-faq/ — OFL fonts may be used in commercial video and graphics, no attribution required
[28] Meryl K. Evans (deaf accessibility advocate and CPACC, writes caption guides) — Why captioned videos are important — https://meryl.net/why-captioned-videos-are-important/ — one colour, no word highlighting, no 1-2 word captions, 1-2 lines (~60 chars), off-black #242424 box with off-white text, bottom placement, sentence case, minimal motion
[33] @merylkevans (Meryl Evans) (deaf accessibility advocate) — Reply: italics — https://x.com/merylkevans/status/1280899601445400576 — italics are meant for a word or two, nothing more
[39] @wayofzorro (Zorro) (Shorts channel operator; checklist post had 6.4k likes, 8.6k bookmarks) — Shorts production checklist — https://x.com/wayofzorro/status/2105523352261542050 — large word-by-word captions inside the safe zone; nothing important in the bottom 20% or right 15%; captions perfectly synced; lock fonts and layout in a master project
[44] Derek Coleman (OpusClip) (senior growth marketer at a short-form clipping company) — Video caption design and placement — https://www.opus.pro/blog/video-caption-design-placement — middle 80% of width, at least 60 px from edges, accent backgrounds at 70-80% opacity, 2-frame gaps, test on a phone at arm's length
[45] HeyGen HyperFrames registry (open-source HTML-to-video framework) — Caption components (registry-item.json descriptions) — https://github.com/heygen-com/hyperframes/tree/main/registry/components — ready blocks: caption-highlight, caption-pill-karaoke, caption-gradient-fill, caption-neon-glow, caption-editorial-emphasis, caption-weight-shift, caption-kinetic-slam, caption-clip-wipe, per-word-rise, per-word-crossfade
[46] Google Fonts (google/fonts repository (license folders)) — google/fonts — https://github.com/google/fonts — verified licence folders: ofl/ for Inter, Montserrat, Poppins, Anton, Bebas Neue, Archivo Black, Figtree, Plus Jakarta Sans, Instrument Serif, Playfair Display, Fraunces, Nunito, Manrope, Atkinson Hyperlegible, Outfit

_TikTok, YouTube, Instagram and Meta are named only to describe their published safe zones; their names, logos and interfaces are trademarks of their owners. Fonts are OFL-1.1 (free for commercial video, no attribution needed) [27]._
