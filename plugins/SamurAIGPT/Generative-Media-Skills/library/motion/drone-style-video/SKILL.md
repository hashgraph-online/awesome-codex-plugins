---
slug: muapi-drone-style-video
name: muapi-drone-style-video
version: "1.0.0"
description: Generate aerial drone-perspective footage — sweeping bird's-eye views, orbit shots, and flyover sequences for landscapes, architecture, and events.
acceptLicenseTerms: true
---


# Drone-Style Video

**Generate aerial drone-perspective footage — sweeping bird's-eye views, orbit shots, and flyover sequences for landscapes, architecture, and events.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `location_or_subject` | text | yes | — | What to shoot from above (e.g. "mountain valley at sunrise", "luxury villa by the ocean", "crowded city intersection"). |
| `shot_type` | text | no | reveal | Camera movement style — 'reveal' (ascend & reveal), 'orbit' (circle subject), 'flyover' (pass over), 'top-down' (bird's eye static). |
| `style` | text | no | golden hour, cinematic, 4K, ultra-detailed | Visual atmosphere (e.g. "dramatic storm clouds", "misty morning", "blue hour city lights"). |
| `aspect_ratio` | text | no | 16:9 | Output aspect ratio. |
| `reference_image` | image_url | no | — | Optional aerial/location reference image. |


## Steps

### Phase A — Generate Drone Footage

Submit the plan with ONE step:

1. **Aerial video** — If `{{reference_image}}` is provided, use `muapi video generate` (model=`veo3.1-image-to-video`); otherwise use `muapi video generate` (model=`veo3.1-text-to-video`).
   - Build prompt based on `{{shot_type}}`:
     - **reveal**: `Drone camera starts low, slowly ascends and reveals {{location_or_subject}}, sweeping wide aerial perspective, {{style}}`
     - **orbit**: `Drone camera orbits {{location_or_subject}} in a smooth circular arc, 360-degree aerial rotation, {{style}}`
     - **flyover**: `Drone camera flies low and fast over {{location_or_subject}}, tracking forward momentum, depth of field, {{style}}`
     - **top-down**: `Perfect overhead bird's eye view of {{location_or_subject}}, drone looking straight down, minimal distortion, {{style}}`
   - Append to all prompts: `DJI-quality drone footage, stabilized gimbal, no shake, cinematic color grade, photorealistic`
   - Aspect ratio: `{{aspect_ratio}}`

After generation, offer:
- A different shot type variation
- Adding wind/ambient audio via `mmaudio-v2-video-to-video`
- Upscaling via `ai-video-upscaler-pro`

## Notes
- For architecture, emphasize "slow orbit to reveal full building facade".
- For landscapes, use "magic hour lighting" for the best results.
- `veo3.1-text-to-video` produces the best physics and camera motion for aerial scenes.

## Trigger Keywords

`drone`, `aerial`, `bird's eye`, `flyover`, `aerial shot`, `drone footage`, `top down`, `overhead video`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
