---
name: cometchat-react-native-push
description: "Push notifications for CometChat in React Native — FCM on Android, APNs on iOS, registering the device token with CometChatNotifications, and why none of it can be verified without a real device. Triggers: CometChat push notifications React Native, FCM CometChat RN, APNs chat notifications, notifications not arriving React Native, VoIP call push RN."
license: "MIT"
compatibility: "React Native >=0.77; @cometchat/chat-sdk-react-native ^4.0.28; @react-native-firebase/messaging"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "chat cometchat react-native push notifications fcm apns voip token"
---

> **Ground truth:** `@cometchat/chat-sdk-react-native@4` + catalog `rn-sdk-v4.json` +
> `features.rn-v5.json` → `push-notifications`. Docs:
> `/notifications/react-native-push-notifications-android` · `…-ios`.
> This skill is **docs-first** — fetch the current setup steps; do not bake a Firebase tutorial.

## Companion skills (read first)
- `cometchat-react-native-core` — install, provider chain, init→login→render. Assumed, not repeated here.

## Use this skill when
- "add push notifications" · "notifications aren't arriving" · "VoIP call push" · "register the FCM token"

## Prerequisites & install

Push is **not** web push. There is no service worker. React Native uses the OS transports:

| Platform | Transport | Needs |
|---|---|---|
| Android | **FCM** | `google-services.json` in `android/app/` |
| iOS | **FCM (via Firebase → APNs)** | `GoogleService-Info.plist`, an APNs key uploaded to the dashboard, Push capability in Xcode |

Enable Push Notifications in the CometChat dashboard **first** and add the provider for the right
platform. With `@react-native-firebase/messaging`, **both** Android and iOS use the **FCM** provider —
Firebase relays to APNs on iOS and hands your app an FCM token, so you register it with CometChat as an
FCM platform (see below). A raw-APNs (`APNS_REACT_NATIVE_*`) provider is only for a hand-rolled PushKit /
native-APNs setup that skips Firebase.

## The wiring — three steps, in this order

1. **`init()` → `login()` must have completed.** A token registered before login belongs to nobody.
2. **Get the device token** from your messaging library (typically `@react-native-firebase/messaging`).
3. **Register it with CometChat:**

```
CometChatNotifications.registerPushToken(token, CometChatNotifications.PushPlatforms.FCM_REACT_NATIVE_ANDROID, providerId)
```

Platform constants match the token you actually hold. Because the Firebase library above yields an
**FCM** token on **both** platforms, use `PushPlatforms.FCM_REACT_NATIVE_ANDROID` on Android and
`PushPlatforms.FCM_REACT_NATIVE_IOS` on iOS (verified in `@cometchat/chat-sdk-react-native` `CometChat.d.ts`).
The `APNS_REACT_NATIVE_DEVICE` / `APNS_REACT_NATIVE_VOIP` constants are ONLY for a raw APNs device/VoIP
token from a hand-rolled PushKit setup — do **not** use them with a Firebase FCM token. **Fetch the exact
argument order from the docs page for that platform.** `CometChatNotifications`, `registerPushToken`,
`unregisterPushToken` and `PushPlatforms` are all verified present in `catalogs/rn-sdk-v4.json`.

4. **Unregister on logout** — `unregisterPushToken()`. Skipping this is why a shared or re-used device
keeps delivering the previous user's notifications.

## Token refresh is not optional
Device tokens rotate. Subscribe to your messaging library's token-refresh event and re-register, or
push silently stops working days later for a subset of users — the hardest push bug to diagnose
because nothing fails at the time.

## VoIP / call notifications
Calls need a **data-only** push plus a native dialer integration (CallKeep) so the device rings while
the app is killed. That is a materially bigger build than message push, with its own iOS entitlements.
Fetch `/notifications/react-native-push-notifications-android` and `…-ios` and follow them — do not
improvise it.

## Why this cannot be smoke-tested
Push requires a real device (or an emulator image **with Play services** for FCM), real credentials,
and the app in background or killed. It cannot be verified headlessly, in CI, or on an iOS simulator.
`features.rn-v5.json` marks it accordingly — treat a "works" claim without device evidence as unproven.

## Common pitfalls
1. **Registering before login** — the token is attached to no user.
2. **Not unregistering on logout** — the next user gets the previous user's pushes.
3. **Ignoring token refresh** — push dies quietly, later.
4. **Wrong platform constant** — registration succeeds, delivery never happens.
5. **Missing `google-services.json` / `GoogleService-Info.plist`** — build or registration failure.
6. **Testing on an iOS simulator** — APNs does not work there.
7. **Expecting message-push setup to cover calls** — VoIP needs data-only push + CallKeep.

## Verify it works
- Every emitted symbol is in `catalogs/rn-sdk-v4.json`.
- Dashboard: push enabled, correct provider added for the platform.
- **On a real device:** notification arrives with the app backgrounded **and** killed; tapping it opens
  the right conversation; after logout the device stops receiving that user's notifications.
