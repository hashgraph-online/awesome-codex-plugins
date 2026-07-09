---
name: runtype-admin
description: >-
  Use when operating a live Runtype account through MCP or Code Mode MCP: inspect resources,
  debug failed flows or agents, read logs and traces, manage products, surfaces, records,
  schedules, secrets, models, evals, batches, conversations, client tokens, or make safe
  account mutations. Includes search/execute patterns, read-before-write, validation,
  pagination, and conservative destructive-change policy.
user-invocable: true
argument-hint: '[live account operation or debugging task]'
---

# Runtype Admin

Use this skill for live account operations. All mutations affect the user's Runtype
workspace unless explicitly run against a disposable test account.

## Operating Stance

- Reads can proceed after discovering the target.
- Single-resource writes the user explicitly requested can proceed after reading current
  state and validating payloads.
- Multi-resource builds should use `runtype-build-product`.
- Destructive, bulk, or hard-to-reverse actions require explicit confirmation.
- Never claim a mutation succeeded unless the tool result confirms it.
- Never show secret values. Use metadata only.

## Standard MCP

For direct MCP tools, discover before acting:

- Identity and inventory: `get_me`, `list_products`, `list_agents`, `list_flows`,
  `list_tools`, `list_records`, `list_schedules`, `list_secrets`,
  `list_model_configs`, `list_conversations`.
- Debugging: `list_logs`, `get_log_stats`, `trace_execution`, `trace_conversation`,
  `list_agent_executions`, `get_record_results`, `get_record_step_results`,
  `get_record_costs`.
- Validation: `validate_flow`, `validate_code`, `validate_product`,
  `validate_product_flow`, `validate_product_agent`, `validate_product_surface`,
  `validate_product_tool`.
- Evals and batches: `submit_eval`, `list_eval_batches`, `get_eval_results`,
  `compare_eval`, `compare_eval_record`, `analyze_eval_steps`, `submit_batch`,
  `get_batch_status`, `get_batch_summary`, `cancel_batch`.

Surfaces are product-scoped. List or mutate them with the product id in hand.

## Code Mode MCP

Code Mode MCP exposes `search`, `execute`, `get_platform_documentation`,
`get_build_instructions`, `generate_persona_embed_code`, and
`get_persona_theme_reference`.

Use `search` first when unsure:

```js
;(spec) => spec.categories
```

Then inspect one method:

```js
;(spec) => spec.methods.updateAgent
```

Use `execute` with shaped results. Filter, project, slice, and aggregate inside the
function before returning data so large responses do not consume context:

```js
;async (runtype) => {
  const products = await runtype.listProducts()
  return products.products.map((p) => ({ id: p.id, name: p.name })).slice(0, 20)
}
```

## Debugging Flow

1. Identify the failing execution, conversation, batch, eval, schedule run, or record.
2. Pull the narrow trace first: `trace_execution` or `trace_conversation`.
3. Use `list_logs` only after the trace, filtering by execution id, conversation id,
   level, status, category, or time window.
4. Inspect the referenced flow, agent, surface, tools, and secrets.
5. Validate the corrected payload.
6. Apply the smallest change and re-run the same scenario.

Common causes: missing secret, wrong secret reference syntax, unresolved template variable,
tool schema mismatch, wrong surface behavior config, model timeout, or a flow that should
be an agent.

## Update Rules

- Read current config before update.
- Preserve fields unrelated to the request.
- Validate before update when validators exist.
- Respect pagination cursors on list endpoints.
- When a payload shape, route, or dashboard URL is uncertain, use Code Mode
  `search` or `get_platform_documentation(topic="platform-catalog")` before guessing.
- Use `get_platform_documentation(topic="dashboard-links")` when giving the user links.
- Use `get_secret_intake_manifest`, `submit_secret_intake`, and `check_secrets` rather
  than asking the model to handle credential values.

If the umbrella `runtype` skill is installed alongside this focused skill, its durable
references provide deeper fallback notes. This skill must still work when installed by
itself; prefer live MCP docs over local sibling files.
