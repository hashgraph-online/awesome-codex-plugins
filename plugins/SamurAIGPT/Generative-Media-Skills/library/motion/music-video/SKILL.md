---
slug: muapi-music-video
name: muapi-music-video
version: "1.0.0"
description: Build a short music video from a song theme — N keyframes, animate each, generate matching music.
acceptLicenseTerms: true
---


# Music Video

**Build a short music video from a song theme — N keyframes, animate each, generate matching music.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `theme` | text | yes | — | Song / video theme (e.g. "lonely robot finds a friend, hopeful"). |
| `scenes` | int | no | 3 | Number of scenes (each becomes a 5s clip). |
| `music_style` | text | no | ambient cinematic, instrumental, slow tempo, warm | Suno-style tags for the soundtrack. |
| `visual_style` | text | no | cinematic, photoreal, soft volumetric light, 16:9 |  |


## Steps

Build one the plan covering:

1. **Layer A (parallel)** — N keyframes + 1 music track all at once.
   - For each scene 1..N: `muapi image generate` with a beat-specific prompt +
     `{{visual_style}}`, model=nano-banana-pro (these feed video gen).
   - One `muapi audio create` (kind=music) using `{{music_style}}`, duration =
     N × 5 + a 2s tail.
2. **Layer B (parallel, depends on Layer A)** — animate each keyframe.
   - For each scene: `muapi video from-image` with `image=$nX.url`, model=veo3.1-image-to-video,
     duration=5, prompt=scene-specific motion direction.
3. Return:
   - The scene keyframes (asset ids in order).
   - The animation clips (asset ids in order).
   - The music track asset id.
   - A short summary describing the cut order.

## Notes
- Keep character continuity by repeating the character description in every
  scene prompt verbatim.
- Don't auto-confirm any single video call > 50 cr — those need the user's
  nod (the loop will prompt automatically).
- If a scene's `muapi video from-image` fails after failover, fall back to
  `muapi video generate` (text-to-video) for that scene only.

## Trigger Keywords

`music video`, `mv`, `video story`, `song visualization`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
