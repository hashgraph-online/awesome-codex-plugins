# docs-map — CometChat Calls SDK v5 (JavaScript, headless): intent → the exact docs page to fetch

## Reaching docs — PREFER the CometChat docs MCP; fetch is the fallback
The canonical doc channel is the **first-party CometChat docs MCP** — tools `search_cometchat_docs`,
`fetch_cometchat_doc_page`, and `get_cometchat_implementation_bundle`. **If those tools are connected,
use them instead of a raw web fetch:**
- **Find the page** → `search_cometchat_docs(query)` — e.g. `search_cometchat_docs("calls javascript join session")`.
- **Read the page** → `fetch_cometchat_doc_page(path)` — pass the SAME `<path>` the tables below list; the MCP
  resolves the `.md` twin and returns raw Markdown. A full `https://…/<path>` URL also works.
- **A whole feature/recipe** → `get_cometchat_implementation_bundle(...)` is **NON-AUTHORITATIVE** — curated
  STATIC recipes that can lag the live docs. Treat any bundle as a hint only: RECONCILE it against the
  `fetch_cometchat_doc_page` result + the catalog; never emit bundle code verbatim.

The MCP reads whatever docs environment it is pointed at (production by default; a preview when repointed),
so it also carries the environment-swap concern below — no hardcoded host on the skill side.

**If the MCP tools are NOT connected:** add it (`claude mcp add --transport http cometchat-docs https://mcp.cometchat.com/mcp`, or reinstall/enable the plugin) and retry; only if it still will not connect, fall back to a plain fetch via `DOCS_BASE` (defined next).
Either way the `<path>` catalog in this file is the source of truth for WHICH page — MCP-vs-fetch is only HOW.

## DOCS_BASE — the fetch FALLBACK entry point (⚠️ SWAP HERE to change environments)
```
DOCS_BASE = https://www.cometchat.com/docs
```
> Production docs (`https://www.cometchat.com/docs`). **Fetch rule:** build a URL as `DOCS_BASE` + the path shown,
> then append `.md`. Never hardcode a host anywhere else; never read `node_modules`/`.d.ts`.

## The convention — Calls v5 lives at the UNVERSIONED root `/calls/javascript/`
`DOCS_BASE` + `<path>` + `.md` → raw Markdown (verbatim code + prop/parameter tables).
```
Fetch:  {DOCS_BASE}/calls/javascript/overview.md
```
> **⚠️ VERSION TRAP.** The **unversioned** `/calls/javascript/**` tree IS **v5** (matches the installed
> `@cometchat/calls-sdk-javascript@5`). The `/calls/v4/**` tree is the OLD v4 SDK — never fetch it for a v5
> build. Legacy `/sdk/javascript/<n>.0/calling-*` pages are older still. When in doubt, prefer the page whose
> body says "Calls SDK v5".

## Scoped index (prefer over the global llms.txt)
```
{DOCS_BASE}/llms.txt
```
Use it to discover any page not listed below (search for `/calls/javascript/`).

## Path catalog — intent → page (all under `/calls/javascript/`)
| Intent | Path |
|---|---|
| SDK overview · architecture · call-flow | `/calls/javascript/overview` |
| Install + `init` / `initFromSettings` | `/calls/javascript/setup` |
| Login / auth-token / user mgmt | `/calls/javascript/authentication` |
| `generateToken` + `joinSession` (meet-style) | `/calls/javascript/join-session` |
| **1:1 RINGING** — initiate · incoming-call listener + **incoming/outgoing call-screen UI** · accept/reject/cancel · then `generateToken`/`joinSession` | `/calls/javascript/ringing` |
| Session settings (the `SessionSettings` object) | `/calls/javascript/session-settings` |
| Events (`addEventListener` — full event list) | `/calls/javascript/events` |
| In-call actions (mute/pause/leave/layout/record…) | `/calls/javascript/actions` |
| **Custom control panel** — replace the built-in controls: hide the whole panel (`hideControlPanel`) OR hide INDIVIDUAL buttons, then drive your own UI off the action methods + keep it in sync via events | `/calls/javascript/custom-control-panel` — the canonical recipe for `SKILL.md` pitfall #1's "user EXPLICITLY wants custom controls" path. Carries the per-button hide flags the session-settings page doesn't foreground: `hideRaiseHandButton` · `hideShareInviteButton` · `hideParticipantListButton` · `hideChatButton` (plus `hideLeaveSessionButton`/`hideToggleAudioButton`/`hideToggleVideoButton`/`hideScreenSharingButton`/`hideRecordingButton`/`hideChangeLayoutButton`/`hideVirtualBackgroundButton`) — all real in the installed `.d.ts`. |
| Call layouts (TILE / SIDEBAR / SPOTLIGHT) | `/calls/javascript/call-layouts` |
| Participant management (pin / mute / list) | `/calls/javascript/participant-management` |
| Recording | `/calls/javascript/recording` |
| Screen sharing | `/calls/javascript/screen-sharing` |
| Virtual background | `/calls/javascript/virtual-background` |
| Raise hand | `/calls/javascript/raise-hand` |
| Idle timeout | `/calls/javascript/idle-timeout` |
| Share invite | `/calls/javascript/share-invite` |
| Call logs (`CallLogRequestBuilder`) | `/calls/javascript/call-logs` — ⚠️ **the live example OMITS the REQUIRED `.setAuthToken(token)` — copying it verbatim BREAKS AT RUNTIME.** The page now DOES document the client-SDK `CallLogRequestBuilder` (added in v5.0.5, in its "Transcripts" section) — but its snippet is `new CometChatCalls.CallLogRequestBuilder().setLimit(30).setHasTranscriptions(true).build()` with **no `setAuthToken`**, and the builder does **NOT** implicitly use the logged-in user's token: `fetchNext()` then throws `{ code: "NOT_ENOUGH_PARAMETERS", message: "`Auth Token` is required to use the fetchNext() method." }` (verified live vs installed `@cometchat/calls-sdk-javascript@5.0.5`, explorer `web-calls-v5`). **EMIT THE BAKED RECIPE, not the doc snippet:** `new CometChatCalls.CallLogRequestBuilder().setLimit(n).setAuthToken(CometChatCalls.getUserAuthToken()).build().fetchNext()` → `Promise<CallLog[]>` (paginated; read `getSessionID`/`getType`/`getStatus`/`getTotalDuration`/`getInitiatedAt`/…). `setAuthToken` is REQUIRED; pass the logged-in user's token from `CometChatCalls.getUserAuthToken()`. Use the SDK builder for an in-app call-log list; don't send the user to the REST API. (Docs bug tracked in `DOCS-BACKLOG.md`; this baked recipe stays authoritative over the doc snippet until it's fixed.) |
| **React** integration (provider + call screen) | `/calls/javascript/react-integration` |
| Vue / Angular / Next.js / Ionic integration | `/calls/javascript/{vue,angular,nextjs,ionic}-integration` |

## DOCS-GAP — `initFromSettings` shape is NOT on the live docs (bake it here)
> **Referenced by `SKILL.md` (Init & login ordering).** The `/calls/javascript/setup` page documents ONLY
> `init({ appId, region })` — it does **not** document `CometChatCalls.initFromSettings(...)`, even though the
> method is real and shipped (installed `@cometchat/calls-sdk-javascript@5` `.d.ts`). Until the docs add it,
> the `initFromSettings` argument shape (the non-exported `CometChatSettings` interface — real in the
> installed `.d.ts`, so absent from the exports-only catalog) is baked here so the skill is not a dead-end:
> ```ts
> await CometChatCalls.initFromSettings({
>   appId: "APP_ID",
>   region: "us",                         // 'us' | 'eu' | 'in'
>   credentials: { authKey: "AUTH_KEY" }, // dev-only auth key
>   callsSDK: { adminHost: null, clientHost: null, host: null },
>   chatSDK: {},                          // Record<string, unknown>
>   uiKit: {},                            // Record<string, unknown>
> });
> ```
> The skills **DEFAULT to `CometChatCalls.initFromSettings(settings)`** — pass the settings object **INLINE**
> (no physical `cometchat-settings.json` file needed). It is the **ai-agent-only telemetry init**
> (persists `integrationSource="ai-agent"`), **INTENTIONALLY undocumented** (`@nodoc`, same posture as
> `CometChatUIKit.initFromSettings` — DOCS-BACKLOG F4), which is WHY the shape is baked here. The
> publicly-documented **`init({ appId, region })` is the FALLBACK only** (a non-skills / doc-following
> context). Do NOT tell a user to "fetch the shape from `/calls/javascript/setup`": that page does not carry
> it. (Explorer `web-calls-v5`, AUDIT-169.)

## 1:1 RINGING (meet-style needs none of this) — the signaling layer is the CHAT SDK
Meet-style (session-id "join a room") uses ONLY the Calls SDK (`generateToken` → `joinSession`). But
**one-on-one ringing** (call a specific user, they get an incoming-call prompt, accept/reject) combines the
**Chat SDK** (`@cometchat/chat-sdk-javascript`) for signaling + the Calls SDK for media.

**The COMPLETE, CURRENT recipe is ONE page — fetch it directly:**
```
fetch_cometchat_doc_page("/calls/javascript/ringing")
```
That page (v5, JS) carries the WHOLE flow, both sides: `CometChat.initiateCall(call, timeout?)` →
`CometChat.addCallListener({ onIncomingCallReceived → show an incoming-call screen, onOutgoingCallAccepted, onOutgoingCallRejected, onIncomingCallCancelled })`
→ `CometChat.acceptCall(sessionId)` / `rejectCall(sessionId, status)` / cancel → `CometChatCalls.generateToken(sessionId)`
→ `CometChatCalls.joinSession(...)` → `leaveSession()` + `CometChat.endCall(sessionId)`. It even includes an
**incoming-call UI example** and an **outgoing-call UI example**.
> **Do NOT reach for `search_cometchat_docs("default calling")`** — search surfaces the STALE
> `/sdk/javascript/3.0/` chat-SDK pages, which end on the deprecated `startSession()` (not `joinSession`) and
> show no incoming-call UI. `/calls/javascript/ringing` is the canonical v5 source of truth; reconcile any
> Chat-SDK symbol against the Chat SDK catalog before emitting.

> **⚠️ Testing 1:1 ringing needs TWO live clients** — different users, in **isolated browser sessions**. CometChat
> stores the logged-in user in `localStorage`, which is SHARED across tabs of the same browser, so two tabs
> both become the same user and the callee never rings. Use two different browsers (or one normal + one
> incognito window), each logged in as a different user with the CallListener active. The caller always shows
> ringing locally; that proves nothing about the callee. This is a two-client protocol, not a bug.
