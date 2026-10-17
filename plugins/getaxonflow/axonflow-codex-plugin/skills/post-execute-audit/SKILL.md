---
name: post-execute-audit
description: Record tool execution in AxonFlow audit trail after tool calls complete. Use after any tool call for compliance evidence.
---

After tool calls complete, call the `audit_tool_call` MCP tool with:

- `tool_name`: the tool that was called (e.g., "Bash", "Write")
- `input`: the tool input (command, file content, etc.)
- `success`: whether the tool call succeeded
- `output`: summary of the result (truncate if large)

This creates a compliance-grade audit record with timestamp, policy context, and execution details.

Note: For Bash tool calls, this is handled automatically by the PostToolUse hook. Use this skill for other tool types that are not hook-governed.
