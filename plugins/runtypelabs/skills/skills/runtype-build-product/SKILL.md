---
name: runtype-build-product
description: 'Build or modify Runtype-hosted AI products, agents, flows, and surfaces using current platform instructions.'
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

Then fetch only relevant `get_platform_documentation` topics:

| Need                           | Topics                                                                    |
| ------------------------------ | ------------------------------------------------------------------------- |
| Product/FPO shape              | `product-schema`, `types-fpo`, `types-fpo-template`                       |
| Flow step configs              | `flow-step-types`, `types-flow-steps`                                     |
| Delivery and embeds            | `surface-types`, `types-surface-configs`, `persona-embed`                 |
| Tools and credentials          | `builtin-tools`, `external-tools`; use `vendor` for one Orthogonal vendor |
| Models                         | `models` plus account `list_model_configs`                                |
| Validation or go-live blockers | `validation-errors`, `setup-readiness`                                    |

Build instructions route deeper subjects such as skills, subagents, retrieval, commerce,
and evals. Do not fetch every catalog in advance or read the same topic again as a resource.

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

When the product needs a custom tool (an `external` HTTP tool, `custom` code, or a
flow exposed as a tool), design it with the `tool-design` skill family before
`create_tool`: it covers the model-facing description and schema, result shape, error
classes, idempotency, secrets, and the save-time validator codes. If that skill is not
installed, the same checklist is public at
`https://github.com/runtypelabs/skills/tree/main/skills/tool-design`.

For commerce products, check UCP support when a merchant domain is known, summarize the
finding, and ask whether to use UCP or the traditional commerce path before proceeding.

## Build Loop

1. Discover only the account state the task needs with `get_me`, `list_products`, `list_agents`, `list_flows`,
   `list_tools`, `list_model_configs`, and product-scoped `list_surfaces` when relevant.
   These large inventory tools use compact string previews by default; keep that shape
   for discovery, use `agent_type` when narrowing agents, and call the matching `get_*`
   tool for complete configuration. Request `view: "full"` only when complete strings
   are needed for every row.
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
5. `create_product` creates an empty container, not an FPO import. Create the required
   agents/flows and tools, attach capabilities and surfaces using returned IDs, and create
   schedules or credentials only when requested delivery requires them. Read
   `get_product_setup` before testing integrations; complete authorized setup or return
   the remaining human-action links. A bare flow does not need product setup.
6. Test at the user-facing layer. Use `execute_agent`, `dispatch`, `execute_tool`,
   `run_flow`, `submit_batch`, `submit_eval`, `trace_execution`, and
   `trace_conversation` as appropriate. Use fixtures/sandbox targets for side effects; do
   not send live messages, charge money, or activate recurring work merely to smoke-test.
   Report validation, setup readiness, tested behavior, and untested paths separately.

## Guardrails

- Never invent schemas or model IDs; fetch docs and model configs.
- Do not inline credentials. Use `{{secret:KEY}}` and secret intake.
- Read before update; preserve fields the user did not ask to change.
- Check update semantics in the live schema; preserve sibling config fields when replacing
  nested objects. `update_flow.steps` replaces the entire step list.
- Surface-level evals catch orchestration and formatting issues that per-agent evals miss.
- If a product needs deeper or newer platform rules than this skill names, fetch
  `platform-catalog` and focused direct resources instead of appending feature
  notes here.

If the umbrella `runtype` skill is installed alongside this focused skill, its durable
references provide deeper fallback notes. This skill must still work when installed by
itself; prefer live MCP docs over local sibling files.
