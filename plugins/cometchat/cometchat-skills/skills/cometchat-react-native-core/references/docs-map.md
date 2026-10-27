# docs-map — CometChat React Native v5: intent → the exact docs page to fetch

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
block: package, peers, key props/methods). 51 of 56 RN pages carry that block — read it FIRST.
```
Fetch:  {DOCS_BASE}/ui-kit/react-native/message-list.md
```
Fallback order: `.md` twin → if it 404s, the same URL **without** `.md` (HTML) → **never** a `.d.ts`.

## Scoped React Native index (prefer over the global llms.txt)
```
{DOCS_BASE}/ui-kit/react-native/llms-react-native-v5.md
```
A React-Native-v5-only index of every page as a `.md` link (~3k tok) — use it to discover any page
not in the table below. Global all-products index (large, ~25k tok; last resort): `{DOCS_BASE}/llms.txt`.

## SDK docs — the FALLBACK reference (a feature the UI Kit has NO component for)
The rule of the pack: **for every feature, first check whether the UI Kit has a component/prop for it**
(this file's table + the catalog). **If it does — USE it. If it does NOT — drop to the React Native
Chat SDK** and call its methods directly (the SDK is already installed under the UI Kit; init/login
already use it). Look the method up — never guess:
```
SDK_DOCS_BASE = https://www.cometchat.com/docs
```
- **SDK index (scoped — PREFER this):** `{SDK_DOCS_BASE}/sdk/react-native/llms-react-native-v4.md` —
  a **React-Native-SDK-v4-only** routing index grouped by area (Messaging · Calling · Users · Groups ·
  AI & campaigns · Listeners · Key Concepts). Start here to find the feature's page.
  **Do NOT use the site-wide global `llms.txt`** except as a last resort.
- **Convention:** `{SDK_DOCS_BASE}/sdk/react-native/<page>` + `.md`.
- ⚠️ **RN has its OWN SDK.** It is `@cometchat/chat-sdk-react-native@4`, **not**
  `@cometchat/chat-sdk-javascript`. Never fetch `/sdk/javascript/*` for a React Native task.

### SDK-fallback features (kit v5 ships NO component — this is not optional depth)
| Need | No component because | SDK path |
|---|---|---|
| user / group details screen | kit v5 removed `CometChatDetails` | `/sdk/react-native/groups-overview` → `CometChat.getUser` / `getGroup` |
| add members | kit v5 removed `CometChatAddMembers` | `/sdk/react-native/group-add-members` → `addMembersToGroup` |
| **banned members (view + unban)** | **no UI surface at all in v5** | `/sdk/react-native/group-kick-ban-members` → `BannedMembersRequestBuilder`, `unbanGroupMember` |
| transfer ownership | kit v5 removed `CometChatTransferOwnership` | `/sdk/react-native/transfer-group-ownership` |
| call log detail / history / participants | kit v5 keeps only the list | **calls** SDK → `CometChatCalls.CallLogRequestBuilder` |

> An app that can **ban** but cannot **view or unban** is an unclosed round-trip — ship the pair.

### PATTERN SOURCE for the above — the official sample app
The kit has no component, so do **not** invent a layout. Cite the real implementation:
`github.com/cometchat/cometchat-uikit-react-native/tree/v5/examples/SampleApp`
(e.g. `src/components/CometChatDetails/CometChatUserDetails.tsx`).
⚠️ Those are sample-app **directory paths**, not kit exports — never `import` them.

## Don't fetch the hot path — it's baked
Install, the provider chain, `init → login → render`, and the drop-in props for "add chat" are BAKED
in `cometchat-react-native-core`. Fetch ONLY for exhaustive props, long-tail components, theming
tokens, or feature enablement.

## The 80% trigger table  (URL = `{DOCS_BASE}` + path, then append `.md`)
| Intent | Path (append `.md`) |
|---|---|
| setup / init / login (bare RN) | `/ui-kit/react-native/react-native-cli-integration` |
| setup (Expo) | `/ui-kit/react-native/expo-integration` |
| conversation list (full props) | `/ui-kit/react-native/conversations` |
| message list | `/ui-kit/react-native/message-list` |
| message composer | `/ui-kit/react-native/message-composer` |
| compact composer | `/ui-kit/react-native/compact-message-composer` |
| message header | `/ui-kit/react-native/message-header` |
| users / groups / group members | `/ui-kit/react-native/users` · `groups` · `group-members` |
| threads | `/ui-kit/react-native/threaded-messages-header` |
| theming / tokens / dark mode | `/ui-kit/react-native/theme` · `colors` · `component-styling` |
| localization | `/ui-kit/react-native/localize` |
| events | `/ui-kit/react-native/events` |
| calls (UI) | `/ui-kit/react-native/calling-integration` · `call-features` · `call-buttons` · `call-logs` · `incoming-call` · `outgoing-call` |
| AI / smart replies | `/ui-kit/react-native/ai-features` |
| search | `/ui-kit/react-native/search` |
| full-screen recipes | `/ui-kit/react-native/react-native-conversation` · `expo-conversation` |
| task guides | `/ui-kit/react-native/guide-new-chat` · `guide-group-chat` · `guide-search-messages` · `guide-threaded-messages` · `guide-block-unblock-user` · `guide-message-privately` |

## ⚠️ DOCS-GAP protocol — flag, never silently source-fill
If a needed component/prop/SDK method is NOT covered by the docs, **FLAG it for the developer**
(page · section · change · reason) and record it. Do **not** quietly read the kit source and bake the
answer as if it were documented — that hides the gap and the next agent re-derives it.

**Known open gaps for React Native (tracked on ENG-38205 as `RN-G*`):**
reactions undocumented · no per-bubble pages · attachment cluster undocumented · `ConversationStarter`
/ `SmartReplies` undocumented · the `DataSourceDecorator` chain undocumented · six pages **import
symbols the kit does not export** · the events page names APIs that do not exist.
Until those land, build from the catalog + kit source **and say so in the flag**.

## ⚠️ Names that differ from the React docs — never port a React snippet
The React UI Kit is a different package with a different API. Verified against
`@cometchat/chat-uikit-react-native@5.4.0`:

| React (do NOT use on RN) | React Native |
|---|---|
| `new UIKitSettingsBuilder()…build()` | a plain `UIKitSettings` **object** — there is no builder export |
| `CometChatUIKit.login(uid)` | `CometChatUIKit.login({ uid })` — an **object** |
| `CometChatMessagePlugin` / `PluginRegistry` | `ChatConfigurator.enable(...)` + a `DataSourceDecorator` subclass |
| `CometChatUrlFormatter` | `CometChatUrlsFormatter` (**plural**) |
| `CometChatCollaborativeWhiteboardBubble` | `CometChatCollaborativeWhiteBoardBubble` (**capital B**) |
| `CometChatFlagMessageDialog` | `CometChatReportDialog` |
| `CometChatErrorBoundary` | none — use a plain React error boundary |
| `CometChatThreadHeader` (same name, web layout) | same name, but it is a **screen**, not a side panel |
| CSS variables / `--cometchat-*` | `CometChatThemeProvider` + `useTheme()` |

| custom message type (decorator) | [message-list]({DOCS_BASE}/ui-kit/react-native/message-list.md) — "Filtering Messages" | The FETCH half (`getAllMessageTypes` / `getAllMessageCategories`) and the after-`login()` registration order. Overriding only `getAllMessageTemplates` renders a bubble that vanishes on reload. |
