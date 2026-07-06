---
slug: muapi-action-figure-generator
name: muapi-action-figure-generator
version: "1.0.0"
description: Convert a photo of a person into a custom 3D action figure, complete with collectible toy packaging.
acceptLicenseTerms: true
---


# Action Figure Generator

**Convert a photo of a person into a custom 3D action figure, complete with collectible toy packaging.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `user_image` | image_url | yes | — | A clear photo of the person to be turned into an action figure. |
| `toy_theme` | text | no | superhero | The theme of the action figure (e.g. superhero, doctor, explorer, sci-fi). |


## Steps

### Phase A — Action Figure Creation

If `{{user_image}}` is not provided, ask the user to upload their photo.

Once the photo is available, submit the plan with ONE step to generate the action figure:

1. **Action Figure Generation** — `muapi image edit` (model=`nano-banana-2-edit`):
   - Reference Image: `{{user_image}}`
   - Prompt: `A high-quality 3D stylized action figure based on the person in the input image. The action figure should maintain the person's likeness (face, hairstyle, skin tone) but be rendered as a plastic toy with visible joints and a semi-glossy finish. The character is dressed in a {{toy_theme}} outfit. The figure is displayed inside its original collectible cardboard and plastic blister packaging. The packaging has the person's name printed on it and features clean, modern graphic design. Soft studio lighting, realistic plastic textures, 8k resolution, cinematic look.`
   - Aspect ratio: 1:1 or 4:5

Present the generated action figure to the user. You can also suggest creating different themes (e.g., changing the character from a doctor to a space explorer).

## Trigger Keywords

`action figure`, `custom toy`, `toy packaging`, `character toy`, `collectible figure`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
