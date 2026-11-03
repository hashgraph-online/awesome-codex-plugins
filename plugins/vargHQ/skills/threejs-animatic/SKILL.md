---
name: threejs-animatic
description: >-
  Build a three.js animatic ("animatronic", 3D previz, blockout) of a multi-shot video: every storyboard shot
  becomes a schematic 3D scene drawn in code, with jointed mannequins and poses, master sets in real metres and
  props, a real camera per shot (START/END keys, lens in mm, move and ease), timed to the music or voiceover,
  reviewed in the browser with a top-down set map of every camera frustum, approved, exported as a camera plan,
  rendered to MP4 frame by frame (headless Chrome or HyperFrames), then used as the @video1 reference for
  Seedance 2.5 video-to-video on varg so the generated shots keep the approved camera and blocking. Use when
  someone asks for a three.js animatic or animatronic, a 3D previz or blockout, camera blocking, a camera plan,
  shot sizes and lenses, a grey-box of a storyboard, previz to Seedance, or a reference video for
  video-to-video. Includes a working starter project (no npm).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
compatibility: >-
  Starter: a browser, Bun, Google Chrome or Chromium, ffmpeg; three.js loads from jsDelivr (pinned). HyperFrames
  path: npx hyperframes. Generation: the varg MCP (https://mcp.varg.ai/mcp) and credits on the varg account.
---

# three.js animatic: approve camera and blocking in code, then let Seedance redraw it

AI video models redraw the world on every call: cameras wander, rooms change layout between shots, a person ends
up as big as their car. A three.js animatic fixes camera, geography, scale and timing **for free**, before the
paid step. It is a grey-box: it approves where things are and how the camera sees them, never the look. The
approved clip then goes to Seedance 2.5 as `@video1`, and the generated shots keep that camera and blocking.

Distilled from real production sessions: a 36-shot vertical music video (previz → 13 Seedance runs), product and
launch films, and a deterministic three.js film rendered through HyperFrames.

## When to use it, and which tool

| project | do |
|---|---|
| 1–3 shots, simple camera | skip the animatic: a still per shot, approve, then image-to-video |
| 3–15 shots, one or two places | **this skill + `starter/`**: hand-key the cameras, review, render, pack |
| a storyboard of 15+ shots, songs, many locations | this skill for the craft, plus the `varg-previz` skill for its full app: auto cameras from storyboard words ("MCU, 3/4 left, push in"), `pack.json` + board builder, story structure and sheet guides (in this repo: [`varg-previz`](../varg-previz/)) |
| the animatic itself is the film (3D product shot, explainer) | this skill, render path B (HyperFrames) with HTML text on top |

## Quick start

```bash
cp -r <this skill>/starter my-film/previz && cd my-film/previz
bun serve.ts                          # http://localhost:8777/  review UI: shot view, set map, timeline, panel
bun tools/check.ts                    # headless: UI screenshot, frames per shot, contact sheet, seek-safety test
bun tools/capture.ts                  # renders/animatic.mp4, frame-exact, 24 fps
```

The demo is generic: two mannequins at a cafe table, a drone flies in and lands; 3 shots, 10 s, 16:9, 120 BPM.
Replace `js/config.js` (format, bpm), `js/sets.js` (the place), `js/shots.js` (shots + blocking). The rest is the
engine. `starter/README.md` lists every key and file.

## The workflow

1. **Brief.** Write the director's words verbatim, dated, in `brief.md`. Lock format (aspect, length, fps),
   music or VO, BPM. Every later note gets applied to brief, shot list and animatic in the same pass.
2. **Shot list.** One entry per shot: `id`, `start`/`end` (cuts on bar lines when there is music; the hook in the
   first 2–3 s), `picture` (what we see), `action` (what happens, written for the video model), camera words,
   `subjects` to check. In the starter this is `SHOTS` in `js/shots.js`; long projects keep a
   `storyboard.json`.
3. **Master sets.** One set per location, built from primitives in real metres from one master plate, with every
   story object named in `S.o`. → `references/sets-and-blocking.md`
4. **Mannequin blocking.** Jointed mannequins posed from a pose library, blended by time ramps; the action is
   blocked ONCE in world time (`BLOCKING(S, T)`), and every shot is only a camera on it.
   → `references/mannequin-rig.md`
5. **Cameras.** Per shot a START and END key (position, look-at target on the subject, lens, roll), an ease and a
   path (`line`, or `arc` for orbits). Key them in code, then fix them by eye in the UI (`1`/`2`, drag, write).
   → `references/camera-language.md`
6. **Review.** Shot view + top-down set map with every START/END frustum + automatic warnings (out of frame,
   on the edge, blocked, camera inside geometry). Run `bun tools/check.ts` and LOOK at `checks/sheet.png`
   (START, middle, last frame before each cut). Do not report a shot as fine without having seen it.
7. **Approve.** Mark each shot approved / needs a fix with a note, `⌘S`. If the direction is still open, approve
   stills first (`capture.ts --stills`) on a board, animate after.
8. **Camera plan.** "export plan" writes `camera_plan.md` (size, angle, lens, move, positions, status, notes) and
   `camera_plan.json` for prompts and tools.
9. **Render the MP4.** Path A: `bun tools/capture.ts` (headless Chrome over CDP, frame i = t i/fps, ffmpeg).
   Path B: `bun tools/make_hf.ts` → `npx hyperframes render hf` when the animatic needs HTML text, audio or
   Studio edits. Both call the same `film.pose(t)`. → `references/seek-safe-rendering.md`
10. **Seedance pack.** Group shots into runs (one location, consecutive shots, 4–30 s), render each run as a
    greyscale clip with `--shots … --grey`, pick image references for exactly what is in frame, write the prompt.
    → `references/seedance-v2v-pack.md`
11. **Generate on varg.** Upload, `estimate_cost`, a yes from the person paying, ONE run first, then the batch.
    QA every output against its `@video1`, cut it back onto the timeline with the run's placement file.

Spend nothing before step 11 except cheap stills. Steps 1–9 are free, and notes cost least there.

## Camera cheat sheet

Size = frame height at the look-at target, `2·d·tan(vFOV/2)`:

| ECU | CU | MCU | MS | MLS | FS | WS | EWS |
|---|---|---|---|---|---|---|---|
| < 0.2 m | < 0.4 m | < 0.7 m | < 1.1 m | < 1.5 m | < 2.4 m | < 8 m | ≥ 8 m |

For objects divide by `height / 1.8` (a 0.3 m bottle: 0.17). Angle from pitch: < −60° top, −60…−15° high,
±15° eye level, 15…60° low, > 60° worm's eye; roll > 5° dutch.

Lens (full-frame equivalent, 36 mm on the long side) → three.js vertical FOV:

| lens | 18 | 24 | 35 | 50 | 65 | 85 | 135 |
|---|---|---|---|---|---|---|---|
| 16:9 vFOV | 58.7° | 45.7° | 32.3° | 22.9° | 17.7° | 13.6° | 8.6° |
| 9:16 vFOV | 90.0° | 73.7° | 54.4° | 39.6° | 31.0° | 23.9° | 15.2° |

Moves as keys: push in / pull out = `p` along the view, same `t`; zoom = `fov` only; truck = `p` and `t`
sideways; crane = `p.y`; pan/tilt = `t` only; orbit = `p` around a fixed `t` with path `arc`; whip = `whip` ease;
impact = `shake: [s]`. One move per shot.

Grammar: keep all cameras of a dialogue on one side of the 180° line (check the map); match eyelines; change angle
by ≥ 30° or one size between consecutive shots of a subject; cut on action or on the beat; vary the coverage.
Narrow frames: horizontal half-FOV = `atan(tan(vFOV/2)·W/H)`; at 9:16 and vFOV 55° that is 16°.

## Lessons and gotchas (from real sessions)

**Building**
- One location = one master set = one master plate. Wides and close-ups share it, or layouts and faces drift.
- Real metres and a 1.8 m mannequin beside every vehicle, product or creature. Models otherwise draw a person as
  big as their ship. Judge shot size against the main subject (a ship by its length, not by a person).
- Mannequins need real limbs, a head with a nose, and feet. Capsules come back as logs or bollards.
- Separate characters by luminance (light top vs dark top): the Seedance reference is greyscale.
- Keep poses clean and props in hands rare. Seedance copies poses literally: arms tangled around a helmet and a
  card in a fist both came back as artefacts. Simplify in the previz, say the detail in the prompt.
- Light every set with a hemisphere fill plus one key. A one-light mesh facing away renders as a black cutout; a
  dark creature against black space vanished until it got a rim light.
- No text, noise, TV static or glitch walls in the previz: text comes back garbled, static comes back as mush.
- Block action once in world time; per-shot cheats only where the wide cannot see them.

**Reviewing**
- Look at every frame. In one 36-shot pass the automatic and visual checks found: a camera inside a bulkhead
  (the shot showed only wall), a headrest hiding the subject, a head 33° below the axis with a 30° half-FOV (out of
  frame in 9:16), a drone flying straight into the lens, a glowing prop covering the frame, a wide that lost both
  subjects. The top-down frustum map shows most of these at a glance.
- Auto cameras and first guesses are starting points: expect to fix about a third of them by eye.
- Previz is where coverage variety is decided: all-frontal medium shots were the main review complaint once.
- Story notes are cheap here and expensive later ("the reveal must be more epic", "too long a pause between
  scenes", "make the weapon readable"): re-block and re-time in the animatic, not in generation.
- Record notes verbatim with dates; apply each one everywhere in the same pass.

**Rendering**
- What is on screen must be a pure function of t: seeded random, no clocks, no state between frames, speeds
  integrated in closed form. HyperFrames renders frames in parallel workers out of order.
  `tools/check.ts` proves it by comparing pixels across render orders.
- Render frame by frame (`capture.ts` or HyperFrames), never by screen recording.
- Headless Chrome: `--headless=new --use-angle=swiftshader --enable-unsafe-swiftshader`; a plain `--screenshot`
  also needs `--virtual-time-budget=8000` or it captures before the first WebGL frame.
- HyperFrames + three.js: `data-duration` on the root is required; pin `three` (and `three/addons/`) in the import
  map; heavy setup goes on `window.__hf.buildReady`; check the last frame before each cut.
- Verify the tail of a padded run clip: the blocking keeps going while the camera holds, and later action can
  walk into frame.
- Review-UI bugs met for real: a body state class equal to a component class hid the whole page (prefix state
  classes); keys before the first frame had no current shot (select it at init); a server without Range support
  could not seek audio (fetch it into a blob).

**Seedance video-to-video**
- Every run needs an image reference for every character, product and place in frame; without one, the
  mannequin came back as a real "toy" person.
- Send `@video1` greyscale and say "copy only camera, cuts and blocking; the result must not look like @video1".
  One colour previz came back unchanged, as the output.
- References only for what is in frame: crop sheets; no exterior stills for interiors; no stale stills.
- References under 300 px wide were rejected: pad crops.
- Output framing is looser than the previz: frame one size tighter.
- Times in prompts are absolute from the clip start. Look line = style only; light per run.
- Runs: one location, consecutive shots, whole seconds 4–30; don't split a continuous scene into tiny runs.
- Image-edit stills for plates and key frames from the blockout render as the FIRST file ("keep camera and
  geometry exactly; grey blocks = …"); an environment image alone still drifted per camera.
- Estimate before spending, quote it as the ceiling, one run first, never resubmit a running job.
- QA every output against its `@video1` (stacked frames), fix small artefacts in the edit, regenerate only what
  the edit cannot fix.

## Files

| path | what |
|---|---|
| `references/camera-language.md` | sizes, angles, lens table, moves as keys, coverage rules, the narrow frame, camera words in prompts |
| `references/mannequin-rig.md` | joint hierarchy and sizes, sign conventions, pose layers, walk cycle, props, readability for AI |
| `references/sets-and-blocking.md` | master sets from plates, lighting, world-time blocking, cheats, labels, the set map |
| `references/seek-safe-rendering.md` | the determinism contract, CDP capture, HyperFrames path, troubleshooting |
| `references/seedance-v2v-pack.md` | runs, the greyscale clip, references, a generic prompt, the `call_tool` request, QA |
| `starter/` | the working project: review UI, set map, camera editor, save/export, checks, MP4/stills capture, HyperFrames builder |

## Related skills

`varg-previz` (full previz app, auto cameras, pack builder), `varg-ai` (models, prices, uploads, jobs),
`varg-video-prompting` (prompting Seedance and other models), `varg-mockups` (still boards before animation),
`varg-consistent-characters` (character and location sheets), `hyperframes` and its three.js adapter (HTML → MP4,
text over the animatic).
