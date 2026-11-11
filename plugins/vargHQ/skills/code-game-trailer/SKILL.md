---
name: code-game-trailer
description: >-
  Turn a browser game or three.js / WebGL scene an agent built into a cinematic trailer MP4: a
  virtual clock injected before the page's scripts makes every frame exact at 30 or 60 fps, a
  director JSON scripts each shot (key and mouse inputs, game setup, trailer camera paths, slow
  motion, HTML titles and end cards), headless Chrome captures 1920x1080 frames, ffmpeg cuts them on
  the beat, a music bed (code-written or from varg) is normalised to -14 LUFS, and a checker measures
  frozen frames, loudness, debug text, third-party names and claims. Includes a tested example game.
  Use when someone asks for a game trailer, to record my three.js game, a gameplay video, a trailer
  for my browser game, a Fable 5.2 game video or a fake AAA gameplay trailer. Not for HTML motion
  graphics (hyperframes), 3D previz for AI video (threejs-animatic), AI-generated footage (varg-ai)
  or editing existing footage (short-form-ffmpeg-cookbook).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
compatibility: >-
  Bun, ffmpeg (libx264, aac, loudnorm; drawtext not needed) and Google Chrome or Chromium; no npm
  packages (a 150-line CDP client is included). Measured 2026-11-10 on an Apple M4 Pro, headless
  Chrome on the GPU (ANGLE Metal): 50-68 ms per 1920x1080 frame, 558 frames in 33.5 s including 8
  page loads; software WebGL (SwiftShader, no GPU) 509 ms per frame. Cut 9.7 s, check 9 s for an
  18.6 s trailer. Free locally; an optional varg music track needs the varg MCP or a VARG_API_KEY.
allowed-tools: Bash(bun:*) Bash(ffmpeg:*) Bash(ffprobe:*) Bash(magick:*) Read Write Edit
---

# Code game trailer: record the game, cut it like a trailer

On launch day of Claude Fable 5.2 (2026-11-09) the most-watched thing people made with it was a
browser game built from one brief: 3.45M views across 18 posts. What travelled was not the game but
the **video of the game**. A screen recording of a game drops frames, drifts from the music and shows
a cursor and a debug counter. A trailer needs exact frames, chosen moments, a camera that moves like
a film camera, a title, a beat and an end card. This skill does that for any HTML/WebGL game an
agent wrote.

The example in `examples/lantern-canyon/` (an original game made for this skill, one HTML file) went
from director JSON to an 18.6 s 1080p trailer in 56 s on a laptop (stills, capture, score, cut and check), with
no credits spent: [the full trailer](https://s3.varg.ai/files/4325c578-378d-4c43-ae53-3cc3218df1ea/file_b715771f882f.mp4)
(1920×1080, 19 MB). Your own runs write it to `examples/<game>/master.mp4`.

## When to use it

| request | use |
|---|---|
| "make a trailer / gameplay video of my browser game", "record my three.js game" | **this skill** |
| a game that does not exist yet ("make a game and a trailer for it") | brief the game first ("Making the game in the first place" below), then this skill |
| the video is HTML motion graphics, captions, a launch film | `hyperframes` |
| a 3D grey-box previz that will feed Seedance video-to-video | `threejs-animatic` |
| footage from AI video models | `varg-ai` |
| cutting, captioning or reformatting existing footage | `short-form-ffmpeg-cookbook` |

## Quick start

```bash
S=<this skill>
bun $S/scripts/capture.ts $S/examples/lantern-canyon/director.json --stills   # 3 stills per shot, ~6 s: LOOK at them
bun $S/scripts/capture.ts $S/examples/lantern-canyon/director.json            # all frames -> examples/lantern-canyon/capture/
bun $S/scripts/score.ts   $S/examples/lantern-canyon/director.json            # music.wav + sfx.wav (written in code, free)
bun $S/scripts/cut.ts     $S/examples/lantern-canyon/director.json --music $S/examples/lantern-canyon/music.wav \
                          --sfx $S/examples/lantern-canyon/sfx.wav --grade      # -> examples/lantern-canyon/master.mp4
bun $S/scripts/check.ts   $S/examples/lantern-canyon/director.json            # measurements + contact sheet to look at
```

For your own game: copy `examples/lantern-canyon/director.json` next to the game's `index.html`, point
`"url"` at it, rewrite the shots. Local paths are served over `http://127.0.0.1` for the run (ES
modules and CDN imports need http, not `file://`).

## The workflow

### 1. Make the game capturable (5 minutes, once)

The recorder needs three things from the page. Add them to the game (or ask the agent that wrote it):

```js
window.__game = {
  ready: false,             // set true after assets loaded AND the first frame rendered
  renderer, camera,         // the THREE.WebGLRenderer and the camera the game renders with
  player,                   // optional Object3D the trailer camera can follow or look at
  anchor,                   // optional Object3D: the player's position with the level's heading, no roll
  setup(opts) { ... },      // reset to a known state: level, distance, score, autopilot, hud on/off
  get events() { ... },     // optional: drain [{ type: 'pickup' | 'hit' | ... }] for sound effects
};
```

Rules that make the capture exact (details: `references/virtual-clock.md`):
- All motion from `requestAnimationFrame` time or `performance.now()` deltas (the clock controls both).
- The level layout uses its **own** seeded random stream, never `Math.random` and never the stream
  that cosmetic effects use (see gotchas).
- HUD in HTML with `vh` units and ≥ 6vh side margins; no FPS counter or debug text unless `?debug`.
- An attract-mode autopilot (the game plays itself) makes every non-hero shot easy to direct.

### 2. Shot list: 4-8 shots plus title and end card

Write it before any camera work. Roles drive the music and the checks:

| role | shows | camera that works | length |
|---|---|---|---|
| `establishing` | the world, the mood, the player arriving | crane down from above, player rising into frame | 2.5-3.5 s |
| `mechanic` | the core verb, with the HUD so people see it is a game | the game's own camera + scripted keys | 2.5-3 s |
| `mechanic` (detail) | the hero object up close | low tracking shot in `__game.anchor` space | 1.5-2 s |
| `escalation` | more speed, more enemies, more particles | game camera with boost, or a world-fixed fly-by | 1-2.5 s each |
| `hero` | the one moment people screenshot | world-fixed camera, `speed: 0.5` slow motion | 2.5-3 s |
| `title` | the name over the game world | slow drift, HTML `overlay`, HUD hidden | 2-2.5 s |
| `end` | where to play, what it is made of | `card` page | 1.5-2 s |

Cut on beats: give shots `"beats"` and the director a `"bpm"`. At 100 BPM a beat is 0.6 s.
Order: wide → close → fast → faster → hero → title → end. Quick shots (1-1.5 s) belong in the
escalation; the hero shot gets room.

### 3. Director JSON

```json
{ "url": "index.html", "fps": 30, "width": 1920, "height": 1080, "seed": 7, "bpm": 100,
  "ready": "window.__game && window.__game.ready", "probe": "window.__game.state.score",
  "shots": [
    { "id": "s2_mechanic", "role": "mechanic", "beats": 5,
      "setup": "__game.setup({distance: 286, lat: 2.5, h: 2.0, score: 37})",
      "inputs": [ { "at": 0.35, "key": "ArrowRight", "hold": 0.4 }, { "at": 1.1, "key": "ArrowLeft", "hold": 0.9 } ] },
    { "id": "s6_gate", "role": "hero", "beats": 5, "speed": 0.5,
      "setup": "__game.setup({distance: 1226, autopilot: true, hud: false})",
      "camera": { "space": "__game.place(1240)", "lookAt": "__game.player", "ease": "linear",
        "keys": [ { "pos": [5, 0.5, -16], "fov": 52 }, { "pos": [3, 1.5, -19], "fov": 58 } ] } },
    { "id": "s8_end", "role": "end", "beats": 3, "card": "cards/card.html?title=MY%20GAME&sub=Play%20in%20your%20browser", "fade_out": 0.6 }
  ] }
```

(Copy `cards/` next to your game for the end card; the example points at `../../cards/card.html`.)
Every shot is a fresh page load (deterministic start), then `setup`, then `warmup` seconds stepped
without recording, then the frames. Camera keys are positions in the `space` object's frame (three.js
convention: +x right, +y up, −z forward); the trailer camera replaces the game camera only inside
`renderer.render` and is restored after, so gameplay never sees it. All fields, inputs and overlays:
`references/director-format.md`.

### 4. Stills first, then verify

`capture.ts … --stills` writes the first, middle and last frame of every shot into `capture/stills/` in
a few seconds (stepping costs 4-6 ms per frame without screenshots). Look at them with the Read tool
(montage them: `magick montage *_b.jpg -tile 2x4 -geometry 960x540+4+4 sheet.jpg`). Fix the camera,
the setup distance and the inputs here, where a try costs seconds. The `probe` value printed per shot
(the score, here) tells you whether scripted inputs actually did something.

Then `capture.ts … --verify --only <shot>` renders the first 45 frames twice from fresh loads and
compares PNG hashes. Measured: 45/45 identical with scripted keys and in slow motion. Anything less
means a clock, `Math.random` or load timing leaks into the picture.

### 5. Capture

`capture.ts director.json` writes `capture/<shot>/00000.jpg …` (JPEG q92; `--format png` for
lossless) and `capture/manifest.json` (frames, ms per frame, game events per frame, the visible text,
the probe). `--only s2,s4` re-records some shots and keeps the rest.

### 6. Sound

- **Free, in code:** `score.ts director.json` writes `music.wav` (pad, bass, drums by role, a riser that
  lands on the hero shot's first game event, impacts on the gate and the title) and `sfx.wav` (a chime
  per pickup that climbs with the chain, a whoosh per gate, a thud per hit) placed on the exact frames
  the capture saw them. The Fable 5.2 games that spread generated all their sound in code too.
- **A real composition from varg:** price it first, then generate an instrumental of the trailer's length:
  `estimate_cost({ tool: "music", input: { model: "mureka_9_5", prompt: "...", duration: 20 } })`, show the
  price, and only after a yes `generate_music({ model: "mureka_9_5", prompt: "dark cinematic trailer bed,
  100 BPM, low drone, pulse, riser, one big hit at 0:11, instrumental, no vocals", duration: 20,
  instrumental: true })`. Name the model: the tool's default is a much pricier one (`varg-ai` lists
  mureka ~25 credits vs ~158). Then `beats.ts music.mp3` finds BPM and the first beat (measured: 99.79
  BPM on a 100 BPM bed, first beat within 30 ms); put both in the director (`"bpm"`,
  `"music": {"file", "offset"}`) and re-time the shots in beats. Keep `sfx.wav` either way.

### 7. Cut

`cut.ts director.json --music … --sfx … --grade` builds the master: shots in order, fades
(`fade_in`, `fade_out`, `flash_in`), gentle contrast and vignette, the mix trimmed to the picture,
two-pass `loudnorm` to -14 LUFS / -1.5 dBTP, H.264 crf 18 + AAC 192k, `+faststart`. It also writes
`master.cuts.json` (where every shot sits). Text is never drawn by ffmpeg: titles are HTML in the
capture (this ffmpeg had no `drawtext`), so they get real fonts, tracking and CSS animation.

Preview for a gallery card (1280x720, 6-10 s, 0.4-2 MB):
`ffmpeg -ss 11.4 -i master.mp4 -t 6.6 -vf scale=1280:-2:flags=lanczos -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -an -movflags +faststart preview.mp4`.
Measure the bitrate per shot first: dense particles cost 721 KB/s at these settings, an end card 86
KB/s, so a 2 MB preview cannot hold an 8 s ember storm.

### 8. Check, then look

`check.ts director.json` measures and prints: duplicate and frozen frames per shot (from the captured
frames, before grading), black frames outside fades, size/fps/codec, integrated loudness and true
peak, a contact sheet (every 15th frame, with a tile → time → shot legend), and every visible string
with flags for debug words, third-party names and claims. Then open the sheet and look at every tile:
the numbers do not see a camera inside a wall or a lantern that never enters the frame.

Before anyone sees it:
- [ ] no third-party IP: no franchise names in titles, captions, HUD, file names; no lookalike
      characters, logos or cars. "GTA-style" in a caption is still their name.
- [ ] captions are true: "one prompt" only if it was one prompt (keep the prompt); "real gameplay" only
      if the shot used the game camera; "made in 8 hours / for $550" only with the receipt. Scripted
      trailer cameras, slow motion and save states are normal in trailers; just do not caption them as
      "unedited".
- [ ] no real people's faces or voices; no brand logos on in-game objects.

## Making the game in the first place (Claude Fable 5.2 / Claude Code)

The launch-day examples, all built by the model from a brief:
[@felixrieseberg](https://x.com/felixrieseberg/status/2119925633564463609)'s rainy-port FPS (2.3M views,
about $550 of API, 8 hours, models, sounds and textures all from code),
[@kevin_t_ngo](https://x.com/kevin_t_ngo/status/2119868968307695818)'s lantern-boat ride through 8
dreamlike worlds (388k), [@mattshumer_](https://x.com/mattshumer_/status/2119870965106483384)'s voxel
engine with sound (222k), and [@ericmaskfr](https://x.com/ericmaskfr/status/2119910195325481026)'s
80s-Miami open-world crime game (148k, 2 h 14 min). His brief is a model of a one-shot prompt: a role,
a tight loop where every system feeds the next, a feel requirement, a no-assets rule, and a
self-test loop with a stopping condition:

> you're a senior game dev. build a third-person open-world crime game in a sunny 80s miami-style
> city. make the loop tight: walk, fight, steal a car, get chased, earn money, spend it. every system
> feeds the next: crimes bring heat, heat brings cops, missions pay, money unlocks the garage. cars need
> weight: gears, skids, real crashes. the city has to feel alive with traffic, people and day into
> night. no audio files, generate every sound in code. after each system, play it yourself, screenshot
> it and fix what looks wrong. don't stop until a stranger could play for 10 minutes without hitting a bug

(His post framed it as a clone of a famous franchise; the trailer must not.) Brief templates and the
trailer-hooks paragraph to append to any brief: `references/game-brief.md`.

## Gotchas met building this skill

- **A screen recording is not a trailer.** Screenshotting the same game in real time advanced 84.5 ms
  of game time per captured frame (max 150 ms): played at 30 fps that is 2.5x too fast, with jumps.
  With the virtual clock every frame is exactly 33.3 ms and the screenshot shows the frame just stepped
  (tested with a frame-indexed colour: no lag).
- **Shared random streams break scripted inputs.** Adding decorative sky lanterns (220 → 260) consumed numbers
  from the world's random stream, every pickup moved, and the scripted keys scored 0 instead of 12.
  Give the level layout its own seeded stream.
- **Plan inputs, do not guess them.** Read the layout from the page (`__game.layout`), then try
  timings: a grid of 486 key timings ran in 61 s (90 frames each, no screenshots) and found 12 points
  vs 2 with no input. Or use the game's autopilot for every shot that is not about the controls.
- **CSS class collisions.** A title overlay class `.tl` picked up the game HUD's `.tl {position:
  absolute; top-left}` and the title's rule line flew to the corner. Prefix overlay classes.
- **Timers keep Bun alive.** `Promise.race([..., Bun.sleep(60000)])` left the recorder hanging 60 s
  after finishing; clear the timer.
- **Additive sprites near a camera become blobs.** Mist sprites and close embers turned into big
  teal and white balls in low trailer shots that the game camera never saw. Fade them by distance to
  the render camera (`onBeforeRender` gets the trailer camera).
- **The trailer camera finds geometry the game hides.** A thin upward strip at the canyon rim (wall
  columns clamped to the rim height) showed as beige scratches only from trailer angles.
- **Grain is expensive.** Temporal film grain at crf 16 made an 18.6 s master 209 MB; without grain
  at crf 18 it is 19 MB with no visible banding (checked at 3x level stretch).
- **AAC raises peaks.** loudnorm at -1 dBTP on the WAV measured -0.7 dBFS after AAC; target -1.5.
- **This ImageMagick has no fonts** (no Freetype/Ghostscript): `montage -label` fails, so contact sheets
  come from ffmpeg `tile` with a printed legend instead of burned-in labels.

## Files

| path | what |
|---|---|
| `scripts/virtual-clock.js` | frame-exact clock: rAF, performance.now, Date, timers, CSS animations, seeded Math.random |
| `scripts/director-runtime.js` | in-page half: trailer camera override, overlays, hidden selectors, letterbox, events |
| `scripts/cdp.ts` | minimal Chrome DevTools Protocol client (launch, inject, keys, mouse, screenshot) |
| `scripts/capture.ts` | director JSON → frames + manifest; `--stills`, `--only`, `--verify`, `--gl swiftshader` |
| `scripts/score.ts` | music bed + game SFX written in code from the director and the capture events |
| `scripts/beats.ts` | BPM + first beat of any track, for cutting on beats |
| `scripts/cut.ts` | frames → master MP4: order, fades, grade, mix, two-pass loudnorm |
| `scripts/check.ts` | duplicates, freezes, black frames, loudness, contact sheet, text/IP/claim audit |
| `cards/card.html` | title and end card page (query parameters, CSS animation on the virtual clock) |
| `examples/lantern-canyon/` | the test game (one HTML file, three.js 0.181.2 from jsDelivr) and its director |
| `references/director-format.md` | every director field, camera spaces, inputs, overlays, the manifest |
| `references/virtual-clock.md` | what the clock covers and does not, load phases, determinism, Playwright variant |
| `references/game-brief.md` | brief templates, the trailer-hooks contract, game-side lessons |
| `references/sound-and-cut.md` | score arrangement, varg music, beats, loudness, grading, preview sizing |
| [example trailer](https://s3.varg.ai/files/4325c578-378d-4c43-ae53-3cc3218df1ea/file_b715771f882f.mp4) | the example's output (1920x1080, 18.6 s), hosted on s3.varg.ai; media is not kept in the repo |

## Related skills

`hyperframes` (HTML → video, for trailers that are mostly motion graphics), `threejs-animatic`
(frame-by-frame three.js rendering for previz and Seedance video-to-video), `varg-ai` (music, voice,
AI footage, prices), `short-form-ffmpeg-cookbook` (vertical cut-downs, captions, reformatting the master
for TikTok/Reels/Shorts).
