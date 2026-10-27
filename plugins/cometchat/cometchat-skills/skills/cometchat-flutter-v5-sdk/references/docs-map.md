# docs-map — Flutter Calls SDK v5 (`/calls/flutter/**`)

**Doc channel = the CometChat Docs MCP.** Use `search_cometchat_docs` / `fetch_cometchat_doc_page` /
`get_cometchat_implementation_bundle` when they are connected — they are the intended path and they
serve production docs for you.

**If the MCP tools are NOT connected:** add it (`claude mcp add --transport http cometchat-docs https://mcp.cometchat.com/mcp`, or reinstall/enable the plugin) and retry; only if it still will not connect, fall back to a plain fetch via `DOCS_BASE` (below).
Either way the `<path>` catalog in this file is the source of truth for WHICH page — MCP-vs-fetch is only HOW.

## DOCS_BASE — the fetch FALLBACK entry point (⚠️ SWAP HERE to change environments)
```
DOCS_BASE = https://www.cometchat.com/docs
```
> Production docs (`https://www.cometchat.com/docs`). **Fetch rule:** build a URL as `DOCS_BASE` + the path shown,
> then append `.md`. Never hardcode a host anywhere else; never read the installed Dart package at authoring
> time for SIGNATURES (the catalog is for EXISTENCE, the docs are for signatures).

## The convention — Calls v5 lives at the UNVERSIONED root `/calls/flutter/`
`DOCS_BASE` + `<path>` + `.md` → raw Markdown (verbatim code + parameter tables).
```
Fetch:  {DOCS_BASE}/calls/flutter/overview.md
```
> **⚠️ VERSION TRAP.** The **unversioned** `/calls/flutter/**` tree IS **v5**. Legacy
> `/sdk/flutter/<n>.0/*calling*` pages are the OLD chat-SDK calling surface — never fetch them for a v5
> build. **Do NOT `search("default calling")`** — search surfaces that stale tree.
> The **UI Kit** calling page (`/ui-kit/flutter/v5/calling-integration`) is a DIFFERENT product; it is
> what this skill exists to be the alternative to.

## Page catalog (25 pages)
| Path | Use it for |
|---|---|
| `/calls/flutter/overview` | the init→login→generateCallToken→joinSession sequence and the component model. **⚠️ its Android/iOS floors are BOTH too low — real: minSdk 26, iOS 13.0 (15.1 from 5.0.7)** |
| `/calls/flutter/setup` | install (the live page now pins `cometchat_calls_sdk: ^5.0.7`; older cached copies said `^5.0.3` — both resolve 5.0.7), Android manifest permissions, iOS `Info.plist`, `CallAppSettingBuilder`, `isInitialized`. **⚠️ its `region` table still says only `us`/`eu` — `in` is also live** |
| `/calls/flutter/authentication` | **`login` / `loginWithAuthToken` / `logout` / `getLoggedInUser`** — the only page with these, and the error-code table |
| `/calls/flutter/join-session` | **`generateCallToken` / `joinSession`** and the `Widget?` return. THE page for the Flutter fork |
| `/calls/flutter/session-settings` | `SessionSettingsBuilder` — every setter and the whole `hide*Button` list |
| `/calls/flutter/events` | all five listener types + every callback name and parameter. **⚠️ the page CONSTRUCTS all five; they are `abstract class`es and cannot be instantiated — take the callback NAMES from here and the shape from SKILL.md** |
| `/calls/flutter/actions` | **every in-call `CallSession.getInstance()` action** — mute/pin/layout/audio-mode/raise-hand/PiP, the toggle+alias pairs, the settings panels, the state getters, and the `Participant` field table |
| `/calls/flutter/ringing` | **1:1 RINGING — the WHOLE flow, both sides.** Fetch this DIRECTLY (see below) |
| `/calls/flutter/call-logs` | `CallLog` fields + pagination. **⚠️ its builder shape is wrong three ways — see SKILL.md's corrections; the real form is `(CallLogRequestBuilder()..limit = 30).build()`** |
| `/calls/flutter/call-layouts` | `LayoutType` values (`.tile` / `.spotlight` / `.sidebar`) and layout switching |
| `/calls/flutter/audio-modes` | `AudioMode` values and routing |
| `/calls/flutter/recording` | recording start/stop, `enableAutoStartRecording`, `Recordings`, prerequisites. **⚠️ nothing here covers TRANSCRIPTION, which shipped in 5.0.7 — there is no page at all; use `references/transcription.md`** |
| `/calls/flutter/participant-management` | roster + moderation (mute / pause video / pin) |
| `/calls/flutter/custom-participant-list` | building your own roster UI |
| `/calls/flutter/custom-control-panel` | replacing the built-in controls — **hide first, then drive** |
| `/calls/flutter/screen-sharing` | the RECEIVE side — the share EVENTS (`onParticipantStartedScreenShare`) and (phantom) `participant.isPresenting`. **⚠️ the page says "receive-only," but 5.0.7 ALSO ships local-share CONTROL methods on `CallSession` (`startScreenShare`/`stopScreenShare`/`toggleScreenShare`/`isScreenSharing`) that the page does NOT document** — see SKILL.md "Screen share" pitfall |
| `/calls/flutter/raise-hand` | raise / lower / toggle hand, `isHandRaised`, remote `raisedHandTimestamp` |
| `/calls/flutter/picture-in-picture` | **TWO kinds, pick one** — in-app PiP layout vs Android system PiP (`enterPipMode`) and its manifest flag |
| `/calls/flutter/idle-timeout` | `setIdleTimeoutPeriod` (default **300**, `0` disables) and `onSessionTimedOut` |
| `/calls/flutter/background-handling` | **`CometChatOngoingCallService`** — Flutter-only Android foreground service, and its manifest permissions |
| `/calls/flutter/in-call-chat` | the chat BUTTON (`onChatButtonClicked`, `setChatButtonUnreadCount`) — the chat itself is the UI Kit |
| `/calls/flutter/share-invite` | `onShareInviteButtonClicked` + the app-side link/deep-link work |
| `/calls/flutter/voip-calling` | **THE page for `call-voip-push`** — the Android-FCM and iOS-APNs/CallKit paths, separately |
| `/calls/flutter/migration-guide-v5` | v4→v5 mapping. **⚠️ its "v4" tab shows the OLD API on purpose — do not read those fences as current** |
| `/calls/flutter/troubleshooting` | common failures |

| Path | Use it for |
|---|---|
| `/notifications/flutter-push-notifications-android` | FCM wiring for the Android half of call notifications |
| `/notifications/flutter-push-notifications-ios` | APNs wiring for the iOS half |
| `/notifications/push-overview` | dashboard providers — you need one configured before any of it rings |

## 1:1 RINGING — fetch the page DIRECTLY
`/calls/flutter/ringing` carries the entire two-sided flow and it is the only page with the **Chat SDK**
signalling signatures. Those symbols (`CometChat.initiateCall` / `addCallListener` / `CallListener` /
`acceptCall` / `rejectCall` / `endCall` / `removeCallListener`, and the `Call` /
`CometChatCallType` / `CometChatReceiverType` / `CometChatCallStatus` types) belong to
**`cometchat_sdk` v5** and are deliberately ABSENT from `flutter-calls-v5.json`, which catalogs the
Calls SDK only. Validate them against the chat SDK's own catalog, not this one.

Three things the page's shape hides:
- **`User` is declared by BOTH barrels.** `cometchat_calls_sdk` and `cometchat_sdk` each export a `User`, so a file importing both — which ringing forces — fails with `ambiguous_import` until one side hides it: `import 'package:cometchat_calls_sdk/cometchat_calls_sdk.dart' hide User;`.
- **`CallListener` is a `mixin`, NOT a constructible class.** The page writes `CallListener(onIncomingCallReceived: …)`; a mixin has no constructor, so that does not compile. Use `class X with CallListener { @override … }` and pass an instance. Every method defaults to a no-op, so override only what you need. (Found building this skill's harness — **not** in docs#492.)
- **There is no `cancelCall`.** Cancelling your own outgoing call is `rejectCall(sessionId, CometChatCallStatus.cancelled)`; rejecting someone else's is the same method with `.rejected`.

**Verifying ringing needs TWO live clients.** One device can prove the wiring compiles and that
`initiateCall` resolves; it can never prove the callee's `onIncomingCallReceived` fired. The harness
runs two devices, one process per role, and only reports success when BOTH report it on the SAME
session id — verified by the pack's dev ringing-smoke harness (internal QA, not shipped).

## STOPGAP — `CometChatCalls.initFromSettings` (intentionally undocumented, ai-agent only)
<!-- STOPGAP: source-derived from cometchat_calls_sdk 5.0.7 and its upstream in
     calls-core/calls-sdk-flutter, NOT from a docs page. `initFromSettings` is marked `@nodoc`.
     Tracked as DOCS-BACKLOG F4, closed WONTFIX by the UI Kit
     owner on 2026-08-21: it is to STAY hidden. This stopgap is therefore permanent by decision,
     not pending a docs fix. Everything else in this file comes from the pages above. -->
```dart
CometChatCalls.initFromSettings(
  onSuccess: (String message) { /* ... */ },
  onError: (CometChatCallsException e) { /* ... */ },
);
```
- **No settings argument.** It reads `cometchat-settings.json` via **`rootBundle.loadString`**.
- The file lives at the **project root** and MUST be registered as a Flutter asset:
  ```yaml
  flutter:
    assets:
      - cometchat-settings.json
  ```
- Shape: root `appId` (required) + `region` (required); optional `callsSDK` → `adminHost` / `clientHost` / `callsHost`. A host value of the literal string `"null"` is ignored, not applied.
- Missing file / bad JSON / missing `appId` / missing `region` each fire **`onError` with a distinct code** — none of them throws, so a silent no-call is the symptom.
- It sets `integrationSource = "ai-agent"`. A plain `CometChatCalls.init` afterwards overwrites that with `"manual"`.
- **NATIVE FORK:** iOS reads the same filename from `Bundle.main` (Copy Bundle Resources); web passes settings inline with no file.

## Callback shapes (VERIFIED against 5.0.7 — the SDK is INCONSISTENT, do not pattern-match)
| API | `onSuccess` receives | Returns |
|---|---|---|
| `init(callAppSettings, …)` | `String` | `void` (not a Future) |
| `initFromSettings(…)` | `String` | `Future<void>` |
| `login(uid:, authKey:, …)` | **`User?`** (nullable) | `void` |
| `loginWithAuthToken(authToken:, …)` | **`User?`** (nullable) | `void` |
| `logout(…)` | `String` | `void` |
| `generateCallToken(sessionId, …)` | `CallToken` | `void` |
| `generateToken(sessionId, userAuthToken, …)` | `GenerateToken` — **⚠️ `@Deprecated`, two POSITIONAL args, and a DIFFERENT type from `generateCallToken`** | `void` |
| `joinSession(sessionId:/callToken:, sessionSettings:, …)` | **`Widget?`** | `Future<void>` |
| `getLoggedInUser()` | — | **`Future<User?>`** (await it; no callbacks) |

Every `onError` receives `CometChatCallsException`. `joinSession` takes **exactly one** of
`sessionId` or `callToken` — passing neither (or both) fails through `onError`, not by throwing.

## `SessionSettingsBuilder` — every setter, and the five DEFAULT-HIDDEN buttons (5.0.7)

> Presented as a CLOSED list, so it has to be complete: `startAudioMuted` and `startVideoPaused`
> were missing from it until an isolation test caught them. A closed list that isn't makes a real
> API look like a phantom — worse than no list. Re-probe before trusting it.
Setters return the builder, so **either** Dart cascades (`..setType(...)`, what the docs show) **or**
chaining works. Build with `.build()`.

`setTitle` · `setDisplayName` · `setType(SessionType)` · `setLayout(LayoutType)` ·
`setAudioMode(AudioMode)` · `setInitialCameraFacing(CameraFacing)` · `setIdleTimeoutPeriod(int)` ·
`setCaptionLanguage(String)` · `startAudioMuted(bool)` · `startVideoPaused(bool)` ·
`enableLowBandwidthMode(bool)` · `enableAutoStartRecording(bool)` · `enableAutoStartTranscription(bool)`

`hideControlPanel` · `hideHeaderPanel` · `hideSessionTimer` · `hideLeaveSessionButton` ·
`hideToggleAudioButton` · `hideToggleVideoButton` · `hideSwitchCameraButton` · `hideAudioModeButton` ·
`hideChangeLayoutButton` · `hideParticipantListButton` · `hideRaiseHandButton` ·
`hideScreenSharingButton` · `hideRecordingButton` · `hideShareInviteButton` · `hideChatButton` ·
`hideTranscriptionButton` · `hideClosedCaptionButton`

> **⚠️ FIVE buttons are HIDDEN BY DEFAULT** — `hideRecordingButton`, `hideShareInviteButton`,
> `hideChatButton` and, new in 5.0.7, `hideTranscriptionButton` and `hideClosedCaptionButton` all
> default to **`true`**. Wiring the matching click callback without passing `false` produces a
> listener that can never fire, and it looks like the events are broken. `setIdleTimeoutPeriod`
> defaults to **300**; every other `hide*` defaults to `false`.

## Listener registration — the names do NOT match the types
| Type | Add | Remove |
|---|---|---|
| `SessionStatusListeners` | `addSessionStatusListener(l)` | `removeSessionStatusListener(l)` |
| `ParticipantEventListeners` | `addParticipantEventListener(l)` | `removeParticipantEventListener(l)` |
| `MediaEventListeners` | `addMediaEvent`**`s`**`Listener(l)` | `removeMediaEvent`**`s`**`Listener(l)` |
| `ButtonClickListeners` | `addButtonClickListener(l)` | `removeButtonClickListener(l)` |
| `LayoutListeners` | `layoutListener = l` | `layoutListener = null` |

All five are on `CallSession.getInstance()`, which is **`null` when no session is active** — use `?.`.
`remove*` matches **by instance**, so the listener must be a retained field.

> **⚠️ `LayoutListeners` is the odd one out.** `CallSession` exposes `set layoutListener(LayoutListeners?)`
> and its getter — there is **no `addLayoutListener` / `removeLayoutListener`**, so only ONE layout
> listener exists at a time and it is cleared by assigning `null`. The events page shows the add/remove
> pair; those methods do not exist.

> **⚠️ All five types are `abstract class`es.** `SessionStatusListeners(onSessionJoined: …)`, the
> shape every page uses, does not compile — `flutter analyze` reports `instantiate_abstract_class`.
> Write `class X extends SessionStatusListeners { @override … }` and pass an instance. Every method
> already has a no-op body, so `extends` lets you override just what you need; `implements` obliges
> you to write them all.

## ⚠️ Doc corrections — VERIFIED against cometchat_calls_sdk 5.0.7
The `Doc corrections` table in `SKILL.md` is authoritative; it lists 13 classes of symbol on the live
pages that do not compile, including **the entire documented token flow** (`generateToken` is
deprecated, takes positional args, and yields a different type than the pages assign it — while
`generateCallToken`, the current API, appeared on no page at all).

Fixed in docs PR **cometchat/docs#492** (56 → 3 analyzer errors across 25 pages). Until it merges the
live pages still carry them. **12 fences on those pages parse in no shape and were never
machine-checked**, so 3 is a floor, not a total — prefer the skill's names over the page's on any
disagreement, and re-check this section when #492 lands.

## Upstream — `calls-core/calls-sdk-flutter` (the SDK monorepo)

The Flutter Calls SDK is developed in the **`calls-core` monorepo**, alongside `ios-sdk`,
`calls-sdk-javascript`, `react-native-sdk` and the shared `calls-sdk-core`. That is where the
`@nodoc` `initFromSettings` path above was read from, and it is the right place to check when a
docs page and the installed package disagree.

**As of 5.0.7 the published package and the monorepo dev branch (`dev-v5`, == `release-next`;
`master-v5` merges it) are byte-identical under `lib/`.** So there is no published-vs-upstream gap
to carry right now.

> **⚠️ Never infer that from a version string.** Before 5.0.7 shipped, the published package and
> the monorepo BOTH read `version: 5.0.6` with different contents. Re-diff the trees; do not
> compare versions.

### 5.0.6 → 5.0.7 (published 2026-09-02)

**Transcription arrived as a complete feature** — and `/calls/flutter` has **no page for it**.
The skill is the only source; see `references/transcription.md` (a labelled STOPGAP) and
DOCS-BACKLOG **D3**. Three new barrel-exported types entered the catalog: `Transcript`,
`TranscriptRequest`, `TranscriptRequestBuilder`.

**iOS floor raised 13.0 → 15.1**, native `CometChatCallsSDK` pin 5.0.0 → 5.0.4. This is breaking
for consumers on iOS 13/14 and can bite on a routine `pub upgrade`, because `^5.0.3` resolves to
5.0.7. Android stayed at `minSdkVersion 26` — the docs' "24 / Android 7.0" was never right for any
5.0.x.

**Six dead enum files were deleted** (`audio_modes`, `avatar_type`, `call_type`, `mode`,
`video_stream_modes`, `video_stream_positions`). All six were already in the catalog's
`internalOnlyExcluded` — never reachable from the barrel — so their removal changed nothing here.
`CallType` is the same phantom skills#183 filed on iOS.
