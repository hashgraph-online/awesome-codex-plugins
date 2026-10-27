# troubleshooting — symptom → cause → fix

The first stop when a Flutter integration renders wrong. Live page: `/ui-kit/flutter/troubleshooting`.

| Symptom | Likely cause | Fix |
|---|---|---|
| Blank/white screen where chat should be | A widget rendered before `login` succeeded | Gate the first frame on init **and** login (`lifecycle.md`) |
| `Unable to load asset: cometchat-settings.json` | File missing, not at project root, or not registered | Add it and list it under `flutter: assets:` in `pubspec.yaml`; re-run `flutter pub get` |
| Crash on `initFromSettings` before any UI | `WidgetsFlutterBinding.ensureInitialized()` missing | Call it first in `main()` |
| `RenderFlex children have non-zero flex but incoming height constraints are unbounded` | A kit list inside an unbounded parent | Wrap in `Expanded`, or give a fixed height (`layout.md`) |
| The list renders as a zero-height sliver | Same — content-driven parent | Same |
| Composer hidden by the keyboard | `resizeToAvoidBottomInset: false`, or a nested/absent `Scaffold` | Leave the default `true`; one `Scaffold` per screen |
| Header under the notch / composer under the home bar | No `SafeArea` | Wrap the body in `SafeArea` |
| `AUTH_ERR_AUTH_TOKEN_NOT_FOUND` / login fails immediately | Wrong **Region**, or the UID does not exist | Check `region` against the Dashboard; use a real UID from Dashboard → Users |
| Login fails only in release builds | Auth Key stripped/obfuscated, or no network permission | Verify the settings asset ships; check Android `INTERNET` permission |
| `Undefined name 'CometChatIncomingCall'` (or any call widget) | Imported only the chat barrel | Also import `package:cometchat_chat_uikit/cometchat_calls_uikit.dart` |
| Call buttons missing from the message header | Calls not enabled | `uiKit.enableCalling: true` in the settings file **and** `cometchat_calls_sdk` added (→ `-calls`) |
| Thread replies never appear / never send | `parentMessageId` passed without `user:`/`group:` | Pass BOTH on the thread list *and* composer |
| `The named parameter 'onBack' isn't defined` on the thread header | Following the docs page | It has no `onBack` — use the screen's `AppBar` (`DOCS-BACKLOG` F5) |
| `The named parameter 'onConversationItemClick' isn't defined` | Following the search docs page | `onConversationClicked` / `onMessageClicked` (`DOCS-BACKLOG` F3) |
| An enabled extension (polls/stickers) doesn't appear | Expecting v5-style registration | v6 auto-surfaces it; confirm the Dashboard toggle, add NO client code |
| Presence/online status never updates | `subscribePresenceForAllUsers` false in settings | Set it `true` (default) |
| Messages arrive only after reopening the screen | Socket not auto-connecting | `chatSDK.autoEstablishSocketConnection: true` |
| Android build fails on minSdk | App below the real floor (the docs' 24 is too low) | `minSdk = 26` in `android/app/build.gradle.kts` — forced by `cometchat_calls_sdk`, a hard dependency of the kit |
| iOS pod install fails | Deployment target too low (the docs' 13.0 is too low on 5.0.7) | `platform :ios, '15.1'` in `ios/Podfile`, then `pod install` |
| Everything breaks after upgrading from v5 | Mixed majors / removed v5 APIs | → `cometchat-flutter-v6-migration`; never mix majors |
