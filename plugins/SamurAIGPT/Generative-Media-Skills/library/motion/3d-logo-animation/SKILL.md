---
slug: muapi-3d-logo-animation
name: muapi-3d-logo-animation
version: "1.0.0"
description: Transform a 2D logo into a premium 3D version and animate it with professional cinematic effects.
acceptLicenseTerms: true
---


# 3D Logo Animation

**Transform a 2D logo into a premium 3D version and animate it with professional cinematic effects.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `logo_image` | image_url | yes | — | A clear 2D image of the logo to be converted to 3D. |
| `material_style` | text | no | glossy glass and chrome | The material style for the 3D logo (e.g., gold, matte plastic, holographic). |


## Steps

### Phase A — 3D Logo Transformation

If `{{logo_image}}` is not provided, ask the user to upload their logo.

Once the logo is available, submit the plan with ONE step to convert it to 3D:

1. **3D Logo Generation** — `muapi image edit` (model=`nano-banana-2-edit`):
   - Reference Image: `{{logo_image}}`
   - Prompt: `Transform this 2D logo into a premium, high-quality 3D version. The logo should have depth and be made of {{material_style}}. Smooth edges, realistic reflections, and professional studio lighting. The logo is centered on a clean, minimal, out-of-focus background. High-end graphic design aesthetic, 8k resolution.`
   - Aspect ratio: 1:1 or 4:3

Present the 3D logo to the user for approval.

### Phase B — Cinematic Logo Animation

Once the 3D logo is ready, submit the plan to animate it:

1. **Logo Animation** — `muapi video from-image` (model=`veo3.1-fast-image-to-video`):
   - Reference Image: The 3D logo from Phase A.
   - Prompt: `A professional cinematic logo reveal animation. The 3D logo rotates slowly with dynamic light sweeps reflecting off its {{material_style}} surface. Subtle camera movement, particle effects in the background, high-quality motion graphics style.`
   - Aspect ratio: 16:9 or 1:1

After generation, present the final 3D logo animation to the user.

## Trigger Keywords

`3d logo`, `logo animation`, `2d to 3d logo`, `animated logo`, `cinematic logo`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
