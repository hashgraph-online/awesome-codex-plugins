# docs-map — CometChat React v7: intent → the exact docs page to fetch

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
> **Fetch rule:** always build a URL as `DOCS_BASE` + the path shown, then append `.md`.
> Never hardcode a host anywhere else; never read `node_modules`/`.d.ts`.

## The convention
`DOCS_BASE` + `<path>` + `.md` → raw Markdown (verbatim code + an "AI Integration Quick Reference"
JSON block: prop names, types, defaults).
```
Fetch:  {DOCS_BASE}/ui-kit/react/components/conversations.md
```
Fallback order: `.md` twin → if it 404s, the same URL **without** `.md` (HTML) → **never** a `.d.ts`.

## Scoped React v7 index (prefer over the global llms.txt)
```
{DOCS_BASE}/ui-kit/react/llms-react-v7.md
```
A React-v7-only index of every page as a `.md` link (~3k tok) — use it to discover any page not in
the table below. Global all-products index (large, ~25k tok; last resort): `{DOCS_BASE}/llms.txt`.

## SDK docs — the FALLBACK reference (a feature the UI Kit has NO component for)
The rule of the pack: **for every feature, first check whether the UI Kit has a component/prop for it
(this file's table + `component-props.md` + the catalog). If it does — USE it. If it does NOT** (e.g.
AI agents, campaigns, advanced/AI moderation, transient messages, bots, webhooks, low-level presence)
**— drop to the JavaScript Chat SDK and call its methods directly** (the SDK library is already
installed under the UI Kit; init/login already use it). Look the method up in the SDK docs — never guess:
```
SDK_DOCS_BASE = https://www.cometchat.com/docs
```
- **SDK index (scoped — PREFER this):** `{SDK_DOCS_BASE}/sdk/javascript/llms-javascript-v4.md` — a **JS-SDK-v4-only** routing index of every SDK page as a `.md` twin, grouped by area (Messaging · Calling · Users · Groups · **AI, campaigns & webhooks: AI Moderation · AI Agents · AI Copilot · Campaigns · Webhooks** · Real-time Listeners · Key Concepts · …). Start here to find the feature's page. **Do NOT use the site-wide global `{SDK_DOCS_BASE}/llms.txt`** (all products, far larger) except as a last resort if the scoped index 404s — mirrors the React scoped-index rule above.
- **Convention:** `{SDK_DOCS_BASE}/sdk/javascript/<page>` then append `.md` for the raw Markdown twin. Each SDK page opens with an **"AI Integration Quick Reference" accordion** (Package · Import · **Key methods**) — read that FIRST for the exact method names/signatures, then the tables + TS/JS examples below.
- **Example:** AI agents → `{SDK_DOCS_BASE}/sdk/javascript/ai-agents.md` → `CometChat.addAIAssistantListener(id, …)`, `CometChat.AIAssistantMessage`, `CometChat.AIToolCall`, `getAssistantMessageData()`, …
> Never hand-roll a feature that exists in the UI Kit OR the SDK, and never guess an SDK method — look it up in the SDK index → the page's Quick-Reference accordion.

## Don't fetch the hot path — it's baked
Install, `init → login → render`, the provider, and the ~12 drop-in props for "add chat" are BAKED
in `cometchat-react-v7-core`. Fetch ONLY for exhaustive props / view-slots / long-tail components /
theming tokens / feature enablement.

## The 80% trigger table  (URL = `{DOCS_BASE}` + path, then append `.md`)
| Intent | Path (append `.md`) |
|---|---|
| setup / init / login / render | `/ui-kit/react/integration-react` |
| Next.js / React Router / Astro setup | `/ui-kit/react/integration-nextjs` · `-react-router` · `-astro` |
| conversation list (full props) | `/ui-kit/react/components/conversations` |
| message list | `/ui-kit/react/components/message-list` |
| message composer | `/ui-kit/react/components/message-composer` |
| message header | `/ui-kit/react/components/message-header` |
| users / groups / group members | `/ui-kit/react/components/users` · `groups` · `group-members` |
| threads | `/ui-kit/react/components/thread-header` |
| message search | `/ui-kit/react/components/search` |
| reactions | `/ui-kit/react/components/reactions` |
| message bubbles (swap/custom) | `/ui-kit/react/components/<x>-bubble` (text/image/video/audio/file/poll/sticker/card…) |
| voice/video call buttons | `/ui-kit/react/components/call-buttons` |
| incoming / outgoing call UI | `/ui-kit/react/components/incoming-call` · `outgoing-call` |
| call logs | `/ui-kit/react/components/call-logs` |
| calls setup / enable calling (calls-setup) | `/ui-kit/react/integration-react` · Calls SDK: `/calls/javascript/setup` |
| custom call surface / joinSession (calls-react-integration) | `/calls/javascript/react-integration` |
| screen-share · recording · device-select · idle-timeout · virtual-bg | `/calls/javascript/screen-sharing` · `recording` · `device-management` · `idle-timeout` · `virtual-background` |
| AI assistant | `/ui-kit/react/components/ai-assistant-chat` |
| web push setup (push-overview / web-push) | `/notifications/push-overview` · `/notifications/web-push-notifications` |
| notification preferences / mute (notification-preferences) | `/notifications/preferences` |
| theming / CSS `--cometchat-*` tokens | `/ui-kit/react/theming` |
| plugins | `/ui-kit/react/plugins/overview` |
| event system | `/ui-kit/react/event-system` |
| full component list | `/ui-kit/react/components-overview` |
| v6→v7 migration / upgrade | `/ui-kit/react/migration-overview` · `/ui-kit/react/migration-property-changes` |

## Task guides (recipes) — for a whole FEATURE, BUILD FROM the guide + COMPARE against it (docs-maximal)
For a TASK/feature ask (a whole capability, not just one component's props), the docs ship **full end-to-end
guides**. **Discover them from the scoped llms index's "Task guides (recipes)" section**
(`{DOCS_BASE}/ui-kit/react/llms-react-v7.md`) — the index is the source of truth (new guides appear there;
do NOT bake this list). At time of writing it lists: `guide-new-chat-creation` · `guide-group-chat-setup` ·
`guide-search-messages` · `guide-threaded-messages` · `guide-message-privately` · `guide-block-unblock-user`.
**Use the matching guide TWO ways — prefer it over baked recipe prose wherever a guide exists:**
1. **As the implementation SOURCE** — fetch `{DOCS_BASE}/ui-kit/react/<guide>.md` and build the feature from
   the official recipe. **Adapt it ADDITIVELY** into the user's app (reuse their routing/auth/layout; never
   drop in the guide's standalone shell).
2. **As a COMPLETENESS + CORRECTNESS check** — after you emit, DIFF your implementation against the guide:
   did you cover every component, prop, step, and affordance it shows? Fill any gap. This is the docs-sourced
   completeness oracle (richer + more current than a baked minimum).
> **Then apply the baked HARDENING DELTAS on top — the guide is the BASELINE, not the whole truth.** The
> guides do NOT carry the audit lessons: thread list/composer need the conversation **`user`/`group` AND**
> `parentMessageId` (AUDIT-060); in-chat search must be **scoped** (`uid`/`guid`) vs global (AUDIT-041);
> container **sizing** (`100dvh` + column CSS); wrap in **`CometChatErrorBoundary`**; roster lists **double
> under StrictMode** (dev); **wire-or-hide** every default-on affordance. Build from the guide, then correct
> with these. (Several audits were literally GAPS in the official guide — the guide gets you complete, the
> deltas get you correct.)

**No matching guide in the index? → continue EXACTLY as before** — build from the pack's baked golden-path /
recipe (`FULL-APP-BLUEPRINT`, placement recipes, `component-props.md`) and fetch each component's `.md` twin
for exact props. **The guide is an ENHANCEMENT when present, never a hard dependency** — a feature without a
task guide is built the normal way, not blocked.

## Not in the table?
Fetch the scoped index (`{DOCS_BASE}/ui-kit/react/llms-react-v7.md`), pick the page, fetch its `.md`.
Never guess a path; never read `.d.ts`; never answer props from memory.
