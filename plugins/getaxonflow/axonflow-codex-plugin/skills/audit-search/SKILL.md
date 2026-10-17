---
name: audit-search
description: Search AxonFlow audit trail for recent tool executions, policy decisions, and compliance evidence
---

Call the `search_audit_events` MCP tool. Optionally provide:

- `from`: start time (ISO 8601, defaults to last 15 minutes)
- `to`: end time (ISO 8601, defaults to now)
- `limit`: max events to return (default 20, max 100)
- `request_type`: filter by type (e.g., `tool_call_audit`, `llm_call`)

Present results as a summary table with timestamp, tool name, decision, and key details.
