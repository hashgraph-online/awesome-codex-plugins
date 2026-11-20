# Kling AI troubleshooting

## MCP tools are missing

Use the client's MCP controls to verify that the plugin's `kling-ai` server is enabled and points to `https://klingai.com/mcp/plugin`. In Claude Code, use `/mcp` to check the connection and `/reload-plugins` after changing plugin files. If tool definitions remain stale, restart the session and check the client's MCP diagnostics. Do not add a duplicate server or use an API key as a workaround.

## Endpoint migration and authorization

This release uses the China endpoint `https://klingai.com/mcp/plugin`. When switching from another region, retain any outstanding task numbers and finish their status checks through the original connection. Disconnect the old host-managed OAuth session, update the plugin, then use the client's native MCP OAuth flow to authorize the China account. Never transfer credentials between hosts or assume that regional task history and credits are shared.

For an authorization failure, select the plugin's Kling server in the client's MCP controls and complete native OAuth. If sign-out or account switching was explicitly requested, call the live `logout` tool as documented and reauthorize before other Kling calls. Do not paste tokens, construct OAuth URLs manually, or add an `oauth_resource` override. In Claude Code, `/reload-plugins` reloads plugin files; it does not refresh OAuth credentials.

OAuth discovery and client registration belong to the host. Do not require a custom client name or try to add one to generation arguments, headers, or the MCP URL. If the server rejects the host's registration, preserve the sanitized error for the service maintainer instead of guessing metadata or requesting credentials in chat.

## Upload or media reference fails

- Read the live `file_upload` schema and [asset workflow](asset-workflows.md).
- A ticket is only the first step. Complete the multipart upload with `ticket` and binary `file`, then use the confirmed media URL.
- Reuse the objective's `taskTraceId` where accepted. Never send local paths or expired signed URLs as remote media inputs.
- If upload is unavailable or fails, stop before dependent Element writes or generation. Do not silently switch to text-only generation or loop on upload requests.
- For invalid media or a signature error, verify the full URL from the successful upload response and the exact input slot. If the problem occurred before any generation call, fix the reference and complete the approved first submission.
- If the service says to retry with the same generation ID, query only a `generationId` confirmed for this submission. An upload ID, source work ID, or ID from another step cannot identify this task. If the submission did not yield a confirmed ID, report that creation and billing are unconfirmed, retain `taskTraceId`, and pause.
- When diagnosing a changed URL, compare the upload response, the reference provided to the model, the tool-call arguments, and the actual outbound MCP request where available. Record only redacted URL summaries and query parameter names, and identify any missing evidence. A resource error alone does not identify where the URL changed.

## Parameter or resolution rejected

- Check the submitted top-level `model` for omission, null, empty, or whitespace-only values. Compare the required `arguments[]`, including `prompt` when required, and the exact required `inputs[]` slots against the selected model. For example, `image_1` and `first_image` are separate slots.
- For a resolution rejection, including on image-to-video Flash models, refresh `who_am_i` and compare the actual submitted value with the field, enum, and applicable conditions for the same account, connection, tool, and model. If the value matches and is still rejected, retain the trace ID and sanitized fields for the service maintainer. Ask the user to choose if their requested specification is unavailable.
- To locate a missing or changed field, compare the model's tool-call arguments with the client's outbound MCP arguments and the same turn's schema `required` list where available. Preserve the original prompt, mode, and reference roles. Correct the rejected field only and follow the core approval rule before any new submission.

## Model capability mismatch

If the user says a requested model is enabled but it is absent, follow [capability discovery](capability-discovery.md): finish all tool-list pages, include `omni_ref_video` for video when present, and query remaining generation entry points before concluding the model was not returned. Check the actual connection, endpoint, and MCP version, then refresh discovery. Another client's results or website membership do not replace this connection's account-scoped capabilities.

If the mismatch remains, report that the current connection did not return the requested model and the cause needs investigation. Do not label it an account-permission failure without evidence, change accounts/endpoints, probe guessed model names through generation, or silently fall back to an older model. Keep diagnostics sanitized; omit credentials, private account fields, and signed URLs.

## Element or motion cannot be used

- Resolve ambiguous names before selecting an ID. Use `element_get` to inspect the resource type and access before reuse or updates.
- Use Elements only with live models declaring both the resource type and binding argument, including conditional caps. Preserve required image inputs and use the model's prompt and structured bindings; entry point names alone do not establish support.
- Keep the existing cover and unmodified secondary images when updating an image Element. Do not change its resource type or delete-and-recreate without explicit authorization.
- Motion control requires a subject image and exactly one source: `motionId` or a video input. A library preview URL is not a motion ID. Validate source duration and model arguments; do not invent a `duration` parameter.
- An empty motion library is a valid result. The current tool surface has no motion create, update, or delete operation.

## Task is still running or the result App does not render

Follow [generation and results](../SKILL.md#generation-and-results) for App refresh and headless queries. If the user says a video or image did not appear, query the known task once. If refresh fails, report the task number and its last confirmed state.

Preserve the tool result and follow the [generation and results rules](../SKILL.md#generation-and-results) for the text fallback, usable result links, and completion status. Keep the same task number when the App fails to render.

## Submission fails or times out

Do not retry generation automatically. If a `generationId` is known, query it once. If no task number is known and the service did not confirm whether it created a task or charged credits, report the unknown state and keep the trace ID for troubleshooting. The current MCP cannot find a task by `taskTraceId`. Any new attempt needs fresh explicit authorization.

For a provider failure, return the sanitized message and preserve task IDs. Treat a generic “service temporarily unavailable” message as a service error even if its outer code is `InvalidParameter`. Use parameter troubleshooting when the response identifies a field.

## Insufficient credits, queue full, or rate limited

- For insufficient credits, use the current balance from `query_membership_and_credits` and the service response. Monthly plan credits do not establish the balance. Follow [resuming a paused generation](tool-workflows.md#resuming-a-paused-generation) and report the actual submission state.
- For a full generation queue, retain the request settings and known task number. Report whether the request was rejected, queued, or remains unconfirmed based on the service response. Follow the same resume workflow if the user asks to continue.
- If a status query is rate limited, stop querying this turn and report the last confirmed state and task number.

## Result link expired

Query the original `generationId` for current outputs immediately before reuse. Do not treat signed URLs as permanent asset identifiers or log them. If the task cannot be queried in the current region, explain the limitation rather than creating a replacement task.
