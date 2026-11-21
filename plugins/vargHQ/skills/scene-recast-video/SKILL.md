---
name: scene-recast-video
description: >-
  Remake a known scene with a new cast: give a video model a short reference clip (a film scene,
  a dance, a fight, a news shot, a meme) plus photos of your own characters and a "replace, keep,
  never" prompt, and get your version with the motion, timing, camera and cuts of the original.
  Covers trimming the clip, character references, the recast prompt, new dialogue, the
  first-frame lock, the motion-only plate (greyscale or depth), three varg routes (Seedance 2.5
  with a video reference, MiniMax H3 Max Recast, Wan 3), a frame-by-frame check against the
  source and a stacked original-vs-remake export. Use when someone wants a parody of a movie
  scene, "this scene but with X", a character swap, a motion-control remake, a live-action
  version of a game or anime scene, a meme recast, or asks how the Higgsfield Genjutsu / Seedance
  video-reference remakes on X are made. For the joke, format choice and the rules for real
  people use ai-parody-video; for a talking monologue use multi-angle-monologue.
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    requires:
      anyBins:
        - curl
    homepage: https://varg.ai/how-to
compatibility: >-
  Needs a VARG_API_KEY with curl (see the varg-ai skill) or the varg MCP connection
  (https://mcp.varg.ai/mcp). ffmpeg and ffprobe to trim, compare and stack.
allowed-tools: Bash(curl:*) Bash(jq:*) Bash(ffmpeg:*) Bash(ffprobe:*) Read Write Edit
---

# Scene recast: a reference clip, your cast, the same motion

A video model with a video reference copies what is hard to write in a prompt (blocking, timing, camera, cuts) and takes who and what is on screen from your images. Creators call it motion control or a remake. The method below is read from the public posts of [@Arminn_Ai](https://x.com/Arminn_Ai) (X, September to November 2026), who describes it as: "You give it a reference clip plus your own character references and a prompt, and it generates your version while keeping the motion, timing and framing of the original" and "just the source video + refs + prompt. A 30 s render takes about 5 min. Easier shots can land in one try, harder ones usually need a few prompt passes." His tool is Higgsfield Genjutsu, which he says runs on Seedance 2.5; the same inputs work on varg.

Generation runs on varg: REST `https://api.varg.ai/v2` (the `varg-ai` skill) or the MCP server `https://mcp.varg.ai/mcp`. Price every run first (`POST /v2/estimate` or `estimate_cost`).

## 1. Ask, then go

- **The clip:** a link or a file, and which 5 to 30 seconds. No clip yet: `find-movie-clips` (clip databases, download, the scene split into uncut takes). A link: `media-download`.
- **The new cast:** one to four characters, each as a photo or a sheet (`varg-character-design`, `character-passport`). Who replaces whom, by position: "the man on the left in the black coat".
- **What else changes:** props, the room, the era, the dialogue. Everything not named stays.
- **Where it goes:** aspect ratio, and whether to post it stacked over the original (section 7).
- **Whose face and whose footage:** read "Before you start" in `ai-parody-video`. A real person in the cast needs their consent or a clear, labelled parody of a public figure; a provider block is a no, not a puzzle.

## 2. Prepare the clip

```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 scene.mp4
# cuts: every shot must be 15 s or shorter for Recast, and a run holds about 3 to 6 cuts well
ffmpeg -i scene.mp4 -vf "select='gt(scene,0.3)',showinfo" -an -f null - 2>&1 | grep -o 'pts_time:[0-9.]*'
# trim on a cut, 24 fps, 720p, no audio (new dialogue comes from the model or from the edit)
ffmpeg -ss 12.0 -to 27.0 -i scene.mp4 -an -r 24 -vf "scale=-2:720" -c:v libx264 -crf 18 plate.mp4
```

- Keep one place per run. A change of location is a new run, joined in the edit.
- Remove burned-in subtitles and logos by cropping (`crop=iw:ih*0.86:0:0`); text in the plate comes back as garbled text.
- More than 30 seconds: split on cuts into runs of 10 to 30 s and carry the same references into each.

## 3. References: one image per thing that changes

- A character needs a face that fills at least a third of the image, the outfit visible, even light. Two angles beat one. Images narrower than 300 px are rejected on the byteplus route.
- Match the pose family of the plate. A seated plate with a full-body standing reference drifts less than the other way round, but a reference in a wildly different costume fights the plate.
- If the outfit should come from the plate ("same black leather coat, new face"), say so in the prompt and crop the reference to head and shoulders.
- A prop or vehicle: three-quarter front and rear views on a plain background.

## 4. The recast prompt: replace, keep, never

Short when the clip carries the direction. The structure Armin posts for his remakes, with the slots opened up:

```
Replace <who or what in @video1, by position and clothing> with the exact <person/object> from
@image1. Copy it exactly as shown: <face, hair, glasses, build, outfit / make, model, colour,
details>. Do not change, redesign or swap it for anyone else.
Replace <second target> with the exact <person> from @image2: <details>.
Keep the original environment, <named set pieces>, lighting, camera movement, framing, timing
and scene progression from @video1. Everyone else stays as they are.
<Dialogue, in order: who says it, the line in quotes, the tone.>
<One line for the new event, if any: "At the end, the man at the fountain turns and is <...>">
Photorealistic, cinematic, natural motion. No extra cuts, no camera jumps, no distortion, no
warped faces, no changing outfit, no different person, no subtitles, captions, watermarks or
text, no extra objects, no AI artifacts.
```

- Name targets by where they stand and what they wear. A position is what the model can see in the plate; a name tells it nothing about which figure you mean.
- Changes at set times: "Preserve the source motion, camera and timing throughout. Apply the following changes by timecode: 0.0–3.0 s Environment: <...>. Main character: <...>." Object swaps "matching position, angle and movement frame for frame". State when a look ends: "The anime look ends completely at 17.0 s and does not carry over."
- Dialogue changes the mouths. If the original speaks and you want other words, write the new lines; if you want silence under music, say "nobody speaks".
- One new event per run (the turn, the reveal). Two and the model drops the plate's timing.

## 5. Three routes on varg

| Route | Send | Use it when |
|---|---|---|
| MiniMax H3 Max Recast, `minimax_h3_max_recast` | `files`: the video (5 to 30 s, no shot over 15 s), then up to four photos; optional `prompt` ("the man becomes the wizard from the photo"); `provider_options.fal.enhance_realism: true` | Start here. Only the people change: room, props, camera and every move stay. Output at 768p or 1080p. |
| Seedance 2.5 with a video reference, `seedance_2_5` | `files`: the plate, then the images (`@video1`, `@image1…`), up to 3 videos and 9 images, 4 to 30 s, `provider_options.piapi.input.omni_reference_task_type: "reference"` | When more than the people should change (set, style, an added event), or you want native audio. The scene is redrawn from the plate, so small set details shift. |
| Wan 3, `fal:alibaba/wan-3.0/reference-to-video` | reference videos (up to 5), images (up to 10), audio (up to 5), 2 to 30 s, 1080p | A second opinion, or when you also bring a voice clip. Not tested here. |

```bash
# Recast: the plate and one character sheet
curl -s -X POST https://api.varg.ai/v2/tools/video/call -H "Authorization: Bearer $VARG_API_KEY" \
  -H "Content-Type: application/json" -d '{
  "model": "minimax_h3_max_recast",
  "prompt": "the man becomes the old wizard from the reference photo",
  "files": [{"url":"PLATE_MP4"},{"url":"CHARACTER_SHEET"}],
  "resolution": "720p"}'

# Seedance 2.5: the plate as a motion reference
curl -s -X POST https://api.varg.ai/v2/tools/video/call -H "Authorization: Bearer $VARG_API_KEY" \
  -H "Content-Type: application/json" -d '{
  "model": "seedance_2_5",
  "prompt": "Reference @video1 for the motion, camera movement and framing. <Character> from @image1 performs exactly the same <action> as the man in @video1, same timing, in the same <room>. One continuous handheld take, no cuts.",
  "files": [{"url":"PLATE_MP4"},{"url":"CHARACTER_SHEET"}],
  "aspect_ratio": "9:16", "resolution": "480p", "duration": 10, "audio": false,
  "provider_options": {"piapi": {"input": {"omni_reference_task_type": "reference"}}}}'
```

### What a real run showed (varg, 2026-11-12)

One plate (a 10 s stock clip of a man dancing in a kitchen, one take, 720x1280), one character sheet (an invented wizard: face close-up plus three full-body views on grey), one run on each route, no retries:

| | Recast | Seedance 2.5, reference task |
|---|---|---|
| Result | Same moves second by second, same kitchen down to the posters, face and costume from the sheet | Same moves second by second, face and costume from the sheet, kitchen redrawn close to the plate |
| Output | 768x1344, 10 s, no audio (the plate had none) | 480x854, 10 s |
| Cost | $3.00 | $2.48 at 480p |

What failed on the way, so you do not pay to learn it:

- **Seedance edit task** (`omni_reference_task_type: "edit"`) rejects the job unless `aspect_ratio` is `"adaptive"` and `duration` is `-1`. The varg body does not accept a top-level `duration` below 1, so leave it out and put both inside `provider_options.piapi.input`.
- **The pinned standard route** (`piapi:seedance-2.5`) answered "Content moderation violation" three times: for the stock clip in edit and in reference mode, and for a clip of an AI-made character. It refuses a photoreal person in the reference video, licensed or generated. The `seedance_2_5` alias routes the same request to a tier that accepts it.
- **A 480p plate** (832x480) came back "Invalid input"; the same clip at 1280x720 was accepted. Keep plates at 720p or more.
- `estimate_cost` gives the ceiling: Recast showed $9.00 and charged $3.00.

Draft on Seedance at 480p, check (section 6), then rerun the keeper at 720p or 1080p with the same inputs. Model facts and limits: `varg-previz/references/seedance-v2v.md`. Armin's own comparison of the two engines he uses: the Seedance tool "is more accurate on motion control and timing", the MiniMax one "drops the timing on some frames" and "wins on cost"; Seedance "goes up to 30 seconds in one clip". On the single-take test above the two were level on timing.

## 6. Check against the source, then fix

```bash
# same second from both, side by side, one row per 2 s
ffmpeg -i plate.mp4 -i take.mp4 -filter_complex \
 "[0:v]fps=1/2,scale=480:-2[a];[1:v]fps=1/2,scale=480:-2[b];[a][b]hstack,tile=1x8" -frames:v 1 check.jpg
```

| What you see | Fix |
|---|---|
| The new character looks like the original actor | The reference is too small or too far from the plate's angle. Add a second angle; describe face, hair and glasses in the prompt; crop the reference tighter. |
| The plate's costume or colours leak in | Use a motion-only plate: greyscale (`ffmpeg -i plate.mp4 -vf hue=s=0 plate_grey.mp4`) or a depth pass, and say "@video1 is a motion plate. Use it for pose, timing, lips, hands, camera and framing. Do not copy its colour or its look. All colour comes from @image1." |
| Detail degrades as the clip moves away from frame 1 | First-frame lock: edit frame 1 of the plate on an image model into your version (new cast in place, same composition), send it as `@image1` with the plate, and write "@image1 is the first frame". Armin: with one locked frame "unwanted details start popping up" later in the clip; several locked frames act "as a proper motion control between them", at some risk to colour consistency. |
| Cuts land late or a shot is missing | Fewer cuts per run (split the plate), and write "N shots, hard cuts exactly as in @video1". |
| The job is refused | Read the reason. Known footage or a known face: the provider has said no to this input. Change the idea (an original scene shot in the style, your own lookalike character, a different clip), do not hunt for a setting that slips it through. |
| A hand, a prop or the crowd breaks in one stretch | Rerun, or keep the take and cut around those seconds. |

A depth or greyscale plate carries movement and drops the source's look. Creators on X also use it to get known scenes past a provider's copyright check; that is bypassing moderation, which providers' terms forbid, and it is not what this skill uses the plate for.

## 7. Finish

- **Stacked comparison** (original on top, remake below), the format that carries "I tested this scene" posts:

```bash
ffmpeg -i plate.mp4 -i take.mp4 -filter_complex \
 "[0:v]scale=1440:-2[a];[1:v]scale=1440:-2[b];[a][b]vstack" -c:v libx264 -crf 17 -an stacked.mp4
```

- **Sound:** keep the model's dialogue if it is clean; otherwise voice and lip sync per shot (`multi-angle-monologue`, `video-sound`). Music and effects last.
- **Subtitles:** two lines at most, lower third, white with a soft shadow (`caption-styles`). They carry the joke with the sound off.
- **Sharper output:** `topaz_video` on the final cut, once.
- **Label and post:** mark it as AI-made on the platform, and say it is a parody in the caption. Details in `ai-parody-video`.

## Cost of a 30-second recast (estimate before you spend)

| Step | Runs | About |
|---|---|---|
| MiniMax H3 Max Recast, 3 plates of 10 s, 2 passes each | 6 | $18 (measured: $3.00 for 10 s at 768p) |
| Or 480p drafts on Seedance 2.5, 3 plates of 10 s, 2 passes each | 6 | $15 (measured: $2.48 for 10 s at 480p) |
| Seedance keepers at 720p or 1080p | 3 | check `estimate_cost` |
| Upscale | 1 | from $0.50 |

## Related skills

`ai-parody-video` (the joke, the format, the rules), `multi-angle-monologue`, `media-download`, `varg-character-design`, `character-passport`, `varg-previz` (your own blockout as the plate), `video-animate`, `caption-styles`, `video-sound`, `media-judge`, `varg-ai`.
