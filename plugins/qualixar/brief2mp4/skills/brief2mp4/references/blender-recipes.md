# Blender motion recipes

Six parameterised scripts for motion that is hard to get right by hand, plus one for a liquid add-on. They sit in `3d/templates/recipes/` next to the 3D pack, run headless in the system Blender, and each reports numbers that prove the motion did what it says. Start from the one that matches the brief, change its parameters, look at three stills, then render.

| Brief says | Recipe | The measurement that proves it |
|---|---|---|
| "seamless loop", "loops forever", a GIF-style background | `loop` | frame 1 and the last frame are the same picture; every curve is cyclic |
| "speed up the middle", "hold the hit longer", fit picture to a voice or beat | `retime` | the pose at each marker is the old pose, only later or earlier |
| "cloth falls on", "a sheet over", a tablecloth, a flag landing | `cloth` | the sheet came down, stays above the floor, rests on the object, drapes |
| "a chain swings", "a hinge", a door, a pendulum, a hanging sign | `rigid` | every joint stays closed for the whole swing |
| "unfolds", "folds in half", paper, a map, a leaflet | `fold` | the width halves per fold, the layers stack, the free edge swings on an arc |
| "walks in", "walks forward", a figure crossing the frame | `walk` | a planted foot moves less than 2 mm a frame; the body travels speed x time |
| a liquid, pouring, a splash (add-on you install) | `flip_bake` | see `references/generators-3d.md` |

## Running one

```bash
b2m3d recipe list
b2m3d recipe run loop -- --loop-frames 73 --turns 1 --out frames --render-frames 1-72
# without the pack's command, straight through Blender:
blender -b --factory-startup --python-exit-code 1 -P <skill>/3d/templates/recipes/b2m_loop.py -- --loop-frames 73 --out frames
# inside a live Blender: references/blender-live.md
```

Every recipe prints one line, `B2M3D_RECIPE {json}`, with its measurements and the list of frames it wrote. `b2m3d recipe run` returns that JSON. Most recipes also report `ok` and `warnings`: a measurement out of its range (a chain leaving the frame, a fold wider than it should be, legs that cannot reach) sets `ok` to false and prints a `WARNING b2m:` line, so a bad number is never silent. Settings that cannot work (a sheet dropped from inside its object, a chain longer than its anchor is high) are refused before anything is built. Run Blender with `--python-exit-code 1`, as `b2m3d recipe run` does, so a refused or crashed recipe exits 1 with its message instead of 0. Frames are named `0001.png`, `0002.png`, so `scripts/finish.sh --in frames --seconds N` reads them directly (`--seconds` is required).

Options every recipe takes:

| Option | Default | Meaning |
|---|---|---|
| `--out` | none | folder for frames; with none, the recipe only measures |
| `--render-frames` | all | `1,48,10-12`; frames render in ascending order so simulations step forward |
| `--width`, `--height`, `--fps` | 1920, 1080, 30 | |
| `--samples`, `--engine` | 16, `EEVEE` | `EEVEE`, `CYCLES` or `WORKBENCH`; engine names are tried in turn for the installed version |
| `--fmt` | `PNG` | `BMP` for tiny test frames |
| `--bg --floor --subject --accent --ink` | a dark neutral set | hex colours, `#rgb` or `#rrggbb` (converted to linear); pick a palette for your video and pass it |
| `--caption` | none | one short line of flat 3D text, bottom left inside the safe margin, after a short bar in the subject colour |
| `--caption-px` | 54 | caption height in pixels at the render size; 34-40 reads as a small lower third at 1080p |
| `--caption-frames`, `--caption-fade` | whole shot, 0 | `a-b` and a fade length in frames: the caption fades in while rising 10 px at `a` and fades out by `b`, so it is gone before a dissolve to the next shot |
| `--look` | `plain` | `plain`: a floor plane and three lights, fast. `studio`: a seamless backdrop (the floor curves up into the back wall, so there is no horizon), a soft key, fill, rim and a wash on the wall, ray-traced reflections and bounce light, exposure -0.35 for a pale set |
| `--orbit` | 0 | degrees per second the camera turns round its aim at constant speed, centred on the middle of the shot and continued past both ends; give every shot in a film the same direction |
| `--stage` | on | `--stage 0` adds only the subject and keeps the scene's own floor, lights, camera and world |
| `--json` | none | also write the result to this file |

The stage is the recipe from `references/blender.md`: a large key light, a warm rim, a weak fill, a floor, a tracking camera, a neutral view transform. Lights ride an `b2m_aim` empty, so a recipe that moves the aim point (`walk`, `fold`) keeps its lighting; the camera sits on a `b2m_orbit` pivot at the aim, which `--orbit` turns. For several shots meant to read as one film, give every recipe the same palette and `--look studio`, and join the shots with short dissolves (example 10 does this).

The caption is 3D text 1 m in front of the lens, so camera depth of field would blur it; the recipes leave depth of field off.

Blender 5 moved animation curves into slotted actions, where `action.fcurves` no longer exists. The recipes read curves through `b2m_common.fcurves()`, which handles 4.x and 5.x. If you write your own script, do the same.

## loop: a seamless loop

A faceted gem turns whole turns, bobs, and carries a ring that rocks. `loop_frames` is the last frame; the loop is `loop_frames - 1` frames long, because the last frame repeats the first. Render frames `1 .. loop_frames - 1` and the video loops with no stutter; frame `loop_frames` exists so the seam can be checked.

Knobs: `--loop-frames 73`, `--turns 1` (a whole number, or the seam jumps: the recipe refuses a fraction), `--bob`, `--bob-cycles`, `--rock`, `--rock-cycles`, `--glow` (the ring's emission, 0 for plain lacquer). Frames past `loop_frames` keep looping, so `--render-frames 1-150` plays the loop twice in one render. `--orbit` must turn the camera a whole number of turns per loop (`360 * fps / (loop_frames - 1)` degrees a second for one turn), or the recipe refuses it, because a part turn shows at the seam. `loop_frames` is at least 4.

How it works: the spin has two linear keys and a Cycles modifier in offset mode, so the value keeps counting up instead of wrapping to zero. Bob and rock are keyed every quarter cycle with smooth handles and a plain Cycles modifier. The Cycles modifier must be the first modifier on the curve: Blender then smooths the handles across the seam.

Reads: `curves`, `cyclic_curves` (must be equal), `pose_gap` (the gem's, the ring's and the camera's matrices at frame 1 against the last frame), `seam_slope_gap` (slope before the seam against after it, as a share of the curve's range). The test renders frames 1, 13 and 25 at 96x54 and compares pixels: frame 1 against 25 is identical, frame 1 against 13 is not.

Traps: every motion must complete a whole number of cycles in the loop, or that one shows a jump at the seam, so keep every `*_cycles` an integer. Simulations (cloth, particles, rigid bodies) are not cyclic: bake a loop of those separately.

## retime: change when the beats happen

Timeline markers name the beats (`start`, `hit`, `end`). `retime_between_markers(scene, {"hit": 40, ...})` moves them and stretches or squeezes every keyframe, and its handles, between two markers by one ratio. A marker you do not name stays where it is, so `{"hit": 40}` alone moves the hit and squeezes the segments either side of it; the scene's end frame follows the old end through the same map. Keys on the objects, their data and shape keys, their materials and node trees, and (with no object list) the world are all remapped. The demo is a ball that arcs onto the floor at `hit` and leaves toward `end`; its caption is made after the retime, so its fade times are the new timeline's.

Knobs: `--marks start=1,hit=25,end=49` (how it was authored), `--targets start=1,hit=40,end=60` (where it should land; empty means no retime), `--tail` (frames kept after the last marker). Target frames are whole frames (markers sit on whole frames) and must increase in the order of the markers, unnamed ones included, or the recipe stops with a message naming them.

How it works: it first turns every handle into a free handle, because auto handles are recomputed from the new key positions and bend the curve; with fixed handles each segment is the old segment stretched, so the value at any mapped time is exactly the old value. Put a key on every marker you retime between; a segment that straddles a marker without a key is bent.

Reads: `markers_after`, `shape_error` (largest difference between the old curve at old times and the new curve at the mapped times; about 1e-7 in the test), `marker_pose_error` (the pose at each marker's new frame against its authored pose: a marker left behind shows here), `moved_keys`. The test also renders the hit before and after: the picture at frame 25 originally equals the picture at frame 40 once retimed.

Use it to fit picture to a measured voice: place a marker on each word or beat in the timeline, then retime to the times from `scripts/retime.py` or the beat grid. Never time-stretch the voice instead (`references/sound.md`).

## cloth: a sheet drops onto an object

A 2.4 m grid with a Cloth modifier falls 1.6 m onto a sphere or box standing on the floor. The floor and the object carry Collision modifiers. The simulation is stepped once from frame 1 in order, then frames render in any order.

The cloth's speed multiplier is set to `30 / fps` (and its solver steps raised to match), because Blender steps cloth once per frame: without that, the same drop lands 2.5 times sooner at 60 fps than at 24. `half_fall_s` (the seconds from release until the centre has fallen half way) is 0.25 to 0.27 s at 24, 30 and 60 fps.

Knobs: `--object sphere|box|none`, `--object-size`, `--cloth-size`, `--cloth-res` (20 is quick, 32 looks good), `--drop-height`, `--delay` (frames the sheet hangs still before release, so the eye sees it before it falls), `--mass`, `--bend` (low drapes into folds, high holds its shape), `--quality`, `--self-collision`, `--smooth-levels 1` for a smoother render (the subdivision is render-only: switching a modifier on and off while stepping resets the cloth cache, so the numbers are read from the simulated grid), `--thickness` (render-only Solidify, 0.01 reads as fabric), `--sheen` (the soft edge glow of cloth, 0-1).

Reads: `start_mean_z`, `final_min_z` (must stay above `floor_z`), `final_max_z`, `centre_z` against `object_top_z`, `edge_mean_z` (lower than the centre when it draped), `motion_last_10_frames` (near zero when settled), `nan_vertices`, `half_fall_s`. The tests assert it fell, never went through the floor, rests on the object, hangs lower at the edges, with `--object none` lies on the floor, and falls at the same speed in seconds at 24 and 60 fps. A drop height inside the object, or a `--delay` that never releases the sheet within `--frames`, is refused.

Traps: if the cloth passes through the object, raise `--quality` before raising resolution. Self collision is slower; a plain drape works without it, but at 56 quads a side and up the hanging folds touch, and without it they show thin seams where the sheet passes through itself. Give a 1.6 m drop at least 60 frames at 30 fps: at 60 the test sheet is on the object and moving about 2 cm per vertex over the last ten frames.

## rigid: constraints that hold

A fixed anchor and `links` boxes joined by rigid-body constraints, released from `release_angle` degrees. `--joint hinge` turns about the Y axis, so the chain stays in one plane (the constraint empty is rotated 90 degrees about X so its Z axis points along Y). `--joint point` is a ball joint, free in every direction. `--links 1` is a pendulum.

A chain that would reach the floor (`links * link_length + link_width` at or above `anchor_height`) is refused, since the floor is not a collider, and so are links shorter than twice their width (they overlap at the joints and jitter apart).

Knobs: `--links`, `--link-length`, `--link-width`, `--joint`, `--release-angle`, `--mass`, `--damping` (0 swings forever), `--anchor-height`, `--frames`, `--stand` (a post and arm that hold the anchor; looks only), `--rounded` (links drawn as rounded bars with a pin at each joint; the physics shape is still the box).

The camera is placed from the chain's reach: the whole arc (the links' length to each side of the anchor, down to the lowest point) fits the frame with a margin, so a long chain released near level is not cut off. A many-link chain can whip above its anchor; if any joint leaves the frame, `frame_margin` goes below zero and `ok` is false with a warning.

Reads: `frame_margin` (the closest any joint or the tip comes to the frame edge, as a share of the frame; below zero means it left the picture), `constraints`, `max_joint_gap` (largest distance, over every joint and frame, between the end of one link and the start of the next), `tip_travel_x` (so a chain that never moved fails the check), `max_out_of_plane`, `min_z` (the lowest link end), `period_s`, `ok`, `warnings`. Tests: the gap stays under 5 percent of a link; a 1 m rod released at 20 degrees swings with a 1.65 s period against 1.64 s from the formula `2 pi sqrt(2L / 3g)`; the control deletes the constraints and the links fall metres apart.

Traps: the solver runs 20 sub-steps and 60 iterations per frame. Stiffer joints hold tighter: for eight 0.5 m, 3 kg links released at 80 degrees from a 4.5 m anchor the largest gap was 6.7 mm at Blender's defaults (10 and 10) and 1.5 mm at 20 and 60 (Blender 5.2.1). Collisions between neighbouring links are off (`disable_collisions`), or the joints fight their own boxes.

## fold: a sheet folds, again, and again

Shape keys, one chain per fold. A single key from flat to folded blends vertex positions in a straight line, so the free edge slides through the sheet and the paper squashes. With `--fold-steps 6` there is a key every 30 degrees, each relative to the one before (`relative_key`), and the free edge follows the arc. The crease is rounded over `--crease-radius`, capped at 6 percent of the stack's width so the later folds of a shrinking stack keep a crease in proportion; folded layers stack `--layer-gap` apart (so they do not touch); no crease point dips under the layer it started on; and the slices are timed with a smoothstep so each fold starts and ends gently.

Knobs: `--folds` (each halves the width of the stack), `--sheet-width`, `--sheet-height`, `--grid-x` (even), `--grid-y`, `--fold-frames`, `--fold-steps`, `--pause`, `--crease-radius`, `--layer-gap`, `--back` (a second colour for the underside, which shows as each fold turns it up), `--thickness` (render-only Solidify, under `--layer-gap`), `--follow` (on: during each fold the camera eases to the middle of the stack and closes in to 0.82 of its distance, so the shrinking stack keeps its place and size in frame).

Reads: `flat_width`, `final_width` against `expected_width` (`width / 2**folds` plus half the folded stack's thickness, `(2**folds - 1) * layer_gap / 2`, because the last crease wraps round the whole stack), `final_height`, `layers` (`2**folds`) and `final_thickness` (`(2**folds - 1) * layer_gap`), `min_layer_separation`, `half_fold_edge_z` against `half_fold_expected_z` (a quarter turn puts the free edge at the height of half the sheet), `area_ratio`, `shape_keys`, `min_z` (the lowest point over every frame), `ok` and `warnings` (a width more than 8 percent off `expected_width`, an area stretch over 20 percent, a crease under the sheet).

Traps: the sheet stretches a little in the crease zone: 4 percent more area at the defaults (two folds), 12 percent for three folds at `--layer-gap 0.01`, because a thick stack's outer layers wrap a longer way round. A smaller radius with a larger `--grid-x` is crisper, and a thinner `--layer-gap` stretches less. A fold count whose stack would be thicker than half its own width (four folds at 0.01) is refused; lower `--layer-gap`. `--fold-steps` is at least 6: one key per 60 degrees squashes the half-fold edge by 13 percent. `--layer-gap` and `--crease-radius` must be above zero. A shape-key value is a straight blend, so keep each key to about 30 degrees of turn. For a curl instead of a crease, a Simple Deform (Bend) modifier with an animated angle is the cheaper tool.

## walk: forward, with the feet planted

A jointed mannequin (tapered rounded limbs, ball joints at knees, shoulders and elbows) walks at `--speed` m/s. The hips move at constant speed. A foot on the ground is held at one world position until it lifts (the plant); a foot in the air swings from one plant to the next with a lift. Each leg is solved with two-bone IK to reach its foot, every frame is keyed, and the result is plain keyframes with no rig or add-on. The stride is fitted to the speed: one foot comes round every `cycle_frames`, so the stride is `speed * cycle_frames / fps` and the plants of the two feet alternate half a stride apart.

Knobs: `--speed`, `--cycle-frames`, `--duty` (share of the cycle a foot is down, 0.6), `--step-height`, `--thigh`, `--shin`, `--hip-height`, `--bob`, `--arm-swing`, `--twist` (the chest turns against the hips), `--lead` (the camera aims this far ahead of the body, leaving room in the direction of travel), `--frames`. `--naive` makes the feet follow the body instead, which is the slide to avoid.

Posture: the hips are lowest while both feet are down and highest over one foot, as in a real walk, so the knees can stay nearly straight. For a natural stance keep `hip_height + bob` near 0.95 of the leg and check the reach: at speed 0.95, `--cycle-frames 34`, a 0.94 m leg, `--hip-height 0.9 --bob 0.024` is upright and `max_leg_stretch` stays zero.

Reads: `root_distance` (speed x time), `contact_frames`, `max_slide_per_frame` (a planted foot moves about 1e-7 m a frame; the naive version about 0.11), `min_foot_z`, `max_foot_lift`, `max_leg_stretch` (zero: the leg never had to be longer than it is), `max_ik_error` (the animated foot is where the solver put it), `step_length`.

Traps: if `hip_height` is too close to `thigh + shin`, the legs cannot reach the ends of the stride and the foot floats or drags at the extremes, where the slide check (which only looks at frames with the foot on the ground) cannot see it: `max_leg_stretch` goes above zero, and `ok` turns false with a warning. `ok` is also false when the feet never plant. `hip_height + bob` at or above `thigh + shin` is refused, and so is a `--duty` outside 0.5 to 1. Shorten the stride (lower speed or `cycle_frames`) or lower the hips. To walk in place on a treadmill, key the world instead of the figure.

## How the tests prove each one

Tests are in `tests/test_blender_*.py` and run the recipe at a few pixels and frames. They skip when Blender is absent (CI has none) and use only the standard library for the picture comparisons (BMP frames). Each is a measurement, not an "it ran" check: pixel difference for `loop` and `retime` (and for `--orbit`, a fading caption and `--look studio`), final heights for `cloth`, joint distance, a pendulum period and the frame margin for `rigid`, bounding box and layer heights for `fold`, per-frame foot motion for `walk`. Each has a control that must fail: a naive walk slides, a chain with its constraints deleted falls apart, a cloth over a floor with its collider removed falls through it, a straight one-key fold squashes the free edge to half its height (`tests/test_recipe_math.py`), a camera move the loop's curves know nothing about shows in `pose_gap`, and a fractional or crossing retime is refused. The recipes' plain arithmetic (`b2m_math.py`: the retime map, frame lists, colours, the leg solver, the fold) imports no Blender, so `tests/test_recipe_math.py` runs in CI on every system; the rest needs Blender and was run on Blender 5.2.1.
