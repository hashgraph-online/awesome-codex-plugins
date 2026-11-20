---
name: kling-ai-generate-image
description: Write or refine Kling AI image prompts, including prompt-only requests, or generate and edit images through the Kling AI MCP in Claude Code. Use for posters, product photography, portraits, covers, advertising stills, visual concepts, and controlled variants.
---

# Kling AI image generation

For prompt-only work, use [prompt construction](references/prompt-construction.md)
to decide whether the prompt needs edits, then return the requested prompt.
Preserve composition requirements such as left-side copy space.
Leave out account queries, uploads, unsolicited submission settings, and invitations
to generate.

Use the workflow and quality defaults only when preparing or submitting generation.
If a required image is missing, request it and explain its role before starting
discovery. Follow the [core Kling Skill](../kling-ai/SKILL.md) for OAuth, billing,
submission, and results.

Read [scene patterns](references/scene-patterns.md) when product, advertising, portrait, poster, or cover work needs scene-specific decisions. For Element reuse or local media, also read the core [asset workflows](../kling-ai/references/asset-workflows.md).

## Workflow

For a request to continue after recharging, start with the [resume workflow](../kling-ai/references/tool-workflows.md#resuming-after-insufficient-credits). It determines whether to report an existing task or proceed with the original settings.

1. Use `text_to_image` for a new image or series without references. Use `image_to_image` when source media controls identity, product structure, composition, editable content, or style. An attachment alone does not determine the mode.
2. Ask only for missing information that materially changes the result: subject, destination and aspect ratio, required copy, reference roles, protected facts, or output count.
3. Create or reuse the UUIDv7 `taskTraceId` for this objective, follow [capability discovery](../kling-ai/references/capability-discovery.md), and select a compatible tool/model pair from this account's `who_am_i` response. Apply [model parameters](../kling-ai/references/model-parameters.md) before constructing arguments or reference bindings.
4. Bind each reference image to the selected model's exact slot, including `image_1` when required. Use the live `inputType` literal, such as `URL` when declared, and the complete media URL. On resume, reuse an original upload URL while it remains valid. Refresh historical Kling results by their source task number before reuse. If a required image is unavailable, pause and follow [media-reference troubleshooting](../kling-ai/references/troubleshooting.md#upload-or-media-reference-fails).
5. Read [prompt construction](references/prompt-construction.md) for every new generation, edit, or variant, including when the user provides a complete prompt. Use it to review the prompt for its intended use. Reuse a suitable prompt verbatim, edit only what needs to change, or write a prompt when none was supplied. For an authorized retry with identical settings, reuse the original prompt.
6. Show the final mode, model, prompt summary, resolution, aspect ratio, output count, and reference roles. Obtain explicit approval under the core Skill's billing rule; honor an existing explicit authorization for the final settings.
7. Verify the top-level `model`, required `arguments[]`, and required `inputs[]` against the [MCP contract](../kling-ai/references/mcp-contract.md). After approval and immediately before calling `text_to_image` or `image_to_image`, run the [balance check](../kling-ai/references/tool-workflows.md#generation) on the same connection. Submit once only when that check permits it, then preserve the task number and follow the core Skill's result workflow.
8. Follow the core Skill's result rules for single images and image series.

## Mode rules

- When the user leaves model selection open, prefer Kling Image 4.0 for `text_to_image` and `image_to_image` if the chosen tool lists it and it meets the request. Otherwise, prefer that tool's compatible `defaultModel`, then another compatible model from the same tool. Honor an explicit model choice, including a request for the tool's default, and explain any unmet requirement before proposing another model.
- For a continuous image series, select a model that explicitly supports series generation at the requested count and resolution in one task. Set the count using the declared field and send a series switch only if the model declares one. Multiple independent outputs do not fulfill a continuous series. If no model fits, explain the limit before submission.
- For Kling Image 4.0 Series Mode, enable `story_mode` and set `imageCount` to the requested total when the live tool/model pair declares those fields. Verify that 8K is available with the requested count and mode; the public 8K specification does not establish MCP access. If the requested combination is unavailable, ask before changing the model, resolution, or count.
- Element support follows the selected model's declared resource types and binding argument, not the entry point name.
- Image-to-image may use one or more images with explicit roles. State the purpose of every image when multiple references are present.
- Before using an Element subject, follow the core asset workflow, call `element_get`, and choose a model that explicitly supports the resource type and binding argument. Check individual and combined reference caps, and bind the exact ID with the model's declared prompt and structured syntax.
- For a variant, lock every fact that the user did not ask to change. Change one major dimension per confirmed generation.
- A status request uses only `query_tasks`; it does not create an image.
- If the provider rejects an argument or reference, retain the prompt, mode, and reference roles while diagnosing the specific field. Recover the image edit using its own confirmed task number. Use the source image's task number only to refresh the source.

## Quality defaults

- Prefer live-supported `2k` for normal delivery, `4k` for commercial work, advertising, fine materials, or crop-heavy post-production, and `1k` only for drafts, speed, or credit savings. Never lower a higher live default.
- Infer ratio from destination: `1:1` for square social or product media, `4:5` for portrait feeds, `9:16` for stories or vertical covers, and `16:9` for banners or thumbnails.
- Generate one image unless the user requests more.
- Unless the user explicitly requests text inside the generated image, prefer a clean image with intentional copy-safe space.
- Treat brand names, logos, faces, product structure, and user-provided copy as protected facts. Never invent performance, price, certification, ingredients, awards, effects, or statistics.

Before submission, internally check focal subject, visual hierarchy, safe area, lighting, reference roles, and conflicting instructions. Claim visual QA only when the result was actually inspected.
