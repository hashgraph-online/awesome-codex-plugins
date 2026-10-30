# Karaoke fill captions

Each word fills with yellow as it is sung or spoken, with a short bar under the current word. Lyric clips, music promos, sing-alongs and rhythmic voice-overs; 16:9 and 9:16; one lyric line per caption.

Fonts: Poppins (OFL-1.1), Montserrat (OFL-1.1). Formats: 16:9, 9:16, 1:1.

## How the pros do it
- Use a sweep fill that runs across the syllable's duration (\kf), or an instant fill (\k) for speech; the karaoke-standard tool times both in centiseconds per syllable [20].
- Fill timing: start the fill at the word onset minus 1 frame and let it finish at the word's end; it follows the voice. A fill that runs >125 ms ahead looks like it anticipates, one 45 ms behind looks late [15].
- Show the whole line before the first word, but never more than 1.5 s ahead of the voice [4].
- Keep song lines intact and in sync with the singing; a 15 s sung line stays 15 s on screen [4].
- Centre lyric lines; mark lyrics with a music note symbol at the start, and at the end of the last line [4].
- Yellow #FFE600 on a black outline is 16.6:1; the BBC lists yellow on black as a standard caption colour [4][8].
- Karaoke highlighting is not an accessible default: some caption-dependent viewers follow the moving fill instead of the meaning [31].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `karaoke-fill-captions.classic-yellow` | White text, yellow wipe per word, underline under the current word | Poppins 800, 16:9 64 px / 9:16 84 px; base #FFF, fill #FFE600, stroke 8 px #000 behind; underline 0.08em #FFE600 at baseline+0.14em; line pre-roll 15 f; fill starts onset-1 f, linear over word [4][8][15][20] |
| `karaoke-fill-captions.two-line-preview` | Current line plus next line dimmed underneath | current line 100%; next line 55% opacity, 85% size; next line promotes up 8 f emphasized when current ends [4][18] |
| `karaoke-fill-captions.speech-instant` | Whole word turns yellow at onset, for spoken voice-over | fill_mode instant (\k), switch onset-1 f, no underline [15][20] |

## Timing and numbers
- Lead or follow? The line leads (appears 0.3-0.7 s early, 10-20 frames, never > 1.5 s); the fill follows the voice (starts 1 frame early, ends with the word) [4][15].
- Sweep speed equals word duration; for held notes the sweep slows naturally, which is the point of the look [4][20].
- Underline slides between words in 4 frames with Material emphasized easing [18].
- At least 2 frames gap between lines; close gaps under 0.5 s [3].
- Shared baseline for every caption look:
  - Frame maths at 30 fps: 1 frame = 33 ms; 4 f = 133 ms; 6 f = 200 ms; 8 f = 267 ms; 12 f = 400 ms.
  - Reading baseline: 160-180 wpm = 0.33-0.375 s per word; adult ceiling 20 characters/s [1][4]. At 180 wpm a word lasts ~10 frames, so any per-word animation must finish inside ~6 frames.
  - Sync: change the active word 1-2 frames before its audio onset. Picture-early is undetectable up to ~125 ms, picture-late is detectable from ~45 ms (ITU-R BT.1359) [15]. Caption blocks go up on the first audio frame or within 1-2 frames [3].
  - 9:16 safe box (1080x1920), worst case of the platforms' ad specs: top 288 px (15%), bottom 672 px (35%), left 120 px, right 192 px; keep the caption block inside x 120-888, y 288-1248. Centred captions: max width 696 px (64% W) so both edges clear 192 px [10][11][13]. TikTok sizes its zone by ratio and ad-caption length, so treat these as minimums [12]. Organic-only posts can go lower: nothing important in the bottom 20% or right 15% [39].
  - 16:9: keep captions inside the central 90% vertically and 75% horizontally; a line is at most 68% of the width [4].
  - Contrast: >= 4.5:1 for text and its immediate background; 3:1 is the floor only for large text [8].
  - Final check: watch a render on a phone at arm's length; if you have to focus to read, go bigger. Keep >= 60 px from the frame edges [44].

## Build it
1. Get word (or syllable) timings: forced alignment of lyrics to the vocal stem (WhisperX alignment on the separated vocal) beats raw ASR on sung audio.
2. HTML: each word is two layers: base white text, and an overlay copy in yellow clipped with `clip-path: inset(0 X% 0 0)`; tween X from 100 to 0 over the word duration with ease 'none'.
3. Underline: a single div; `tl.to(bar,{x, width, duration:4/30}, word.start-1/30)`.
4. ASS/ffmpeg: `Dialogue: ... ,{\kf45}Hold {\kf30}me {\kf80}close` with PrimaryColour=yellow, SecondaryColour=white; burn with `subtitles=lyrics.ass` [20].

## Mistakes that look amateur
- Fill keyed to line start with an even split per word → drifts off the singing within 2-3 words; use real word timings.
- Line appearing 3 s early → reads like a spoiler and fights the previous line [4].
- Editing lyrics for length → keep lines whole; song lyrics are captioned verbatim [4][5].
- Yellow fill without outline on bright footage → #FFE600 on white is near invisible; keep the black stroke [8].
- Using sweep for fast speech → 6-frame sweeps flicker; use the instant preset.

## Sources
[1] Netflix (Netflix partner help (style guide owner)) — English (USA) Timed Text Style Guide — https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-USA-Timed-Text-Style-Guide — 42 characters per line, max 2 lines, 20 cps adults / 17 cps children, line-break rules, italics rules
[3] Netflix (Netflix partner help) — Timed Text Style Guide: Subtitle Timing Guidelines — https://partnerhelp.netflixstudios.com/hc/en-us/articles/360051554394-Timed-Text-Style-Guide-Subtitle-Timing-Guidelines — in-time on the first audio frame or within 1-2 frames, 2-frame minimum gap, close gaps under 0.5 s, out-time 0.5 s after audio, shot-change rules
[4] BBC (BBC accessibility team (UK public broadcaster)) — BBC Subtitle Guidelines — https://www.bbc.co.uk/accessibility/forproducts/guides/subtitles/ — 160-180 wpm (0.33-0.375 s/word), line height 7-8% of height (16:9) and 3.9-4.5% (9:16), font ~3.5% of height for 9:16, 68%/90% line width, 2 lines (3 for 9:16), per-line background with 0.5 em padding, white/yellow/cyan/green on black, 9:16 captions a little higher in the lower third, sync and lag limits, lyrics rules
[5] DCMP (Described and Captioned Media Program (US Dept. of Education funded)) — Captioning Key: Presentation Rate — https://dcmp.org/learn/601-captioning-key---presentation-rate — 130/140/160 wpm ceilings by audience level; borrowing up to 15 frames around the audio is hardly noticed
[8] W3C WAI (World Wide Web Consortium accessibility standard) — Understanding WCAG 2.2 SC 1.4.3 Contrast (Minimum) — https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html — 4.5:1 normal text, 3:1 large text (18 pt / 14 pt bold); ratios are not rounded. We used its formula to compute every colour pair in the presets
[10] Meta (Meta Ads Guide (platform spec)) — Instagram Reels video ad specs — https://www.facebook.com/business/ads-guide/update/video/instagram-reels — keep 14% top, 35% bottom and 6% each side free of text
[11] Socialync (safe-zone tool that compiles the platforms' published ad margins) — Social media safe zones — https://www.socialync.io/tools/safe-zones — 1080x1920 margins: TikTok 240/660/120/120, Reels 269/672/65/65, Shorts 288/672/48/192 (top/bottom/left/right), all ad specs
[12] TikTok (TikTok Ads help (platform spec)) — TikTok Auction In-Feed Ads — https://ads.tiktok.com/help/article/tiktok-auction-in-feed-ads?lang=en — safe zone depends on ratio, ad caption length and extra formats; published as downloadable files
[13] Google (Google Ads help (platform spec)) — Safe zones for vertical video ads on YouTube — https://support.google.com/google-ads/answer/9128498?hl=en — 1080x1920 safe-zone image with pixel margins (values read via [11])
[15] Randy Hoffner / ITU-R BT.1359 (broadcast engineering columnist, TV Technology) — AV synchronization: how bad is bad? — https://www.tvtechnology.com/opinions/av-synchronization-how-bad-is-bad — ITU-R BT.1359 detectability about +45 ms (sound early) to -125 ms (sound late); people tolerate picture-before-sound far more than sound-before-picture
[18] Google Material Design 3 (Material motion tokens, Apache-2.0 source) — md-sys-motion tokens (material-web) — https://github.com/material-components/material-web/blob/main/tokens/versions/v0_192/_md-sys-motion.scss — durations short1-4 = 50/100/150/200 ms, medium1-4 = 250-400 ms; emphasized cubic-bezier(0.2,0,0,1), emphasized-decelerate (0.05,0.7,0.1,1), emphasized-accelerate (0.3,0,0.8,0.15)
[20] Aegisub (the standard open-source subtitle/karaoke editor) — ASS override tags — https://aegisub.org/docs/latest/ass_tags/ — \k instant fill, \kf sweep fill over the syllable duration (centiseconds), \ko outline reveal, \bord/\shad in px, \blur, animate \fscx/\fscy with \t instead of \fs
[31] @merylkevans (Meryl Evans) (deaf accessibility advocate) — Reply: karaoke-style captions — https://x.com/merylkevans/status/1821233367712711088 — eyes follow the highlighted word instead of comprehending the text
[39] @wayofzorro (Zorro) (Shorts channel operator; checklist post had 6.4k likes, 8.6k bookmarks) — Shorts production checklist — https://x.com/wayofzorro/status/2105523352261542050 — large word-by-word captions inside the safe zone; nothing important in the bottom 20% or right 15%; captions perfectly synced; lock fonts and layout in a master project
[44] Derek Coleman (OpusClip) (senior growth marketer at a short-form clipping company) — Video caption design and placement — https://www.opus.pro/blog/video-caption-design-placement — middle 80% of width, at least 60 px from edges, accent backgrounds at 70-80% opacity, 2-frame gaps, test on a phone at arm's length

_TikTok, YouTube, Instagram and Meta are named only to describe their published safe zones; their names, logos and interfaces are trademarks of their owners. Fonts are OFL-1.1 (free for commercial video, no attribution needed) [27]._
