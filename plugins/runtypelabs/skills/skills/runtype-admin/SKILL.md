---
name: runtype-admin
description: 'Inspect, debug, or manage a live Runtype account through MCP or CLI; mutate only within the requested scope.'
user-invocable: true
argument-hint: '[live account operation or debugging task]'
---

# Runtype Admin

Use this skill for live account operations. Every mutation changes the user's Runtype
workspace unless you run it against a disposable test account.

## Before you start

Runtype has two hosted MCP servers. Both accept browser sign-in on the first call, or a
Runtype API key sent as `Authorization: Bearer <key>`.

| Server        | URL                                       | Tools                                                                                                                                                             |
| ------------- | ----------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Standard MCP  | `https://api.runtype.com/v1/mcp/protocol` | One named tool per operation, such as `get_me`, `list_agents`, and `list_runs`                                                                                    |
| Code Mode MCP | `https://code.runtype.com/mcp`            | `search`, `execute`, `get_platform_documentation`, `search_documentation`, `get_build_instructions`, `generate_persona_embed_code`, `get_persona_theme_reference` |

To check which server is connected, look at the tool list. Code Mode lists only the seven
tools in the table. Call `get_me` (on Code Mode, `execute` with
`async (runtype) => runtype.getMe()`) to confirm the organization before you change anything.

## Operating rules

- Read freely once you have identified the resource ID with a `list_*` or `get_*` call.
- Write to a single resource only when the user asked for that change. Follow
  [Update resources safely](#update-resources-safely).
- Use the `runtype-build-product` skill for builds that span several resources.
- Get explicit confirmation before destructive, bulk, or hard-to-reverse actions. When you
  ask, state what else is removed and offer the reversible alternative:
  - `delete_product` removes the product's surfaces, surface items, and surface keys. It
    keeps the flows and agents.
  - `bulk_delete_records` and `delete_conversation` are irreversible.
  - `delete_schedule` also deletes the schedule's run history. Use `pause_schedule` instead.
  - `delete_messaging_conversation` deletes the transcript. Close the thread with
    `update_messaging_conversation` instead.
- Never claim a mutation succeeded unless the tool result confirms it.
- Never show secret values. Use metadata only.

## Standard MCP tools

Discover before you act:

- Identity and inventory: `get_me`, `list_products`, `list_agents`, `list_flows`,
  `list_tools`, `list_records`, `list_collections`, `list_skills`, `list_schedules`,
  `list_secrets`, `list_conversations`, `list_model_configs`, `list_model_configs_grouped`,
  `list_provider_keys`.
- Debugging: `list_runs`, `trace_execution`, `trace_conversation`, `list_logs`,
  `get_log_stats`, `list_schedule_runs`, `get_record_results`, `get_record_step_results`,
  `get_record_costs`.
- Validation: `validate_flow`, `validate_code`, `validate_product`,
  `validate_product_flow`, `validate_product_agent`, `validate_product_surface`,
  `validate_product_tool`.
- Test runs: `execute_agent`, `run_flow`.
- Evals and batches: `create_eval_suite`, `run_eval_suite`, `add_eval_cases`,
  `add_eval_case_from_execution`, `submit_eval`, `list_eval_batches`, `get_eval_results`,
  `compare_eval`, `compare_eval_record`, `analyze_eval_steps`, `submit_batch`,
  `get_batch_status`, `get_batch_summary`, `cancel_batch`.
- Versions and releases: `list_flow_versions`, `get_published_flow_version`,
  `publish_flow_version`, `list_agent_versions`, `get_published_agent_version`,
  `publish_agent_version`, `list_agent_aliases`, `rollback_agent_alias`,
  `list_agent_deployments`.

Surfaces belong to a product. List or change them with the product ID in hand.

Use `list_model_configs` to see which models the account can run. `list_available_models`
is the platform catalog: its `isEnabled` and `isDefault` fields are always null or false,
so it cannot tell you whether a model is enabled.

Large inventories (`list_products`, `list_agents`, `list_flows`, `list_tools`,
`list_records`, `list_collections`, `list_skills`, and `list_schedules`) return compact
string previews by default. Use that shape to find the resource, then call the matching
`get_*` tool. Pass `view: "full"` only when you need complete strings across the whole
page. `list_agents` also accepts `agent_type` (`runtype`, `external`, or
`claude_managed`) when you know the type.

## Code Mode MCP

Call `search` first when you are unsure which method to use:

<!-- prettier-ignore -->
```js
(spec) => spec.categories
```

Then inspect one method:

<!-- prettier-ignore -->
```js
(spec) => spec.methods.updateAgent
```

Call `execute` and shape the result inside the function. Filter, project, and aggregate
before you return data, so large responses do not fill the context:

<!-- prettier-ignore -->
```js
async (runtype) => {
  const { data } = await runtype.listProducts({ limit: 20 })
  return data.map((p) => ({ id: p.id, name: p.name }))
}
```

Pass an arrow function with one parameter, such as `async (runtype) => ...`. Do not add a
leading semicolon: the call fails with a syntax or validation error.

## Use the CLI

Sign in with `runtype auth login`, or set `RUNTYPE_API_KEY`. The CLI calls either MCP
server directly:

```bash
runtype mcp tools
runtype mcp call list_runs -F limit=20 --json
runtype mcp call execute --server code -F code=@query.js --json
```

Use `-f key=value` for string values and `-F key=value` for JSON values. For log reads,
`runtype logs list` and `runtype logs stats` take the same filters as `list_logs`, such as
`--execution`, `--agent`, `--status`, and `--from`.

## Debug a failed run

1. Find the run with `list_runs`. Filter by `agent_id`, `flow_id`, `conversation_id`,
   `surface_id`, `record_id`, or `batch_execution_id`, and pass `status: "failed"`.
   Subagent and nested-flow runs fold under their parent in the unfiltered list. Pass
   `include_children` to list them flat. `list_runs` covers the last 24 hours unless you pass `from`. For a schedule, start
   with `list_schedule_runs`.
2. Pull the trace for that run: `trace_execution`, or `trace_conversation` for a
   multi-turn conversation.
3. Use `list_logs` after the trace. Filter by execution ID, conversation ID, level, status,
   or category. `list_logs` and `get_log_stats` search only the last 24 hours unless you
   pass `from` or `minutes_ago`. An empty result says nothing about older runs.
4. Inspect the referenced flow, agent, surface, tools, and secrets.
5. Validate the corrected payload.
6. Apply the smallest change. Re-run the same input with `execute_agent` or `run_flow`,
   then capture the case with `add_eval_case_from_execution` or `add_eval_cases`.

Common causes:

- A missing secret. Check with `check_secrets`.
- A secret referenced in any form other than `{{secret:NAME}}`. `{{_internal.*}}`
  variables are blocked at runtime.
- An unresolved template variable.
- A tool schema that does not match the call.
- A wrong surface behavior setting.
- A model timeout.

To stop a failing schedule, call `pause_schedule`. `run_schedule_now` counts toward the
daily execution limit.

## Take over a messaging thread

Messaging threads (Slack, iMessage, SMS, email, Telegram) are separate from assistant
conversations. Their IDs start with `mconv_`, and `list_conversations` does not return
them.

1. Find the thread with `list_messaging_conversations`. Filter by `surface_id`, `status`,
   or `agent_mode`.
2. Call `takeover_messaging_conversation`. If another operator took it over at the same
   time, the call returns 409 and names that operator.
3. Reply with `send_messaging_message`.
4. Call `resume_messaging_conversation` to hand the thread back to the agent.

A takeover lapses after the surface's idle timeout (24 hours by default) without an
operator reply. To start a fresh conversation on an SMS or iMessage surface, close the
thread with `update_messaging_conversation`. Do not delete it.

## Update resources safely

- Read the current configuration before you update it.
- Keep fields that the request does not mention.
- Validate before you update when a validator exists.
- Follow pagination cursors on list tools. On `list_runs` and `list_logs`, stop paging when
  `pagination.cursorReset` is true: the response is page one again, and its cursor loops
  forever.
- Use `get_platform_documentation` for exact contracts, such as schemas, routes, and the
  tool catalog (`topic="platform-catalog"`). Use `search_documentation` for how-to
  questions. On Code Mode, use `search` to find method signatures.
- Use `get_platform_documentation(topic="dashboard-links")` when you give the user links.
- Use `get_secret_intake_manifest`, `submit_secret_intake`, and `check_secrets` so that
  credential values never pass through the conversation.

## Roll back a change

Before you change a flow or agent, note its published version with
`get_published_flow_version` or `get_published_agent_version`.

- Flow: find the earlier version with `list_flow_versions`, then publish it with
  `publish_flow_version`.
- Agent: publish the earlier version with `publish_agent_version`. If the agent uses
  release aliases, call `rollback_agent_alias` and check the result with
  `list_agent_deployments`.

A rollback restores configuration only. It does not undo messages sent, records written,
or other external effects.

Get explicit confirmation before you:

- Set `on_conflict` to overwrite a flow or agent that is managed as code. Publishing
  rejects these by default.
- Move the `live` alias. This needs the `AGENTS:DEPLOY:LIVE` permission and the alias's
  current revision as `if_match`.

## Handle permission errors

On `Permission denied` (HTTP 403), do not retry with guessed IDs. Tell the user which
permission is missing, or request a new key:

1. Call `request_api_key` with the narrowest `permissions` that cover the task and a
   specific `reason`. Keep the returned `codeVerifier`. It cannot be recovered.
2. Wait for a person to approve the request in the dashboard.
3. Redeem it with `runtype api-keys claim <request_id> --verifier <codeVerifier>`, or with
   `claim_api_key` using the default `delivery: "secret"`.

Never print the key into the conversation.

For deeper reference, load the `runtype` skill if it is installed. Prefer live MCP
documentation over local files.
