# docs-map — where to look anything up

## Reaching docs — PREFER the CometChat docs MCP; fetch is the fallback
The canonical doc channel is the **first-party CometChat docs MCP** — tools `search_cometchat_docs`,
`fetch_cometchat_doc_page`, and `get_cometchat_implementation_bundle`. **If those tools are connected,
use them instead of a raw web fetch:**
- **Find the page** → `search_cometchat_docs(query, version?)` — replaces browsing the scoped `llms-*` index.
- **Read the page** → `fetch_cometchat_doc_page(path)` — pass the SAME `<path>` the tables below list
  (the conversations page path for your platform); the MCP resolves the `.md` twin and returns raw Markdown.
  A full `https://…/docs/<path>` URL also works.
- **A whole feature/recipe** → `get_cometchat_implementation_bundle(...)` is **NON-AUTHORITATIVE** — curated STATIC recipes that can lag the live docs (verified stale vs v7: e.g. `CometChatConversationsWithMessages`, `css-variables.css`). Treat any bundle as a hint only: RECONCILE it against the `fetch_cometchat_doc_page` result + the pack's hardening; never emit bundle code verbatim.

The MCP reads whatever docs environment it is pointed at (production by default; a preview when repointed),
so it also carries the environment-swap concern below — no hardcoded host on the skill side.

**If the MCP tools are NOT connected:** add it (`claude mcp add --transport http cometchat-docs https://mcp.cometchat.com/mcp`, or reinstall/enable the plugin) and retry; only if it still will not connect, fall back to a plain fetch via `DOCS_BASE` (defined next).
Either way the `<path>` catalog in this file is the source of truth for WHICH page — MCP-vs-fetch is only HOW.

## DOCS_BASE — the fetch FALLBACK entry point (⚠️ SWAP HERE to change environments)
```
DOCS_BASE = https://www.cometchat.com/docs
```
**Fetch rule:** build a URL as `DOCS_BASE` + the path below, then append `.md` for the clean Markdown twin. The same applies to any `docs_topic` in `features.angular-v5.json` / `contracts.angular-v5.json` — those are paths, not URLs, so they resolve against whatever `DOCS_BASE` is set to.
```
Fetch:  {DOCS_BASE}/ui-kit/angular/components/cometchat-conversations.md
```
Most pages open with an **"AI Integration Quick Reference"** block — read that first for package, imports and key inputs.

## Scoped Angular v5 index (prefer over the global llms.txt)
```
{DOCS_BASE}/ui-kit/angular/llms-angular-v5.md
```
A 91-page, Angular-v5-only routing index including a **"Task guides (recipes)"** section — start here to find the right page. Site-wide `{DOCS_BASE}/llms.txt` spans every product and is far larger; last resort only.

> This scoped index now resolves on prod (corrected upstream — verified against cometchat/docs, 2026-09-09). If a `.md` twin ever 404s, fall back to the same path without `.md`, or use the per-page paths below.

## Component docs (append `.md`)
| Need | Path under `{DOCS_BASE}/ui-kit/angular` |
| --- | --- |
| Conversation list | `/components/cometchat-conversations` |
| Message header | `/components/cometchat-message-header` |
| Message list | `/components/cometchat-message-list` |
| Message composer | `/components/cometchat-message-composer` |
| Thread header | `/components/cometchat-thread-header` |
| Users / Groups | `/components/cometchat-users` · `/components/cometchat-groups` |
| Group members | `/components/cometchat-group-members` |
| Search | `/components/cometchat-search` |
| Reactions | `/components/cometchat-reactions` |
| Calls | `/components/cometchat-call-buttons` · `/components/cometchat-incoming-call` |
| Notification feed | `/components/notification-feed` *(no `cometchat-` prefix — the one exception)* |
| All components | `/components/components-overview` |
| Theming | `/customization/theming` |
| Localization | `/customization/localization` |
| Global config | `/customization/global-config` |
| Events · Methods · Core | `/events` · `/methods` · `/core-features` |
| Extensions · AI · Calls | `/extensions` · `/ai-features` · `/call-features` |
| Services (DI) | `/api-reference/introduction` |
| **v4→v5 migration / upgrade** | `/customization/migration-guide` *(the official "Upgrading From V4": Integration · Components · Theming · Properties · Shared Dependencies · State Management · Localization · Quick Checklist. Angular has **no** `migration-property-changes` twin like React's — per-component inputs/outputs come from each component page above.)* |

## Task guides (recipes) — build FROM these
| Task | Path |
| --- | --- |
| New chat | `/guides/new-chat` |
| Group chat | `/guides/group-chat` |
| Threaded messages | `/guides/threaded-messages` |
| Search messages | `/guides/search-messages` |
| Message privately | `/guides/message-privately` |
| Block / unblock | `/guides/block-unblock-user` |
| Custom message types | `/guides/custom-message-types` |
| Text formatters | `/guides/custom-text-formatter` · `/guides/mentions-formatter` · `/guides/url-formatter` · `/guides/hashtag-formatter` · `/guides/shortcut-formatter` |
| Rich text | `/guides/rich-text-formatting` |
| Card messages | `/guides/card-messages` |
| State management | `/guides/state-management` |
| RxJS patterns | `/guides/subscription-patterns` |
| Call log details | `/guides/call-log-details` |

**Reference layouts** — whole-screen shells, not single-feature recipes. Fetch the matching one before composing a surface:

| Layout | Path | Shape |
| --- | --- | --- |
| Tab-based app | `/ui-kit/angular/angular-tab-based-chat` | left sidebar + `@switch (activeTab)` over `ChatStateService`. **The grow target** — build it only when the user asks for tabs. Its tab set (Chats · Call Logs · Users) is ONE example, not the definitive list. |
| Conversation list ↔ pane | `/ui-kit/angular/angular-conversation` | the default "add chat" shape (`placement/references/core-surface.md`) |
| Single 1:1 chat | `/ui-kit/angular/angular-one-to-one-chat` | one fixed conversation, no selector |

Use a guide as the implementation SOURCE, then compare your output against it.

## SDK docs — the per-feature fallback
When a capability has **no UI Kit component**, drop to the headless JS SDK. Angular uses the same SDK as every other web family — there is no Angular-specific SDK.

```
SDK_DOCS_BASE = https://www.cometchat.com/docs
# Production docs base
SDK index (scoped — PREFER):  {SDK_DOCS_BASE}/sdk/javascript/llms-javascript-v4.md
Convention:                   {SDK_DOCS_BASE}/sdk/javascript/<page> then append .md
```
The scoped index groups every SDK page by area — Messaging · Calling · Users · Groups · AI, campaigns & webhooks · Real-time Listeners · Key Concepts. Each page opens with an **"AI Integration Quick Reference"** accordion listing package, import and key methods — read that first, then the examples.

Common entry points: `/sdk/javascript/send-message` · `/sdk/javascript/receive-messages` · `/sdk/javascript/retrieve-conversations` · `/sdk/javascript/user-management` · `/sdk/javascript/groups-overview` · `/sdk/javascript/ai-agents`.

Using the SDK from Angular, two rules from `lifecycle.md` always apply: remove listeners in `ngOnDestroy`, and repaint after SDK-callback state updates via a **signal** or `ChangeDetectorRef.markForCheck()` (Angular v21 is zoneless by default, so `NgZone.run()` won't trigger change detection).

## Never
Do not read a symbol's shape from `node_modules/**/*.d.ts` and present it as documentation, and never answer inputs/outputs from memory. Fetch the page.

## Docs first for the API — the installed kit for BEHAVIOUR the docs omit (full detail)
> `SKILL.md` § "Docs first for the API" keeps the spine; the deep methodology + examples live here.

**What exists and what it is called comes from the docs.** Fetch the component's page (`DOCS_BASE` + path + `.md`).
Each opens with an **AI Integration Quick Reference** — selector, key inputs/outputs, view slots, anchors into the
props table. Read that first; it usually answers the question without loading the page.

Do **not** invent an API from the type declarations. The types expose internal-only names that are not importable
and members with no defined behaviour — that is how a plausible-but-wrong symbol reaches the emitted code.

**But reading the shipped bundle IS correct when the docs state a prop and not its semantics.** The props table
often gives a type and a one-line description without saying how the input behaves. Real examples in this kit:

- `attachmentOptions` is documented as *"Custom attachment options for the attachment menu"* — it does not say
  whether yours **append to** or **replace** the built-ins. (They append: the composer pushes yours onto the built-in
  list.) Guess "replace" and you silently delete image/video/file/audio attachments.
- `messagesRequestBuilder` — whether a supplied builder overrides or merges with defaults is not stated for the
  message list.

When behaviour is load-bearing and undocumented, **verify it in the installed package**
(`node_modules/@cometchat/chat-uikit-angular/fesm2022/*.mjs`) rather than guessing. Then do two things:

1. **State in your summary that you verified it against the installed kit**, not the docs — so the developer knows it
   is pinned to this version.
2. **Report it as a docs gap**, naming the page and the missing sentence. That is how the docs improve instead of
   every agent re-deriving it.

Reading the package is also fine for confirming the installed **version**.
