---
name: runtype-persona
description: 'Embed, theme, or debug a Runtype Persona chat widget on a website: client tokens, embed snippets, fullscreen assistant layouts, WebMCP page tools, and browser-side chat integrations.'
user-invocable: true
argument-hint: '[Persona widget or chat UI task]'
---

# Runtype Persona

Persona (`@runtypelabs/persona`) is an open-source chat widget that works with any
backend. It is a themeable chat UI with no framework dependency, and it streams from any
backend that sends server-sent events. It has first-party Runtype support, so the
recommended production path is a Runtype agent with a browser-safe `clientToken`. Use this
skill for website widgets, assistant layouts, deployment snippets, theming, artifacts,
WebMCP page tools, and local browser tools.

## Where to Deploy

Default to Runtype. Embed with a browser-safe `clientToken`, and the widget talks to
`api.runtype.com` directly. You need no proxy and no server code. This is the recommended
path, and it is what `generate_persona_embed_code` produces.

If MCP is unavailable and the user wants a starter deploy, run `runtype persona init`. It
creates an agent, a client token, and a snippet you can paste. Without flags, the token is
a `test` token that allows every origin (`*`). For production, pass
`--origins https://your-site.example` and `--environment live`.

Persona also runs on other streaming backends through the Persona SSE protocol. Adapter
examples cover the Vercel AI SDK, OpenAI Agents, LangGraph, and the Anthropic Claude Agent
SDK, among others. Use a self-hosted backend or `@runtypelabs/persona-proxy` only when you
must hide a secret API key or front a non-Runtype agent. Otherwise, use the hosted
`clientToken` embed, which needs no server code.

## Required First Calls

When MCP is available:

- Use `get_platform_documentation(topic="persona-embed")` for current embed docs.
- Use `get_platform_documentation(topic="persona-fullscreen-assistant")` for fullscreen
  split-pane assistant layouts.
- Use `get_platform_documentation(topic="types-surface-configs")` when surface behavior
  config details matter.
- Use `get_persona_theme_reference` before custom themes.
- Use `generate_persona_embed_code` for final snippets whenever possible.

Do not hand-write embed code unless the MCP tools are unavailable. For details not listed
here, fetch one of the documentation topics above.

## Critical Constants

- Package: `@runtypelabs/persona`.
- CDN base: `https://cdn.runtype.com/persona/latest`.
- Installer script: `https://cdn.runtype.com/persona/latest/install.global.js`.
- Self-contained browser bundle: `https://cdn.runtype.com/persona/latest/index.global.js` (exposes `window.AgentWidget`).
- Do not load `/index.js` (the ESM build) directly in a browser. It keeps bare import specifiers such as `marked`, fails with `Failed to resolve module specifier "marked"`, and leaves an empty mount. The ESM build is for bundlers (npm) only.
- CSS for npm usage: `@runtypelabs/persona/widget.css`. For a manual CDN install, use `https://cdn.runtype.com/persona/latest/widget.css`.
- Init function: `initAgentWidget()`.
- Script installer lifecycle callbacks: `onScriptLoad`, `onLauncherShown`,
  `onChatReady(handle)`, and `onError`.
- Ready event: `persona:chat-ready`.
- Direct `initAgentWidget()` returns the handle. Its `onChatReady` option is a fire-only
  callback, not the primary way to get the handle.
- Controller events include `user:message` and `assistant:complete`.

Common wrong answers: `@runtype/persona`, `Persona.mount()`, `window.Persona`,
`index.umd.js`, missing `widget.css`, `persona:ready`, `onReady`, `widget:ready`,
`message:sent`, or `message:received`.

### Load from cdn.runtype.com

When you load Persona from a CDN, use `cdn.runtype.com`. Pages published with the
`publish_page` tool load scripts only from `cdn.runtype.com`, and scripts from other CDNs
fail without an error. On a page that
Runtype deploys, replace `latest` with the current published version, for example
`https://cdn.runtype.com/persona/PERSONA_VERSION/install.global.js`, so a new release does
not change the widget under your deployed page. Pin the version in the script URL, never
as a `version` or `cdn` key in `data-config`.

## Build Pattern

1. Create or identify the agent or flow. A `chat` surface is optional for a basic embed:
   a token that names the agent in `agentIds` is enough. You need a `chat` surface to use
   WebMCP page tools, because the surface holds the `behavior.webmcp` policy.
2. Create a scoped client token with `create_client_token`, or with
   `Runtype.clientTokens.ensure({ name, agentIds, allowedOrigins })` from `@runtypelabs/sdk`
   in code. Without a surface, pass `agentId` to the widget (`data-agent-id` or
   `config.agentId`).
   - `create_client_token` defaults to `environment: "live"` and `allowed_origins: ["*"]`,
     so an unqualified call creates a live token that any origin can use. Pass
     `environment: "test"` while you build, and for production list the exact site
     origins in `allowed_origins`.
   - Use a `test` token (`ct_test_`) only while you build. Test tokens allow localhost
     automatically.
   - A live token (`ct_live_`) created in the dashboard is shown once. Save its value
     when you create it.
3. For a production widget, set a release target on the token so an agent edit does not
   change the live widget at once. Set `target_alias` (for example `live`) and deploy the
   agent to that alias, or set `target_version_id` to pin one exact version. A pinned
   version requires exactly one agent in `agentIds`. A token with no target resolves like
   any run that names no version, so depending on your organization's live-default setting,
   a saved agent edit can reach the widget immediately.
4. Generate embed code with `generate_persona_embed_code`.
5. For consumer-facing widgets, hide tool calls and reasoning by default.
6. For internal or debug widgets, expose useful traces intentionally.
7. For custom themes, set explicit high-contrast component tokens and verify header,
   launcher, user message, primary button, tool call, and reasoning bubble contrast.
8. Keep Persona's default HTML sanitization enabled unless all rendered content is
   trusted.
9. If the assistant should ask structured follow-up questions or suggest replies, set
   `features.askUserQuestion.expose: true` or `suggestions.followUps.expose: true` in the
   widget config instead of hand-writing duplicate local tools.

If a token value leaks, run `regenerate_client_token` and update the embed. The old value
stops working immediately.

## Signed-in and Returning Visitors

- To pass a verified signed-in user to the agent and its tools, set `identityProvider` (the
  Identity Exchange integration's provider value, such as `clerk` or `workos`) and
  `getIdentityProof` in the widget config (Persona 4.24.0 or later). The widget then sends
  `identityProof: { provider, token }` on every chat turn and stops the turn when the proof
  is `null`. Without `identityProvider`, the proof goes only on init, so an agent whose
  `tenancyStrategy` requires a tenant or end user rejects widget chat. See
  [End-user identity](https://docs.runtype.com/developer-guides/guides/end-user-identity).
- To give each visitor a conversation list that persists, set
  `features.history: { enabled: true }` in the widget config and configure
  `behavior.conversationHistory` on the chat surface. See
  [Client conversation history](https://docs.runtype.com/developer-guides/guides/client-conversation-history).

## Fullscreen Assistant Layouts

For ChatGPT-style or Claude-style layouts, read the fullscreen assistant resource first.
The default launcher embed is not enough. Fullscreen layouts usually need full-height
mode, panel chrome changes, a persistent shell, an artifact pane, composer customization,
and layout-specific token choices.

## Local Tools

Use browser-side local tools when the assistant needs to read page state or trigger UI
actions that are only available in the front end. For Persona widgets, these are WebMCP
page tools registered on `document.modelContext` and admitted by the chat surface's
`behavior.webmcp` policy. Pair local tools with hidden parameters when authenticated
context should not enter model context.

For server-side tools that need the signed-in visitor's identity, pass an Identity
Exchange proof as `identityProof` on `/v1/client/init` and `/v1/client/chat` (in Persona,
set `identityProvider` with `getIdentityProof`), then
reference `{{_tenant.id}}` or `{{_endUser.id}}` in the tool's header (or send
`{{_identity.token}}` for a signed assertion your API verifies). The model cannot set
these values, and the call fails closed when the execution has no identity. Docs:
https://docs.runtype.com/developer-guides/guides/tool-template-variables

Good local tool examples:

- Read current page HTML or selected DOM regions.
- Navigate to a record detail page.
- Open a modal or fill a safe form.
- Read browser-only state that has no server API.

Required WebMCP setup:

- Register page tools on `document.modelContext` in the host page, for example with
  `registerTool(...)`. Persona collects them on each turn and runs returned
  `webmcp:<name>` calls in the browser.
- Create the client token with `product_surface_id` set to the `chat` surface, and include
  the embedding page origin in `allowed_origins`. A token that is not bound to the surface
  drops every page tool. `product_surface_id` is fixed at creation, so recreate an
  existing unbound token.
- Enable page tools in the widget config with `webmcp: { enabled: true }`. Persona asks
  for approval before every page-tool call. Use `webmcp.autoApprove = (info) => ...` to
  skip approval only for safe read-only tools, and `webmcp.onConfirm` only when the host
  page needs custom confirmation UI. The widget-side `webmcp.allowlist` is a convenience
  filter, not a security boundary.
- Set the `chat` surface `behavior.webmcp.enabled` to `true`.
- Add origin-scoped `behavior.webmcp.allowlist` rules for page tools that should be
  callable, for example `{ origin: "https://store.example.com", tools: ["search_*"] }`.
  The server enforces only `enabled` and `allowlist`. `behavior.webmcp.requireConfirmFor`
  (for example `["checkout_*"]`) is a confirmation hint for Persona, not a security
  boundary.
- After real traffic, open the surface's **WebMCP** section in the dashboard to review
  discovered tools and observed origins. Discovery records the offered page tools before
  allowlist filtering.
- Do not confuse WebMCP page tools with an `mcp` surface. WebMCP runs inside the browser
  page. An `mcp` surface exposes Runtype capabilities to external AI clients.

## Custom Chat UIs Without Persona

A custom browser chat UI that uses a client token calls `/v1/client/chat` and resumes
with `/v1/client/resume`. That path follows the same surface `behavior.webmcp` policy as
Persona. For an `approval_start` on a gate with `tools.approval.approver: "end-user"`,
POST `{ sessionId, executionId, approvalId, decision }` to `/v1/client/approve` and read
the continued SSE stream as you would from `/v1/client/resume`. Never send `remember`.
Owner gates never reach a client-token chat; it refuses them with 501.

A trusted server or SDK process can send local tools directly to `/v1/dispatch` as
top-level `clientTools[]` and resume with `/v1/dispatch/resume`. This path requires a
secret API key, so never run it in a browser. It uses the optional
`clientToolsPolicy.allowlist` and does not use `behavior.webmcp`, client-token origins, or
dashboard discovery.

## Verify and Troubleshoot

1. Load the page and send a message in the widget.
2. Confirm that the turn reached Runtype with
   `list_conversations(source="client_token", client_token_id="ct_...")` or `list_logs`.

If the widget loads but does not respond, check the response body in the browser's
Network tab:

| Status | Error                           | Fix                                                                                     |
| ------ | ------------------------------- | --------------------------------------------------------------------------------------- |
| `401`  | `Invalid client token`          | Install the current token value. A regenerated token invalidates the old value.         |
| `403`  | `Origin not allowed`            | Add the exact page origin to the token's list, and to the surface's list if it has one. |
| `403`  | `Chat surface is not active`    | Activate the chat surface.                                                              |
| `429`  | `Session message limit reached` | Start a new session, or raise `max_messages_per_session` with `update_client_token`.    |

If page tools never run, confirm that the token is bound to the chat surface, that
`behavior.webmcp.enabled` is `true`. If the surface has a `behavior.webmcp.allowlist`,
confirm that a rule matches the page origin and the tool name. For the full error list and token limits, see
[Client tokens and domain restrictions](https://docs.runtype.com/user-guide/products-surfaces/client-tokens-and-domain-restrictions).

## Related Docs

- [Quickstart: From Agent to Chat Widget](https://docs.runtype.com/user-guide/getting-started/quickstart-from-agent-to-chat-widget)
- [Embedding the chat widget (script tag)](https://docs.runtype.com/user-guide/products-surfaces/embedding-the-chat-widget-script-tag)
- [Embedding the chat widget (React)](https://docs.runtype.com/user-guide/products-surfaces/embedding-the-chat-widget-react)
- [Client tokens and domain restrictions](https://docs.runtype.com/user-guide/products-surfaces/client-tokens-and-domain-restrictions)
