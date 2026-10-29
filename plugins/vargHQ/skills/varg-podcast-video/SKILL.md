---
name: varg-podcast-video
description: >-
  Makes podcast-style and two-character dialogue videos on varg with AI characters who stay the
  same in every angle: an empty studio set, one wide master shot built from character
  references, close-ups and lighting cutaways derived from that master, then 5-second
  image-to-video scenes in which each character speaks their line with native audio, reviewed
  on an HTML storyboard and stitched into one MP4. Use when someone asks for a podcast video, an
  AI podcast, a video podcast with two hosts, an interview, debate or talk-show clip between two
  characters, a myth-vs-truth or "lie vs truth" explainer, or a short of talking characters
  trading punchy lines. Not for cutting an existing podcast recording into shorts (find a
  clipping skill with video-skills), one speaker on a stage (use varg-character-keynote),
  multi-location ads with real actors (use varg-consistent-characters), or songs (use
  varg-music-video).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    requires:
      anyBins:
        - curl
    homepage: https://varg.ai
compatibility: >-
  Needs a VARG_API_KEY with curl (see the varg-ai skill) or the varg MCP connection
  (https://mcp.varg.ai/mcp). Stitching locally needs ffmpeg; otherwise varg's ffmpeg tool does it.
allowed-tools: Bash(curl:*) Bash(jq:*) Bash(ffmpeg:*) Bash(ffprobe:*) Read Write Edit
---

# varg podcast video

Generate consistent-character podcast and dialogue videos with varg image generation + image-to-video with native audio.

Generation runs on varg: the `varg-ai` skill (REST at `https://api.varg.ai/v2`, sign-in and model details) or the varg MCP server (`https://mcp.varg.ai/mcp`: `generate_image`, `generate_video` or `call_tool`, then `get_job`). The REST calls below map one-to-one onto the MCP tools.

## When to use

- Two-character conversation videos (podcast, interview, debate)
- Educational content with a "lie vs truth" format
- Any multi-scene video where character consistency matters across angles
- Short-form content (5 s per scene, punchy dialogue lines)

## Prerequisites

- A `VARG_API_KEY` (the `varg-ai` skill finds or sets one up) or the varg MCP connection
- Credits on the varg balance (`GET /v2/billing/balance` or MCP `check_balance`)
- Reference images for each character (photos or AI-generated portraits), uploaded with `POST /v2/files` so you have URLs

## The workflow (8 steps)

Every generation returns a job. Poll `GET https://api.varg.ai/v2/jobs/{id}` until `status` is `completed`; the file is at `output.outputs[0].url`.

### Step 1: Write a short script

Each scene = **5 seconds**. One short punchy line per scene. No long monologues.

```
Scene 1.1 — Host: "So... is multitasking actually a superpower?"
Scene 1.2 — Trickster: "Absolutely. Five tabs, three calls, zero problems."
Scene 1.3 — Trickster: "Focus is overrated. Real pros do everything at once."
Scene 1.4 — Host (truth cutaway, to camera): "Truth: every switch costs focus. One thing at a time gets more done."
```

Format: `Scene X.Y — Character: "short line"`. Keep lines under 15 words.

### Step 2: Generate the studio set (empty)

Generate the background/set as a standalone image with **no characters**. It becomes the base reference for every later shot.

```bash
curl -s -X POST https://api.varg.ai/v2/image \
  -H "Authorization: Bearer $VARG_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nano_banana_2_1",
    "prompt": "A modern podcast studio interior, wide establishing shot. Dark walnut wood paneled walls, two brown leather armchairs facing each other at an angle, a small dark wood table between them with two black microphones on boom arms. Warm amber recessed lighting. Bookshelf background. No people. Empty studio set.",
    "aspect_ratio": "16:9"
  }'
```

### Step 3: Generate character clothing (if needed)

If a character needs clothing different from their reference photo, generate the outfit as a standalone image:

```bash
curl -s -X POST https://api.varg.ai/v2/image \
  -H "Authorization: Bearer $VARG_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nano_banana_2_1",
    "prompt": "A dark elegant Victorian-style outfit on a mannequin. Black and dark red velvet tailcoat, high collar, dark crimson vest. Gothic aristocratic aesthetic. No person, just the clothing. Studio product photography.",
    "aspect_ratio": "1:1"
  }'
```

### Step 4: Generate the wide shot (both characters)

Pass **all references together** in `files`: character 1 + character 2 + clothing + studio. With `files`, `nano_banana_2_1` edits from the references.

**CRITICAL**: Do NOT describe the characters' appearance in the prompt. Reference them by position ("left character from ref 1", "right character from ref 2 wearing outfit from ref 3"). Describing appearance conflicts with the ref image and produces a different person.

```bash
curl -s -X POST https://api.varg.ai/v2/image \
  -H "Authorization: Bearer $VARG_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nano_banana_2_1",
    "prompt": "Two characters sitting in leather armchairs facing each other in this podcast studio. Left character from ref 1. Right character from ref 2 wearing the outfit from ref 3. Small table with microphones between them. Warm lighting.",
    "files": [
      { "url": "HOST_REF_URL" },
      { "url": "TRICKSTER_REF_URL" },
      { "url": "TRICKSTER_CLOTHES_URL" },
      { "url": "STUDIO_URL" }
    ],
    "aspect_ratio": "16:9"
  }'
```

This wide shot becomes the **base reference** for all camera angles.

### Step 5: Generate camera angles from the wide shot

Pass the wide shot as the **first** reference. The prompt must say:

> "Exact same scene as the reference image — same room, same characters, same positions, same lighting, same set. ONLY change: [camera move]. Do NOT rearrange anything. Do NOT move characters. Do NOT change the set."

```bash
# Close-up on character A
curl -s -X POST https://api.varg.ai/v2/image \
  -H "Authorization: Bearer $VARG_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nano_banana_2_1",
    "prompt": "Exact same scene as the reference image — same room, same characters, same positions, same lighting, same everything. ONLY change: move camera closer to the left character. Same angle, just tighter framing. Do NOT rearrange anything. Do NOT move characters. Do NOT change the set.",
    "files": [
      { "url": "WIDE_SHOT_URL" },
      { "url": "CHARACTER_A_REF" }
    ],
    "aspect_ratio": "16:9"
  }'

# Close-up on character B
# Same, but "move camera closer to the right character" + pass character B's ref

# Truth cutaway (lighting change)
# "Exact same scene — ONLY changes: shift lighting from warm to cold blue, the left character turns their head to look directly at camera. Do NOT rearrange anything."
```

**What works:**
- Close-up on character A (camera moves closer)
- Close-up on character B (camera moves closer)
- Lighting shift (warm → cold blue)

**What does NOT work:**
- Over-the-shoulder shots (OTS): the model rearranges characters and breaks positions
- Describing new appearance details in the prompt: produces a different character

Show the stills to the user and get approval before any video. Stills cost a few credits each; video clips cost ten times more or more.

### Step 6: Image-to-video with native audio

**CRITICAL**: Put the dialogue line **directly in the video prompt** and ask for native audio. The model voices the line itself; no separate TTS.

```bash
curl -s -X POST https://api.varg.ai/v2/video \
  -H "Authorization: Bearer $VARG_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "kling_v4",
    "prompt": "The man in the grey sweater leans forward toward the microphone and says: \"So... is multitasking actually a superpower?\" He gestures with open hands, eyes widen with curiosity, natural talking motion.",
    "files": [{ "url": "CLOSEUP_HOST_URL" }],
    "duration": 5,
    "aspect_ratio": "16:9",
    "audio": true
  }'
```

**Prompt structure for video:**
```
[Character description] [action/gesture] and says: "[exact dialogue line]" [more action]
```

- `"audio": true` is varg's unified native-audio switch. Without it, or on a model without native audio, the clip is silent. A flat `"provider_options": {"varg": {"generate_audio": true}}` is dropped by the API.
- One image in `files` = the first frame. Each close-up from step 5 is the start of its scene.
- Model choice: `kling_v4` (default here, native audio, integer 3–30 s); `seedance_2_5` for hero close-ups (best faces and lip movement, higher price); `heygen_video_1` for cheap drafts (sound is built in, 5–15 s). `minimax_h3_max` has no native audio on varg's current routes, so it comes back silent.
- Price one clip with `POST /v2/estimate` (same body) or MCP `estimate_cost` before the batch, quote it in credits, and wait for the user's go.

**Add action to every scene**; without action the video is a static talking head:
- Leans forward/back, gestures, picks up an object, waves a hand, crosses arms
- Snaps fingers, points, draws in the air, taps the table
- Eye roll, head tilt, eyebrow raise, a smirk forming

**Voice drift.** Native audio picks the voice per clip, so a character can sound different from scene to scene. If that happens, generate each character's lines with `eleven_v4` and one fixed voice (`POST /v2/speech`), then lip-sync each close-up with `sync_v3` (a silent clip + the line) or `minimax_h3_max_lipsync` (the still + the line).

### Step 7: Build an HTML storyboard

Create an HTML file with all videos embedded. Include:
- A "Play all" button that plays the scenes in sequence
- Each scene: video (320×180) + character tag + dialogue line + duration
- Color coding: warm scenes (red border), truth cutaways (blue border)

```html
<video src="VIDEO_URL" controls playsinline></video>
```

```javascript
// Play all in sequence
function playAll() {
  let i = 0;
  function next() {
    if (i >= videos.length) return;
    videos.forEach(v => v.pause());
    const v = videos[i];
    v.currentTime = 0;
    v.muted = false;
    v.play();
    v.scrollIntoView({ behavior: 'smooth', block: 'center' });
    v.onended = () => { i++; next(); };
  }
  next();
}
```

### Step 8: Stitch the approved scenes into one MP4

Locally, with the clips downloaded in order:

```bash
printf "file '%s'\n" scene_1_1.mp4 scene_1_2.mp4 scene_1_3.mp4 > list.txt
ffmpeg -f concat -safe 0 -i list.txt -c:v libx264 -c:a aac -r 30 episode.mp4
```

Or on varg, with the `ffmpeg` tool (`POST /v2/ffmpeg`, MCP `call_tool` with tool `ffmpeg`):

```json
{ "model": "ffmpeg",
  "command": "-i {{in_1}} -i {{in_2}} -i {{in_3}} -filter_complex \"[0:v][0:a][1:v][1:a][2:v][2:a]concat=n=3:v=1:a=1[v][a]\" -map \"[v]\" -map \"[a]\" -c:v libx264 -c:a aac {{out_1}}",
  "input_files": { "in_1": "SCENE_1_1_URL", "in_2": "SCENE_1_2_URL", "in_3": "SCENE_1_3_URL" },
  "output_files": { "out_1": "episode.mp4" } }
```

Captions, if wanted: transcribe the episode (`POST /v2/transcription`, word timestamps included) and burn them in, or rebuild the episode as a cloud render with `<Captions>` (see `varg-ai`).

## Key rules (learned the hard way)

1. **Never describe appearance in edit prompts.** Pass ref images and say "character from ref 1". Describing appearance = a different person.
2. **The wide shot is the base for all angles.** Pass it as the first ref and say "exact same scene, ONLY change the camera".
3. **No OTS shots.** The model rearranges characters. Use close-ups instead.
4. **Dialogue goes in the video prompt**, and the video model voices it.
5. **`"audio": true`** on a model with native audio; otherwise the video is silent.
6. **5 seconds per scene**: short lines, one idea per scene. Long monologues don't fit.
7. **Add physical action**: gestures, objects, movement. Static talking heads are boring.
8. **Generate clothes separately** if a character's ref photo has the wrong outfit, and pass them as an extra ref.
9. **Truth cutaway = lighting change only**: same positions, just warm → blue + the character looks at camera.
10. **Keep prompts byte-identical when re-running**: identical requests are free cache hits.

## Cost estimate

Rough credits from the varg catalog (October 2026); quote the exact figure from `POST /v2/estimate` / `estimate_cost`.

| Item | Credits (~) |
|------|---------|
| Studio set image | 8 |
| Clothing ref image | 8 |
| Wide shot image | 8 |
| 3 close-up / cutaway images | 24 |
| 9 video scenes, 5 s each at 720p (`kling_v4`) | ~750+ |
| **Total per question (9 scenes)** | **~800** |

Video is almost all of the cost. `heygen_video_1` drafts cost a fraction of that; `seedance_2_5` costs more than twice as much.

## File structure

```
podcast/
  script.md                 # Full script (all questions)
  storyboard.html           # HTML review page with embedded videos
  ref_host.png              # Character reference
  ref_trickster.png         # Character reference
  studio_set.png            # Studio background
  trickster_clothes.png     # Clothing reference
  wide.png                  # Wide shot (base for angles)
  cu_host.png               # Close-up, host
  cu_trickster.png          # Close-up, trickster
  truth.png                 # Truth cutaway (blue light)
  scenes/                   # Generated clips, one per scene
  episode.mp4               # Stitched result
```

## Related skills

`varg-ai` (sign-in, models, REST and cloud render), `varg-consistent-characters` (the same people across several locations, with captions and QA), `varg-character-keynote` (one speaker on a stage), `video-skills` (find a skill for another format, e.g. clipping a real podcast).
