# Kinetic lyric video

The song's lyrics animate on screen in sync with the vocal, one word, phrase or line at a time. Type does the work of the footage: size, weight and motion carry the emphasis, and the camera moves between phrases. Use it for a single release, a teaser for a chorus, or a social clip of the hook. 9:16 is the default for short-form, 16:9 for YouTube and 1:1 for feed. A typical length is 15–30 s for a hook clip (this preset targets 27 s, about 45 beats at 100 BPM) and the full song for a release.

Use only lyrics and audio the user owns or has licensed. Never reproduce a real artist's official lyric video design.

## How the pros do it
- **Time all the text before you design anything.** Professional lyric-video animators sync every lyric to the track first, then arrange and animate, then add imagery. They plan the piece in 10–15 s segments and get approval at each stage [123].
- **Mark phrases on the waveform, then refine.** Show the waveform and drop a marker at each new phrase [124]. Joey Korenman (School of Motion) taps markers live during playback as a rough pass, puts them on the comp so they survive pre-comps, then fixes them by hand [120]. In code, the transcript's word timestamps are the markers. Correct them against the waveform, not by ear.
- **Animate slightly before the sung word.** When a motion takes time to read, Korenman starts it about 5 frames before the audio and nudges sound-synced hits 2–3 frames earlier so they land with the sound [121][120]. Composer Hans Zimmer, quoted on a filmmakers' forum, says to be a frame ahead of the cut to jolt the audience [106]. Lead: 1–2 frames for hard cuts, 3–5 frames for motion entrances.
- **Short, fast word moves.** Korenman's numbers: word slide-ins over 4–5 frames. A letter swing over 6 frames plus a 2-frame overshoot and settle, starting smaller but not at zero. A snap zoom over 6 frames, a 2-frame hold, then a 1-frame correction. A pull-back over 8 frames on easy ease [121].
- **Contrast in size carries emphasis.** Korenman shrinks a whispered word to about 50% next to the shouted ones and offsets a duplicate in a contrast color by 1 frame to give it a highlight edge [121]. Map vocal intensity to scale: whisper 0.5x, normal 1x, hook word 1.6–2x.
- **One or two lines at a time, big and legible.** Adobe's guide calls 1–2 lines on screen the most natural pace, warns against a whole verse at once, and asks for large letters because a word may only be on screen for a second or two [122].
- **Respect reading speed.** Netflix caps adult subtitles at 20 characters per second, 42 characters per line and two lines. Line breaks go after punctuation and before conjunctions and prepositions, never splitting an article from its noun, and the bottom line is longer [118]. An event lasts at least 20 frames at 24 fps (5/6 s), with a 2-frame gap between events. The in-time sits on the first frame of audio, and with no next line the out-time sits 0.5 s after the audio ends [119].
- **Put the lyric in the world when there's footage.** A viral 2026 AI music video was praised for weaving each lyric into screens, dashboards, road signs and interfaces, so finding the next line became part of watching [125]. With footage, track the text onto surfaces instead of floating it over the image.
- **Match motion to the song's mood.** Pick a typeface and movement style for the artist and track early [123]. A playful face doesn't suit a sad song [122].
- **Finish with a light hand.** Add a small RGB fringe plus a 2-frame chromatic kick on every hard cut and low-opacity grain. If a still looks like a filter, halve every value [126].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `kinetic-lyric-video.word-punch` | One huge word per beat, center frame, alternating entry directions | Anton 22% of frame height. Slide-in 5 frames `expo.out`, lead 2 frames. Hook words 1.8x. Black #0A0A0A / white #F5F5F0 / accent #FF3D2E |
| `kinetic-lyric-video.line-karaoke` | Two lines on screen, the current word lights up as it is sung | Inter 800 at 6.5% of height. Unsung #FFFFFF at 45%, sung #FFFFFF at 100% plus accent underline. Max 24 chars/line |
| `kinetic-lyric-video.ballad-drift` | Serif words fade and drift up softly, wide spacing, slow camera | Instrument Serif 9% of height. Per-word fade 10 frames plus 24 px rise. Camera push 1.0→1.06 per phrase |
| `kinetic-lyric-video.build-and-slam` | The phrase builds word by word from the right, then the hook slams full-screen with a snap zoom | Build 4 frames/word. Snap zoom 6 frames, hold 2, correct 1. Pull-back 8 frames. 1-frame chromatic kick |
| `kinetic-lyric-video.in-world` | Lyrics tracked onto screens, signs and walls in footage or 3D | Text lives on surfaces, perspective-matched. Min contrast 4.5:1 against the local background |

## Timing and numbers
- **Beat math:** `beat_s = 60 / BPM`. At 100 BPM, a beat is 0.6 s (18 frames at 30 fps) and a bar is 2.4 s. 27 s is 45 beats, or about 11 bars. At 90 BPM a beat is 0.667 s (20 frames), and at 140 BPM it is 0.4286 s (12.86 frames).
- **Display mode from vocal density** (derived from the 20 cps ceiling [118]: an average English word plus space is about 6 characters, so the ceiling is about 3.3 words/s):
  - ≤ 1 word per beat at ≤ 110 BPM → **word-punch** (one word fills the frame).
  - 1–2 words per beat → **build** (words add to a line) or **karaoke** (whole line plus highlight).
  - More than 2 words per beat (rap, fast verses) → **line-karaoke** only. Never one-word-per-screen, because nobody can read it.
- **Minimum on-screen time:** 25 frames at 30 fps (5/6 s, the same rule as Netflix's 20 frames at 24 fps) for any text event. Gaps between events are either 2 frames or ≥ 0.5 s, never in between [119].
- **Lead times:** hard cut-on text 1–2 frames before the sung onset. Sliding or scaling entrances start 3–5 frames before the onset. Exits start on the next onset, never before [106][121].
- **Motion durations at 30 fps:** word slide 4–5 frames. Letter swing 6+2 frames. Snap zoom 6 in, 2 hold, 1 correct. Pull-back 8. Exit 4–6 frames, about 30% faster than the entry [121].
- **Type sizes** (% of frame height): hero single word 18–28% in 9:16 and 22–32% in 16:9 (cap height must fit inside the margins). Line mode 6–8% in 9:16 and 7–9% in 16:9. Whisper words 50% of the line size [121]. Line length ≤ 24 characters in 9:16 and ≤ 32 in 16:9 (tighter than Netflix's 42 [118] because display type is larger). Line height 0.95–1.05 for display, 1.15 for line mode. Tracking −2% to −4% on condensed display faces.
- **Safe zones (house defaults):** 9:16 keeps lyrics inside x 8–92% and y 15–75%, clearing the bottom 25% (caption, sound and comment UI) and the right 12% (action buttons) on short-form platforms. 16:9 uses 5% margins. 1:1 uses 6%.
- **Contrast:** text-to-background contrast ≥ 4.5:1, and 7:1 for line mode over footage. Over footage, add a 20–30% black scrim or a 0 0 24px rgba(0,0,0,.45) shadow.
- **Structure for a 27 s hook clip at 100 BPM:**

| Bars | Seconds | Section | Treatment |
|---|---|---|---|
| 1 | 0.0–2.4 | Intro / title | Song title in line mode, artist small, hold |
| 2–5 | 2.4–12.0 | Verse | Line-karaoke or build, 1 phrase per 1–2 bars, camera drifts 1.0→1.04 |
| 6–9 | 12.0–21.6 | Chorus / hook | Word-punch on the hook words, snap zoom on the hardest word, colour inverts on bar 6 |
| 10–11.25 | 21.6–27.0 | Tag / outro | The last line holds ≥ 1.5 s, then exits on the final downbeat |

## Build it
1. **Music and timing.** Use the `music-to-video` skill. `analyze-beatgrid.py` writes `audiomap.json` (bpm, beats, phrases, hard stops). Get word timestamps by transcribing the vocal through `/media-use`, or take the user's lyrics and align them to the phrases [124]. Store the lyrics as `[{word, t_in, t_out, emphasis: 0|1|2}]`.
2. **Choose the mode per phrase** with the density rule above, so verse and chorus can differ.
3. **Start from registry components:** `caption-kinetic-slam` (full-screen single word, alternating directions) for word-punch. `caption-pill-karaoke` or `caption-highlight` for karaoke. `kinetic-center-build` (words push the phrase left until it locks centered) for build. `per-word-rise` or `per-word-crossfade` for the ballad. `kinetic-type-swap` for a repeating hook with one changing word. Music-to-video templates such as `roll-flipbook-word-cycle` and `split-anchor-word-slot` cover many hook sections.
4. **Keep it seek-safe.** Every entrance is `tl.from(el, {...}, word.t_in - lead)` on one paused master timeline. No timers, no CSS transitions.
5. **Add the finish last.** Add a 1-frame contrast-colour duplicate on hook words [121], a 2-frame chromatic kick on hard cuts, and grain at 4–6% opacity [126]. Render stills at three points (verse, hook, outro) and check readability on a phone-sized preview.

## Mistakes that look amateur
- Words appear after they are sung → put entrances on the onset minus 1–5 frames. Never trust uncorrected transcript timestamps [119][120].
- One word per screen in a fast rap verse → switch to line-karaoke above 2 words per beat [118].
- A whole verse on screen → 1–2 lines maximum [122].
- Lines flashing for less than half a second → at least 25 frames at 30 fps, and merge short lines [119].
- Every word with the same size and motion → a 3-level emphasis scale (0.5x / 1x / 1.8x) driven by the vocal [121].
- Bad line breaks ("the / night") → break after punctuation and before conjunctions, and keep the bottom line longer [118].
- Thin script fonts over busy footage → a heavy display face plus a scrim, contrast ≥ 4.5:1.
- Heavy glitch, RGB and shake on a ballad → match motion to the mood, and halve the effects if a still looks like a filter [122][126].

## Sources
[106] EOSHD forum thread "Editing" (quoting composer Hans Zimmer) — https://www.eoshd.com/comments/topic/46696-editing/ — a frame ahead to jolt
[118] Netflix — English (USA) Timed Text Style Guide — https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-USA-Timed-Text-Style-Guide — 20 cps adult, 42 chars/line, 2 lines, line-break rules
[119] Netflix — Timed Text Style Guide: Subtitle Timing Guidelines — https://partnerhelp.netflixstudios.com/hc/en-us/articles/360051554394-Timed-Text-Style-Guide-Subtitle-Timing-Guidelines — 20-frame minimum, 2-frame gaps, in-time on audio, +0.5 s out
[120] Joey Korenman, School of Motion — Kinetic Typography in After Effects, Part 1 — https://schoolofmotion.com/blog/kinetic-typography-after-effects-part-1 — live marker tapping, comp markers, nudging hits 2–3 frames earlier, null-driven camera
[121] Joey Korenman, School of Motion — Kinetic Typography in After Effects, Part 2 — https://schoolofmotion.com/blog/kinetic-typography-after-effects-part-2 — 5-frame lead, 4–5 frame slides, 6+2 swing, snap zoom 6/2/1, 8-frame pull-back, 50% whisper, 1-frame colour offset
[122] Adobe — How to make a lyric video — https://www.adobe.com/creativecloud/video/discover/how-to-make-a-lyric-video — 1–2 lines, big legible type, mood-matched fonts, masks
[123] Creative Commission — The creative process: how to make a lyric video (Tom Readdy, Oriane Rondeau, Sophie Graves, Alejandra López Martín) — https://creative-commission.com/news/creative-process-how-make-lyric-video — time text first, plan in 10–15 s segments, mood-led type and motion
[124] Storyblocks — How to make professional lyric videos — https://www.storyblocks.com/resources/tutorials/make-professional-lyric-videos — waveform markers per phrase, one layer per word, emphasis words animate differently
[125] @theSethian on X — on a viral kinetic-type AI music video — https://x.com/theSethian/status/2104508003948830877 — lyrics woven into screens, signs and interfaces
[126] @Pashoke1 (Yaori) on X — finishing pass — https://x.com/Pashoke1/status/2115041115590037582 — RGB fringe, 2-frame chromatic kick on hard cuts, grain, halve values if it looks like a filter
