---
slug: muapi-multi-angle-reshoot
name: muapi-multi-angle-reshoot
version: "1.0.0"
description: Re-render a subject or scene from multiple dramatic camera angles, such as fish-eye, bird's-eye, low-angle, and macro, while maintaining consistent identity and detail.
acceptLicenseTerms: true
---


# Multi-Angle Reshoot

**Re-render a subject or scene from multiple dramatic camera angles, such as fish-eye, bird's-eye, low-angle, and macro, while maintaining consistent identity and detail.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `subject_description` | text | yes | — | Description of the subject or scene (e.g. "a professional woman in a black suit holding a laptop"). |
| `reference_image` | image_url | no | — | Optional reference image to maintain consistency across angles. |


## Steps

### Phase A — Subject Establishment

If `{{reference_image}}` is not provided, submit the plan with ONE step to create the base subject:

1. **Subject Generation** — `muapi image generate` (model=`nano-banana-pro`):
   - Prompt: `A high-quality, professional photograph of {{subject_description}}. Clean studio lighting, sharp focus, realistic textures, cinematic quality.`
   - Aspect ratio: 3:4 or 1:1

Present the base image to the user for approval.

### Phase B — Multi-Angle Reshoot

Once the subject is established, submit the plan using `muapi image edit` (model=`nano-banana-2-edit`) to generate the requested angles. Use the approved image from Phase A as the reference for ALL steps.

1. **Bird's Eye View**
   - Reference: Base Image
   - Prompt: `A dramatic bird's eye view (from directly above) of the same subject. High-angle perspective, wide shot, looking down. Maintain exact clothing, face, and setting consistency.`
2. **Fish Eye Lens**
   - Reference: Base Image
   - Prompt: `A high-distortion fish-eye lens photograph of the same subject. Ultra-wide angle, curved edges, dramatic perspective, immersive feel. Maintain exact clothing and face consistency.`
3. **Low Angle (Hero Shot)**
   - Reference: Base Image
   - Prompt: `A low-angle "hero shot" looking up at the subject. Makes the subject appear powerful and dominant. Maintain exact clothing and face consistency.`
4. **Dutch Angle**
   - Reference: Base Image
   - Prompt: `A stylized Dutch angle (tilted horizon) photograph of the same subject. Cinematic, slightly uneasy or dramatic vibe. Maintain exact clothing and face consistency.`
5. **Macro Close-up**
   - Reference: Base Image
   - Prompt: `An extreme macro close-up focused on a specific detail of the subject (e.g., eyes, texture of the suit, or a feature of the laptop). Shallow depth of field, incredible detail. Maintain exact colors and textures.`
6. **Worm's Eye View**
   - Reference: Base Image
   - Prompt: `A worm's eye view from ground level looking straight up at the subject. Dramatic vertical perspective. Maintain exact clothing and face consistency.`

After generating the variations, present the multi-angle gallery to the user. You can also offer to generate specific individual angles based on their feedback.

## Trigger Keywords

`multi angle`, `photo reshoot`, `change camera angle`, `fish eye view`, `birds eye view`, `low angle shot`, `macro photography`, `camera perspective`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
