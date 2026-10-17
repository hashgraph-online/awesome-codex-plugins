---
slug: muapi-talking-baby-video
name: muapi-talking-baby-video
version: "1.0.0"
description: Create a viral-style video of a talking baby with custom costumes and scripts.
acceptLicenseTerms: true
---


# Talking Baby Video

**Create a viral-style video of a talking baby with custom costumes and scripts.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `baby_costume` | text | no | a pilot uniform | The costume the baby is wearing (e.g., doctor, chef, pilot). |
| `dialogue` | text | no | Airbus A380 big plane! Go zoom! Have lots seats. People like fly in it. Best plane ever! | The script for the baby to say. |
| `baby_description` | text | no | A cute 6 months old male baby | Description of the baby. |


## Steps

### Phase A — Baby Character Generation

Submit the plan with ONE step to create the baby character:

1. **Baby Image Generation** — `muapi image generate` (model=`nano-banana` or `wan2.5-text-to-image`):
   - Prompt: `{{baby_description}} sitting and wearing {{baby_costume}}. High-quality photography, soft natural lighting, adorable expression, detailed fabric textures, shallow depth of field, Pixar-like charm but realistic.`
   - Aspect ratio: 9:16 or 1:1

Present the baby image to the user for approval.

### Phase B — Talking Animation

Once the image is approved, submit the plan to animate the baby talking:

1. **Talking Animation** — `muapi video from-image` (model=`grok-imagine-image-to-video`):
   - Reference Image: The baby image from Phase A.
   - Prompt: `A viral-style talking baby video. The baby is expressive, moving their mouth and head naturally while speaking the following lines: "{{dialogue}}". Subtle facial expressions like blinking and smiling. High-quality animation, smooth movements.`
   - Aspect ratio: 9:16 or 1:1

After generation, present the final talking baby video.

## Trigger Keywords

`talking baby`, `viral baby video`, `baby pilot`, `baby doctor`, `funny baby animation`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
