---
name: code-path-traced-film
description: >-
  Make a short animated film in which everything is code the agent writes, including the renderer: a
  path tracer in one WebGL2 shader (no Blender, no three.js, no meshes, no textures), characters and props as
  signed distance fields, a meadow of analytic curved grass blades, moon, firefly and window lights with soft
  shadows, depth of field and motion blur, a variance-guided denoiser, a score synthesized in numpy from the
  same timeline, captions and an encode. Includes the complete tested film "The Smallest Star" (70 s, 11
  shots, two characters) as a starter, a live page that runs the same renderer in the browser, and the
  speed-ups and traps found while making it. Use when someone asks for a film, short or music piece "made
  entirely in code", "write your own renderer / ray tracer / path tracer and make a film with it", a
  storybook or clay-diorama 3D short without Blender, a "no assets, no video model" showcase of what a coding
  model can do, or a remake of The Smallest Star with another story. Not for a Blender film (blender-code-film),
  a three.js explainer (code-3d-explainer), recording a browser game (code-game-trailer), 2D motion graphics
  (kinetic-type-art, hyperframes) or AI-generated footage (varg-ai).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
compatibility: >-
  Google Chrome with WebGL2, EXT_color_buffer_float and EXT_float_blend (headless on the real GPU; tested on
  Chrome 157, Apple M4 Pro, Metal), Bun 1.x, Python 3 with numpy and Pillow, ffmpeg. No API key, no credits.
  Measured on a MacBook Pro M4 Pro: shader compile 0.2-0.6 s, a 480x270 draft still about 0.4 s, a whole-film
  contact sheet (33 stills) 13 s, final frames at 1280x720 0.2-15 s each (20-50 samples per pixel).
allowed-tools: Bash(bun:*) Bash(python3:*) Bash(ffmpeg:*) Bash(ffprobe:*) Read Write Edit
---

# A film where the renderer is code too

Coding models make video by writing programs. Most of those programs drive someone else's renderer
(Blender, three.js). This skill goes one step down: the agent writes the path tracer itself, then tells a
story with it. The claim a viewer can check is simple and strong: no 3D software, no models, no textures, no
video model, no music model. The starter is a finished film made this way in one session.

- Film: `scripts/smallest-star/` renders "The Smallest Star", a 70 s fable about a firefly and a lost mouse
  ([watch it](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_8d3b65611ed8.mp4)). All
  1,560 frames at 1280x720 took 1 h 46 min on a MacBook Pro M4 Pro; the whole session, from a one-line
  prompt to the encoded film, took under three hours (2026-11-10).
- Live page: `scripts/smallest-star/live/` bundles the same renderer into one HTML file. Viewers drag the
  camera and watch the picture converge on their own GPU (28 ms a sample at 960x540 on the same laptop).
  Post the link with the film: it is the proof.

## Ask first

Put these to the person before building. Each one changes hours of work.

1. **Story.** Their own (a moral in one line is enough) or one the agent writes. Two characters and three
   places is the ceiling for one session.
2. **Length.** 30, 60 or 90 s. Render time grows with length: the 60 s film took about two hours of GPU at
   1280x720 on one laptop. Offer 30 s when they want it today.
3. **Look.** The starter is a night diorama: clay characters, indigo sky, one warm light. A day scene needs
   a new sky and light balance (one more hour). Keep one dominant light source that is also a character or a
   story object; path tracing is at its best when the light is the story.
4. **Delivery.** 16:9 film only, or film plus the live page.

## The order of work

1. **Write the fable, then the shot list on a bar grid.** Pick a tempo whose bars divide into frames
   (72 bpm in 3/4 gives 2.5 s bars = 60 frames at 24 fps). Every shot starts on a bar line. Put shots, moods,
   captions and sound cues in one `timeline.json`. Picture, score and assembly all read this file.
2. **Start the score now, in parallel.** `audio/score.py` is pure numpy: music box, pad, bass, crickets,
   wing buzz, footfalls, a hand-written reverb and a BS.1770 loudness meter. It reads `timeline.json`, so it
   follows every later change. Hand it to a second agent with the brief in `references/score-brief.md`.
3. **Lay out the world as data** (`src/world.js`): where the path runs, pond, house, props. The same file
   emits GLSL constants and JS helpers, so the shader and the animation never disagree.
4. **Model characters as distance fields**, a dozen primitives each, joined with smooth unions. Give each a
   pose vector (head pitch, ears, squash, tail) driven from JS. Look at them under a bright studio light
   first (`--dev dev_mouse:0.2`), not in the dark scene.
5. **Write every shot as a function of time** (`src/shots.js`): camera, both characters, lights, exposure.
   Motion blur is free: the renderer asks for the state at a different time for every sample.
6. **Render the whole film as a contact sheet** before polishing anything: 33 stills at 480x270, 8 samples,
   13 s. Fix blocking and framing here. Repeat after every change; it is cheap.
7. **Look pass.** Night only reads when the visible sky is far darker than the sky that lights the scene:
   keep two gains. Numbers that worked are in `references/look.md`.
8. **Motion strips.** Render every second frame of the fast moments at 384x216 and read them as a strip.
   Put footfalls on the beat by shifting the hop phase so the landing, not the take-off, falls on the cue.
9. **Time one frame per shot at final settings, then start the long render in the background** with
   resume (`render.ts` skips frames that exist). Do not edit `src/` while it runs: a retry would pick up the
   new code mid-film.
10. **Making-of passes, assembly, encode.** `--modes 2,1` writes normals and albedo from one render;
    one sample per pixel with no denoise shows the raw light. `post/compose.py` scales, adds captions and
    pipes frames to ffmpeg with the score.
11. **Build the live page** (`live/build.py`) and test that its canvas really draws before publishing.

## What makes the renderer fast enough

These three changes took a 720p frame from 13-23 s to about 4 s at 16 samples, and stopped the GPU from
dropping the WebGL context.

- **The ground is a heightfield, not a distance field.** Step by `height / (slope bound - ray slope)` with
  a local slope bound. A grazing ray over flat ground takes 5 steps instead of 120.
- **Objects are marched only inside their bounding hull.** Intersect the ray with a few boxes and spheres
  first; most rays never touch the object march. Inside a bound, return the bound's distance until close.
- **Grass is analytic.** One blade is a parabolic ribbon: a ray meets it by solving one quadratic. Blades
  live in a grid; walk the cells along the ray (2D DDA), skip a cell when the ray passes above its tallest
  blade, and derive all blade parameters from two hashes. Keep every blade inside its cell so the first
  cell with a hit ends the walk.
- **One sample per draw call, in four bands.** Additive blending into RGBA32F targets, a 1-pixel read
  between bands. A single long draw is what triggers context loss.

## What makes the picture clean

- **Sample every light directly** at every hit: the moon as a narrow cone, the firefly as a small sphere,
  the window as a point just outside the wall. The emissive mesh itself only shows to the camera.
- **A light inside a character must skip that character in its own shadow rays**, or it lights nothing.
- **Grass transmits.** Give blades a back-side lobe and let shadow rays through them tinted green. Backlit
  blades and coloured shadows are most of the look.
- **Denoise with guides and variance.** Accumulate radiance with its squared luminance, plus first-hit
  albedo, depth and normal. An a-trous filter weighted by all four cleans 20 samples without smearing
  shadow edges. Keep sky, emitters and analytic glow in a second buffer that is never filtered.
- **Glow is analytic.** The halo around a point light in fog has a closed form (an arctangent along the
  ray). No volume marching, no noise.
- **Close-ups get a shadowless fill** from the camera side. It is a cheat every film uses.

## Traps

| You see | Cause | Fix |
|---|---|---|
| A black wedge across the sky with a dead-straight edge | `pow(x, 2.0)` with negative `x` is NaN on Metal | Multiply instead of `pow` wherever the base can be negative |
| "webgl context lost" after a few heavy frames | One draw call ran too long | Draw in bands, one sample per call, sync between them |
| Everything looks like fog at dusk, not night | Visible sky uses the same gain as the sky that lights the scene | Separate `skyVis` (dark) from `sky` (ambient), cut fog colour and glow by 5-10x |
| Stars look like snow | Too many, all the same brightness | Three layers, sixth-power brightness, 10-25% cell fill |
| A blurred blade covers the hero | Camera stands in the grass | Clear a corridor by blade hash (two zones: empty sight line, thinned sides); never by moving the camera |
| The pond shows no reflection | The mirror point lies on the shore | Solve the camera height: reflection point = camera + (h_cam / (h_cam + h_subject)) x distance must land on water |
| Bokeh discs of stars sparkle from frame to frame | Each disc is a few lucky rays | More samples for that shot only, then a light temporal filter in the encode |
| Hops land off the beat | The cue marks the landing, the animation starts at take-off | Advance the hop phase by the air fraction |
| Text on dark frames bands after upload | 8-bit gradients | Add grain after the temporal filter, never before |

## Optional narration

A narrator makes the film work with sound on, and it is the one part that cannot be code. Generate one
clip per caption (the starter used ElevenLabs v4 through varg, 11 lines, $0.11), put the clips in
`audio/vo/` and their start times in `timeline.json` under `narration`, then run `audio/mix_vo.py`: it
levels every line, ducks the music 9.5 dB under speech and brings the mix to -16 LUFS. Build with
`post/compose.py --narrated`, which also adds a credit line for the voice. Keep the captions on screen:
feeds start muted. Deliver both cuts and let the person choose.

## What you may claim

Say only what is true of the files. For the starter: story, characters, world, light transport, denoiser,
animation, score and sound effects are code written in the session; nothing was modelled, painted, sampled
or generated by an image, video or music model. The letterforms in captions are a system font, so do not
say "every pixel". If you add a narrator, say that the voice is an AI voice. Publish the source next to
the film.

## Files

- `scripts/smallest-star/src/shader.js`: the path tracer and post passes (GLSL in template strings)
- `scripts/smallest-star/src/engine.js`: accumulate, denoise, bloom, tone map
- `scripts/smallest-star/src/world.js`, `shots.js`, `vec.js`: layout, animation, helpers
- `scripts/smallest-star/render.ts`: Bun driver for headless Chrome; stills, ranges, modes, resume
- `scripts/smallest-star/audio/score.py`: the score and sound from `timeline.json`
- `scripts/smallest-star/audio/mix_vo.py`: optional narration over the score
- `scripts/smallest-star/post/compose.py`: captions, making-of wipe, end card, encode
- `scripts/smallest-star/live/`: the one-file interactive page
- `references/look.md`, `references/score-brief.md`, `references/commands.md`
