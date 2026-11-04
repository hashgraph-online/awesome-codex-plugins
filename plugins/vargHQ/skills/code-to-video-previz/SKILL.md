---
name: code-to-video-previz
description: >-
  Prototype a video in code with an agent. Decides if a shot needs a 3D prototype at
  all and which tool fits (Three.js, Blender, a phone act-out, storyboards, Remotion, Cinema 4D, Unreal), stages
  geometry, people, camera and light in real metres, copies a reference video shot by shot with a solved 3D camera,
  stages a shot from a painting or still, invents one when there is no reference, checks
  everything with numbers and frames, and writes the handoff to Seedance or other video models. Same scene file renders
  in Three.js and headless Blender. Use for "previz", "blockout", "3D animatic", "three.js or blender", "prototype this
  video", "copy this shot", "recreate this video in 3D", "stage this painting", "camera blocking with Claude or Codex", "code to video", "rank takes", "LLM judge", or when generated shots keep drifting. Not for a full multi-shot three.js
  film with a review UI (threejs-animatic, varg-previz), prompting a shot with no prototype (varg-video-prompting) or the full animation pass (video-animate).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
compatibility: >-
  Scene checks: python3 only. Three.js path: Bun, Chrome, ffmpeg, no npm (three.js loads from jsDelivr, so it needs the network).
  Blender and camera solving: pip bpy 5.2.3 on Python 3.13 through uv, or a Blender install. measure_shot.py: uv. Generation: the varg MCP (https://mcp.varg.ai/mcp) or any Seedance access.
---

# Code to video: a prototype in 3D, then a real video

Video models redraw the world on every call, so cameras wander, counts change and rooms rearrange. A prototype fixes
those things for free, before the paid step. The agent can build it, because camera and layout are maths. Three
limits decide everything below, so tell the person about them:

- **Agents can't watch video.** They check frames and numbers. Pacing and feel stay a human call.
- **Agents block well and model badly.** Cameras, layout and scale come out right. Curves, faces and hero objects don't.
- **The video model copies what you show,** bad motion included. A crude clip is an advantage, not a compromise.

## 1 · Does this shot need a prototype?

Find the one hard thing in the shot, then use the cheapest prototype that pins it down. People who tested previz and
say to use it selectively give the same order: words, then images, then references, then previz, each only when the last one fails.

| the hard thing | use | why |
|---|---|---|
| nothing exact: one or two subjects, randomness welcome | **no prototype**: prompt + start frame | a previz adds cost and can make motion worse |
| the idea and look of a sequence | **storyboard stills** | fast to redo, and stills are the cheapest place to find problems |
| timing, tempo, positions, crowd paths, side-on shots | **2.5D conte** in Remotion or HyperFrames | minutes to make. Not for orbits, occlusion, height or hands |
| an exact camera path, exact counts, spatial continuity, long takes | **3D prototype**: section 2 | this is what 3D is for |
| a human performance and a real camera could shoot it | **phone act-out** | carries weight and timing better than any stand-in |
| a performance and an impossible camera | **act-out → mocap → 3D** | Motion2MixamoRig, Move.ai or DeepMotion, then Blender |

No same-shot test of act-out against 3D has been published, so say that if asked. Faces are unsolved on every route.

## 2 · Pick the 3D tool

| pick | when | the catch |
|---|---|---|
| **Three.js** (default) | rough placement and the model fills in the rest; live and editable; no install, weak laptop, a phone; many shots in one diffable file; a code-rendered final | no rigs; agent-written human animation looks stiff |
| **Blender** | you must lock acting, camera and timing yourself; rigs, Mixamo or mocap, real assets; heavy sets; stills for storyboards; an artist will open the file | more tokens (one report, on a finished render: $20.39 vs $0.97 for the same prompt and model); needs a local install or `bpy` |
| **Cinema 4D** (Maxon's MCP) | you already own and know it, and a hero object needs a real rig and motion blur | paid; the GUI stays open; no headless path |
| **Unreal + MetaHuman** | fast human bodies, big casts, and you work on a Windows GPU | agent + Unreal + Seedance has not been shown joined end to end |
| **Gaussian splat world** (Marble) | the place itself is the hard part and nothing touches the set | one full report only, from a World Labs employee |

Nobody was found using Unity, Godot, Houdini (except simulation), Rhino or SketchUp for this. Skip them unless you
already live there. HyperFrames, After Effects and DaVinci belong after generation, for type and finish.

**You don't have to commit.** Write the scene as data (`staging.json`) and both Three.js and Blender render it, with
the same lens maths. Start in Three.js. Move to Blender (`--blend scene.blend`) when you need a rig or an asset.
For Blender setup, MCP vs headless and what to do by hand: `references/blender.md`.

## 3 · Name the object you're making

| object | for | looks like |
|---|---|---|
| **guide clip** | a video model, as `@video1` | crude and flat-lit, no text, no shadows, stand-ins. Exact seconds |
| **storyboard pages** | people, or a model as key frames | stills from the shot cameras, 2 to 4 per shot, captions |
| **code-rendered film** | the audience | textures, light, a pure function of time. No video model |

No video model named? A plain "render it as a clip" means a code-rendered film, so keep the light. One file can't be all three. An animatic with outlines, text and hard shadows has to be rebuilt before it can be a guide
clip, because "the reference video is a pixel channel, not a spec channel": whatever is visible can come back in the film.

## 4 · The loop

1. **Write the brief down** in the person's words, dated, with format, length, and what the shot must achieve.
2. **Write beats in seconds and metres.** Who, where, doing what, which way they face, the end state of each beat, one
   camera move per beat. "The parts you can't write are the parts that are vague in your own head."
3. **Write `staging.json`**, not a new engine. → `references/staging-format.md`
4. **Run the numbers:** `python3 scripts/check_staging.py staging.json`. Fix every ERROR.
5. **Render stills**, first, middle and last frame of each shot, and look at every one. Fix one thing at a time.
6. **Have a fresh agent review it.** A builder rates its own work too high. Give the reviewer only the frames, the
   reference and the beats, and ask for the biggest gap, not a score. Check its claims against an overlay before acting: reviewers are wrong too.
   To rank several takes: `references/judging.md`. Never a 1 to 10 score, and never "which is better?" with no criteria.
7. **The person approves the stills,** then the clip. Stop here for notes: they cost nothing now. If nobody can reply, make the call and say so in your report.
8. **Render the clip** frame by frame, never by screen recording.
9. **Hand it off** (section 7), one short test first, with a price and a yes from whoever pays.

Stop rule: 3 rounds without progress on one problem, then change the approach. A round should move a named number or fix a named gap. Matching a painting's colour takes more: sample the colours instead of guessing. Add nothing the beats don't ask for.

## 5 · Staging rules

**Geometry.** Build as little as explains the action. Same prompt, two previzes: "barebones won. The more detail you
put into the previs, the more literally Seedance follows it." Simplify by event, though: keep the heading, openings,
joints that bear on the action, contact surfaces and a signature silhouette. Use real metres and put a 1.75 m person
beside anything without a familiar scale. Round head on a capsule is enough for people unless the pose is the point.
Ambiguity ruins a pass, crudeness doesn't. A bent lamppost comes back as a snake, and loose blocks near a figure come
back as extra people. Mark a vehicle's front. Don't model hero props: get them from Tripo, Meshy or a sketch, or say
them in the prompt.

**Stand-ins: unsettled.** Capsules let the model invent the gait, jointed mannequins hand it a gait to copy, and half-animated
limbs are the bad middle ("toy soldiers"). Several creators report stiff results from posed figures. Start with
capsules. Use joints only when a specific pose must survive. Run a 4 to 6 s test on your model before a long pass.

**Blocking.** Block the action once in world time and make every shot a camera on it, so continuity comes free. Replace
hard animation with a before pose, an after pose and a cut: "let the cut sell the speed". Keep poses clean: models copy tangled
arms literally. For speed, remember that a slow proxy gives sluggish output and a slow move is ambiguous, so write its state in words.

**Camera.** Only what a real camera could do: "We try not to do anything a real camera couldn't physically do" (Patrick
Lin, Pixar). The "magic camera" is the known previs failure, and an 18 mm close-up of a face is what drives Roger Deakins "insane".
One move per shot, each with a job: "every shot was a zoom" is the common complaint. Vary the coverage and check it: the audit
warns when all moves match.

| want | lens |
|---|---|
| wide interiors, orbits | 24 to 30 mm |
| neutral, walking | 35 mm |
| over the shoulder | 32 to 45 mm (Deakins: 32 or 35) |
| closer shot, medium | 40 to 50 mm (Deakins: "But I have no rule") |
| close-up, compression | 65 to 85 mm |

Choose the lens from what the scene is about, not from what fits the frame. With a wide lens, boom instead of tilting, so verticals stay straight.

Write orbits as arcs (`"path": "arc"`), because a straight line between two orbit keys goes through the subject. Keep the
180° line in dialogue. Frame one size tighter than you want: generated framing comes back looser. Stiff camera? Don't animate jitter in;
write "handheld" in the prompt, or add noise in Blender.

**Light.** A guide clip says nothing about light. Keep it flat and put light in the image references and prompt, and
tell the model to reject viewport lighting. The exception is a shot whose composition is the light, such as a painted reference:
then block one hard source and its shadow edge, and use it for stills and look approval, not for the clip. Work in order: shadow,
then separation, then fill (Stephen Burum, ASC). One clear direction, or you get "a mushy light sandwich". Night is more black in
the frame, not lower exposure. Write light as numbers: direction, height, ratio (2:1, 4:1, 8:1), Kelvin (candle 1,850, tungsten
3,200, daylight 5,600). Words such as "Rembrandt" and "chiaroscuro" did not read reliably in the one test found, while backlight, silhouette and rim did.

**Order.** "Block it out first without animation", in static compositions with posed figures, then timing, which "needs
to be dead on or pretty close" (fxguide's notes on the previs guide by Chris Edwards of The Third Floor). Pixar's order is "camera, action, lights". Leave lights last.

**Determinism.** What's on screen is a pure function of t. No clocks, no unseeded random, no state between frames.

**Leave out** text, subtitles, labels, UI, TV static and glitter: Seedance read a subtitle in a previz and spoke it.

## 6 · References

| you have | do | details |
|---|---|---|
| **a reference video** | decide what you take. Same camera with a new look: feed the clip directly. Change the camera, the count or the set: split it, measure the camera, stage from picture coordinates, compare by overlay and by numbers | `references/reference-video.md` |
| **a painting or a still** | read it for light and structure. Use a grid, get lens and eye height from a known size, place everything from picture coordinates, compare by overlay | `references/paintings.md` |
| **nothing** | generate a reference image first, because with none the output is generic. Or ask for 3 named camera options as moving stand-ins and pick one | `references/no-reference.md` |

References fix the look, not the structure. Giving an agent a nice picture won't produce the right meshes, so structure
comes from the beats and the numbers.

## 7 · Turn it into a real video

Three routes, from people who have run them:

- **Guide clip to `@video1`.** Most common. Keeps camera, positions and cut timing. Also keeps stiffness.
- **Storyboard pages as image references.** PJ Ace's team swapped to this on one film because Blender motion felt stiff
  and reference images cost less, then said it was a per-shot choice. Fuller control over look, looser over motion.
- **Code-rendered final.** No video model. Suits machines, products, diagrams and flat characters, not people.

Division of labour, reached separately by users writing in three languages:
**video = camera, path, position, timing. Images = identity and look. Text = what boxes can't show.**

What we measured on our own 10-shot run (Seedance 2.5, grey previz, one film, not a controlled test):

- Cuts land on the planned frame, within one frame.
- Framing mostly holds, one size looser.
- **When the words disagreed with the previz, the words won.** In 2 of 2 shots where the prompt said "the android's face"
  or "close-up of the woman" over a previz from behind, the model turned the character to camera. So describe each shot as
  the previz shows it.
- **Camera moves are not guaranteed.** Of 7 shots with enough tracking to measure, 4 kept the direction, often with close
  numbers (zoom 1.124 vs 1.125), 1 stopped moving and 2 reversed. The one shot whose prompt named its move kept it.
  So **name the move in the words for every shot**, and measure the result: `uv run scripts/measure_shot.py`.

Other limits people measured: 10 to 15 s clips hold and 20 to 30 s drift (28 renders, Scenario); 16 s with 7 shots hit 6 of 6 cuts
within 0.07 s, and a 28 s piece lost 3 and added 4 (VLM harness). Keep runs short and in one location. Kling 4 tended to
ignore the previz in the one test found. Contact, fast action and identity in fights stay weak everywhere.

**Grey or colour: unsettled.** Grey: a colour previz once came back as the output, unchanged, and several people report
that grey adheres cleanly. Colour: Scenario reports an all-grey clip losing identity and a bare grey mannequin being refused
by a provider, and users map saturated colours to `@image` refs with success. Nobody has published a controlled test. **Default:
greyscale with characters separated by brightness. Use identity colours with a written legend when characters must stay
apart.** Test both on one short window before a long pass, because results vary by model.

The prompt: `references/handoff.md`. Copy-paste prompts for every step: `references/prompts.md`. For the full animation pass after this (model per shot, takes, sync, plates), use `video-animate`.

## 8 · Say honestly

- Report what you looked at and what you only measured. Passing a check doesn't mean it matches the reference, or that it's good.
- Never call a film "pure code" if a video model drew any of it.
- Generation costs money: quote with `estimate_cost`, get a yes, run one test first, report the billed cost.
- Study by copying, publish by transforming. Take a shot's move, height and rhythm into your own scene, never a sequence's
  staging plus its look. Tell the person when a reference is someone else's work. Details: `references/reference-video.md`.
- A person picks frames from ShotDeck and Shot Cafe: their terms ban automated tools.

## Files

| path | what |
|---|---|
| `references/staging-format.md` | the scene file and every command |
| `references/blender.md` | setup, MCP or headless, Workbench, what to do by hand |
| `references/reference-video.md` | Case A: copy a reference video |
| `references/paintings.md` | Case B: stage from a painting or still |
| `references/no-reference.md` | Case C: no reference at all |
| `references/handoff.md` | prompts and rules for Seedance and other models |
| `references/prompts.md` | paste-ready prompts |
| `references/judging.md` | rank takes with an LLM judge: what we measured, the biases, gate and pair prompts, what a judge can't see |
| `references/sources.md` | who said what, with links |
| `scripts/check_staging.py` | number audit, standard library only |
| `scripts/stage_three.ts`, `stage_three.html`, `cdp.ts` | three.js renderer (Bun, Chrome, ffmpeg) |
| `scripts/stage_blender.py` | Blender renderer (`bpy`) |
| `scripts/shots.py`, `grid.py`, `compare.py` | split a video, read a picture, compare a render (ffmpeg) |
| `scripts/measure_shot.py` | read a shot's move as a picture: pan, tilt, zoom, roll (uv, OpenCV) |
| `scripts/solve_camera.py`, `solved_to_staging.py` | recover a shot's real 3D camera with Blender's tracker, then turn it into a camera path |
| `scripts/place.py` | picture coordinates to world coordinates |
| `scripts/judge_pack.py` | a blind judging round: random names, both orders, a copy that must tie, scoring |
| `example/calling/` | Caravaggio's *The Calling of Saint Matthew*, staged from the picture |
| `example/ab-test/` | one 5 s shot as 4 variants (grey or colour, capsule or joints), to settle the open questions on your model |

## Related skills

`threejs-animatic` and `varg-previz` (a full three.js film with a review UI and pack builder), `video-animate` (animate from an approved previz, model per shot), `varg-video-prompting`
(prompting a shot), `video-moodboard` and `find-references` (look and references), `varg-consistent-characters` (identity),
`varg-ai` (generation), `hyperframes` (type and finish on top of the video).
