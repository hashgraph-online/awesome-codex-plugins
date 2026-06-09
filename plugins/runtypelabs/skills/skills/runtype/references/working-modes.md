# Working Modes & Deployment

Runtype supports a range of ways to build and deploy. They all drive the same underlying config — there's no separate "API-first vs UI-first" code path. The choice is about workflow, team practices, and constraints. Read this when helping a user pick how to work.
Prefer live `sdk-reference`, `platform-catalog`, and Code Mode `search` when available.

## Contents

- [The three authoring modes (equivalent)](#the-three-authoring-modes-equivalent)
- [The SDK story (TypeScript & Python)](#the-sdk-story-typescript--python)
- [What the SDK unlocks beyond authoring](#what-the-sdk-unlocks-beyond-authoring)
- [On-prem deployment (enterprise)](#on-prem-deployment-enterprise)
- [Picking a mode](#picking-a-mode)
- [Anti-patterns](#anti-patterns)

## The three authoring modes (equivalent)

These three drive the same database; mix freely.

### Dashboard (`use.runtype.com`)

Full SaaS UI: visual product designer, playground, log viewer, eval interface, surface configuration, schedule management, secret intake.

Best for:

- First-time exploration. The playground is the lowest-friction way to see what a model/tool combination does. Sessions can be saved as agents or flows directly.
- Visual product design where seeing the capabilities-to-surfaces graph helps.
- Eval inspection — the comparison views are useful.
- Non-technical or semi-technical users.
- Inspecting logs and running ad-hoc tests.

### MCP server (`https://api.runtype.com/v1/mcp/protocol`)

For driving Runtype from inside an LLM agent harness (Claude Code, Cursor, Claude Desktop, any MCP client). 100+ tools cover the main product-building and operations workflows exposed by the platform.

Best for:

- Building with an AI pair. The agent has full read/write access to your workspace.
- "Use Claude Code to check Runtype logs, change an agent's prompt, run an eval, decide what to do next" — that workflow.
- Bringing context from elsewhere (a doc, a codebase, a Granola note) into the build session.

Setup: `mcpServers.runtype.url = "https://api.runtype.com/v1/mcp/protocol"`. OAuth on first call.

### REST API

Broad API coverage for using Runtype from any code.

Best for:

- Embedding Runtype-driven AI features in an existing product.
- CI/CD: programmatic deployment, eval-as-test, automated migrations.
- Integrations from internal systems.

Pair with the SDKs (next section) for typed clients and a better developer experience.

## The SDK story (TypeScript & Python)

The Runtype SDKs let you define agents and flows **in code, in source control**. Three modes within that:

### Stored

Created in Runtype like any other agent or flow. The SDK is just a typed authoring path; behavior at runtime is identical.

### Upsert on execute

Stored in Runtype, but overwritten every time you execute from your code. Your code is the source of truth; the Runtype database stays in sync.

Useful for:

- Teams who want their agent definitions in Git but still want the Runtype dashboard for inspection/eval.
- CI/CD-driven deployment: push a code change, the next execution updates Runtype's copy.

### Virtual

Not persisted in Runtype at all. The flow or agent definition is sent over the wire on each execution.

Useful for:

- Tests and one-offs that shouldn't pollute the dashboard.
- Hard privacy or compliance requirements where the definition itself shouldn't be stored.
- Per-tenant customization in a multi-tenant product where each tenant gets a slightly different agent.

## What the SDK unlocks beyond authoring

The SDK path enables capabilities the dashboard path can't:

### Local tool calling

Tools that are **invoked client-side**, not inside Runtype. The LLM still issues the tool-call message; Runtype routes it to the SDK; the SDK invokes the tool in your environment; the result goes back to the LLM through Runtype.

Two flavors:

- **Browser-side / WebMCP** (Persona widget context). Tools are registered on
  `document.modelContext`, snapshotted by Persona, admitted by the chat
  surface's `behavior.webmcp` policy, and executed in the user's page. Use for
  browser APIs, page HTML, navigation, and front-end state.
- **Server-side** (Python/TS SDK on your server). Tools run on your infrastructure. Useful for: calling internal services without exposing them via Runtype, hitting local AI models, working with sensitive data you don't want passing through Runtype.

### Hidden parameters

Every tool parameter can be marked **hidden from the LLM**. The model doesn't see the parameter exists; the SDK fills it in at invocation time.

Combined with local tools, this is how you let an LLM orchestrate operations on sensitive data without ever putting that data into the model's context window. The LLM sees "lookup_user_email(user_id)" and the hidden parameter is the authenticated request context.

This pattern is the current best practice for AI-product security. Runtype bakes it in.

## On-prem deployment (enterprise)

For large teams with their own infrastructure, compliance constraints, or data-residency requirements.

The platform is built as a **library plus adapters**. The library is the agent/flow execution engine; adapters provide surfaces, integrations, logging sinks. Runtype's hosted offering uses Runtype's own adapters; on-prem, you can pick which adapters to use, replace them, or build new ones.

What on-prem unlocks:

- Production artifacts run on your AWS / GCP / on-prem infrastructure.
- Connect to your own model providers — your own API keys, your own gateway, even local models.
- Standalone deployments can run silent by omitting or disabling telemetry. If telemetry is enabled, configure the endpoint and API key explicitly.
- Compliance-friendly: data residency, audit, key management can all be self-managed.

The expected **graduation pattern**:

1. **Beta**: use the hosted Runtype runtime with all built-in adapters. Move fast, validate.
2. **Production**: opt into your own adapters where they matter — typically a custom logging sink, a custom secret store, a custom surface that integrates with internal systems.
3. **Long-term**: replace adapters as you outgrow defaults, while keeping the rest.

You don't have to pick all-or-nothing.

## Picking a mode

| Situation                                                         | Mode                            |
| ----------------------------------------------------------------- | ------------------------------- |
| Exploring what's possible                                         | Dashboard + playground          |
| Building an AI agent with Claude Code                             | MCP server                      |
| Embedding AI into an existing app                                 | REST API + SDK                  |
| Multi-tenant product where each customer's config differs         | SDK with virtual flows          |
| Compliance-sensitive customer who can't have data leave their VPC | On-prem (enterprise)            |
| Source of truth must be Git                                       | SDK with upsert mode            |
| Quick experiment that shouldn't show up in the dashboard          | SDK with virtual flows          |
| Need a tool to access browser DOM in the chat widget              | Persona WebMCP page tool        |
| Need a tool to call internal services on your server              | SDK + local tool (server-side)  |
| LLM should orchestrate but can't see sensitive data               | Hidden parameters + local tools |

## Anti-patterns

- **Reaching for SDK virtual flows for everything.** Use stored/upsert mode unless you have a reason. The dashboard's eval and logging are easier to use when entities are persisted.
- **Storing the agent's full conversation history in Runtype records.** Records are for correlation and small bits of memory. For long conversations, lean on conversation primitives, not the record store.
- **Treating REST API and MCP server as different platforms.** They're the same backend. The MCP server is just a translation layer that exposes the REST API to LLMs.
- **Going to on-prem too early.** Hosted is faster to iterate. Move on-prem when a customer requires it, not preemptively.
