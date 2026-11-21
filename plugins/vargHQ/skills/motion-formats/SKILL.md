---
name: motion-formats
description: >-
  Seven complete motion formats, each with a beat structure in seconds, a shot list and presets: a
  found-footage analog-horror trailer of a website, an authentic VHS bouncing-logo screensaver, a
  pixel-art runner on a CRT, a wordmark with a wave running through it, a one-shot music video that
  follows a DAW timeline, a launch trailer for an import feature, and a kinetic lyric video. Values
  come from VHS signal models (ntsc-rs, Finn McKenty), pixel-art conventions (Pedro Medeiros,
  Slynyrd), School of Motion, Netflix timing rules, screenlife rules and launch-film designers on X.
  Use when someone asks for one of these formats, a VHS or analog-horror look, a pixel art animation,
  a lyric video or a beat-synced launch video. NOT for generating the song or footage (varg-ai,
  varg-music-video).
license: MIT
compatibility: >-
  HyperFrames 0.8 (npx hyperframes; brings Chrome, needs Node 22 and ffmpeg) or Remotion 4. No API
  key.
metadata:
  author: vargHQ
  version: "0.1.0"
  varg.cost.typical: "0 credits; renders locally"
  varg.runtime.typical: "minutes per template, mostly render time"
  varg.models: "none"
  varg.outputs: "mp4, webm or mov (alpha) from HyperFrames or Remotion"
  varg.presets: "7 templates, 32 presets"
---

# Motion formats: seven signature videos with beat structures and presets

Seven formats with the structure already worked out: every time derives from the BPM, hits land a frame or two before the transient, and old media is degraded with a signal model rather than an overlay.

## Gates

- **Your own song and brand.** Lyric and music formats use music the person owns or licensed; the wordmark and launch formats use their own brand.
- **Times from the BPM.** Compute t0 + n x (60/BPM); never add up rounded frame counts.
- **Free fonts only.** Every font in the presets is OFL or Apache. Swap in the person's brand font only if they have a license for video.
- **Seek-safe.** Every value is a function of timeline time; randomness is seeded by frame. No `Date.now()`, `requestAnimationFrame` or unseeded `Math.random()`.
- **No credits here.** These templates render locally for free. Generated footage, voice or music is the varg-ai skill: call `estimate_cost` and wait for the person's approval before any generation.

## Pick a template

7 templates, 32 presets. Each reference file has the same sections: how the pros do it (every rule cited), presets, timing and numbers, how to build it, mistakes that look amateur, sources. Each JSON file holds the same presets as machine-readable values.

| Template | Use it for | Presets | Files |
|---|---|---|---|
| **DAW timeline one-shot** | One continuous camera move over a mock music-app arrangement view; a bracket tracker locks onto every clip the playhead hits on the beat, the drop pulls back to the whole arrangement. | Follow cam, Build and drop reveal, Vertical follow, Light studio | [`daw-timeline-one-shot.md`](references/daw-timeline-one-shot.md) · [`json`](assets/presets/daw-timeline-one-shot.json) |
| **Found-footage website trailer** | A 25 s analog-horror teaser that browses a fictional website as a screen recording or a camcorder pointed at a CRT, escalates, and ends on a title. | Camcorder filming a CRT, Clean screen capture that corrupts, Broadcast-slate interruptions, 9:16 | [`found-footage-website-trailer.md`](references/found-footage-website-trailer.md) · [`json`](assets/presets/found-footage-website-trailer.json) |
| **Import-from-any-editor launch trailer** | 18 s feature launch film: project files from other editors are dropped onto the app and the timeline rebuilds on the beat, ending on the logo. | Drop and rebuild, Format rain, One-take loop, Vertical cutdown | [`import-launch-trailer.md`](references/import-launch-trailer.md) · [`json`](assets/presets/import-launch-trailer.json) |
| **Kinetic lyric video** | Lyrics animate in sync with the vocal; type size, weight and motion carry emphasis; for releases, hook teasers and social clips. | Word punch, Line karaoke, Ballad drift, Build and slam, Lyrics in the world | [`kinetic-lyric-video.md`](references/kinetic-lyric-video.md) · [`json`](assets/presets/kinetic-lyric-video.json) |
| **Pixel-art runner on a CRT** | An 18 s side-scrolling pixel-art mini game (run, jump, reach the logo) shown through a curved, scanlined CRT. | 16-colour console, 16:9, 4-shade handheld green, Strict 8-bit sprite limits, 9:16, 1:1 fantasy console | [`pixel-runner-crt.md`](references/pixel-runner-crt.md) · [`json`](assets/presets/pixel-runner-crt.json) |
| **VHS bouncing-logo screensaver** | A 5 s brand sting or loop: a logo bouncing at constant speed on a worn videotape at 50/60 fps, landing in a corner on cue. | PAL 50 fps, landscape, NTSC 60 fps, landscape, 9:16 phone screensaver, 1:1, Worn EP rental tape | [`vhs-bouncing-logo.md`](references/vhs-bouncing-logo.md) · [`json`](assets/presets/vhs-bouncing-logo.json) |
| **Wave-through wordmark** | A 2 s logo sting: a crest of lift, weight or seesaw tilt runs through a wordmark letter by letter and settles back to the exact logo. | Lift wave, Seesaw, Weight wave, Snap, Idle loop | [`wave-wordmark.md`](references/wave-wordmark.md) · [`json`](assets/presets/wave-wordmark.json) |

## Workflow

1. **Match the request** to a template and one or two presets from the table. Say which and why in one line, and show the person the preset names with their one-line looks before building anything.
2. **Read the reference** for that template, and load its JSON. Take values from the JSON; do not re-guess them.
3. **Build it** the way the reference's "Build it" section says, starting from the named HyperFrames blocks or varg components where it names them. Drive every value from timeline time so any frame renders the same on a re-render.
4. **Fit it to the brand:** swap in the person's colors and fonts only where the reference allows, then re-check contrast and safe zones with the numbers in "Timing and numbers".
5. **Check a draft:** render stills at the key moments (entrance, hold, exit), go through "Mistakes that look amateur", and fix before the final render.


## Rules that hold for every template

1. Derive every time from 60/BPM: t0 + n·beat; never sum rounded frames.
2. Visual hits 1–2 frames before the transient; entrances start 3–5 frames early.
3. Every camera move needs a reason; hide unavoidable seams in 4–6 frame whip pans, never dissolves.
4. One event per beat, holds of 1 s or less, end card held at least 1 s.
5. Degrade with a signal model (tape damage → downscale → CRT shader), not overlays.
6. Seek-safe and true to the medium: triangle-wave bounce, floor(t/pose) sprites, integer pixels, 50/60 fps field rate.
7. Show less; degrade only on the beats; silence before the title; hold the title at least 2 s.
8. Constrain like the hardware: integer scaling, 4-colour sprites in a 16-colour scene, 3–8 run poses at 80–160 ms, per-letter stagger via each.

## Built from

Finn McKenty + ntsc-rs defaults (VHS); Pedro Medeiros (saint11), Raymond Schlitter (Slynyrd) (pixel art); Joey Korenman / School of Motion (kinetic type); Netflix timed text; @twoclipping, @bohdanmotion (launch films); Timur Bekmambetov (screenlife).

Every rule in the references cites its source by number. The full list, with links and what was taken from each, is in [`references/sources.md`](references/sources.md). Values marked as house defaults in a reference are our own starting points where no expert published a number.

## Related skills

- [varg-music-video](../varg-music-video/): AI music videos with generated shots.
- [kinetic-type-art](../kinetic-type-art/), [transition-craft](../transition-craft/): the type and transitions these formats use.
- HyperFrames registry (`npx hyperframes catalog --query "…"`): about 450 ready-made blocks; the references name the ones to start from.
