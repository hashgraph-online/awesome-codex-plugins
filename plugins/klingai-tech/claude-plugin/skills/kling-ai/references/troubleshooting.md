# Claude Code troubleshooting

## MCP tools are missing

Use `/mcp` to verify that the plugin's `kling-ai` server is enabled and points to `https://kling.ai/mcp/plugin`. After changing plugin files, run `/reload-plugins`; if the tool definitions remain stale, restart the Claude Code session and check its MCP diagnostics. Do not add a duplicate server or use an API key as a workaround.

## Endpoint migration and authorization

This release uses the Global endpoint `https://kling.ai/mcp/plugin`. The previous `https://klingai.com/mcp` endpoint belongs to a different region. Before updating an existing connection, retain any outstanding task numbers and finish their status checks through the original connection. Disconnect the old host-managed OAuth session, update the plugin, then use `/mcp` to authorize the Global account. Never transfer credentials between hosts or assume that regional task history and credits are shared.

For an authorization failure, use `/mcp`, select the plugin's Kling server, and complete native OAuth. If sign-out or account switching was explicitly requested, call the live `logout` tool as documented and reauthorize before other Kling calls. Do not paste tokens, construct OAuth URLs manually, or add an `oauth_resource` override. `/reload-plugins` reloads plugin files; it does not refresh OAuth credentials.

OAuth discovery and client registration belong to the host. Do not require a custom client name or try to add one to generation arguments, headers, or the MCP URL. If the server rejects the host's registration, preserve the sanitized error for the service maintainer instead of guessing metadata or requesting credentials in chat.

## Upload or media reference fails

- Read the live `file_upload` schema and [asset workflow](asset-workflows.md).
- A ticket is only the first step. Complete the multipart upload with `ticket` and binary `file`, then use the confirmed media URL.
- Reuse the objective's `taskTraceId` where accepted. Never send local paths or expired signed URLs as remote media inputs.
- If upload is unavailable or fails, stop before dependent Element writes or generation. Do not silently switch to text-only generation or loop on upload requests.
- For an invalid-resource or signature error, compare the confirmed upload URL and the actual slot and reference against the [upload rules](asset-workflows.md#local-media-uploads). If the failure occurred during upload or local validation, correct the reference before the authorized first submission.
- When the provider says to retry with the same generation ID, query only the `generationId` confirmed for that submission. Use a source work's ID only to refresh that source. If the submission has no confirmed ID and its outcome is unclear, retain the `taskTraceId` and report creation and billing as unconfirmed.
- If diagnostics are available, compare the upload response, Claude Code tool arguments, and outbound MCP payload from the same attempt. Record only redacted summaries and query parameter names, and identify any missing observations. `ResourceNotFound` alone leaves the point of failure undetermined.

## Model capability mismatch

If the user says a requested model is enabled but it is absent, follow [capability discovery](capability-discovery.md): finish all tool-list pages, include `omni_ref_video` for video when present, and query remaining generation entry points before concluding the model was not returned. Check the actual connection, endpoint, and MCP version, then refresh discovery. Another client's results or website membership do not replace this connection's account-scoped capabilities.

If the mismatch remains, report that the current connection did not return the requested model and the cause needs investigation. Do not label it an account-permission failure without evidence, change accounts/endpoints, probe guessed model names through generation, or silently fall back to an older model. Keep diagnostics sanitized; omit credentials, private account fields, and signed URLs.

## Parameter or output setting rejected

- Compare the actual request's top-level `model`, required prompt and arguments, and required media slots with the live tool and selected model. Check whether `model` was omitted, null, empty, or whitespace-only. Verify exact slot names, such as `image_1` or `first_image` where declared. If field handling is unclear, compare available Claude Code tool arguments and MCP request diagnostics against the same tool schema's `required` list.
- For a resolution rejection, including on Flash models, compare the submitted value against the live enum and conditions for the same account, tool, and model. If they agree and the service still rejects the request, retain the trace ID and sanitized values for the maintainer. If the requested setting is unsupported, let the user choose an available setting before a new submission.

## Element or motion cannot be used

- Resolve ambiguous names before selecting an ID. Use `element_get` to inspect the resource type and access before reuse or updates.
- Use Elements only with live models declaring both the resource type and binding argument, including conditional caps. Preserve required image inputs and use the model's prompt and structured bindings; entry point names alone do not establish support.
- Keep the existing cover and unmodified secondary images when updating an image Element. Do not change its resource type or delete-and-recreate without explicit authorization.
- Motion control requires a subject image and exactly one source: `motionId` or a video input. A library preview URL is not a motion ID. Validate source duration and model arguments; do not invent a `duration` parameter.
- An empty motion library is a valid result. The current tool surface has no motion create, update, or delete operation.

## Task is still running or the result App does not render

Follow [task status refresh](tool-workflows.md#task-status-refresh) for App and headless behavior. When the user reports a missing video, query the original video task once. If the query fails, report the task number and the last confirmed state.

For a rendering problem, preserve the tool result and follow the [core Skill's result rules](../SKILL.md#generation-and-results) for the text fallback and links. Do not register a local MCP server, embed duplicate media, or claim that an unmounted App was displayed.

## Submission fails or times out

If a `generationId` is known, query it once. If an ambiguous submission has no confirmed `generationId`, report creation and billing as unknown. Keep the `taskTraceId` for troubleshooting. Any new generation after an attempted submission needs fresh explicit authorization.

For a provider failure, return the sanitized message and preserve task IDs. Treat a generic service-unavailable message as a service error even if the outer code is `InvalidParameter`. Use parameter troubleshooting when the response identifies a specific rejected field.

## Rate limit or queue full

For a full generation queue, retain the original settings and any confirmed task number. Report whether the service queued the request, rejected it, or left its state unconfirmed. If the user asks to continue, check any known original task first. If the service confirmed that it created no task and charged no credits, follow the [approved generation workflow](tool-workflows.md#generation) for a new attempt. A rate-limited status refresh ends the current polling loop. Return the task number and last confirmed status.

## Insufficient credits

Use the current `query_membership_and_credits` balance and any live cost estimate for the same settings. State whether the balance check stopped the request, the service rejected it, or the submission outcome is unconfirmed. Follow [resuming after insufficient credits](tool-workflows.md#resuming-after-insufficient-credits) for recharge and continuation.

## Result link expired

Query the original `generationId` for current outputs immediately before reuse. Do not treat signed URLs as permanent asset identifiers or log them. If the task cannot be queried in the current region, explain the limitation rather than creating a replacement task.
