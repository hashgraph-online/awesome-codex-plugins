---
slug: muapi-selfie-with-celebrities
name: muapi-selfie-with-celebrities
version: "1.0.0"
description: Generate a realistic behind-the-scenes selfie of the user with a celebrity or main actor from a specific movie, followed by an option to generate a cinematic long-take video connecting multiple selfies.
acceptLicenseTerms: true
---


# Selfie with Celebrities

**Generate a realistic behind-the-scenes selfie of the user with a celebrity or main actor from a specific movie, followed by an option to generate a cinematic long-take video connecting multiple selfies.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `movie_name` | text | yes | — | The name of the movie featuring the celebrity you want to take a selfie with (e.g., "Harry Potter", "The Matrix"). |
| `user_image` | image_url | yes | — | A clear photo of the user to be used for the selfie. |


## Steps

### Phase A — Generate First Selfie Image

If the `{{user_image}}` is not provided, ask the user to upload their image first.

Once provided, submit the plan with ONE step:

1. **Selfie Image Generation** — `muapi image edit` (model=`nano-banana-2-edit`):
   - Reference Image: `{{user_image}}`
   - Prompt: `POV: close up shot, A realistic photo of the person (don't change the person's original clothes) holding a black iPhone 16 to take a picture with the main actor from the movie "{{movie_name}}" on a movie set with movie scene background. Behind-the-scenes atmosphere, including film equipment, film cameras, filled with props, and busy crew members. Sharp focus on the characters. bright scene. Aspect ratio 9:16.`
   - Aspect ratio: 9:16

After generating the first image:
- Present the generated selfie to the user.
- Ask the user if they would like to create a second, third, etc. image with different movies or actors.
- Also, suggest to the user that once they have multiple images, you can create a seamless cinematic video transitioning between the selfies.

### Phase B — Generate Connecting Video (Only when requested)

If the user has generated at least two selfies and asks to create a video connecting them, submit the plan with ONE step:

1. **Cinematic Video Generation** — Use an image-to-video model like `kling-o1-image-to-video`, `pixverse-v5.5-i2v`, or `veo3.1-image-to-video`.
   - First frame image: The first generated selfie.
   - Last frame image: The second generated selfie (or use multiple steps if connecting more than two).
   - Prompt: `A seamless cinematic long-take. The camera follows a person as she finishes a photo with an actor, then she naturally turns and walks toward the right. The camera tracks her movement with a smooth gimbal-like motion. Her gait is consistent and confident. Upon entering a new behind-the-scenes movie set, she slows down and stops gracefully, raising her phone with a bright smile to take a selfie with two actors. The scene transition is natural and smooth, with a seamless connection.`
   - Aspect ratio: 9:16

After generation:
- Present the video to the user.

## Trigger Keywords

`selfie with celebrity`, `movie star selfie`, `celebrity photo`, `take a picture with actor`, `behind the scenes selfie`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
