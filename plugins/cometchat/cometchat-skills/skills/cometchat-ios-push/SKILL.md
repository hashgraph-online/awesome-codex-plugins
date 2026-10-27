---
name: cometchat-ios-push
description: "Add push notifications to an iOS CometChat app — APNs registration, token handoff, tap-to-open, badge counts and VoIP call pushes. Triggers: 'push notifications cometchat ios', 'apns cometchat', 'open chat from notification ios', 'voip push call ios'."
license: "MIT"
compatibility: "CometChatUIKitSwift 5.1.22 · CometChatSDK 4.1.7 · iOS 15.1+"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat ios push apns voip pushkit notifications swift v5"
---

## Companion skills (read first)
- `cometchat-ios-core` owns setup and login. This skill ADDS delivery. It is **docs-first and thin**: push depends on your Apple account, certificates and Dashboard configuration, so fetch the notifications docs via `cometchat-ios-core/references/docs-map.md` rather than trusting a baked recipe.

## Use this skill when
"add push notifications", "open the right chat when a notification is tapped", "ring on an incoming call while backgrounded".

## What you must have before any code
Push is **not** a code-only feature. All of these are prerequisites and none are things a skill can do for the user: an Apple Developer account with the Push Notifications capability, an APNs key or certificate uploaded to the **CometChat Dashboard**, and the Notifications product enabled for the app. If any are missing, say so plainly and stop — do not emit code that cannot work.

## The shape of the integration — use `CometChatPushNotifications`, do NOT hand-roll
The current, canonical iOS path is the **`CometChatPushNotifications`** SDK (module `CometChatPushNotificationsSwift`), the same one `cometchat-ios-v5-sdk` documents. Do **not** hand-roll `UIKitSettings.set(deviceToken:)` / `set(voipToken:)`, `PKPushRegistryDelegate` or `CXProviderDelegate` — those setters exist but are the legacy path the sample app and current docs no longer use.

1. Request authorisation and register for remote notifications (on a real device — **the simulator does not receive APNs**).
2. After `CometChat.init`, call `CometChatPushNotifications.shared.initialize(config:)` and set its `.delegate`. In `didRegisterForRemoteNotificationsWithDeviceToken`, forward the APNs token with `CometChatPushNotifications.shared.registerDeviceToken(_:)`. **Ordering is not your problem** — the token can arrive before login; the SDK caches it and binds it to the user automatically once you initialize and the user logs in. (There is no need to gate `didRegister…` on login, and no `set(deviceToken:)` call.)
3. Handle the tap: read the payload, resolve the conversation, and push your chat screen — the same screen core builds. A notification that opens the app to the wrong place is the push equivalent of a dead-end affordance.
4. **Log out unregisters.** Leaving a stale token delivers a user's messages to a device someone else may now be using — treat it as a correctness and privacy requirement, not a nicety.

## VoIP / calls
Ringing while backgrounded is **also `CometChatPushNotifications`**, not a hand-rolled channel: it owns PushKit + CallKit for you (`registerForVoIPPushes()`, `presentCallScreen(for:sessionId:)`). **Never write your own `PKPushRegistryDelegate` / `CXProviderDelegate` or call `UIKitSettings.set(voipToken:)`** — the SDK owns both and a hand-rolled one fights it for the same callbacks. Full VoIP wiring lives in `cometchat-ios-v5-sdk` (§ "VoIP call notifications"); it needs an APNs **VoIP** provider in the Dashboard, the Voice-over-IP Background Mode, and a physical device.

## Gotchas
- **Simulator cannot verify this.** Delivery must be checked on a physical device; expect the automated gate to report push as blocked-external.
- **Badge counts drift** unless you update and clear them deliberately.
- **Sandbox vs production APNs** are different environments — a token from one will not deliver on the other.

## Verify it works
On a real device: background the app, send a message from another user, see the notification, tap it and land in the right conversation. Then log out and confirm notifications stop.
