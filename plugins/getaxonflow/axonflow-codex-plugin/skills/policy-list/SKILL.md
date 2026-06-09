---
name: policy-list
description: List all active governance policies with categories, patterns, and severity levels
---

Call the `list_policies` MCP tool. Optionally filter by:

- `category`: policy category (e.g., `security-dangerous`, `pii-us`)
- `severity`: minimum severity (`critical`, `high`, `medium`, `low`)

Present the policies grouped by category with name, severity, and what they protect against.
