---
name: runtype
description: 'Scope a Runtype project or set up platform access; route implementation to the relevant Runtype skill.'
user-invocable: true
argument-hint: '[Runtype goal or setup question]'
---

# Runtype

Runtype is a platform for shipping AI products: agents, flows, tools, surfaces, records,
schedules, evals, and product templates. Use this skill as the entry point when the user
asks about Runtype broadly or needs help connecting an agent to the platform.

This skill is a router. For implementation work, switch to the narrower skill that
matches the job.

## Start with live context

**If the Runtype MCP tools are available**, use them as the source of truth before you
give schema, catalog, or creation guidance:

- `get_build_instructions(task="explain-capabilities")` for scoping.
- `get_build_instructions(task="build-product")` before you build a product.
- `get_build_instructions(task="generate-flow")` before you build a flow.
- `get_platform_documentation(topic=...)` for schemas, surface traits, tool catalogs,
  SDK docs, Persona embed docs, dashboard links, and type definitions.
- `search_documentation(query=...)` for how-to and conceptual questions. It returns an
  answer with citations to doc pages.

**If the MCP tools are not available**, check for existing authentication:

- Run `runtype auth status` for a stored login or a pending signup.
- If `RUNTYPE_API_KEY` is set, verify it with `runtype auth whoami --no-tty`. The
  `status` command ignores environment credentials.
- Reuse valid authentication. If a signup is pending, resume it with the `next` command
  that `status` prints.
- If `status` reports `unauthenticated` with a `requestedOrgId`, the directory is linked
  to an organization with no stored login. Do not register a new account: have the user
  log in to that organization privately (`runtype auth login --api-key <key>`), or confirm
  with them before `runtype unlink` if the link is stale.

Keep working through the CLI while MCP is unavailable: `runtype mcp tools` lists the
hosted tools and `runtype mcp call <tool>` runs one. Use MCP after its tools appear in
your session. A written configuration does not prove that the connection is active.

**Only if the user asks for setup**, install or sign up:

- **New account.** Run `runtype auth register --email <email>`, then ask the user for the
  6-digit code from their email and run `runtype auth verify <code>`. Neither command
  needs a TTY or a browser. Until the email is verified, the account is temporary, with
  limited models and quota. If you registered without `--email`, send the code with
  `runtype auth claim <email>`.
- **Existing account.** Have the user set `RUNTYPE_API_KEY` in the environment, or run
  `runtype auth login --api-key <key>` themselves. Credentials must not be pasted into the
  conversation. Do not start the interactive browser login from a coding assistant.
- **A narrower key.** Run
  `runtype api-keys request --name <name> --scopes <list> --reason <text>` with the
  narrowest scopes the task needs. The user approves the request in the dashboard, and the
  CLI writes the key to a local key file. From MCP, call `request_api_key`, keep the
  `codeVerifier` it returns, and redeem the approved request with `claim_api_key`. Its
  default delivery stores the key as a Runtype secret and returns only a `{{secret:KEY}}`
  reference, so the key is never shown in the conversation.
- **MCP.** Run `runtype install-mcp` for the current coding assistant, follow the action
  or restart it reports, then confirm the account with `runtype auth whoami --no-tty`.

For installation or auth recovery, read the public setup script at
`https://runtype.ai/.well-known/agent.md`. The raw auth protocol is at
`https://runtype.com/auth.md`.

## Route to a focused skill

Use this routing table instead of loading every Runtype detail into context:

| User intent                                                                                                                                                                                        | Use                       |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| Build, deploy, or validate a product with agents, flows, tools, surfaces, records, secrets, schedules, evals, or Agent Skills                                                                      | `runtype-build-product`   |
| Inspect or modify a live account, debug failures, read logs/traces, compare evals, manage resources                                                                                                | `runtype-admin`           |
| Embed or theme a Persona chat widget, build fullscreen assistant layouts, use client tokens, or configure WebMCP/browser-side local tools                                                          | `runtype-persona`         |
| Package a product as a distributable FPO template, handle pending secrets, validate import readiness                                                                                               | `runtype-templates`       |
| Use the TypeScript/Python SDK, CLI, Marathon, playbooks, sandboxes, or code-first stored/upsert/virtual workflows                                                                                  | `runtype-sdk-marathon`    |
| Connect an agent that runs outside Runtype (Flue, Cloudflare Agents SDK, Vercel AI SDK, LangChain, custom): send its traces to Runtype, let Runtype call it, capture and improve it from real runs | `runtype-external-agents` |
| Design or review the tools an agent calls (names, schemas, results, errors, idempotency, secrets, bundling), on Runtype or any MCP or function-calling runtime                                     | `tool-design`             |

## Platform concepts

- Product: the container the user ships.
- Agent: an LLM with a system prompt and tools. Start here for most interactive products.
- Flow: a deterministic pipeline. Use for fixed sequences, indexing, batch work, and hot
  paths that should be fast and cheap.
- Tool: a typed callable, from built-ins, Orthogonal APIs, MCP servers, external HTTP,
  custom code, local SDK tools, flows, or subagents.
- Agent Skill: a versioned SKILL.md context bundle bound to a Runtype agent, which loads
  it at run time through a `skill:<slug>` tool. It is a product feature, separate from
  this coding-assistant skill. Read `get_platform_documentation(topic="agent-skills")`.
- Surface: where users or machines reach the product, such as `chat`, `api`, `mcp`,
  `mcp_code`, `webhook`, `email`, `slack`, `schedule`, `sms`, `imessage`, `discord`,
  `whatsapp`, `telegram`, `messaging`, `a2a`, and `hosted-page`. For the current list,
  read `get_platform_documentation(topic="surface-types")`.
- Record: Runtype state and agent memory. Keep the source of truth for data that already
  lives in another system there.
- Eval: a saved set of test cases and graders that scores a flow or agent (an eval suite),
  or a one-time batch that compares variants such as models or prompts. Surface evals in
  the dashboard also cover routing and channel formatting end to end.
- FPO template: the portable distribution format for a product.

When a product has multiple capabilities on one conversational surface, Runtype can
provision an orchestrator that routes each incoming message to the right capability.
Surfaces and capabilities are many-to-many.

## Reference files

These local references are fallback context only. Prefer live MCP docs when available.

- `references/primitives.md` for the deeper platform model.
- `references/mcp-tools.md` for MCP tool groups and selection.
- `references/surfaces.md` for surface traits and prompt implications.
- `references/flow-steps.md` for flow step categories and common mistakes.
- `references/persona-widget.md` for Persona embed details.
- `references/fpo-templates.md` for template packaging.
- `references/working-modes.md` for dashboard, MCP, REST, SDK, and on-prem tradeoffs.
- `references/recipes.md` for worked product shapes.

## Rules

- Do not invent payload shapes. Fetch live docs or validate first.
- Keep this router short. When you need more detail, fetch
  `get_platform_documentation(topic="platform-catalog")` or a focused topic, then read
  the MCP resources that the docs point to.
- Do not inline secret values. Use `{{secret:KEY}}` and pending-secret intake.
- Do not copy a whole customer database into records. Store what Runtype needs to
  correlate and remember.
- Set an explicit, enabled model on every agent and prompt step. Do not rely on account
  defaults.
- Do not report success before you validate (`validate_flow` or `validate_product`) and
  run a safe test (`execute_agent` or `run_flow`). Say which paths you did not test.
- Do not use Runtype for generic one-off LLM chat unless the user wants to ship a
  repeatable product or operational workflow.
