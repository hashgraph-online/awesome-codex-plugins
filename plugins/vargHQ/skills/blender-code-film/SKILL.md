---
name: blender-code-film
description: >-
  Make a short 3D film in Blender written entirely in Python by an agent (Claude Fable 5.2, Claude Code,
  Codex): the shots and the look as data, a world built from code (procedural terrain, hundreds of instanced
  props, node materials, lights, haze), one camera per shot bound to timeline markers, a stills-first approval
  pass, a quarter-size draft, a contact-sheet audit, a fresh critic subagent, then the final render to PNG frames
  and an ffmpeg encode with an optional varg music bed. Includes a tested starter (scripts/film.py, a 9 s
  three-shot film) and the Blender 5.x traps that turn frames black. Use when someone asks for a Blender
  animation or film made with code or Python, "make a video in Blender with Claude", a 3D short, music video,
  toy commercial or product film rendered in Blender, a low-poly or storybook 3D film, or a remake of a viral
  Fable 5.2 Blender video. Not for previz that feeds Seedance (code-to-video-previz, varg-previz), three.js
  films in the browser (karpathy-3d-story, code-3d-explainer), recording a browser game (code-game-trailer),
  2D motion graphics (hyperframes, kinetic-type-art) or AI-generated footage (varg-ai).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
compatibility: >-
  Blender 4.2+ run headless (`blender -b`; tested on 5.3.0), ffmpeg. Eevee needs no GPU setup: the starter
  (216 frames, 1920×1080, 96 samples, haze) rendered in 10 min 34 s on an Apple Silicon Mac (2.9 s/frame);
  quarter-size stills take under a second each. Music from varg (`generate_music`) is optional and needs the
  varg MCP (https://mcp.varg.ai/mcp) or VARG_API_KEY.
allowed-tools: Bash(blender:*) Bash(ffmpeg:*) Bash(ffprobe:*) Bash(bash:*) Read Write Edit
---

# Blender film from code

An agent can make a finished 3D film without touching Blender's interface: it writes one Python file that
builds the world, places the cameras and renders the frames. On the day Claude Fable 5.2 came out
(2026-11-09) this was one of the most saved formats on X:

- [@rileybrown](https://x.com/rileybrown/status/2119902109709537708): one prompt, live on stream. A desk
  room in Blender, the laptop screen showing a web page the model also built, 13 camera shots, golden hour to
  night to sunrise, graded, titled and scored. 4K rendered in 52 min on 10 rented GPUs for $5.75. 606k views
  and 6,165 bookmarks; his reply with the recipe alone got 812 bookmarks.
- [@alexmichael](https://x.com/alexmichael/status/2119876626179870838): "made this entire video from
  scratch, writing Python to control Blender" (117k views).
- [@kevin_t_ngo](https://x.com/kevin_t_ngo/status/2120198663062622581): a music video animated in Python and
  rendered in Blender; his earlier storybook film rebuilt a 2D code animation in 3D.

The starter in `scripts/film.py` is this skill's own test: a lantern orb drifts up a low-poly forest valley
at dusk in three shots (wide, follow, reveal), with haze, sparks and a warm rim light. Nothing is downloaded.

## 1. Ask before building

Put these to the person (in their language) and wait:

1. **Look**: low-poly storybook (flat shading, warm lamps), stylized toon, or photoreal (Cycles, slower).
2. **Length and frame**: 9–30 s; 16:9 for X and YouTube, 9:16 for Reels and TikTok, 1:1 for a feed.
3. **Sound**: none, a music bed from varg (about $0.10 per track; quote it from `estimate_cost`), or sounds
   synthesized in code.
4. **Render budget**: this machine with Eevee (minutes), this machine with Cycles (hours with volumes), or a
   rented GPU farm for 4K Cycles (Riley's 52 min on 10 GPUs cost $5.75).

## 2. Set up

```bash
blender --version || brew install --cask blender     # or the installer from blender.org
blender -b --factory-startup -P scripts/film.py -- --stills --draft --out render/stills
```

Always run headless (`-b`) with `--factory-startup` so the user's add-ons and preferences can't change the
picture. Arguments after `--` go to the script.

## 3. The film is data

Everything that changes the picture sits at the top of `film.py`:

- `LOOK`: the palette in linear RGB (sky, ground, materials, key and fill colors). One palette for the whole
  film; one warm key light and one cool fill; practical lights (lamps, the orb) for the rest.
- `SHOTS`: one row per shot with `start`/`end` frames, `lens` in mm, the camera's start and end position in
  metres, what it aims at (a moving point or an object), and `key`, the frame that `--stills` renders.
- The `build_*` functions: one per part of the world, in metres, seeded (`--seed`) so a re-render gives
  identical frames.

Write the beat sheet first (what happens in each shot, in one line), then turn it into `SHOTS`. Rebuild the
whole scene from scratch on every run (`read_factory_settings(use_empty=True)`); never patch a saved .blend.

## 4. Building the world in code

- **Ground you can ask about.** Make terrain a Python function of (x, y) (`ground_z` in the starter) and build
  the mesh from it. Then every tree, rock and path sits on the ground exactly, with no ray casts.
- **Hundreds of props, one mesh.** Build a prototype once, create objects that share its mesh
  (`bpy.data.objects.new(name, proto.data)`), then delete the prototype. The starter places 420 trees this way.
- **Keep the lens clear.** Sample every camera move and keep props 5 m from it, or the first wide shot opens on
  a giant tree trunk (the starter's first render did).
- **Materials are node trees** set in code: Principled BSDF with `Base Color`, `Roughness`, `Emission Color`
  and `Emission Strength`. Dark albedos (below 0.05) read as black under a grazing sun; start near 0.1.
- **Cameras**: one camera per shot with a Track To constraint on an aim object, depth of field focused on it,
  and a timeline marker at the shot's first frame with `marker.camera = cam`. Keyframes from
  `keyframe_insert` are Bezier and already ease in and out.
- **Sound in code** if chosen: synthesize with numpy and write WAV beside the frames; `mux.sh` takes any audio.

## 5. Stills first, then motion

1. `--stills --draft`: one quarter-size still per shot (under 1 s each after the first run). Look at them.
2. Send the stills to a **fresh critic** (below). Fix, repeat.
3. `--stills` at full size: show the person and get a yes before any animation.
4. `--draft`: every frame at quarter size, then `scripts/sheet.sh render/draft 12` makes a contact sheet of
   every 12th frame. Check: the camera never clips through geometry, nothing pops or flickers, no shot is
   empty, exposure holds across cuts, the subject stays in the frame.
5. Final: `blender -b --factory-startup -P film.py -- --out render/final`, or `--shot <name>` to redo one shot.
   Frames are PNGs, so a crash keeps every finished frame and one shot can be redone alone.
6. `scripts/mux.sh render/final film.mp4 [music.mp3]` encodes H.264 CRF 18, cuts the music to the film, fades
   it out over the last second and normalizes it to -14 LUFS.

## 6. The critic loop

The builder never grades its own work (a rule that spread with Fable 5.2 prompts such as
[@everestchris6's](https://x.com/everestchris6/status/2120175941616128277)).

- After each round of stills or each draft, start a new subagent that has seen none of the work. Give it only
  the beat sheet and the images.
- It answers yes or no, then at most five problems ranked worst first, each with a fix in numbers ("camera
  2 m lower", "key light 30% dimmer", "orb 20% smaller"), then what already works.
- Fix the worst problem first, render again, and ask a new critic. Repeat until yes.
- For taste (palette A or B, lens 24 or 40 mm), show a critic both versions labelled A and B and let it pick.

## 7. Eevee or Cycles

| | Eevee | Cycles |
|---|---|---|
| Starter at 1920×1080 | 2.9 s/frame (96 samples, with haze) | not practical with haze |
| One 960×540 still, haze on | under 1 s | 3 min 16 s (64 samples, Metal GPU, includes the first kernel compile) |
| One 960×540 still, haze off | under 1 s | about 1.5 s (48 samples, denoised) |
| Whole film at 960×540, haze off (216 frames) | 2 min 29 s (0.7 s/frame) | 8 min 19 s (2.3 s/frame, 48 samples) |
| Use for | stylized, low-poly, toon, drafts, most finals | glass, caustics, photoreal interiors, product shots |

Volumes are what make Cycles slow: drop the haze (`--no-haze`) or render Cycles finals on a GPU farm.
`film.py --engine cycles` switches Cycles to the GPU backend the machine has (Metal, OptiX, CUDA, HIP,
oneAPI); with `--factory-startup` it would otherwise render on the CPU.

## 8. Traps in Blender 5.x (each one hit while testing this skill)

- **A world volume turns the frame black.** In Eevee the world's volume is infinite and swallows the sun and
  the sky at any density. Put haze in a large cube around the set instead (`build_haze`), and raise
  `scene.eevee.volumetric_end` past the set (default 100 m) or the far sky shows a clean band.
- **A light inside a glowing mesh lights nothing.** The mesh shadows its own lamp. Set
  `obj.visible_shadow = False` on the orb, bulb or lantern.
- **`action.fcurves` no longer exists** (Blender 5 actions have layers and slots). To edit curves use
  `bpy_extras.anim_utils.action_get_channelbag_for_slot(obj.animation_data.action,
  obj.animation_data.action_slot).fcurves`, or avoid it: default keys already ease.
- **Engine ids changed.** Eevee is `BLENDER_EEVEE` in 5.x and was `BLENDER_EEVEE_NEXT` in 4.2–4.x. Read the
  enum instead of hard-coding it (the starter does).
- **Emission input names.** Principled BSDF has `Emission Color` since 4.0 (older scripts set `Emission`).
- `Material.use_nodes` and `World.use_nodes` print deprecation warnings in 5.x; they still work until 6.0.

## 9. Briefs to start from

Short briefs that work as one prompt (fill the brackets; ask the section 1 questions first):

```text
Make a [20]-second [16:9] film in Blender, entirely in Python, run headless. Low-poly storybook look,
flat shading, warm practical lights, soft haze. Story in [4] shots: [one line per shot]. One palette:
[cream, teal, warm orange]. Every model, material and texture from code, nothing downloaded. Stills of
every shot first; a fresh critic reviews them before any animation. Then a quarter-size draft and a contact
sheet, then the final at 1920x1080, then an MP4 with [a calm piano bed from varg].
```

```text
Make a 15-second 90s-style toy commercial in Blender with Python: [the toy] on a turntable, a hero push-in,
two close-ups of [features], a glow moment, then a packshot. Plastic materials with clear-coat, a
glossy studio floor, three-point light plus one colored rim. No real brands. Stills first, critic loop, then
render and mux with an upbeat jingle bed.
```

```text
Make a music video in Blender for [song.mp3]: measure the BPM, cut on the downbeats, drive the lights and one
hero object's scale from the kick. [Theme], [palette], [3-6] shots. Contact sheet every 12th frame before
the final render.
```

## Files

- `scripts/film.py`: the starter film (world, shots, render modes `--stills`, `--draft`, `--shot`,
  `--engine cycles`, `--samples`, `--percent`, `--no-haze`, `--seed`). Replace the world and `SHOTS` with yours.
- `scripts/sheet.sh`: contact sheet of every Nth frame (frame numbers when ffmpeg has drawtext).
- `scripts/mux.sh`: frames (+ music) to MP4.

Related: `code-to-video-previz` (a Blender or three.js blockout that drives Seedance),
`code-game-trailer`, `code-3d-explainer`, `model-split-screen` (Fable vs Opus, Eevee vs Cycles),
`video-sound`, `varg-ai`.
