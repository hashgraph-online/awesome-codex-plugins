# docs-map — CometChat Flutter v6: intent → the exact docs page to fetch

Fetch a page instead of guessing a prop. This file is the map; `SKILL.md` bakes only the hot path.

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
> The ONLY line to change for a preview/staging deploy. Every path below is identical across environments.
>
> **Fetch rule:** build a URL as `DOCS_BASE` + the path shown, then append `.md`. Never hardcode a host
> anywhere else; never read installed Dart source in place of a missing doc (see the DOCS GAP protocol).

## The convention
`DOCS_BASE` + `<path>` + `.md` → raw Markdown (verbatim code + prop tables).
```
Fetch:  {DOCS_BASE}/ui-kit/flutter/conversations.md
```
Fallback order: `.md` twin → the same URL **without** `.md` (HTML) → **DOCS GAP** (below).

## ⚠️ Scoped index — DOES NOT EXIST YET for Flutter (tracked DOCS GAP, go-live dependency)
```
{DOCS_BASE}/ui-kit/flutter/llms.txt   → 404 as of 2026-08-21
{DOCS_BASE}/sdk/flutter/llms.txt      → 404 as of 2026-08-21
```
Neither scoped index has been generated. **Until they exist, use the page table below as the index**
(it was derived from the global index and is complete for this family), and fall back to the global
all-products index — `{DOCS_BASE}/llms.txt` (large; last resort) — for anything not listed.
> **Go-live ask (owner: docs):** generate the **scoped UI-Kit `llms.txt` for Flutter v6, including its
> "Task guides (recipes)" section**, and the **SDK `llms.txt` for the Flutter Chat SDK**. Without them the
> docs-maximal, guide-first completeness check degrades to component-wiring only. Tracked in `DOCS-BACKLOG.md`.

## `[verified]` signatures — confirmed against the kit AND the live docs
These signatures were wrong on the live pages when the skill was written (`DOCS-BACKLOG` F1/F2/F3/F5); all four
were **corrected upstream** and re-verified against `cometchat/docs`@`2ebb1db` (2026-09-09), so the pages now
AGREE with `SKILL.md`. Kept here as the authoritative signature reference. Re-verify with
`npm run verify:fences:flutter-v6` if a page ever drifts again.

| Symbol | Confirmed signature |
|---|---|
| `CometChatThreadedHeader` | `parentMessage:` + required `loggedInUser:` (not `message:`) |
| `onThreadRepliesClick` | `void Function(BaseMessage, BuildContext, {CometChatMessageTemplate? template})` |
| `CometChatThreadedHeader` back/error | none — no `onBack:` / `onError:`; back comes from the screen's own `AppBar` |
| `CometChatSearch` results | `onConversationClicked` / `onMessageClicked` |
| `getting-started` init | `initFromSettings()` + `cometchat-settings.json` — **deliberately undocumented (F4 WONTFIX)**; this skill is its reference |

## Component docs (intent → path)
| Intent | Path |
|---|---|
| Install · init · login · first screen | `/ui-kit/flutter/getting-started` |
| What v6 is · architecture | `/ui-kit/flutter/overview` · `/ui-kit/flutter/components-overview` |
| Conversation list props | `/ui-kit/flutter/conversations` |
| Message list props | `/ui-kit/flutter/message-list` |
| Composer props | `/ui-kit/flutter/message-composer` |
| Message header props | `/ui-kit/flutter/message-header` |
| Thread screen | `/ui-kit/flutter/threaded-messages-header` (⚠️ see the wrong-pages table) |
| Search | `/ui-kit/flutter/search` (⚠️ see the wrong-pages table) |
| Users / Groups / Members | `/ui-kit/flutter/users` · `/groups` · `/group-members` |
| Calls (incoming/outgoing/logs/buttons) | `/ui-kit/flutter/call-features` · `/incoming-call` · `/outgoing-call` · `/call-logs` · `/call-buttons` |
| Notification feed | `/ui-kit/flutter/notification-feed` |
| Push notifications (FCM/APNs setup — `-push`) | `/notifications/push-overview` · `/notifications/flutter-push-notifications-android` · `/notifications/flutter-push-notifications-ios` (NOT the legacy singular `/notifications/flutter-push-notifications`) |
| Theming — tokens & palette | `/ui-kit/flutter/theme-introduction` · `/color-resources` · `/component-styling` · `/message-bubble-styling` |
| Customization — slots & behavior | `/ui-kit/flutter/customization-overview` · `-view-slots` · `-state-views` · `-menu-options` · `-bloc-data` · `-datasource` · `-text-formatters` |
| Custom message types | `/ui-kit/flutter/message-template` |
| Formatters (mentions / custom / shortcut) | `/ui-kit/flutter/mentions-formatter-guide` · `/custom-text-formatter-guide` · `/shortcut-formatter-guide` |
| Events (SDK listeners vs UI events) | `/ui-kit/flutter/events` |
| Extensions (all dashboard-enabled) | `/ui-kit/flutter/extensions` |
| Localization | `/ui-kit/flutter/localize` |
| Sounds | `/ui-kit/flutter/sound-manager` |
| Methods / helpers | `/ui-kit/flutter/methods` |
| Troubleshooting | `/ui-kit/flutter/troubleshooting` |
| v5 → v6 upgrade | `/ui-kit/flutter/upgrading-from-v5` |

## Task guides (recipes) — BUILD FROM THESE, then COMPARE (docs-maximal, `RULES.md` §20)
For a whole task, **build from the guide and compare your implementation against it for completeness**,
then apply the hardening deltas in `SKILL.md`. **No matching guide? Build the normal way** (wire the
widgets + fetch props) — the guide is an enhancement, not a prerequisite.

| Task | Guide |
|---|---|
| Guide index | `/ui-kit/flutter/guide-overview` |
| One-to-one chat | `/ui-kit/flutter/flutter-one-to-one-chat` |
| Conversation + messages | `/ui-kit/flutter/flutter-conversation` |
| Tab-based app (the grow target) | `/ui-kit/flutter/flutter-tab-based-chat` · `/multi-tab-chat-ui-guide` |
| Group chat | `/ui-kit/flutter/guide-group-chat` |
| Threaded messages | `/ui-kit/flutter/guide-threaded-messages` (⚠️ signatures wrong — see above) |
| Start a new chat | `/ui-kit/flutter/guide-new-chat` |
| Message privately | `/ui-kit/flutter/guide-message-privately` |
| Block / unblock | `/ui-kit/flutter/guide-block-unblock-user` |
| Call log details | `/ui-kit/flutter/guide-call-log-details` |
| AI agentic flow | `/ui-kit/flutter/guide-message-agentic-flow` |

## SDK docs — the FALLBACK reference (so the SDK ALSO works, `RULES.md` §13)
**UI-Kit first, SDK fallback.** For every feature, first check whether the UI Kit has a widget/prop
(the table above + the catalog). If it does — use it. If it does NOT (AI agents, campaigns,
advanced/AI moderation, transient messages, bots, webhooks, banned-members listing, low-level presence)
— drop to the Flutter Chat SDK and call its method directly. The SDK is **already installed and
re-exported by the kit barrel**, so `User`, `Group`, `Conversation`, `BaseMessage`, `TextMessage` and the
`*RequestBuilder` types need no extra import.
```
SDK_DOCS_BASE = https://www.cometchat.com/docs/sdk/flutter
```
| Intent | Path |
|---|---|
| Overview · setup · auth | `/overview` · `/setup` · `/authentication-overview` |
| Send / receive / edit / delete messages | `/messaging-overview` · `/send-message` · `/receive-messages` |
| Real-time listeners | `/real-time-listeners` · `/connection-status` |
| Users · presence · block | `/users-overview` · `/user-presence` · `/block-users` |
| Groups · members · kick/ban | `/groups-overview` · `/group-kick-ban-members` |
| Conversations & unread | `/conversations-overview` |
| Threads | `/threaded-messages` |
| AI agents / chatbots | `/ai-agents` · `/ai-moderation` |
| Campaigns | `/campaigns` |
| Push token registration | no `sdk/flutter` page (`/sdk/flutter/push-notifications` 404s) — use the three `/notifications/*` push pages in the component table above |
| Webhooks | `/webhooks-overview` |
> Each SDK page carries an **AI Integration Quick Reference** block with method signatures — read that
> first. The SDK's scoped `llms.txt` does not exist yet (see the index gap above); use this table.

## DOCS GAP protocol (`RULES.md` §20 — never silently source-fill)
If a prop/method/behavior you need is **absent or wrong** in the docs:
1. **Do not** substitute reading installed Dart source as though it were documentation, and do not bake a
   permanent workaround into a skill for what is really a docs bug (AUDIT-072 / CHECKLIST row 24).
2. **Verify** the actual behavior by compiling against the pinned kit
   (`npm run verify:fences:flutter-v6` / `test-suite/typecheck/flutter-v6`) — the compiler is the oracle.
3. **TELL THE DEVELOPER**: page · section · what's there now · what it should say · why it matters.
4. **Record it** in `DOCS-BACKLOG.md` (owner **docs**) + an `AUDIT.md` row, and bake only a clearly-labelled
   temporary stopgap in the skill, citing the backlog entry — exactly as F1–F5 are handled in `SKILL.md`.
