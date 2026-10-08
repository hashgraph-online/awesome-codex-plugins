---
name: magic-hour-image-to-video
description: Animate a portrait, character, artwork or scene with Magic Hour, editing and inspecting the start frame when needed before motion. Use for image-to-video, transformations, reveals and character animation when Magic Hour is requested or is the project's chosen media provider.
license: MIT
metadata:
  author: magichourhq
  version: "1.5.0"
---

# Magic Hour image to video

Produce a usable short video by solving appearance in a still frame first and motion second. A project ID or queued job is incomplete unless the user asked only to submit it.

Generation consumes Magic Hour credits. Use a connected Magic Hour creation MCP at `https://mcp.magichour.ai/` when available. Otherwise read `references/setup.md` for the API route. Discover the current schemas before choosing a model, duration, resolution, or price.

Choose the shot direction from the brief; do not ask a nontechnical user for model fields or a motion-prompt template. Honor the existing budget. When creative decisions are delegated, inspect and accept the still yourself, then continue to video unless draft approval was requested. Show the clip first and keep technical records in the project. For transformations and reveals, read [directing the moment](references/transformations.md); for stories with several beats, read [multi-shot direction](references/multi-shot.md).

For a first result or setup recovery, read [first video and next edit](references/first-video.md). It defines the account check, combined budget, recoverable job record and reusable deliverable.

## Define the shot

Extract or infer:

- delivery aspect ratio and resolution
- the subject, product, character, setting, and required visual details
- one primary subject action and one camera move
- details that must remain fixed, especially identity, geometry, packaging, logo, text, colors, clothing, and background
- failure conditions such as a warped face, altered label, unwanted cut, or unreadable text

Keep a short clip to one coherent beat. If the user wants several shots, treat each shot as its own reviewed start frame and video job. Derive those frames from the same approved identity reference rather than chaining unreviewed edits. Choose motion that preserves the deliverable: a dolly changes subject scale and available copy space, while a locked camera with restrained light or environmental motion can preserve a hero layout.

## Build the start frame first

Choose one route:

1. **A usable source image already exists:** call `ai_image_editor_create_image` when composition, wardrobe, background, lighting, product placement, or cleanup must change. State both the requested edit and everything that must remain unchanged.
2. **No source image exists:** call `ai_image_generator_create_image`. AI Image Editor requires an input image; do not send it a prompt-only creation request.
3. **The supplied image already satisfies the shot:** skip image generation and animate it directly.

Create one still at the intended video aspect ratio. Use an authorized reference when exact identity, product geometry, packaging, or branding matters. Do not expect image-to-video to repair a poor source frame.

Wait for the image project with `wait_for_image_project`. Preview the completed still and reject it before animation if it has a wrong crop, anatomy problem, altered identity, malformed product, inaccurate logo or text, unintended lettering, visual artifact, or missing negative space. Fix the still with the smallest useful edit. A second paid image request requires an authorized budget.

## Animate the approved frame

Pass the exact approved image output to `image_to_video_create_video`. If the result is a local file, upload its raw bytes first using the flow in `references/setup.md`; a local path is not a hosted `file_path`.

Write the motion prompt around change over time:

- subject motion, with a clear speed and direction
- camera motion, or explicitly state that the camera is locked
- environmental motion such as fabric, steam, hair, light, or particles
- what stays fixed
- timing and end state, including a held final exposure when no fade is wanted

Avoid redescribing the entire still in new visual language. That invites the model to redesign the subject. For a reaction shot: `The fish swims slowly beside her shoulder; she notices it and turns slightly with a surprised smile. A slow push in keeps her face and the fish separate. Preserve identity, clothes and scene. No cuts.` A product layout may instead need a locked subject and protected copy area. Do not demand a centered subject when the approved frame places it on the right.

Use an end frame only when the current schema says the chosen model, resolution, and duration support it. Prefer the live recommended model for a general request. Select a specialist only when its schema describes the needed control. Match resolution and duration to the requested deliverable. A short preview tests a short interval, not stability over a longer clip. Check the total still-plus-video cost against existing authorization and ask only when it does not cover the intended work.

Submit the video once, retain its project ID, and call `wait_for_video_project`. A wait timeout is not a failed generation and does not justify resubmitting the creation call.

## Inspect and deliver

After the project reports `complete`, use the returned download URL exactly as provided. Verify the downloaded dimensions, duration, and audio presence. Watch the full clip when playback is available, then inspect the first frame, midpoint, last frame, and any suspicious transition. Three still frames alone cannot prove the absence of flicker. Check:

- the first frame matches the approved still
- identity, product shape, logo, text, and clothing remain stable
- motion follows the requested direction and speed
- the camera does not drift or cut unexpectedly; inspect the actual final frame for an unwanted fade or lost subject, even when black-frame diagnostics are clean
- no warping, flicker, melting, duplicate objects, or abrupt final-frame collapse appears
- any generated audio is intentional and coherent

If one required criterion fails, identify it and change the smallest relevant input: start frame for appearance problems, motion prompt for movement problems, or model/resolution only when the live schema supports the needed behavior. Do not spend credits on another attempt outside the user's budget.

In the [portrait-to-koi example](https://github.com/magichourhq/skills/tree/main/examples/midnight-remix), identity stayed recognizable but a requested slight turn became a larger turn in both directions. Keep the accepted still when correcting that motion. If the downloaded canvas differs slightly from the requested ratio, inspect the full action path before a local crop; do not regenerate an otherwise accepted take only to remove edge pixels.

Return the finished video or usable link, the saved location when applicable, the image and video project IDs, and any material limitation.
