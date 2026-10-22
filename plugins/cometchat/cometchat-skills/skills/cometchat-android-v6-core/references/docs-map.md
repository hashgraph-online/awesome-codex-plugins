# docs-map — CometChat Android v6: intent → the exact docs page to fetch

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
> Production docs (`https://www.cometchat.com/docs`). The Android v6 UI Kit tree lives at the UNVERSIONED root: `/ui-kit/android/<page>`
> (v5 is `/ui-kit/android/v5/...` — do not fetch it for a v6 build).
> **Fetch rule:** always build a URL as `DOCS_BASE` + the path shown, then append `.md`.
> Never hardcode a host anywhere else; never decompile the AAR or read kit source for signatures.

## The convention
`DOCS_BASE` + `<path>` + `.md` → raw Markdown (verbatim code +, on many pages, an "AI Integration
Quick Reference" accordion). **Every component page carries a `Kotlin (XML Views)` tab AND a
`Jetpack Compose` tab — read the tab for YOUR cohort** (the same `CometChat*` names, different wiring).
```
Fetch:  {DOCS_BASE}/ui-kit/android/conversations.md
```
Fallback order: `.md` twin → if it 404s, the same URL **without** `.md` (HTML) → **never** kit source.

## Scoped Android v6 index (prefer over the global llms.txt)
```
{DOCS_BASE}/ui-kit/android/llms-android-v6.md
```
An Android-v6-only index of every page as a `.md` link — use it to discover any page not in the
table below. Global all-products index (large; last resort): `{DOCS_BASE}/llms.txt`.
> **Scoped index:** `{DOCS_BASE}/ui-kit/android/llms-android-v6.md` is live (the `docs/android-llms-indexes`
> branch merged). Use it to find pages; the per-page `.md` twins below + the global `llms.txt` remain fallbacks.

## SDK docs — the FALLBACK reference (a feature the UI Kit has NO component for)
The rule of the pack: **for every feature, first check whether the UI Kit has a component/param for it
(this file's table + `component-props.md` + the catalog). If it does — USE it. If it does NOT** (e.g.
AI agent events, transient messages, webhooks, low-level presence/connection, unread counts, granular
group management) **— drop to the Android Chat SDK and call it directly** (the SDK is already installed
under the UI Kit; init/login already use it). Look the method up in the SDK docs — never guess:
```
SDK_DOCS_BASE = https://www.cometchat.com/docs
```
- **SDK index (scoped — PREFER this):** `{SDK_DOCS_BASE}/sdk/android/v5/llms-android-v5.md` — an
  **Android-SDK-v5-only** routing index grouped by area (Messaging · Calling · Users · Groups · AI &
  advanced · Resources & listeners · Advanced). Start here to find the feature's page. Do NOT use the
  site-wide `{SDK_DOCS_BASE}/llms.txt` except as a last resort. Same DOCS-GAP note as above.
- **⚠️ URL trap:** Android SDK v5 pages are VERSIONED — `{SDK_DOCS_BASE}/sdk/android/v5/<page>` then
  append `.md`. The unversioned `/sdk/android/<page>` tree is **v4** — never fetch it for a v5 build.
- **Example:** flag a message → `{SDK_DOCS_BASE}/sdk/android/v5/flag-message.md` →
  `CometChat.flagMessage(...)`, `CometChat.getFlagReasons(...)`.
> Never hand-roll a feature that exists in the UI Kit OR the SDK, and never guess an SDK method —
> look it up in the SDK index → the page.

## Don't fetch the hot path — it's baked
Install, `init → login → render`, and the core drop-in callbacks for "add chat" are BAKED in
`cometchat-android-v6-core`. Fetch ONLY for exhaustive params/attrs / long-tail components /
theming tokens / feature enablement.

## The 80% trigger table  (URL = `{DOCS_BASE}` + path, then append `.md`)
| Intent | Path (append `.md`) |
|---|---|
| setup / init / login (XML Views) | `/ui-kit/android/getting-started-kotlin` |
| setup / init / login (Compose) | `/ui-kit/android/getting-started-jetpack` |
| pick a chat experience / recipes | `/ui-kit/android/getting-started` · `one-to-one-chat` · `tab-based-chat` · `conversation-message-view` |
| conversation list (full params) | `/ui-kit/android/conversations` |
| message list | `/ui-kit/android/message-list` |
| message composer | `/ui-kit/android/message-composer` |
| message header | `/ui-kit/android/message-header` |
| users / groups / group members | `/ui-kit/android/users` · `groups` · `group-members` |
| threads | `/ui-kit/android/threaded-messages-header` |
| message search | `/ui-kit/android/search` |
| message templates / custom types | `/ui-kit/android/message-template` (⚠️ verify symbols vs catalog — see core map) |
| voice/video call buttons | `/ui-kit/android/call-buttons` |
| incoming / outgoing call UI | `/ui-kit/android/incoming-call` · `outgoing-call` |
| call logs | `/ui-kit/android/call-logs` |
| calls setup / enable calling | `/ui-kit/android/calling-integration` · `call-features` · Calls SDK: `/calls/android/setup` |
| AI features (starter/replies/summary) | `/ui-kit/android/ai-features` |
| AI agent chat / assistant history | `/ui-kit/android/guide-ai-agent` · `/ui-kit/android/ai-assistant-chat-history` |
| notification feed | `/ui-kit/android/notification-feed` |
| push setup (FCM) | `/notifications/push-overview` |
| extensions (stickers/polls/translation…) | `/ui-kit/android/extensions` — **client half only**; see the enablement table below |
| theming / colors / styling | `/ui-kit/android/theme-introduction` · `color-resources` · `component-styling` · `message-bubble-styling` |
| customization (slots/styles/events/formatters…) | `/ui-kit/android/customization-overview` (+ the specific `customization-*` page) |
| localization / sounds | `/ui-kit/android/localize` · `sound-manager` |
| methods / events reference | `/ui-kit/android/methods` · `/ui-kit/android/events` |
| full component list | `/ui-kit/android/components-overview` |
| troubleshooting | `/ui-kit/android/troubleshooting` |
| v5→v6 migration / upgrade | `/ui-kit/android/upgrading-from-v5` |

## Enablement — the half that is NOT in `ui-kit/android`
Most "add <feature>" asks have a **dashboard/extension prerequisite**. The component renders and
nothing happens until it is switched on, so a skill that only wires the client has not finished the
job. These pages live OUTSIDE the UI-Kit tree — say the prerequisite out loud to the user, and fetch
the page when you need the exact steps.

| Intent | Enablement page (append `.md`) |
|---|---|
| any extension — first stop | `/fundamentals/extensions-overview` |
| polls · stickers | `/fundamentals/polls` · `/fundamentals/stickers` |
| collaborative whiteboard / document | `/fundamentals/collaborative-whiteboard` · `/fundamentals/collaborative-document` |
| link preview · thumbnail generation | `/fundamentals/link-preview` · `/fundamentals/thumbnail-generation` |
| message translation | `/fundamentals/message-translation` |
| smart replies · conversation starter · summary | `/fundamentals/ai-user-copilot/smart-replies` · `conversation-starter` · `conversation-summary` (overview: `/fundamentals/ai-user-copilot/overview`) |
| AI agents | `/ai-agents` |
| profanity filter / moderation | `/fundamentals/moderation-extensions` · `/moderation/overview` · `/moderation/getting-started` · `/moderation/rules-management` |
| push notifications (Android) | `/notifications/push-overview` · **`/notifications/android-push-notifications`** · `/notifications/badge-count` |
| campaigns / announcements | `/campaigns/campaigns` · `/campaigns/templates` · `/campaigns/channels` |
| auth keys, roles, permissions | `/fundamentals/user-auth` · `/fundamentals/user-roles-and-permissions` |
| server-side webhooks | `/fundamentals/webhooks-overview` · `/calls/webhooks` |

> Both scoped LLM indexes now carry this same routing, so either door reaches it:
> `{DOCS_BASE}/ui-kit/android/llms-android-v6.md` and
> `{SDK_DOCS_BASE}/sdk/android/v5/llms-android-v5.md`.

## Task guides (recipes) — for a whole FEATURE, BUILD FROM the guide + COMPARE against it (docs-maximal)
For a TASK/feature ask (a whole capability, not just one component's params), the docs ship **full
end-to-end guides**. **Discover them from the scoped llms index's "Task guides (recipes)" section**
(`{DOCS_BASE}/ui-kit/android/llms-android-v6.md`) — the index is the source of truth (new guides appear
there; do NOT bake this list). At time of writing it lists: `guide-overview` · `guide-threaded-messages` ·
`guide-block-unblock-user` · `guide-new-chat` · `guide-message-privately` · `guide-call-log-details` ·
`guide-group-chat` · `guide-search-messages` · `guide-ai-agent` · `custom-text-formatter-guide` ·
`mentions-formatter-guide` · `shortcut-formatter-guide`.
**Use the matching guide TWO ways — prefer it over baked recipe prose wherever a guide exists:**
1. **As the implementation SOURCE** — fetch `{DOCS_BASE}/ui-kit/android/<guide>.md` (your cohort's tab)
   and build the feature from the official recipe. **Adapt it ADDITIVELY** into the user's app (reuse
   their navigation/theme/auth; never drop in the guide's standalone shell).
2. **As a COMPLETENESS + CORRECTNESS check** — after you emit, DIFF your implementation against the
   guide: every component, param, step, and affordance covered? Fill any gap.
> **Then apply the baked HARDENING DELTAS on top — the guide is the BASELINE, not the whole truth:**
> credentials via `local.properties`→`BuildConfig` (guides hardcode placeholders); the init→login gate
> with failures surfaced; thread screens take the conversation target AND the parent message id;
> IME/insets sizing (`references/layout.md`); wire-or-hide every default-on affordance; listener
> teardown in the matching lifecycle. Build from the guide, then correct with these.

**No matching guide in the index? → continue EXACTLY as before** — build from the pack's baked
golden path + `component-props.md` and fetch each component's `.md` twin for exact params. **The guide
is an ENHANCEMENT when present, never a hard dependency.**

## Not in the table?
Fetch the scoped index (`{DOCS_BASE}/ui-kit/android/llms-android-v6.md`), pick the page, fetch its `.md`.
Never guess a path; never read kit source; never answer params from memory.
