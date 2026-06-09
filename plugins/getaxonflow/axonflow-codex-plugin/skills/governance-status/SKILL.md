---
name: governance-status
description: Check active governance policies and recent activity summary
---

Call the `get_policy_stats` MCP tool to see governance activity. Optionally provide:

- `from`: start date (ISO 8601)
- `to`: end date (ISO 8601)
- `connector_type`: filter by tool type

Present the results showing total events, compliance score, and triggered policies.
