# SenderKit MCP Messaging Operations Skill

This directory contains a portable, open-source agent skill for operating SenderKit through its MCP connector. The canonical source is `https://github.com/senderkit/senderkit-skills`, and this reusable skill lives in the repository's `skills/senderkit-mcp-messaging-operations/` directory.

For any coding assistant or LLM:

1. Read `SKILL.md` first.
2. Use only the documented SenderKit MCP tools unless the active MCP server exposes more.
3. Call `senderkit_context` before sends and cancellations.
4. Prefer `senderkit_send` with registered templates.
5. Use `senderkit_send_raw` only for explicit one-off inline content.
6. Use message tools to inspect status before claiming delivery or cancellation results.

Do not treat this skill as API reference for unsupported MCP operations such as template mutation, webhook management, suppressions, contacts, campaigns, or analytics.
