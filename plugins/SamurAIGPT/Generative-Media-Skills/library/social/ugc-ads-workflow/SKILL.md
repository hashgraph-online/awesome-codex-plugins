---
slug: muapi-ugc-ads-workflow
name: muapi-ugc-ads-workflow
version: "1.0.0"
description: Create a User-Generated Content (UGC) video ad by combining a human selfie and a product image, then generating a video script and an animated ad.
acceptLicenseTerms: true
---


# UGC Ads Workflow

**Create a User-Generated Content (UGC) video ad by combining a human selfie and a product image, then generating a video script and an animated ad.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `product_name` | text | yes | — | The name of the product being advertised (e.g. "Blume SuperBalm in plum"). |
| `human_image` | image_url | no | — | A selfie or photo of the human influencer. |
| `product_image` | image_url | no | — | A clear photo of the product. |


## Steps

### Phase A — Image Combination

If `{{human_image}}` or `{{product_image}}` is not provided, ask the user to upload them or offer to generate them.

Once both images are available, submit the plan with ONE step to combine them:

1. **Image Generation** — `muapi image edit` (model=`gpt-image-2-text-to-image`):
   - Reference Images: Use both `{{human_image}}` and `{{product_image}}`.
   - Prompt: `A natural, candid UGC-style photo of the influencer from the first reference image holding and showcasing the product from the second reference image. The influencer is smiling genuinely at the camera, holding the product up. Natural indoor lighting, lifestyle aesthetic, high quality.`
   - Aspect ratio: 9:16 (vertical for TikTok/Reels/Shorts).

Present the combined image to the user for approval.

### Phase B — Script & Video Generation

1. **Research & Scripting**: Use your web search tools to find details about `{{product_name}}` to understand its key benefits.
2. Based on the research, craft a UGC-style video script with timestamps, similar to this format:

   *(0-2s) Influencer is holding the {{product_name}}, smiling genuinely to the camera.*
   "Okay, so you know how I'm always looking for that perfect everyday product?"
   *(2-7s) Influencer shows the product closer to the camera...*
   "Well, I found it! This {{product_name}} is seriously so good."
   *(7-12s) Influencer uses/applies the product.*
   "It feels amazing and actually works."
   *(12-15s) Influencer smiles, slightly pouts, and casually shrugs or nods in approval.*
   "It’s totally become my go-to. You have to try it!"

3. **Video Generation**: Submit the plan using an image-to-video model (e.g. `sd-2-omni-reference` or `veo3.1-image-to-video`).
   - Reference Image: The combined image from Phase A.
   - Prompt: Use the visual actions from the script you generated. For example: `A UGC-style video. The influencer holds the {{product_name}}, smiling genuinely. She brings it closer to the camera to show the label, then applies it smoothly. She nods in approval and smiles. Natural movements, talking to the camera, lifestyle vlog style.`
   - Aspect ratio: 9:16

After generating the video, present it along with the written script so the user can record their own voiceover or use a lipsync tool later.

## Trigger Keywords

`ugc ad`, `ugc video`, `influencer ad`, `product ad video`, `combine product and human`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
