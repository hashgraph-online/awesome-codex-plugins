---
name: pre-execute-check
description: Check AxonFlow governance policy before executing commands, writing files, or modifying any state. Also scan file content for PII before writing. Use before any tool call that creates, modifies, or deletes data.
---

Before using tools that modify state (terminal commands, file writes, file edits, MCP operations):

**Step 1: Check policy**

Call the `check_policy` MCP tool with:
- `connector_type`: `codex.Bash` (for commands), `codex.Write` (for file writes), or the appropriate tool type
- `statement`: the command or content to check
- `operation`: `execute`

If the response shows `allowed: false`, do NOT proceed. Report the block reason to the user.

**Step 2: For file writes — also scan content for PII**

If you are writing a file and the content might contain sensitive data (names, SSNs, credit cards, emails, phone numbers, addresses, medical records, financial data), call the `check_output` MCP tool with:
- `connector_type`: `codex.Write`
- `message`: the content being written

If a `redacted_message` is returned, write the redacted version instead. If `allowed: false`, do not write the file.

These checks take 2-5ms and protect against dangerous commands, SQL injection, credential access, SSRF, path traversal, and PII exposure.
