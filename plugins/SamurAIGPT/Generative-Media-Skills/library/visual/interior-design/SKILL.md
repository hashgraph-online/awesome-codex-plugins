---
slug: muapi-interior-design
name: muapi-interior-design
version: "1.0.0"
description: Create professional interior design visualizations — redesign existing rooms, generate new room concepts, or visualize specific furniture styles in a space.
acceptLicenseTerms: true
---


# Interior Design

**Create professional interior design visualizations — redesign existing rooms, generate new room concepts, or visualize specific furniture styles in a space.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `room_type` | text | yes | — | The type of room (e.g. "modern living room", "scandinavian kitchen", "luxury master bedroom", "minimalist home office"). |
| `design_style` | text | no | modern minimalist | The aesthetic direction (e.g. "japandi", "industrial loft", "boho chic", "mid-century modern", "art deco"). |
| `color_palette` | text | no | neutral tones with wood accents | Preferred colors and materials (e.g. "sage green and brass", "monochrome black and white", "warm terracotta"). |
| `specific_elements` | text | no | — | Particular items to include (e.g. "large floor-to-ceiling windows", "velvet green sofa", "statement pendant light"). |
| `room_photo` | image_url | no | — | Optional photo of an existing room to redesign or use as layout reference. |


## Steps

### Phase A — Room Concept / Redesign

Submit the plan with ONE or TWO steps:

1. **Main Visualization** — If `{{room_photo}}` is provided, use `muapi image edit` (model=`flux-kontext-pro-i2i`); otherwise use `muapi image generate` (model=`nano-banana-pro`):
   - Prompt: `Professional interior design visualization of a {{room_type}}. Style: {{design_style}}. Color palette: {{color_palette}}. {{specific_elements}}. Cinematic lighting, architectural photography style, wide angle lens, 8k resolution, photorealistic textures. High-end interior design magazine quality.`
   - If `{{room_photo}}` is used, add: `Maintain the structural layout and window placement of the reference room. Completely transform the furniture, decor, and wall finishes to match the new style.`
   - Aspect ratio: 16:9 (standard for room views)

2. **Alternative Angle (Optional)** — `muapi image generate` (model=`bytedance-seedream-v4.5`):
   - Prompt: `A different perspective/closeup of the same {{room_type}} — focus on the textures and lighting of the {{specific_elements}}. {{design_style}} aesthetic, {{color_palette}}. Professional interior photography.`

After generation:
- Present the new room design
- Offer to "expand the room" using `ai-image-extension` to see more of the space
- Suggest adding a 3D-style walkthrough video using `kling-v3.0-pro-image-to-video`
- Offer to generate a specific mood board for this design

## Notes
- `flux-kontext-pro-i2i` is the best model for maintaining the "soul" of a room while changing the design style.
- For small rooms, suggest using "bright natural light" and "minimal furniture" to make the space feel larger.
- For commercial spaces (offices, cafes), add "professional workplace lighting" to the prompt.

## Trigger Keywords

`interior design`, `room redesign`, `home decor`, `architecture visualization`, `room concept`, `furniture layout`, `house design`, `interior visualization`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
