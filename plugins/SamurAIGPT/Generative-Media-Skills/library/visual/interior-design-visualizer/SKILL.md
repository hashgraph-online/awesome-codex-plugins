---
slug: muapi-interior-design-visualizer
name: muapi-interior-design-visualizer
version: "1.0.0"
description: Visualize interior design by generating an empty room and filling it with stylish furniture and decor, or by redesigning an existing room.
acceptLicenseTerms: true
---


# Interior Design Visualizer

**Visualize interior design by generating an empty room and filling it with stylish furniture and decor, or by redesigning an existing room.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `room_type` | text | no | modern living room | The type of room to design (e.g. living room, bedroom, office). |
| `design_style` | text | no | contemporary minimalist | The aesthetic style (e.g. Scandinavian, Industrial, Bohemian). |
| `empty_room_image` | image_url | no | — | Optional image of an empty room to be used as a base. |


## Steps

### Phase A — Room Setup

If `{{empty_room_image}}` is not provided, submit the plan with ONE step to generate an empty base room:

1. **Empty Room Generation** — `muapi image generate` (model=`gpt-image-2-text-to-image`):
   - Prompt: `A professional wide-angle photograph of a completely empty {{room_type}} with {{design_style}} architecture. Large windows with natural light, clean wooden or tiled flooring, white or neutral-colored walls, no furniture, high ceiling. High-quality architectural photography, cinematic look.`
   - Aspect ratio: 4:3 or 1:1

Present the empty room to the user.

### Phase B — Furnishing & Styling

Once the base room is ready, submit the plan to fill it with furniture:

1. **Room Furnishing** — `muapi image edit` (model=`nano-banana-2-edit`):
   - Reference Image: The empty room image from Phase A (or the user-provided `{{empty_room_image}}`).
   - Prompt: `A stunningly designed {{room_type}} filled with high-end furniture in a {{design_style}} style. Includes a comfortable sofa, stylish coffee table, elegant rug, indoor plants, decorative wall art, and ambient lighting. The furniture placement is natural and architecturally sound. Photorealistic textures, soft lighting, cozy and inviting atmosphere, 8k resolution.`
   - Aspect ratio: Same as the base image.

After generation, present the final interior design visualization to the user. You can offer to generate variations with different styles (e.g., "Change style to Industrial").

## Trigger Keywords

`interior design`, `room visualizer`, `furniture design`, `home decor`, `redesign room`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
