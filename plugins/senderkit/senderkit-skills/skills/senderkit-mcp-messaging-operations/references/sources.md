# Source notes

This skill was built from:

- SenderKit open-source skills repository: `https://github.com/senderkit/senderkit-skills`
  - Reusable MCP messaging operations skill folder: `skills/senderkit-mcp-messaging-operations/`
  - License: MIT.
- SenderKit MCP overview: `https://docs.senderkit.com/mcp/overview`
  - Describes SenderKit MCP as a way for AI assistants to send notifications, inspect templates, inspect messages, and check connection mode.
  - Documents OAuth, hosted API-key, and local stdio connection modes.
- SenderKit MCP tools: `https://docs.senderkit.com/mcp/tools`
  - Documents the ten-tool MCP surface:
    - `senderkit_context`
    - `senderkit_send`
    - `senderkit_send_raw`
    - `senderkit_templates_list`
    - `senderkit_templates_get`
    - `senderkit_templates_create`
    - `senderkit_templates_regenerate`
    - `senderkit_messages_list`
    - `senderkit_messages_get`
    - `senderkit_cancel_message`
  - Template authoring tools produce drafts only (no publish/send); `regenerate` replaces a draft and discards manual edits.
  - Notes that no MCP prompts or resources are exposed.
- SenderKit docs index: `https://docs.senderkit.com/llms.txt`
  - Lists related REST API, CLI, concepts, guides, SDK, MCP, and webhook documentation.

Prefer the current SenderKit MCP docs over this source note when they differ.
