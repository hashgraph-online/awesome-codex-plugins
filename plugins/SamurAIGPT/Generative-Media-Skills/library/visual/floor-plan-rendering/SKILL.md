---
slug: muapi-floor-plan-rendering
name: muapi-floor-plan-rendering
version: "1.0.0"
description: Design a 2D floor plan and convert it into a realistic, high-quality 3D architectural rendering.
acceptLicenseTerms: true
---


# Floor Plan Rendering

**Design a 2D floor plan and convert it into a realistic, high-quality 3D architectural rendering.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `floor_plan_description` | text | yes | — | Description of the floor plan (e.g. "a modern 2-bedroom apartment with a balcony and open kitchen"). |
| `base_plan_image` | image_url | no | — | Optional 2D floor plan image to use as a starting point. |


## Steps

### Phase A — 2D Floor Plan Design

If `{{base_plan_image}}` is not provided, submit the plan with ONE step to create the 2D blueprint:

1. **Floor Plan Generation** — `muapi image generate` (model=`nano-banana-2`):
   - Prompt: `A professional, clean 2D architectural floor plan of {{floor_plan_description}}. Top-down view, technical drawing style, white background, black lines, labeled rooms (Living Room, Kitchen, Bedroom, etc.), high contrast, minimalist design.`
   - Aspect ratio: 4:3 or 1:1

Present the 2D plan to the user for approval.

### Phase B — 3D Rendering

Once the 2D plan is ready, submit the plan to convert it into a realistic 3D visualization:

1. **3D Conversion** — `muapi image edit` (model=`nano-banana-2-edit`):
   - Reference Image: The 2D plan from Phase A.
   - Prompt: `A stunning, realistic 3D isometric cutaway rendering of the architectural floor plan. Photorealistic textures, warm wooden flooring, modern furniture, soft natural sunlight coming from windows, realistic shadows. High-end architectural visualization, cinematic look, 8k resolution, clean white studio background.`
   - Aspect ratio: 4:3 or 1:1

After generation, present the final 3D rendering to the user.

## Trigger Keywords

`3d floor plan`, `architectural rendering`, `2d to 3d plan`, `house design`, `interior plan`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
