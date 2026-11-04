# Shadow-only minimal captions

White text with a soft shadow and no box; the spoken word is just a little brighter than the rest. Cinematic vlogs, travel, aesthetic brand films and calm podcasts; 16:9 and 9:16; one phrase per caption.

Fonts: Inter (OFL-1.1), Figtree (OFL-1.1). Formats: 16:9, 9:16, 1:1.

## How the pros do it
- Without a box, legibility comes from the shadow: use a drop or rim shadow on medium-weight sans serif [6].
- Boxless white text fails on bright frames; caption-dependent viewers prefer a dark box, so use this look only over controlled, mid-to-dark footage [28].
- When the background is bright, add a ~35% dark dimming layer behind the text area [25].
- Make the active difference small but visible: inactive white at 80% opacity, active at 100% [8].
- Phrase-based captions, 1-2 lines, bottom placement; in 9:16 a little higher in the lower third [4].
- Time by reading speed, not by word rhythm (160-180 wpm) [4].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `shadow-minimal-captions.soft-shadow` | Inter 600 white, 3-layer shadow, active 100% vs 80% | 9:16 76 px (4% H) / 16:9 60 px (5.6% H); shadow 0 0 2px rgba(0,0,0,.9), 0 2px 8px rgba(0,0,0,.6), 0 0 24px rgba(0,0,0,.35); inactive opacity .8 [4][6][8] |
| `shadow-minimal-captions.cinema-lower` | 16:9 film subtitle feel, smaller, wider tracking | 16:9: 52 px (4.8% H), tracking .01em, bottom 7% H, max line 68% W [4] |
| `shadow-minimal-captions.bright-guard` | Adds a soft gradient dim when the caption area is bright | if mean luma in caption box > 0.55: gradient rgba(0,0,0,.35)→0 over 30% H from bottom [25] |

## Timing and numbers
- Caption in/out: 3-frame opacity fade at most; active brightness change 2 frames [18].
- Shadow sizes scale with type: blur ~0.1 em and ~0.3 em; offsets <= 0.03 em.
- Shared baseline for every caption look:
  - Frame maths at 30 fps: 1 frame = 33 ms; 4 f = 133 ms; 6 f = 200 ms; 8 f = 267 ms; 12 f = 400 ms.
  - Reading baseline: 160-180 wpm = 0.33-0.375 s per word; adult ceiling 20 characters/s [1][4]. At 180 wpm a word lasts ~10 frames, so any per-word animation must finish inside ~6 frames.
  - Sync: change the active word 1-2 frames before its audio onset. Picture-early is undetectable up to ~125 ms, picture-late is detectable from ~45 ms (ITU-R BT.1359) [15]. Caption blocks go up on the first audio frame or within 1-2 frames [3].
  - 9:16 safe box (1080x1920), worst case of the platforms' ad specs: top 288 px (15%), bottom 672 px (35%), left 120 px, right 192 px; keep the caption block inside x 120-888, y 288-1248. Centred captions: max width 696 px (64% W) so both edges clear 192 px [10][11][13]. TikTok sizes its zone by ratio and ad-caption length, so treat these as minimums [12]. Organic-only posts can go lower: nothing important in the bottom 20% or right 15% [39].
  - 16:9: keep captions inside the central 90% vertically and 75% horizontally; a line is at most 68% of the width [4].
  - Contrast: >= 4.5:1 for text and its immediate background; 3:1 is the floor only for large text [8].
  - Final check: watch a render on a phone at arm's length; if you have to focus to read, go bigger. Keep >= 60 px from the frame edges [44].

## Build it
1. Measure caption-area luminance per shot (ffmpeg `signalstats` on a crop, or sample the frame in a pre-pass) and switch to the bright-guard preset per shot, not per frame.
2. Use `opacity` on word spans for inactive/active rather than grey colours so the shadow dims with the text consistently.
3. ASS/ffmpeg: `BorderStyle=1, Outline=1, Shadow=2, BackColour=&H80000000`, plus `\blur3` for a soft shadow edge [20].

## Mistakes that look amateur
- Boxless white text over snow, sky or a white kitchen → unreadable; use the guard or a box look [25][28].
- Hard 1 px black shadow only → looks like 2000s DVD subtitles; use the soft 3-layer stack.
- Active word in a colour → breaks the minimal look; brightness only.
- Shadow radius tuned at 1080p and reused at 4K → too thin; size in em.

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
[28] Meryl K. Evans (deaf accessibility advocate and CPACC, writes caption guides) — Why captioned videos are important — https://meryl.net/why-captioned-videos-are-important/ — one colour, no word highlighting, no 1-2 word captions, 1-2 lines (~60 chars), off-black #242424 box with off-white text, bottom placement, sentence case, minimal motion
[39] @wayofzorro (Zorro) (Shorts channel operator; checklist post had 6.4k likes, 8.6k bookmarks) — Shorts production checklist — https://x.com/wayofzorro/status/2105523352261542050 — large word-by-word captions inside the safe zone; nothing important in the bottom 20% or right 15%; captions perfectly synced; lock fonts and layout in a master project
[44] Derek Coleman (OpusClip) (senior growth marketer at a short-form clipping company) — Video caption design and placement — https://www.opus.pro/blog/video-caption-design-placement — middle 80% of width, at least 60 px from edges, accent backgrounds at 70-80% opacity, 2-frame gaps, test on a phone at arm's length

_TikTok, YouTube, Instagram and Meta are named only to describe their published safe zones; their names, logos and interfaces are trademarks of their owners. Fonts are OFL-1.1 (free for commercial video, no attribution needed) [27]._
