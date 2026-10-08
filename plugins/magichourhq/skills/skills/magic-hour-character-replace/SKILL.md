---
name: magic-hour-character-replace
description: Replace a subject in an existing video or transfer its performance onto a reference character with Magic Hour. Use for whole-character recasting and motion transfer; not face-only swaps or generating unrelated scenes with a recurring character.
license: MIT
metadata:
  author: magichourhq
  version: "1.1.0"
---

# Magic Hour character replace

Reuse a performance the user already likes. Accept “make my character do this” or “replace this performer”; infer the correct mode from what the user wants to preserve. Keep the reference and source footage distinct and complete the requested clip within the existing budget.

## Choose replace or animate

| Request                                                 | Mode                          | What to inspect                                                         |
| ------------------------------------------------------- | ----------------------------- | ----------------------------------------------------------------------- |
| Put my character into this footage, keeping the setting | `replace`                     | Intended subject replaced, source action and surrounding scene retained |
| Make the character in my image perform this motion      | `animate`                     | Reference character and image composition, transferred performance      |
| Change only this person's face                          | Face Swap                     | Facial identity; body and costume are outside that operation            |
| Same character in a newly invented scene                | Image Editor → Image-to-Video | New approved still before motion                                        |

Do not use a text prompt to invent a source performance that was already supplied. The current Character Replace schema has mode and subject-selection controls, not a general scene-prompt field. Do not fabricate camera, seed or strength settings.

## Prepare the performance

Inspect the actual video interval, dimensions, cuts, subject count, visible limbs, occlusions and motion speed. Match the character reference to the visible body and framing when possible. A portrait cannot establish faithful unseen legs; complicated hand contacts and fast turns need a representative output check. Keep the original, rather than repeatedly feeding generated revisions back into the model.

Use authorized footage and reference images. For a difficult or long source, generate a short representative interval before committing the remaining budget. Select the difficult action, not only the easiest stationary moment. Preserve any user-requested duration and review point.

For one unambiguous subject, use `style.selection_mode: auto`. For a specific subject in a crowd, use `point` and inspect a source frame to obtain `position_x`, `position_y` in original video pixels plus `time_seconds`. Coordinates from a resized preview must be scaled back. Time uses the source clock, including when `start_seconds` is nonzero. Never guess coordinates or add a cropped-clip offset twice. Ask only when the target person is ambiguous.

## Execute and compare

Use `character_replace_create_video` with `assets.image_file_path`, `assets.video_file_path`, the source interval, supported resolution and `style.mode`. Use the creation MCP at `https://mcp.magichour.ai/`; [setup](https://github.com/magichourhq/magic-hour-mcp/blob/main/user.md). API users should consult the [live schema](https://docs.magichour.ai/api-reference/openapi.json) for `/v1/character-replace`. Check final interval cost against the existing authorization.

Upload local inputs through `video_assets_generate_presigned_url`, PUT raw bytes without the API bearer token, then pass `file_path`. Create once, save the project ID, and use `wait_for_video_project`. Resume the same project on a timeout. Keep returned download URLs intact and save the completed file.

Review the whole result beside both inputs: correct target, recognizable character, intended mode, head/body proportions, hands and feet, source gesture timing, contact with objects, occlusion boundaries, background and audio. Multiple attractive frames cannot establish a preserved performance. Check every cut; a changed face or extra limb is a failed requirement.

Measure the actual output interval and dimensions before assembly. Our [replace-mode example](https://github.com/magichourhq/skills/tree/main/examples/midnight-remix) kept a recognizable fox character but returned 5.375 seconds for a 0–5-second request. Compare the same source moments; do not assume matching frame numbers or silently retime a required performance.

The [animate-mode example](https://github.com/magichourhq/skills/tree/main/examples/scene-remixes) uses the same reference and performance but keeps the reference's studio setting, while replace mode keeps the source station. Use that difference to honor “keep my character's world” versus “put my character in this footage.” Both require timing and full-playback review; one simple head turn does not establish dance or complex-contact quality.

If the wrong person changes, fix subject selection. If body shape fails, improve framing/reference compatibility or simplify the source interval. If the scene changes unexpectedly, verify the mode before spending again. Repair only the failed shot within budget. Do not describe all motion as faithfully transferred merely because the job completed.

Deliver the finished clip, source/reference/mode retained in the existing project brief, and unresolved defects. Reuse the same reference for the next performance; reuse the accepted performance when only the character changes. Saved web-app Characters are not automatically addressable through MCP—use actual accessible images or supported account-library tools if they become available.
