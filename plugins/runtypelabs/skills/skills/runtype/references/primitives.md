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

- `model` — model config reference (use `list_model_configs`)
- `systemPrompt` — the main thing that defines the agent's behavior
- `tools` — array of tool ids
- `maxToolCalls` — how many tool calls the agent can make in one turn (default is 10; raise it deliberately for tool-heavy tasks)
- `agentLoop` config (optional, advanced) — how many full turns of reflection the agent can do
- `responseFormat`, `humanInLoopApprovals`, etc.

Lifecycle: `create_agent`, `get_agent`, `update_agent` (wholesale replacement), `delete_agent`, `execute_agent`, `list_agent_executions`. Staging: `list_agent_versions`, `publish_agent_version`.

### Most important thing: the system prompt

The system prompt is where you spend your time on agent design. Analogy: writing the employee handbook for a new hire. Be explicit about:

- What this agent does
- Who the users are
- The tone and style expected
- Tool usage guidelines
- What NOT to do

When an agent isn't doing what you want, the first reach is to improve the system prompt — not to add tools, not to switch models, not to add a flow. Be more explicit.

### `maxToolCalls` vs `agentLoop`

Two different knobs that get confused.

- **`maxToolCalls`**: how many tool calls the agent can make in one execution. Default is 10. Raise it deliberately when the task requires several lookups, writes, or sub-agent calls in one turn.
- **`agentLoop`**: how many _full reflection turns_ the agent gets — re-running with the previous results as context, getting another shot. Advanced. Risks: looping with the same goal does the same task each iteration unless you explicitly tell it to reflect or vary approach. The most expensive, easiest-to-mess-up architecture.

Tune `maxToolCalls` before reaching for `agentLoop`. Use `agentLoop` only when you've verified the agent needs reflection and a clearer prompt or a different approach won't do it.

Often, **sub-agents** (agents that the orchestrator calls as tools) are better than agent loops. They get clean context, can use different models tuned for sub-tasks, and avoid the same-task-repeated trap.

### Picking a model

Axes to consider:

- **Intelligence** — generally correlates with size and recency.
- **Latency** — bigger = slower.
- **Cost** — bigger = more expensive.
- **Compliance/governance** — data residency, region. Drives provider choice (Vertex/Gemini for GCP shops, etc.).
- **Family-specific tools** — provider-native search, fetch, image, or research tools available only on certain model families.

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
- `steps` — array of step objects with type and config (see `flow-steps.md`)
- Each step has optional `when` (skip condition), retry/fallback config, and streaming-visibility config

Step results become flow variables. Reference in templates as `{{stepName.field}}`, or via the `input` object in `transform-data` JS code.

Lifecycle: `create_flow`, `validate_flow`, `update_flow` (creates new version), `list_flow_versions`, `publish_flow_version`, `get_published_flow_version`, `dispatch`, `delete_flow`.

Flows are versioned. Updates create new versions; only the published one is invoked by surfaces.

### When flows beat agents

Flows can be much faster and cheaper than the equivalent agent when the steps are deterministic. The win comes from skipping LLM tool-selection round trips.

Good candidates to be a flow (not an agent):

- Sending an email: format → render → send
- Indexing data: crawl → chunk → embed → store
- API-to-API pipelines: fetch → transform → upsert
- Anything you know happens every time, in this order

Often a flow is part of an agent's tool set — the agent decides _when_ to invoke the deterministic pipeline.

## Tool

A typed callable. The agent's interface to the outside world.

Three categories:

1. **First-party integrations** — Firecrawl, Exa, Weaviate, Cloudflare Vectorize, Orthogonal, web search, asset generation. Preferred when they fit.
2. **External MCP server tools** — register an external MCP server, its tools become available.
3. **Custom tools** — HTTP/REST tool, custom JS code, or a flow exposed as a tool.

Shape for custom:

- `name`, `description` — what the LLM sees when deciding to call
- `inputSchema` (or `parameters`) — typed args with descriptions
- `code` (JS) or `config` (HTTP)
- `auth.secrets` — secret keys, referenced inside config as `{{secret:KEY}}`

Lifecycle: `validate_code` → `create_tool` → `update_tool` / `delete_tool` / `execute_tool`.

### Tool descriptions and parameters are the LLM's interface

If an agent isn't calling a tool you expected it to, the first thing to fix is the **tool description and parameter docs**. Treat them like docstrings. Describe:

- What the tool does
- When to use it
- What each parameter means
- What the result will look like

For flow-as-tool, the platform has a "generate parameters from a description" capability — it runs an internal AI flow to fill in parameter descriptions and types based on what you wrote. Use it as a first pass, then tune.

### Surface-specific tools (auto-registered)

When an agent connects to a surface, **surface-specific tools auto-register**. The agent definition stays the same; its tool surface adapts.

Examples:

- **Persona (web chat)**: markdown artifact generation, document toolbar, etc.
- **Slack**: thread-context lookup, rich-mrkdwn formatting.
- **Telegram, Discord, etc.**: channel-specific helpers.

Don't manually add tools for things the surface already provides.

### Browser use / sandbox use

Agents can provision a whole computer (Daytona sandbox or browser session) and take actions in it. Powerful. Expensive. Slow. Use only when there's no scoped tool that fits.

The right order: scoped API tool > MCP server > custom HTTP tool > sandbox/browser use.

### Local tool calling (SDK only)

Tools that run **client-side**, invoked through the SDK rather than in Runtype. The LLM issues a tool call; the SDK on your client picks it up; the tool runs locally; the result goes back through Runtype.

Two flavors:

- **Browser-side** (Persona context): tools call browser APIs — read HTML, navigate, access front-end state.
- **Server-side** (Python/TS SDK on your server): tools run on your infrastructure, can call local AI models, can access data you don't want passing through Runtype.

Combined with hidden parameters (below), this is the security architecture for products where the LLM orchestrates operations on data it shouldn't see.

### Hidden parameters

Every tool parameter can be marked hidden from the LLM. The model sees the tool's shape minus those parameters; the SDK fills them at invocation time (typically with authenticated request context, tenant info, user-scoped credentials, etc.).

Pattern: the LLM sees `lookup_orders(filter)` and decides to call it. Hidden parameters add `{ user_id, tenant_id, auth_token }` that the model never sees in its context window.

## Capability

A capability is just "an agent or flow exposed inside a product." It's the unit a surface invokes.

The dashboard sometimes labels these "capabilities"; the API often calls them "agents and flows." Same concept.

Tools: `add_product_capability`, `remove_product_capability`. Surfaces reference them via `add_surface_item`.

### The many-to-many shape

Capabilities and surfaces are **many-to-many**. Concrete examples:

- One agent exposed across three surfaces (Slack, email, web chat) — same agent, three surfaces.
- Three agents exposed on one MCP surface — three MCP tools auto-generated.
- Three agents exposed on one web chat surface — Runtype provisions an orchestrator (see below).
- A flow exposed as both a REST endpoint and an MCP tool simultaneously.

### Auto-generated REST and MCP APIs

When you bind capabilities to a `mcp` or `api` surface, the platform **automatically generates** endpoints (for REST) or tools (for MCP) from each capability. You pick the auth scheme. Hosted URL. Done.

You're not coding API endpoints; you're declaring which capabilities go on which surface.

### The orchestrator (when multiple capabilities → one conversational surface)

When **more than one capability** is connected to a conversational surface (`chat`, `slack`, `telegram`, `discord`, `email`, etc.), Runtype **automatically provisions an orchestrator agent**. It decides which capability handles each incoming message.

Defaults:

- Inexpensive fast model (because routing at 10-20s defeats the purpose).
- Minimum data over the wire — usually just a short label per capability.
- Alphabetical labels (A, B, C…) for the route options.

Overridable: model, system prompt, routing logic. **Run a product eval on the orchestrator** to compare routing strategies before launch.

Practical implication: you don't need to write your own "router agent." Add the capabilities, let the orchestrator route.

## Surface

How clients (humans or machines) reach into a product. ~15 types — see `surfaces.md` for the full trait matrix.

Each surface has:

- A **type** (`chat`, `slack`, `webhook`, `api`, `mcp`, `schedule`, etc.)
- **Traits** the platform enforces: streaming behavior, markdown dialect, max response length, reasoning visibility, etc.
- A **behavior config** specific to the type
- Optional **surface keys** for authentication (clients use these)
- For Persona: **client tokens** issued via `create_client_token`
- For hosted pages: product-level `HostedPageBehavior` and per-capability
  `HostedPagePresentation` in `runtype://types/surface-configs`

Lifecycle: `create_surface` → `add_surface_item` (wire a capability in) → `update_surface` / `delete_surface`. Slack-specific: `install_slack_integration` for OAuth.

## Record

Runtype's built-in record store. Free-form data with vector-search.

Shape:

- `id` (auto), `type` (table-like), `name` (unique within type), `metadata` (JSON), `createdAt`, `updatedAt`
- Optional embedding for vector search

The right mental model: **records are correlation keys plus agent memory**, not a full business database. The source of truth for user/business data should live in the user's existing systems; records hold the small bits Runtype needs to correlate and remember.

The simplest useful pattern: give an agent record read/write/update tools. That's how the agent "remembers" what users asked it to do.

Operations: `create_record`, `update_record`, `get_record`, `list_records`, `bulk_edit_records`, `bulk_delete_records`. Flow steps: `retrieve-record`, `upsert-record`, `update-record`. Per-record execution data: `get_record_results`, `get_record_step_results`, `get_record_costs`. Vector: `generate-embedding`, `store-vector`, `vector-search` flow steps.

Filtering supports complex queries: contains/equals on metadata fields, group ANDs/ORs, filter on top-level columns. Test filters in a flow first (you can run iteratively), then move to a schedule with the same filter.

## Schedule

Cron or one-time trigger.

Shape: `target` (`{ type: "flow"|"agent", id }`), `trigger` (cron / one-time), `input`, `enabled`.

For flows: standard "call function on schedule." For agents: the trigger looks like a message being pushed into a conversation — useful for **heartbeat patterns** ("every morning, check the todo list and decide what to do"). Schedules can also fan out as a batch over all records of a particular type.

Lifecycle: `create_schedule`, `update_schedule`, `delete_schedule`, `pause_schedule` / `resume_schedule`, `run_schedule_now` (manual trigger), `list_schedule_runs`.

## Eval

Multi-variate testing for AI products.

Eval at the **surface level (product eval)** when you can — it measures what users actually experience, including orchestration and surface-specific formatting. Per-agent evals are useful for tuning a single agent in isolation but miss the integration.

Variables to test:

- Model choice
- System prompt variants
- Tool set differences
- Different routing strategies (if there's an orchestrator)
- Different fallback configurations

Eval batches run a flow or agent over a record set. Results compare across runs.

Lifecycle: `submit_eval`, `get_eval_results`, `compare_eval`, `compare_eval_record`, `analyze_eval_steps`, `get_eval_group`, `list_eval_batches`.

Evals can also run from your own code (via REST / SDK) — useful for CI/CD or eval harnesses that aren't tied to Runtype.

## Secrets

Multi-tenant secret store with envelope encryption (workspace KEK in Cloudflare Secrets Store wraps per-tenant DEKs in D1 with AES-KW).

Reference syntax — same everywhere (tool configs, FPO templates, runtime): `{{secret:KEY}}` — **singular `secret`, colon separator, UPPER_CASE key**. Example: `"Authorization": "Bearer {{secret:STRIPE_API_KEY}}"`.

Two adjacent syntaxes that look similar but are different:

- `{{secrets:KEY}}` — **plural with colon is invalid**. The resolver rejects it.
- `{{secrets.key}}` — plural with **dot** is a different system entirely: per-request dispatch-scoped values (passed in at dispatch time), not managed secrets.

**Always redacted in logs at every level.** If a value matches a known secret, it's stripped from log output across the platform.

Lifecycle: `create_secret`, `list_secrets`, `get_secret` (metadata only), `update_secret`, `delete_secret`, `check_secrets` (bulk existence check).

### Pending-secret pattern (for product setup and distribution)

Best practice for setting up a product:

1. Declare the tool's secret needs in `auth.secrets`.
2. Reference them in tool config as `{{secret:KEY}}` — same syntax in stored tool configs and in FPO templates.
3. Don't fill in the secret values yet — leave them pending.
4. The user (or the product's installer) fills them in via the intake flow.

This means the product architecture is set up completely without anyone needing the credential values in hand. Secrets never end up in product records or template files.

## Conversation

Multi-turn agent state.

Operations: `create_conversation`, `get_conversation`, `update_conversation` (title, model, system prompt, metadata, messages), `delete_conversation`, `list_conversations`, `trace_conversation`.

Conversations attach to surfaces with `threadModel: "threaded"` or `"reply_chain"` (Slack, Discord, email). For `flat` surfaces, each invocation is typically a new conversation unless input wires it to an existing one.

## External and federated agents (A2A, cloud-managed)

Runtype can federate **external agents** into a product as capabilities:

- **A2A agents** — external agents that speak the Agent-to-Agent protocol. Register their skills, mix them with native Runtype agents in the same product, expose the combined surface set to users.
- **Cloud-managed agents** — externally hosted agents registered as capabilities. The agent lives outside Runtype; Runtype routes traffic to it.

Why this matters:

- **Incremental migration**: if you have an existing agent in another framework (CrewAI, custom), expose it as A2A and federate it into Runtype to get the surface delivery layer (Slack/email/SMS/etc.) without rewriting.
- **Best tool for the job**: use specialized frameworks (CrewAI is mentioned as goal-oriented and great for that) for sub-tasks, while Runtype owns the product personality and the surface delivery.

The execution engine routes intelligently across native + federated capabilities. From the user's perspective, it's one product.

## Persona client tokens

For the embedded chat widget, `chat` surfaces use browser-safe `clientToken`s created with `create_client_token`. These tokens are public, scoped to specific agents or flows, revocable, and can be constrained with origin and rate-limit settings.

Lifecycle: `create_client_token`, `get_client_token`, `list_client_tokens`, `regenerate_client_token`, `delete_client_token`.

Generate embed code via `generate_persona_embed_code`. Theme reference via `get_persona_theme_reference`.

See `persona-widget.md` for details.
