---
name: magic-hour-body-swap
description: Place a supplied person into a scene image with Magic Hour Body Swap, preserving the intended identity and checking pose, scale and scene contact. Use for full-person photo placement; use Face Swap for only a face and Character Replace for an existing video performance.
license: MIT
metadata:
  author: magichourhq
  version: "1.0.0"
---

# Magic Hour body swap

Accept “put me in this scene.” Identify the person reference and destination image, choose settings within the existing budget, inspect the result and deliver the image. Do not swap source and destination or reinterpret a face-only request as replacing the whole person.

## Prepare compatible inputs

Use `body_swap_create_image` when an entire person belongs in a supplied scene. Use photo Face Swap when the existing body/outfit must remain, AI Image Editor for a directed background or wardrobe change, and Character Replace when preserving a video performance is the actual job.

Inspect both images before generating: intended person, visible body extent, pose, camera height, lighting and destination scale. A headshot cannot specify unseen clothing or legs. Prefer a reference showing the body the scene needs; if a new view is necessary, create/edit it deliberately within budget and identify invented details. Preserve actual identity and clothing choices rather than adding unsolicited body or beauty changes.

Determine whether the scene contains one obvious replacement subject or needs a new placement. The endpoint has person and scene inputs but no point selector, mask or placement prompt. For multiple people or a precise empty-space location, use a tool that exposes suitable control, or first prepare an unambiguous scene. Do not guess which bystander the endpoint will replace.

## Generate and inspect the contact

Use the creation MCP at `https://mcp.magichour.ai/`; [setup](https://github.com/magichourhq/magic-hour-mcp/blob/main/user.md). Pass `assets.person_file_path` for the identity/body reference, `assets.scene_file_path` for the destination and a supported `resolution`. API users should read `/v1/body-swap` in the [live schema](https://docs.magichour.ai/api-reference/openapi.json). It does not accept a general prompt, strength, mask, seed or model field; do not invent them.

Upload local inputs with `video_assets_generate_presigned_url`, PUT raw bytes to `upload_url` without the API bearer token, then use `file_path`. Submit once, save the ID and `wait_for_image_project`. Resume the same ID after a timeout. Preserve exact download URLs and save a durable image.

Compare against both inputs: recognizable face, intended outfit/body, pose, limb count, hands, perspective, subject scale, ground/chair contact, shadow direction, occlusion and unchanged surrounding people/objects. Inspect full resolution and the intended small display size. Verify the downloaded dimensions; a plausible face alone does not make a convincing placement.

For wrong identity, return to a clearer original reference. For wrong position or altered bystanders, use an available editor with the needed control instead of repeating the same uncontrolled request. For bad body geometry, fix reference/framing compatibility. Repair only the failed requirement within budget and state unresolved issues.

In the [published placement case](https://github.com/magichourhq/skills/tree/main/examples/scene-remixes), Body Swap changed facial likeness and recomposed the station. A two-reference Image Editor repair restored a closer likeness and the side-platform setting; framing and fine scene details still differed. Inspect both attempts; do not treat a successful Body Swap request as proof that the destination was preserved.

## Continue to motion only after the still works

If video was requested, animate the accepted placement through Image-to-Video and describe action, camera and end state. Do not ask motion generation to repair extra limbs or incorrect contact in the start frame. If exact choreography was supplied, use Character Replace with the original performance instead.

Deliver the finished image or requested video, both source references and the accepted placement decisions. Reuse the scene when changing the person and the person reference when changing the scene; a crop or caption does not need another body swap.
