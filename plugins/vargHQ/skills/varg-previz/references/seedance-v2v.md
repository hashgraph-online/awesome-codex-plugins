# Seedance 2.5 video-to-video pack (varg)

## Model facts (re-check https://varg.ai/models/seedance_2_5.md; never take prices from it)

- `seedance_2_5`; video-to-video runs on `byteplus:dreamina-seedance-2-5-260628` (cheapest, used here),
  `byteplus:…-260628-less-restriction` and `fal:bytedance/seedance-2.5/reference-to-video`. Pin the route as `model`.
- Inputs: `files: [{url}]`, up to 9 images, 3 videos, 3 audios; refer to them as `@image1…`, `@video1` (1-based per
  media type, the order inside `files` matters per type). 480p/720p/1080p, 4–30 s, `aspect_ratio` 16:9, 9:16, 1:1,
  4:3, 3:4, 21:9; `audio: false` for clips that get music/VO in the edit.
- `provider_options.byteplus.omni_reference_task_type: "reference"` (use the clip as a reference, not an edit).
- byteplus rejects reference images narrower than 300 px (a 266 px crop failed two runs): pad crops onto the sheet's
  background, e.g. to 432×768. `build_pack.py --check` flags it.
- Price seen (480p v2v, byteplus): `estimate_cost` quoted 361 credits for 9 s and 315 for 4 s, but runs billed
  ≈16 credits/s (4 s = 65, 6 s = 97, 8 s = 129, 9 s = 145, 11 s = 177). Quote the estimate as the ceiling, report
  the billed cost after (`get_job` → `cost_credits`), and put the rate in `pack.json` `credits_per_second`.

## What v2v copies and what it does not (tested 2026-10-26, 4 s, 480p, no image refs)

| from @video1 | result |
|---|---|
| hard-cut timing | kept exactly (cut at 2.0 s) |
| camera move (arc, push in) | kept |
| blocking / action (presenter lifts the bottle beside her face) | kept |
| framing / shot size | looser than the previz: a CU of the product came out as a medium shot |
| the grey-box look | **copied**: with no image refs the mannequin became a real "toy" person, despite "do not copy its look" |

So: **every run needs an image ref for every character and product in frame** (`build_pack.py --check` errors on a
run without refs unless `"allow_no_refs": true`, e.g. an empty landscape). Frame a size tighter in the previz than
you want if framing matters. Keep the pack `look` line to style only: location light goes into each run's `notes`
(a "sunset outside" in a shared look line put sunset windows into a studio).

## Build the pack (`previz/seedance/`)

`pack.json` holds everything project-specific:

```json
{ "title": "…", "model": "byteplus:dreamina-seedance-2-5-260628", "resolution": "480p", "credits_per_second": 16,
  "look": "style only: medium, palette, lens",
  "refs": { "hero_sheet": { "file": "hero_sheet.jpg", "copy_from": "stills/hero_sheet.jpg", "url": null,
                            "role": "the hero's character sheet: same face, …" } },
  "runs": [ { "key": "A", "title": "Café · the drop", "shots": ["s01", "s02"], "refs": ["hero_sheet", "M_cafe"],
              "notes": ["constraints and light for this run"] } ],
  "reuse": { "s09": "existing clip" }, "lipsync": ["s06"], "actions": { "s01": "optional override of storyboard action" } }
```

1. `python3 tools/build_pack.py --check` (unknown shots/refs, missing files, refs < 300 px, runs without refs,
   missing action text, runs over 15 s, shots in no run).
2. `bun tools/capture.mjs <frames> "$(python3 tools/build_pack.py --plan)"` with the previz server running: clean
   24 fps frames, tails included.
3. `python3 tools/build_pack.py <frames>` → `shots/*.mp4`, `video/video_XX__*.mp4` (length = the run's `duration`),
   `requests.json`, `PROMPTS.md`, `index.html` board (video + refs + placement + prompt per run).
4. Review the board with the director; fix refs per run. Add `--runs A,C` to any step to work on some runs only.

## Prompt template (written by build_pack.py)

```
@video1 is a grey-box 3D previz of this sequence. Copy from @video1 ONLY the camera (framing, lens, camera position
and movement), the hard-cut timing and the blocking (where everyone is and what they do). Do not copy its look: no
flat grey shapes, no 3D render style, none of its colours.
@image1 is <role + the facts it locks>.  … one line per ref …
<run notes: constraints (one person in the car / no creature here / we are inside) and the light of this run>
Look: <locked style line>.

N shots, hard cuts exactly as in @video1:
1. 0.0–1.8 s. <shot size + angle>: <one action, timed in absolute seconds from the clip start>
…
Camera: one move per shot, as in @video1. Full-bleed <aspect> frame, no borders, no letterbox. No text, letters,
numbers, logos or UI anywhere in the frame (all graphics are added later). No dialogue, no lip-sync.
```
Times are always absolute from the clip start ("halfway through this shot" if relative): "at 1.8 s" inside shot 2 of
a run is ambiguous.

## Run it

1. `check_balance` and `get_current_team` (the connection may bill a team; switching is the user's call).
2. Per file: `create_upload` (with `sha256:` hash for dedup) → `curl -X PUT -H "Content-Type: application/octet-stream"
   --data-binary @file "https://api.varg.ai<proxy_url>"` (auto-registers). Paste URLs into `pack.json` refs (`url`)
   and `requests.json`.
3. `estimate_cost` on one request, quote the total as a ceiling, get an explicit go. First time on a project: run ONE
   short run, look at it, then the batch.
4. `call_tool(video, input, wait:false)` per run; write `jobs.json` (run → job id) immediately.
5. Poll `get_job`; download outputs to `out/XX_<run>.mp4`; compare frames against the previz clip at the same times
   (a 2-row montage) before accepting. Then lip-sync (`sync_v2_pro`) the sung/spoken shots from voice slices, and cut
   clips onto the timeline with the placement table.

## Pass-through check (do it on every output)

One 4 s run came back as the previz itself, re-encoded (grey 3D render, frame-identical) and billed less (65 credits).
Compare a few frames of every output with its @video1 before using it. Retake fix that worked: send the reference as
**greyscale** (`ffmpeg -vf hue=s=0`) and say "@video1 is a black-and-white previz … redraw every frame as full-colour
hand-drawn anime; the result must not look like @video1".
