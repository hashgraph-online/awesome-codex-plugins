---
slug: muapi-couple-grid-creator
name: muapi-couple-grid-creator
version: "1.0.0"
description: Create a stylized 6-box grid featuring a couple in various romantic poses and outfits, with each pose framed inside a unique cardboard box packaging.
acceptLicenseTerms: true
---


# Couple Grid Creator

**Create a stylized 6-box grid featuring a couple in various romantic poses and outfits, with each pose framed inside a unique cardboard box packaging.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `couple_image` | image_url | yes | — | A clear photo of the couple to maintain identity. |


## Steps

### Phase A — Multi-Pose Grid Generation

If `{{couple_image}}` is not provided, ask the user to upload a photo of the couple.

Once the photo is available, submit the plan with ONE step to generate the stylized grid:

1. **Grid Generation** — `muapi image edit` (model=`qwen-image-edit-plus`):
   - Reference Image: `{{couple_image}}`
   - Prompt: `Convert the above image into an 8k portrait of both faces. Both faces should be clearly visible inside separate packaging: brown square hollow cardboard boxes. There should be 6 big boxes fully occupying the frame in a grid layout. In each box, the couple's faces should be visible, striking different decent romantic poses. Each box should feature a different costume for the couple to differentiate the scenes, with both wearing decent western wear. The background inside each box should be solid black. Maintain strict identity consistency for both the man and the woman from the reference image. Cinematic tone, sharp focus, professional photography.`
   - Aspect ratio: 1:1 or 4:5

Present the generated 6-box couple grid to the user.

## Trigger Keywords

`couple grid`, `romantic grid`, `packaging grid`, `couple photo box`, `stylized couple portrait`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
