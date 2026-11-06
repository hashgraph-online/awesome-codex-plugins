# From the approved animatic to Seedance video-to-video

The animatic fixes what video models are worst at: camera, geography, scale and timing. Seedance 2.5
(`seedance_2_5` on varg) takes the animatic clip as `@video1` and redraws it in the film's look with the
characters and places from image references. The full pack builder (a `pack.json`, a board, `requests.json`)
lives in the `varg-previz` skill; this page is the short version you can do by hand for a few runs.

## What video-to-video copies, and what it does not

Tested on real runs (480p, 4–11 s each):

| from `@video1` | result |
|---|---|
| hard-cut timing | kept exactly |
| camera moves (push in, arc, crane) | kept |
| blocking (who is where, who does what) | kept |
| shot size | looser than the previz: a CU came back as a medium shot. Frame one size tighter |
| poses | copied literally, including bad ones (tangled arms, a prop through a fist) |
| the grey-box look | **copied** when a character in frame had no image reference: the mannequin became a real "toy" person |
| the whole clip | once returned **unchanged** (the previz itself, re-encoded, billed). Fixed by sending the clip in greyscale |

So: every run gets a greyscale `@video1`, an image reference for every character, product and location in frame,
and a prompt that says what to take from the video and what not.

## 1 · Group shots into runs

A run is one generation: consecutive shots of ONE location, cut as in the film. Seedance 2.5 takes whole seconds
from 4 to 30. Short runs (4–11 s) are cheap to redo when one shot fails; one long run keeps a single location's
light and identity consistent. Do not split a continuous scene into many tiny generations when one run (up to 30 s) can
hold it: faces and light drift between generations.

For the starter: one run, `s01 s02 s03`, 10 s, one location.

## 2 · Render the reference clip

```bash
bun tools/capture.ts --shots s01,s02,s03 --grey --out renders/run_A.mp4
```

Greyscale (`hue=s=0`, a little contrast), 480p at the film's aspect, 24 fps, no text, the tail padded to whole
seconds. `run_A.json` records where each shot sits in the clip and on the timeline. Look at the clip, including
the tail, before uploading it.

## 3 · Image references: only what is in frame

- One character sheet per person (front, three-quarter, profile on a plain background), one model sheet per
  product or vehicle **with a person beside it for scale**, one master plate per location.
- Only for what is in this run's frame. A sheet that also shows the antagonist pulled the antagonist into shots
  that should not have it: crop it. An exterior still used for an interior scene put open sky inside.
- A shot that was rewritten has a stale still: do not feed it.
- References narrower than 300 px were rejected (a 266 px crop failed two runs): pad crops onto the sheet's
  background colour, e.g. to 432×768.
- `files` order sets the numbers: images become `@image1…@imageN` in order, the first video is `@video1`.
  Up to 9 images and 3 videos for `seedance_2_5`.

Need a plate or a key frame that matches the previz camera? Render the blockout still
(`bun tools/capture.ts --stills --size 1536x864`) and edit it with `gpt_image_2_5` or `nano_banana_2_1`, the
render as the FIRST file, the prompt "keep the camera and the geometry exactly; grey blocks = …" with every block
mapped. Approve these stills on a board before any video is paid for.

## 4 · The prompt (generic example for the starter run)

```
@video1 is a black-and-white grey-box 3D previz of this sequence. Copy from @video1 ONLY the camera (framing, lens,
camera position and movement), the hard-cut timing and the blocking (where everyone is and what they do). Do not
copy its look: no flat grey shapes, no 3D-render look, no greyscale. Redraw every frame as live-action footage;
the result must not look like @video1.
@image1 is the character sheet of the woman on the left: same face, short dark hair, cream knit sweater, brown
trousers.
@image2 is the character sheet of the man on the right: same face, short black hair, dark teal jacket, black
trousers.
@image3 is the master shot of the cafe: small round wooden table, two black chairs, a tall window behind them with
the street outside, a wooden counter with shelves of bottles on the right wall.
@image4 is the drone's model sheet: a small black quadcopter about half a metre across with one red light at the
front, much smaller than a person.
Only two people in this sequence; every hand belongs to one of them.
Soft daylight from the window for the whole sequence.
Look: natural film look, 35 mm, gentle grain, muted colours.

3 shots, hard cuts exactly as in @video1:
1. 0.0–4.0 s. Wide shot at eye level, slow push in: the woman talks and gestures with her right hand, the man
   listens and nods; at 3.0 s a small drone appears far away outside the window.
2. 4.0–6.0 s. Over her shoulder, medium close-up on the man: at 4.5 s he stops listening and looks up toward the
   window.
3. 6.0–10.0 s. Low angle from the table edge, both people on the sides of the frame: the drone flies in through the
   window, slows over the table and lands between the cups at 8.6 s; both lean back and at 7.0 s she lifts both
   hands; at 9.0 s he leans in to look at it.

Camera: one move per shot, as in @video1. Full-bleed 16:9 frame, no borders, no letterbox. No text, letters,
numbers, logos or UI anywhere in the frame. No dialogue.
```

Rules behind it:

- Times are **absolute seconds from the clip start**. "At 1.8 s" inside shot 2 is ambiguous.
- Keep the `Look:` line to style only (medium, lens, grain, palette). Light and weather go in a per-run line: a
  "sunset outside" in a shared look line put sunset windows into a studio run.
- One action per shot, written for the model, not for a person ("he looks up toward the window", not "he senses
  danger").
- Say the scale and the count ("only two people", "exactly two hands", "half a metre across").
- No text from the model, ever. Titles, captions and UI are drawn later in code.
- Do not describe noise, TV static, glitch walls or particle storms. A run built around a wall of static came back
  as mush and was regenerated with "clean frames, no static, no noise, no grain wall".

## 5 · The request (varg MCP `call_tool`)

Upload first (local files are not URLs): `upload_file_widget` or `create_upload` in MCP clients, or
`upload_file({ url })` for a file that already has a public URL. Then:

```json
{
  "tool": "video",
  "input": {
    "model": "seedance_2_5",
    "prompt": "<the prompt above>",
    "files": [
      { "url": "https://…/woman_sheet.png" },
      { "url": "https://…/man_sheet.png" },
      { "url": "https://…/cafe_master.png" },
      { "url": "https://…/drone_sheet.png" },
      { "url": "https://…/run_A_grey.mp4" }
    ],
    "aspect_ratio": "16:9",
    "resolution": "480p",
    "duration": 10,
    "audio": false
  },
  "wait": false
}
```

- Read the live schema first: `get_tool({ tool: "video", model: "seedance_2_5" })`. If it offers a mode for video
  references (reference vs edit), choose **reference**: the clip guides camera and blocking, it is not footage to
  restyle. Put that option exactly where the schema says.
- A reference-mode run with images only and no video was rejected: keep `@video1` in every v2v request.
- `audio: false` when music or voice is added in the edit.
- Price before you promise. `seedance_2_5` is about 210 credits per 5 s at 720p (1 credit = 1 cent; see the
  `varg-ai` skill's models list), less at 480p. Run `estimate_cost` on the real request, quote it as the
  ceiling (billed runs came in lower than the estimate), check `check_balance` and which team pays
  (`get_current_team`), and get a yes before generating. First run of a project: ONE short run, look at it, then
  the batch.
- `call_tool(..., wait: false)`, write the job id down at once (`jobs.json`), poll `get_job`. Do not resubmit a
  job that is still running: that is a second charge.

## 6 · QA every output before it goes on the timeline

1. **Pass-through check.** Extract the same moments from the output and from `@video1` and stack them:
   `ffmpeg -ss 2 -i out.mp4 -frames:v 1 a.png; ffmpeg -ss 2 -i run_A_grey.mp4 -frames:v 1 b.png;
   ffmpeg -i a.png -i b.png -filter_complex vstack check.png`. Grey, 3D-looking output = the previz came back:
   retake (greyscale clip, the "must not look like @video1" line, references for everything in frame).
2. **Count people and hands**, check every face against its sheet, look for objects fused into hands.
3. **Framing**: looser than the previz is expected; if a shot needs to be tight, retake with a tighter previz or
   crop in the edit.
4. **Fix small artefacts in the edit, not by regenerating**: cut the 0.2 s with the artefact, reuse a good take of
   the same shot, slow a clip slightly to fill. Regenerate only what the edit cannot fix.
5. Cut each shot back onto the film timeline with the placement file (`in`/`out` inside the clip, `timeline` start
   in the film). Watch frame rounding at the joins: a remainder of a few frames once showed one frame of the next
   world at a cut.
