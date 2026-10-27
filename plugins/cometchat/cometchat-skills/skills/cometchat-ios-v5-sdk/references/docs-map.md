# docs-map — iOS Calls SDK v5 (`/calls/ios/**`)

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
> then append `.md`. Never hardcode a host anywhere else; never read the `.swiftinterface` at authoring time
> for SIGNATURES (the catalog is for EXISTENCE, the docs are for signatures).

## The convention — Calls v5 lives at the UNVERSIONED root `/calls/ios/`
`DOCS_BASE` + `<path>` + `.md` → raw Markdown (verbatim code + parameter tables).
```
Fetch:  {DOCS_BASE}/calls/ios/overview.md
```
> **⚠️ VERSION TRAP.** The **unversioned** `/calls/ios/**` tree IS **v5**. Legacy `/sdk/ios/<n>.0/calling-*`
> pages are the OLD chat-SDK calling surface (deprecated `startSession`, no incoming-call UI) — never fetch
> them for a v5 build. **Do NOT `search("default calling")`** — search surfaces that stale tree.

## Page catalog
| Path | Use it for |
|---|---|
| `/calls/ios/overview` | the init→login→generateToken→joinSession sequence, CallSession model |
| `/calls/ios/setup` | install (SPM + CocoaPods), Info.plist permissions, background modes, `CallAppSettingsBuilder` |
| `/calls/ios/ringing` | **1:1 RINGING — the WHOLE flow, both sides.** Fetch this DIRECTLY (see below) |
| `/calls/ios/session-settings` | `SessionSettingsBuilder` — every setter, the `hide*Button` list, layout/audio enums |
| `/calls/ios/events` | listener protocols + every event name and callback signature |
| `/calls/ios/call-logs` | `CallLogsBuilder` / `CallLogsRequest` / `CallLog` fields, pagination |
| `/calls/ios/recording` | recording start/stop, `enableAutoStartRecording`, prerequisites (`hideRecordingButton` defaults to **true** — the built-in control is HIDDEN until you opt in). **Recording AND transcription are DASHBOARD-GATED and the actions are fire-and-forget:** `startRecording()`/`startTranscription()` return `Void` and surface **no error** when the feature is off for the app — nothing happens, silently. Gate your UI on `MediaEventsListener.onRecordingStarted`/`onRecordingStopped`, never on the call returning, and tell the user to enable recording on the app first |
| `/calls/ios/authentication` | **`login` / `logout` / `getLoggedInUser`** — the only page with these |
| `/calls/ios/join-session` | **`generateToken` / `joinSession`** signatures + container setup |
| `/calls/ios/actions` | **every in-call `CallSession.shared` action** — mute/pin/layout/audio-mode/raise-hand. The only page with these signatures |
| `/calls/ios/call-layouts` | `LayoutType` values (`.tile` / `.spotlight` / `.sidebar`) and layout switching |
| `/calls/ios/audio-modes` | `AudioMode` values and routing |
| `/calls/ios/participant-management` | roster + moderation |
| `/calls/ios/custom-participant-list` | building your own roster UI |
| `/calls/ios/screen-sharing` | **receive-only on iOS** — the share EVENTS; local capture needs a Broadcast Upload Extension |
| `/calls/ios/raise-hand` | raise/lower hand (a built-in button exists by default) |
| `/calls/ios/transcription` | transcription + `TranscriptsRequest`/`TranscriptsBuilder`/`Transcript`. **`hideTranscriptionButton` and `hideClosedCaptionButton` default to hidden** |
| `/calls/ios/picture-in-picture` | PiP — **TWO kinds, pick one.** In-app (a draggable tile over your own app) uses **`PiPViewCoordinator`, which SHIPS in the Calls SDK**; System PiP (floating over OTHER apps) IS in the 5.0.4 binary, behind the undocumented `enableIOSPictureInPicture(_:)` — see below. `enablePictureInPictureLayout()` only reshapes the call UI — alone it does nothing visible |
| `/calls/ios/idle-timeout` | `setIdleTimeoutPeriod` |
| `/calls/ios/custom-control-panel` | replacing the built-in controls |
| `/calls/ios/in-call-chat` · `/calls/ios/share-invite` · `/calls/ios/background-handling` | the remaining in-call surfaces |
| `/calls/ios/voip-calling` | the HAND-WIRED `PKPushRegistry`/`CXProvider` recipe — **do NOT follow it**; the push SDK owns both delegates. The real VoIP page is `/notifications/ios-push-notifications-sdk`. `/calls/ios/troubleshooting`'s "CallKit UI not showing → implement CXProvider" row points here too and is equally wrong for this skill |
| `/calls/ios/migration-guide-v5` | v4→v5 mapping; also the only place `switchCamera()` is shown |
| `/calls/ios/troubleshooting` | common failures |

| `/notifications/ios-push-notifications-sdk` | **VoIP call notifications — THE page for `call-voip-push`.** `CometChatPushNotifications` 1.0.0: install, `initialize(config:)`, `registerDeviceToken`, the delegate, `notifyCallsSDKReady()`, the Notification Service Extension |
| `/notifications/push-overview` | dashboard providers (you need an **APNs VoIP** provider) |
| *(verified on a physical iPhone)* | **Testing VoIP: suspend the app ≥ 30s before ringing it, or you are testing the socket, not the push.** A freshly-backgrounded app keeps its WebSocket; the push SDK dedupes a call "delivered via WebSocket before the VoIP push", so CallKit still rings and APNs delivery goes unproven. Measured: at 2s in background the socket won; at 51s the push woke the suspended app and the socket's copy arrived 7s *after* resume. Also: on the **lock screen** CallKit shows slide-to-answer, not an Accept button |
| `/notifications/ios-apns-push-notifications` | the HAND-WIRED alternative. Do not follow it unless the user explicitly wants to own `PKPushRegistry`/`CXProvider` themselves |

> The three rows above live OUTSIDE `/calls/ios/**`. VoIP is a different package
> (`CometChatPushNotifications`), not part of `CometChatCallsSDK`.

**All 26 pages of the `/calls/ios` tree are listed above.** Earlier revisions listed only 7, which dead-ended every
lookup for in-call actions, `login` and `joinSession`. `llms.txt` does NOT index `/calls/ios/**` — use
`sitemap.xml` (or this table) for discovery, never the index.

## 1:1 RINGING — fetch the page DIRECTLY
**one-on-one ringing** (call a specific user, they get an incoming prompt, accept/reject) combines the
**Chat SDK** (`CometChatSDK` v4) for signaling + the Calls SDK for media.

**The COMPLETE, CURRENT recipe is ONE page — fetch it directly:**
```
fetch_cometchat_doc_page("/calls/ios/ringing")
```
That page carries the whole flow, both sides: `CometChat.initiateCall(call:timeout:onSuccess:onError:)` →
`CometChat.addCallListener(<id>, delegate)` + `CometChatCallDelegate` (`onIncomingCallReceived`,
`onOutgoingCallAccepted`, `onOutgoingCallRejected`, `onIncomingCallCancelled`, `onCallEndedMessageReceived`)
→ `CometChat.acceptCall(sessionID:)` / `rejectCall(sessionID:status:)` → `joinSession(...)` →
`CallSession.shared.leaveSession()` **and** `CometChat.endCall(sessionID:)` → `CometChat.removeCallListener(<id>)`.

> **⚠️ TESTING RINGING NEEDS TWO LIVE CLIENTS.** One app instance cannot ring itself: you need two logged-in
> users on two devices/simulators. A single-simulator run can verify meet-style end-to-end but can only verify
> that ringing is WIRED, not that it rings. Say which you did.

### BAKED — the Chat SDK's OWN init + login (NO page in this map covers it)
The ringing page starts at `initiateCall` and assumes the Chat SDK is already up. It is a SECOND SDK
with its OWN lifecycle, stated nowhere in `/calls/ios/**` — so bake it:

```swift
// Chat SDK — BEFORE addCallListener / initiateCall. Reads the SAME bundled cometchat-settings.json
// as the Calls SDK (root appId + region), so one file serves both.
CometChat.initFromSettings(onSuccess: { (ok: Bool) in }, onError: { (e: CometChatException) in })
CometChat.login(UID: uid, authKey: key, onSuccess: { user in }, onError: { e in })
```
`initFromSettings` → `onSuccess (Bool)`, `onError` **NON-optional** `CometChatException` — both differ
from the Calls SDK's shapes (see the callback table below). The classic
`CometChat(appId:appSettings:onSuccess:onError:)` builder also exists and is the fallback when no
settings file is bundled. Full ordering for ringing: **Chat init → Chat login → Calls init → Calls
login → addCallListener → initiateCall.**

**This is now live-certified, not just wired.** Two app instances run CONCURRENTLY on two DIFFERENT
simulators, one per role, and must land on the SAME session id — the actual proof of one overlapping
call, not two independent successes.

## BAKED — `CometChatCalls.initFromSettings` (intentionally undocumented, ai-agent only)
Not on any doc page by design (`@nodoc`, ai-agent-only — same posture as the chat SDK's `initFromSettings`).
Signature takes **no settings argument**:
`CometChatCalls.initFromSettings(onSuccess: (String) -> Void, onError: (CometChatCallException?) -> Void) -> CometChatCalls?`

It reads **`cometchat-settings.json` from `Bundle.main`** — the file must be added to the target's
**Copy Bundle Resources**. Schema (root fields shared with the chat SDK; only the `callsSDK` section is read here):
```json
{
  "appId": "APP_ID",
  "region": "us",
  "callsSDK": { "host": "", "adminHost": "", "clientHost": "", "callsHost": "" }
}
```
`appId` and `region` are REQUIRED (`SETTINGS_MISSING_APP_ID` / `SETTINGS_MISSING_REGION`); the whole `callsSDK`
block is optional. Missing file → `SETTINGS_FILE_NOT_FOUND`; bad JSON → `SETTINGS_FILE_INVALID`.
It persists `integrationSource="ai-agent"` BEFORE delegating to the builder init — which is why a direct
`CometChatCalls(callsAppSettings:)` call afterwards re-attributes the app to `"manual"`.

## Picture-in-Picture: `PiPViewCoordinator` is the in-app mechanism
`enablePictureInPictureLayout()` ONLY re-lays-out the call UI — it creates no window, so on its own
nothing visibly happens and an emit that stops there ships a call that vanishes off-screen.

- **In-app PiP** (draggable tile over your own app): **`PiPViewCoordinator` ships in the SDK.**
  `init(withView:)` on the SAME view given to `joinSession(container:)` →
  `configureAsStickyView(withParentView:)` (pass the parent — it otherwise falls back to the key
  window) → `show()` → `enterPictureInPicture()` alongside `enablePictureInPictureLayout()`.
  `resetBounds(bounds:)` on rotation. `initialPositionInSuperView` is one of four corners; tile size
  is fixed at 150px (`c` is deprecated).
- `PiPViewCoordinatorDelegate.exitPictureInPicture()` is a **notification that PiP already ended**
  (the coordinator restored the view before calling you) — not a request to end it. Do
  `disablePictureInPictureLayout()` there.
- **System PiP** (over OTHER apps): **the SDK DOES ship this — do not tell the user it is absent.**
  5.0.4 implements the whole AVKit path internally (`AVPictureInPictureController`,
  `AVPictureInPictureControllerContentSource`, `AVPictureInPictureVideoCallViewController`,
  `AVPictureInPictureControllerDelegate`; `AVKit` is in the framework's load commands), gated behind
  **`SessionSettingsBuilder.enableIOSPictureInPicture(_:)`** — a real setter in the interface that
  appears on **no** `/calls/ios/**` page. Turn it on in the builder (the SDK echoes
  `"enableIOSPictureInPicture": true` in its own settings dictionary) and add Background Modes →
  *Audio, AirPlay and Picture in Picture*. **NOT certified by this pack:** it needs a physical device
  with a live video stream — the Simulator has no camera feed and no window appears there. Offer it
  as an opt-in flag with that caveat; never claim the SDK lacks system PiP.
- **⚠️ The PiP container must be FRAME-managed, NOT Auto Layout-pinned.** `PiPViewCoordinator`
  positions the view by setting `.frame` and toggling `autoresizingMask` (it clears the mask in
  `enterPictureInPicture()`), so constraints pinning the container to its superview win at the next
  layout pass: the SDK hides its control bar and `onPictureInPictureLayoutEnabled` fires, but the
  call stays FULL-SCREEN — no tile, no controls, no way back. The join-session recipe's "pin the
  container with constraints" directly conflicts with the PiP recipe; for a PiP call let the
  coordinator own the frame.

## VoIP push: map the incoming `Call` to a `SessionType` (documented NOWHERE)
`presentCallScreen(for call: Call, sessionId:)` hands you a Chat-SDK `Call`, and `joinSession`
needs a `SessionType`. No page says how to bridge them, so an emit that hardcodes `.video`
opens a VOICE call with the camera on. `Call.callType` IS readable — a non-optional
`CometChat.CallType` (`.video` · `.audio` · `.audioVideo`):

```swift
let sessionType: SessionType = (call.callType == .audio) ? .voice : .video
```

(`.voice`, not `.audio` — `SessionType.audio` is deprecated. Two different enums with
overlapping case names: `CometChat.CallType` on the Chat SDK's `Call`, `SessionType` on the
Calls SDK's builder.)

## Call-log entity types (VERIFIED in the 5.0.4 interface — documented NOWHERE)
`CallLog.initiator` and `.receiver` are typed `CallEntity`, and no doc page lists a single member,
so "show who the call was with" looks impossible from the docs. It is not:

| Type | Members |
|---|---|
| `CallEntity` (base) | **`name: String`** — NON-optional, so `callLog.initiator.name` works directly, no downcast |
| `CallUser : CallEntity` | `uid: String` · `avatar: String?` |
| `CallGroup : CallEntity` | `guid: String` · `icon: String?` |
| `CallEntityType` | `.callUser` · `.callGroup` (+ `.value` for the raw string) |

Downcast (`as? CallUser` / `as? CallGroup`, keyed off `receiverType`) ONLY when you need the
id or avatar — never for the display name.

Nesting the flat catalog cannot show you: **`CallLogsRequest.CallLogsBuilder`** is nested
(`CallLogsRequest.CallLogsBuilder()`), exactly like `SessionSettingsBuilder.SessionSettings`.

## Listener semantics + threading (VERIFIED in the calls-core `CallSession.swift` source)
Neither fact is in any doc page, and both change what correct code looks like.

- **Listeners are held WEAKLY** — `CallSession` stores every listener set as
  `Set<WeakWrapper<T>>`. So there is NO retain cycle and `deinit` DOES fire: a `deinit`-based
  teardown is valid. The real hazard is the opposite one — **a listener object with no other
  strong owner is silently deallocated and stops receiving events.** If you register a standalone
  helper (not the view controller itself), the app must retain it.
- **Callbacks are NOT guaranteed on the main thread.** `CallSession` observes
  `NotificationCenter` with `addObserver(self, selector:)` and **no** `queue:`, and contains zero
  `DispatchQueue.main` hops — so callbacks run on whichever thread posted the event. `joinSession`
  mounts a `UIView` and listener callbacks usually drive UI, so **hop to main yourself** before
  touching UIKit. Every doc sample that chains straight from a callback into UI is a latent
  off-main crash.

## Listener callback SETS — copy from here, never by analogy (5.0.4)
Every listener protocol is `@objc` with `optional` members, so a callback name that is **not** in the
protocol still COMPILES — and then silently never fires. That is the `canceledCall` failure mode, and
it applies to all five Calls-SDK protocols, not just the Chat SDK's delegate. `/calls/ios/events` is
the page, but bake the one that gets guessed most:

- **`SessionStatusListener` — exactly six:** `onSessionJoined` · `onSessionLeft` · `onSessionTimedOut`
  · `onConnectionLost` · `onConnectionRestored` · `onConnectionClosed`.
  There is **NO `onSessionEnded`** and **NO `onError`** — both are plausible, both compile, both are
  dead. `onSessionTimedOut` is the idle-timeout end (`setIdleTimeoutPeriod`); `onSessionLeft` is the
  normal one. Verified live: a session left via the built-in leave button fires `onSessionLeft` only.

## ⚠️ Participant moderation is NOT buildable headless on iOS (VERIFIED LIVE, 5.0.4)
`CallSession.shared` exposes `muteParticipant(participantId:)`, `pauseParticipantVideo(participantId:)`
and `pinParticipant(participantId:type:)`, and `/calls/ios/participant-management` shows all three —
but every sample starts from a `participant` you already hold, or the literal `"PARTICIPANT_UID"`.
**Neither the docs nor the SDK gives you a way to obtain that uid.**

Measured on two simulators in ONE session, peer visibly rendered as a second tile, listener registered
on `CallSession.shared` before joining exactly as this skill instructs:
- `onParticipantJoined` and `onParticipantLeft` **never fired**;
- `onParticipantListChanged` fired on both the join and the leave transition with an **EMPTY**
  `[Participant]` array;
- `MediaEventsListener` and `LayoutListener` on the SAME object fired normally throughout
  (`onAudioModesChanged`, `onVideoPaused`/`Resumed`, PiP enabled/disabled) — so registration is fine.

`Participant` also has no state flags and there is no roster accessor, so there is **no** second route
to a uid. **Therefore: do NOT emit a custom moderation UI, a participant list, or any
`*Participant(participantId:)` call — you cannot supply the argument.** Say so plainly, and point the
user at the SDK's own participant-list panel (`hideParticipantListButton` defaults to `false`): the
built-in **more (⋮) → Participants** sheet renders the roster with a search field, per-row audio level,
a mic toggle and an overflow menu — verified live. **That panel proves the SDK HAS the roster
internally; only the listener surface is empty.** So moderation is reachable through the built-in UI
and only through it. Revisit if a later 5.x populates the event.

## `SessionSettingsBuilder.hide*Button` — the complete list (5.0.4 interface)
Pitfall #1 says to hide the built-ins before adding custom controls. These are the setters:
`hideAudioModeButton` · `hideChangeLayoutButton` · `hideChatButton` · `hideControlPanel` ·
`hideHeaderPanel` · `hideLeaveSessionButton` · `hideParticipantListButton` · `hideRaiseHandButton` ·
`hideRecordingButton` · `hideRecordingStatusIndicator` · `hideSessionTimer` ·
`hideShareInviteButton` · `hideStreamingButton` · `hideStreamingStatusIndicator` ·
`hideSwitchCameraButton` · `hideToggleAudioButton` · `hideToggleVideoButton`

The presence of `hideRaiseHandButton` is also the proof that **a raise-hand button is rendered by
default** — hiding it is opt-OUT, so "let people raise their hand" needs no button of your own.

## CRASH — declare `var window: UIWindow?` on the AppDelegate (verified live)
The Calls SDK embeds a React Native runtime whose `RCTDeviceInfo._interfaceOrientationDidChange`
reads `UIApplication.delegate.window`. Xcode's default template since iOS 13 is SCENE-based, so
`window` lives on the SceneDelegate and the AppDelegate has no such selector — the app aborts:

```
*** Terminating app due to uncaught exception 'NSInvalidArgumentException',
    reason: '-[YourApp.AppDelegate window]: unrecognized selector sent to instance …'
```

It fires on the first orientation/permission pass — in practice the instant the CAMERA permission is
granted, i.e. AFTER init, login and join have all succeeded, so it reads like a media bug rather than
a missing property. **Fix: declare `var window: UIWindow?` on the AppDelegate.** It never has to be
assigned; the selector merely has to exist. `RCTDeviceInfo` is in the shipped 5.0.4 binary.

## Callback signatures (VERIFIED in the 5.0.4 interface — the SDK is INCONSISTENT)
`?.` on a non-optional is a hard Swift compile error, so guessing here breaks the build. The doc
pages are CORRECT and differ from each other because the **SDK** differs. Copy per-API:

| API | `onSuccess` param | `onError` param |
|---|---|---|
| `initFromSettings` | `String` | **`CometChatCallException?`** |
| `login` | `CallsUser` | **`CometChatCallException`** (NOT optional) |
| `logout` | `String` | **`CometChatCallException`** (NOT optional) |
| `generateToken` | `String?` | **`CometChatCallException?`** |
| `joinSession` | `String` | **`CometChatCallException?`** |

Do NOT sidestep this with `String(describing: error)` or `{ _ in }` — that throws away the error
text the user needs. Use the exact shape for the API you are calling.

**⚠️ `joinSession`'s `onError` is NOT terminal.** On a normal, successful join it fires **1–2 times**
with `"CometChatCalls in not Initialised properly"` **before** `onSuccess` — even though
`initFromSettings` and `login` both already succeeded (the SDK carries on, POSTs `/v3.0/call_tokens`
and joins). Reproduced on every join, on two simulators, in 5.0.4. So **`onSuccess` is the only join
verdict**: log the error, never alert / pop the call screen / retry / tear down listeners from
`onError`. An emit that treats it as fatal — the natural reading, and what the doc sample's shape
invites — kills every call it makes.

Arity the types-only catalog cannot give you: **`isCallSessionActive()` is a METHOD returning
`Bool`**, not a property — it is the correct guard against a double `leaveSession()`.

## ⚠️ Doc corrections — VERIFIED against CometChatCallsSDK 5.0.4
These pages contain symbols that do not exist. Prefer the right-hand column; do not "fix" the skill to match
the page.
| Page | The page writes | Reality (interface + binary) |
|---|---|---|
| `events`, `session-settings`, `recording` | `AudioModeType` | **`AudioMode`** (`.speaker`/`.earpiece`/`.bluetooth`/`.headphones`) |
| `ringing` | `CometChat.CallStatus` | **`CometChat.callStatus`** (lowercase `c`) |
| `ringing`, `session-settings`, `join-session`, `idle-timeout`, `migration-guide-v5` | `.setType(.video)` — Swift AND the ObjC `setType:` | **`.setSessionType(.video)`** — `SessionSettingsBuilder` has no `setType` in either language |
| `setup` | SPM URL `…/cometchat-calls-sdk-ios` | **`https://github.com/cometchat/calls-sdk-ios`** (documented URL 404s) |
| `setup` | Podfile `platform :ios, '16.0'` | package floor is **`.iOS("15.1")`** — 16.0 is the sample app's target |
| `overview` | "Minimum iOS version: 16.0" | the SAME defect on the overview page — the package floor is **15.1** (`Package.swift`; the shipped slice targets ios15.1) |
| `setup` | `region` documented as "`us` or `eu`" | **`in` is also valid** — `CometChatCalls.init` only guards `region.length > 0` (calls-core `CometChatCalls.swift:39`); the harness app itself runs in `in` |
| `setup` | `.setAppId()` / `.setRegion()` | **`.set(appID:)` / `.set(region:)`** — `setAppId`/`setRegion`/`setHost` are `@available(deprecated)` in 5.0.4 |
| `ringing` | `call.callInitiator?.name` (L121, and the ObjC variant L157) | **`(call.callInitiator as? User)?.name`** — `callInitiator` is `AppEntity?` (CometChatSDK 4.1.7 L950); `name` lives on `User : AppEntity` (L1864/1869). The documented line does not compile. |
| `session-settings`, `join-session`, `ringing`, `idle-timeout`, `migration-guide-v5` | `CallType` / `CallTypeVideo` as the session type | **`SessionType` / `SessionType.video`** — `CallType` has **zero** occurrences in the Calls SDK interface. It is a **Chat SDK** type (`CometChat.CallType`), correct ONLY on the ringing path |
| `session-settings` | `SessionType.audio` for audio-only | **`.voice`** — `.audio` and `.audioVideo` are `@available(*, deprecated)` in 5.0.4 |
| `setup`, `session-settings` | the **Objective-C** tabs | **Do not copy them.** Deprecated `setAppId:`/`setRegion:` (real: **`setWithAppID:`/`setWithRegion:`**, read from the framework binary) and too few opening brackets for the chain — they never compiled |
| `ringing`, `voip-calling` | `CometChatCallType*`, `CometChatReceiverType*`, `CometChatCallStatus*` in ObjC | **No `CometChat` prefix** — the generated `CometChatSDK-Swift.h` emits `CallTypeVideo`, `ReceiverTypeUser`, `callStatusRejected`/`callStatusCancelled` |
| `ringing` | `onIncomingCallCancelled(cancelledCall:error:)` | **`onIncomingCallCancelled(canceledCall:error:)`** — the METHOD name has two Ls, the ARGUMENT label has ONE (`canceledCall`). The docs' spelling COMPILES (every `CometChatCallDelegate` member is `@objc optional`, so a near-miss is just a new method) and then **silently never fires** — cancelled calls are never noticed. No gate catches this: G5 passes, and G6 never exercises the cancel path. Verified in the 4.1.7 interface; a review emit shipped exactly this dead handler. |
| `events` | `onScreenShareStarted()` / `onScreenShareStopped()` on `MediaEventsListener` — in the Swift sample AND the "Media Events" table | **Neither exists.** Zero occurrences in the 5.0.4 `.swiftinterface` **and** zero in the shipped binary. `MediaEventsListener`'s real members are `onRecordingStarted`/`Stopped` · `onStreamingStarted`/`Stopped` · `onAudioModeChanged` · `onAudioModesChanged` · `onCameraFacingChanged` · `onAudioMuted`/`onAudioUnMuted` · `onVideoPaused`/`onVideoResumed`. Because the protocol is `@objc optional` the phantom pair COMPILES and then silently never fires — the `canceledCall` failure mode again. There is no LOCAL screen-share event on iOS at all; only the peer events `onParticipantStartedScreenShare`/`onParticipantStoppedScreenShare` are real. **Still wrong on the corrected preview — not covered by PR #489.** |
| `ringing` | (unstated) | **Chat-SDK enum casing is inconsistent** — `Call(receiverId:callType:receiverType:)` takes `CometChat.CallType` and `CometChat.ReceiverType` (Capitalised) while `rejectCall(status:)` takes `CometChat.callStatus` (lowercase). Verified in CometChatSDK 4.1.7 lines 958/1238/2479. |
| `session-settings`, `events` | `CameraFacing.BACK` — the "CameraFacing Values" table on BOTH pages, and `.setInitialCameraFacing(.BACK)` in the session-settings sample | **`.REAR`** — `CameraFacing`'s only cases are **`.FRONT` / `.REAR`** (UPPERCASE, verified in the 5.0.4 `.swiftinterface`). **`.BACK` does not exist** and fails `swiftc` ("type 'CameraFacing' has no member 'BACK'"). `CameraFacing` is ALSO the ONE Calls-SDK enum with UPPERCASE cases — every other enum is lowercase (`AudioMode.speaker`, `LayoutType.tile`, `SessionType.video`), so writing `.front`/`.rear` by analogy ALSO fails to compile. Use `.FRONT` / `.REAR`. (This one is NOT in docs PR #489 — separate docs fix owed; owner: docs.) |

Docs PR cometchat/docs#489 **merged 2026-09-08; re-verified below** against the live `/calls/ios/**` pages.
Almost every row above is now CORRECT on the live pages — the live page matches the right-hand ("Reality")
column: `AudioMode` (events/session-settings/recording), `CometChat.callStatus` (ringing), `.setSessionType`
in place of `.setType` (ringing/session-settings/join-session/idle-timeout/migration-guide-v5),
the SPM URL `…/calls-sdk-ios`, `region` now "`us`, `eu` or `in`", `.set(appID:)`/`.set(region:)` (and the
ObjC `setWithAppID:`/`setWithRegion:`), `(call.callInitiator as? User)?.name`, `SessionType`/`SessionType.video`
for the session type, `SessionType.voice` for audio-only, the corrected ObjC tabs (no `CometChat`-prefixed
enum constants — `ReceiverTypeUser`/`CallTypeVideo`/`callStatusRejected`/`callStatusCancelled`), the
`onIncomingCallCancelled(canceledCall:error:)` one-L argument label, and the removal of the phantom
`onScreenShareStarted`/`onScreenShareStopped` from `MediaEventsListener` (the events page now states outright
that `MediaEventsListener` has NO screen-share callback and points to the peer-only
`onParticipantStartedScreenShare`/`StoppedScreenShare`). **STILL wrong on the live pages: `CameraFacing.BACK`**
— both `session-settings` and `events` still show `.FRONT` / `.BACK` in their "CameraFacing Values" tables (and
the session-settings sample still uses `.setInitialCameraFacing(.FRONT)`), so the `.BACK → .REAR` carve-out
above stays exactly as-is (owner: docs, not in #489). Every correction stays as defensive Swift guidance
regardless — the pages can regress.
