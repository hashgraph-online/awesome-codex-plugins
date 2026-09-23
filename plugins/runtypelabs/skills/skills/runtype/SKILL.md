---
name: runtype
description: 'Scope a Runtype project or set up platform access; route implementation to the relevant Runtype skill.'
user-invocable: true
argument-hint: '[Runtype goal or setup question]'
---

# Runtype

Runtype is a platform for shipping AI products: agents, flows, tools, surfaces, records,
schedules, evals, and product templates. Use this skill as the entry point when the user
is asking about Runtype broadly or needs help connecting an agent to the platform.

This skill is intentionally a router. For implementation work, switch to the narrower
skill that matches the job.

## First Move

If the Runtype MCP server is available, use it as the live source of truth before giving
schema, catalog, or creation guidance:

- `get_build_instructions(task="explain-capabilities")` for scoping.
- `get_build_instructions(task="build-product")` before product construction.
- `get_build_instructions(task="generate-flow")` before flow construction.
- `get_platform_documentation(topic=...)` for schemas, surface traits, tool catalogs,
  SDK docs, Persona embed docs, dashboard links, and type definitions.

If MCP is not connected, check `runtype auth status` for stored login/signup state.
If `RUNTYPE_API_KEY` is configured, verify it with `runtype auth whoami --no-tty` instead;
`status` ignores environment credentials. Reuse valid authentication before resuming
a stored pending signup using its `next` command. For a new account,
use `runtype auth register --email <email>` then `runtype auth verify <code>` — both work
without a TTY or browser. Do not run browser-only `runtype auth login` from a coding harness.

Run `runtype install-mcp` for the current harness, follow its action/restart status,
and keep working through the CLI while MCP is unavailable (`runtype mcp tools` and
`runtype mcp call <tool>` bridge the hosted tools). Use MCP once its tools actually appear;
configuration alone does not prove the connection is active.

For installation or auth recovery, read the public setup script at
`https://runtype.ai/.well-known/agent.md`; the raw auth protocol is at
`https://runtype.com/auth.md`. Existing-account credentials must be configured privately,
not pasted into the conversation. Only install or sign up when the user requests setup.

## Route To Focused Skills

Use this routing table instead of loading every Runtype detail into context:

| User intent                                                                                                                                                                                        | Use                       |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| Build, deploy, or validate a product with agents, flows, tools, surfaces, records, secrets, schedules, or evals                                                                                    | `runtype-build-product`   |
| Inspect or modify a live account, debug failures, read logs/traces, compare evals, manage resources                                                                                                | `runtype-admin`           |
| Embed or theme a Persona chat widget, build fullscreen assistant layouts, use client tokens, or configure WebMCP/browser-side local tools                                                          | `runtype-persona`         |
| Package a product as a distributable FPO template, handle pending secrets, validate import readiness                                                                                               | `runtype-templates`       |
| Use the TypeScript/Python SDK, CLI, Marathon, playbooks, sandboxes, or code-first stored/upsert/virtual workflows                                                                                  | `runtype-sdk-marathon`    |
| Connect an agent that runs outside Runtype (Flue, Cloudflare Agents SDK, Vercel AI SDK, LangChain, custom): send its traces to Runtype, let Runtype call it, capture and improve it from real runs | `runtype-external-agents` |
| Design or review the tools an agent calls (names, schemas, results, errors, idempotency, secrets, bundling), on Runtype or any MCP or function-calling runtime                                     | `tool-design`             |

## Mental Model

- Product: the container the user ships.
- Agent: an LLM with a system prompt and tools. Start here for most interactive products.
- Flow: a deterministic pipeline. Use for fixed sequences, indexing, batch work, and hot
  paths that should be fast and cheap.
- Tool: a typed callable, from built-ins, Orthogonal APIs, MCP servers, external HTTP,
  custom code, local SDK tools, flows, or subagents.
- Surface: where users or machines reach the product, including `chat`, `api`, `mcp`,
  `mcp_code`, `webhook`, `email`, `slack`, `schedule`, `sms`, `imessage`, `discord`,
  `whatsapp`, `telegram`, `messaging`, `a2a`, and `hosted-page`.
- Record: Runtype state and memory. It is not a replacement for the user's business
  database.
- Eval: surface-level or capability-level comparison. Prefer surface/product evals when
  measuring user experience.
- FPO template: the portable distribution format for a product.

When a product has multiple capabilities on one conversational surface, Runtype can
provision an orchestrator that routes each incoming message to the right capability.
Treat surfaces and capabilities as many-to-many.

## Durable References

These local references are fallback context only. Prefer live MCP docs when available.

- `references/primitives.md` for the deeper platform model.
- `references/mcp-tools.md` for MCP tool groups and selection.
- `references/surfaces.md` for surface traits and prompt implications.
- `references/flow-steps.md` for flow step categories and common mistakes.
- `references/persona-widget.md` for Persona embed details.
- `references/fpo-templates.md` for template packaging.
- `references/working-modes.md` for dashboard, MCP, REST, SDK, and on-prem tradeoffs.
- `references/recipes.md` for worked product shapes.

## Do Not Do

- Do not invent payload shapes. Fetch live docs or validate first.
- Do not let this router grow into platform docs. If more detail is needed, fetch
  `get_platform_documentation(topic="platform-catalog")` or a focused topic, then
  read the relevant direct MCP resources when the docs point to them.
- Do not inline secret values. Use `{{secret:KEY}}` and pending-secret intake.
- Do not store all customer data in records; keep the source of truth where it belongs.
- Do not use Runtype for generic one-off LLM chat unless the user wants to ship a
  repeatable product or operational workflow.
