# Case A: copy a reference video

**Decide what you're taking first.** If you own the clip and want the same camera with a different world, the shortest route is the
clip itself as `@video1` in a model such as Seedance, with image references for the new look. The cleanest public A/B (@aratamadao): a
reference traces cuts and timing but drags quality to its own level; stills plus a prompt gave better camera and acting but lost sync, so he
fixed sync afterwards in code.

Build a prototype only for something specific: an exact head count, contact points, continuous camera speed across clips, sync to
music, or changing the camera, set or blocking. Or when the clip belongs to someone else and you only want its grammar.

## 1 · Split it and look

```bash
python3 scripts/shots.py reference.mp4 --out breakdown/
```

`shots.json` and contact sheets, one row per shot. The three cells are 2 frames inside each cut, at first, middle and last, 426 px wide. Measure
cuts in code: Claude only gets frames, and Gemini samples video at 1 fps by default. Write down each shot's size, angle, what moves and what it
does for the story. Cut exact frames at full size when you compare later: `ffmpeg -ss <t> -i reference.mp4 -frames:v 1 first.png`.

## 2 · Read the move

```bash
uv run scripts/measure_shot.py reference.mp4 --start 74.1 --end 79.3
```

It tracks the background, ignores what moves against it, and reports pan, tilt, zoom and roll at the frame's centre. This reads the **picture**, not the camera.
Example from a real shot: `pan +2.4%, tilt +7.1%, zoom 1.65`. A solve of the same shot found a 1.6 m dolly, panning left 8.8° and tilting down 5.8°: the dolly hides the pan.
On any shot with parallax, where near things slide faster than far things, **use it to describe and compare, not to set camera keys**. The zoom is the zoom of whatever has corners:
moving stand-ins, with the camera untouched, moved it from 1.76 to 1.64 in one test. Locked-off shots, nodal pans and real zooms read true. "trust" only counts tracked points.

## 3 · Solve the camera, if the camera really moves

```bash
ffmpeg -ss 74.083 -to 79.375 -i reference.mp4 -an -crf 12 -pix_fmt yuv420p shot.mp4        # one shot, no cuts
uv run --python 3.13 --with bpy==5.2.3 python scripts/solve_camera.py shot.mp4 --out solved.json
python3 scripts/solved_to_staging.py solved.json --horizon-v .31 --height 1.75 --travel-m 1.6 --out path.json
```

This is cheap and it works: on a dark, compressed 5 s film shot, Blender's tracker solved 127 of 127 frames on CPU in about 2 minutes, with 0.7 px error. A fresh agent using the same
method got a 25 mm lens (flat from 24 to 28) and matched the solved path with a camera within 7 mm and 0.27°, 1.76 px median against the film's own tracks.

- **Read the lens table.** The lowest error shows the lens and a flat stretch means a range. The free solve is a second opinion.
- **You supply gravity and scale,** because a solve has neither. `--horizon-v` is where the horizon sits in the first frame. For scale, use `--travel-m`, or `--scale` from two tracked points of known distance (`points` in `path.json`). Angles don't depend on scale. For a firm vertical, vote with vertical lines across the shot.
- **Paste `path.json`'s `shot` into `staging.json`.** It carries several keys and roll.
- **It fails** on a locked-off shot or a nodal pan (no parallax, use the 2D read: Blender's tracker has a Tripod mode for pure pans), when a moving subject fills the frame (try NVIDIA ViPE, untested by us), and on flat renders. A previz with bare grey surfaces solved to 13.3 mm against a known 25 mm, so test a solve on a render with real surface detail: that gave 24.86 mm.
- Nobody we found on X documents a solved camera reaching Seedance with a measured match. We haven't run that handoff either.

## 4 · Read the frame and stage it

```bash
python3 scripts/grid.py first.png --out first_grid.png        # add --crop .4,.5,.7,.8 --step .05 for detail
```

Read subjects, horizon and big masses as fractions of the frame, on first, middle and last frames.

- **Level camera:** `scripts/place.py` gives depth and height from a known size, as in `references/paintings.md`.
- **Tilted or moving camera:** `place.py` assumes level, and on a shot looking down 10° it put the camera 0.9 m too low. Use `points` from `path.json`: the tracked features in the staging world tell you where the film has things. Shoot rays from the solved camera for the rest.

Put detail only at depths where the reference has detail. Add pins with a time (`[world, [u, v], t]`) on first, middle and last frames: a pin on frame 1 says little about a moving shot.

## 5 · Compare with numbers and eyes

```bash
python3 scripts/check_staging.py staging.json
bun scripts/stage_three.ts staging.json still s01:0 mine_first.png
python3 scripts/compare.py first.png mine_first.png --out cmp_first
bun scripts/stage_three.ts staging.json film all mine.mp4 --flat
python3 scripts/compare.py reference.mp4 mine.mp4 --out cmp --video --start 74.083 --end 79.375
uv run scripts/measure_shot.py mine.mp4
```

Blender instead: `uv run --python 3.13 --with bpy==5.2.3 python scripts/stage_blender.py staging.json film all workbench frames/ --blend scene.blend`.

Dark reference? Look at edge overlays or brighten it. Compare the two `measure_shot` outputs as a sanity check only. With a solve, the real comparison is your camera against the solved path.
Check any reviewer's claims against the overlays: in our test the fresh reviewer was right about two things and wrong about three. Then make the changes you came for.

## Body motion

`Motion2MixamoRig` (on GVHMR), SAM 3D Body, Move.ai, DeepMotion. One person, head to toe, the whole time. "Foot sliding is still something I'm working on" (its author). **GVHMR, SMPL and
SMPL-X are non-commercial even under MIT or Apache repo badges.** A depth pass of the clip as `@video1` keeps the camera and frees the performance (two reports), and loses faces.
Vista4D reprojects footage into a point cloud to change the camera (one report, heavy, non-commercial weights).

## Taste and rights

Brian De Palma on Hitchcock: "But I'll take the grammar wherever I can get it." Roger Ebert on the shot-for-shot *Psycho*: pointless.
The rule that follows is **study by copying, publish by transforming**: take one shot's move, height and rhythm into your own
scene, never a sequence's staging plus its look. A grey-box built from a film is still derived from it.

This isn't legal advice, and no case squarely covers a camera move. In the US, *Rentmeester v. Nike* treats pose, lighting and camera
angle as free in isolation while protecting their combination. *Mannion v. Coors* can reach a recreated scene. *Dr. Seuss v. ComicMix* cuts
against "new skin on a meticulous copy", which is close to a video-to-video reskin. The UK and EU are stricter (*Temple Island*, *Painer*). Providers put the risk on you: fal,
BytePlus and Dreamina make you warrant rights in what you upload. Keep the credit on open films: CC-BY needs it.

Reference libraries: ShotDeck and Shot Cafe ban scrapers and automated tools, so a person picks the frames.
