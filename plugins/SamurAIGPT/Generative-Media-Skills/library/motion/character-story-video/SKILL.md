---
slug: muapi-character-story-video
name: muapi-character-story-video
version: "1.0.0"
description: Create a multi-part animated story video by first establishing a consistent character and then generating sequential scenes and animating them.
acceptLicenseTerms: true
---


# Character Story Video

**Create a multi-part animated story video by first establishing a consistent character and then generating sequential scenes and animating them.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `character_description` | text | yes | — | Description of the main character (e.g. "a cute piglet wearing a leather aviator jacket and goggles"). |
| `story_premise` | text | yes | — | The overall story arc (e.g. "building a jetpack and flying to space"). |
| `reference_image` | image_url | no | — | Optional starting image of the character to maintain consistency. |


## Steps

This skill involves multiple phases to build a cohesive narrative.

### Phase A — Character Establishment

If `{{reference_image}}` is NOT provided, submit the plan with ONE step to create the character:
1. **Character Creation** — `muapi image generate` (model=`nano-banana-pro`):
   - Prompt: `{{character_description}}, introducing the main character, cinematic lighting, highly detailed, Pixar 3D animation style.`
   - Aspect ratio: 4:5 or 1:1

If `{{reference_image}}` IS provided, use it as the established character and proceed to Phase B.

After generation, ask the user to confirm the character design before proceeding.

### Phase B — Sequential Scene Generation

Once the character is established, create the story beats (e.g., Scene 1, Scene 2, Scene 3).
Submit the plan using `muapi image edit` (model=`nano-banana-2-edit` or `flux-kontext-pro-i2i`) to maintain character consistency. Use the established character image as the reference for ALL these steps.

1. **Scene 1 (Beginning)**
   - Reference: Character Image
   - Prompt: `The character ({{character_description}}) in the first scene of the story: [Describe the beginning of {{story_premise}}]. Cinematic lighting, Pixar 3D animation style, storybook illustration.`
2. **Scene 2 (Middle)**
   - Reference: Character Image
   - Prompt: `The character ({{character_description}}) in the second scene: [Describe the climax or middle action of {{story_premise}}]. Cinematic lighting, Pixar 3D animation style, storybook illustration.`
3. **Scene 3 (End)**
   - Reference: Character Image
   - Prompt: `The character ({{character_description}}) in the final scene: [Describe the resolution of {{story_premise}}]. Cinematic lighting, Pixar 3D animation style, storybook illustration.`

*Note: All scenes should be generated in parallel or sequentially depending on the story flow.*

After generating the scenes, present them to the user and ask if they are ready to animate the story.

### Phase C — Animation (Sequel Part 1, Part 2, Part 3)

Submit the plan to animate the generated scenes using an image-to-video model (e.g., `kling-v3.0-pro-image-to-video` or `veo3.1-image-to-video`).

1. **Part 1 Video**
   - Input: Scene 1 Image
   - Prompt: `Cinematic animation of the scene, character comes to life, subtle natural movements, high quality 3D animation.`
2. **Part 2 Video**
   - Input: Scene 2 Image
   - Prompt: `Cinematic animation of the scene, character comes to life, dynamic action, high quality 3D animation.`
3. **Part 3 Video**
   - Input: Scene 3 Image
   - Prompt: `Cinematic animation of the scene, character comes to life, triumphant resolution, high quality 3D animation.`

After generating the videos, present them to the user as a multi-part story sequence. You may also suggest using the `muapi predict result` + ffmpeg concat tool to merge them into a single movie if requested.

## Trigger Keywords

`character story`, `story video`, `animated story`, `sequel video`, `multi part video`, `sequential story`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
