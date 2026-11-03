# three.js animatic starter

A working, generic animatic: two mannequins at a cafe table, a drone flies in through the window and lands.
3 shots, 10 s, 16:9, 120 BPM. Copy the folder, then replace the set, the shots and the blocking with your film.

No npm and no build step: three.js r181 comes from jsDelivr through an import map (pinned in `index.html`).
Needs [Bun](https://bun.sh) for the server and tools, Google Chrome (or Chromium) for headless checks and
renders, and `ffmpeg` for MP4 encoding.

```bash
bun serve.ts                         # http://localhost:8777/   (review UI, saves edits)
bun tools/check.ts                   # headless: UI screenshot, frames per shot, contact sheet, seek-safety test
bun tools/capture.ts                 # whole film -> renders/animatic.mp4 (24 fps, 854x480)
bun tools/capture.ts --shots s01,s02,s03 --grey --out renders/run_A.mp4   # one Seedance v2v reference + run_A.json
bun tools/capture.ts --stills --size 1536x864                              # START/middle/END png per shot
bun tools/make_hf.ts && npx hyperframes render hf -o renders/animatic_hf.mp4   # same film through HyperFrames
```

Without Bun, `python3 -m http.server 8777` serves the review UI read-only (save and export then download files).

## The review UI

- **Shot view** (left): the shot camera at the current time, with thirds and a 90% safe frame (`G`), shot id,
  bar.beat, and the auto description: size · angle · lens · move.
- **Set map** (centre): the set from the top, in metres. Every shot's START (green) and END (orange) frustum,
  the dashed camera path, shot ids, and the live camera (yellow). `H` toggles the other shots, `M` resets the view.
- **Panel** (right): picture and action text, the camera spec, START/END values, ease (`inOut`, `linear`, `in`,
  `out`, `whip`, `hold`), path (`line`, or `arc` to orbit at constant distance), automatic warnings, approval
  and a note.
- **Timeline** (bottom): beats and bars, shot blocks with approval dots, drag to scrub.

Edit a camera: `1` / `2` jumps to START / END and enters framing (orange border). Drag to orbit around the
target, shift-drag to pan/tilt in place, right-drag to truck, wheel to dolly, alt-wheel or the slider for the
FOV, WASD/QE to fly. Then **→ write START / END**. `⌘S` saves to `data/edits.json` (a copy goes to
`data/history/`); **export plan** writes `camera_plan.md` and `camera_plan.json`.

Keys: `space` play · `←` `→` previous/next shot · `L` loop the shot · `K` click on every beat (when there is no
audio) · `F` frame the current moment · `Esc` leave framing.

## Files

| file | what | edit per project |
|---|---|---|
| `js/config.js` | title, fps, bpm, aspect, export size, duration, audio path | yes |
| `js/shots.js` | `SHOTS` (timing, picture, action, START/END camera, subjects to check) and `BLOCKING(S, T)` | yes |
| `js/sets.js` | the master set: geometry, light, named objects in `S.o`, `reset()` | yes, one builder per location |
| `js/props.js` | primitives, ink outlines, seeded random, jointed mannequin + poses, table, chair, drone, labels | add props |
| `js/camera.js` | camera keys, eases, arc moves, lens mm ↔ FOV, size/angle/move words, the framing rig | rarely |
| `js/film.js` | the seek-safe core: `film.pose(t)` and the export hooks `__seek` / `__frame` / `__film` | no |
| `js/main.js` | the review UI | no |
| `serve.ts` | static server + `POST /api/save`, `POST /api/export` (localhost only) | no |
| `tools/cdp.ts` | tiny Chrome DevTools Protocol client (headless Chrome, software WebGL) | no |
| `tools/check.ts`, `tools/capture.ts`, `tools/make_hf.ts` | checks, MP4/stills renders, HyperFrames variant | no |

## Rules the code follows (keep them when you extend it)

- What is on screen is a pure function of time: `film.pose(t)` resets the set and runs `BLOCKING(S, T)`.
  No `Math.random` (use `rng(seed)`), no clocks, no state carried between frames. `tools/check.ts` proves it by
  rendering the same moments out of order and comparing pixels.
- Block the action once in world time; shots are cameras on it. A per-shot cheat goes in `shot.cheat(S, c)`.
- A speed that changes is integrated in closed form (see the rotor spin-down in `shots.js`).
- Text labels (`labelSprite`) are review-only and hidden in every export.
- Shot cameras render layer 0; frustums, paths and ids live on layer 1, which only the map camera sees.
