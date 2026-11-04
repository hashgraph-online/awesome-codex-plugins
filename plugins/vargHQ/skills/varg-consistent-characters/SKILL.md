---
name: varg-consistent-characters
description: >-
  Makes multi-scene ad videos on varg in which the same people, outfits and location stay
  consistent in every shot, built from real actor photos or generated characters: one profile
  card per actor, an empty location card, scene composites approved as stills first, then
  image-to-video with native dialogue audio, trimmed and captioned in one cloud render. Also
  covers frame and audio QA of the output and turning a reference video into a scene script.
  Use when a script names actors (A1, A2), a location (L1) and numbered scenes, when someone
  sends actor or model photos, or asks for a consistent character, the same person in every
  scene, a recurring mascot or brand character, a UGC or skit ad with two actors, or to remake a
  reference ad with new people. Not for one speaker on a stage (use varg-character-keynote),
  seated two-person podcast dialogue (use varg-podcast-video), music videos (use
  varg-music-video), or one-off images and clips (use varg-ai).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    requires:
      anyBins:
        - curl
        - bun
    homepage: https://varg.ai
compatibility: >-
  Needs a VARG_API_KEY (see the varg-ai skill) or the varg MCP connection
  (https://mcp.varg.ai/mcp). The images-only approval script needs bun; the final render runs in
  the cloud with curl. QA uses ffmpeg/ffprobe locally.
allowed-tools: Bash(bun:*) Bash(bunx:*) Bash(curl:*) Bash(jq:*) Bash(ffmpeg:*) Bash(ffprobe:*) Bash(nohup:*) Read Write Edit
---

# varg consistent characters

Turn a scene script + actor photos into a multi-scene vertical ad where characters, outfits and location stay consistent across every cut. Tested on a 5-scene, 22-second 9:16 fitness ad with two real actors in one gym.

Generation runs on varg: the `varg-ai` skill (sign-in, models, local and cloud render) or the varg MCP server (`https://mcp.varg.ai/mcp`). This skill assumes a working `VARG_API_KEY` or MCP connection.

## Core idea: cards, then composites

Never describe characters from scratch in every scene prompt. Build a small set of **frozen reference images** once, then compose every scene from them.

```
photo A1 ──edit──> a1Card ─┐
photo A2 ──edit──> a2Card ─┼──edit──> scene1..N ──image-to-video──> vid1..N
prompt   ──gen───> gymLoc ─┘
```

Upload the actor photos first (`POST /v2/files`, or the MCP upload tools) and use the returned URLs.

No actor photos? Design the cast with `varg-character-design` (archetypes, a model sheet per character on flat grey) and use each character's full-body crop as the profile card below.

## 1. Consistency

### 1.1 Character profile cards

One image-edit call per actor, from their photo:

```tsx
const a1Card = Image({
  prompt: {
    text: "Full-body character reference card of the exact same woman from the photo: same face, same grey hair, same body shape. <age/build>. She wears <FIXED OUTFIT, described precisely>. Standing straight facing camera, neutral relaxed pose, arms at her sides. Plain light grey studio background, even soft lighting, head-to-toe framing, photorealistic",
    images: [A1_PHOTO_URL],
  },
  model: varg.imageModel("nano_banana_2_1"),   // edits when images are passed
  aspectRatio: "9:16",
});
```

Rules that make cards work:

- **"exact same ... from the photo: same face, same hair, same body shape"** anchors identity to the reference instead of the text description.
- **Fix the outfit in the card.** The card's clothes become the outfit for the whole video. Pick it so the script works (e.g. arms or legs visible if scenes point at them). Never re-describe clothes differently later.
- **Full body, neutral pose, plain studio background**: a clean card composites into any scene; a scene-styled card does not.

The pipeline was first built with Nano Banana Pro edit; `nano_banana_2_1` is its successor and varg's default. For the hardest identity cases try `gpt_image_2_5`.

### 1.2 Location card

One text-to-image generation, **no people**:

```tsx
const gymLoc = Image({
  prompt: "Empty modern gym interior with huge floor-to-ceiling windows... No people. ... photorealistic, 9:16 portrait framing",
  model: varg.imageModel("nano_banana_2_1"),
  aspectRatio: "9:16",
});
```

An empty location card lets every scene reuse the same walls, light and floor without characters from a previous scene leaking in.

### 1.3 Scene composites

Every scene is one edit call with **all three refs**:

```tsx
const SAME =
  "First reference image is Woman A (<short recap of card>). Second reference image is Woman B (<short recap>). Third reference image is the gym location with huge windows. Keep both women's faces, hair, bodies and outfits exactly as in their reference cards, and the gym exactly as in the location reference.";

const scene2 = Image({
  prompt: { text: `${SAME} <scene-specific framing, poses, gestures>`, images: [a1Card, a2Card, gymLoc] },
  model: varg.imageModel("nano_banana_2_1"),
  aspectRatio: "9:16",
});
```

- The `SAME` preamble is **shared verbatim** across all scenes. It names each reference by position ("First reference image is...") and pins identity.
- Image edit models take several refs fine. For **Video**, one image = the first frame; several images switch to reference mode, which only some models support (see `varg-ai`).
- Scene text only describes what changes: camera framing, poses, gestures, expressions.

### 1.4 Cache discipline (critical)

Identical prompt + params = free cache hit, both locally and **server-side on api.varg.ai**. This is what makes the whole pipeline cheap:

- Keep prompts **byte-identical** between the images-only script, the local template and the cloud template. Copy-paste, never retype.
- The full 5-scene video re-rendered in the cloud for a few credits (the stitching fee) because every image, video and music prompt matched the earlier runs.
- Editing one scene's prompt regenerates only that scene; everything else stays cached.

### 1.5 Content-moderation gotcha

Body-part wording such as "rear" or "booty" in an **image** prompt can silently stall generation for ~10 min (provider moderation). Rephrase to neutral anatomy: "hips and thighs". The same words inside spoken dialogue in **video** prompts passed fine.

Fitness and swimwear scenes trip filters on words, not pictures: "girl" instead of "woman, 28", "tight", "bikini" and short prompts without a garment description get blocked on GPT Image 2.5, FLUX 3 and Grok, while a catalog-style prompt (adult age as a number, each garment named, an activity, "activewear brand catalog photo") passed on all six image models we tried. A block can be random: retry once, then rephrase, then route. Test log, safe-phrasing table and routing: `varg-character-design` → `references/moderation.md`.

## 2. Photos-for-approval pass (images first)

Generate and show all stills **before** paying for any video. A still costs a few credits; a video clip costs ten times more or more. Approve the cheap layer first.

Standalone script pattern (`<project>-images.ts`, run with bun):

```ts
import { Image } from "vargai/react";
import { createVarg } from "vargai/ai";

const varg = createVarg({ apiKey: process.env.VARG_API_KEY! });
// ... define a1Card, a2Card, gymLoc, scene1..sceneN exactly as in 1.x ...

async function save(name: string, el: ReturnType<typeof Image>) {
  const resolved = await el;               // await triggers generation (cached)
  await Bun.write(`output/<project>/${name}.png`, await resolved.file.data());
}

// cards + location first, then scenes (scenes reference the cards)
await Promise.all([save("a1-card", a1Card), save("a2-card", a2Card), save("location", gymLoc)]);
await Promise.all([save("scene1", scene1), /* ... */]);
```

Key facts:

- `Image({...})` is a lazy thenable: `await` resolves it, `.file.data()` gives the bytes. Awaited results are cached, so the later video render reuses them for free.
- Run it in the background (`nohup bun run <project>-images.ts > images.log 2>&1 &`) and report the PID.
- Show the user: the cards + location + every scene. Iterate on individual scene prompts (only the changed one regenerates) until approved.

No bun? Generate the same stills one by one with `POST /v2/image` (or MCP `generate_image`), passing the references in `files`. Keep the prompts identical to the ones you will use in the render.

## 3. Final render: cloud (`POST /v2/render`)

After the stills are approved, wrap them in videos + composition and submit the whole TSX to the cloud. No bun or ffmpeg needed on the machine that submits.

### 3.1 Video layer: image-to-video with native audio

Dialogue is written into the video prompt and the model voices it:

```tsx
const vid2 = Video({
  prompt: {
    text: `Same gym with huge windows. <scene action, static camera>.
The trainer says matter-of-factly: "<the scene's line>"
Soft gym ambient sounds.`,
    images: [scene2],                      // exactly ONE image = the first frame
  },
  model: varg.videoModel("kling_v4"),
  audio: "native",                         // generates and keeps the dialogue audio
  duration: 4,                             // integer seconds (kling_v4: 3-30)
});
```

- Quote dialogue lines verbatim in the prompt; add a voice direction ("clear encouraging voice", "matter-of-factly").
- Budget ~1 s of dialogue per ~2.5 words, then trim (3.3).
- `kling_v3` is what this pipeline was first tested on and still works the same way (integer 3-15 s); `kling_v4` is the current Kling. `seedance_2_5` gives the best faces and lip movement at a higher price.
- Native audio needs `audio: "native"`. A flat `providerOptions: { varg: { generate_audio: true } }` is silently dropped and you get a silent clip.

### 3.2 Cloud TSX rules

`POST https://api.varg.ai/v2/render` with `{"code": "<tsx>"}` (MCP: `render_video` with `code`):

- **No imports, no `createVarg`**: `Render/Clip/Image/Video/Music/Captions` and `varg` are injected as globals. Local LSP errors on this file are expected and fine.
- Must `export default (<Render ...>...)`; no named exports.
- Same `varg.*Model()` ids as local.

Price it first (MCP `estimate_cost` with tool `render` and the code, or `POST /v2/estimate` on each clip's request) and get the user's go-ahead. Then submit and poll:

```bash
curl -s -X POST https://api.varg.ai/v2/render \
  -H "Authorization: Bearer $VARG_API_KEY" -H "Content-Type: application/json" \
  -d "{\"code\": $(jq -Rs . < template-cloud.tsx)}"
# -> {"id":"job_xxx",...}; poll every 15s:
curl -s https://api.varg.ai/v2/jobs/JOB_ID -H "Authorization: Bearer $VARG_API_KEY"
# completed -> output.outputs[0].url  (s3.varg.ai mp4)
```

If all prompts match a previous run, the cloud render costs a few credits (server cache) and finishes in ~2 min.

### 3.3 Dynamic pacing: trim dead air

Generated clips have ~0.2-0.5 s of warm-up and often trailing silence. Detect speech boundaries on the generated clips, then cut tight:

```bash
ffmpeg -i scene.mp4 -af "silencedetect=noise=-35dB:d=0.35" -f null -
```

```tsx
<Clip cutFrom={0.2} cutTo={5.6} duration={5.4}>{vid1}</Clip>  // cut right after the line ends
```

This took the test video from 27 s to 22.4 s with no content loss.
Keep `Music` `duration` an **integer**: a fractional total like 22.4 failed with a 422 on ElevenLabs music. Round down.

### 3.4 Centered captions in the cloud (inline SRT)

`<Captions>` transcribes `Speech` elements by itself. For dialogue that lives in a video's native audio, the tested route is two passes (newer vargai builds also accept `src={vid.audio}`; if the render rejects that with "Captions src must be ...", use this route):

1. Render once without captions (cloud or local).
2. Upload the audio and transcribe it on varg: `POST /v2/files` (upload) -> `POST /v2/transcription` with `{"model":"whisper_large_v3","audio_url":...}`. The result has word-level timestamps.
3. Build a word-level SRT; fix Whisper mishears (product names, unusual words). Captions' `prompt` prop can also pass context hints to Whisper.
4. Embed the SRT **inline** in the cloud TSX. The `srt` prop takes a file path, and template code runs on the render server, so write the file to `/tmp` at module eval:

```tsx
const SRT_CONTENT = `1
00:00:00,260 --> 00:00:00,320
You
...`;
const SRT_PATH = `/tmp/project-${Date.now()}.srt`;
await Bun.write(SRT_PATH, SRT_CONTENT);
// in <Render>:
<Captions srt={SRT_PATH} style="tiktok" position="center"
          color="#ffffff" activeColor="#a3e635" wordsPerLine={3} fontSize={64} />
```

Re-submitting is nearly free (everything cached); only the composition re-runs.
Important: if you change any clip trim, **regenerate the SRT**, because the timings shift.

## 4. QA: how to analyze what you generated

Agents can't watch video, but they can read frames and measure audio.

### 4.1 Visual QA: extract frames and READ them

After every render (and every images pass), pull frames and inspect them as images. Never ship a video you haven't frame-checked.

```bash
# one frame per scene, at a timestamp INSIDE that scene (mind the trims)
ffmpeg -v error -ss 3  -i out.mp4 -frames:v 1 -vf scale=270:-1 check-s1.png -y
ffmpeg -v error -ss 9  -i out.mp4 -frames:v 1 -vf scale=270:-1 check-s3.png -y
ffmpeg -v error -ss 14 -i out.mp4 -frames:v 1 -vf scale=270:-1 check-s4.png -y
```

- Downscale (`scale=270:-1` .. `360:-1`): enough to judge, cheap on context.
- Read several frames **in one parallel tool call**.
- No local ffmpeg? The varg MCP `analyze_video` tool answers questions about a rendered video.

Visual checklist per frame:

- **Identity**: same face/hair/body as the profile cards, in every scene.
- **Outfit drift**: clothes must match the cards exactly (color, cut, shoes). Drift usually means a scene prompt re-described clothing: fix the wording, not the card.
- **Location drift**: windows/floor/props consistent with the location card.
- **Framing**: matches the script (full-body vs close-up); subjects not cropped at the wrong place; both actors present when required.
- **Captions**: correct position (center), readable size, active-word color visible, no overlap with faces.
- **Age/build drift**: edit models can age or slim a person between scenes. Compare against the card and regenerate the outlier scene only.

Also verify structure numerically:

```bash
ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 out.mp4
```

Duration must equal the sum of clip durations; a mismatch means a clip or music duration bug, not an encoding issue.

### 4.2 Audio QA: silencedetect as ears

`silencedetect` shows where speech actually lives in each generated clip:

```bash
ffmpeg -i scene.mp4 -af "silencedetect=noise=-35dB:d=0.35" -f null - 2>&1 | grep silence_
```

Read it per clip:

- silence at the **start** -> dead air / late speech start -> raise `cutFrom`;
- silence at the **end** -> line finished early -> lower `cutTo`;
- **no silence** in an N-second clip -> speech fills it; if the line is long, the model may have rushed or truncated it: listen-check via transcription;
- silence in the **middle** of a one-line clip -> possible stutter or split delivery.

Then confirm the words: transcribe the final mix (3.4 step 2) and diff the transcript against the script. This catches mispronunciations by the video model and mishears by Whisper. Fix mishears in the SRT; regenerate the clip only if the model actually said the wrong thing.

### 4.3 When to regenerate vs when to trim

| Symptom | Fix |
|---|---|
| Dead air, late start, early finish | Trim with `cutFrom`/`cutTo`: free |
| Wrong/garbled spoken line | Regenerate that Video |
| Identity/outfit drift in one scene | Regenerate that scene Image, then its Video |
| Caption timing off after re-trim | Regenerate the SRT only (one transcription) |

## 5. No script? Analyze the reference video first

When the user sends a reference video instead of a script, reverse-engineer the same A/L/Scene structure this skill consumes. Do this **before** touching any generation. (`media-download` fetches a reference by link.)

### 5.1 Extract structure

```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1 ref.mp4

# scene cut candidates (hard cuts)
ffmpeg -i ref.mp4 -vf "select='gt(scene,0.35)',showinfo" -f null - 2>&1 | grep showinfo | grep pts_time

# speech map
ffmpeg -i ref.mp4 -af "silencedetect=noise=-35dB:d=0.35" -f null - 2>&1 | grep silence_
```

Scene-cut timestamps + speech gaps together give the beat structure: how many scenes, how long each, where dialogue sits.

### 5.2 Sample frames per scene

Extract 1-2 frames inside each detected scene and read them (parallel call):

```bash
ffmpeg -v error -ss <t> -i ref.mp4 -frames:v 1 -vf scale=360:-1 ref-s1.png -y
```

From the frames, document for each scene:

- **Actors**: who is on screen, rough age/build/hair -> becomes A1, A2...
- **Wardrobe**: what each actor wears (this defines the profile-card outfits).
- **Location**: environment, light, key props -> becomes L1 (L2...).
- **Framing**: full-body / medium-wide / close-up; front or back view; camera static or moving; who is closer to camera.
- **Action + gesture**: what each actor does (squats, points at X, thumbs-up).

### 5.3 Get the dialogue

Transcribe the reference audio (same varg call as 3.4). Map each line to its scene via the timestamps. If there's no speech, note the music mood and on-screen text instead.

### 5.4 Write the script, then confirm

Assemble the standard format and **show it to the user for approval** before generating anything:

```
Actors:
- A1: <description from frames>  - C1: <wardrobe>
- A2: <description>
Location:
- L1: <description>
Scene 1 (Ns): <framing>. <action>. A2 says: "<line>". L1
Scene 2 ...
```

From here the pipeline is identical: cards (1.1) -> location (1.2) -> composites (1.3) -> approval pass (2) -> videos + cloud render (3). Use the reference's measured scene durations as the initial `duration` values, and its framing notes verbatim in scene prompts.

## Cost reference (5 scenes, ~22 s at 9:16)

Rough credits from the varg catalog (October 2026). Always quote the user the exact figure from `POST /v2/estimate` / `estimate_cost`, in credits.

| Step | Credits (~) |
|---|---|
| 8 images (2 cards + location + 5 scenes), `nano_banana_2_1` | ~65 |
| 5 Kling clips with native audio, 4-6 s at 720p | ~400-500 |
| Music bed (`mureka_9_5`) + one transcription | ~30 |
| Cloud re-render with everything cached | a few (stitching fee) |
| Iterating one scene image / one scene video | ~8 / ~80-100 |

## Related skills

`varg-ai` (sign-in, models, render formats), `varg-character-keynote` (one speaker on a stage), `varg-podcast-video` (two seated characters in dialogue), `varg-previz` (plan many shots and camera moves first), `media-download` (fetch a reference video), `video-skills` (find a skill for another format).
