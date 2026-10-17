# Primitives

This file goes deeper on each Runtype primitive: its shape, its lifecycle, and which MCP tools touch it.
Prefer live `platform-catalog`, `product-schema`, and type resources when available.

## Contents

- [Product](#product)
- [Agent](#agent)
- [Flow](#flow)
- [Tool](#tool)
- [Capability](#capability)
- [Surface](#surface)
- [Record](#record)
- [Schedule](#schedule)
- [Eval](#eval)
- [Secrets](#secrets)
- [Conversation](#conversation)
- [External and federated agents (A2A, cloud-managed)](#external-and-federated-agents-a2a-cloud-managed)
- [Persona client tokens](#persona-client-tokens)

## Product

The container. A Product groups everything: agents, flows, tools, surfaces, capabilities, schedules, secrets. The thing you deploy.

A product expresses **what your AI does, who it's for, and where users reach it**. The same agent in two different products with different system prompts and different surfaces is two different products.

Shape (`FullProductObject`):

- Metadata (name, description, version)
- Agents, flows, tools, schedules
- Surfaces, with capabilities mapped to each
- Secret declarations
- Optional record seed data

Operations: `create_product`, `update_product`, `delete_product`, `list_products`, `get_product`, `get_product_configuration` (secret-config status + dashboard URL), `validate_product`.

Secret intake: `get_secret_intake_manifest` returns what's missing; `submit_secret_intake` batches values in.

## Agent

An LLM with a system prompt and a tool set. Reaches for tools to accomplish a goal.

Shape:

- `model`: model config reference (use `list_model_configs`)
- `systemPrompt`: the main thing that defines the agent's behavior
- `tools`: array of tool ids
- `maxToolCalls`: how many tool calls the agent can make in one turn (default is 10; raise it deliberately for tool-heavy tasks)
- `agentLoop` config (optional, advanced): how many full turns of reflection the agent can do
- `responseFormat`, `config.tools.approval` (tools that pause for a human), etc.

Lifecycle: `create_agent`, `get_agent`, `update_agent` (partial: only the fields you pass change, but a tool list you pass replaces the whole set), `delete_agent`, `execute_agent`. List an agent's runs with `list_runs` and `agentId` (`list_agent_executions` is deprecated).

Versions and releases: every save records an immutable version (`list_agent_versions`, `get_agent_version`). A release alias (`live` plus previews) points at one version: `list_agent_aliases`, `get_agent_alias`, `activate_agent_alias`, `rollback_agent_alias`, `archive_agent_alias`, and `list_agent_deployments` for the receipt history. Pass `alias` or `version_id` to `execute_agent` to run a specific pointer; a request that selects neither runs the saved agent, so a save reaches it immediately. `publish_agent_version` applies a stored version onto the saved agent.

### Most important thing: the system prompt

The system prompt is where you spend your time on agent design. Analogy: writing the employee handbook for a new hire. Be explicit about:

- What this agent does
- Who the users are
- The tone and style expected
- Tool usage guidelines
- What NOT to do

When an agent isn't doing what you want, the first reach is to improve the system prompt, not to add tools, switch models, or add a flow. Be more explicit.

### `maxToolCalls` vs `agentLoop`

Two different knobs that get confused.

- **`maxToolCalls`**: how many tool calls the agent can make in one execution. Default is 10. Raise it deliberately when the task requires several lookups, writes, or sub-agent calls in one turn.
- **`agentLoop`** (`loopConfig.maxTurns`): a cap on how many _full turns_ the agent may take, each re-running with the previous results as context. The loop ends as soon as the model finishes its turn; it takes another turn only when the turn was cut off by the `maxToolCalls` budget, when the model call failed and is retried, or when a skill load or tool search expanded the tool surface (newly granted tools activate on the next turn, so skill-using agents need `maxTurns` of at least 2). It is a safety cap, not a target. A higher cap costs nothing on turns the agent never takes. The risk lives inside the loop, not in the ceiling: looping on the same goal repeats the same work unless you explicitly tell the agent to reflect or vary approach.

Tune `maxToolCalls` before reaching for `agentLoop`. Raise `maxTurns` when the agent genuinely needs another pass: reflection, more tool calls than one turn's budget allows, or skill capabilities that only activate on a following turn.

Often, **sub-agents** (agents that the orchestrator calls as tools) are better than agent loops. They get clean context, can use different models tuned for sub-tasks, and avoid the same-task-repeated trap.

### Picking a model

Axes to consider:

- **Intelligence**: generally correlates with size and recency.
- **Latency**: larger models are slower.
- **Cost**: larger models cost more.
- **Compliance/governance**: data residency, region. Drives provider choice (Vertex/Gemini for GCP shops, etc.).
- **Family-specific tools**: provider-native search, fetch, image, or research tools available only on certain model families.

Default: use the current model catalog and routed model IDs. Pick one intelligent
enough for the task and optimized for speed/cost. Avoid starting on the largest
available model unless the task genuinely needs it.

Use `list_available_models`, `list_model_configs`, and
`get_platform_documentation(topic="models")` for current availability and key
requirements.

## Flow

A deterministic, multi-step pipeline. Use when the steps are known and you want speed/cost optimization over flexibility.

Shape:

- `inputSchema` / `outputSchema`
- `steps`: array of step objects with type and config (see `flow-steps.md`)
- Each step has optional `when` (skip condition), retry/fallback config, and streaming-visibility config

Step results become flow variables. Reference in templates as `{{stepName.field}}`, or via the `input` object in `transform-data` JS code.

Lifecycle: `create_flow`, `validate_flow`, `update_flow`, `list_flow_versions`, `get_flow_version`, `publish_flow_version`, `get_published_flow_version`, `run_flow`, `dispatch`, `delete_flow`.

Flows are versioned. `update_flow` saves the definition (its `steps` replace the whole list) and records a draft version; `publish_flow_version` applies a stored version to the saved definition, which entry points that are not pinned to a version run immediately.

### When flows beat agents

Flows can be much faster and cheaper than the equivalent agent when the steps are deterministic. The win comes from skipping LLM tool-selection round trips.

Good candidates to be a flow (not an agent):

- Sending an email: format → render → send
- Indexing data: crawl → chunk → embed → store
- API-to-API pipelines: fetch → transform → upsert
- Anything you know happens every time, in this order

Often a flow is part of an agent's tool set, and the agent decides _when_ to invoke the deterministic pipeline.

## Tool

A typed callable. The agent's interface to the outside world.

Three categories:

1. **First-party integrations**: Firecrawl, Exa, Weaviate, Cloudflare Vectorize, Orthogonal, web search, asset generation, and connected apps (Slack, GitHub, Linear, Google Workspace, Granola). Preferred when they fit.
2. **External MCP server tools**: register an external MCP server to make its tools available.
3. **Custom tools**: HTTP/REST tool, custom JS code, or a flow exposed as a tool.

Shape for custom:

- `name`, `description`: what the LLM sees when deciding to call
- `inputSchema` (or `parameters`): typed args with descriptions
- `code` (JS) or `config` (HTTP)
- `auth.secrets`: secret keys, referenced inside config as `{{secret:KEY}}`

Lifecycle: `validate_code` → `create_tool` → `update_tool` / `delete_tool` / `execute_tool`.

### Tool descriptions and parameters are the LLM's interface

If an agent isn't calling a tool you expected it to, the first thing to fix is the **tool description and parameter docs**. Treat them like docstrings. Describe:

- What the tool does
- When to use it
- What each parameter means
- What the result will look like

For flow-as-tool, the dashboard tool editor's **Generate from Flow** button drafts parameter names, types, and descriptions from the flow's steps and the variables they reference. Treat the draft as a first pass and edit it.

### Surface-specific tools (auto-registered)

When an agent connects to a surface, **surface-specific tools auto-register**. The agent definition stays the same; its tool surface adapts.

Examples:

- **Persona (web chat)**: markdown artifact generation, document toolbar, etc.
- **Slack**: thread-context lookup, rich-mrkdwn formatting.
- **Telegram, Discord, etc.**: channel-specific helpers.

Don't manually add tools for things the surface already provides.

### Browser use / sandbox use

Agents can provision a whole computer (a sandbox or a browser session) and take actions in it. Browser and sandbox tools cost more and run slower than scoped API tools, so use them only when no scoped tool fits.

The right order: scoped API tool > MCP server > custom HTTP tool > sandbox/browser use.

### Local tool calling (SDK only)

Tools that run **client-side**, invoked through the SDK rather than in Runtype. The LLM issues a tool call; the SDK on your client picks it up; the tool runs locally; the result goes back through Runtype.

Two flavors:

- **Browser-side** (Persona context): tools call browser APIs to read HTML, navigate, and access front-end state.
- **Server-side** (Python/TS SDK on your server): tools run on your infrastructure, can call local AI models, can access data you don't want passing through Runtype.

Combined with hidden parameters (below), this is the security architecture for products where the LLM orchestrates operations on data it shouldn't see.

### Hidden parameters

List parameter names in a runtime tool's `hiddenParameterNames` to fill them from execution variables instead of from the model. Runtype strips them from the model-facing schema, overrides any model-supplied value, and shows `[REDACTED]` in `tool_start` / `tool_input_complete`.

Pattern: the LLM sees `list_orders(status)`. With `hiddenParameterNames: ['_tenant']` and a header `X-Tenant-Id: {{_tenant.id}}`, the verified tenant reaches the API without entering the model's context.

- `_tenant` / `_endUser` come from the execution's end-user identity (Identity Exchange or a trusted backend). `_`-prefixed hidden names resolve only from the host and fail the call closed when unset. `_internal*` names are rejected.
- A hidden name without a leading `_` is best-effort: if no execution variable (or `_record.metadata` field) matches, it stays visible and the model supplies it. Never use one for identity.
- Tool templates resolve only tool arguments, hidden parameters, and `{{secret:KEY}}`. `{{_record.*}}`, `{{_flow.*}}`, and `{{_user.*}}` do not resolve in a tool's url/headers/body.
- `{{_tenant.id}}` / `{{_endUser.id}}` are host-only automatically wherever referenced: external tool templates (runtime and saved tools) and `auth.headers` of MCP servers in an agent's `tools.mcpServers`. Saved MCP servers send static auth only.
- For identity your API verifies itself, send `Authorization: Bearer {{_identity.token}}`: a per-call Runtype-signed JWT, minted only for an agent with a `tenancyStrategy`.
- Credentials still go in `{{secret:KEY}}`, never in a hidden parameter.

Docs: https://docs.runtype.com/developer-guides/guides/tool-template-variables

## Capability

A capability is just "an agent or flow exposed inside a product." It's the unit a surface invokes.

The dashboard sometimes labels these "capabilities"; the API often calls them "agents and flows." Same concept.

Tools: `add_product_capability`, `remove_product_capability`. Surfaces reference them via `add_surface_item`.

### The many-to-many shape

Capabilities and surfaces are **many-to-many**. Concrete examples:

- One agent exposed across three surfaces (Slack, email, web chat).
- Three agents exposed on one MCP surface, which generates three MCP tools.
- Three agents exposed on one web chat surface, for which Runtype provisions an orchestrator (see below).
- A flow exposed as both a REST endpoint and an MCP tool simultaneously.

### Auto-generated REST and MCP APIs

When you bind capabilities to a `mcp` or `api` surface, the platform **automatically generates** endpoints (for REST) or tools (for MCP) from each capability. You pick the auth scheme, and Runtype hosts the URL.

You're not coding API endpoints; you're declaring which capabilities go on which surface.

### The orchestrator (when multiple capabilities → one conversational surface)

When **more than one capability** is connected to a conversational surface (`chat`, `slack`, `telegram`, `discord`, `email`, etc.), Runtype **automatically provisions an orchestrator agent**. It decides which capability handles each incoming message.

Defaults:

- Inexpensive fast model (because routing at 10-20s defeats the purpose).
- Minimum data over the wire, usually just a short label per capability.
- Alphabetical labels (A, B, C…) for the route options.

Overridable: model, system prompt, routing logic. **Run a surface eval (dashboard) on the orchestrator** to compare routing strategies before launch.

Practical implication: you don't need to write your own "router agent." Add the capabilities, let the orchestrator route.

## Surface

How clients (humans or machines) reach into a product. See `surfaces.md` for the trait matrix, and `get_platform_documentation(topic="surface-types")` for the current list of types.

Each surface has:

- A **type** (`chat`, `slack`, `webhook`, `api`, `mcp`, `schedule`, etc.)
- **Traits** the platform enforces: streaming behavior, markdown dialect, max response length, reasoning visibility, etc.
- A **behavior config** specific to the type
- Optional **surface keys** for authentication (clients use these)
- For Persona: **client tokens** issued via `create_client_token`
- For hosted pages: product-level `HostedPageBehavior` and per-capability
  `HostedPagePresentation` in `runtype://types/surface-configs`

Lifecycle: `create_surface` → `add_surface_item` (wire a capability in) → `update_surface` / `delete_surface`. Slack-specific: connect the workspace with the `slack-setup` runbook (`runtype://guide/slack-setup`); `install_slack_integration` is only for a caller who already holds a bot token and signing secret.

## Record

Runtype's built-in record store. Free-form data with vector-search.

Shape:

- `id` (auto), `type` (table-like), `name` (unique within type), `metadata` (JSON), `createdAt`, `updatedAt`
- Optional embedding for vector search

Records suit data that Runtype owns: agent memory, correlation keys, and product data such as a catalog or customer list that agents read and update. When the source of truth already lives in another system, keep it there and store only what Runtype needs to correlate and remember.

The simplest useful pattern: give an agent record read/write/update tools. That's how the agent "remembers" what users asked it to do.

Operations: `create_record`, `update_record`, `get_record`, `list_records`, `bulk_edit_records`, `bulk_delete_records`. Flow steps: `get-record`, `list-records`, `upsert-record`, `update-record`. Per-record execution data: `get_record_results`, `get_record_step_results`, `get_record_costs`. Vector: `generate-embedding`, `store-vector`, `vector-search` flow steps.

Filtering supports complex queries: `recordFilter: { type, where }` with conditions on top-level columns and top-level metadata keys, combined in AND/OR groups. Name a metadata key bare (`field: "owner_key"`), not `metadata.owner_key`. Test filters in a flow first (you can run iteratively), then move to a schedule with the same filter.

## Schedule

Cron or one-time trigger.

Shape: `target` (exactly one of `flow_id` or `agent_id`; flow schedules may add `record_ids` or `record_type`), `trigger` (`{ type: "recurring", cron, timezone }` or `{ type: "one_time", run_at }`), and `messages` passed to each run.

For flows: standard "call function on schedule." For agents: the trigger looks like a message being pushed into a conversation, which is useful for **heartbeat patterns** ("every morning, check the todo list and decide what to do"). Schedules can also fan out as a batch over all records of a particular type.

Lifecycle: `create_schedule`, `update_schedule`, `delete_schedule`, `pause_schedule` / `resume_schedule`, `run_schedule_now` (manual trigger), `list_schedule_runs`.

## Eval

Two mechanisms for two jobs:

- **Eval suites** are the regression harness. A suite is a saved set of cases plus graders attached to one flow or agent, and every run produces a score (passed cases / total). Create one with `create_eval_suite`, author cases with `add_eval_cases`, capture a real run (hosted or ingested from an external agent) with `get_eval_capture_preview` then `add_eval_case_from_execution`, and re-run with `run_eval_suite` after every prompt, model, or tool change. Read scores with `get_eval_run_scores`.
- **Ad-hoc eval batches** compare variants once: `submit_eval` runs a flow or agent over records or messages, optionally with several model configs, then `get_eval_results`, `compare_eval`, `compare_eval_record`, `analyze_eval_steps`, `get_eval_group`, and `list_eval_batches`.

Graders run on every case. Deterministic kinds check the output (`contains`, `regex`, `valid_json`, `json_field`, `matches_expected`, `latency`, `no_error`, …); trace kinds check what the run did (`called_tool`, `not_called_tool`, `tool_order`, `max_tool_calls`, `ran_step`, `cost`, …); `ai` is an LLM judge with plain-language criteria. A grader is a `gate` (default: a miss fails the case) or `soft` (tracked; fails only on a `strict` run).

`run_eval_suite` can target an agent release alias or version (`agent_alias`, `agent_version_id`) or swap the model (`model_override`), so test a preview before moving `live`. To grow coverage, `get_eval_coverage` shows which tools and instructions no case exercises and `generate_eval_cases` proposes cases; nothing enters the suite until you accept it (`list_eval_proposals`, `resolve_eval_proposal`). `review_eval_score` records whether an `ai` grader's verdict was right.

Things worth varying: model choice, system prompt variants, tool set differences, fallback configurations. The MCP eval tools target a flow or agent. For a multi-capability product, also run a surface eval from the dashboard (it sends messages through the surface, so orchestrator routing and channel formatting are covered).

Evals can also run from your own code (REST / SDK), which is useful for CI/CD.

## Secrets

Managed secret store. Values are encrypted at rest and never returned by the API: reads return metadata (key, status, version) and a short masked preview only.

Reference syntax, the same everywhere (tool configs, FPO templates, runtime): `{{secret:KEY}}`, with **singular `secret`, colon separator, UPPER_CASE key**. Example: `"Authorization": "Bearer {{secret:STRIPE_API_KEY}}"`.

Two adjacent syntaxes that look similar but are different:

- `{{secrets:KEY}}`: **plural with colon is invalid**. The resolver rejects it.
- `{{secrets.key}}`: plural with **dot** is RETIRED, not a managed secret: a non-empty dispatch `secrets` map is refused with 400 `RUNTIME_AGENT_TRANSIENT_SECRETS_UNSUPPORTED` on agent dispatches and 400 `RUNTIME_FLOW_TRANSIENT_SECRETS_UNSUPPORTED` on flow dispatches. Never emit it; `{{secret:KEY}}` is the only credential contract.

Log output is scrubbed for credential-shaped values (known API-key formats and high-entropy strings). Still keep secret values out of prompts, tool results, and record metadata.

Lifecycle: `create_secret`, `list_secrets`, `get_secret` (metadata only), `update_secret`, `delete_secret`, `check_secrets` (bulk existence check).

### Pending-secret pattern (for product setup and distribution)

Best practice for setting up a product:

1. Declare the tool's secret needs in `auth.secrets`.
2. Reference them in tool config as `{{secret:KEY}}`, the same syntax in stored tool configs and in FPO templates.
3. Don't fill in the secret values yet. Leave them pending.
4. The user (or the product's installer) fills them in via the intake flow.

This means the product architecture is set up completely without anyone needing the credential values in hand. Secrets never end up in product records or template files.

## Conversation

Multi-turn agent state.

Operations: `create_conversation`, `get_conversation`, `update_conversation` (title, model, system prompt, metadata, messages), `delete_conversation`, `list_conversations`, `trace_conversation`.

Conversations attach to surfaces with `threadModel: "threaded"` or `"reply_chain"` (Slack, Discord, email). For `flat` surfaces, each invocation is typically a new conversation unless input wires it to an existing one.

## External and federated agents (A2A, cloud-managed)

Runtype can federate **external agents** into a product as capabilities:

- **A2A agents**: external agents that speak the Agent-to-Agent protocol. Register their skills, mix them with native Runtype agents in the same product, expose the combined surface set to users.
- **Cloud-managed agents**: externally hosted agents registered as capabilities. The agent lives outside Runtype; Runtype routes traffic to it.

Why this matters:

- **Incremental migration**: if you have an existing agent in another framework (CrewAI, custom), expose it as A2A and federate it into Runtype to get the surface delivery layer (Slack/email/SMS/etc.) without rewriting.
- **Best tool for the job**: use a specialized framework such as CrewAI for a sub-task, and let Runtype own the product persona and surface delivery.

The execution engine routes intelligently across native + federated capabilities. From the user's perspective, it's one product.

## Persona client tokens

For the embedded chat widget, `chat` surfaces use browser-safe `clientToken`s created with `create_client_token`. These tokens are public, scoped to specific agents or flows, revocable, and can be constrained with origin and rate-limit settings.

Lifecycle: `create_client_token`, `get_client_token`, `list_client_tokens`, `regenerate_client_token`, `delete_client_token`.

Generate embed code via `generate_persona_embed_code`. Theme reference via `get_persona_theme_reference`.

See `persona-widget.md` for details.
