# Import-from-any-editor launch trailer

An 18-second product launch film for one feature: bring a project in from another editor and keep working. Project files fly in, one is dropped on the app, and the timeline rebuilds track by track on the beat. It ends on a clean logo lockup. Use it for a launch post on X or LinkedIn, a changelog hero or a landing-page loop. Master in 16:9 (1920×1080) or 1:1 (1440×1440) for X, then cut 9:16 from the same project. Typical length is 15–20 s, which is 30–40 beats at 120 BPM.

Other editors are named only by their generic interchange formats (FCP XML, AAF, CMX 3600 EDL, OTIO), never by their logos. Every product name and trademark belongs to its owner. Only show formats the product really imports.

## How the pros do it
- **Product on screen in the first seconds, no voiceover intro.** A breakdown of a widely viewed 2026 launch film shows it skipping the voiceover intro and building the product live within the first 10 seconds. It ends on a clean zoom-out to the full workspace and the logo [111]. A second breakdown opens on a real task typed live, so the viewer understands the product in about 3 seconds [112]. Agencies say the same: the viewer should understand the product within the first 10 s [117].
- **Five beats of story: task → zoom on setup → zoom out to show the whole → quick proof cuts → simple end card** [112]. For an import feature, that is: file → drop → timeline rebuilds → three source formats in quick cuts → logo.
- **Something on every beat, nothing fades.** One launch-film prompt set 120 BPM, one event per beat and one continuous take. It banned crossfades, blur-ins and holds longer than 1 s. The zoom lands on the drop, and the last frame equals the first so it loops [107].
- **Arrive at full speed, then decelerate. Never zoom text.** One editor's settings: `cubic-bezier(.25,0,.11,1)`. New graphics cut in at 1.52x and zoom out to 1x over 1.2 s. Text arrives word by word, dropping about 56 px while fading in, and text never zooms [108].
- **The camera zooms to where the click is.** Screen-recording tools build their auto-zooms from clicks, and a zoom with no click has nothing to aim at [110]. They use a "focused" settle when on-screen text must be read [109]. Give each zoom a cursor action as its reason: grab, drop, click Import.
- **Real UI, not placeholder boxes. Storyboard stills before motion.** Fake-looking UI is the quickest way to look cheap. Make three storyboard options and one still per scene before rendering, and cut the 9:16, 1:1 and 16:9 versions from the same project [113].
- **Break down a reference, then review frame by frame.** Pull one frame per second from a reference launch film to read its pacing, type and transitions. After rendering, review second by second and label problems P0/P1/P2 before fixing [114].
- **Use standard UI motion tokens for the app's own animations.** Material 3 uses emphasized decelerate `cubic-bezier(0.05, 0.7, 0.1, 1)` for entering elements and emphasized accelerate `cubic-bezier(0.3, 0, 0.8, 0.15)` for exits. Durations run 250–500 ms (medium1–long2) [115]. Use these for menus, toasts and progress bars inside the mock app. Use the faster cinematic curve [108] for the camera.
- **Name real interchange formats.** OpenTimelineIO converts through adapters for AAF, CMX 3600 EDL, FCP 7 XML, FCPX XML and its own `.otio` JSON [116]. Format chips with those names read as true to editors. Logos of other apps don't belong in the film.

## Presets
| Preset | Look | Key values |
|---|---|---|
| `import-launch-trailer.drop-and-rebuild` | Off-white canvas, dark app window. A file chip is dragged in and the timeline rebuilds one track per beat | 120 BPM, 36 beats. Camera `cubic-bezier(.25,0,.11,1)`. Track cascade 1 per beat. Logo hold 1.5 s |
| `import-launch-trailer.format-rain` | Dark canvas. Six format chips (XML, AAF, EDL, OTIO…) rain in on beats and funnel into one app icon | Chip 64 px tall at 1080p, 1 chip per 8th note, funnel 0.5 s on `power3.in`, flood 0.3 s |
| `import-launch-trailer.one-take-loop` | One continuous take where every scene grows out of the previous one. Last frame = first frame | No cuts or fades, holds ≤ 1 s, zoom lands on the drop, 60 fps with 4 subframes |
| `import-launch-trailer.vertical-cut` | 9:16 cutdown from the same scenes | Camera 1.35x on the app window, headline in the top 30%, end card centered |

## Timing and numbers
- **Beat math:** at 120 BPM, a beat is 0.5 s (15 frames at 30 fps, 30 at 60 fps) and a bar is 2 s. 18 s is 36 beats, or 9 bars. For a 128 BPM track, the beat is 0.469 s. Always derive times from `60 / BPM` and the analyzer's beat list.
- **Beat structure and shot list (18 s at 120 BPM):**

| # | Beats | Seconds | Shot | Motion |
|---|---|---|---|---|
| 1 | 1–4 | 0.0–2.0 | Hook: "Bring your edit." Headline rises word by word, one word per beat | Words drop 56 px and fade in over 10 frames. No zoom on text [108] |
| 2 | 5–8 | 2.0–4.0 | 3–5 format chips (FCP XML · AAF · EDL · OTIO) pop in on 8th notes around the headline | Pop scale 0→1.08→1.0 over 9 frames with a spring. Stagger 0.25 s |
| 3 | 9–12 | 4.0–6.0 | The cursor grabs one chip and drags it onto the app window | Drag follows the cursor 1:1. Lift tilt 6°. Drop settle 8 frames |
| 4 | 13 (drop) | 6.0 | Drop lands → camera zooms into the app timeline | Cut in at 1.5x, settle to 1.0x over 1.2 s [108]. Zoom lands on the music drop [107] |
| 5 | 13–24 | 6.0–12.0 | The timeline rebuilds: one track per beat (V3, V2, V1, A1, A2…), clips slide in left to right | Each clip 6 frames, stagger 2 frames. Material emphasized decelerate [115] |
| 6 | 25–30 | 12.0–15.0 | Proof: three quick cuts, each a different source format → the same rebuilt timeline | 2 beats each. Hard cut on the beat. Label chip in the corner |
| 7 | 31–32 | 15.0–16.0 | Zoom out to the full app window [111] | 1.0 → 0.6 over 0.8 s, focused settle |
| 8 | 33–36 | 16.0–18.0 | The app window contracts into the app icon, then the wordmark. Hold | Icon morph 0.4 s. Wordmark letter cascade 0.5 s. Hold still ≥ 1.0 s |

- **Flood / contract transitions:** a shape flooding the frame must overscale past the corners and take about 0.3 s, or half the screen changes in one frame [107].
- **Cursor:** 28 px arrow at 1080p, scaled with the camera. Press is 90% scale for 3 frames plus a 40 px ring expanding over 10 frames.
- **Type:** headline Geist 700 (or Inter 800), 7–8% of frame height, tracking −2%. UI labels Geist 500 at 14–16 px at 1x. Format chips Geist Mono 600 at 22 px inside a 64 px pill with 20 px horizontal padding.
- **Colors:** canvas #F5F4F0, app chrome #0F0F12, panel #17171B, accent (brand) for the playhead and selection. Format chips: stroke #D4D4D8, label #18181B.
- **Safe zones:** 16:9 uses 5% margins and keeps the end-card wordmark centered. 9:16 keeps the headline inside the top 30% and clears the bottom 20% of platform UI. 1:1 uses 6% margins.
- **Audio:** the music starts on a downbeat, the drop is placed at beat 13, and the track is loudness-normalized to −14 LUFS [107]. Each click and drop gets a real SFX aligned to its peak.

## Build it
1. **Plan.** Get the brand kit (logo SVG, colors, fonts, three real product screenshots or the live UI). Write the shot list above and make one still per shot before animating [113]. Pick a 115–125 BPM track with a clear drop near 6 s, or move shot 4 to the drop.
2. **Build the app window** as a real HTML mock of the product UI: timeline, tracks and inspector. Start from `browser-device-stage` or `device-frame-stage` for the window, and `ui-focus-zoom` for anchored zoom-and-hold.
3. **Drive the cursor** with `cursor-drag-drop` (grab, lift, carry, drop, settle) and `cursor-zoom-follow` (camera pushes toward each click and eases out). Every zoom needs a click or drop as its reason [110].
4. **Rebuild the timeline** with a GSAP stagger keyed to the beat list: `tl.from(clips, {x: -40, opacity: 0, duration: 0.2, ease: "expo.out", stagger: {each: 0.0667}}, beatTime(13))`. Use one paused master timeline, seek-safe.
5. **For the ending,** use `logo-brand-close` (letter cascade, accent lands last, holds dead still) or `logo-sting` for a harder hit. Use `icon-morph-beat` for the window-to-icon morph.
6. **For cutdowns,** keep one composition with three camera presets (16:9, 1:1, 9:16) and never re-animate [113]. Review one frame per second, fix P0s, then render the final [114].

## Mistakes that look amateur
- A logo splash or voiceover intro before the product → the product is on screen by 2 s and the logo goes last [111][112].
- Gray placeholder boxes for the UI → real product screens or a faithful HTML rebuild [113].
- Zooms with no cursor action → each zoom needs a click, drag or drop as its reason [110].
- Crossfades and blur-ins between scenes → morph, flood or hard-cut on the beat. No hold over 1 s except the end card [107].
- Zooming text or a headline that scales up → words drop in, and only UI and graphics zoom [108].
- Real logos of other editors on the format chips → generic format names only (XML, AAF, EDL, OTIO), and only formats that truly import [116].
- A rebuild cascade with even, linear timing → decelerate each clip (emphasized decelerate) and stagger 2 frames [115].
- An end card that keeps moving → the wordmark lands and holds still for ≥ 1 s.

## Sources
[107] @twoclipping on X — code-only launch film prompt — https://x.com/twoclipping/status/2103835273813496100 — every beat, no fades, ≤1 s holds, zoom on drop, 0.3 s flood, −14 LUFS, loop
[108] @RajAdonis on X — motion settings — https://x.com/RajAdonis/status/2113906813020344579 — easing curve, 1.52x→1x in 1.2 s, 56 px word drop, text never zooms
[109] Screen Studio guide — Animations — https://screen.studio/guide/animations — focused vs smooth, motion blur per move
[110] Screen Studio guide — Auto zoom — https://screen.studio/guide/auto-zoom — zooms target clicks; no click, no zoom target
[111] @bohdanmotion (Bohdan, launch-video producer at Flash Motion) on X — breakdown of a 2026 launch film — https://x.com/bohdanmotion/status/2080610655237751033 — no VO intro, product in <10 s, zoom-out to logo ending
[112] @bohdanmotion on X — breakdown of a 48 s agent launch film — https://x.com/bohdanmotion/status/2079974237893456071 — 5-stage structure, live-typed task, zoom in/out rhythm, simple CTA
[113] @ArchiveExplorer on X — launch video pipeline — https://x.com/ArchiveExplorer/status/2105023417716191488 — real UI, storyboard stills first, 9:16/1:1/16:9 from one project
[114] @Voxyz_ai on X — motion video team prompt — https://x.com/Voxyz_ai/status/2104194355556671987 — 1 fps reference breakdown, second-by-second P0/P1/P2 review
[115] Material Design 3 motion tokens (material-web, Apache-2.0) — https://github.com/material-components/material-web/blob/main/tokens/versions/v0_192/_md-sys-motion.scss — easing curves and 50–1000 ms durations
[116] OpenTimelineIO docs — Adapters — https://opentimelineio.readthedocs.io/en/latest/tutorials/adapters.html — AAF, cmx_3600, fcp_xml, fcpx_xml, otio
[117] Moonb (video agency) — How to make the perfect demo video — https://www.moonb.io/blog/perfect-demo-video — understand the product in the first 10 s
