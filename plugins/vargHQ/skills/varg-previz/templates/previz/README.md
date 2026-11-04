# previz: a 3D grey-box animatic for AI video

A schematic 3D previz of every storyboard shot on the timeline. Use it to approve scenes, location geography and
cameras (position, angle, lens, move) before any paid generation, then export clean clips as video-to-video
references.

## Start

```bash
python3 <skill>/scripts/new_previz.py <project>      # copies this app to <project>/previz/
python3 <project>/previz/serve.py                     # http://localhost:8765/previz/
```

No build step and no npm: three.js r169 is in `vendor/`. The server serves the project folder (storyboard, track,
stills) and saves edits.

## On screen

- **Shot view** (project aspect): the shot camera at the current time; shot id, bar.beat (or seconds), the line, and
  an "ADD IN EDIT" chip for graphics drawn later in code.
- **Set map**: the same set from above with START (green) and END (orange) frustums of every shot in this location
  and the yellow live camera, so you can see close-ups share the wide's geography.
- **Panel**: shot text, current still, camera spec (size, angle, mm, move), START/END keys, approval + note, warnings.
- **Timeline**: scene bands, shots, bar grid; a dot shows approval (green ok, yellow fix).

## Edit a camera

1. Pick a shot, press `1` (START) or `2` (END): the frame border turns orange.
2. Frame in the view: drag = orbit, shift+drag = pan/tilt in place, right-drag = truck, wheel = dolly,
   alt+wheel = FOV, WASD/QE = fly. FOV and roll also have sliders.
3. "→ write START" / "→ write END". Pick the move curve in the panel.
4. `⌘S` saves to `data/edits.json` (copies in `data/history/`); edits override `js/shots.js` and auto cameras.
5. "Export plan" writes `camera_plan.md`: every shot's size, angle, lens, move, status and note.

Keys: `space` play, `←/→` shot, `L` loop shot, `F` frame, `O` still overlay, `G` guides, `C` animatic,
`H` all cameras, `M` map home.

## Files

| file | what | edit per project |
|---|---|---|
| `config.json` | title, storyboard and audio paths, aspect, bpm, scenes, scale, hud cards, export size | yes |
| `js/sets.js` | one builder per location (starters: studio, room, street) | yes |
| `js/shots.js` | per-shot animation, hand-made cameras, shake | only shots that need it |
| `js/props.js` | mannequin + poses, product, car, table, chair, effects | add props |
| `js/autocam.js` | storyboard camera words → camera keys | no |
| `js/main.js`, `js/rig.js`, `index.html`, `serve.py` | the app | no |
| `seedance/` | `pack.json` + tools for the video-to-video pack | `pack.json` |
| `sample/storyboard.json` | the 6-shot sample used when a project has no storyboard | no |
| `examples/space-opera/` | sets, shots, props and pack of a full 36-shot music video, for techniques | read only |

## Seedance pack (`seedance/`)

```bash
cd previz/seedance
python3 tools/build_pack.py --check
bun tools/capture.mjs /tmp/frames "$(python3 tools/build_pack.py --plan)"   # previz server must be running
python3 tools/build_pack.py /tmp/frames                                       # add --runs A to build one run
```
Output: `video/video_XX__<run>__<shots>.mp4` (@video1 per run), `refs/`, `requests.json` (ready `call_tool`
inputs, not run), `PROMPTS.md` (prompts + where each shot lands on the timeline), `index.html` (review board).
