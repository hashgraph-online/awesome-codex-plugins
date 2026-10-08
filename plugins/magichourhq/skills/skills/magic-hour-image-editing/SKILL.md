---
name: magic-hour-image-editing
description: Edit an existing image with Magic Hour while protecting details outside the requested change. Use for background replacement, cleanup, relighting, recoloring or reframing when Magic Hour is requested or is the project's chosen provider. Requires a source image; not prompt-only creation.
license: MIT
metadata:
  author: magichourhq
  version: "1.3.0"
---

# Magic Hour image editing

Deliver the requested change without redesigning the source. A convincing image can still be a failed edit if it changes the subject's face, shape, label, or other protected detail.

Infer the edit from the supplied image and plain-language request; recommend one treatment if needed. Choose technical settings yourself, reuse existing spending authorization and inspect the result before delivery. Do not insert draft approvals when the user delegated creative decisions. Show the image first and retain technical records in the project. For relighting, new backgrounds or difficult aspect ratios, read [faithful edits](references/faithful-edits.md).

## Establish the edit boundary

Inspect the source. Separate **change** (background, color, lighting, object, framing) from **preserve** (identity, geometry, pose, clothing, exact text, unaffected surroundings). Infer from the request; ask only when ambiguity changes the result. Do not describe unseen details as verified.

Keep the source as the identity reference. If multiple references are supported, identify each role: subject, setting, or style. A style reference must not replace the subject. Check the chosen model's reference limit rather than assuming the endpoint's maximum applies to every model.

- If a crop already meets the composition, use an available local image tool; do not pay to regenerate the subject.
- For new backgrounds, lighting, colors, or missing canvas, use `ai_image_editor_create_image` with the real source. Do not reconstruct an exact product or person using text-to-image.
- For background-only changes, preserve viewpoint and pose. A new angle asks the model to invent unseen details.
- Do not claim masking, exact pixel preservation, transparent output, or a negative-prompt field unless the current tool supports it. “Keep unchanged” is an instruction, not a guarantee.

## Prompt the change, then protect the source

Use this order: requested edit; output framing; protected details; shadows/reflections; rejection conditions. Keep the prompt proportional to the edit. Do not add cinematic styling to a simple cleanup.

> Replace only the wet stone and dark setting with a clean white studio background and a soft contact shadow. Reframe to a square with the complete bottle centered and breathing room on every edge. Preserve the reference bottle's silhouette, cap dimensions, blue glass, camera angle, and single label reading “AURORA”. Remove the colored background light while keeping the blue material recognizable. No extra objects, duplicated labels, or new text.

For a personal transformation, use the same change/preserve boundary: “Move this person into a midnight platform with golden fish swimming through the air. Keep their face, hair, coat and pose. Place the nearest fish beside the shoulder without covering the face. Match the new lighting.” Preserve the person's actual features; do not add beauty, age or body changes unless requested. If video is next, solve the final canvas, visible limbs and effect placement here before paying for motion.

Do not paste the original generation prompt wholesale: it may request the background being replaced. Keep promotional copy in a separate layout layer when a suitable tool is available. Text already printed on the subject is protected content.

## Execute once and compare

Use the connected creation MCP at `https://mcp.magichour.ai/`; [setup](https://github.com/magichourhq/magic-hour-mcp/blob/main/user.md). For API fallback, keep credentials outside chat/source code. Read the [live schema](https://docs.magichour.ai/api-reference/openapi.json) for model eligibility, resolution, aspect ratio, reference count, and cost. Web-app settings do not prove API support.

For local inputs, call `video_assets_generate_presigned_url`, PUT raw bytes to `upload_url`, verify success, and use its `file_path`. Never send the API bearer token to storage. Direct API creation is `POST /v1/ai-image-editor`; retrieval is `GET /v1/image-projects/{id}`. Retain the ID, use `wait_for_image_project` or retrieve that same job, and never repeat an ambiguous creation request automatically.

Use one output at a resolution that reveals the critical detail. A tiny preview cannot validate small label text. Stay within the existing authorized budget; ask only when it does not cover the intended work. Do not buy credits or upgrade. A model/resolution change needs a fresh cost check, not automatic reconfirmation when already authorized.

Compare the completed result beside the source, including a close view of protected details:

- Did the requested change happen everywhere, including reflections and contact areas?
- Are identity, silhouette, proportions, label, and unaffected content still correct?
- Do hair, glass, edges, shadows, and removed-object regions look natural?
- Does the downloaded file have the required dimensions and detail? A requested aspect ratio can be ignored. Crop only if it preserves the full subject and copy area; otherwise choose a supported reframing/model route within budget. Never stretch or silently deliver the wrong size.

If it fails, name the failure. Revise from the original when identity drifted; use an accepted edit for minor cleanup only after its protected details pass inspection. Do not chain unreviewed edits. Stop at the budget limit and disclose unresolved defects.

| Failure                                                    | Change on the next authorized attempt                                                                                 |
| ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Wrong dimensions despite a ratio setting                   | Verify model support; use a safe crop or a different supported reframing route, not another adjective-heavy prompt.   |
| Correct setting but altered face, cap, label, or viewpoint | Return to the original, remove competing appearance instructions, and consider a model with better reference control. |
| Correct identity but wrong placement                       | Keep model and source; specify subject scale and a clear boundary for the copy area.                                  |
| Floating object or retained old reflection                 | Describe the new contact surface and shadow/reflection treatment; keep unrelated details fixed.                       |

Use the exact download URL, retrieve the same project if it expires, and save a durable file when requested. Return the edited image, project ID, and limitations. If you cannot inspect the image, say so rather than reporting it as verified.
