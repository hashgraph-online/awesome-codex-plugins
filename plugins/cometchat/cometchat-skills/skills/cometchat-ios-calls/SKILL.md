---
name: cometchat-ios-calls
description: "Add voice and video calling to an iOS CometChat app — call buttons, incoming/ongoing call screens, call logs, and CallKit ringing. Triggers: 'add video calling ios', 'cometchat voice call swift', 'incoming call screen ios', 'call logs cometchat ios'."
license: "MIT"
compatibility: "CometChatUIKitSwift 5.2.3+ · CometChatCallsSDK 5.0.4+ (Up to Next Major) · iOS 15.1+"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat ios calls voice video callkit swift v5"
---

## Companion skills (read first)
- `cometchat-ios-core` owns setup and the chat surface. This skill ADDS calling, and with it the `CometChatCallsSDK` package (`https://github.com/cometchat/calls-sdk-ios`, Up to Next Major from 5.0.4). The kit does not declare it (it links it optionally since 5.2.3), so this skill is where it gets added. If the project already has it, reuse that entry; never add it twice.

## Use this skill when
"add voice/video calling", "show an incoming call screen", "add call history".

## Calls SDK init and login after the UI Kit login

**Since 5.2.0 the kit logs the Calls SDK in for you:** `CometChatUIKit.login(uid:)` /
`login(authToken:)` call `CometChatCalls.login(authToken:)` with the chat token once the kit's own
Calls init has finished, and logout ends that session too (5.2.3 source, `CometChatUIKit.swift`
`loginCallsSDK` / `logoutCallsSDK`). Before 5.2.0 it did not, and `CometChatCallLogs` showed
"Oops! Looks like something went wrong" with an EMPTY `authToken` (measured on 5.1.19/5.0.3).

Still run the bootstrap below after the UI Kit login. It is now for **attribution**, not auth: the
core recipe's classic `CometChatUIKit(uiKitSettings:)` init makes the kit init the Calls SDK
through the `CallAppSettingsBuilder` path (stamped `"manual"`); this `initFromSettings` call
re-stamps the Calls SDK as `"ai-agent"`, and its login repeats the kit's with the same chat token. (Kit-managed
login is source-verified on 5.2.3; this bootstrap was device-verified on 5.1.22.)

```swift
// DEFAULT — the ai-agent / telemetry-attributed init (persists integrationSource="ai-agent").
// Takes NO settings argument: it reads the SAME bundled cometchat-settings.json the core skill
// already ships (Copy Bundle Resources) — do not build a second settings object.
_ = CometChatCalls.initFromSettings(onSuccess: { _ in
    guard let token = CometChat.getUserAuthToken() else { return }
    CometChatCalls.login(authToken: token,
                         onSuccess: { _ in /* calls surfaces are now live */ },
                         onError:   { error in debugPrint("calls login:", error.errorDescription) })
}, onError: { error in debugPrint("calls init:", error?.errorDescription ?? "nil") })
```

⚠️ **Init the Calls SDK via `CometChatCalls.initFromSettings`, NOT the classic
`CometChatCalls(callsAppSettings: CallAppSettingsBuilder()...)` builder — that path attributes the app
to `"manual"` and loses the ai-agent telemetry (RULES §5 / AUDIT-175, the SAME rule the headless
`cometchat-ios-v5-sdk` follows).** The builder init is the **FALLBACK ONLY**, for an app that does not
bundle `cometchat-settings.json`:

```swift
// FALLBACK — only when no cometchat-settings.json is bundled. Loses ai-agent attribution.
let callSettings = CallAppSettingsBuilder().set(appID: appID).set(region: region).build()
_ = CometChatCalls(callsAppSettings: callSettings, onSuccess: { _ in /* ... login as above ... */ },
                   onError: { error in debugPrint("calls init:", error?.errorDescription ?? "nil") })
```

**Never do both** — a builder init AFTER `initFromSettings` re-attributes the app to `"manual"`.
`initFromSettings` fails `SETTINGS_FILE_NOT_FOUND` if the file is not in Copy Bundle Resources — the
core skill already adds it for chat, so a UI-Kit app that shipped chat first already satisfies this.

Chat-only apps skip all of this and do not link the Calls SDK at all (5.2.3 builds and launches
without it; see the core skill's install notes).

## The five components
| Component | Role |
|---|---|
| `CometChatCallButtons` | Voice/video triggers. **Has NO no-arg init — construct it as `CometChatCallButtons(width:height:)`.** `set(user:)` **or** `set(group:)`, plus `set(controller:)`. Put it in the message header's slot, not beside it. |
| `CometChatIncomingCall` | The ringing screen. `set(call:)`, `set(onAcceptClick:)`, `set(onCancelClick:)` — **decline is `onCancelClick`, there is no `onDeclineClick`.** |
| `CometChatOngoingCall` | The in-call surface. `set(sessionId:)` — **lowercase `d`**; `set(sessionID:)` does not compile. Also `set(callSettingsBuilder:)`, `set(callWorkFlow:)`, `set(call:)` (5.2.1+). `setOnCallEnded(onCallEnded:)` fires since 5.2.1 (with the `set(call:)` call, or a stand-in carrying the session id), but the screen then calls `self.dismiss(animated:)` itself, so present it modally; never embed it. |
| `CometChatOutgoingCall` | The caller's ringing screen while the other side has not answered. `set(call:)`, `set(onCancelClick:)`. |
| `CometChatCallLogs` | Call history. See the `Any` warning below — this component is the worst offender. |

> **`CometChatCallLogs` callbacks are `Any`-typed — cast before touching anything.** Unlike every other list component, five of its setters hand back untyped values and will not compile if you use them directly:
> `set(onItemClick:)` → `(_ callLog: Any)` · `set(onCallButtonClicked:)` → `(Any)` · `set(options:)` → `(_ callLog: Any)` · `set(onLoad:)` → `([Any])` · **`set(onError:)` → `(_ error: Any)`**, not `CometChatException` like everywhere else.
> ```swift
> logs.set(onItemClick: { callLog in
>     guard let log = callLog as? CallLog else { return }   // NOT `as? Call` — that cast FAILS at
>     ...  // runtime and makes the tap a silent no-op (measured: RUNTIME TYPE = CallLog).
>     // CallLog exposes status, type, mode, initiator, receiver — not the Call spellings
>     // (callStatus/callType/callInitiator/callReceiver). CallLog is a Calls-SDK type.
> })
> logs.set(onError: { error in
>     // The value is the CALLS SDK's exception type — casting to the chat SDK's
>     // CometChatException fails and prints nothing useful (measured).
>     debugPrint((error as? CometChatCallException)?.errorDescription ?? "\(error)")
> })
> ```

> **`sessionID` vs `sessionId` — the same concept, spelled two ways.** The SDK's `Call` exposes **`sessionID`** (capital), while the kit's `CometChatOngoingCall` takes **`set(sessionId:)`** (lowercase). Reading a log and starting a call in the same function means using both spellings; neither compiles in the other's place.

Voice/video click handlers on `CometChatCallButtons` are **properties**: `callButtons.onVoiceCallClick = { user, group in ... }`, `onVideoCallClick` likewise. And it is `set(callSettingsBuilder:)` — **plural "Settings"**.

> **`@MainActor` if you construct these in a factory.** Inside a `UIViewController` this wiring is free (already main-actor). But if you wrap it in a standalone factory/enum/`static` method, mark that context `@MainActor` — the components' setters are main-actor-isolated. **`CometChatOutgoingCall` is the strictest:** unlike `CometChatIncomingCall`/`CometChatCallButtons` it carries no `@preconcurrency`, so under Swift 5 its `set(call:)`/`set(onCancelClick:)` are a HARD ERROR from a nonisolated context ("call to main actor-isolated instance method ... in a synchronous nonisolated context"), not just a warning. (Same rule as `cometchat-ios-core`'s `@MainActor`-factory note.)

```swift
// Minimum voice-video-calls wiring — all five components (inside a @MainActor context, e.g. a UIViewController)
let callButtons = CometChatCallButtons(width: 180, height: 40)
callButtons.set(user: user)          // or .set(group:) for a group call
callButtons.set(controller: self)
callButtons.onVoiceCallClick = { user, group in /* initiate voice call */ }
callButtons.onVideoCallClick = { user, group in /* initiate video call */ }

// Present incoming call over any screen via a global app-level listener
let incoming = CometChatIncomingCall()
incoming.set(call: incomingCall)
// accept/cancel closures are TWO-arg: (call: Call?, controller: UIViewController?). A one-arg
// `{ call in ... }` does NOT compile ("expects 2 arguments, but 1 was used").
incoming.set(onAcceptClick: { call, _ in /* push CometChatOngoingCall */ })
incoming.set(onCancelClick: { call, _ in self.dismiss(animated: true) })

let outgoing = CometChatOutgoingCall()
outgoing.set(call: pendingCall)
outgoing.set(onCancelClick: { call, _ in self.dismiss(animated: true) })

let ongoing = CometChatOngoingCall()
// `Call.sessionID` (uppercase D, SDK) is OPTIONAL (String?); `set(sessionId:)` (lowercase d, kit)
// wants a non-optional String — so GUARD it. Passing the optional directly does not compile.
if let sid = pendingCall.sessionID { ongoing.set(sessionId: sid) }

let logs = CometChatCallLogs()
// NOTE: CometChatCallLogs has NO `set(controller:)` — present/push it like any UIViewController
// (e.g. UINavigationController(rootViewController: logs)). Its only setters are the Any-typed
// callbacks below plus set(callRequestBuilder:).
logs.set(onItemClick: { callLog in guard let log = callLog as? CallLog else { return } /* ... */ })
```

## Incoming calls are app-level, not screen-level
A call can arrive on any screen, so listen at the app level (`CometChatCallEventListener` / `CometChatCallEvents`) and present `CometChatIncomingCall` over whatever is showing. Wiring it inside one chat screen means calls are missed everywhere else.

## Permissions and background
Camera and microphone usage descriptions in `Info.plist`, or the app crashes on first call rather than failing gracefully. Ringing while backgrounded is handled by the **`CometChatPushNotifications`** SDK — it owns CallKit + PushKit for you. **Do NOT hand-roll `PKPushRegistryDelegate` / `CXProviderDelegate` or call `UIKitSettings.set(voipToken:)`** (that setter is the legacy path the current docs no longer use). Full VoIP wiring: `cometchat-ios-v5-sdk` § "VoIP call notifications" and `cometchat-ios-push`; needs an APNs VoIP provider in the Dashboard and a physical device.

## Huddle / docked call (Slack-style)
Group calls start, join and render through the Calls SDK into YOUR view: `references/huddle.md` (BAKED — re-verified vs 5.2.3 + Calls 5.0.4), pattern in `cometchat-onboarding/references/clone-mode.md` → *Huddle / drop-in room pattern*.

## Gotchas
- **Simulator limits.** No camera; a WebRTC surface may behave differently than on device. Verify calling on a real device.
- **The kit's group call button and meeting Join present `CometChatOngoingCall` full screen.** For a docked or mini call, follow `references/huddle.md`; don't embed `CometChatOngoingCall` (it dismisses on end).
- **Every call screen needs an exit.** Accept, decline and hang-up must all lead somewhere.
- **Versions.** Kit Up to Next Major from 5.2.3 (it resolves the Chat SDK itself) + Calls SDK Up to Next Major from 5.0.4. Don't stop at kit 5.2.0 to 5.2.2 (launch crash without the Calls SDK) and don't hand-pin the Chat SDK.

## Verify it works
On a device: the call button appears in the header, tapping it rings the other side, the incoming screen shows over whatever was on screen, accept connects with audio and video, hang-up releases camera and microphone, and the call appears in call logs.
