---
name: cometchat-flutter-v6-push
description: "Add push notifications to a Flutter app with CometChat — FCM on Android, FCM/APNs on iOS, registered through CometChatNotifications with the Dashboard provider as the sender. THIN + docs-first: the Firebase setup is FETCHED from CometChat's notifications docs; this skill bakes the SDK symbols and the token lifecycle. Triggers: 'add push notifications in flutter', 'FCM push flutter', 'notify me when the app is closed', 'cometchat push flutter'."
license: "MIT"
compatibility: "Flutter >=3.38.9; cometchat_chat_uikit ^6 (6.1.x); cometchat_sdk ^5.0.6 (ships CometChatNotifications); firebase_messaging (FCM)"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat flutter push notifications fcm apns firebase v6"
---

> **Ground truth — DOCS-FIRST.** Push is an EXTERNAL integration (a Firebase project, native config on both platforms, and a Dashboard provider), not a UI Kit widget. The current setup lives in **CometChat's notifications docs — FETCH them**, via `../cometchat-flutter-v6-core/references/docs-map.md` → `/notifications/push-overview` · `/notifications/flutter-push-notifications-android` · `/notifications/flutter-push-notifications-ios`. (The old singular `/notifications/flutter-push-notifications` now redirects to a legacy page — use the per-platform pages above.) This skill bakes ONLY the SDK symbols (verified vs `cometchat_sdk` 5.0.6) and the hardening deltas. **Symbols baked; the step-by-step is fetched.**

## Companion skills (read first)
- `cometchat-flutter-v6-core` — install, credentials, `init→login→render`. This skill ASSUMES it (push registers AFTER login, on the SAME SDK).
- `cometchat-flutter-v6-events` — the listener lifecycle; a push registration is a lifecycle-bound side effect.

## Use this skill when
"add push notifications", "FCM push", "notify me when the app is closed / backgrounded".

## Build it — FETCH the docs, then apply the deltas
1. **FETCH the setup** (source of truth): the notifications docs above. Follow their Firebase project creation, `google-services.json` / `GoogleService-Info.plist` placement, the Gradle/Podfile changes, and (iOS) the APNs key upload. **If the docs are wrong or missing a step, that is a DOCS gap — flag it (`RULES.md` §20), don't bake a permanent workaround.**
2. **Dashboard prerequisite:** configure the **push provider in the CometChat Dashboard** — it is the SENDER. Note the **provider ID**; registration needs it. Without this, nothing is ever delivered no matter how correct the client is.
3. **Install:** `flutter pub add firebase_core firebase_messaging`. `CometChatNotifications` ships with the already-installed `cometchat_sdk` — no extra CometChat package.

## Baked SDK symbols (verified vs 5.0.6 — do NOT guess these)
```dart
import 'package:cometchat_chat_uikit/cometchat_chat_uikit.dart';

// Register AFTER login, with the token you got from firebase_messaging getToken().
Future<void> registerPush(String fcmToken, String providerId) async {
  await CometChatNotifications.registerPushToken(
    PushPlatforms.FCM_FLUTTER_ANDROID,        // FCM_FLUTTER_IOS on iOS; for a raw APNs token use APNS_FLUTTER_DEVICE / APNS_FLUTTER_VOIP (there is NO plain PushPlatforms.APNS)
    providerId: providerId,                   // from the Dashboard provider you configured
    fcmToken: fcmToken,
    onSuccess: (res) {},
    onError: (e) {},
  );
}

// On logout — otherwise the device keeps receiving the previous user's messages.
Future<void> unregisterPush() async {
  await CometChatNotifications.unregisterPushToken(onSuccess: (res) {}, onError: (e) {});
}
```
> `PushPlatforms` is an enum with per-platform Flutter variants — pick the one matching the running platform and the token type (`fcmToken` vs `deviceToken` vs `voipToken`). Do not pass an FCM token as a `deviceToken`.

## The token lifecycle (the part docs usually under-specify)
1. **Register AFTER `login` succeeds** — a token registered against no user goes nowhere.
2. **Re-register on token refresh.** FCM rotates tokens; listen to `onTokenRefresh` and re-register, or delivery silently stops days later.
3. **Unregister on logout**, before `CometChatUIKit.logout()` — otherwise the next user of that device receives the previous user's notifications. This is a privacy bug, not just a nuisance.
4. **Ask permission at the right moment** — iOS (and Android 13+) require a runtime prompt. Request it on a deliberate user action, not at first launch, or users decline permanently.

## Common pitfalls (BAKED)
- **No Dashboard provider** → the client is perfect and nothing is delivered. Check this FIRST when debugging.
- **Registering before login** → silence.
- **Never re-registering on refresh** → push works for days, then stops.
- **No unregister on logout** → the previous user's messages land on the device.
- **Testing on a simulator** → iOS simulators cannot receive push. Use a real device.
- **Expecting push while the app is foregrounded** — foreground messages arrive as data; you present them yourself.
- **Assuming the web/desktop story matches mobile** — verify before promising it.

## Verify it works
On a REAL device: permission granted → the token registers after login (no error) → background the app → a message from another user produces a notification → tapping it opens the app → logging out stops delivery to that device. Nothing arriving with a clean client almost always means the Dashboard provider or the platform credential (APNs key / `google-services.json`), not your Dart.
> Live delivery is a **manual device check** — it cannot be automated here. Say so honestly rather than claiming verification you did not do.
