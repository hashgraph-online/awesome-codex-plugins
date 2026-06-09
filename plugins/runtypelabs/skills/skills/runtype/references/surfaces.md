# Surface Types

Every surface has a **type** and carries **traits** that the platform uses to enforce channel-appropriate behavior. When designing a product, pick the surface type first — its traits constrain everything downstream (max response length, streaming, markdown dialect, reasoning visibility).

Prefer live `get_platform_documentation(topic="surface-types")` and `runtype://types/surface-configs` when available. This file is fallback orientation.

Many surfaces carry an `executionHint` that should be appended to the agent's system prompt to enforce formatting. The platform may do this automatically; check before duplicating it manually.

## Contents

- [Trait dimensions](#trait-dimensions)
- [Surface type catalog](#surface-type-catalog)
- [Auto-generated REST and MCP APIs](#auto-generated-rest-and-mcp-apis)
- [The orchestrator (multi-capability conversational surfaces)](#the-orchestrator-multi-capability-conversational-surfaces)
- [Surface-specific auto-registered tools](#surface-specific-auto-registered-tools)
- [Picking a surface](#picking-a-surface)
- [Trait-driven prompt construction](#trait-driven-prompt-construction)

## Trait dimensions

| Trait                 | What it controls                                                                             |
| --------------------- | -------------------------------------------------------------------------------------------- |
| `streaming`           | `required` / `optional` / `none` — whether streaming is supported (and required)             |
| `messagesMutable`     | Whether messages in the thread can be edited after send (Slack, Discord, Telegram)           |
| `deliveryModel`       | `real_time` / `sync` / `async` — how the platform delivers responses                         |
| `mediaSupport`        | `none` / `images` / `rich` — inbound and outbound media                                      |
| `interactiveUI`       | `none` / `generative` / `forms` / `buttons` — interactive UI primitives the channel supports |
| `inboundMediaSupport` | Whether the channel accepts inbound media (images, files)                                    |
| `consumerType`        | `human` / `machine` / `agent` — informs the eval framing                                     |
| `reasoningVisibility` | `pass_through` / `always_strip` — whether `<thinking>` traces are exposed                    |
| `markdownDialect`     | `none` / `markdown` / `mdx` / `mrkdwn` / `html`                                              |
| `threadModel`         | `flat` / `threaded` / `reply_chain`                                                          |
| `senderIdentity`      | `anonymous` / `authenticated` / `verified`                                                   |
| `maxResponseLength`   | Response length budget/cap (chars)                                                           |
| `executionHint`       | A formatting instruction appended to the agent's system prompt                               |

## Surface type catalog

### `chat`

Website widget, support bots, conversational UIs.

- Use cases: support, onboarding, internal tools, FAQ bots
- Streaming: **required**, `mediaSupport: images`, `interactiveUI: generative` (the Persona widget supports rich generative components)
- `reasoningVisibility: pass_through` — reasoning is shown unless config opts out
- `markdownDialect: mdx`
- For the SDK and embed code, use `generate_persona_embed_code` and see `persona-widget.md`
- Optional WebMCP page tools are configured under `behavior.webmcp`. They are
  browser-side tools registered on `document.modelContext`, gated by
  `enabled` plus origin-scoped allow-list rules, and executed by Persona in the
  host page. Keep client-token `allowedOrigins` configured separately for CORS.

### `api`

Programmatic HTTP endpoints for backend integrations.

- Use cases: REST API, webhook consumer, integration endpoint
- Streaming: optional, no media, no UI
- `consumerType: machine`
- Authenticated via surface keys

### `mcp`

AI assistant integration. The agent's tool set becomes the MCP server's tool catalog. Consumed by Cursor, Claude Code, Claude Desktop, etc.

- Use cases: developer tools, code review, doc assistants, DB query helpers
- `consumerType: agent`
- Authenticated

### `mcp_code`

Code Mode MCP server for programmatic agent access — for advanced agent integrations and custom automation scripts.

- Similar to `mcp` but framed for code-mode (where the model generates code that calls tools rather than calling them directly).

### `email`

Email-triggered processing and automated responses.

- Use cases: auto-reply support agent, invoice processor, email-to-task converter
- `deliveryModel: async`, `mediaSupport: rich`, `markdownDialect: html`
- `reasoningVisibility: always_strip` — never leak thinking traces
- `threadModel: reply_chain`
- **Execution hint**: "Respond via email. Write in a professional, organized tone. Use clear paragraphs. Avoid bullet-point overload — prefer flowing prose where appropriate. Don't include reasoning traces, tool call narration, or internal process details."

### `webhook`

Event-driven processing from third-party services. Accepts JSON and form-encoded payloads.

- Use cases: Stripe payment handler, GitHub event processor, Twilio inbound SMS, Shopify order webhook
- Payloads are **never** treated as a Runtype envelope. The full parsed body lands in `payload` in the execution message. Top-level fields are spread into flow inputs so `{{field}}` template variables resolve in `prompt` and `api-call` step bodies.
- `behavior.inputMapping` can rename or deep-pick fields by dot path.
- `behavior.response` returns a static HTTP body — useful for providers that require specific ACK shapes (e.g. empty TwiML for Twilio, 204 for Shopify). When set, the flow fires **async**.
- `consumerType: machine`, `deliveryModel: sync`

### `slack`

Slack bot for team collaboration.

- Use cases: team support, daily standups, alert channel manager
- `mediaSupport: rich`, `interactiveUI: forms`, `markdownDialect: mrkdwn`, `threadModel: threaded`
- `messagesMutable: true` — messages can be edited mid-thread
- `reasoningVisibility: always_strip`, `maxResponseLength: 4000`
- **Execution hint**: "Responding in Slack. Be concise and direct — Slack messages should be scannable. Avoid lengthy prose. No reasoning traces or tool call narration."
- Install via `install_slack_integration`, not `create_surface_key`

### `schedule`

Cron jobs and periodic processing.

- Use cases: daily reports, weekly sync, hourly health check
- `deliveryModel: async`, no media, no UI
- `reasoningVisibility: always_strip`
- Triggered via `create_schedule` + the flow/agent target

### `sms`

SMS messaging — typically via Twilio.

- Use cases: SMS support, reminders, two-way texting, surveys
- `deliveryModel: async`, no media, `markdownDialect: none`, `maxResponseLength: 160`
- **Execution hint**: "Responding via SMS. Be extremely brief — one or two short sentences. Plain text only, no markdown, no lists. No reasoning traces."

### `imessage`

iMessage messaging via Sendblue for Apple ecosystem.

- Use cases: customer support, appointment reminders, rich messaging
- `mediaSupport: images`, `inboundMediaSupport: true`
- `senderIdentity: verified`, `maxResponseLength: 1200`
- **Execution hint** is extensive — covers texting tone, no greetings/closings, lowercase OK, one-emoji-max, multi-bubble formatting via blank lines. Read it in full when configuring an iMessage agent; it's strict.

### `discord`

Discord bot for community engagement.

- Use cases: community FAQ, moderation, welcome bots
- `mediaSupport: rich`, `interactiveUI: buttons`, `markdownDialect: markdown`, `threadModel: threaded`
- `reasoningVisibility: always_strip`
- **Execution hint**: friendly, community-appropriate, markdown OK, concise

### `whatsapp`

WhatsApp Business for customer communication.

- Use cases: support, order updates, scheduling
- `mediaSupport: rich`, `interactiveUI: buttons`, `markdownDialect: none`, `maxResponseLength: 1024`
- `senderIdentity: verified`
- **Execution hint**: concise, conversational, plain text. No reasoning traces.

### `telegram`

Telegram bot for messaging.

- Use cases: support, notifications, group admin
- `mediaSupport: rich`, `interactiveUI: buttons`, `markdownDialect: html`, `maxResponseLength: 4096`
- `messagesMutable: true`, `threadModel: flat`
- **Execution hint**: clear and concise, no unnecessary verbosity, no reasoning traces

### `messaging`

Generic messaging surface for multi-channel delivery.

- Use cases: unified support, channel-agnostic bots, internal routing across messaging providers
- `deliveryModel: real_time`, `mediaSupport: images`, `markdownDialect: none`
- Use when live docs expose a generic messaging integration for the target workflow. Prefer dedicated surfaces (`sms`, `whatsapp`, `telegram`, etc.) when channel-specific constraints, formatting, identity, or setup matter.
- **Execution hint**: clear, concise, plain-text-safe responses with no reasoning traces

### `a2a`

Agent-to-agent communication protocol.

- Use cases: multi-agent workflows, agent orchestration, distributed processing
- `consumerType: agent`, `deliveryModel: sync`
- Use when one agent product needs to be invokable as a tool by another agent product.

### `hosted-page`

Hosted publisher page for exposing one or more capabilities as a branded mini-app.

- Use cases: public mini-apps, customer-facing tools, authenticated internal pages
- Presentation config lives on surface items; product-level page behavior controls route, auth requirement, nav style, branding, and social metadata
- Read `runtype://types/surface-configs` before authoring because this surface has structured `HostedPageBehavior` and `HostedPagePresentation` fields

## Auto-generated REST and MCP APIs

When you bind capabilities to a `mcp` or `api` surface, the platform **auto-generates** endpoints (for REST) or tools (for MCP) from each capability. You don't write the endpoints yourself.

- Each capability connected to an `api` surface becomes a REST endpoint.
- Each capability connected to an `mcp` surface becomes an MCP tool.
- You pick the auth scheme.
- You get a hosted URL.

So mapping three agents to one `mcp` surface gives you three MCP tools on one server. Mapping the same three agents to one `api` surface gives three REST endpoints.

## The orchestrator (multi-capability conversational surfaces)

When more than one capability is bound to a single **conversational** surface (`chat`, `slack`, `telegram`, `discord`, `email`, `whatsapp`, etc.), Runtype provisions an **orchestrator agent** automatically. It decides which capability handles each incoming message.

Defaults are designed for fast, cheap routing:

- Small inexpensive model
- Minimum data over the wire
- Alphabetical-label voting (A/B/C…)

Overridable: model, system prompt, label scheme. **Run a product eval on the orchestrator** to compare strategies — out-of-box vs. tuned, alphabetical vs. semantic, small model vs. larger.

If you need a custom router, you can replace the default — but try the default first. Routing should usually be a sub-second operation.

## Surface-specific auto-registered tools

When an agent is bound to a surface, **surface-specific tools auto-register** with the agent. Same agent definition, different tool surface per channel.

Examples:

- **Persona chat**: artifact generation, document toolbar tools.
- **Slack**: thread-context lookup, rich-mrkdwn formatting helpers.
- **Telegram**, **Discord**: channel-appropriate helpers.

You don't manually add these. The agent adapts.

## Picking a surface

> "I need a chat window on a website" → `chat` (+ Persona widget)
> "I need a Slack bot" → `slack`
> "I need to receive Stripe / Twilio / Shopify webhooks" → `webhook` (set `behavior.response` for ACK-shape requirements)
> "I want to expose my tools to Cursor / Claude Code" → `mcp`
> "I want an auto-generated REST API for my product's agents" → `api`
> "I want to run something every morning at 9" → `schedule`
> "I need an email auto-responder" → `email`
> "I have one bot that should work over SMS, WhatsApp, and Telegram" → three surfaces (one per channel) with channel-specific tuning. The channels' constraints diverge enough that per-surface configuration almost always beats a single shared surface.
> "I need a generic multi-channel messaging gateway" → `messaging`
> "I want to federate an external agent into my product" → `a2a` surface, register the external agent as a capability
> "I want Runtype to host a branded mini-app for this product" → `hosted-page`

## Trait-driven prompt construction

When writing an agent's system prompt, factor in the surface trait:

- If `reasoningVisibility: always_strip`, end the prompt with: "Do not include reasoning traces, tool call narration, or process details in your response."
- If `maxResponseLength` is set, mention it explicitly: "Keep responses under N characters."
- If `markdownDialect` ≠ user's default formatting (e.g. `mrkdwn` for Slack), call it out: "Use Slack mrkdwn (`*bold*`, `_italic_`), not standard markdown."
- If `executionHint` is set on the surface type, append it (the platform may do this automatically — check, don't double up).
