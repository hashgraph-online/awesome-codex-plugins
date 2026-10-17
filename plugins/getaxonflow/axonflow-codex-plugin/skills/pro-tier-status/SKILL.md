---
name: pro-tier-status
description: Report the user's current AxonFlow tier (Free or Pro), Pro license expiry date, endpoint, and whether a license token is configured. Use when the user asks "am I on Pro?", "what tier am I on?", "when does my Pro license expire?", "is my license active?", or wants to know which AxonFlow they're talking to.
---

The Codex plugin runs in one of two tiers:

- **Free.** No `AXONFLOW_LICENSE_TOKEN` env var and no `license_token = "..."` line in `~/.codex/axonflow.toml` (or the line is there but its JWT `exp` is in the past — the plugin will not forward an expired token). The plugin omits the `X-License-Token` HTTP header on every governed request, and the agent applies free-tier quota / retention defaults.
- **Pro tier active.** Either `AXONFLOW_LICENSE_TOKEN` is exported in the Codex environment (operator override; CI use) or `~/.codex/axonflow.toml` contains a `license_token = "AXON-..."` line whose JWT `exp` is in the future. The plugin sends `X-License-Token: <token>` on every governed request, and the agent's `PluginClaimMiddleware` validates the Ed25519 signature + DB row, then stamps a Pro-tier context on the request.

Invoke the status surface in one of two ways:

1. **Prefer the local script — it answers without an agent round-trip.** `scripts/recover.sh status` reads `tenant_id` and tier directly from the plugin's persisted state (`~/.config/axonflow/try-registration.json`, the configured license token's JWT `exp` claim). No HTTP call to the agent. Faster, works offline, and works exactly when the user typically asks this question — while debugging the Stripe Checkout flow, when the agent isn't reachable yet, or when they just want a quick read on which tenant they're on. Tell the user: "I'll run `scripts/recover.sh status` to print your tenant_id, tier, and Pro license expiry locally — no agent round-trip." Invoke via `exec_command`:

```bash
bash $PLUGIN_DIR/scripts/recover.sh status
```

2. **Use the MCP tool only when the user explicitly wants server-truth.** The AxonFlow agent exposes `axonflow_get_tenant_id` via the `axonflow` MCP server (auto-discovered by Codex when `axonflow` is configured in `~/.codex/config.toml` MCP servers). It returns the same shape but resolved server-side, which catches edge cases the local script can't: a Pro license revoked by the platform, clock skew on JWT `exp`, or a server-side tier override. Use it when the user asks something like "is my Pro license still valid on the server" or "the agent is rejecting me, what does the agent see for me?". In all other cases the local script is sufficient and cheaper.

## Related agent-callable tools

When the AxonFlow MCP server is available, Codex can answer related questions directly via tool calls without spawning shell scripts:

- `axonflow_get_tenant_id` — tenant identity + tier + upgrade URLs.
- `axonflow_list_pro_features` — locked V1 Pro feature list (5 differentiators + $9.99 / 90 days pricing). Useful when the user asks "what would I get if I upgraded?".
- `axonflow_request_approval` — file a HITL approval request before a risky operation (Free tier: 1 per rolling 7d; Pro: unlimited).
- `axonflow_create_tenant_policy` — create a custom tenant policy (Free tier: 2 active max; Pro: unlimited).
- `axonflow_get_cost_estimate` — pre-flight LLM cost for a multi-step plan. Pro-only — the tool isn't visible to Free callers.

Prefer these tools over equivalent shell scripts when both exist; they are auth-context-aware on the server side and don't require local shell state.

## Tier line shape

The script's `tier` line takes one of three shapes — surface whichever one the user got:

- `tier   Pro tier active (expires 2026-08-03, 90 days remaining)` — paid Pro tier active.
- `tier   Pro tier active (expires UNKNOWN — could not parse token)` — token configured but the JWT body did not parse. Treat as Pro for display; the platform is the source of truth on validity.
- `tier   Free tier (Pro expired 2026-02-04 — visit https://getaxonflow.com/pricing/ to renew)` — token is on disk but its `exp` has passed. The plugin will not forward an expired token; the user must buy a renewal and replace the token via `AXONFLOW_LICENSE_TOKEN=<new>` or `scripts/recover.sh apply-token`.
- `tier   Free tier (no AXON- license token configured)` — no token loaded.

When the user lands on `Free tier (Pro expired …)`, point them at the renew URL embedded in the line and the `scripts/recover.sh apply-token` hint the script prints below.

## Other lines the script reports

- the active endpoint (`AXONFLOW_ENDPOINT` or the community-saas default)
- whether `~/.codex/axonflow.toml` exists
- the user's `tenant_id` (read from `~/.config/axonflow/try-registration.json`) — needed to paste into the Stripe checkout custom field at /pro
- a redacted preview of the configured license token (`set (AXON-...XXXX)` — last 4 chars only, never the full bearer credential)

## Renewal + upgrade path

If the user is on Free and asks about upgrading, tell them: a Pro license token arrives by email after Stripe Checkout completes, and they install it with `scripts/recover.sh apply-token` (or by setting `AXONFLOW_LICENSE_TOKEN`). Don't paste the token into chat — the script reads from stdin or env.

For richer governance activity (policy hits, override usage, audit volume), point the user to the `governance-status` skill, which calls the platform's `get_policy_stats` MCP tool.

The script extracts the JWT `exp` claim for display only; signature validation is the platform's job.
