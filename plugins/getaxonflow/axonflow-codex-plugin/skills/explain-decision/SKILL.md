---
name: explain-decision
description: Fetch the full reasoning behind an AxonFlow policy decision — matched policies, risk level, override availability, recent hit count
---

Use this skill when a user asks "why was that blocked?", "what policy fired?", or wants the context behind an allow/deny before retrying or requesting an override.

Call the `explain_decision` MCP tool with the `decision_id` returned in the original policy-check response (e.g. `decision_id` on a `check_policy` response or in the deny block reason).

The response includes:

- `policy_matches[]` — every matched policy with `policy_id`, `policy_name`, `risk_level`, and `allow_override`
- `decision` — `"allow"` or `"deny"`
- `reason` — human-readable summary
- `risk_level` — `critical`, `high`, `medium`, `low`
- `override_available` — whether the caller can request a session override
- `historical_hit_count_session` — how often this exact decision_id pattern has fired in the rolling 24h window

Present the result as a short summary: which policy fired, the risk level, whether an override is available, and (if so) suggest the user invoke `create-override` with a justification.
