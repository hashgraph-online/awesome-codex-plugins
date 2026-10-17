---
name: create-override
description: Create a governed session override for a policy that would otherwise deny — mandatory justification, server-clamped TTL, blocked for critical-risk policies
---

Use this skill when a user has been blocked by a non-critical policy and wants to bypass it for the rest of their session with a documented justification.

Before calling this skill, the user MUST provide:

1. **`policy_id`** — the ID of the policy to override (typically surfaced by `explain-decision`)
2. **`policy_type`** — `"static"` (system / dynamic registry policy) or `"dynamic"`
3. **`override_reason`** — free-text justification (1-500 chars). This is mandatory and recorded in the audit trail.

Optional:

- `tool_signature` — restrict the override to a specific tool name (recommended; narrower scope)
- `ttl_seconds` — requested duration. Server clamps to `[60, 86400]`; default 3600 (1h).

Call the `create_override` MCP tool. The platform will reject the request (HTTP 403) when:

- The policy is critical-risk (no override permitted)
- The policy has `allow_override: false`
- The justification is missing or empty

Surface the response's `id`, `expires_at`, and any `clamped` flag (set when the requested TTL was clamped down). Tell the user: "Override `<id>` active until `<expires_at>` — the next attempt at the blocked tool will succeed within that window."
