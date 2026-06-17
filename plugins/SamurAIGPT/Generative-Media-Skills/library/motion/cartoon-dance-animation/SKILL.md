---
slug: muapi-cartoon-dance-animation
name: muapi-cartoon-dance-animation
version: "1.0.0"
description: Convert a photo of a person into a Pixar-style 3D cartoon character, then animate it using a reference dance or motion video.
acceptLicenseTerms: true
---


# Cartoon Dance Animation

**Convert a photo of a person into a Pixar-style 3D cartoon character, then animate it using a reference dance or motion video.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `user_image` | image_url | yes | — | A clear full-body or medium-shot photo of the person to be cartoonified. |
| `reference_video` | video_url | no | — | A video containing the specific dance or motion to apply to the character. |


## Steps

### Phase A — Cartoon Character Generation

If `{{user_image}}` is not provided, ask the user to upload their photo.

Once the photo is available, submit the plan with ONE step to cartoonify the image:

1. **Image Generation** — `muapi image edit` (model=`nano-banana-2-edit`):
   - Reference Image: `{{user_image}}`
   - Prompt: `Use the uploaded input photo as the exact same person in the final render. Preserve identity accurately: same face shape, eyes, nose, lips, jawline, skin tone, hairstyle, hairline, expression, age, and overall vibe. Do NOT change the person into a different face. Keep it clearly recognizable as the same person. Create one full-size ultra-high-quality 3D stylized character illustration, Pixar-inspired but original, based on the input person. Smooth plastic-like skin, soft rounded facial features, big expressive eyes, small nose, subtle blush (very minimal), cozy wholesome aesthetic. High-end character sculpting with stylized proportions while maintaining the real person’s likeness. 👕 Outfit / Costume (MUST MATCH INPUT) Keep the costume/outfit EXACTLY the same as the input image. Do not change colors, fabric type, accessories, layers, patterns, logos, or fit. No added glasses, no headphones, no new jacket, no new styling. 💇 Hair (Exact Match) Hair must remain the same as the input image: same hairstyle, same length, same hairline, only converted into clean stylized 3D hair shapes. 🎨 Render Quality Premium character sculpting, soft studio lighting, global illumination, subsurface scattering, soft shadows, cinematic depth of field, crisp edges. Octane/Arnold render look, ultra-clean, high-quality shading, 8K detail. 🎯 Composition Single full-size image (NOT a grid). Full-body or medium shot matching the input pose and vibe. Minimal clean studio background (solid color), no clutter.`
   - Negative Prompt: `No outfit change, no costume change, no new clothes, no extra accessories, no glasses, no headphones, no makeup, no cosmetics, no lipstick, no eyeliner, no facial redesign, no different face, no extra limbs, no deformed hands, no scary look, no photoreal skin pores, no wrinkles, no blur, no noise, no watermark, no logo, no text.`
   - Aspect ratio: Maintain the aspect ratio of the input image or default to 9:16.

Present the generated cartoon character to the user for approval.

### Phase B — Motion Control Animation

After the character is approved, ask the user to upload a `reference_video` (if not already provided) containing the dance or movement they want the character to perform.

Once the video is provided, submit the plan with ONE step:

1. **Motion Control Video Generation** — `muapi video from-image` or `edit_video` (model=`kling-v2.6-std-motion-control`):
   - Reference Image: The cartoon image generated in Phase A.
   - Reference Video: `{{reference_video}}`
   - Prompt: `Smooth, fluid 3D character animation. The 3D character perfectly replicates the movements and dance from the reference video. High frame rate, dynamic motion, consistent character details, Pixar animation quality.`

After generation, present the final animated dance video to the user.

## Trigger Keywords

`cartoon dance`, `3d animation`, `pixar character`, `animate my photo`, `motion control video`, `dance video`, `cartoonify and animate`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
