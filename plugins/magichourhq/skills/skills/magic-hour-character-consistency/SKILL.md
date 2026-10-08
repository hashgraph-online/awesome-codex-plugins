---
name: magic-hour-character-consistency
description: Keep a recurring character recognizable across Magic Hour images, storyboards, and video shots. Use for a mascot, fictional character, or authorized person appearing in multiple scenes; not a single portrait or face swap.
license: MIT
metadata:
  author: magichourhq
  version: "1.2.0"
---

# Magic Hour character consistency

Make the same character survive changes of scene, pose, and camera. A repeated name or seed does not establish visual identity.

Reuse the existing character and series context. Choose staging and technical settings yourself when delegated; do not make the user fill out a character template or repeatedly approve in-budget work. Respect requested review points and show the accepted scenes first. For a cast, new angle or recurring episode, read [series continuity](references/series.md).

## Establish the anchor

Read the existing character sheet or approved image before asking for another. Separate fixed traits (face shape, hair silhouette, build, distinctive marks, rendering style) from scene variables (pose, expression, setting, lighting). Clothing is fixed only when the brief requires continuity. Record visible facts; do not infer hidden details or a real person's identity.

If there is no reference, create one useful view with `ai_image_generator_create_image`. Prefer a clear face and readable silhouette at the scale the story needs. An elaborate turnaround is unnecessary for two similar shots; a back view or unusual angle may need its own reviewed anchor. Keep only individually accepted views—an inconsistent contact sheet is not a better reference.

## Build shots from the original

For each scene, use `ai_image_editor_create_image` with the approved identity image in `assets.image_file_paths`. If using additional pose/style images, describe each reference's role and check the chosen model's input limit. Do not merge a style donor's face or clothing into the character. Never claim reference ordering or weighting controls that the live schema does not expose.

Start with the scene change and a request to retain the reference character. State critical identity details when the brief needs them, but do not automatically copy the entire character sheet into every prompt. A detailed prompt does not rule out duplicates or omissions. In the [Nori comparison](https://github.com/magichourhq/skills/tree/main/examples/nori-character), the shorter prompt preserved details better in one scene; added identity instructions helped another. Choose by the output, not prompt length.

> Place this robot in a sunlit greenhouse, watering a small potted seedling. Keep the same character and watercolor-and-ink illustration style. Full body, three-quarter view. No text or extra characters.

Adapt that example to the actual reference and requested scene; do not add the robot to an unrelated request. Derive each new scene from an approved anchor, not from the last unreviewed scene. Compare the first new scene before spending on the rest.

For requested animation, review each shot's still first, then pass that exact image to `image_to_video_create_video`. Prompt for one coherent action and restrained camera motion. If a required face turns away or becomes small, inspect that interval particularly carefully. Match continuity at cuts: screen direction, eyeline, scale, wardrobe, palette and time of day. Do not promise identical pixels across generations or a seamless transition between independently generated shots.

## Run and recover

Use the connected creation MCP at `https://mcp.magichour.ai/`; [setup](https://github.com/magichourhq/magic-hour-mcp/blob/main/user.md). Otherwise consult the [live API schema](https://docs.magichour.ai/api-reference/openapi.json): `/v1/ai-image-generator`, `/v1/ai-image-editor`, `/v1/image-to-video`. Choose supported parameters and count anchor creation, scene edits and animation against the existing budget. Never buy credits or expand a batch automatically.

Upload local files with `video_assets_generate_presigned_url`, PUT raw bytes to its `upload_url` without the API bearer token, then pass the returned `file_path`. Submit once, retain each ID and use `wait_for_image_project` or `wait_for_video_project`. Resume the same job after a polling timeout; do not repeat an ambiguous creation call. Preserve signed download URLs exactly and save durable outputs.

## Accept and reuse

Compare all accepted scenes side by side with the anchor, not just each other. Check face/eye shape, proportions, distinctive marks, clothing continuity, hands, duplicate limbs and style. Count repeated details such as scarf ends and antennae; a recognizable character can still gain or lose them. Mark required details hidden by a prop or pose as unverified. Inspect the full videos for momentary identity changes. Reject only the failed scene and return to the anchor; do not redesign accepted scenes to match an error.

Deliver individual shots in order plus the accepted anchor and a short reusable identity note. Record changed traits and rejected outputs explicitly. Keep project IDs and local files so the next episode can reuse approved work without reconstructing it from chat. The Nori case publishes five authenticated MCP outputs and mixed prompt-comparison results; broader character coverage and animation quality remain unverified.
