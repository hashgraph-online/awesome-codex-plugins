# Neon tube captions

Words glow like neon tubes (hot pink by default) inside a dark box with a glowing border. Nightlife, music, gaming, event promos and retro edits; 9:16 and 1:1; 2-4 words per page.

Fonts: Nunito (OFL-1.1), Outfit (OFL-1.1). Formats: 9:16, 1:1, 16:9.

## How the pros do it
- Build the glow from a stack of zero-offset shadows: a tight white core (7, 10, 21 px) under a coloured halo (42, 82, 92, 102, 151 px); one shadow looks flat [26].
- Scale those radii to your type: at 84 px caption type use roughly 0.08/0.12/0.25 em white and 0.5/1.0/1.2 em colour.
- Keep the glyph fill near-white (#FFE6F7) so the core reads hot; the colour lives in the halo. #FF4FD8 on #0B0B12 is 6.9:1 [8][26].
- If it flickers, flicker one word or one moment, and never more than 3 flashes in a second [9][26].
- Prefer the slow pulse variant (glow radius grows and shrinks) over flicker for anything longer than a beat [26].
- Use an OFL rounded face such as Nunito (rounded terminals read as bent tubes) at weight >= 800 so the core stays legible inside the halo [27][46].
- Active word: increase halo intensity rather than changing colour, so the palette stays two-tone [28].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `neon-tube-captions.hot-pink` | Pink halo, near-white core, pink border box | Nunito 900, 84 px; fill #FFE6F7; inactive shadow 0 0 .06em #fff,0 0 .3em #FF4FD8,0 0 .7em #FF4FD8; active adds 0 0 1.2em #FF4FD8,0 0 1.8em #FF4FD8; box #0B0B12 85% border 3 px #FF4FD8 glow 0 0 24px #FF4FD8 [8][26] |
| `neon-tube-captions.cyan-ice` | Cyan halo for tech/gaming | halo #00FFFF (16.8:1 on black), fill #E6FFFF, border #00FFFF [4][8] |
| `neon-tube-captions.pulse-only` | Halo breathes 1 cycle per 2 s | halo radius ×0.85↔×1.15, period 2 s, sine.inOut; no on/off flashes [9][26] |

## Timing and numbers
- Flicker budget: at most 2 off-frames per flicker event, at most one event per 2 s, and only on page entrance; this stays well below 3 flashes/s [9].
- Neon 'switch-on' entrance: glow opacity 0→0.6 (2 frames) →0.2 (1 frame) →1 (3 frames), then hold.
- Active word: halo intensifies over 3 frames, decays over 4 after the word ends.
- Shared baseline for every caption look:
  - Frame maths at 30 fps: 1 frame = 33 ms; 4 f = 133 ms; 6 f = 200 ms; 8 f = 267 ms; 12 f = 400 ms.
  - Reading baseline: 160-180 wpm = 0.33-0.375 s per word; adult ceiling 20 characters/s [1][4]. At 180 wpm a word lasts ~10 frames, so any per-word animation must finish inside ~6 frames.
  - Sync: change the active word 1-2 frames before its audio onset. Picture-early is undetectable up to ~125 ms, picture-late is detectable from ~45 ms (ITU-R BT.1359) [15]. Caption blocks go up on the first audio frame or within 1-2 frames [3].
  - 9:16 safe box (1080x1920), worst case of the platforms' ad specs: top 288 px (15%), bottom 672 px (35%), left 120 px, right 192 px; keep the caption block inside x 120-888, y 288-1248. Centred captions: max width 696 px (64% W) so both edges clear 192 px [10][11][13]. TikTok sizes its zone by ratio and ad-caption length, so treat these as minimums [12]. Organic-only posts can go lower: nothing important in the bottom 20% or right 15% [39].
  - 16:9: keep captions inside the central 90% vertically and 75% horizontally; a line is at most 68% of the width [4].
  - Contrast: >= 4.5:1 for text and its immediate background; 3:1 is the floor only for large text [8].
  - Final check: watch a render on a phone at arm's length; if you have to focus to read, go bigger. Keep >= 60 px from the frame edges [44].

## Build it
1. Start from HyperFrames `caption-neon-glow` or `caption-neon-accent` [45].
2. Keep the many-layer text-shadow only on the active word; inactive words use 3 layers. Big blur radii on every word slow down headless renders.
3. Drive the pulse from timeline time (`Math.sin(2*Math.PI*t/2)`) so the render is seek-safe.
4. Footage version with ffmpeg: render the text layer as RGBA PNG/ProRes 4444 from HTML, then `overlay`; do not try to build the glow with drawtext.

## Mistakes that look amateur
- Pink-on-pink: coloured glyph fill plus coloured halo → no core, unreadable; keep the fill near-white [26].
- Random flicker throughout → flash risk and fatigue [9].
- Thin font weight → the halo eats the letters; >= 800.
- Glow halos clipped by `overflow:hidden` on the box → give the text layer room or let the box overflow visible.

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
[26] Silvia O'Dwyer (CSS-Tricks) (front-end developer and writer) — How to Create Neon Text With CSS — https://css-tricks.com/how-to-create-neon-text-with-css/ — white inner glow 7/10/21 px + coloured outer glow 42/82/92/102/151 px; flicker by dropping the shadow at a few keyframes; subtle pulse variant
[27] SIL Open Font License (OFL FAQ) — OFL-FAQ — https://openfontlicense.org/ofl-faq/ — OFL fonts may be used in commercial video and graphics, no attribution required
[28] Meryl K. Evans (deaf accessibility advocate and CPACC, writes caption guides) — Why captioned videos are important — https://meryl.net/why-captioned-videos-are-important/ — one colour, no word highlighting, no 1-2 word captions, 1-2 lines (~60 chars), off-black #242424 box with off-white text, bottom placement, sentence case, minimal motion
[39] @wayofzorro (Zorro) (Shorts channel operator; checklist post had 6.4k likes, 8.6k bookmarks) — Shorts production checklist — https://x.com/wayofzorro/status/2105523352261542050 — large word-by-word captions inside the safe zone; nothing important in the bottom 20% or right 15%; captions perfectly synced; lock fonts and layout in a master project
[44] Derek Coleman (OpusClip) (senior growth marketer at a short-form clipping company) — Video caption design and placement — https://www.opus.pro/blog/video-caption-design-placement — middle 80% of width, at least 60 px from edges, accent backgrounds at 70-80% opacity, 2-frame gaps, test on a phone at arm's length
[45] HeyGen HyperFrames registry (open-source HTML-to-video framework) — Caption components (registry-item.json descriptions) — https://github.com/heygen-com/hyperframes/tree/main/registry/components — ready blocks: caption-highlight, caption-pill-karaoke, caption-gradient-fill, caption-neon-glow, caption-editorial-emphasis, caption-weight-shift, caption-kinetic-slam, caption-clip-wipe, per-word-rise, per-word-crossfade
[46] Google Fonts (google/fonts repository (license folders)) — google/fonts — https://github.com/google/fonts — verified licence folders: ofl/ for Inter, Montserrat, Poppins, Anton, Bebas Neue, Archivo Black, Figtree, Plus Jakarta Sans, Instrument Serif, Playfair Display, Fraunces, Nunito, Manrope, Atkinson Hyperlegible, Outfit

_TikTok, YouTube, Instagram and Meta are named only to describe their published safe zones; their names, logos and interfaces are trademarks of their owners. Fonts are OFL-1.1 (free for commercial video, no attribution needed) [27]._
