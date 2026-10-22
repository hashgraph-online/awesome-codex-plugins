---
name: cometchat-ios-v5-sdk
description: "Add voice & video calling to any iOS app FROM SCRATCH with the headless CometChat Calls SDK v5 (`CometChatCallsSDK`, via Swift Package Manager) — no UI Kit. init→login→generateToken→joinSession into a UIView, CallSession listeners, in-call actions (mute/video/layout/record/transcribe/PiP), meet-style session rooms AND 1:1 ringing (Chat SDK signaling + Calls SDK media). Triggers: 'add calling from scratch ios', 'standalone video call swift', 'headless calls sdk ios', 'build my own call screen ios', 'meeting room join by session id ios', 'one-on-one ringing call without uikit ios'."
license: "MIT"
compatibility: "iOS 15.1+ (the Calls SDK package floor; the docs' Podfile sample says 16.0 — that is the SAMPLE APP's target, not the package minimum). CometChatCallsSDK ~> 5.0 (verified against 5.0.4). 1:1 ringing also needs CometChatSDK v4 (verified against 4.1.7 — the version this pack compiles against; the live getting-started page pins a newer 4.1.9, so re-check the docs before overriding) for signaling. Swift/UIKit; the call surface is a UIView, so SwiftUI hosts it via UIViewRepresentable."
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat calls sdk v5 headless voice video webrtc swift ios calling standalone"
---

> **Ground truth:** `CometChatCallsSDK` v5 + catalog `ios-calls-v5.json` (the closed symbol list — every type below is in it). Official docs: `/calls/ios/**` = **v5** · Docs MCP. Fetch exact `SessionSettings` fields, event names and signatures from the docs (`references/docs-map.md`) — never memory. **⚠️ Twelve doc pages contain symbols that DO NOT COMPILE — see "Doc corrections" below; prefer THIS skill's names over the page's.** **APPEND to the user's app — additive wiring only.**

## Companion skills (read first)
- **Standalone/headless entry** — owns its own package (the Calls SDK), no `-core` sibling, never depends on the iOS UI Kit. **1:1 ringing** additionally drives the **Chat SDK** (`CometChatSDK` v4) for signaling.
- **App wants chat too, or the prebuilt call UI?** `cometchat-ios-core` + `cometchat-ios-calls` — not this skill.

## Use this skill when
"add calling from scratch / without the UI Kit", "standalone voice/video on iOS", "build my own call screen", "headless calls SDK", "meeting-room join by session id", "one-on-one ringing".

## ASK FIRST (BAKED) — two choices, and NOTHING upstream asks them
Ask whichever the request has not already settled, then **WAIT**. Never infer from silence — each answer means a different SDK set and a different screen.
1. **Prebuilt call UI, or build your own?** Prebuilt (drop-in, themeable) → **STOP, route to `cometchat-ios-calls`.** Build your own → continue here.
2. **Meet-style room, or 1:1 ringing?** *Room* — everyone joining the same session id lands in one call; Calls SDK only. *Ringing* — you call a specific user and their device rings; adds `CometChatSDK` v4 for signaling (signatures: `references/docs-map.md` § "1:1 RINGING"), plus `CometChatPushNotifications` to ring while the app is backgrounded/closed.

Only EXPLICIT wording settles a question — "from scratch"/"my own call screen" → 1, "ringing"/"call a user" → 2. **"Add calling to my iOS app" settles NEITHER — ask both.**

## Prerequisites & install
**Swift Package Manager only — never CocoaPods**, even if a `Podfile` exists (same rule as `cometchat-ios-core`: CocoaPods distribution is winding down; a Podfile is a detection signal, not an instruction). In Xcode: *File → Add Package Dependencies*, URL:
```
https://github.com/cometchat/calls-sdk-ios
```
⚠️ **The docs print `github.com/cometchat/cometchat-calls-sdk-ios` — that repo 404s.** Use the URL above. The package vends ONE product, `CometChatCallsSDK`, which bundles **WebRTC** as a second binary target — do not add WebRTC separately.

**1:1 ringing additionally needs the Chat SDK** (`CometChatSDK` v4) for signaling — add it as a second SPM package: URL `https://github.com/cometchat/chat-sdk-ios` (product `CometChatSDK`, verified against 4.1.7). Without it the `import CometChatSDK` on the ringing path does not resolve. (Meet-style / room-only does NOT need it.)

**Info.plist — REQUIRED or the call dies on first permission prompt:** `NSCameraUsageDescription` + `NSMicrophoneUsageDescription`. For calls that survive backgrounding, add **Background Modes** → *Audio, AirPlay and Picture in Picture* (+ *Voice over IP* if you use VoIP push).

**Credentials:** App ID · Region · Auth Key (dev only). Load the CLI on demand — `npx @cometchat/skills-cli@3 auth login` → `provision use --app-id <id> --json` (`@3` pins the CLI major that matches the v5 skills). Already have App ID / Region / Auth Key? Just paste them. Mint **auth tokens server-side** for production; never ship the Auth Key.

## Init & login ordering (BAKED — invariant)
Init (once, must succeed) → `CometChatCalls.login(...)` → then `generateToken` / `joinSession` / listeners. Nothing joins before init+login resolve.
- **DEFAULT to `CometChatCalls.initFromSettings(onSuccess:onError:)`** — the ai-agent / telemetry-attributed path (persists `integrationSource="ai-agent"`). It takes **no settings argument**: it reads a **physical `cometchat-settings.json` from `Bundle.main`** (root `appId` + `region`; optional `callsSDK` → `host`/`adminHost`/`clientHost`/`callsHost`). The file **MUST be in the target's Copy Bundle Resources** or init fails `SETTINGS_FILE_NOT_FOUND`. It is intentionally undocumented (ai-agent-only) — the settings shape is baked in `references/docs-map.md`.
- **Fallback (public-doc path):** `CallAppSettingsBuilder().set(appID:).set(region:).build()` → `CometChatCalls(callsAppSettings:onSuccess:onError:)`. ⚠️ Use `set(appID:)`/`set(region:)` — the `setAppId`/`setRegion`/`setHost` spellings the docs use are **deprecated** in 5.0.4.
- ⚠️ **Never do both.** A direct builder init AFTER `initFromSettings` re-attributes the app to `"manual"` and the ai-agent telemetry is lost.

## SDK method map (BAKED closed list — from the catalog; signatures → FETCH from docs)
- **Lifecycle:** `CometChatCalls.initFromSettings` · `CometChatCalls(callsAppSettings:)` · `CallAppSettingsBuilder` · `CometChatCalls.login` (UID+authKey / UID+apiKey / authToken) · `logout` · `getLoggedInUser` → `CallsUser`
- **Session:** `CometChatCalls.generateToken` · `CometChatCalls.joinSession` · `CometChatCalls.sessionSettingsBuilder` · `SessionSettingsBuilder` → `SessionSettingsBuilder.SessionSettings` (NESTED — that is the type `joinSession(callSetting:)` takes)
- **⚠️ TWO join paths, both real in 5.0.4** — pick one: `generateToken(sessionID:)` → `joinSession(callToken:callSetting:container:)`, **or** `joinSession(sessionID:callSetting:container:)` directly.
- **In-call actions — on `CallSession.shared`, for CUSTOM controls ONLY** (the default surface already renders them; see pitfall #1): `leaveSession` · `muteAudio`/`unmuteAudio` · `pauseVideo`/`resumeVideo` · `setLayout` · `setAudioMode` · `switchCamera` · `raiseHand`/`lowerHand` · `startRecording`/`stopRecording` · `startTranscription`/`stopTranscription` · `startStreaming`/`stopStreaming` · `pinParticipant`/`unpinParticipant` · `muteParticipant` · `pauseParticipantVideo` · `enablePictureInPictureLayout`/`disablePictureInPictureLayout` · `isCallSessionActive`
- **Listeners (add on `CallSession.shared`, remove on teardown):** `SessionStatusListener` · `MediaEventsListener` · `ParticipantEventListener` · `LayoutListener` · `ButtonClickListener` · `clearAllListeners`
- **Call logs:** `CallLogsBuilder` → `CallLogsRequest` → `CallLog` (+ `CallUser`/`CallGroup`/`CallEntity`/`CallStatus`/`CallCategory`/`CallDirection`)
- **Enums:** `AudioMode` (`.speaker`/`.earpiece`/`.bluetooth`/`.headphones`) · `SessionType` (`.video`/`.voice`) · `LayoutType` (`.tile`/`.spotlight`/`.sidebar`) · **`CameraFacing` (`.FRONT`/`.REAR` — UPPERCASE, the ONE Calls-SDK enum that breaks the lowercase convention; `.front`/`.rear` fail to compile, and the docs' `.BACK` does NOT exist — see Doc corrections)**
> This map is a **curated highlight, NOT the full surface** — the AUTHORITATIVE closed list is the **`ios-calls-v5.json` catalog** (60 symbols). A symbol is real **iff it's in the catalog** — confirm THERE, then fetch its exact signature from the docs page in `references/docs-map.md`.

## Listener lifecycle (BAKED)
Register listeners on `CallSession.shared` **BEFORE** joining; remove each one (or `clearAllListeners()`) on teardown, and call `CallSession.shared.leaveSession()` when the screen goes away. For ringing also `CometChat.removeCallListener(<id>)`. Never leak.

**The listener contract (all five, verified in the 5.0.4 interface):**
- Every listener protocol is `@objc` and **EVERY member is `optional`.** Implement ONLY the callbacks you need — do NOT stub the rest. **A name that is NOT in the protocol also compiles, then silently never fires** — copy callback names from the events page / `references/docs-map.md`, never by analogy.
- Because they are `@objc`, the conforming type MUST be a class inheriting **`NSObject`**.
- Exact add/remove pairs on `CallSession.shared` — the names are NOT in the catalog (it is types-only), so use these:

| Protocol | Register / remove |
|---|---|
| `SessionStatusListener` | `addSessionStatusListener(_:)` / `removeSessionStatusListener(_:)` |
| `MediaEventsListener` | `addMediaEventsListener(_:)` / `removeMediaEventsListener(_:)` |
| `ParticipantEventListener` | `addParticipantEventListener(_:)` / `removeParticipantEventListener(_:)` |
| `LayoutListener` | `addLayoutListener(_:)` / `removeLayoutListener(_:)` |
| `ButtonClickListener` | `addButtonClickListener(_:)` / `removeButtonClickListener(_:)` |

- **`ButtonClickListener` callbacks fire BEFORE the SDK's own action, and do NOT suppress it.** Reacting to `onLeaveSessionButtonClicked` must NOT also call `leaveSession()` — the SDK is already leaving; doing both double-leaves.
- **`Participant` has EXACTLY 12 fields, all Optional:** `uid` · `name` · `avatar` · `mid` · `state` · `isJoined` · `joinedAt` · `leftAt` · `deviceID` · `totalAudioMinutes` · `totalVideoMinutes` · `totalDurationInMinutes`. Identity is **`uid`** (`String?` — unwrap before passing to `muteParticipant(participantId:)`), never `name`.
- **⚠️ The docs use SIX `Participant` fields that DO NOT EXIST** — `pid`, `isPinned`, `isAudioMuted`, `isVideoPaused`, `isPresenting`, `raisedHandTimestamp`. Copying any of them fails to compile. `pid` → use `uid`; the five state flags have **no field at all** — track that state yourself from the `ParticipantEventListener` callbacks (`onParticipantAudioMuted`/`Unmuted`, `onParticipantHandRaised`/`Lowered`, `onParticipantStarted`/`StoppedScreenShare`).

## Least-code recipe (meet-style — ORDER, not signatures)
```swift
// Fetch every signature/field from references/docs-map.md. This is the ORDER, which is the part that bites.
import UIKit
import CometChatCallsSDK

1. CometChatCalls.initFromSettings(onSuccess:onError:)   // ai-agent default; reads bundled cometchat-settings.json
2. CometChatCalls.login(UID:authKey:onSuccess:onError:)   // or login(authToken:) in production
3. let settings = CometChatCalls.sessionSettingsBuilder.setSessionType(.video).build()   // NOT .setType — see Doc corrections
4. CallSession.shared.addSessionStatusListener(self)      // register BEFORE joining
5. CometChatCalls.joinSession(sessionID:callSetting:container:onSuccess:onError:)  // container = a UIView with REAL bounds
   //   or: generateToken(sessionID:) -> joinSession(callToken:callSetting:container:)
6. // NO control buttons needed — the joined surface ALREADY renders mute/video/leave.
7. // teardown -> CallSession.shared.clearAllListeners(); CallSession.shared.leaveSession()
```
The `container` MUST have real bounds — a zero-frame view renders invisibly. In SwiftUI wrap it with `UIViewRepresentable`.

## VoIP call notifications (SEPARATE package — `CometChatPushNotifications`)
Ringing a user whose app is **backgrounded or terminated** is NOT the Calls SDK's job. It is
`CometChatPushNotifications` **1.0.0** — a different package. Do not hand-roll it.

- **Install:** SPM `https://github.com/cometchat/push-notifications-sdk-ios` @ `1.0.0` (product
  `CometChatPushNotificationsSwift`). **Its `Package.swift` declares NO dependencies, yet the binary
  imports `CometChatSDK` + `CometChatCallsSDK`** — the app must ALSO have both packages above
  (`chat-sdk-ios` + `calls-sdk-ios`) or the build fails. **`import CometChatPushNotificationsSwift`** — the
  module name differs from the class name; importing `CometChatPushNotifications` does not compile.
- **Three steps, nothing more:**
  1. after `CometChat.init`: `CometChatPushNotifications.shared.initialize(config: .init(providerId:))` then set `.delegate`
  2. in `AppDelegate`: forward `registerDeviceToken(_:)` (+ `handleRegistrationFailure(_:)`)
  3. implement `CometChatPushNotificationsDelegate` — **every method is optional**; the ones that matter are `presentCallScreen(for:sessionId:)` and `onCallCleanupComplete()`
- **NEVER emit a `PKPushRegistryDelegate` or a `CXProviderDelegate`.** The SDK owns both. Writing
  either is the #1 mistake here — it fights the SDK for the same callbacks.
- **Cold start:** call `CometChatPushNotifications.shared.notifyCallsSDKReady()` from the **login**
  success — NOT init success. It only lifts the buffer; it does not check that anyone is logged in,
  so releasing at init hands `presentCallScreen` an unauthenticated session and the `joinSession`
  after it fails on auth. (A 3s safety timeout fires the buffered call anyway, so a slow login can
  still present early — do not assume a live session in the call screen.)
- **The call is ALREADY accepted** when `presentCallScreen` fires — present UI and join; do not accept again.
- **Prerequisites (state them, they are not code):** an **APNs VoIP provider** in the dashboard,
  the Push Notifications + Background Modes (Voice over IP, Remote notifications) capabilities, and
  a **PHYSICAL DEVICE** — VoIP pushes are never delivered to the Simulator.
- `ForegroundCallPresentation` = `.callKit` (default) · `.inApp` (`CometChatIncomingCallView`, styled
  via `CometChatIncomingCallStyle`) · `.none` (present your own).

> **Callback shapes differ PER API and `?.` on a non-optional does not compile** — `login`/`logout`
> hand you a NON-optional `CometChatCallException`; `initFromSettings`/`generateToken`/`joinSession`
> hand you an Optional. Exact table + `isCallSessionActive()` arity: `references/docs-map.md`.

## Doc corrections (VERIFIED against CometChatCallsSDK 5.0.4 — prefer these over the page)
| The docs write | It does not compile — use |
|---|---|
| `AudioModeType` (events, session-settings, recording) | **`AudioMode`** — `AudioModeType` exists in neither the interface nor the binary |
| `CometChat.CallStatus` (ringing) | **`CometChat.callStatus`** — lowercase `c`; Swift is case-sensitive |
| `.setType(.video)` (ringing, session-settings, join-session, idle-timeout, migration-guide) | **`.setSessionType(.video)`** — `SessionSettingsBuilder` has no `setType` in any spelling |
| SPM URL `…/cometchat-calls-sdk-ios` (setup) | **`https://github.com/cometchat/calls-sdk-ios`** — documented URL 404s |
| `region` is "`us` or `eu`" (setup) | **also `in`** — the SDK only checks the string is non-empty; `in` is a live region |
| `.setAppId()` / `.setRegion()` (setup) | **`.set(appID:)` / `.set(region:)`** — the `setX` spellings are deprecated in 5.0.4 |
| `call.callInitiator?.name` (ringing) | **`(call.callInitiator as? User)?.name`** — `callInitiator`/`callReceiver` are `AppEntity?`; only `User` has `name` |
| `CallType` / `CallTypeVideo` as the session type (5 pages) | **`SessionType` / `SessionType.video`** — `CallType` has **zero** occurrences in `CometChatCallsSDK`. It is a **Chat SDK** type (`CometChat.CallType`), valid ONLY on the ringing path. Never pass it to `SessionSettingsBuilder` |
| `SessionType.audio` for audio-only | **`.voice`** — `.audio` and `.audioVideo` are `@available(*, deprecated)` in 5.0.4 |
| The **Objective-C** tabs (setup, session-settings, ringing, voip-calling) | **Do not copy them** — deprecated setters, too few opening brackets, and enum constants wrongly `CometChat`-prefixed. Exact names: `references/docs-map.md` |
| `participant.pid` / `.isPinned` / `.isAudioMuted` / `.isVideoPaused` / `.isPresenting` / `.raisedHandTimestamp` (actions, participant-management, custom-participant-list — 23×) | **None of these exist on `Participant`.** `pid` → **`uid`**; the five flags have no field — derive them from the participant events. Two review emits failed `swiftc` on exactly this |
| `CallSession.shared.setAudioMode` / `setLayout` taking an enum | **They take a `String`** — `"SPEAKER"`/`"EARPIECE"`/`"BLUETOOTH"`/`"HEADPHONES"`, `"TILE"`/`"SPOTLIGHT"`/`"SIDEBAR"`. Only the **builder** forms take `AudioMode` / `LayoutType`. Same method name, two different parameter types |
| docs show only `login(UID:apiKey:)` / `login(authToken:)` | **`login(UID:authKey:)` also exists** in 5.0.4 — the docs are incomplete, the skill's recipe is correct |
| — (unstated anywhere) | **Chat-SDK enum casing is INCONSISTENT** — `CometChat.CallType`/`.ReceiverType` Capitalised, `CometChat.callStatus` lowercase. Analogy fails to compile; check each. |

Docs PR cometchat/docs#489 merged 2026-09-08 and the live `/calls/ios/**` pages now carry these fixes — re-verified against the live pages. The one exception is **`CameraFacing.BACK`**: it is still live on both `session-settings` and `events` (`.BACK`, not `.REAR`) — #489 did not touch it (separate docs fix owed). Keep every correction above as defensive guidance. Detail + per-symbol live status: `references/docs-map.md`.

## Common pitfalls (BAKED)
- **Don't duplicate the built-in call controls (the #1 mistake).** The joined session renders a COMPLETE call UI — mute, camera, layout, participants, raise-hand, leave. Do NOT add your own buttons. `CallSession.shared` actions are for CUSTOM controls ONLY — reach for them **just when the user EXPLICITLY asks** to replace the defaults, and hide the built-ins first (`hide*Button` list in `references/docs-map.md`). To merely REACT to the leave button, implement `ButtonClickListener.onLeaveSessionButtonClicked` — never a second button.
- **Ringing teardown needs BOTH SDKs.** `CallSession.shared.leaveSession()` ends YOUR media; `CometChat.endCall(sessionID:)` tells the peer and completes the call log. Do only the first and the other side still thinks the call is live.
- **Zero-bounds container** — `joinSession` mounts into your `UIView`; give it real size.
- **CRASH — declare `var window: UIWindow?` on your AppDelegate, even in a scene-based app.** The SDK reads `UIApplication.delegate.window`; without it the app aborts (`unrecognized selector`) right after the camera permission is granted. Detail: `references/docs-map.md`.
- **Missing Info.plist usage strings** — no `NSCameraUsageDescription`/`NSMicrophoneUsageDescription` means iOS kills the app at the first permission request.
- **`cometchat-settings.json` not bundled** — `initFromSettings` fails `SETTINGS_FILE_NOT_FOUND`; the file must be in Copy Bundle Resources.
- **Double init** — a builder init after `initFromSettings` silently re-attributes telemetry to `"manual"`.
- **No local screen share on iOS.** Only the PEER events `onParticipantStarted`/`StoppedScreenShare` are real — no start/stop action (web has one), and local capture needs a Broadcast Upload Extension. Do not emit one. (The docs' `onScreenShareStarted`/`Stopped` do not exist — see docs-map.)
- **No virtual background on iOS** — the web Calls SDK has it; this one does not.
- **No roster, no participant state — so moderation is UNBUILDABLE.** There is no participant-list accessor, `Participant` carries no mute/pin/hand/share flag, and (verified live on two clients) the participant events deliver nothing: `onParticipantJoined`/`Left` never fire and `onParticipantListChanged` arrives EMPTY. You can never obtain a peer `uid`, so `muteParticipant`/`pinParticipant`/`pauseParticipantVideo` have no argument. Do NOT emit them or a custom roster — the built-in participant panel is already on screen. Detail: `references/docs-map.md`.
- **Assuming a signature** — event names, `SessionSettings` fields and action params are FETCHED from docs, never guessed.

## Verify it works
- **Tier-1 catalog:** every `CometChatCallsSDK` symbol emitted appears in `ios-calls-v5.json` (`node test-suite/scripts/verify-catalog.mjs --family ios-calls-v5`).
- **Tier-2 compile:** the emit type-checks against the installed `CometChatCallsSDK` (5.0.4) with `swiftc -typecheck`.
- **Tier-3 smoke:** the calls round-trip on a simulator (init→login→generateToken→join-wiring→leaveSession). **Ringing runs as TWO concurrent simulators** (one process per role), and only counts if both report success on the SAME session id — live-certified, not just wired.
