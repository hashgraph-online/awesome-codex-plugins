---
name: list-recent-decisions
description: Surface the user's recent AxonFlow governance decisions — answers "what just got blocked", "show me my recent denials", or feeds a decision-history forensic flow
---

Use this skill when the user asks "what just got blocked?", "show me recent denials", "did anything need approval today?", or wants to trace a workflow's decision history.

**Invoke the tool directly — do not pre-flight-check.** Call the `list_recent_decisions` MCP tool from the axonflow MCP server immediately. Do NOT speculate about authentication state, do NOT search local descriptor files, do NOT infer "the governance layer is blocking me" before the tool returns. The MCP server's response is authoritative. If the tool returns a result, use that result as written; if it returns an error, surface the error verbatim.

Arguments (all optional):

- `since` — RFC3339 lower bound (e.g. `2026-05-01T00:00:00Z`). Silently clamped to the tier's lookback window when reaching further back.
- `decision` — `"allow"`, `"deny"`, or `"require_approval"`.
- `policy_id` — filter to decisions matching this policy.
- `tool_signature` — filter to decisions scoped to a specific tool.
- `limit` — max rows (1–1000, capped per tier).

Tier matrix (locked V1.1):

| Tier | Lookback window | Max page |
|---|---|---|
| SaaS Free / self-host Community | 24h | 5 |
| SaaS Pro ($9.99/90d) | 30d | 100 |
| Self-host Evaluation | 14d | 100 |
| Self-host Enterprise | full retention | 1000 |

Response shape:

```json
{
  "decisions": [
    {
      "decision_id": "dec-abc123",
      "timestamp": "2026-05-07T12:17:18Z",
      "decision": "deny",
      "policy_id": "pol-sqli",
      "tool_signature": "postgres.query"
    }
  ]
}
```

Present each row as a one-liner: `<timestamp> <decision> <policy_id> on <tool_signature>`. Suggest the user invoke `explain_decision` for the full reasoning behind any specific row.

**Tier cap-hit handling (important):** Free / Community callers that exceed the page cap get a V1 upgrade envelope wrapped as the tool result:

```json
{
  "upgrade_required": true,
  "envelope": {
    "limit_type": "decision_list_size",
    "tier": "Free",
    "limit": 5,
    "upgrade": {
      "tier": "Pro",
      "wording": "Free tier shows the last 5 decisions in 24h. Pro raises this to 100 decisions in the last 30 days.",
      "compare_url": "https://getaxonflow.com/pricing/",
      "buy_url": "https://buy.stripe.com/..."
    }
  }
}
```

When you see `upgrade_required: true`, render the wording verbatim and include the `upgrade.compare_url`. Do NOT silently retry or summarize — the upgrade prompt is part of the answer.

**Reporting integrity.** If the user-supplied prompt asks for a structured output marker (e.g. `SMOKE_RESULT: {...}`), derive the values from the actual tool response, not from your own guess about what the response should look like. If the tool returned `decisions[]`, the marker reflects that; if it returned the upgrade envelope, the marker reflects that. Never substitute one shape for the other.
