---
name: senderkit-mcp-messaging-operations
description: Send and operate transactional messages — email, SMS, push, or web-push — at runtime through the connected SenderKit MCP server. Use whenever the SenderKit MCP tools (senderkit_*) are available and a user wants to actually send a message (a test or live send, a welcome/OTP/notification message), check delivery or message status, debug a failed or stuck send, look up/draft/regenerate templates, filter recent messages, check scheduled sends, or cancel a scheduled or queued message — rather than editing application code (that is the senderkit-integration skill).
---

# SenderKit MCP messaging operations

Use this skill when SenderKit is connected as an MCP server and the user wants you to operate SenderKit through tool calls. The documented MCP surface is small and tool-only: ten tools, all prefixed with `senderkit_`.

This skill **operates SenderKit at runtime via MCP** and does not change application code. To add or wire SenderKit into a codebase (SDK/REST integration, migrating a provider), use the `senderkit-integration` skill instead.

## Source of truth and drift

The connected MCP server's advertised tool list is the runtime source of truth, not this document.

- The tool map below mirrors the published surface at `https://docs.senderkit.com/mcp/tools` (ten tools). Treat that page as canonical when the two disagree, and prefer the live tool list over both.
- If the connected server advertises an additional `senderkit_*` tool that is not listed here, you may use it after reading its tool schema. Do not assume a tool exists because it appears here; if a listed tool is absent at runtime, skip it and tell the user.
- Older or restricted servers may expose fewer tools (for example without the template-authoring tools). Confirm a tool is present before relying on it.

## Required workflow

1. Check context before acting.
   - Call `senderkit_context` before any send or cancellation.
   - Tell the user whether the active connection is `test` or `live`.
   - In `live` mode, do not send or cancel unless the user's request clearly authorizes that real-world action.

2. Prefer template sends.
   - Use `senderkit_send` when the user names or implies an existing template.
   - If the template slug is uncertain, call `senderkit_templates_list`.
   - Before sending with an unfamiliar slug, call `senderkit_templates_get` to inspect the template's channel, status, and published version.
   - Pass template variables in `vars` as a JSON object.
   - Use `version` only when the user asks to pin a specific template version or the workflow requires a known version.

3. Use raw sends narrowly.
   - Use `senderkit_send_raw` only for explicit one-off inline content.
   - For email raw sends, provide `subject` and `html`; include `text` when practical.
   - For SMS, push, and web-push raw sends, provide the channel-specific required body/title fields.
   - Set `interpolate: true` only when the user wants server-side variable substitution over the inline content.

4. Make sends traceable and retry-safe.
   - Include `idempotencyKey` for retryable sends, scheduled sends, or any send that might be repeated by an agent or job.
   - Use stable keys such as `<flow>/<entity-id>/<recipient-id>`.
   - Include scalar `metadata` values for later filtering, such as flow, internal entity ID, tenant/workspace ID, or reason.
   - Do not put secrets, message bodies, or unnecessary PII in metadata.

5. Inspect messages for status and debugging.
   - Use `senderkit_messages_list` for recent sends, filtered searches, failures, template-specific history, channel-specific history, or metadata lookups.
   - Use `senderkit_messages_get` when the user provides a message ID or when a list result needs full detail.
   - Explain that accepted sends are asynchronous; a returned message ID is not proof of delivery.
   - When reporting failures, include the status, relevant provider response or event timeline if returned, and the next concrete check.

6. Cancel only pending messages.
   - Call `senderkit_context` first.
   - Use `senderkit_messages_get` if the current status is unknown.
   - Use `senderkit_cancel_message` only for messages that are `scheduled` or `queued`.
   - If the status is later than queued, explain that delivery has already started or reached a terminal state and is not reversible through MCP.

## Authoring templates (drafts only)

`senderkit_templates_create` and `senderkit_templates_regenerate` author AI-composed templates. Both produce **drafts** — they never send and never publish.

- `senderkit_templates_create` - generate a new draft from a plain-language `brief` for a given `channel`. Required: `channel`, `brief`. Optional: `slug` (auto-derived from the brief if omitted; a numeric suffix is added on collision) and `description`. It returns a deep link to review the draft in the editor; the template is not usable for live sends until a human publishes it. May return `template_limit_reached` if the workspace template cap is hit.
- `senderkit_templates_regenerate` - replace a **draft's** content from a new `brief`. Required: `slug`, `brief`. This discards any manual edits made in the editor and only affects drafts (published templates are untouched). Confirm the slug is a draft with `senderkit_templates_get` first, and warn the user that manual edits will be lost before calling.
- After creating or regenerating, tell the user the draft must be reviewed and published in the dashboard before it can be sent — especially in `live` mode.

## Tool map

- `senderkit_context` - confirm workspace and `test` or `live` mode.
- `senderkit_send` - send a registered template to one recipient.
- `senderkit_send_raw` - send inline email, SMS, push, or web-push content to one recipient.
- `senderkit_templates_list` - discover available templates.
- `senderkit_templates_get` - inspect one template by slug.
- `senderkit_templates_create` - generate a new draft template from a brief (does not publish or send).
- `senderkit_templates_regenerate` - regenerate a draft template's content from a new brief (drafts only; discards manual edits).
- `senderkit_messages_list` - list and filter message history.
- `senderkit_messages_get` - inspect one message by ID.
- `senderkit_cancel_message` - cancel a still-pending scheduled or queued message.

## Boundaries

The surface can author **draft** templates (`senderkit_templates_create`, `senderkit_templates_regenerate`) but cannot publish them, edit a published version's content, or render templates over MCP — publishing and content editing happen in the dashboard. Do not claim MCP support for webhooks, suppressions, contacts, campaigns, analytics, provider setup, or domain configuration unless the active MCP server exposes tools for those operations.

When a user asks for an unsupported operation, explain the supported MCP alternatives: discover/inspect templates, draft a new template, send templated or raw messages, inspect message history, or cancel pending messages.

## Reference

Read `references/sources.md` when you need the canonical SenderKit MCP documentation links used to build this skill.
