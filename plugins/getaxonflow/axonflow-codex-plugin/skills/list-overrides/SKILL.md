---
name: list-overrides
description: List active session overrides scoped to the caller's tenant — useful for auditing dangling overrides or confirming an override is in effect before retrying
---

Use this skill to inventory active session overrides — for example, before asking the user "should we keep that override active?", or to confirm an override is still in effect before retrying a previously-blocked tool call.

Call the `list_overrides` MCP tool. Optional filters:

- `policy_id` — restrict to overrides for a specific policy
- `include_revoked` — include already-revoked overrides (default: false)

The response is `{ overrides: [...], count: <int> }` where each override carries `id`, `policy_id`, `expires_at`, `created_at`, and the original justification.

Present results as a short table: ID, policy, expires-at, justification. Flag any override whose `expires_at` is more than 12 hours away as "long-lived — consider revoking when the work that needed it is done".
