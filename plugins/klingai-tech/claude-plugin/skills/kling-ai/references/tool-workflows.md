# Remote tool workflows

## Generation

1. Use the plugin's single `kling-ai` connection at `https://kling.ai/mcp/plugin` and follow [capability discovery](capability-discovery.md), including all tool-list pages and relevant new entry points.
2. Create or reuse the objective's UUIDv7 `taskTraceId`, reuse the successful `who_am_i` response for this preparation, and apply [model parameters](model-parameters.md) to the selected tool/model pair. Video selection follows [video routing](../../kling-ai-generate-video/references/model-routing.md), including `omni_ref_video` when available. Refresh capability data when invalidated, not just because another reference was loaded.
3. For Elements, motion-library selections, or local media, follow [asset workflows](asset-workflows.md). A library operation does not authorize generation. Do not silently fall back to text-only generation if a required reference is unavailable.
4. Show the final mode, model, prompt summary, resolution, duration when applicable, aspect ratio, output count, and reference roles. Include live-required billing disclosures, including per-second billing and input video duration when applicable. Describe shot controls only as declared by the model, without inferring the actual number of cuts. Obtain explicit approval under the core Skill's billing rule.
5. Validate the actual payload against the [MCP contract](mcp-contract.md). Immediately before submission, call `query_membership_and_credits` on the same connection. If no current balance is available, preserve the request and explain that the balance could not be confirmed. If the balance is zero or negative, the provider reports insufficient credits, or a live estimate for these settings exceeds the balance, follow [the resume workflow](#resuming-after-insufficient-credits). Submit only after the balance check permits it. A positive balance with no live estimate does not guarantee coverage.
6. Call the selected generation tool once and preserve its returned `generationId` and status. Follow [task status refresh](#task-status-refresh) for the result.
7. Apply the [core Skill's result rules](../SKILL.md#generation-and-results) to terminal results. Without a rendered App, include the task number, text fallback, and one primary media link per usable requested result.

## Resuming after insufficient credits

1. Keep the original objective, tool, canonical model ID, prompt, output settings, reference slots and available source references in the current conversation. Keep the `taskTraceId`, submission state, and any confirmed `generationId`. State whether the request stopped before submission, was rejected, or has an unconfirmed outcome. Quote a credit shortfall only when the live service estimates the cost for the same settings.
2. Direct the user to the official recharge entry returned for the connected account's region, or to [Kling's Global site](https://kling.ai/) to sign in and recharge the same account. Ask them to return to the same conversation and request continuation. A report that they have recharged by itself calls for a balance refresh only.
3. When the user asks to continue, resolve the original request from the conversation. If multiple requests match, ask which one. If the submission has a known `generationId`, query that task first and report its status or result. If a submission was attempted without a confirmed task number, proceed only when the service explicitly confirmed that it created no task and charged no credits. Otherwise report the unknown state and pause.
4. Before any permitted new submission, revalidate the original model and media slots on the same account and reuse the `taskTraceId`. Reuse valid upload URLs and refresh historical Kling results by task number. For an expired upload URL, upload the original media again if accessible, or ask for the missing media. Keep the approved settings where available. Changes to billable settings or another attempt after a rejected call require explicit approval under the core Skill. Run the balance check immediately before submission, then submit once if it passes.

## Task status refresh

- If the Claude Code MCP App renders, let it refresh internally. For a direct status request or a report that a result is missing, query the original `generationId` once and report the current status or usable result.
- If the App does not render during generation, poll the same `generationId` with `query_tasks` at the provider-permitted interval until success, failure, cancellation, or the turn cannot continue. If the query returns an invalid-resource error and explicitly asks to query the same ID later, allow one more query at the permitted interval during that polling loop. Stop on a repeated error, rate limit, or other query failure.
- If refresh stops or fails, return the task number and the last confirmed status, such as submitted or processing, and explain that it could not be refreshed. Report the status as unknown only when no status was confirmed. A status refresh never creates another generation.

## Read-only operations

- Credits: call `query_membership_and_credits` once.
- Task status: call `query_tasks` once with a known `generationId`; do not start long-running polling for a direct status request.
- Model capabilities: call `who_am_i` without creating a task.
- Motion library: call `motion_library_list`; do not call `motion_control` merely to browse.
- Subject library: use `element_list` and `element_get` to resolve real subjects and resource types.

## State changes

- Create or update an Element only as requested, following the complete-resource rules in [asset workflows](asset-workflows.md).
- Delete an Element only when the user explicitly identifies the deletion target. A cover replacement that requires delete-and-recreate needs explicit authorization for the ID change.
- Call `logout` or switch accounts only when explicitly requested. Re-enter native Claude Code OAuth through `/mcp` and stop other Kling calls until authorization completes.

Never retry a generation automatically. For an ambiguous submission without a confirmed `generationId`, report unknown creation and billing state. Task-history or trace-ID lookup is unavailable.
