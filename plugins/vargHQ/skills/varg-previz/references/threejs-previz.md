# three.js previz

Goal: a small local app where the director scrubs the timeline, sees every shot as a schematic 3D frame, and approves
camera position, lens, movement and blocking. Not pretty, readable. Code: `templates/previz/`.

## Set up

```bash
python3 <skill>/scripts/new_previz.py <project> [--aspect 16:9] [--bpm 120] [--audio assets/track.mp3]
python3 <project>/previz/serve.py            # http://localhost:8765/previz/
```

No storyboard yet → the sample (6 shots, café / street / studio, 9:16) is written so the app opens at once.
With your storyboard, `js/shots.js` starts empty and every shot gets an auto camera from its `camera` words.
`--force` refreshes the app files and keeps `data/edits.json`.

## Storyboard schema (`storyboard.json`, project root)

```json
{ "title": "…", "duration": 12.0, "bpm": 120, "aspect": "9:16", "song": "assets/track.mp3",
  "shots": [ { "id": "s01", "start": 0.0, "end": 2.0,
    "scene": "A_cafe",            // location + light state: groups shots into runs
    "set": "room",                // which 3D set frames it (js/sets.js)
    "subject": "a",               // what the auto camera frames (a key of set.subjects)
    "camera": "CU, 3/4 right, slow push in",
    "picture": "what we see (for people)",
    "action": "what happens, written for the video model (goes into the Seedance prompt)",
    "line": "lyric or VO line", "beat": "hook", "overlay": "text/graphics added in the edit",
    "source": "gen | reuse | code", "film_ref": "…", "still": "url of the current still", "needs_new_still": false } ] }
```
`lyric`, `act`, `campbell`, `bars`, `kind` from older storyboards are shown too. Only `id, start, end` are required.

`previz/config.json`: `title, storyboard, audio, bpm, aspect, stills ("../stills/{id}.jpg"), scenes ({id: {label,
color}}, auto-coloured if missing), scale (reference heights for shot-size maths), hud ([{text, from, to, pos}]
cards shown only in the UI, e.g. the hook), safe ({top, bottom} fractions), export ({width, height}), planFile`.

## Auto cameras (`js/autocam.js`)

`camera` words → START/END keys. size `ECU CU MCU MS MLS FS WS EWS` (or "close-up", "medium", "wide",
"establishing"); angle `front, 3/4 left/right, profile left/right, back, ots, pov` + `low, high, top, dutch`;
move `static, push in, pull out, orbit left/right, crane up/down, truck left/right, pan, tilt, zoom in/out, whip`.
Left/right are the subject's. People are framed from the head; objects (product, car) by their own height, so
"CU product" fills the frame with the product. A subject that moves in the shot's `anim` is framed where it is at
START and at END, so the camera tracks it (say "static" / "locked" to stop that).

Auto cameras are a starting point, not an answer: look at every one. In the test project 2 of 6 needed fixing
(a camera inside a walking subject before tracking existed; a wide that lost both subjects in the narrow 9:16 frame).
Fix in the UI (keys below) or by a hand `cam` in `js/shots.js`.

## Layout

- **Shot view** (left, in the project's aspect): the shot camera now; HUD with shot id, bar.beat or seconds, the
  line, a dashed "ADD IN EDIT:" chip for graphics drawn later; toggles for thirds/safe zones and an onion-skin of the
  current still.
- **Map view** (centre): the same set from a free camera; START (green) / END (orange) frustums of every shot in this
  set (`CameraHelper` on ghost cameras, layer 1, so the shot camera never sees them), dashed path, id sprites, the
  live camera in yellow.
- **Panel** (right): storyboard text, still, auto camera spec (size, angle, lens, move), START/END values, ease,
  approve / needs-a-fix + note, warnings (unknown set, anim errors).
- **Timeline** (bottom): scene bands, shot blocks coloured by scene, bar grid (or seconds), status dots, scrub by drag.
- One `WebGLRenderer` on a full-window canvas behind the DOM renders each view with `setViewport/setScissor` from the
  placeholder element's rect.

## Files

| file | what | edit? |
|---|---|---|
| `js/sets.js` | one builder per location; starters: `studio` (product + presenter), `room` (two at a table), `street` (car + walker) | yes, per project |
| `js/shots.js` | per-shot `anim`, hand `cam`, `shake`, `ref` | yes, only shots that need it |
| `js/props.js` | primitives, mannequin + poses, product, car, table, chair, effects | add props |
| `js/autocam.js`, `js/main.js`, `js/rig.js`, `index.html`, `serve.py` | the app | no |
| `config.json` | paths, aspect, bpm, scenes, scale, hud | yes |

A set is `{ id, title, scene, o, subjects, helperFar, mapHome?, ref?, mapFollowShot?, reset() }`: `o` holds the
named objects the story touches (`S.o.product`), `subjects` what cameras can frame, `reset()` restores the neutral
state every frame. A shot's `anim(S, c)` then poses the set from time only (`c.k` 0..1, `c.lt` local s, `c.T`
timeline s, `c.beat` s per beat), so scrubbing and export are exact. Edits (`data/edits.json`, timestamped copies in
`data/history/`) override only changed cameras + status + note.

## Sets and objects (best practices)

- Units metres; forward = −Z, up = +Y, a character's right hand = +X (written at the top of `props.js`).
- Build from primitives with flat shading and an ink outline (`EdgesGeometry` lines): it reads like a storyboard.
  Skip ink on InstancedMesh (edges are not instanced).
- Mannequin poses are a dictionary of joint Eulers blended in layers: `pose(p, [['sit',1], ['phone',1-k],
  ['handsOnTable',k]])`. Signs: shoulder.x>0 raises the arm forward, knee.x<0 bends back, a right arm swings inward
  with negative z. Seated: pelvis at seat height + 0.05.
- Name every object the story touches and expose it on `set.o`, so shot animations stay one-liners.
- Colour code like the film (enemy, our side, brand colour). Text labels (signs, UI cards) are `labelPlane`s:
  flagged `userData.label` (hidden in export) and optionally `userData.billboard` (face the camera).
- Big repeated detail via `InstancedMesh`. Speed without moving the hero: scroll the environment modulo its repeat
  length. Blackouts/flashes: a sphere around the camera with `depthTest:false` and a high `renderOrder`.

## Camera editing

- `1`/`2` jump to START/END and enter framing mode (orange border): drag = orbit, shift-drag = pan/tilt in place,
  right-drag = truck, wheel = dolly, alt-wheel = FOV, WASD/QE fly. "→ write START/END" stores the pose; `⌘S` saves.
- Auto spec per shot: size from the frame height at the target vs the subject (people: 1.8 m with thresholds tuned
  so the narrow side of the frame still holds a face; objects: their own height), angle from pitch, lens =
  full-frame equivalent (36 mm along the long side of the frame), move from START→END.
- "Export plan" writes `camera_plan.md` (size, angle, lens, move, positions, status, note) for prompts and review.

## Verify in a headless browser (do this, do not guess)

- `bun add playwright-core` in the project; system Chrome with `--use-angle=swiftshader --enable-unsafe-swiftshader`.
- Open the app, `app.seek(t)` per shot, screenshot `#view-shot`, montage with PIL, look at every frame.
  `app.describe(shot)` returns the size/angle/lens/move text; `app.shots[i].warn` any problem.
- Bugs actually hit, check for them:
  - a body state class equal to a component class (`body.guides` + `.guides{display:none}`) hid the whole page →
    state classes are prefixed (`is-guides`), plus `[hidden]{display:none!important}`.
  - keyboard before the first rAF → no current shot; the shot is selected synchronously at init.
  - Python `http.server` has no Range support → audio cannot seek; the track is fetched into a blob URL.
  - "loop shot" must track the shot captured at play/seek time, not the last rendered one.
  - subjects outside the narrow frame, cameras inside walls/headrests/bulkheads or inside a walking subject, a map
    camera outside a tunnel set.
  - one broken `anim` used to stop the render loop: anims now run in try/catch and report in the panel.

## Clean export for references

`?export=1`: only the shot view at `config.export` (default 480 px on the short side), pixel ratio 1, no HUD or
guides, text labels hidden, rAF stopped; `app.exportFrame(id, localTime)` renders one frame (local time may pass the
shot end to render a tail handle). `seedance/tools/capture.mjs` screenshots every frame at 24 fps (finds Chrome on
macOS/Linux or `CHROME=`, server URL from `PREVIZ_URL`); `build_pack.py` encodes per shot and concatenates per run.
