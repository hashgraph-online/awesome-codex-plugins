---
name: kling-ai-generate-video
description: Write Kling AI / 可灵 video prompts and storyboards, prepare video settings including HDR for approval, and submit authorized text-to-video, image-to-video, omni reference, keyframe, or motion-control requests in Claude Code.
---

# Kling AI video generation

Deliver the user's current step. Use the execution workflow only when preparing or submitting generation. The [core Kling Skill](../kling-ai/SKILL.md) owns OAuth, billing, task identity and result handling.

## Choose the current step

- **Prompt or storyboard only:** use [motion and shots](references/motion-and-shots.md) to decide whether supplied text needs edits or to guide new writing. Deliver the requested text. Leave out account queries, uploads, unsolicited submission settings, and invitations to generate.
- **Final settings for approval:** discover compatible capabilities, present a complete proposal, and wait for approval.
- **Authorized generation:** run the workflow below and honor approval already given for those settings.
- **Continue after recharging:** follow the [resume workflow](../kling-ai/references/tool-workflows.md#resuming-after-insufficient-credits) first. Preserve the model, output settings, prompt, and reference roles. For image-to-video, recheck the original first-frame slot and source availability before any new submission.
- **Existing task:** follow the core status workflow and query the known `generationId` once.

When preparing generation with a missing required asset, ask only for that asset
and explain its role. For example, "请发商品图片或可访问的图片链接，我会用它作首帧。"
Wait for the asset before discovery or upload.

Read [scene patterns](references/scene-patterns.md) when product, advertising, social, or cinematic work needs scene-specific decisions. For Elements, the motion library, or local media, also read the core [asset workflows](../kling-ai/references/asset-workflows.md).

## Workflow

1. **Capture the request.** Record the user's model restriction, duration, ratio, resolution, dynamic range (HDR or SDR), count, sound, shot intent, and reference roles. Clarify only unresolved choices that materially change the result. Create or reuse the UUIDv7 `taskTraceId` under the core Skill.
2. **Discover candidates.** Follow [capability discovery](../kling-ai/references/capability-discovery.md) and [video routing](references/model-routing.md). Compare `text_to_video` and `omni_ref_video` for text-driven requests, or `image_to_video` and `omni_ref_video` for image-driven requests, when present. Keep text-only omni models eligible even without attachments.
3. **Match the requirements.** Choose one live tool/model pair that supports the requested model, output settings, sound and input roles. Required HDR needs a declared HDR mode compatible with the resolution. Required silence needs a declared sound-off value or an explicit silent-output guarantee. A required first frame needs a dedicated frame input. Name the eligible variant, Kling 4.0 or Kling 4.0 Flash, when recommending one. If no pair meets the requirements, explain the conflict and stop.
4. **Build and verify the request.** Read the selected tool's complete `inputSchema`, using `ToolSearch` if the tool is deferred. Use [model parameters](../kling-ai/references/model-parameters.md) to bind settings such as duration and an explicit first-frame aspect ratio. For a requested resolution such as `1080p`, check the selected tool/model pair's enum and applicable conditions. Read [motion and shots](references/motion-and-shots.md) for every new generation, edit, or variant, including when the user provides a complete prompt. Reuse a suitable prompt verbatim, edit only what needs to change, or write a prompt when none was supplied. For an authorized retry with identical settings, reuse the original prompt. Prepare media for that pair and stop on upload failure. Check the serialized request against the brief and the [MCP contract](../kling-ai/references/mcp-contract.md), including top-level `model`, the required prompt, and the required first-frame slot.
5. **Present settings and submit with approval.** Show the selected pair, prompt summary, output settings including the resolution and any requested dynamic range, shot structure, reference roles and required billing disclosure. Follow the [balance check and single-submission workflow](../kling-ai/references/tool-workflows.md#generation), then use the core Skill's App or headless result workflow. For invalid references, follow [media-reference troubleshooting](../kling-ai/references/troubleshooting.md#upload-or-media-reference-fails). Use a confirmed video task number to recover the video and source task numbers only to refresh references.

## Mode rules

- Element use requires explicit support for its resource type and binding argument in the selected model; do not infer it from the entry point name.
- Image-to-video and omni reference distinguish first frame, tail frame, keyframes, identity or product reference, style, video, and audio. Pass only roles declared by the selected model and satisfy all conditional combination limits. Pure-text omni reference requires a model that permits no media input.
- Keep audio references, generated sound, and original-sound retention distinct. Use the selected model's declared audio controls and input slots. Describe the submitted controls separately from audio or video quality you inspected.
- For a continuous-shot request, express that intent in the prompt and use only legal shot settings. If the user needs a hard guarantee, require explicit model support before submitting.
- Motion control requires a subject image. Choose exactly one motion source - a motion-library ID or a source video - as directed by the live tool. Use the core asset workflow to resolve library IDs and validate motion direction and duration.
- A multi-shot plan is one confirmed video task. Do not submit one generation per shot unless the user explicitly approves separate tasks.

## Quality defaults

- Prefer `1080p` for normal delivery and supported `4k` for commercial, large-screen, or post-production work. Use `720p` for drafts, speed, credit savings, or model limitations. Never lower a higher live default.
- Use about 5 seconds for one action or shot, about 10 seconds for dialogue, a complete product action, or two connected beats, and longer only when supported and narratively necessary.
- Honor the user's explicit duration, ratio, resolution and count before applying defaults. For text-to-video with no requested ratio, infer it from the destination. For image-to-video with no requested ratio, preserve the first-frame composition unless the tool requires a ratio. An explicitly requested ratio must be passed when supported, even with a first frame.
- Use one primary camera movement in a five-second shot. Use multiple shots only when location, time, scale, or information state changes.
- Do not add unrequested narration, readable text, extra characters, product claims, prices, endorsements, or certifications.

Before submission, internally check whether the action fits the duration, camera instructions conflict, first and tail frame intent is clear, references remain continuous, and multi-shot durations sum correctly. Claim visual QA only when the result was actually inspected.
