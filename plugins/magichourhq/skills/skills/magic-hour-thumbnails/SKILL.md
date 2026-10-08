---
name: magic-hour-thumbnails
description: Create readable, truthful video thumbnails and covers with Magic Hour, preserving supplied faces and products and testing composition at small display size. Use for YouTube thumbnails, Shorts covers, or episode covers, not a general product catalog set.
license: MIT
metadata:
  author: magichourhq
  version: "1.1.0"
---

# Magic Hour thumbnails

Make the actual topic legible in a small image. Visual drama is useful only if the viewer can identify the subject and the promised content exists in the video.

Infer the hook from supplied content and recommend one composition; do not require a technical prompt or a long creative interview. Honor existing spending authorization and delegated creative decisions while respecting requested draft approvals. Show the finished cover first. For concept selection, editable headlines and series reuse, read [cover design](references/cover-design.md).

## Find the honest visual hook

Read the supplied title, transcript, outline or footage. Choose one specific tension, comparison or outcome that it supports. Do not invent a result, reaction, endorsement, screenshot or person to make the cover more clickable. Use an authorized source image when face or product identity matters.

Build a composition around one dominant subject and one supporting cue. Put optional exact copy in a separate layout layer. Let copy complement the title rather than restating a long sentence; preserve supplied wording unless adaptation is authorized. Use the destination's actual aspect ratio and overlay regions; a thumbnail and a vertical cover need separately reviewed layouts.

## Generate only the needed visual

Use `ai_image_editor_create_image` for reference-based changes; use `ai_image_generator_create_image` when no source must be preserved. State the subject's position, scale, expression if relevant, contrast and copy region. Request the change first and protected identity second. Do not depend on generated lettering for an exact headline.

> Use my supplied workshop photo. Make the repaired blue chair the dominant subject on the right, with the damaged chair from my second photo smaller on the left. Preserve both chairs' actual construction and damage; do not exaggerate the result. Simple workshop background, clear separation, no added words. Leave the upper-left area clear for my exact headline.

If the brief supports two candidate concepts and the budget covers both, vary one meaningful idea: the comparison, framing, or subject expression. Do not spend on several nearly identical adjective changes. Generate the first candidate, inspect it, then decide whether the second answers a real question.

## Finish and judge small

Compose the exact headline/logo using available local layout tools and original assets. Keep an editable text source. Inspect the full-size export and a small preview near its actual feed size; around 160 pixels wide can expose hierarchy problems but is not a platform specification. Check recognition without zooming, text contrast, clutter, crop and overlays. Grayscale can reveal weak value separation, but does not replace color inspection.

If the subject disappears at small size, enlarge it or simplify the background before adding more text. If the exact copy clips, wrap or resize it; do not silently shorten it. If the face/product drifted, return to the original reference. Keep any watermark visible and disclose it. A visually preferred candidate is not a measured click-through winner.

## Execute and retain

Use the creation MCP at `https://mcp.magichour.ai/`; [connection guide](https://github.com/magichourhq/magic-hour-mcp/blob/main/user.md). Read live models, input limits, resolution and prices. For API use, inspect the [OpenAPI](https://docs.magichour.ai/api-reference/openapi.json), then `/v1/ai-image-editor` or `/v1/ai-image-generator`. Stay inside existing spending authorization.

Upload local inputs through `video_assets_generate_presigned_url`, PUT raw bytes without the API bearer token to storage, and use `file_path`. Create once, retain the ID, then `wait_for_image_project`; a wait timeout means retrieve the same job. Do not repeat an ambiguous creation request. Preserve signed URLs and save the final file locally.

Deliver the cover, editable copy, dimensions and any rejected requirement. Reuse the accepted series palette, type hierarchy and crop rules for the next episode, while changing the visual hook to match that episode. The [Nori case](https://github.com/magichourhq/skills/tree/main/examples/nori-thumbnail) publishes two authenticated image edits and a finished layout; broader thumbnail quality and audience response remain unmeasured.
