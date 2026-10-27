# docs-map — CometChat Calls SDK v5 (Android, headless): intent → the exact docs page to fetch

## Reaching docs — PREFER the CometChat docs MCP; fetch is the fallback
The canonical doc channel is the **first-party CometChat docs MCP** — tools `search_cometchat_docs`,
`fetch_cometchat_doc_page`, and `get_cometchat_implementation_bundle`. **If those tools are connected,
use them instead of a raw web fetch:**
- **Find the page** → `search_cometchat_docs(query)` — e.g. `search_cometchat_docs("calls android join session")`.
- **Read the page** → `fetch_cometchat_doc_page(path)` — pass the SAME `<path>` the tables below list; the MCP
  resolves the `.md` twin and returns raw Markdown (read the **Kotlin** tab). A full `https://…/<path>` URL also works.
- **A whole feature/recipe** → `get_cometchat_implementation_bundle(...)` is **NON-AUTHORITATIVE** — curated
  STATIC recipes that can lag the live docs. Treat any bundle as a hint only: RECONCILE it against the
  `fetch_cometchat_doc_page` result + the catalog; never emit bundle code verbatim.

**If the MCP tools are NOT connected:** add it (`claude mcp add --transport http cometchat-docs https://mcp.cometchat.com/mcp`, or reinstall/enable the plugin) and retry; only if it still will not connect, fall back to a plain fetch via `DOCS_BASE` (defined next).
Either way the `<path>` catalog in this file is the source of truth for WHICH page — MCP-vs-fetch is only HOW.

## DOCS_BASE — the fetch FALLBACK entry point (⚠️ SWAP HERE to change environments)
```
DOCS_BASE = https://www.cometchat.com/docs
```
> Production docs (`https://www.cometchat.com/docs`). **Fetch rule:** build a URL as `DOCS_BASE` + the path shown,
> then append `.md`. Never hardcode a host anywhere else; never decompile the AAR for signatures (the pack's
> catalog already did — `android-calls-v5.json` is the closed list).

## The convention — Calls v5 lives at the UNVERSIONED root `/calls/android/`
```
Fetch:  {DOCS_BASE}/calls/android/overview.md
```
> **⚠️ VERSION TRAP.** The **unversioned** `/calls/android/**` tree IS **v5** (matches the installed
> `calls-sdk-android:5.0.x`). `/calls/v4/android/**` is the OLD v4 SDK (`startSession` / `CallSettingsBuilder`) —
> never fetch it for a v5 build. The UI-Kit calling pages (`/ui-kit/android/calling-integration`, `call-buttons`,
> `incoming-call`…) belong to `cometchat-android-v6-calls`, not this skill.
> **⚠️ MISSING PAGES return the docs HOME page, not a 404**: `/calls/android/permissions` and
> `/calls/android/virtual-background` do NOT exist — a fetched page whose first heading is `# Home` is a miss.

## Scoped index (prefer over the global llms.txt)
```
{DOCS_BASE}/llms.txt
```
Use it to discover any page not listed below (search for `/calls/android/`).

## Path catalog — intent → page (all under `/calls/android/`)
| Intent | Path |
|---|---|
| SDK overview · architecture · call-flow · feature cards | `/calls/android/overview` — now correctly states minSdk **26** (`react-native-svg` transitive floor), matching the manifest merge (DOCS-BACKLOG C11 RESOLVED, AUDIT-229) |
| Install (Gradle repo + dependency) · manifest permissions · `init` · **SoLoader Step 4** | `/calls/android/setup` — now states minSdk 26 AND documents the SoLoader `OpenSourceMergedSoMapping` init (C10 RESOLVED); documents ONLY `init(context, CallAppSettings, l)`, the skills' `initFromSettings` default is the DOCS-GAP note below. ⚠️ Its `compileOptions` shows Java **8**; the skill uses JVM 11 (both compile). NO `<service>` (C12) and NO from-scratch Gradle heap line (`-Xmx4096m`, AUDIT-225) — those stay skill-owned |
| Login (uid + API key dev / auth token prod) · `getLoggedInUser` · `logout` · error codes | `/calls/android/authentication` |
| `generateToken` + `joinSession` (meet-style) · container setup · error codes | `/calls/android/join-session` — ⚠️ its `SessionSettingsBuilder().setType(...)` is `setSessionType(...)` in the AAR |
| **1:1 RINGING** — `initiateCall` · `CallListener` · accept/reject/cancel · join · **end call on BOTH SDKs** | `/calls/android/ringing` — ⚠️ FOREGROUND-only in auto socket mode (`/sdk/android/v5/connection-behaviour`: backgrounded ⇒ WebSocket dropped, no incoming/accept callbacks, no replay); background ringing = `/calls/android/voip-calling`; recipe + caller-side reconcile in `references/ringing.md` |
| `SessionSettingsBuilder` — every option (`setSessionType`, `setLayout`, `setAudioMode`, `hide*Button`, `hideControlPanel`, `setIdleTimeoutPeriod`, `enableAutoStartRecording`, `setInitialCameraFacing`, …) | `/calls/android/session-settings` |
| Listeners (`SessionStatus` / `ParticipantEvent` / `MediaEvents` / `ButtonClick` / `Layout`) — full callback lists | `/calls/android/events` — ⚠️ `MediaEventsListener` has NO `onScreenShareStarted/Stopped`; screen-share callbacks are on `ParticipantEventListener` |
| In-call actions on `CallSession` (mute/pause/switch camera/layout/audio mode/record/raise hand/pin/leave) | `/calls/android/actions` — ⚠️ `unMuteAudio`/`unPinParticipant` are `unmuteAudio`/`unpinParticipant`; `pinParticipant` takes `(uid, pid)` |
| Call layouts (TILE / SIDEBAR / SPOTLIGHT) + `LayoutListener` | `/calls/android/call-layouts` — `SessionSettingsBuilder.setLayout` at join works; ⚠️ `CallSession.setLayout()` mid-call was a NO-OP in 5.0.4 (no `onCallLayoutChanged`) |
| Audio modes (SPEAKER / EARPIECE / BLUETOOTH / HEADPHONES) | `/calls/android/audio-modes` |
| Recording (start/stop, auto-start, indicators, recordings on `CallLog`) | `/calls/android/recording` — ⚠️ `startRecording()` from code gave no callback and no error in 5.0.4; recording is plan-gated ("must be enabled for your app") with NO error signal on refusal |
| **Transcription & closed captions** (auto-start, manual `startTranscription`/`stopTranscription`, `hideTranscriptionButton`/`hideClosedCaptionButton`/`setCaptionLanguage`, retrieve via `TranscriptRequest`) | `/calls/android/transcription` — **v5.0.4+**; PLAN-GATED ("must be enabled for your app"). `TranscriptRequest.TranscriptRequestBuilder().setSessionId(REQUIRED).setLimit(n).build()` → `fetchNext`/`fetchPrevious` → `List<Transcript>`; `Transcript.transcriptUrl` is a pointer to a downloadable JSON (download it yourself). A session with no transcript delivers an **empty list, not an error** (verified live, AUDIT-228) |
| Call logs (`CallLogRequest.CallLogRequestBuilder` + filters + pagination + recordings) | `/calls/android/call-logs` |
| Participant management (mute / pause video / pin / `Participant` fields) | `/calls/android/participant-management` |
| Screen sharing — **receive-only on Android** (web initiates) | `/calls/android/screen-sharing` |
| Raise hand | `/calls/android/raise-hand` — ⚠️ `CallSession.raiseHand()`/`lowerHand()` from code were a NO-OP in 5.0.4 (no `onParticipantHandRaised`, no error) — the surface's own button works (SKILL.md pitfalls) |
| Idle timeout (`setIdleTimeoutPeriod`, `onSessionTimedOut`) | `/calls/android/idle-timeout` |
| Share invite (`hideShareInviteButton(false)` + `onShareInviteButtonClicked` → share sheet; deep links) | `/calls/android/share-invite` |
| Picture-in-picture (Activity PiP + `enablePictureInPictureLayout`) | `/calls/android/picture-in-picture` |
| Background handling (`CometChatOngoingCallService.launch/abort`, `OngoingNotification`) | `/calls/android/background-handling` — the AAR declares no `<service>`, so without YOUR `<service android:name="com.cometchat.calls.services.CometChatOngoingCallService" android:exported="false" android:foregroundServiceType="camera|microphone|mediaPlayback"/>` `launch()` fails silently (SKILL.md Prerequisites). ⚠️ The docs manifest block now ships this exact `<service>` (corrected upstream, verified 2026-09-09) · its "Complete Example" uses a `RelativeLayout` container matching the real `joinSession(sessionId, SessionSettings, RelativeLayout, l)` signature |
| Custom control panel (`hideControlPanel(true)` + your buttons → `CallSession` actions) — **explicit request only** | `/calls/android/custom-control-panel` |
| VoIP push / receiving calls when the app is killed | `/calls/android/voip-calling` — pair with `cometchat-android-v6-push` posture: docs-first, delivery is a manual device check |

## DOCS-GAP — `initFromSettings` is NOT on the live docs (bake it here)
> **Referenced by `SKILL.md` (Init & login ordering).** `/calls/android/setup` documents ONLY
> `CometChatCalls.init(context, CallAppSettings, listener)` — it does **not** document
> `CometChatCalls.initFromSettings(context, CallbackListener<String>)`, even though the method is real and shipped
> (`javap` of the installed 5.0.4 AAR: `public static void initFromSettings(Context, CallbackListener<String>)`).
> It reads **`app/src/main/assets/cometchat-settings.json`** — the SAME gitignored file `CometChat.initFromSettings` /
> `CometChatUIKit.initFromSettings` read, so one asset serves chat AND calls:
> ```json
> {
>   "appId": "APP_ID",
>   "region": "us",
>   "credentials": { "authKey": "AUTH_KEY" },
>   "callsSDK": { "host": null, "adminHost": null, "clientHost": null, "callsHost": null },
>   "chatSDK": {},
>   "uiKit": {}
> }
> ```
> `appId` + `region` are REQUIRED (`ERROR_SETTINGS_FILE_MISSING_APPID` / `…_MISSING_REGION`); a missing asset is
> `ERROR_SETTINGS_FILE_NOT_FOUND`; the `callsSDK` block is optional host overrides (on-prem). The skills
> **DEFAULT to `initFromSettings`** — the **ai-agent-only telemetry init** (persists `integrationSource="ai-agent"`),
> **INTENTIONALLY undocumented** (`@nodoc`, same posture as `CometChatUIKit.initFromSettings` — DOCS-BACKLOG F4 / C1),
> which is WHY the shape is baked here. The publicly-documented `init(...)` is the FALLBACK only. Do NOT tell a
> user to "fetch the shape from `/calls/android/setup`": that page does not carry it. `authKey` for the dev
> `login(uid, authKey, l)` is read back out of `credentials.authKey` of this same asset (never a second copy).

## 1:1 RINGING (meet-style needs none of this) — the signaling layer is the CHAT SDK
Meet-style (session-id "join a room") uses ONLY the Calls SDK (`generateToken` → `joinSession`). But
**one-on-one ringing** (call a specific user, they get an incoming prompt, accept/reject) combines the
**Chat SDK** (`com.cometchat:chat-sdk-android:5.0.5`, `com.cometchat.chat.*`) for signaling + the Calls SDK for media.

**The COMPLETE, CURRENT recipe is ONE page — fetch it directly:**
```
fetch_cometchat_doc_page("/calls/android/ringing")
```
That page (v5, Kotlin) carries the WHOLE flow, both sides: `CometChat.initiateCall(Call(uid, RECEIVER_TYPE_USER,
CALL_TYPE_VIDEO), l)` (+ `(call, timeoutSec, l)`) → `CometChat.addCallListener(ID, object : CometChat.CallListener()
{ onIncomingCallReceived / onOutgoingCallAccepted / onOutgoingCallRejected / onIncomingCallCancelled /
onCallEndedMessageReceived })` → `CometChat.acceptCall(sessionId, l)` / `rejectCall(sessionId, CALL_STATUS_REJECTED |
CALL_STATUS_CANCELLED, l)` → `CometChatCalls.joinSession(call.sessionId, …)` on BOTH sides → hang-up =
`CallSession.getInstance().leaveSession()` **and** `CometChat.endCall(sessionId, l)` (the peer's
`onCallEndedMessageReceived` then leaves too; without `endCall` the log is incomplete).
> **Chat SDK init + login come first** — `CometChat.initFromSettings(context, l)` → `CometChat.login(uid, authKey, l)`
> (the `cometchat-android-v5-sdk` recipe; same settings asset). `Call` is **`com.cometchat.chat.core.Call`**
> (NOT `chat.models`). `CometChatException` exists in BOTH SDKs (`com.cometchat.chat.exceptions` /
> `com.cometchat.calls.exceptions`) — alias one when a file imports both.
> **Do NOT reach for `search_cometchat_docs("default calling")`** — search surfaces the STALE `/sdk/android/3.0/`
> chat-SDK pages (`startCall` / `CallSettingsBuilder`, the v4 media path). `/calls/android/ringing` is the
> canonical v5 source; reconcile any Chat-SDK symbol against `sdk-android-v5.json` before emitting.

> **⚠️ Testing 1:1 ringing needs TWO live clients** — two devices/emulators, two different users, each logged in
> with the global `CallListener` registered **and the app in the FOREGROUND** (auto socket mode drops the WebSocket in background). The caller always shows ringing locally; that proves nothing about
> the callee. This is a two-client protocol, not a bug.
