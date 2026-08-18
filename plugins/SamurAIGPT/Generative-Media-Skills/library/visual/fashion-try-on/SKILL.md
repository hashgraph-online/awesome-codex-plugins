---
slug: muapi-fashion-try-on
name: muapi-fashion-try-on
version: "1.0.0"
description: Virtually try on different outfits by combining a person's photo and a clothing item, then optionally generate a professional fashion model video.
acceptLicenseTerms: true
---


# Fashion Try-On

**Virtually try on different outfits by combining a person's photo and a clothing item, then optionally generate a professional fashion model video.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `person_image` | image_url | yes | — | A photo of the person or model who will try on the clothes. |
| `clothing_image` | image_url | yes | — | A photo of the clothing item to try on. |


## Steps

### Phase A — Virtual Try-On

If `{{person_image}}` or `{{clothing_image}}` is not provided, ask the user to upload them.

Once both images are available, submit the plan with ONE step to perform the try-on:

1. **Fashion Try-On** — `muapi image edit` (model=`qwen-image-edit-2511`):
   - Reference Images: Use both `{{person_image}}` and `{{clothing_image}}`.
   - Prompt: `A high-quality fashion photograph of the person from the first reference image wearing the exact clothing item from the second reference image. The fit should be natural and realistic, maintaining the person's pose and the clothing's texture and patterns. Soft studio lighting, neutral background, professional fashion photography style.`
   - Aspect ratio: 1:1 or 4:5

Present the resulting fashion photo to the user for approval.

### Phase B — Fashion Video Generation (Optional)

After the image is generated, ask the user if they would like to create a professional fashion video of the model wearing the outfit.

If requested, submit the plan with ONE step:

1. **Fashion Video Generation** — `muapi video from-image` (model=`seedance-v1.5-pro-i2v-fast`):
   - Reference Image: The try-on image generated in Phase A.
   - Prompt: `Shot type of Three-Quarter Length Shot. [Push in] as model gracefully places hand on hip, shifts weight to one side, tilts head slightly with soft smile, and gently adjusts hair with fingertips, creating elegant movement and confidence.`
   - Aspect ratio: 9:16 or 4:5

After generation, present the final fashion video.

## Trigger Keywords

`fashion try on`, `virtual fitting room`, `try on clothes`, `model fashion`, `clothing preview`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
