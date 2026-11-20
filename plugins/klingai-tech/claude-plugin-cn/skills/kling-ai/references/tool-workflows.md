# Remote tool workflows

## Generation

1. Use the plugin's single `kling-ai` connection at `https://klingai.com/mcp/plugin` and follow [capability discovery](capability-discovery.md), including all tool-list pages and relevant new entry points.
2. Create or reuse the objective's UUIDv7 `taskTraceId`, reuse the successful `who_am_i` response for this preparation, and apply [model parameters](model-parameters.md) to the selected tool/model pair. Video selection follows [video routing](../../kling-ai-generate-video/references/model-routing.md), including `omni_ref_video` when available. Refresh capability data when invalidated, not just because another reference was loaded.
3. For Elements, motion-library selections, or local media, follow [asset workflows](asset-workflows.md). A library operation does not authorize generation. Do not silently fall back to text-only generation if a required reference is unavailable.
4. Show the final mode, model, prompt summary, resolution, duration when applicable, aspect ratio, output count, and reference roles. Include live-required billing disclosures, including per-second billing and input video duration when applicable. Describe shot controls only as declared by the model, without inferring the actual number of cuts. Obtain explicit approval under the core Skill's billing rule.
5. Validate the request against the [MCP contract](mcp-contract.md), including the top-level `model` and all required arguments and media slots.
6. Immediately before submitting, call `query_membership_and_credits` on the same connection. Pause if the balance is unavailable, nonpositive, or explicitly insufficient, including when the live estimate for these settings exceeds the balance. Keep the prepared request even if the upload already succeeded. A positive balance alone does not confirm affordability when the cost is unknown. Never submit to probe the balance.
7. Call the selected generation tool once using its live schema. Preserve `generationId` and follow the core Skill's [generation and results](../SKILL.md#generation-and-results). Keep at most one active generation for the same objective. For dependent steps, wait for terminal success and a usable source result before continuing.

## Resuming a paused generation

1. Keep the original intent, tool, canonical model ID, prompt, settings, reference roles and usable references, `taskTraceId`, submission state, and known `generationId` in the current conversation. If credits are insufficient, explain whether submission was prevented, rejected, or remains unconfirmed. Report a credit shortfall only when the live service provides a cost for the same settings.
2. For insufficient credits, share the official top-up entry returned for the current region when available. Otherwise direct the user to sign into the same China account on the [Kling AI website](https://klingai.com/app) and open the top-up page from the account. The user completes the purchase and can return to the same conversation with “Continue the previous generation.” A message that only says the user topped up can trigger a balance check.
3. On an explicit request to continue, identify the original task. If more than one task matches, ask which one. If that submission returned a `generationId`, query it before checking credits or preparing another submission and report its state or results. Resume submission only if no generation call was sent or the service confirmed that it created no task and charged no credits. If submission remains ambiguous, report the unknown state and stop.
4. Before submitting, use the same account and check that the original model, settings, and references are still valid. Reuse valid references and refresh expired ones from the original media where possible. Ask for replacement media only if the original cannot be recovered. Apply the core approval rule if the billable settings change. If a previous attempt was rejected, an explicit request to continue with the previously approved settings provides fresh authorization for that attempt. Recheck the balance immediately before the single submission and preserve the original trace ID.

## Read-only operations

- Credits: call `query_membership_and_credits` once.
- Task status: call `query_tasks` once with a known `generationId`; do not start long-running polling for a direct status request.
- Model capabilities: call `who_am_i` without creating a task.
- Motion library: call `motion_library_list`; do not call `motion_control` merely to browse.
- Subject library: use `element_list` and `element_get` to resolve real subjects and resource types.

## State changes

- Create or update an Element only as requested, following the complete-resource rules in [asset workflows](asset-workflows.md).
- Delete an Element only when the user explicitly identifies the deletion target. A cover replacement that requires delete-and-recreate needs explicit authorization for the ID change.
- Call `logout` or switch accounts only when explicitly requested. Reauthorize through the client's native MCP OAuth flow and stop other Kling calls until authorization completes.

Never retry a generation automatically. If a submission is ambiguous and no `generationId` was received, report unknown creation and billing state. Task queries require a real task number. An unchanged balance or a missing history entry does not resolve an ambiguous submission.
