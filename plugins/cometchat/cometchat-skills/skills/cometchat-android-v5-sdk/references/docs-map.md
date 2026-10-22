# docs-map — CometChat Android Chat SDK v5: intent → the exact docs page to fetch

## Reaching docs — PREFER the CometChat docs MCP; fetch is the fallback
The canonical doc channel is the **first-party CometChat docs MCP** — tools `search_cometchat_docs`,
`fetch_cometchat_doc_page`, and `get_cometchat_implementation_bundle`. **If those tools are connected,
use them instead of a raw web fetch:**
- **Find the page** → `search_cometchat_docs(query, version?)` — replaces browsing the scoped `llms-*` index.
- **Read the page** → `fetch_cometchat_doc_page(path)` — pass the SAME versioned `<path>` the tables below
  list (e.g. `/sdk/android/v5/<page>`); the MCP resolves the `.md` twin and returns raw Markdown. A full
  `https://…/docs/<path>` URL also works. (The v5-vs-v4 URL trap below still applies to the path you pass.)
- **A whole feature/recipe** → `get_cometchat_implementation_bundle(...)` is **NON-AUTHORITATIVE** — curated STATIC recipes that can lag the live docs (verified stale vs v7: e.g. `CometChatConversationsWithMessages`, `css-variables.css`). Treat any bundle as a hint only: RECONCILE it against the `fetch_cometchat_doc_page` result + the pack's hardening; never emit bundle code verbatim.

The MCP reads whatever docs environment it is pointed at (production by default; a preview when repointed),
so it also carries the environment-swap concern below — no hardcoded host on the skill side.

**If the MCP tools are NOT connected:** add it (`claude mcp add --transport http cometchat-docs https://mcp.cometchat.com/mcp`, or reinstall/enable the plugin) and retry; only if it still will not connect, fall back to a plain fetch via `SDK_DOCS_BASE` (defined next).
Either way the `<path>` catalog in this file is the source of truth for WHICH page — MCP-vs-fetch is only HOW.

## SDK_DOCS_BASE — the fetch FALLBACK entry point (⚠️ SWAP HERE to change environments)
```
SDK_DOCS_BASE = https://www.cometchat.com/docs
```
> **⚠️ URL TRAP — the Android SDK is VERSIONED.** v5 pages live at `/sdk/android/v5/<page>`.
> The UNVERSIONED tree `/sdk/android/<page>` is **v4** — never fetch it for a v5 build.
> (The UI Kit is the opposite: its latest, v6, lives at the unversioned `/ui-kit/android/…`.)
>
> **Fetch rule:** build a URL as `SDK_DOCS_BASE` + the path shown, then append `.md`.
> Never decompile the AAR and never answer an API from memory.

## The convention
`SDK_DOCS_BASE` + `<path>` + `.md` → raw Markdown (verbatim code + method signatures, parameters,
listener contracts). Pages show Kotlin and Java variants where they differ — read the one the app uses.
```
Fetch:  {SDK_DOCS_BASE}/sdk/android/v5/send-message.md
```
Fallback order: `.md` twin → the same URL **without** `.md` (HTML) → **never** kit/AAR internals.

## Scoped Android SDK v5 index (prefer over the global llms.txt)
```
{SDK_DOCS_BASE}/sdk/android/v5/llms-android-v5.md
```
An Android-SDK-v5-only index of every page as a `.md` link, grouped by area (Messaging · Calling ·
Users · Groups · AI & advanced · Resources & listeners · Advanced). Use it to discover any page not
in the table below. Global all-products index (large; last resort): `{SDK_DOCS_BASE}/llms.txt`.
> **DOCS-GAP note:** this scoped index ships with docs branch `docs/android-llms-indexes`; until that
> merges, the per-page `.md` twins below already work — fall back to this table.

## Don't fetch the hot path — it's baked
Install, `initFromSettings → login` ordering, the method map, and the listener add/remove discipline
are BAKED in `cometchat-android-v5-sdk`. Fetch ONLY for exhaustive parameters, long-tail methods,
group/user management details, calling, or edge-case listeners.

## The 80% trigger table  (URL = `{SDK_DOCS_BASE}` + path, then append `.md`)
| Intent | Path (append `.md`) |
|---|---|
| install / init / app settings | `/sdk/android/v5/setup` |
| login, auth tokens, session | `/sdk/android/v5/authentication-overview` · `/sdk/android/v5/login-listeners` |
| send a text message | `/sdk/android/v5/send-message` |
| media / file / attachments | `/sdk/android/v5/upload-files` |
| receive messages (listeners) | `/sdk/android/v5/receive-messages` · `/sdk/android/v5/real-time-listeners` |
| message history / filtering / pagination | `/sdk/android/v5/additional-message-filtering` |
| conversations list | `/sdk/android/v5/retrieve-conversations` · `/sdk/android/v5/delete-conversation` |
| threads | `/sdk/android/v5/threaded-messages` |
| edit / delete / flag a message | `/sdk/android/v5/edit-message` · `delete-message` · `flag-message` |
| typing indicators | `/sdk/android/v5/typing-indicators` |
| delivery & read receipts | `/sdk/android/v5/delivery-read-receipts` |
| reactions | `/sdk/android/v5/reactions` |
| mentions | `/sdk/android/v5/mentions` |
| transient messages | `/sdk/android/v5/transient-messages` |
| users: list / manage / block | `/sdk/android/v5/retrieve-users` · `user-management` · `block-users` |
| presence | `/sdk/android/v5/user-presence` |
| groups: list / create / update / join / leave / delete | `/sdk/android/v5/retrieve-groups` · `create-group` · `update-group` · `join-group` · `leave-group` · `delete-group` |
| group members + moderation | `/sdk/android/v5/retrieve-group-members` · `group-add-members` · `group-kick-member` · `group-change-member-scope` · `transfer-group-ownership` |
| calling | `/sdk/android/v5/calling-overview` (+ the `/calls/android/*` tree for call UI/behavior) |
| AI moderation / agents / copilot / chatbots | `/sdk/android/v5/ai-moderation` · `ai-agents` · `ai-user-copilot-overview` · `ai-chatbots-overview` |
| campaigns · extensions · webhooks | `/sdk/android/v5/campaigns` · `extensions-overview` · `webhooks-overview` |
| message structure / key concepts | `/sdk/android/v5/message-structure-and-hierarchy` · `key-concepts` |
| connection status / behaviour | `/sdk/android/v5/connection-status` · `connection-behaviour` |
| rate limits | `/sdk/android/v5/rate-limits` |
| Play Store publishing | `/sdk/android/v5/publishing-app-on-playstore` |
| upgrading from v4 | `/sdk/android/v5/upgrading-from-v4` |
| changelog | `/sdk/android/v5/changelog` |

## Want ready-made UI instead?
If the user would accept drop-in chat UI, the **Android UI Kit v6** is far less code —
`cometchat-android-v6-core` and `{SDK_DOCS_BASE}/ui-kit/android/llms-android-v6.md`. Say so before
hand-building a full chat UI on the SDK.

## Not in the table?
Fetch the scoped index (`{SDK_DOCS_BASE}/sdk/android/v5/llms-android-v5.md`), pick the page, fetch its
`.md`. Never guess a path; never read AAR internals; never answer an API from memory.
