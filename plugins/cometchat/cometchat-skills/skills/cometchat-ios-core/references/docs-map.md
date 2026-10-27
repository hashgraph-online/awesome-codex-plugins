# docs-map — CometChat iOS v5: intent → the exact docs page to fetch

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

**If the MCP tools are NOT connected:** add it (`claude mcp add --transport http cometchat-docs https://mcp.cometchat.com/mcp`, or reinstall/enable the plugin) and retry; only if it still will not connect, fall back to a plain fetch via `DOCS_BASE`/`SDK_DOCS_BASE` (defined next).
Either way the `<path>` catalog in this file is the source of truth for WHICH page — MCP-vs-fetch is only HOW.

## DOCS_BASE — the fetch FALLBACK entry point (⚠️ SWAP HERE to change environments)
```
DOCS_BASE     = https://www.cometchat.com/docs
SDK_DOCS_BASE = https://www.cometchat.com/docs
```
> **Fetch rule:** always build a URL as `DOCS_BASE` + the path shown, then append `.md`.
> Never hardcode a host anywhere else; **never** read the kit's `.swiftinterface`, and never
> answer API from memory.
>
> **Docs note (`DOCS-BACKLOG.md`):** the v4 composite components (`*WithMessages`) do not exist in
> 5.1.22. The live pages now say so (`conversations.md` states there is no composite; `*WithMessages`
> survives only on `upgrading-from-v4`, correctly as the v4 "before" side). Still: verify every symbol
> against `catalogs/ios-v5.json` before emitting — the catalog is the ground truth, not the docs.

## The convention
`DOCS_BASE` + `<path>` + `.md` → raw Markdown (verbatim Swift + an "AI Integration Quick Reference"
block: component, package, props, callbacks).
```
Fetch:  {DOCS_BASE}/ui-kit/ios/conversations.md
```
Fallback order: `.md` twin → if it 404s, the same URL **without** `.md` (HTML) → **never** the
`.swiftinterface`, never memory.

## Scoped iOS v5 index
```
{DOCS_BASE}/ui-kit/ios/llms-ios-v5.md
```
> Covers all 51 iOS UI Kit v5 pages, and its **"Task guides (recipes)"** section is the source for
> the guide list below. Prefer this index over the site-wide `{DOCS_BASE}/llms.txt` (large; last
> resort). The twin of React's `llms-react-v7.md` and Angular's `llms-angular-v5.md`.
> If this path 404s, fall back to the trigger table below.

## SDK docs — the FALLBACK reference (a feature the UI Kit has NO component for)
The rule of the pack: **for every feature, first check whether the UI Kit has a component for it**
(the table below + `catalogs/ios-v5.json`). **If it does — USE it. If it does NOT** (AI agents,
campaigns, moderation, add-members, transient messages, low-level presence, webhooks) **— drop to the
Chat SDK and call its method directly.** The SDK is already linked under the kit. Look the method up —
never guess:
- **SDK index:** prefer the scoped `{SDK_DOCS_BASE}/sdk/ios/llms-ios-v4.md` — it routes every iOS
  Chat SDK v4 page by intent. If it 404s, fall back to `{SDK_DOCS_BASE}/sdk/ios/overview.md` and
  the page for the area.
- **Convention:** `{SDK_DOCS_BASE}/sdk/ios/<page>` + `.md`. Each page opens with an **"AI Integration
  Quick Reference"** accordion (package · import · key methods) — read that FIRST.
- **Worked example (the kit ships no component):** adding group members →
  `{SDK_DOCS_BASE}/sdk/ios/group-add-members.md` →
  `CometChat.addMembersToGroup(guid:groupMembers:bannedUIDs:onSuccess:onError:)`, driven from a
  `CometChatUsers` picker in `selectionMode`.

## Don't fetch the hot path — it's baked
Install, the exact version trio, `init → login → render`, the golden-path composition and its five
layout rules are BAKED in `cometchat-ios-core`. Fetch ONLY for exhaustive API, long-tail components,
theming tokens, or feature enablement.

## The 80% trigger table  (URL = `{DOCS_BASE}` + path, then append `.md`)
| Intent | Path (append `.md`) |
|---|---|
| install / init / login / permissions | `/ui-kit/ios/getting-started` |
| conversation list → chat screen (THE core recipe) | `/ui-kit/ios/ios-conversation` |
| 1:1 or group chat from a user/group list | `/ui-kit/ios/ios-one-to-one-chat` |
| tab-based app | `/ui-kit/ios/ios-tab-based-chat` |
| conversation list (full API) | `/ui-kit/ios/conversations` |
| message list · composer · header | `/ui-kit/ios/message-list` · `message-composer` · `message-header` |
| users · groups · group members | `/ui-kit/ios/users` · `groups` · `group-members` |
| threads | `/ui-kit/ios/threaded-messages-header` |
| search | `/ui-kit/ios/search` |
| call buttons · incoming · outgoing · ongoing · logs | `/ui-kit/ios/call-buttons` · `incoming-call` · `outgoing-call` · `ongoing-call` · `call-logs` |
| calling setup | `/ui-kit/ios/calling-integration` |
| AI features / assistant history | `/ui-kit/ios/ai-features` · `/ui-kit/ios/ai-assistant-chat-history` |
| theming: tokens · colors · per-component · bubbles | `/ui-kit/ios/theme-introduction` · `color-resources` · `component-styling` · `message-bubble-styling` |
| localization · sounds | `/ui-kit/ios/localize` · `/ui-kit/ios/sound-manager` |
| formatters (mentions · shortcuts) | `/ui-kit/ios/mentions-formatter-guide` · `shortcut-formatter-guide` |
| message templates | `/ui-kit/ios/message-template` |
| events | `/ui-kit/ios/events` |
| extensions (dashboard-gated) | `/ui-kit/ios/extensions` |
| full component list | `/ui-kit/ios/components-overview` |
| v4 → v5 upgrade | `/ui-kit/ios/upgrading-from-v4` |
| push notifications | `/notifications/push-overview` |

## Task guides (recipes) — for a whole FEATURE, BUILD FROM the guide + COMPARE against it
For a TASK ask (a whole capability, not one component's API), the docs ship **end-to-end guides**. iOS
has **nine** — more than React:
`guide-overview` · `guide-new-chat` · `guide-group-chat` · `guide-group-ownership` ·
`guide-threaded-messages` · `guide-message-privately` · `guide-block-unblock-user` ·
`guide-call-log-details` · `guide-ai-agent`
(at `{DOCS_BASE}/ui-kit/ios/<guide>.md`). Use the matching guide **two ways**:
1. **As the implementation SOURCE** — build the feature from the official recipe, adapted
   **ADDITIVELY** into the user's app (reuse their navigation, auth and layout; never drop in the
   guide's standalone shell).
2. **As a COMPLETENESS check** — after you emit, DIFF your implementation against the guide: every
   component, call and affordance it shows. Fill any gap.

> **Then apply the baked HARDENING DELTAS — the guide is the BASELINE, not the whole truth.**
> The guides do not carry the runtime lessons: `set(controller:)` on every component or its
> affordances are inert; the composer pinned to the **safe-area bottom** (NOT `keyboardLayoutGuide` — the kit composer already handles the keyboard, and double-pinning collapses the list)
> the recipe shows; explicit vertical division or the list collapses; the host nav bar hidden or you
> get two headers; and the thread trap — `CometChatThreadedMessageHeader` takes
> `set(parentMessage:)`; the LIST takes `set(user:parentMessage:withParent:)` (parent in the same
> call as the target); the composer takes `set(user:)` + `set(parentMessageId:)`.

**No matching guide? → build from this skill's baked golden path** and fetch each component's `.md`
twin for exact API. The guide is an enhancement when present, never a hard dependency.

## Not in the table?
Fetch the page from the trigger table nearest your intent, or the site-wide `{DOCS_BASE}/llms.txt`.
Never guess a path; never read the `.swiftinterface`; never answer API from memory. If a symbol is not
in `catalogs/ios-v5.json`, it does not exist in v5 — do not emit it, whatever a page says.
