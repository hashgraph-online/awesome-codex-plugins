---
name: magic-hour-image-editing
description: Edit an existing image or apply the same edit to a folder of images with Magic Hour. Use for background replacement, cleanup, relighting, recoloring or reframing when Magic Hour is requested or is the project's chosen provider. Protect details outside the requested change. Requires source images.
license: MIT
metadata:
  author: magichourhq
  version: "1.5.0"
---

# Magic Hour image editing

Deliver the requested change without redesigning the source. A convincing image can still be a failed edit if it changes the subject's face, shape, label, or other protected detail.

Infer the edit from the supplied image and plain-language request; recommend one treatment if needed. Choose technical settings yourself, reuse existing spending authorization and inspect the result before delivery. For a single image, do not insert draft approvals when the user delegated creative decisions. For a folder, follow the preview and approval steps below. Show the image first and retain technical records in the project. For relighting, new backgrounds or difficult aspect ratios, read [faithful edits](references/faithful-edits.md).

## Establish the edit boundary

Inspect the source. Separate **change** (background, color, lighting, object, framing) from **preserve** (identity, geometry, pose, clothing, exact text, unaffected surroundings). Infer from the request; ask only when ambiguity changes the result. Do not describe unseen details as verified.

If the user names a saved character or reference instead of attaching an image, use `list_saved_items` (or authenticated `GET /v1/saved-items` through the existing API) with the matching type. Match the name, paginate with `next_cursor` as needed and disambiguate multiple matches. Inspect a suitable `IMAGE` asset and reuse its durable `file_path` in `assets.image_file_paths`, without another upload. An explicitly supplied image remains authoritative.

Keep the source as the identity reference. If multiple references are supported, identify each role: subject, setting, or style. A style reference must not replace the subject. Check the chosen model's reference limit rather than assuming the endpoint's maximum applies to every model.

- If a crop already meets the composition, use an available local image tool; do not pay to regenerate the subject.
- For new backgrounds, lighting, colors, or missing canvas, use `edit_image` with the real source. Do not reconstruct an exact product or person using text-to-image.
- For background-only changes, preserve viewpoint and pose. A new angle asks the model to invent unseen details.
- Do not claim masking, exact pixel preservation, transparent output, or a negative-prompt field unless the current tool supports it. “Keep unchanged” is an instruction, not a guarantee.

## Prompt the change, then protect the source

Use this order: requested edit; output framing; protected details; shadows/reflections; rejection conditions. Keep the prompt proportional to the edit. Do not add cinematic styling to a simple cleanup.

> Replace only the wet stone and dark setting with a clean white studio background and a soft contact shadow. Reframe to a square with the complete bottle centered and breathing room on every edge. Preserve the reference bottle's silhouette, cap dimensions, blue glass, camera angle, and single label reading “AURORA”. Remove the colored background light while keeping the blue material recognizable. No extra objects, duplicated labels, or new text.

For a personal transformation, use the same change/preserve boundary: “Move this person into a midnight platform with golden fish swimming through the air. Keep their face, hair, coat and pose. Place the nearest fish beside the shoulder without covering the face. Match the new lighting.” Preserve the person's actual features; do not add beauty, age or body changes unless requested. If video is next, solve the final canvas, visible limbs and effect placement here before paying for motion.

Do not paste the original generation prompt wholesale: it may request the background being replaced. Keep promotional copy in a separate layout layer when a suitable tool is available. Text already printed on the subject is protected content.

## Execute once and compare

Use the connected creation MCP at `https://mcp.magichour.ai/`; [setup](https://github.com/magichourhq/magic-hour-mcp/blob/main/user.md). For API fallback, keep credentials outside chat/source code. Read the [live schema](https://docs.magichour.ai/api-reference/openapi.json) for model eligibility, resolution, aspect ratio, reference count, and cost. Web-app settings do not prove API support. Check both selected settings and omitted-field defaults against the account's effective tier. The current Image Editor default is paid-only; live guidance supplies an explicit Free-compatible combination when it fits the brief. Set those fields explicitly rather than assuming omission is plan-aware. Credits do not unlock paid-only models or resolutions. After a tier restriction, avoid an unchanged retry or blind field removal. Change settings only within delegated choices; ask before changing explicit model/resolution requirements.

For local inputs, call `get_upload_urls`, PUT raw bytes to `upload_url`, verify success, and use its `file_path`. Never send the API bearer token to storage. Direct API creation is `POST /v1/ai-image-editor`; retrieval is `GET /v1/image-projects/{id}`. Retain the ID, use `wait_for_image_project` or retrieve that same job, and never repeat an ambiguous creation request automatically.

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

## Apply the same edit to a folder

1. **Choose the inputs.** List the supported originals directly in the requested folder. Include subfolders only when requested and skip the output folder. Choose a separate output directory and a distinct destination for each original, including files with the same stem. Keep a local batch record there with the input list, destinations, edit instructions and settings, approvals, and each file's status. Save using the actual output format and preserve existing files.
2. **Preview one original.** Use `get_account_info` and verify eligibility and the per-image price in the live [Image Editor schema](https://docs.magichour.ai/api-reference/openapi.json). Start with `model: flux-2-klein`, `resolution: 640px` and `image_count: 1` (5 credits at the documented settings). It keeps the source aspect ratio. If these settings cannot meet the requested detail or framing, or the price cannot be verified, pause before spending. Use existing authorization for the preview or ask before running it. Submit it using the per-file procedure below. Show the actual edit beside its source and get approval of the result.
3. **Confirm the remaining cost.** Keep the accepted preview as that original's result. Confirm the exact price against the preview's `credits_charged` and current pricing. Show the remaining file count, credits per file and total credits for the remaining batch. If there are files left, get explicit approval of that spend and record it before submitting any of them. Get fresh approval if the approved inputs, edit, settings or price change.
4. **Edit each file separately.** Use `get_upload_urls` and `edit_image` for each original with the approved prompt and settings. Pass only that original in `assets.image_file_paths`. Before submission, record a unique project `name` and mark the file as submitting. Save the returned job ID and charge immediately. Wait for that job, inspect the output against its own original, and save one accepted result per file.
5. **Resume from the record.** Keep completed outputs. If a job ID exists, get the same project with `get_image_project` and recover its download if needed. If a submission might have gone through without a returned ID, check the original tool response and look for the exact recorded project name in the same account's creations if available. If the job cannot be confirmed, leave that file pending for reconciliation. A missing download or a timeout is not evidence that the job never ran. Continue with files known to be unsubmitted within the approved spend. Reconcile the prior submission and get approval before any new paid attempt for the same file.
6. **Report the results.** List successful files with output paths and files that need attention with the reason and any known job IDs. Include credits charged when available, and call out unresolved charges separately.
