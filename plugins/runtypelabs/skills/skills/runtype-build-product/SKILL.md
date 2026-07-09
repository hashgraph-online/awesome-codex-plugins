---
name: runtype-build-product
description: >-
  Use when building, designing, validating, or deploying Runtype AI products with agents,
  flows, tools, surfaces, records, secrets, schedules, evals, orchestration, webhooks,
  Slack/email/SMS/Telegram/Discord/WhatsApp/iMessage/messaging/chat/API/MCP/A2A/hosted-page
  surfaces, commerce tools, agent skills, or hosted product generation. Always fetch current MCP build
  instructions before creating resources.
user-invocable: true
argument-hint: '[product idea or build task]'
---

# Runtype Build Product

Use this skill when the user wants to create or materially change a Runtype product.
MCP is the source of truth for schemas, catalogs, and current platform rules.

## Required First Calls

Before designing or creating resources:

- Product build: `get_build_instructions(task="build-product", description=...)`.
- Flow build: `get_build_instructions(task="generate-flow", description=..., name=...)`.
- Capability scoping: `get_build_instructions(task="explain-capabilities")`.

Then fetch only the docs needed for the current design:

- `get_platform_documentation(topic="surface-types")`
- `get_platform_documentation(topic="flow-step-types")`
- `get_platform_documentation(topic="product-schema")`
- `get_platform_documentation(topic="types-fpo")`
- `get_platform_documentation(topic="types-flow-steps")`
- `get_platform_documentation(topic="types-entities")`
- `get_platform_documentation(topic="types-surface-configs")`
- `get_platform_documentation(topic="builtin-tools")`
- `get_platform_documentation(topic="agent-skills")`
- `get_platform_documentation(topic="orthogonal-tools")`
- `get_platform_documentation(topic="external-tools")`
- `get_platform_documentation(topic="models")`
- `get_platform_documentation(topic="dashboard-links")`
- `get_platform_documentation(topic="mock-ecommerce")`
- `get_platform_documentation(topic="persona-embed")`
- `get_platform_documentation(topic="persona-fullscreen-assistant")`
- `get_platform_documentation(topic="sdk-reference")`

Also read MCP resources directly when available for richer coverage:
`runtype://types/fpo-template`, `runtype://guide/subagent-delegation`,
`runtype://catalog/skills`, `runtype://catalog/provider-native-search`, and
`runtype://catalog/ucp-commerce`.

## Design Policy

Answer these before building:

- Who is the product for: personal, internal team, external customers, machines, or agents?
- Where do users work: website chat, Slack, email, SMS, messaging apps, webhook, API, MCP,
  schedule, or A2A?
- What is the capability: agent, flow, existing agent, existing flow, or external agent?
- What tools and state does it need: built-ins, Orthogonal tools, MCP servers, external
  HTTP tools, custom code, local SDK tools, WebMCP page tools, records, secrets?

Start with an agent unless the work is a fixed sequence. Use flows for deterministic
pipelines, indexing, batch processing, artifact rendering, and hot paths that should be
cheap and fast. Use subagents or multiple capabilities instead of one giant prompt.

For commerce products, check UCP support when a merchant domain is known, summarize the
finding, and ask whether to use UCP or the traditional commerce path before proceeding.

## Build Loop

1. Discover account state with `get_me`, `list_products`, `list_agents`, `list_flows`,
   `list_tools`, `list_model_configs`, and product-scoped `list_surfaces` when relevant.
2. Pick surfaces from the live `surface-types` docs. Include `messaging` as the generic
   multi-channel surface, and prefer dedicated surfaces when channel constraints matter.
   For browser-side WebMCP tools, use a `chat` surface with `behavior.webmcp` rather
   than an `mcp` surface. For the WebMCP mechanics and the advanced non-Persona
   raw-`/v1/dispatch` `clientTools[]` path, use `runtype-persona`.
3. Prefer first-party/built-in tools, then Orthogonal tools, then MCP servers, then custom
   HTTP/JS tools.
4. Validate before creating: `validate_product`, `validate_flow`, `validate_product_flow`,
   `validate_product_agent`, `validate_product_surface`, `validate_product_tool`, and
   `validate_code` for custom JS or transform code.
5. Create in a reviewable order: tools/secrets, agents/flows, product, capabilities,
   surfaces, surface items, schedules, client tokens, and evals.
6. Test at the user-facing layer. Use `execute_agent`, `dispatch`, `execute_tool`,
   `run_flow`, `submit_batch`, `submit_eval`, `trace_execution`, and
   `trace_conversation` as appropriate.

## Guardrails

- Never invent schemas or model IDs; fetch docs and model configs.
- Do not inline credentials. Use `{{secret:KEY}}` and secret intake.
- Read before update; preserve fields the user did not ask to change.
- Treat `update_agent` as wholesale replacement unless live docs say otherwise.
- Surface-level evals catch orchestration and formatting issues that per-agent evals miss.
- If a product needs deeper or newer platform rules than this skill names, fetch
  `platform-catalog` and focused direct resources instead of appending feature
  notes here.

If the umbrella `runtype` skill is installed alongside this focused skill, its durable
references provide deeper fallback notes. This skill must still work when installed by
itself; prefer live MCP docs over local sibling files.
