# Persona Chat Widget

Persona (`@runtypelabs/persona`) is the SDK behind the embeddable chat UI for any Runtype agent or flow surface of type `chat`.

When asked to generate embed code, prefer calling `generate_persona_embed_code` on the MCP server — it returns a tested, current snippet. Only hand-write embed code when the MCP tool is unavailable. When hand-writing, follow this guide exactly.
For current WebMCP and fullscreen layout details, prefer `persona-embed`,
`persona-fullscreen-assistant`, and `types-surface-configs`.

## Contents

- [Critical common mistakes](#critical-common-mistakes)
- [CDN base URL](#cdn-base-url)
- [Client token](#client-token)
- [Three integration options](#three-integration-options)
- [Config reference](#config-reference)
- [Programmatic access](#programmatic-access)
- [WebMCP page tools](#webmcp-page-tools)
- [Built-in client tools](#built-in-client-tools)
- [Theme contrast rules (critical)](#theme-contrast-rules-critical)
- [Tool calls and reasoning bubbles](#tool-calls-and-reasoning-bubbles)
- [Fullscreen AI-assistant layouts](#fullscreen-ai-assistant-layouts)
- [Generating artifacts that embed the widget](#generating-artifacts-that-embed-the-widget)

## Critical common mistakes

These are the errors most agents make. Read this section first.

- **Package name**: `@runtypelabs/persona` — NOT `@runtype/persona`.
- **Global script file**: `install.global.js` — NOT `index.umd.js`.
- **API**: `initAgentWidget()` — NOT `Persona.mount()`, `window.Persona`, `window.RuntypePersona`. These don't exist.
- **CSS**: When using ESM/manual setup, you **must** load `widget.css`. The script installer handles this automatically.
- **Ready event**: `persona:chat-ready`; `persona:ready` is only a deprecated alias — NOT `widget:ready` or `agentwidget:ready`.
- **Ready callback**: `onChatReady(handle)`; `onReady` is only a deprecated alias.
- **Controller events**: use `user:message` and `assistant:complete` — NOT `message:sent` or `message:received`.

## CDN base URL

```
https://cdn.jsdelivr.net/npm/@runtypelabs/persona@latest/dist
```

## Client token

Persona uses a `clientToken`, created with `create_client_token`, for browser-side chat access. This is not a surface key. Client tokens are public, scoped to specific agents or flows, and can be constrained with origin and rate-limit settings.

## Current defaults to preserve

- Script-tag installs use the tiny `launcher.global.js` fast path for ordinary floating launchers and defer the full widget until first open when safe.
- Persona sanitizes rendered message HTML with DOMPurify by default. Keep `config.sanitize` enabled unless all rendered content is trusted.
- Shadow DOM is opt-in with `useShadowDom: true`; the default is `false` for CSS compatibility.
- For programmatic access, prefer `onChatReady` or `persona:chat-ready`.

## Three integration options

### Option 1: Script installer (simplest)

One script tag, no CSS import needed.

```html
<script
  src="https://cdn.jsdelivr.net/npm/@runtypelabs/persona@latest/dist/install.global.js"
  data-runtype-token="YOUR_CLIENT_TOKEN"
></script>
```

To mount in a specific container:

```html
<div id="chat"></div>
<script
  src="https://cdn.jsdelivr.net/npm/@runtypelabs/persona@latest/dist/install.global.js"
  data-runtype-token="YOUR_CLIENT_TOKEN"
  data-config='{"target":"#chat","apiUrl":"https://api.runtype.com"}'
></script>
```

### Option 2: ESM / manual

Full control. Requires loading `widget.css` separately.

```html
<link
  rel="stylesheet"
  href="https://cdn.jsdelivr.net/npm/@runtypelabs/persona@latest/dist/widget.css"
/>
<div id="chat"></div>
<script type="module">
  import {
    initAgentWidget,
    markdownPostprocessor,
  } from 'https://cdn.jsdelivr.net/npm/@runtypelabs/persona@latest/dist/index.js'

  initAgentWidget({
    target: '#chat',
    config: {
      apiUrl: 'https://api.runtype.com',
      clientToken: 'YOUR_CLIENT_TOKEN',
      parserType: 'json',
      postprocessMessage: ({ text }) => markdownPostprocessor(text),
      launcher: {
        enabled: true,
        title: 'Chat',
        subtitle: 'How can I help you today?',
        position: 'bottom-right',
      },
    },
  })
</script>
```

### Option 3: npm / React

```bash
npm install @runtypelabs/persona
```

```ts
import '@runtypelabs/persona/widget.css'
import { DEFAULT_WIDGET_CONFIG, initAgentWidget, markdownPostprocessor } from '@runtypelabs/persona'

initAgentWidget({
  target: '#chat',
  config: {
    ...DEFAULT_WIDGET_CONFIG,
    apiUrl: 'https://api.runtype.com',
    clientToken: 'YOUR_CLIENT_TOKEN',
    parserType: 'json',
    postprocessMessage: ({ text }) => markdownPostprocessor(text),
  },
})
```

## Config reference

| Property                                 | Type                          | Notes                                                             |
| ---------------------------------------- | ----------------------------- | ----------------------------------------------------------------- |
| `target`                                 | string \| HTMLElement         | CSS selector or DOM element                                       |
| `useShadowDom`                           | boolean                       | Style isolation (default false)                                   |
| `config.apiUrl`                          | string                        | `https://api.runtype.com` (or another configured Runtype API URL) |
| `config.clientToken`                     | string                        | Browser-safe client token from `create_client_token`              |
| `config.parserType`                      | `'json'`                      | Always `'json'` for Runtype streams                               |
| `config.postprocessMessage`              | function                      | Use `markdownPostprocessor` for rich text                         |
| `config.launcher`                        | object                        | `{ enabled, title, subtitle, position }`                          |
| `config.colorScheme`                     | `'light' \| 'dark' \| 'auto'` | Theme mode                                                        |
| `config.theme`                           | `DeepPartial<PersonaTheme>`   | Light theme overrides                                             |
| `config.darkTheme`                       | `DeepPartial<PersonaTheme>`   | Dark theme overrides                                              |
| `config.sanitize`                        | `boolean \| (html) => string` | Sanitize rendered message HTML; default uses DOMPurify            |
| `config.webmcp`                          | object                        | Widget-side WebMCP page-tool discovery/execution config           |
| `config.features.askUserQuestion.expose` | boolean                       | Advertise built-in LOCAL `ask_user_question` via `clientTools[]`  |
| `config.features.suggestReplies.expose`  | boolean                       | Advertise built-in LOCAL `suggest_replies` via `clientTools[]`    |
| `windowKey`                              | string                        | Stores handle on `window[windowKey]` for programmatic access      |
| `onChatReady`                            | `(handle) => void`            | Callback when the controller API is callable                      |

## Programmatic access

Three ways. Pick by context.

**Script installer with `windowKey`:**

```html
<script
  src=".../install.global.js"
  data-runtype-token="YOUR_CLIENT_TOKEN"
  data-config='{"windowKey":"myChat"}'
></script>
```

**`onChatReady` callback (via `window.siteAgentConfig`):**

```html
<script>
  window.siteAgentConfig = {
    clientToken: 'YOUR_CLIENT_TOKEN',
    windowKey: 'myChat',
    onChatReady(handle) {
      handle.on('user:message', (message) => console.log('sent:', message))
      handle.on('assistant:complete', (message) => console.log('received:', message))
    },
  }
</script>
<script src=".../install.global.js"></script>
```

**`persona:chat-ready` event** (works from any script, including separately-loaded ones):

```html
<script>
  window.addEventListener('persona:chat-ready', (e) => {
    const handle = e.detail
    handle.open()
  })
</script>
```

`onReady` and `persona:ready` still work as deprecated aliases, but do not use
them in new snippets.

## WebMCP page tools

WebMCP page tools are browser-side local tools registered on the embedding page
with `document.modelContext.registerTool(...)`. Persona snapshots them at the
start of each chat turn, sends them to Runtype as `clientTools[]` with
`origin: 'webmcp'`, and executes them back in the page when the model calls
them.

Use WebMCP only when the assistant needs page-local state or UI:

- visible product catalog or cart state
- selected DOM regions or hydrated front-end state
- navigation inside the host app
- opening safe modals or filling safe forms
- browser-only context with no server API

Do not use WebMCP for work that can run server-side. Prefer built-ins,
Orthogonal/UCP tools, external HTTP tools, custom tools, or standard MCP server
tools first.

Required setup:

1. Create a client token with `allowedOrigins` containing the exact embedding
   page origin.
2. Enable page-tool consumption in the widget config: `webmcp: { enabled: true }`.
3. Set the chat surface `behavior.webmcp.enabled` to `true`.
4. Add origin-scoped allow-list rules when the surface should restrict which
   page tools are available. If `allowlist` is omitted or empty while WebMCP is
   enabled, every offered WebMCP tool is admitted from every allowed origin.

```ts
initAgentWidget({
  target: '#chat',
  config: {
    clientToken: 'YOUR_CLIENT_TOKEN',
    webmcp: { enabled: true },
  },
})
```

```json
{
  "type": "chat",
  "behavior": {
    "webmcp": {
      "enabled": true,
      "allowlist": [
        { "origin": "https://store.example.com", "tools": ["search_*", "get_cart"] },
        { "origin": "*", "tools": ["read_page"] }
      ],
      "requireConfirmFor": ["checkout_*"]
    }
  }
}
```

Rules:

- Tool names are registered bare by the page. Runtype applies the `webmcp:`
  prefix after validation.
- Allow-list patterns match bare tool names. Use exact names, `*`, or one
  trailing wildcard such as `search_*`.
- The HTTP `Origin` header is canonical. `pageOrigin` is diagnostic only.
- `requireConfirmFor` is a Persona-side confirmation hint, not server-side
  enforcement.
- The dashboard WebMCP tab shows discovered tools and observed origins from the
  trailing 7 days and can promote tools into allow-list rules. It shows an
  "Allow all tools" mode for the empty-allowlist case and reveals the rule
  editor only when "Use an allow-list" is selected.
- The WebMCP Tool Inspector example template is useful for a drop-in chat agent
  that enumerates and tests whichever page tools are registered at runtime.

WebMCP is not a Runtype `mcp` surface. An `mcp` surface exposes Runtype
capabilities to external AI clients; WebMCP exposes browser-page tools to a
Persona `chat` surface.

Advanced direct dispatch:

- Customers implementing a non-Persona chat UI, native/desktop app, or server
  proxy can submit WebMCP-style local tools directly to API-key `/v1/dispatch`
  with top-level `clientTools[]`.
- Proxies using `@runtypelabs/persona-proxy` should forward `clientTools[]` and
  expose the matching `${apiUrl}/resume` route so WebMCP and SDK local tools can
  complete paused executions.
- This path requires a secret Runtype API key and must run from a trusted
  server or SDK process, never directly from an untrusted browser page.
- Raw dispatch admits submitted `origin: "webmcp"` tools by default. Use
  `clientToolsPolicy.allowlist` to narrow bare tool names for that request.
- The raw dispatch path resumes via `/v1/dispatch/resume` after local-tool
  await events. It does not use `behavior.webmcp`, client-token
  `allowedOrigins`, or dashboard discovery telemetry.

## Built-in client tools

Persona can advertise SDK-owned LOCAL tools without any page registration. Use
these when the assistant needs common client-side UI primitives:

```ts
config: {
  features: {
    askUserQuestion: { expose: true },
    suggestReplies: { expose: true },
  }
}
```

- `ask_user_question` renders a blocking answer sheet over the composer, supports
  one to eight multiple-choice questions, persists progress, and resumes the
  agent with the selected answer(s).
- `suggest_replies` renders follow-up chips, lets users click a suggestion as
  their next message, and auto-resumes the paused execution.
- Both default to `expose: false`. Leave them off if the flow already declares
  equivalent `runtimeTools`.

## Theme contrast rules (critical)

Don't trust palette scale steps (`primary.50`, `primary.500`) to give you contrast automatically. Compute contrast on the **final resolved colors** for each foreground/background pair, in both light and dark themes.

For both `config.theme` and `config.darkTheme`:

- `components.header.titleForeground` and `subtitleForeground` need **≥4.5:1** contrast against `components.header.background`.
- `components.header.actionIconForeground` and `iconForeground` need **≥3:1** contrast against the surface they sit on.
- `components.header.iconBackground` should be visually distinct from `header.background`.
- Apply the same logic to `components.launcher.foreground`, `components.message.user.text`, `components.button.primary.foreground` against their respective backgrounds.
- Prefer explicit solid hex foreground colors over semi-transparent `rgba(...)` unless you've verified the composited contrast ratio.

Dark header → use `#ffffff` or `#f5f5f5` for foregrounds.
Light header → use `#111827` or `#1f2937`.

Before generating any custom theme, call `get_persona_theme_reference` to get the design-token docs and example themes — these are your starting points, not your fallbacks.

## Tool calls and reasoning bubbles

Three control layers: **visibility**, **behavior**, **styling**.

### Visibility

```ts
config: {
  features: {
    showToolCalls: true,
    showReasoning: true,
  }
}
```

Set to `false` for consumer-facing widgets. Leave on for dev/debug surfaces.

### Behavior

Tool calls — `config.features.toolCallDisplay`:

- `expandable`: when `false`, collapsed summary only
- `collapsedMode`: `"tool-call"` | `"tool-name"` | `"tool-preview"`
- `activePreview`: live preview during execution
- `previewMaxLines`, `activeMinHeight`, `grouped`

Reasoning — `config.features.reasoningDisplay`:

- `expandable`, `activePreview`, `previewMaxLines`, `activeMinHeight`

### Visual styling

Three levels:

**1. Shared chrome via `components.collapsibleWidget`:**

```ts
theme: {
  components: {
    collapsibleWidget: {
      container: "palette.colors.gray.50",
      surface: "semantic.colors.surface",
      border: "semantic.colors.border",
    }
  }
}
```

**2. Per-bubble shadow tokens:**

```ts
theme: {
  components: {
    toolBubble: { shadow: "palette.shadows.sm" },
    reasoningBubble: { shadow: "palette.shadows.sm" }
  }
}
```

Use `"none"` for flat callouts.

**3. Imperative tool-call overrides via `config.toolCall`:**
Properties include `shadow`, `backgroundColor`, `borderColor`, `borderRadius`, `headerBackgroundColor`, `headerTextColor`, `contentBackgroundColor`, `contentTextColor`, `codeBlockBackgroundColor`, etc.

Reasoning bubbles do **not** have an imperative override layer. Style them via theme tokens only (especially `components.collapsibleWidget` and `components.reasoningBubble`).

### Contrast rules for bubbles

- Bubble background must contrast with the surrounding chat surface.
- Header text and toggle icons must be readable against the header background.
- If you set `config.toolCall.headerBackgroundColor`, explicitly set `headerTextColor` and `toggleTextColor`.
- Labels like "Arguments", "Result", "Activity" must remain readable.
- Code block text must contrast against code block background.

### Common recipes

Hidden internals (consumer-facing):

```ts
config: { features: { showToolCalls: false, showReasoning: false } }
```

Visible but not expandable:

```ts
config: {
  features: {
    toolCallDisplay: { expandable: false },
    reasoningDisplay: { expandable: false }
  }
}
```

Flat minimal callouts:

```ts
theme: {
  components: {
    toolBubble: { shadow: "none" },
    reasoningBubble: { shadow: "none" },
    collapsibleWidget: {
      container: "#f8f9fa",
      surface: "#ffffff",
      border: "#e9ecef"
    }
  }
}
```

## Fullscreen AI-assistant layouts

For ChatGPT/Claude-style fullscreen split-pane layouts (chat on left, artifacts on right), read the `runtype://guide/persona-fullscreen-assistant` MCP resource. It covers the non-default `launcher.fullHeight`, panel-chrome removal, split artifact pane, document toolbar preset, custom composer plugin, and the dark palette those UIs use.

## Generating artifacts that embed the widget

When generating standalone HTML files or Claude artifacts that embed the widget:

1. Use the **script installer** approach for simplicity.
2. For more control, use **ESM** — and include `widget.css`.
3. `clientToken` / `data-runtype-token` is the browser-safe client token from `create_client_token`.
4. API URL is `https://api.runtype.com` (or environment-appropriate).
5. Don't invent APIs. The only init function is `initAgentWidget()`. The current ready event is `persona:chat-ready` (`persona:ready` is deprecated).
6. For custom themes, call `get_persona_theme_reference` first; set explicit high-contrast component tokens.
7. For programmatic access, use `windowKey` + `onChatReady` or the `persona:chat-ready` listener.
