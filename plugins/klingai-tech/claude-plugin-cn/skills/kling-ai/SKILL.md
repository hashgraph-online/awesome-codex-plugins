---
name: kling-ai
description: Handle Kling AI / 可灵 requests, including prompt-only planning, missing-asset next steps, generation preparation and approved image/video creation. Route creative work to the dedicated Skills; manage Elements, motion library, uploads, credits, existing tasks and account switching through the remote MCP.
license: MIT
---

# Kling AI

Use only the remote China MCP configured by this plugin: `https://klingai.com/mcp/plugin`. Do not switch regions, register a second Kling MCP, or start or depend on a local MCP server.

## Request routing

- Identify whether the user wants creative writing, a generation proposal, a submission, or an existing-task query. Creative writing ends with the requested prompt or plan. A generation proposal uses live capability discovery and ends with the settings for review. Submit only after approval under the billing rules below.
- For image prompts, creation, or editing, follow [kling-ai-generate-image](../kling-ai-generate-image/SKILL.md).
- For video prompts, storyboards, missing-image next steps, generation, model selection or motion transfer, follow [kling-ai-generate-video](../kling-ai-generate-video/SKILL.md). For generation preparation, discover relevant entry points including pure-text omni; prompt-only work and requesting a missing asset do not need account queries.
- Keep uploads, Elements, motion-library browsing, account operations, credit checks, and task status in this Skill. It also supplies the shared connection, billing, submission, and result rules for both generation Skills.
- Motion library: browse with `motion_library_list`. Resolve the selected motion, then follow the video Skill for `motion_control` with a subject image and exactly one motion source.
- Subject library / Elements: use `element_list`, `element_get`, `element_create`, `element_update`, or `element_delete` for the requested operation. Resolve real IDs before reuse.
- Account and credits: use `query_membership_and_credits`; model capabilities come from `who_am_i`.
- Existing tasks or missing results: use [generation and results](#generation-and-results) with the known `generationId` for that submission. A status or library request never creates a generation.
- To continue after topping up or a queue rejection, follow [resuming a paused generation](references/tool-workflows.md#resuming-a-paused-generation) before preparing a submission. A top-up notification by itself calls for a balance check only.
- Sign-out or account switching: act only on an explicit user request, stay on the China endpoint, and complete the client's native MCP OAuth before further Kling calls.

Call only tools present in the live tool list. An attachment alone does not determine its role; clarify only when first frame, tail frame, identity/product reference, editable source, motion source, or style reference would materially change the request.

Read [asset workflows](references/asset-workflows.md) for Elements, the motion library, or uploads. Before generation, follow [capability discovery](references/capability-discovery.md), then [model parameters](references/model-parameters.md), [tool workflows](references/tool-workflows.md), and the [MCP contract](references/mcp-contract.md). Use [prompt examples](references/prompt-examples.md) for creative direction and [troubleshooting](references/troubleshooting.md) after a failure.

## Connection and task identity

- Use the client's native MCP OAuth flow for the plugin's `kling-ai` server. In Claude Code, select it from `/mcp`. Never request an API key, token, cookie, authorization header, or credential file. Never log private account fields, upload tickets, or signed URLs.
- Let the client manage OAuth discovery, client registration, and credentials through its native MCP flow. This plugin does not configure a custom OAuth client name; do not invent registration overrides or block authorization because the host cannot set one. If the real OAuth flow fails, report the sanitized error and follow [troubleshooting](references/troubleshooting.md).
- Create one UUIDv7 `taskTraceId` for each unrelated new objective. Reuse it across discovery, upload, generation, and querying for that objective wherever the live tool accepts it.
- Preserve exact returned IDs. Present `generationId` as the task number; expose `taskTraceId` only when troubleshooting requires it.

## Billing and single submission

- Image, video, and motion generation consume credits. Call `who_am_i` during preparation and select only models returned in the current account's `availableModels` for the chosen tool, with their declared arguments, inputs, and combination limits. Follow capability discovery for cross-tool selection and refresh stale definitions before proceeding. Do not infer model access from a tool's existence, membership tier, or static examples.
- Show the final workflow, model, prompt summary, duration/resolution, aspect ratio, output count, and reference roles. Honor existing explicit authorization for the same unsubmitted intent and unchanged final settings; otherwise obtain confirmation before submission. An upload, library operation, or credit check is not generation approval.
- Include any billing disclosure required by the live model/tool in those final settings. For omni reference that declares per-second billing with input video duration included, explain both facts before submission; output duration alone is not the total billed duration. Do not invent a rate or total credit estimate.
- Each approval covers one submission attempt. A rejected attempt, timeout, ambiguous response, or rendering problem requires fresh approval before another submission.
- Do not save an Element automatically during ordinary generation. Element writes and deletion must follow the user's explicit request as described in [asset workflows](references/asset-workflows.md).

## Generation and results

1. Resolve reference roles, Elements, and motion sources; prepare local media before submission. Use the returned provider references exactly as the selected live schema requires.
2. Follow [tool workflows](references/tool-workflows.md#generation) to confirm the final billable settings, validate the request, check the balance on the same connection, and submit once. A multi-shot plan remains one task unless the user approves separate tasks.
3. Once `generationId` is known, use only `query_tasks` for follow-up and keep the ID even if a later query omits it. If an ambiguous submission yields no ID, report the observed error or incomplete response and the unknown creation and billing state, then stop. `query_tasks` requires the ID. A trace ID, unchanged balance, or absent history entry cannot resolve that state.
4. If the client renders the generation MCP App and it can refresh, let the App own automatic refresh. Do not add duplicate media, thumbnails, or download links.
5. If the App is absent or cannot refresh, query the same task at the provider-permitted interval until terminal, cancelled, rate limited, interrupted, or a query fails. During polling, if a resource error explicitly says to check the same task later, retry that status query once at the permitted interval. Return the tool's text fallback and at most one primary link per usable result, in the returned order. Do not add Markdown image/video embeds or claim an unmounted App was displayed.
6. For an explicit status request or a report that the result is missing, query the original task once and report its state and any usable result. When a query fails or polling stops before completion, keep the task number, label the last confirmed state (such as accepted or processing), and explain that the current state could not be confirmed. Use “status unconfirmed” if no state was ever confirmed.
7. Report full completion only after terminal success with the requested number of usable results of the requested media type. Count a work with its own status only if that status is successful. For video, count playable video rather than its cover. If a successful task yields fewer usable results than requested, deliver the available results and report the actual count (for example, “2 of 3 images generated”). If none are usable, report the missing results. Keep the original task number in either case.

Report the returned status, known task number, and effective submitted settings when available. State the actual credit charge only if the tool returns it, for example in `creditsConsumed`.

## Quality defaults

Apply only when the user has not specified another choice and the live model supports it:

- Prefer full-quality models. Use Turbo, fast, or low-cost modes when the user prioritizes drafts, speed, or credit savings.
- Images: prefer `2k` for normal delivery and `4k` for commercial or crop-heavy work; use `1k` for drafts or speed. Never lower a higher live default.
- Videos: prefer `1080p` for normal delivery and supported `4k` for commercial or post-production work; use `720p` for drafts, cost, speed, or model limitations.
- Generate one result unless more are requested. Use about 5 seconds for one action, about 10 seconds for two connected beats, and longer only when supported and needed. Motion-control duration comes from the selected source and live constraints.
- When the user did not specify a ratio, infer it from the destination, or preserve the first frame for image-to-video unless the tool requires one. When the user did specify a ratio, pass that supported value even with a first frame.

## Failure behavior

- Unauthorized: use the client's native MCP OAuth and continue only after authorization succeeds.
- Unsupported argument or invalid media: follow [troubleshooting](references/troubleshooting.md) to verify the request and locate the original task before considering a new submission.
- Insufficient credits: preserve the original settings and submission state and follow [resuming a paused generation](references/tool-workflows.md#resuming-a-paused-generation).
- Provider failure: report the sanitized provider message and preserve the task number. Do not resubmit automatically.
- Expired media URL: query the original `generationId` for current outputs before reuse. A failed refresh is not permission to create a replacement task.
