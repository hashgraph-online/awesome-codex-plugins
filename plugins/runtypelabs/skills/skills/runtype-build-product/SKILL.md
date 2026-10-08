---
name: runtype-build-product
description: 'Build, deploy, validate, or modify Runtype-hosted AI products, agents, flows, tools, surfaces, schedules, and eval suites, including from example templates.'
user-invocable: true
argument-hint: '[product idea or build task]'
---

# Runtype Build Product

Use this skill when the user wants to create or materially change a Runtype product.
The Runtype MCP server is the source of truth for schemas, catalogs, and current
platform rules.

## Prerequisites

If the Runtype MCP tools are not available, run `runtype install-mcp` for the current
agent harness. Until the tools appear, call them through the CLI with `runtype mcp tools`
and `runtype mcp call <tool>`. For sign-in and account setup, use the `runtype` skill.

## Required first calls

Before designing or creating resources:

- Product build: `get_build_instructions(task="build-product", description=...)`.
- Flow build: `get_build_instructions(task="generate-flow", description=..., name=...)`.
- Capability scoping: `get_build_instructions(task="explain-capabilities")`.

For a product build, pass `focus` as a comma-separated list when the product clearly
needs one of these areas: `commerce`, `embed`, `subagents`, `skills`, `search`, or
`retrieval`. The response then includes those full guides instead of pointers to them.

Then fetch only the `get_platform_documentation` topics the task needs:

| Need                                        | Topics                                                                                                            |
| ------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Product shape (FPO, the product definition) | `product-schema`, `types-fpo`, `types-fpo-template`                                                               |
| Flow step configs                           | `flow-step-types`, `types-flow-steps`                                                                             |
| Delivery and embeds                         | `surface-types`, `types-surface-configs`, `persona-embed`                                                         |
| Slack workspace connection                  | `slack-setup`                                                                                                     |
| Tools and credentials                       | `builtin-tools`, `orthogonal-tools`, `external-tools`; pass `vendor` instead of a topic for one Orthogonal vendor |
| Models                                      | `models` plus the account's `list_model_configs`                                                                  |
| Agent that runs outside Runtype             | `external-agents`, or the `runtype-external-agents` skill                                                         |
| Validation or go-live blockers              | `validation-errors`, `setup-readiness`                                                                            |

The build instructions point to deeper topics, such as evals, when the task needs them.
Do not fetch every catalog in advance, and do not read the same topic again as a resource.

## Design policy

Answer these questions before building:

- Who is the product for: personal use, an internal team, external customers, machines,
  or other agents?
- Where do users work: website chat, Slack, email, SMS, messaging apps, webhook, API, MCP,
  schedule, or A2A?
- What is the capability: a new agent, a new flow, an existing agent or flow, or an agent
  that runs outside Runtype?
- What tools and state does it need? Options are built-in tools, Orthogonal tools (paid
  third-party APIs from the Orthogonal catalog), MCP servers, external HTTP tools, custom
  code, local tools that run in the caller's own code through the SDK, WebMCP page tools,
  records, and secrets.

Start with an agent unless the work is a fixed sequence. Use flows for deterministic
pipelines, indexing, batch processing, artifact rendering, and high-volume steps that
must be fast and cheap. Split large jobs into subagents or several capabilities instead
of one long prompt.

For commerce products, check UCP support when a merchant domain is known, summarize the
finding, and ask whether to use UCP or the traditional commerce path before you continue.

## Build loop

1. Check for a ready-made example. If the request matches a gallery example, or the user
   gives an example or `/now` link, call `list_example_templates` and then
   `create_product_from_example` with one of `slug`, `session`, or `url`. If required
   variables are missing, the tool creates nothing and returns the variable specs. Ask the
   user for the values and call it again. The example creates the product and its
   resources, so skip to reading `get_product_setup` in step 6, then test in step 7.
2. Discover only the account state the task needs.
   - Call `get_me`, `list_products`, `list_agents`, `list_flows`, `list_tools`,
     `list_model_configs`, and, for an existing product, `list_surfaces`.
   - `list_products`, `list_agents`, `list_flows`, and `list_tools` return compact string
     previews by default. Keep that shape for discovery. Pass `view: "full"` only when you
     need complete strings for every row.
   - Use `agent_type` to narrow `list_agents`. Call the matching `get_*` tool for one
     resource's full configuration.
3. Pick surfaces from the live `surface-types` docs. `messaging` is the generic
   multi-channel surface. Prefer a dedicated surface such as
   `slack`, `email`, or `sms` when you need channel-specific setup or formatting. For
   browser-side WebMCP tools, use a `chat` surface with `behavior.webmcp`, not an `mcp`
   surface. For WebMCP details and client-side tools outside the Persona widget, use the
   `runtype-persona` skill.
4. Choose tools in this order: built-in tools, then Orthogonal tools, then MCP servers,
   then external HTTP or custom JavaScript tools.
5. Validate before creating. Use `validate_product`, `validate_flow`,
   `validate_product_flow`, `validate_product_agent`, `validate_product_surface`,
   `validate_product_tool`, and `validate_code` for custom JavaScript or transform code.
   Require `valid: true` with no errors. Fix only the reported fields, not the whole
   definition.
6. Create the resources.
   - `create_product` creates an empty product. It does not import an FPO definition.
   - Create the agents, flows, and tools. Before `create_tool` for a custom tool (an
     `external` HTTP tool, `custom` code, or a flow exposed as a tool), apply the
     `tool-design` skill checklist. If that skill is not installed, it is public at
     `https://github.com/runtypelabs/skills/tree/main/skills/tool-design`.
   - Call `add_product_capability` for each capability, `create_surface` for each channel,
     and `add_surface_item` to route capabilities to each surface. Use the returned IDs.
     `create_surface` does not accept every surface type; check its schema. For
     `imessage`, use the REST endpoint `POST /v1/products/{id}/surfaces`.
   - Create schedules or credentials only when the requested delivery needs them.
   - Read `get_product_setup` before testing integrations. Complete authorized setup, or
     return the remaining human-action links. A bare flow does not need product setup.
7. Test at the user-facing layer.
   - Use `execute_agent`, `dispatch`, `execute_tool`, `run_flow`, `submit_batch`,
     `trace_execution`, and `trace_conversation` as appropriate.
   - A direct `execute_agent` run does not prove surface routing or formatting. For
     `telegram`, `slack`, `sms`, and `imessage` surfaces, use `test_surface` to check
     formatting and message chunking without delivering anything. For a chat widget,
     create a client token with `create_client_token` and generate the snippet with
     `generate_persona_embed_code`.
   - Use fixtures or sandbox targets for side effects. Do not send live messages, charge
     money, or turn on recurring work only to run a smoke test.
8. Add a graded eval suite for any agent or flow the user will run repeatedly. Create it
   with `create_eval_suite`, add realistic cases with `add_eval_cases`, and run it with
   `run_eval_suite`. Run it again after each prompt, step, or tool change, and pass
   `model_override` to compare models. Turn a real failed agent run into a case with
   `add_eval_case_from_execution`. `submit_eval` runs an ungraded, one-off comparison.
9. Report the results. Give validation, setup readiness, tested behavior, and untested
   paths separately. Share resource IDs and dashboard links. If readiness is
   `needs_setup`, say that the product is built but setup remains, and give the user the
   checklist. Create a surface key only when the surface requires one, and never print it.

## If something fails

- Validation error (400): correct the reported fields. Do not regenerate the whole
  object.
- Not found (404): check the ID, the account, and whether the feature is available. A 404
  does not prove that the resource was deleted.
- Execution error: inspect the trace, fix the named step or config, validate again, and
  test again safely. Do not retry a write that is not safe to repeat after an unclear
  timeout.
- Missing secret, surface not installed, or integration error: call `get_product_setup`
  or `get_surface_setup` before you guess.
- If the same error remains after one targeted fix, inspect the schema or report the
  blocker. Do not retry unchanged.

## Guardrails

- Never invent schemas or model IDs. Fetch the docs and the account's model configs.
- Set an explicit, enabled model on every agent and prompt step. Choose it from
  `list_model_configs` and the `models` topic. Never leave it to account defaults.
- Never ask for secret values in chat, and never put credentials inline. Reference
  secrets as `{{secret:KEY}}` and call `check_secrets` for missing keys. Give the user the
  dashboard link from `get_secret_intake_manifest` or `get_product_setup`.
- Read before you update. Keep fields the user did not ask to change.
- Check update behavior in the live schema. When you replace a nested object, keep its
  other fields. `update_flow.steps` replaces the entire step list.
- Surface-level evals catch routing and formatting issues that per-agent evals miss.
- If the product needs platform rules this skill does not cover, fetch
  `platform-catalog` and the focused topic it points to.

If the `runtype` skill is installed, its references hold more background. The live MCP
docs take precedence.
