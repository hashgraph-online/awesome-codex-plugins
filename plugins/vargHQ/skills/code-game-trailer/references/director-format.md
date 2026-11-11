# Director JSON: every field

One file describes the whole trailer. `capture.ts`, `score.ts`, `cut.ts` and `check.ts` all read it.
Paths are relative to the director file. The tested example: `examples/lantern-canyon/director.json`.

## Top level

| field | default | meaning |
|---|---|---|
| `url` | required (unless every shot has `card`) | the game page: a local path (served over http for the run) or an `http(s)://` URL |
| `fps` | 30 | frames per second of the capture and the master (60 doubles the capture time) |
| `width`, `height` | 1920, 1080 | viewport and frame size (the page sees exactly this `innerWidth`/`innerHeight`) |
| `seed` | 1 | seed for the page's `Math.random` (shots can override) |
| `bpm` | none | tempo; shots may then give `beats` instead of `duration` |
| `music` | none | `{ "file": "music.mp3", "offset": 0.42, "bpm": 100 }`: default track for `cut.ts`, start offset in seconds |
| `ready` | `true` | JS expression that is true when the game can be recorded, e.g. `window.__game && window.__game.ready` |
| `probe` | none | JS expression read at mid-shot and at the end of each shot (score, lives, level) and printed; skipped on cards |
| `hooks` | `{renderer: "window.__game.renderer", camera: "window.__game.camera"}` | where the trailer camera finds the renderer and the game camera |
| `out` | `capture/` | capture folder (also `--out`) |
| `format` | `jpeg` | `jpeg` (q92, ~0.19 MB per 1080p frame: 104 MB for the example's 558 frames) or `png` (lossless, slower) |

## A shot

| field | meaning |
|---|---|
| `id` | folder name and label; unique |
| `role` | `establishing`, `mechanic`, `escalation`, `hero`, `title`, `end`: drives `score.ts` and relaxes `check.ts` freeze rules on `title`/`end` |
| `duration` or `beats` | length in seconds, or in beats at `bpm` |
| `url` | another page for this shot (default: top-level `url`) |
| `card` | a card page instead of the game, e.g. `../../cards/card.html?kicker=…&title=…&sub=…&foot=…&accent=ff5315` |
| `seed` | per-shot `Math.random` seed |
| `setup` | JS run after the page is ready: put the game in a known state (`__game.setup({...})`) |
| `warmup` | seconds stepped (at speed 1) after `setup`, not recorded: lets particles, trails and cameras settle |
| `speed` | game time per video time: `0.5` = slow motion, `2` = fast-forward. Inputs and camera keys stay in video seconds |
| `inputs` | list, see below; times in shot video seconds |
| `camera` | trailer camera, see below; omit to record the game's own camera |
| `hide` | CSS selectors to hide for this shot, e.g. `["#hud"]` |
| `overlay` | `{ "html": "...", "css": "..." }` injected in a full-screen layer above the game (titles, supers). Its CSS animations run on the virtual clock. Prefix your classes: the game's CSS applies too |
| `letterbox` | e.g. `2.39`: black bars for a scope frame |
| `fade_in`, `fade_out` | seconds from/to black, applied in `cut.ts` |
| `flash_in` | seconds from white (an impact cut) |
| `probe` | per-shot probe expression |

Every shot starts from a fresh page load, so shots are independent and can be re-recorded alone
(`--only`). To show a later moment, put the state there with `setup` (a level, a distance, a score):
the shot list does not need a continuous play-through.

## Inputs

```json
{ "at": 0.35, "key": "ArrowRight", "hold": 0.4 }      keyDown at 0.35 s, keyUp 0.4 s later (min 1 frame)
{ "at": 1.0, "key": "Space" }                          a 1-frame press
{ "at": 1.2, "mouse": [0.5, 0.4] }                      move to 50% / 40% of the frame (values > 1 are pixels)
{ "at": 1.3, "mouse": [960, 540], "click": true }      move and click
{ "at": 2.0, "eval": "__game.boost(true)" }            any JS, e.g. a game API call
```

Keys: `ArrowLeft/Right/Up/Down`, `Space`, `Enter`, `Escape`, `Shift`, `Control`, `Alt`, `Tab`,
`Backspace`, `a`-`z`, `0`-`9`. Events are real CDP input (trusted, `key`, `code` and `keyCode` set),
dispatched before the frame they belong to. Held keys are released at the end of the shot.
Pointer lock does not work headless: give the game a fallback (mouse position or keys) for look controls.

## Trailer camera

```json
"camera": {
  "space": "__game.anchor",          // "world" (default) or a JS expression returning an Object3D; keys are in its frame
  "lookAt": "__game.player",         // optional Object3D to aim at (overrides the keys' "look")
  "lookOffset": [0, 1.5, 0],         // world-space offset added to the lookAt target
  "ease": "inOutSine",               // linear, inOutSine, inOutCubic, outCubic, inCubic, outQuart, outExpo
  "handheld": 0.6,                   // deterministic drift (sines of the shot clock); 0.3-1 reads as handheld
  "keys": [                          // 1 key = locked off; 2 = a move; 3+ = a Catmull-Rom path
    { "t": 0,   "pos": [4.5, -2.6, -9], "look": [0, 0.4, 0], "fov": 42, "roll": 0 },
    { "t": 1.8, "pos": [-3.0, -2.2, -7.5], "look": [0, 0.4, 0], "fov": 40 }
  ]
}
```

- `t` defaults to 0 for the first key and the shot length for the last.
- Spaces in three.js convention: +x right, +y up, **−z forward**. In `__game.anchor` (the player with the
  level heading, no roll) `[0, 3, 10]` is 10 m behind and 3 m above; `[3.5, -2.5, -9]` is ahead, right and
  below, looking back at the player.
- A world-fixed camera at a place in the level (`__game.place(s)` in the example returns an Object3D at
  canyon distance s) plus `lookAt: "__game.player"` gives a fly-by: the player rushes past a camera that pans.
- The override applies only when `renderer.render(scene, camera)` is called with the game camera, which
  covers `EffectComposer` (its RenderPass passes that camera; bloom quads use their own). Position,
  rotation and FOV are restored after each render call.
- `roll` in degrees; `fov` is the vertical FOV (35 mm-equivalent: 24 mm ≈ 45.7°, 35 mm ≈ 32.3°, 50 mm ≈ 22.9° at 16:9).

## Camera recipes that worked in the example

| shot | space | keys |
|---|---|---|
| crane reveal (player rises into frame) | `__game.place(0)`, `lookAt` player, `lookOffset [0,6,-70]` | `[-4,36,24]` → `[0,15,-6]`, fov 42 → 40, inOutSine |
| low skim with handheld | `__game.anchor`, handheld 0.6 | `[4.5,-2.6,-9]` → `[-3,-2.2,-7.5]`, look `[0,0.4,0]`, linear |
| fly-by past a pillar | `__game.place(838)`, `lookAt` player | locked at `[6,2,0]`, fov 30 → 28 |
| hero through the gate, slow motion | `__game.place(1240)`, `lookAt` player, `speed: 0.5` | `[5,0.5,-16]` → `[3,1.5,-19]`, fov 52 → 58 |
| title behind the gate | `__game.place(1960)` | `[0,9,46]` → `[0,8,38]`, look `[0,12,-60]`, overlay in the lower third |

## What capture.ts writes

`capture/<id>/00000.jpg …` and `capture/manifest.json`:

```json
{ "fps": 30, "width": 1920, "height": 1080, "seconds": 33.5, "s_per_frame": 0.06,
  "shots": [ { "id": "s2_mechanic", "frames": 90, "duration": 3, "speed": 1, "ms_per_frame": 50.4,
      "events": [ { "frame": 41, "type": "spark" } ], "text": "SPARKS 0041 ×1 CHAIN 4 …",
      "probe_mid": 41, "probe_end": 49 } ] }
```

`cut.ts` adds `master.cuts.json` (`{ cuts: [{ id, role, start, end, frames, first_frame }] }`) and
`check.ts` writes `master.check.json` and `master.sheet.jpg`.
