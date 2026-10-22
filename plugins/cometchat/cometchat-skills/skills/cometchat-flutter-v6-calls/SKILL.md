---
name: cometchat-flutter-v6-calls
description: "Add voice & video calling to a Flutter app with the CometChat v6 UI Kit — turn calling on in settings, wire the native config and the root navigatorKey (the kit presents incoming/outgoing call screens itself), and add call-log surfaces. Triggers: 'add voice and video calls in flutter', 'add calling to my flutter chat', 'enable video call flutter', 'add call buttons flutter', 'show call logs flutter'."
license: "MIT"
compatibility: "Flutter >=3.38.9; cometchat_chat_uikit ^6 (6.1.x, verified 6.1.0); cometchat_calls_sdk ^5 (5.0.x — separate package)"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat flutter calls voice video calling webrtc v6"
---

> **Ground truth:** the call UI ships INSIDE `cometchat_chat_uikit`, but in a **second barrel**, and the WebRTC engine is a separate package (`cometchat_calls_sdk`). Every symbol below is catalog-verified against 6.1.0. Exhaustive props: FETCH the twin via `../cometchat-flutter-v6-core/references/docs-map.md` (`call-features` · `incoming-call` · `outgoing-call` · `call-logs` · `call-buttons`). **APPEND to the user's app — additive wiring only.**

## Companion skills (read first)
- `cometchat-flutter-v6-core` — install, credentials, the settings asset, `init→login→render`. This skill ASSUMES it (calling rides the SAME init).
- `cometchat-flutter-v6-components` — the widget catalog.
- `cometchat-flutter-v6-placement` — where call surfaces sit in the app shell (incoming calls need only the root `navigatorKey` — no widget).

## Use this skill when
"add voice & video calls", "enable video call", "add call buttons", "show call logs". Precondition: chat already works (core done).

## Prerequisites & install
`cometchat_chat_uikit` **already depends on `cometchat_calls_sdk`** (`^5.0.4`, in the kit's own `dependencies:` — verified in the 6.1.x pubspec), so the WebRTC engine is pulled in transitively; you do **not** need to add it. Add an explicit direct dependency **only** if you import `cometchat_calls_sdk` symbols directly (then pin it to keep resolution predictable):
```bash
flutter pub add cometchat_calls_sdk   # optional — only if you import the package directly
```
Then the native config the docs require — **all four steps, or calling silently never rings**:
1. `cometchat_calls_sdk` (transitive via the kit; pin `^5.0.4` in `pubspec.yaml` only if you added it directly).
2. **Android** `android/app/build.gradle.kts`: `minSdk = 26`.
3. **iOS** `ios/Podfile`: `platform :ios, '15.1'`, then `pod install`.
4. **Permissions** — camera + microphone (`AndroidManifest.xml`; `NSCameraUsageDescription` / `NSMicrophoneUsageDescription` in `Info.plist`). Without them the call surface opens black.
> **⚠️ The docs' floors are too low and these are compiler-verified instead.** `cometchat_calls_sdk`
> pins `minSdkVersion 26` in its `android/build.gradle` and `platform :ios, '15.1'` in its podspec
> (5.0.7; it was 13.0 through 5.0.6). Gradle and CocoaPods take the MAXIMUM across the dependency
> graph, so a lower app-level value is a build error, not a warning. Docs say 24 / 13.0 —
> DOCS-BACKLOG D7. Platform floors do move: re-verify against the installed package, not the page.

## THE BARREL TRAP (read before writing a line)
Every call widget resolves **only** from the calls barrel, and that barrel does **not** re-export the chat widgets. A calls screen imports **both**:
```dart
import 'package:cometchat_chat_uikit/cometchat_chat_uikit.dart';        // chat widgets + SDK types
import 'package:cometchat_chat_uikit/cometchat_calls_uikit.dart';       // ALL call widgets
```
Importing only the chat barrel and then emitting `CometChatIncomingCall` fails to compile with *"Undefined name"* — the single most common calls mistake.

## Enable calling (BAKED — the #1 gotcha: TWO things must be true)
Calling is off until **(a)** the Calls SDK is installed **and (b)** calling is enabled in settings. Core inits via `initFromSettings`, which reads `cometchat-settings.json` — so flip it **in the file**:
```json
{
  "appId": "APP_ID",
  "region": "REGION",
  "credentials": { "authKey": "AUTH_KEY" },
  "uiKit": { "subscribePresenceForAllUsers": true, "enableCalling": true },
  "chatSDK": { "autoEstablishSocketConnection": true }
}
```
> `uiKit.enableCalling` is the **only** way to enable calling on the `initFromSettings` path — `UIKitSettings` defaults it to false. (If the project uses the classic builder instead, the equivalent is `..enableCalls = true` plus `..callingConfiguration = CallingConfiguration()`.)

## Wire it (BAKED)
**1. A navigator key at the app root** so the kit can present call screens from anywhere:
```dart
import 'package:cometchat_chat_uikit/cometchat_calls_uikit.dart';
import 'package:flutter/material.dart';

Widget app(Widget home) => MaterialApp(
      navigatorKey: CallNavigationContext.navigatorKey,   // REQUIRED for call routing
      home: home,
    );
```

**2. That's it for incoming calls — the kit does the rest.** Do **NOT** add your own root `CallListener` or present `CometChatIncomingCall` yourself. When `uiKit.enableCalling` is true, the kit's `CallEventService` registers its **own** `CometChat.addCallListener(...)` on login and shows the incoming-call overlay automatically via `IncomingCallOverlay` (verified in `cometchat_chat_uikit` 6.1.x). Adding a second listener + a manual overlay produces a **DOUBLE** incoming-call screen. All you owe it is the `navigatorKey` from step 1 (that is how the overlay finds a context to present — without it the kit logs *"Incoming call overlay cannot be shown"*).

**To customize the incoming/outgoing/call-button surfaces, pass a `CallingConfiguration`** — not a hand-rolled listener. On the classic builder path: `..callingConfiguration = CallingConfiguration(incomingCallConfiguration: ..., outgoingCallConfiguration: ..., callButtonsConfiguration: ...)`. `CallingConfiguration` (with `incomingCallConfiguration` / `outgoingCallConfiguration` / `callButtonsConfiguration`) is the kit's supported entry point; fetch its fields via the twin (`call-features`).

**3. Extra surfaces you place yourself** — call logs, and the incoming/outgoing widgets only when you build a fully custom flow — from the CALLS barrel:
```dart
import 'package:cometchat_chat_uikit/cometchat_calls_uikit.dart';
import 'package:flutter/material.dart';

Widget logs() => const CometChatCallLogs();
// Only when replacing the built-in overlay with a fully custom flow — otherwise the kit
// already presents these for you:
Widget incoming(Call call, User user) => CometChatIncomingCall(call: call, user: user);
Widget outgoing(Call call, User user) => CometChatOutgoingCall(call: call, user: user);
```
> **Call buttons are already in `CometChatMessageHeader`** — do NOT hand-roll them. They appear once calling is enabled; hide with `hideVoiceCallButton` / `hideVideoCallButton`. `CometChatCallButtons` is for placing them somewhere else (e.g. a profile screen).

## Common pitfalls (BAKED — the ones that actually bite)
- **Enabled in only one place** — SDK installed but `enableCalling` false (or vice-versa) ⇒ every call affordance stays hidden, with no error.
- **Missing camera/mic permissions** ⇒ the call surface opens black. Test on a real device; simulators have no camera.
- **Adding your own root `CallListener` + `CometChatIncomingCall`** ⇒ a DOUBLE incoming-call screen. The kit's `CallEventService` already listens and shows the overlay when calling is enabled — don't duplicate it; customize via `CallingConfiguration`.
- **No `navigatorKey`** (`CallNavigationContext.navigatorKey` on your `MaterialApp`) ⇒ the kit's overlay has no context to present from and logs *"Incoming call overlay cannot be shown"*.
- **A call surface with no bounded height** ⇒ zero-dimension video (`../cometchat-flutter-v6-core/references/layout.md`).
- **Group calls do not ring** the way 1:1 does — group calling is join-based. Verify the behaviour you promise against `call-features`.
- **Details screens are host-composed** — there is no `CometChatCallLogDetails` widget; build it from `guide-call-log-details`.

## Verify it works
On TWO real devices (not simulators): calling enabled in the settings file and the Calls SDK installed → the header shows call buttons → placing a call rings the other device → accept shows the ongoing surface with real video → decline/end returns both sides cleanly → the call appears in `CometChatCallLogs`. A black surface means permissions; no ring means the enable pair or a missing `navigatorKey`; two incoming screens means a hand-added listener/`CometChatIncomingCall`.
> Build the feature; do not write tests unless asked (`RULES.md`) — the above is an advisory human pass.

**Close (after it builds):** end with the shared 3-option selectable menu and WAIT — **① add another feature · ② customize theming · ③ test it manually** (same contract as core, `RULES.md` §19).
