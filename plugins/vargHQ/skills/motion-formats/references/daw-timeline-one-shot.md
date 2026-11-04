# DAW timeline one-shot

One continuous camera move over a music app's arrangement view: the playhead runs across the clips, and the camera never cuts. A bracket tracker snaps onto each clip as the playhead reaches it on the beat, and the camera punches in on downbeats and pulls back on the drop. Use it for a producer's "how this beat was made" post, a track teaser or a music launch. 16:9 is the native shape because a timeline is wide. 9:16 works as a tighter follow-cam (2.0–2.4x). A typical length is 20–30 s, which is 12–18 bars at 140 BPM.

The DAW interface is a generic mockup, with no real product's logo or exact skin. Every DAW name and trademark belongs to its owner. Do not use a real artist's track or name unless the user owns the rights.

## How the pros do it
- **The playhead motivates every move.** Spielberg's long takes hide the camera by letting the action drive each reframe, so the audience feels the drama and not the camera [105]. Here the action is the playhead. Every pan, push and lock-on answers what the playhead touches next, and the camera never drifts on its own.
- **Copy how the real app scrolls.** In an arrangement view, tracks stack vertically, the beat-time ruler reads bars.beats.sixteenths, and "Follow" scrolls the display with the song position [101]. Draw a bar-number ruler and vertical track lanes, and keep the playhead moving at a constant px-per-beat. Viewers who know these apps will notice a playhead that speeds up or slows down.
- **Something happens on every beat, all through one take.** A widely shared code-only launch film used 120 BPM and 54 beats, with something on every beat, nothing faded or cut, and each scene made out of the previous one [107]. Treat the beat grid as the shot list: one event per beat, such as a lock-on, a clip lighting up or a ruler tick flashing.
- **Hide the seam if you need one.** Artificial long takes hide their cuts in whip pans, where motion blur covers the edit, or behind a foreground object [104]. If the build needs two compositions, join them in a 4–6 frame whip pan along the timeline. Never use a dissolve.
- **Hit transients a frame early.** Composer Hans Zimmer, as quoted on a filmmakers' forum, says to be a frame ahead of the cut to jolt the audience, and that cutting 6–12 frames late changes the feel [106]. Fire lock-ons and punch-ins 1 frame before the kick or snare transient. Ease the camera behind the beat, 6–12 frames late, only in the breakdown.
- **Punch in at peak speed, then settle.** One editor's settings: graphics cut in at 1.52x and zoom out to 1x over 1.2 s, with `cubic-bezier(.25,0,.11,1)`, so things arrive at full speed and only slow down [108]. Use the same curve for downbeat punches at a smaller scale (1.0 → 1.10–1.15) so the UI stays readable.
- **Use two camera personalities.** Screen-recording tools offer a "focused" animation that settles fast for reading and a "smooth" one for creative content. They apply motion blur separately to zoom, pan and cursor [109]. Use focused settles (≤ 12 frames) when the camera stops on a clip name, and smooth travel between sections. Blur pans and zooms, never the static UI.
- **Short, one idea, end on the payoff.** Producer content guides keep short-form beat videos at 15–60 s on one idea, often a before/after or a walkthrough that ends on the finished track [103]. Make the drop the payoff: show the full arrangement in one wide frame at the drop.
- **Know the tempo before you design.** Genre sets tempo: hip-hop runs 60–100 BPM, house 115–130, techno 120–140, dubstep 135–145, drum and bass 160–180 [102]. Read the BPM from the beat analyzer and derive every duration from `60 / BPM`. Never hand-type seconds.

## Presets
| Preset | Look | Key values |
|---|---|---|
| `daw-timeline-one-shot.follow-cam` | Dark arrangement view. Camera rides the playhead at 1.6x with bracket lock-ons on every beat | Playhead held at 38% of frame width. 96 px/beat at 1x. Lock-on snaps in 2 frames, holds 0.75 beat, releases in 4 frames. Downbeat punch 1.0→1.12 over 1.2 s |
| `daw-timeline-one-shot.drop-reveal` | Tight 2.4x follow through the build, then a whip pull-back to the whole arrangement on the drop | Build at 2.4x. Riser zoom to 3.0x over the last 2 bars. Drop: 0.3 s pull to 1.0x, 1-frame white flash at 35% opacity, clips pulse |
| `daw-timeline-one-shot.vertical-follow` | 9:16 crop of the timeline, at the same speed as 16:9 | Camera 2.2x. Track lanes 92 px tall. Playhead at 50% width. Captions above the safe band |
| `daw-timeline-one-shot.light-studio` | Light-theme DAW for brand or education posts | Background #F4F4F2, clips at 70% saturation, playhead #FF3B30, mono labels #1A1A1A |

## Timing and numbers
- **Beat math:** `beat_s = 60 / BPM`. `bar_s = 4 × beat_s` (4/4). At 140 BPM, a beat is 0.4286 s (12.86 frames at 30 fps, 25.71 at 60 fps) and a bar is 1.714 s. A 30 s piece is 70 beats, or 17.5 bars. At 120 BPM, a beat is 0.5 s (15 frames at 30 fps). Compute each event time as `t0 + n × beat_s` from the beat index, and never by adding rounded frame counts. Rounding drifts by a frame every few bars.
- **Use the analyzer's beats.** When the track is rhythmic, take `beats_sec` from `audiomap.json`, which tracks real tempo drift. Use the constant grid only for a click-perfect stem.
- **Playhead position:** `x(t) = x_start + (t − t_song0) × (BPM / 60) × px_per_beat`. At 1x zoom on 1920 px, 96 px/beat shows 20 beats (5 bars) across the frame. The camera target is `playhead_x − 0.38 × frame_w / zoom`, so the playhead sits a little left of center and the next clips are visible ahead.
- **Lock-on bracket:** 4 corner brackets. Each arm is 18 px at 1080p, the stroke is 3 px and the color is the accent. Snap from 140% of the clip box to 100% in 2 frames with `expo.out`. Hold 0.75 beat. Fade in 4 frames. Fire 1 frame before the transient [106].
- **Downbeat punch:** scale 1.00 → 1.12 in 2 frames, then back to 1.00 over 1.2 s with `cubic-bezier(.25,0,.11,1)` [108]. Fire only on bar 1 of each 4-bar phrase, because punching on every bar looks mechanical.
- **Section structure (30 s at 140 BPM):**

| Bars | Seconds | Beat | Camera |
|---|---|---|---|
| 1–2 | 0.00–3.43 | Establish | Wide 1.0x, playhead enters from the left, the title sits in the empty upper lane |
| 3–6 | 3.43–10.29 | Drums enter | Push to 1.6x, follow cam, a lock-on on each kick/snare clip |
| 7–8 | 10.29–13.71 | Riser / build | Zoom 1.6x → 3.0x over 2 bars on `power2.in`, the tracker locks every 8th note |
| 9 (drop) | 13.71 | DROP | 0.3 s pull to 1.0x, 1-frame flash, every clip lights |
| 9–14 | 13.71–24.00 | Groove | Follow at 1.6x, a downbeat punch every 4 bars, a vertical pan to the melody lane on bar 11 |
| 15–17.5 | 24.00–30.00 | Outro | Slow push to 1.2x, the playhead stops on the last clip, logo/title lock-on, hold 1.0 s |

- **Frame rate:** 60 fps keeps the scrolling grid smooth, because a moving 1 px ruler judders at 24–30 fps. Render motion blur as 4 subframes per frame, blended [107].
- **Type:** Track names in Inter 600 at 15–16 px at 1080p×1x, which is 26 px on screen at 1.6x. Ruler numbers in JetBrains Mono 500 at 13 px. Title in Inter 800 at 6–7% of frame height.
- **Colors (dark):** background #121214, lanes alternate #18181B / #1C1C20, grid lines #2A2A30 (bar) / #202026 (beat). Clips use a 6-color set: #FF5A5F, #FFB020, #4ADE80, #38BDF8, #A78BFA, #F472B6. Playhead #FFFFFF at 2 px with a 6 px 30% glow.
- **Safe zones:** 16:9 keeps the title inside 5% margins. 9:16 keeps captions 12% from the top and 20% from the bottom, clear of platform UI.

## Build it
1. **Analyze the music.** Run the `music-to-video` skill's `analyze-beatgrid.py` on the track, which writes `audiomap.json` (bpm, beats_sec, key_moments with the DROP). Pacing is `beat_cut` for this format.
2. **Build the timeline as one big DOM element.** Make a `<div class="daw">` about 6000×1400 px with track header column, ruler, lanes and clips as positioned divs. Generate clips from a JSON arrangement such as `{track, startBeat, lengthBeats, color, label}`. Draw waveforms with the `waveform` block or a static SVG path per clip. Drive the playhead from timeline time, not from CSS animation.
3. **Run the camera as a single GSAP tween group** on a wrapper (`x`, `y`, `scale`), computed per beat from the formulas above. Use one paused master timeline for the whole piece. `ui-focus-zoom` (zoom/pan to an anchored region and hold) and `scroll-camera-story` (forced pass with parallax) are good starting points. Add `camera-shake` at 2–3 px for the drop only.
4. **Add lock-ons and accents.** Adapt `camera-scan-gate`, whose viewfinder brackets lock and pulse, and attach them to the clip under the playhead at each beat. Add `beat-accent` (flash plus micro scale pulse) on the drop. Add `telemetry-hud` or `oscilloscope-trace` as a small meter overlay if the brief asks for a technical look.
5. **Keep it seek-safe.** Compute everything from `t` and never use `requestAnimationFrame` or wall-clock time. Check frames at t=0, each section start, the drop and the last frame.
6. **For 9:16,** render the same composition with a different camera preset (2.2x, playhead at 50%). Don't relayout the DAW.

## Mistakes that look amateur
- The playhead speeds up or slows down to "hit" a clip → keep it linear at a constant px-per-beat and move the camera instead [101].
- Every bar gets a zoom punch → punch only on phrase downbeats (every 4 bars) and the drop. Lock-ons carry the per-beat rhythm.
- Lock-ons land on the visual beat but late in the audio → fire 1 frame before the transient, and check on a local file, because streaming players delay audio by 1–2 frames [106].
- The camera drifts with nothing motivating it → each move must answer "what does the playhead reach next" [105].
- A crossfade to hide a stitch → use a 4–6 frame whip pan with blur [104].
- Rounding the beat to 13 frames at 140 BPM → after 16 bars the visuals are 9 frames late. Compute from the beat index.
- Tiny unreadable track names at 1x → never hold below 1.4x on a clip you want read.
- A real DAW's logo, splash or exact skin → generic mockup only, and note that trademarks belong to their owners.

## Sources
[101] Ableton (Live 12 Reference Manual) — Arrangement View — https://www.ableton.com/en/manual/arrangement-view/ — vertical track stacking, bars-beats-sixteenths ruler, Follow behaviour, zoom keys
[102] Ableton Learning Music — Tempo and genre — https://learningmusic.ableton.com/make-beats/tempo-and-genre.html — BPM ranges by genre
[103] Simon Gilbert, RouteNote Create blog — 5 ways video content creation can boost your beatmaking potential — https://create.routenote.com/blog/5-ways-video-content-creation-can-boost-your-beatmaking-potential/ — 15–60 s, one idea, show the DAW, before/after
[104] No Film School (Fandor essay; text by Shaina Hodgkinson) — The art of the artificial long take — https://nofilmschool.com/2017/05/watch-art-artificial-long-take — whip pans and foreground objects hide cuts
[105] No Film School on Tony Zhou (Every Frame a Painting) — The Spielberg Oner — https://nofilmschool.com/2014/05/study-steven-spielbergs-cinematography-help-you-master-long-take — motivated, disguised camera movement
[106] EOSHD forum thread "Editing" (quoting composer Hans Zimmer) — https://www.eoshd.com/comments/topic/46696-editing/ — a frame ahead to jolt, 6–12 frames late to breathe, streaming audio delay
[107] @twoclipping on X — code-only launch film prompt — https://x.com/twoclipping/status/2103835273813496100 — one continuous take, something on every beat, 4 subframes at 60 fps
[108] @RajAdonis on X — motion settings — https://x.com/RajAdonis/status/2113906813020344579 — cubic-bezier(.25,0,.11,1), cut in at 1.52x, settle to 1x over 1.2 s
[109] Screen Studio guide — Animations — https://screen.studio/guide/animations — focused vs smooth screen animation, per-move motion blur
