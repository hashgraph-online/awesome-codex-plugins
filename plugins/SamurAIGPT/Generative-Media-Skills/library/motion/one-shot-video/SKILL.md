---
slug: muapi-one-shot-video
name: muapi-one-shot-video
version: "1.0.0"
description: Generate a single continuous cinematic shot video — no cuts, one seamless flowing scene with dramatic lighting and motion.
acceptLicenseTerms: true
---


# One-Shot Video

**Generate a single continuous cinematic shot video — no cuts, one seamless flowing scene with dramatic lighting and motion.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `scene` | text | yes | — | The scene to render (e.g. "a chef plating food in a moody Michelin-star kitchen"). |
| `style` | text | no | cinematic, anamorphic lens, shallow depth of field, dramatic lighting | Visual tone and style (e.g. "noir, handheld, golden hour"). |
| `duration` | text | no | 10s | Target duration (e.g. "5s", "10s"). |
| `aspect_ratio` | text | no | 16:9 | Output aspect ratio — "16:9", "9:16", or "1:1". |
| `reference_image` | image_url | no | — | Optional reference image for subject/scene anchoring. |


## Steps

### Phase A — Generate the One-Shot Video

Submit the plan with ONE step:

1. **One-shot video** — If `{{reference_image}}` is provided, use `muapi video generate` (model=`veo3.1-image-to-video`); otherwise use `muapi video generate` (model=`veo3.1-text-to-video`).
   - Prompt: `{{scene}}, one continuous uncut shot, no transitions, camera slowly moves through scene, {{style}}, ultra cinematic, film grain, 4K quality`
   - Aspect ratio: `{{aspect_ratio}}`
   - Duration: `{{duration}}`

After generation, present the video and suggest:
- A second angle variation
- Adding ambient sound with `mmaudio-v2-video-to-video`

## Notes
- Emphasize "no cuts, no transitions" in the prompt for true one-shot feel.
- For portrait/vertical style (9:16), add "vertical format, smartphone framing" to the prompt.
- If the scene involves a person, suggest `kling-v3.0-pro-image-to-video` as an alternative for better human motion.

## Trigger Keywords

`one shot video`, `single take`, `continuous video`, `one take`, `cinematic shot`, `seamless video`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
