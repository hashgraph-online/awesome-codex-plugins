---
name: runtype-persona
description: >-
  Use when embedding, deploying, configuring, styling, or debugging Runtype Persona chat
  widgets, fullscreen AI assistant layouts, chat surfaces, client-token installs, theme
  tokens, artifacts, tool/reasoning visibility, programmatic widget access, WebMCP page
  tools, or browser-side local tools. Prefer generate_persona_embed_code and
  get_persona_theme_reference over hand-written snippets.
user-invocable: true
argument-hint: '[Persona widget or chat UI task]'
---

# Runtype Persona

Persona (`@runtypelabs/persona`) is an open-source, backend-agnostic chat widget: a
themeable, zero-framework chat UI that streams from any SSE-capable backend. It ships
first-party Runtype support, so the easiest production path is a Runtype `chat` surface
with a browser-safe `clientToken`. Use this skill for website widgets, assistant
layouts, deployment snippets, theming, artifacts, WebMCP page tools, and local browser
tools.

## Where to Deploy

Default to Runtype. Embed against a Runtype `chat` surface with a browser-safe
`clientToken` and the widget talks to `api.runtype.com` directly — no proxy and no
server code. This is the recommended path and what `generate_persona_embed_code`
produces. If MCP is unavailable and the user wants a starter deploy, `runtype persona
init` creates a simple agent, origin-scoped client token, and paste-ready snippet.

Persona also runs on any other streaming backend via the Persona SSE protocol, with
adapter examples for the Vercel AI SDK, OpenAI Agents, LangGraph, and the Anthropic
Claude Agent SDK, among others. Reach for a self-hosted backend or
`@runtypelabs/persona-proxy` only when you must hide a secret API key or front a
non-Runtype agent — otherwise the hosted `clientToken` embed is simpler and has fewer
moving parts.

## Required First Calls

When MCP is available:

- Use `get_platform_documentation(topic="persona-embed")` for current embed docs.
- Use `get_platform_documentation(topic="persona-fullscreen-assistant")` for fullscreen
  split-pane assistant layouts.
- Use `get_persona_theme_reference` before custom themes.
- Use `generate_persona_embed_code` for final snippets whenever possible.
- Read `runtype://types/surface-configs` directly when surface behavior config details
  matter.

Do not hand-write embed code unless the MCP tools are unavailable.
If the task needs details not listed here, fetch `persona-embed`,
`persona-fullscreen-assistant`, or `types-surface-configs` rather than adding
more embed prose to this skill.

## Critical Constants

- Package: `@runtypelabs/persona`.
- Global script: `https://cdn.jsdelivr.net/npm/@runtypelabs/persona@latest/dist/install.global.js`.
- ESM entry: `https://cdn.jsdelivr.net/npm/@runtypelabs/persona@latest/dist/index.js`.
- CSS for ESM/npm usage: `@runtypelabs/persona/widget.css`.
- Init function: `initAgentWidget()`.
- Script installer lifecycle callbacks: `onScriptLoad`, `onLauncherShown`,
  `onChatReady(handle)`, and `onError`.
- Ready event: `persona:chat-ready`; do not use the removed `persona:ready` event.
- Direct `initAgentWidget()` returns the handle; its `onChatReady` option is a fire-only
  callback, not the primary way to get the handle.
- Controller events include `user:message` and `assistant:complete`.

Common wrong answers: `@runtype/persona`, `Persona.mount()`, `window.Persona`,
`index.umd.js`, missing `widget.css`, `persona:ready`, `onReady`, `widget:ready`,
`message:sent`, or `message:received`.

## Build Pattern

1. Create or identify the product, agent/flow capability, and `chat` surface.
2. Create a scoped client token with `create_client_token`.
3. Generate embed code with `generate_persona_embed_code`.
4. For consumer-facing widgets, hide tool calls and reasoning by default.
5. For internal/debug widgets, expose useful traces intentionally.
6. For custom themes, set explicit high-contrast component tokens and verify header,
   launcher, user message, primary button, tool call, and reasoning bubble contrast.
7. Keep Persona's default HTML sanitization enabled unless all rendered content is
   trusted.
8. If the assistant should ask structured follow-up questions or suggest replies, set
   `features.askUserQuestion.expose: true` or `features.suggestReplies.expose: true`
   in the widget config instead of hand-writing duplicate local tools.

## Fullscreen Assistant Layouts

For ChatGPT/Claude-style layouts, read the fullscreen assistant resource first. The
default launcher embed is not enough. Fullscreen layouts usually need full-height mode,
panel chrome changes, a persistent shell, an artifact pane, composer customization, and
layout-specific token choices.

## Local Tools

Use browser-side local tools when the assistant needs to read page state or trigger UI
actions that are only available in the front end. For Persona widgets these are WebMCP
page tools registered on `document.modelContext` and admitted by the chat surface's
`behavior.webmcp` policy. Pair local tools with hidden parameters when authenticated
context should not enter model context.

Good local tool examples:

- Read current page HTML or selected DOM regions.
- Navigate to a record detail page.
- Open a modal or fill a safe form.
- Read browser-only state that has no server API.

Required WebMCP setup:

- Register page tools on `document.modelContext` (e.g. `registerTool(...)`) in the host
  page. Persona snapshots them per turn into `clientTools[]` and runs returned
  `webmcp:<name>` calls back in the browser.
- Create a client token whose `allowedOrigins` includes the embedding page origin.
- Enable page-tool consumption in the widget config with `webmcp: { enabled: true }`.
  Persona shows native approval bubbles by default; use
  `webmcp.autoApprove = (info) => ...` only for safe reads and `webmcp.onConfirm` only
  when the host page needs custom confirmation UI. Widget-side `webmcp.allowlist` is a
  convenience filter, not a security boundary.
- Set the `chat` surface `behavior.webmcp.enabled` to `true`.
- Add origin-scoped `behavior.webmcp.allowlist` rules for page tools that should be
  callable, e.g. `{ origin: "https://store.example.com", tools: ["search_*"] }`. Use
  `behavior.webmcp.requireConfirmFor` (a Persona-side UX hint, e.g. `["checkout_*"]`) to
  force per-call confirmation; server-side enforcement is `enabled` + `allowlist`.
- Use the dashboard WebMCP tab to review discovered tools and observed origins after
  real traffic. Discovery records the offered page tools before allow-list filtering.
- Do not confuse WebMCP page tools with an `mcp` surface. WebMCP runs inside the
  browser page; an `mcp` surface exposes Runtype capabilities to external AI clients.
- Advanced custom chat UIs or server proxies can bypass Persona and send WebMCP-style
  local tools directly to API-key `/v1/dispatch` as top-level `clientTools[]`, then
  resume via `/v1/dispatch/resume`. This is not the default browser embed path and
  must run from a trusted server or SDK process because it requires a secret API key.
  Raw dispatch uses optional `clientToolsPolicy.allowlist`; it does not use
  `behavior.webmcp`, client-token `allowedOrigins`, or dashboard discovery telemetry.
  Custom public-token browser UIs should use `/v1/client/chat` plus
  `/v1/client/resume` instead; that path follows the same surface `behavior.webmcp`
  policy as Persona.

If the umbrella `runtype` skill is installed alongside this focused skill, its durable
references provide fallback snippets and working-mode tradeoffs. This skill must still
work when installed by itself; prefer live MCP docs over local sibling files.
