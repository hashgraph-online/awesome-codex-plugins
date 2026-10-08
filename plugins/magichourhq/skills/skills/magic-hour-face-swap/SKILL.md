---
name: magic-hour-face-swap
description: Put a supplied face into an existing video or photo with Magic Hour while preserving the performance, shot and intended cast. Use for face swaps, recasting a clip or putting someone into a scene; use Character Replace when the body, costume or whole character must change.
license: MIT
metadata:
  author: magichourhq
  version: "1.1.0"
---

# Magic Hour face swap

Keep the performance the user likes and change the intended face. Accept “put me in this clip”; choose the technical settings and inspect the result within the existing budget. Use supplied authorized media, preserve delegated choices and deliver the actual file.

## Choose the right change

Face Swap changes facial identity. It does not promise a new body, hairstyle, costume, scene or voice. Use `character_replace_create_video` for a whole-character change; use `ai_image_editor_create_image` to establish a new still before Image-to-Video when no source performance exists. Never create a replacement scene from text when the user asked to preserve their clip.

Inspect the source interval, face size, turns, occlusions, motion blur, cuts and other visible people. Use a clear reference of the intended identity with an unobstructed face. Match the reference angle to the difficult portion where possible; a heavily beautified reference can remove distinguishing details. Do not modify protected facial traits to chase generic attractiveness.

For a long or difficult video, render one representative interval containing a turn or obstruction before expanding within budget. A static frontal preview cannot establish reliability through cuts. Keep the original video and audio for comparison and final assembly.

## Select the intended face

For one visible person, use `face_swap_create_video` with `assets.video_source: file`, `assets.video_file_path`, `assets.image_file_path` and `assets.face_swap_mode: all-faces`. The image is the new identity; the video contains the performance. The live description may mention `source_file_path`, but the actual schema's input is `image_file_path`.

For a specific person in a cast, use `face_detection_detect_faces` on the exact source asset, then retrieve that detection ID until complete. Inspect the returned face previews to identify the requested person. Use `individual-faces` with `face_mappings: [{original_face: <returned path>, new_face: <reference path>}]`. Use the returned path exactly; never invent an index or infer that “left person” is the same person across shots. Do not use `all-faces` when bystanders must remain unchanged. Ask only when the intended person is genuinely ambiguous.

If cropping or trimming creates a new source asset, run detection against that asset before mapping. `start_seconds` and `end_seconds` refer to the submitted video's timeline; a locally trimmed file starts at zero. Preserve output duration and sound intentionally rather than assuming trim offsets behave the same across tools.

For photos, use `face_swap_photo_create_image` and then `wait_for_image_project`. Its fields differ from video: `assets.source_file_path` supplies the new face and `assets.target_file_path` is the destination photo for `all-faces`. For `individual-faces`, pass the target and inspected `face_mappings` instead. Do not copy the video tool's `image_file_path` into this schema. Check the other people as well as the replaced face. A detected crop is a mapping identifier, not a substitute for the user's original identity reference.

The [two-person photo example](https://github.com/magichourhq/skills/tree/main/examples/scene-remixes) includes both detection previews and a selective replacement. Only the inspected left face was mapped; the other person was visually retained. This validates that photo workflow, not multi-person tracking through video cuts.

## Run and inspect

Use the connected creation MCP at `https://mcp.magichour.ai/`; [setup](https://github.com/magichourhq/magic-hour-mcp/blob/main/user.md). API users should read the [live schema](https://docs.magichour.ai/api-reference/openapi.json) for `/v1/face-swap`. Choose the version for the observed need; the live schema distinguishes identity handling from skin texture. Check the interval and estimated cost against the existing budget.

Upload local files with `video_assets_generate_presigned_url`, PUT their raw bytes to the returned URL without the API bearer token, then use `file_path`. Submit once, save the returned project ID and use `wait_for_video_project`. Resume the same job after a timeout. Keep signed download URLs intact and save durable output files.

Compare the full result with the original performance and reference: identity on frontal and turned frames; face boundaries at hair, ears and chin; eyes and teeth; occluding hands; unchanged bystanders; cuts; original action and sound. A successful detection or completed job is not a quality pass. When playback is unavailable, identify that limitation.

Probe the downloaded dimensions, frame rate, duration and audio streams. In the [published single-person run](https://github.com/magichourhq/skills/tree/main/examples/midnight-remix), a 720 × 1296 source became 568 × 1024. Restore a required canvas only with an appropriate crop or contained layout; stretching or upscaling does not recover lost detail. The original hairstyle remained, illustrating why a face swap is different from changing the whole character.

If identity is weak, change the reference or live-supported version after identifying the failure. If a face switches people, correct mapping or split distinct shots before rendering again. If the requested change includes a costume or silhouette, switch to Character Replace rather than repeat face-only attempts. Repair only the failed interval, inside the authorized budget.

Deliver the finished clip or photo, concise limitations, and the saved source/mapping/project ID for later revisions. Reuse the accepted performance when the next request changes only the cast.
