---
slug: muapi-jewelry-product-video
name: muapi-jewelry-product-video
version: "1.0.0"
description: Create a luxury jewelry advertisement with high-end commercial cinematography and detailed macro animation.
acceptLicenseTerms: true
---


# Jewelry Product Video

**Create a luxury jewelry advertisement with high-end commercial cinematography and detailed macro animation.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `jewelry_description` | text | no | a delicate rose gold ring with a lotus design and a sparkling diamond | Detailed description of the jewelry item. |
| `surface_description` | text | no | a beige surface | The surface the jewelry is resting on. |


## Steps

### Phase A — High-End Jewelry Rendering

Submit the plan with ONE step to create the base luxury image:

1. **Luxury Image Generation** — `muapi image generate` (model=`nano-banana-2-edit`):
   - Prompt: `Style: Luxury product ad, high-end commercial feel. Scene: {{jewelry_description}} resting on {{surface_description}}. A soft, warm light highlights the diamond, creating subtle highlights on the metal. 100mm macro lens photography, shallow DOF, incredible detail, elegant and minimal composition.`
   - Aspect ratio: 1:1 or 4:5

Present the luxury image to the user for approval.

### Phase B — Cinematic Animation

Once the image is approved, submit the plan with TWO sequential video steps to build the commercial:

1. **Macro Rotation** — `muapi video from-image` (model=`grok-imagine-image-to-video`):
   - Reference Image: The luxury image from Phase A.
   - Prompt: `[00:00–00:02] Close-up shot, 100mm macro lens, shallow DOF. A soft, warm light highlights the diamond, creating subtle highlights on the rose gold. Slight 1-second camera rotation around the ring. Smooth, elegant movement.`
   
2. **Facet Gliding** — `muapi video from-image` or `muapi video from-image` (model=`grok-imagine-image-to-video`):
   - Reference Image: The luxury image from Phase A.
   - Prompt: `[00:02–00:05] Extreme close-up on the diamond, 200mm macro lens, razor-thin DOF. A focused LED light illuminates the diamond, catching every facet. The camera glides slowly over the diamond, showcasing its brilliance. Ethereal, sparkling highlights.`

*Note: You can use the `muapi predict result` + ffmpeg concat tool to merge these shots into a final 5-second commercial.*

After generation, present the final jewelry commercial video to the user.

## Trigger Keywords

`jewelry video`, `luxury ad`, `diamond animation`, `ring commercial`, `high-end jewelry showcase`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
