# Platform notes — Flutter Calls SDK v5

Two surfaces that sit beside the call rather than on the join path: keeping a call alive when the
app goes to the background, and ringing a user whose app is closed. Neither is needed to get a
call working; both are needed before shipping one.

## Backgrounding (FLUTTER-ONLY — `CometChatOngoingCallService`)
Android kills a call the moment the app backgrounds unless a foreground service holds it:
`CometChatOngoingCallService.launch()` from the **session-joined** callback (not `build()`), `.abort()`
alongside `leaveSession()`. Both are **safe no-ops on iOS**, where CallKit owns that state — call them
unconditionally, but say that rather than implying they do something on iOS. The manifest permissions
on `/calls/flutter/background-handling` are **not optional**; without them the call drops on background
and reads as a network fault. No iOS or web analogue exists.

## Call notifications when the app is backgrounded or killed (NO single Flutter package)
**iOS has a first-party `CometChatPushNotifications` package that owns PushKit and CallKit. Flutter
does not.** There is no `cometchat_push_notifications` on pub.dev, and **no symbol in this skill's
catalog implements this feature** — if an emit names such a package it invented it. The real shape is
two separate paths over the app's own push plugin:
- **Android** — FCM: register the token with CometChat, receive the call payload, show the incoming UI.
- **iOS** — APNs + PushKit + CallKit, wired by the app (`flutter_callkit_incoming` or equivalent), not by CometChat.
- On accept, **join the session — the call is already accepted server-side**; do not accept again.
- **Prerequisites (state them, they are not code):** a push provider configured in the dashboard, and a **PHYSICAL DEVICE** — neither FCM call pushes nor APNs VoIP pushes reach an emulator or Simulator.
Pages: `/calls/flutter/voip-calling`, `/notifications/flutter-push-notifications-android`, `/notifications/flutter-push-notifications-ios`.

## iOS Simulator on Apple Silicon — `CometChatWebRTC` excludes arm64

`CometChatWebRTC.podspec` sets `EXCLUDED_ARCHS[sdk=iphonesimulator*] = arm64`, and CocoaPods
propagates it into `Pods-Runner`. So the app builds **x86_64** and Flutter warns:

> The following target(s) do not support arm64 architecture, which is a requirement for Apple
> Silicon iOS 26+ simulators: CometChatWebRTC (transitive dependency of Flutter plugin
> cometchat_calls_sdk)

What that means in practice:

- **iOS 18 simulator: works**, through Rosetta. Verified — a calling app built, launched, logged
  in and joined a live session.
- **iOS 26+ simulator: will not run at all.**
- **Physical device: unaffected** (the `ios-arm64` slice is fine).

The vendored `WebRTC.xcframework` **does** ship `ios-arm64_x86_64-simulator`, so the exclusion
looks gratuitous rather than necessary — but it is the SDK's podspec, not something the app can
override cleanly. Target a device or an iOS 18 simulator, and do not spend time hunting a missing
slice that is present.

Nothing in `/calls/flutter/**` mentions this, troubleshooting included. It is the most likely
first-five-minutes blocker for an iOS developer.
