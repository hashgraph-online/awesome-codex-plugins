# Runtype MCP tool catalog

The Runtype MCP server at `https://api.runtype.com/v1/mcp/protocol` exposes the platform's agent-facing tools. This file groups them by purpose so you can find the right one fast.

For Code Mode MCP, use the `search` and `execute` tools to inspect the generated API spec and run shaped JavaScript against the Runtype API. Call `get_build_instructions` before code-mode writes for products or flows, just as you would in standard MCP.

Prefer live tool discovery and `get_platform_documentation` when available; this file is a fallback map.

## Contents

- [Discovery and identity](#discovery-and-identity)
- [Validation (use before create)](#validation-use-before-create)
- [Tools (creating, running)](#tools-creating-running)
- [Flows (creating, running, versioning)](#flows-creating-running-versioning)
- [Agents (creating, running, versioning)](#agents-creating-running-versioning)
- [Products, surfaces, capabilities](#products-surfaces-capabilities)
- [Records](#records)
- [Schedules](#schedules)
- [Conversations](#conversations)
- [Tracing, logs, costs](#tracing-logs-costs)
- [Batches and evals](#batches-and-evals)
- [Eval suites and the improvement loop](#eval-suites-and-the-improvement-loop)
- [Skills](#skills)
- [Question sets](#question-sets)
- [Messaging conversations](#messaging-conversations)
- [Secrets](#secrets)
- [Models](#models)
- [Persona widget tokens](#persona-widget-tokens)
- [Sandboxes](#sandboxes)
- [Platform docs](#platform-docs)
- [Quick selection guide](#quick-selection-guide)

## Discovery and identity

Start here when you need to understand the state of the workspace.

Resource discovery tools with potentially large rows (`list_products`, `list_agents`,
`list_flows`, `list_tools`, `list_records`, `list_collections`, `list_skills`, and
`list_schedules`) use a
compact response by default: string values longer than 100 characters end in `…`. Keep
that bounded form while browsing, then use the matching `get_*` tool for one resource.
Pass `view: "full"` only when complete strings are required across the page.
`list_agents` accepts `agent_type` (`runtype`, `external`, or `claude_managed`).

| Tool                                                | Use for                                      |
| --------------------------------------------------- | -------------------------------------------- |
| `get_me`                                            | Confirm auth context: user id, org id, email |
| `list_products`                                     | All products in the workspace                |
| `list_flows`                                        | All flows                                    |
| `list_agents`                                       | All agents                                   |
| `list_tools`                                        | All tools                                    |
| `list_surfaces`                                     | Surfaces for a given product                 |
| `list_records`                                      | Records (filterable by type)                 |
| `list_collections`                                  | Registered record types and schemas          |
| `list_skills`                                       | Agent skills (see [Skills](#skills))         |
| `list_schedules`                                    | All schedules                                |
| `list_secrets`                                      | All secrets (metadata only)                  |
| `list_conversations`                                | All conversations                            |
| `list_available_models`                             | What models are available platform-wide      |
| `list_model_configs` / `list_model_configs_grouped` | Models configured for this workspace         |

## Validation (use before create)

Schema feedback here is far more useful than waiting for create errors.

| Tool                       | Validates                                                                                    |
| -------------------------- | -------------------------------------------------------------------------------------------- |
| `validate_product`         | Full FPO product object                                                                      |
| `validate_flow`            | Flow definition                                                                              |
| `validate_product_flow`    | Flow inside an FPO                                                                           |
| `validate_product_agent`   | Agent inside an FPO                                                                          |
| `validate_product_tool`    | Tool inside an FPO                                                                           |
| `validate_product_surface` | Surface inside an FPO                                                                        |
| `validate_code`            | JS snippet (for `transform-data` steps or custom tools) before `create_tool` / `create_flow` |

## Tools (creating, running)

| Tool           | Use                                            |
| -------------- | ---------------------------------------------- |
| `create_tool`  | New custom tool                                |
| `get_tool`     | Full tool config                               |
| `update_tool`  | Modify tool                                    |
| `delete_tool`  | Remove tool                                    |
| `execute_tool` | Run a single tool outside a flow (for testing) |

`discover_mcp_server_tools` lists the tools an external MCP server offers before you register it.

## Flows (creating, running, versioning)

| Tool                         | Use                                                             |
| ---------------------------- | --------------------------------------------------------------- |
| `create_flow`                | New flow with step definitions                                  |
| `get_flow`                   | Flow details                                                    |
| `update_flow`                | Modify; `steps` replace the whole list; records a draft version |
| `delete_flow`                | Remove                                                          |
| `list_flow_versions`         | All versions                                                    |
| `get_flow_version`           | A specific version                                              |
| `get_published_flow_version` | The live version (with step config)                             |
| `publish_flow_version`       | Apply a stored version to the saved flow                        |
| `dispatch`                   | Execute the flow with input (and optional conversation context) |
| `run_flow`                   | Execute an existing flow by id                                  |
| `get_flow_step_results`      | Step-level results for a flow's runs                            |
| `export_flow_runtime`        | Self-contained definition for `@runtypelabs/...` SDK            |

`dispatch`, `run_flow`, and `execute_agent` accept `async: true` for long work; poll the returned handle with `get_execution_status` instead of re-running. `list_runs` lists agent and flow runs together.

## Agents (creating, running, versioning)

| Tool                          | Use                                             |
| ----------------------------- | ----------------------------------------------- |
| `create_agent`                | New agent                                       |
| `get_agent`                   | Agent config                                    |
| `update_agent`                | Partial update; a tool list replaces the set    |
| `delete_agent`                | Remove                                          |
| `list_agent_executions`       | Deprecated: use `list_runs` with `agentId`      |
| `execute_agent`               | Send a message to an agent and capture response |
| `export_agent_runtime`        | Self-contained definition for SDK execution     |
| `list_agent_versions`         | Agent version list                              |
| `get_agent_version`           | Specific version                                |
| `get_published_agent_version` | Live version                                    |
| `publish_agent_version`       | Apply a stored version to the saved agent       |
| `list_agent_aliases`          | Release aliases (`live`, previews)              |
| `get_agent_alias`             | One alias, its version and revision             |
| `activate_agent_alias`        | Point an alias at a version                     |
| `rollback_agent_alias`        | Re-point an alias at its previous version       |
| `archive_agent_alias`         | Retire a preview alias                          |
| `list_agent_deployments`      | Alias deployment history                        |

Run a specific release with `execute_agent` and `alias` or `version_id`; without either, the saved agent runs. Moving an existing `live` needs the alias's current revision as `if_match`.

## Products, surfaces, capabilities

| Tool                                        | Use                                                                                                 |
| ------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `create_product`                            | New product                                                                                         |
| `get_product`                               | Product details                                                                                     |
| `update_product`                            | Modify                                                                                              |
| `delete_product`                            | Remove                                                                                              |
| `get_product_configuration`                 | Secret config status + dashboard URL                                                                |
| `add_product_capability`                    | Attach a flow or agent as a capability                                                              |
| `remove_product_capability`                 | Detach                                                                                              |
| `create_surface`                            | New surface on a product                                                                            |
| `get_surface`                               | Surface details                                                                                     |
| `update_surface`                            | Modify                                                                                              |
| `delete_surface`                            | Remove                                                                                              |
| `add_surface_item`                          | Wire a capability into a surface                                                                    |
| `remove_surface_item`                       | Unwire                                                                                              |
| `create_surface_key` / `delete_surface_key` | Surface API keys                                                                                    |
| `get_slack_app_manifest`                    | Slack app manifest + connect handoff; the from-zero Slack entry point (see the `slack-setup` topic) |
| `install_slack_integration`                 | Slack install for a caller who already holds a bot token and signing secret (migration or rotation) |
| `get_slack_app_status`                      | Slack app connection state                                                                          |
| `create_integration`                        | Reserve a pending Slack integration                                                                 |
| `get_product_setup`                         | Remaining setup steps (secrets, OAuth, installs) before a product is live                           |
| `get_surface_setup`                         | Whether one surface is live, and its remaining install steps                                        |
| `test_surface`                              | Send a mock inbound message through a surface and capture what would be delivered                   |
| `get_surface_channel_context`               | Recent channel messages and reply decisions for a Slack, Telegram, or iMessage group surface        |
| `list_example_templates`                    | First-party example templates                                                                       |
| `create_product_from_example`               | Create a product from an example slug or a template/quick-start URL                                 |

## Records

| Tool                                        | Use                                       |
| ------------------------------------------- | ----------------------------------------- |
| `create_record`                             | New record                                |
| `get_record`                                | Read one                                  |
| `list_records`                              | Browse / filter                           |
| `update_record`                             | Edit                                      |
| `delete_record`                             | Remove one                                |
| `bulk_edit_records` / `bulk_delete_records` | Multi-record ops                          |
| `get_record_results`                        | Execution history for a record            |
| `get_record_step_results`                   | Step-level results for a record           |
| `get_record_costs`                          | Cost aggregation by model                 |
| `delete_record_result`                      | Remove one execution result from a record |

Collections register a record type, optionally with a metadata schema: `list_collections`, `get_collection`, `create_collection`, `update_collection`, `delete_collection`. `infer_collection_schema` proposes a schema from existing records, `validate_collection_records` dry-runs records against one, and `get_collection_types` returns TypeScript declarations for the SDK.

## Schedules

| Tool                                 | Use                            |
| ------------------------------------ | ------------------------------ |
| `create_schedule`                    | Cron or one-time trigger       |
| `get_schedule`                       | Schedule details               |
| `update_schedule`                    | Modify                         |
| `delete_schedule`                    | Remove                         |
| `list_schedule_runs`                 | Per-schedule execution history |
| `pause_schedule` / `resume_schedule` | Toggle without deleting        |
| `run_schedule_now`                   | Force an immediate run         |

## Conversations

| Tool                  | Use                                             |
| --------------------- | ----------------------------------------------- |
| `create_conversation` | New conversation thread                         |
| `get_conversation`    | Thread + messages                               |
| `update_conversation` | Title, model, system prompt, metadata, messages |
| `delete_conversation` | Remove                                          |
| `list_conversations`  | Browse                                          |

## Tracing, logs, costs

| Tool                    | Use                                               |
| ----------------------- | ------------------------------------------------- |
| `trace_execution`       | Structured trace tree for a single execution      |
| `trace_conversation`    | Trace spanning multiple turns                     |
| `list_logs`             | Query persisted logs                              |
| `get_log_stats`         | Aggregated counts by level/category + time-series |
| `get_batch_cost`        | Total cost for a batch execution                  |
| `get_batch_record_cost` | One record's cost within a batch                  |
| `get_record_costs`      | Per-record cost by model                          |

## Batches and evals

| Tool                     | Use                                |
| ------------------------ | ---------------------------------- |
| `submit_batch`           | Execute a flow across many records |
| `get_batch_status`       | Progress                           |
| `get_batch_summary`      | Workspace-wide batch summary       |
| `get_batch_record_steps` | Per-record step results in a batch |
| `cancel_batch`           | Kill a running batch               |
| `submit_eval`            | Eval batch                         |
| `get_eval_results`       | Per-record outputs                 |
| `compare_eval`           | Compare across runs                |
| `compare_eval_record`    | Drill into one record across runs  |
| `analyze_eval_steps`     | Step-level performance             |
| `get_eval_group`         | Group of related evals             |
| `list_eval_batches`      | List eval batches                  |

## Eval suites and the improvement loop

| Tool                           | Use                                                                                 |
| ------------------------------ | ----------------------------------------------------------------------------------- |
| `create_eval_suite`            | Saved cases + graders for one flow or agent                                         |
| `add_eval_cases`               | Author cases by hand                                                                |
| `get_eval_capture_preview`     | Preview fork points before capturing a real run                                     |
| `add_eval_case_from_execution` | Capture a real run (hosted or ingested from an external agent) as a regression case |
| `run_eval_suite`               | Re-run the suite; needs a target Runtype can execute (hosted, or external over A2A) |
| `get_eval_run_scores`          | Scores for one run                                                                  |
| `generate_eval_cases`          | Machine-proposed cases                                                              |
| `get_eval_coverage`            | Coverage gaps                                                                       |
| `list_eval_proposals`          | Review proposed cases                                                               |
| `resolve_eval_proposal`        | Accept or reject a proposal                                                         |
| `review_eval_score`            | Record agreement with a judge verdict                                               |

Manage suites and cases with `list_eval_suites`, `get_eval_suite`, `update_eval_suite`, `delete_eval_suite`, `update_eval_case`, and `delete_eval_case`.

## Skills

Runtype Agent Skills are loadable instruction bundles for deployed agents. A bound agent loads one through its `skill:<slug>` tool.

| Tool                                                  | Use                                                       |
| ----------------------------------------------------- | --------------------------------------------------------- |
| `list_skills` / `get_skill`                           | Browse skills and their versions                          |
| `create_skill` / `update_skill` / `delete_skill`      | Author a skill                                            |
| `import_skill`                                        | Import an external SKILL.md document as a draft           |
| `publish_skill_version`                               | Make a draft version live for bound agents                |
| `bind_skill` / `unbind_skill` / `list_skill_bindings` | Attach skills to an agent (track latest or pin a version) |
| `list_skill_proposals`                                | Agent-authored skill proposals awaiting review            |
| `approve_skill_proposal` / `reject_skill_proposal`    | Review a proposal; approving publishes it                 |

Read `get_platform_documentation(topic="agent-skills")` before authoring.

## Question sets

Versioned judgment question sets: named boolean, choice, or score questions answered with probabilities. Publish a version before a tool config or step references the set.

| Tool                                                                | Use                                       |
| ------------------------------------------------------------------- | ----------------------------------------- |
| `create_question_set` / `update_question_set`                       | Author questions (updates add a draft)    |
| `get_question_set` / `list_question_sets`                           | Browse                                    |
| `publish_question_set_version`                                      | Make a version current                    |
| `calibrate_question_set_version` / `list_question_set_calibrations` | Record and review per-question thresholds |

## Messaging conversations

Threads on messaging surfaces (Slack, SMS, iMessage, email, Telegram, and others).

| Tool                                                              | Use                                                           |
| ----------------------------------------------------------------- | ------------------------------------------------------------- |
| `list_messaging_conversations` / `get_messaging_conversation`     | Find a thread                                                 |
| `takeover_messaging_conversation`                                 | Hand the thread to a human operator; the agent stops replying |
| `send_messaging_message`                                          | Reply as the operator                                         |
| `resume_messaging_conversation`                                   | Return the thread to the agent                                |
| `update_messaging_conversation` / `delete_messaging_conversation` | Edit or remove a thread                                       |

## Secrets

| Tool                         | Use                                                               |
| ---------------------------- | ----------------------------------------------------------------- |
| `create_secret`              | New secret                                                        |
| `get_secret`                 | Metadata (not the value)                                          |
| `list_secrets`               | All secrets in scope                                              |
| `update_secret`              | New value or description                                          |
| `delete_secret`              | Hard delete                                                       |
| `check_secrets`              | Bulk existence/revocation check                                   |
| `get_secret_intake_manifest` | Which secrets need values for a source (manual, FPO import, etc.) |
| `submit_secret_intake`       | Batch fill secret values                                          |

## Models

| Tool                         | Use                             |
| ---------------------------- | ------------------------------- |
| `list_available_models`      | Platform-wide model catalog     |
| `list_model_configs`         | Workspace's configured models   |
| `list_model_configs_grouped` | Grouped by base model           |
| `create_model_config`        | Add a model with provider key   |
| `update_model_config`        | Update provider key or settings |
| `delete_model_config`        | Remove                          |
| `toggle_model_config`        | Enable/disable                  |
| `set_default_model_config`   | Set provider default            |

Bring-your-own provider credentials: `list_provider_keys`, `create_provider_key`, `update_provider_key`, `delete_provider_key`, and `select_organization_provider_credential`. For an OpenAI-compatible endpoint, `discover_provider_models` reads its model list and `sync_provider_models` saves the models to offer.

## Persona widget tokens

| Tool                          | Use                                                                           |
| ----------------------------- | ----------------------------------------------------------------------------- |
| `create_client_token`         | New token for browser-side Persona widget                                     |
| `get_client_token`            | Details                                                                       |
| `list_client_tokens`          | All tokens                                                                    |
| `update_client_token`         | Change name, scope, origins, or limits                                        |
| `delete_client_token`         | Remove                                                                        |
| `regenerate_client_token`     | Invalidate old, issue new                                                     |
| `generate_persona_embed_code` | **Generate ready-to-use embed code**; prefer this over hand-writing the embed |
| `get_persona_theme_reference` | Design tokens, default palette, examples; call before generating themes       |

## Sandboxes

| Tool              | Use                                                            |
| ----------------- | -------------------------------------------------------------- |
| `deploy_sandbox`  | Deploy code to a Runtype Sandbox; returns a public preview URL |
| `destroy_sandbox` | Tear down                                                      |

`extend_asset_expiry` extends a preview page published by the `builtin:publish_page` tool, keeping its URL.

## Platform docs

| Tool                         | Use                                              |
| ---------------------------- | ------------------------------------------------ |
| `get_build_instructions`     | Detailed instructions for building on Runtype    |
| `get_platform_documentation` | Schemas, type definitions, docs                  |
| `search_documentation`       | Natural-language answer from the docs, cited     |
| `submit_feedback`            | Report a Runtype bug or doc gap (free)           |
| `generate_proposal`          | Scope-of-work proposal tool for a client project |
| `generate-proposal`          | MCP prompt variant of the proposal workflow      |

Start with the `index` topic (task-to-topic map). Useful documentation topics include `platform-catalog`, `surface-types`, `flow-step-types`, `models`, `product-schema`, `types-fpo`, `types-flow-steps`, `types-entities`, `types-surface-configs`, `orthogonal-tools`, `builtin-tools`, `agent-skills`, `external-tools`, `external-agents`, `evals`, `limits`, `validation-errors`, `setup-readiness`, `dashboard-links`, `mock-ecommerce`, `persona-embed`, `persona-fullscreen-assistant`, and `sdk-reference`.

For WebMCP page tools, read `persona-embed` and `types-surface-configs`. Configure
widget `config.webmcp.enabled` and `behavior.webmcp` on a `chat` surface; do not
create an `mcp` surface unless you want to expose Runtype capabilities to
external MCP clients. See
`persona-widget.md` for the full WebMCP setup and the advanced non-Persona
direct-`/v1/dispatch` `clientTools[]` path.

Useful MCP resources include `runtype://catalog/platform`, `runtype://catalog/surface-types`, `runtype://catalog/flow-step-types`, `runtype://catalog/models`, `runtype://schema/fpo`, `runtype://types/fpo`, `runtype://types/fpo-template`, `runtype://types/flow-steps`, `runtype://types/entities`, `runtype://types/surface-configs`, `runtype://catalog/orthogonal-tools`, `runtype://catalog/builtin-tools`, `runtype://catalog/skills`, `runtype://guide/external-tools`, `runtype://guide/subagent-delegation`, `runtype://catalog/provider-native-search`, `runtype://catalog/dashboard-links`, `runtype://catalog/mock-ecommerce`, `runtype://catalog/ucp-commerce`, `runtype://catalog/persona-embed`, `runtype://guide/persona-fullscreen-assistant`, and `runtype://types/sdk-reference`.

## Quick selection guide

> "I want to test a single tool" → `execute_tool`
> "I want to test an agent without committing" → `execute_agent` (against an existing agent)
> "I want to run a one-shot prompt" → `dispatch` (inline virtual flow with a single prompt step)
> "I want to test an existing (multi-step) flow with input" → `dispatch` / `run_flow` against the stored flow id
> "I want to run a flow over a record set" → `submit_batch`
> "I want to compare two prompts" → `submit_eval` + `compare_eval`
> "I want this fix to stay fixed" → `add_eval_case_from_execution` into a suite, then `run_eval_suite` after each change
> "I want to ship an agent change safely" → `activate_agent_alias` on a preview, `run_eval_suite` with `agent_alias`, then move `live` (callers that select `live` follow it)
> "Something failed. What happened?" → `trace_execution` → if not enough, `list_logs` with the execution id
> "How much did this cost?" → `get_batch_cost` / `get_record_costs`
> "I need to embed a chat widget" → `generate_persona_embed_code` → look at `persona-widget.md` for theming
> "What can I build?" → `get_build_instructions` then `get_platform_documentation`
