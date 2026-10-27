---
name: cometchat-flutter-v6-troubleshooting
description: "Diagnose a broken CometChat Flutter integration — blank screens, unbounded-height crashes, lists that don't fill, login and Region failures, calls that never ring, push that never arrives, and v5 leftovers. Symptom → cause → fix. Triggers: 'cometchat not working flutter', 'blank chat screen', 'RenderFlex unbounded height', 'login failed cometchat', 'calls not ringing', 'push not arriving'."
license: "MIT"
compatibility: "Flutter >=3.38.9; cometchat_chat_uikit ^6 (6.1.x, verified 6.1.0); cometchat_sdk ^5.0.6"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat flutter troubleshooting diagnostics errors symptoms v6"
---

> **Ground truth:** every cause below was confirmed against the published 6.1.0 (compiler or documented behaviour). The live page is `/ui-kit/flutter/troubleshooting` via `../cometchat-flutter-v6-core/references/docs-map.md`. The deeper per-topic tables live in core's `references/troubleshooting.md` and `references/anti-patterns.md` — this skill is the entry point that ROUTES to the right one.

## Companion skills (read first)
- `cometchat-flutter-v6-core` — install, credentials, `init→login→render`, plus the reference tables this skill routes into. This skill ASSUMES it.

## Use this skill when
Something is already built and is not working: a blank screen, a crash, an empty list, no ring, no notification.

## Prerequisites & install
None — diagnosis only.

## Triage in order (cheapest first)
1. **Does `flutter analyze` pass?** A stale v5 symbol or a wrong barrel import is a compile error, not a runtime mystery.
2. **Did `init` AND `login` both reach `onSuccess`?** Log both. Most "blank chat" reports stop here.
3. **Is the failing widget inside a bounded box?** The second-most-common cause, and it is always the host's container.
4. **Is the thing you expect actually enabled** — Dashboard toggle (extensions, moderation), `uiKit.enableCalling`, a push provider?
5. Only then look at the kit.

## Symptom → cause → fix
| Symptom | Cause | Fix |
|---|---|---|
| Blank/white chat screen | A widget built before `login` resolved | Gate the first frame on init **and** login (`lifecycle.md`) |
| `Unable to load asset: cometchat-settings.json` | Not at project root, or not registered | Add under `flutter: assets:`, re-run `flutter pub get` |
| Crash on startup before any UI | `WidgetsFlutterBinding.ensureInitialized()` missing | Call it first in `main()` — `initFromSettings` reads an asset |
| `RenderFlex … unbounded height` | A kit list in an unbounded parent | `Expanded`/`Flexible`, or a fixed height (`layout.md`) |
| List renders as a zero-height sliver | Same — content-driven parent | Same |
| Composer hidden by the keyboard | `resizeToAvoidBottomInset: false`, or nested `Scaffold`s | Leave the default `true`; one `Scaffold` per screen |
| Header under the notch | No `SafeArea` | Wrap the body |
| Two app bars | Your `Scaffold` `AppBar` + the widget's own | `hideAppbar: true` on the list widget |
| Login fails instantly | Wrong **Region**, or the UID doesn't exist | Match the Dashboard region exactly; use a real UID (Dashboard → Users) |
| Works in debug, fails in release | Obfuscation, or the settings asset not bundled | Test the release build; verify the asset ships |
| `Undefined name 'CometChatIncomingCall'` (any call widget) | Only the chat barrel imported | Also import `…/cometchat_calls_uikit.dart` (`-calls`) |
| Call buttons never appear | Calls not enabled on BOTH sides | `uiKit.enableCalling: true` **and** `cometchat_calls_sdk` installed |
| Call surface opens black | Camera/mic permission missing, or a simulator | Add usage strings/permissions; test on a real device |
| Incoming call never shows (calling on) | No `navigatorKey` on the root `MaterialApp` — kit logs *"Incoming call overlay cannot be shown"* | `navigatorKey: CallNavigationContext.navigatorKey` (`-calls`) |
| Two incoming-call screens | Own `CallListener` + `CometChatIncomingCall` on top of the kit's `CallEventService` overlay | Remove yours — the kit presents it; customize via `CallingConfiguration` |
| Thread replies never send | `parentMessageId` without `user:`/`group:` | Pass BOTH on the thread list *and* composer |
| Enabled extension doesn't appear | Expecting v5 registration | v6 auto-surfaces it; confirm the Dashboard toggle, add NO code |
| Push never arrives | No Dashboard provider, or registered before login | Configure the provider; register after login; re-register on refresh (`-push`) |
| Previous user still gets notifications | Push token never unregistered on logout | Unregister before `logout()` |
| Presence never updates | `subscribePresenceForAllUsers` false | Set it `true` in the settings file |
| Messages only arrive on reopen | Socket not auto-connecting | `chatSDK.autoEstablishSocketConnection: true` |
| Duplicate events after hot restart | Listener not removed in `dispose` | Pair every add with a remove (`-events`) |
| `The named parameter 'x' isn't defined` on a kit widget | Following a doc page that drifted | Trust the compiler; several Flutter pages had wrong signatures — check `DOCS-BACKLOG.md` PART 4 |
| Android build fails on minSdk | Below the floor (the docs' 24 is too low) | `minSdk = 26` — forced by `cometchat_calls_sdk`, a hard dependency of the kit |
| iOS pod install fails | Deployment target too low | `platform :ios, '15.1'` (13.0 through calls-sdk 5.0.6), then `pod install` |
| Everything broke after upgrading | Mixed majors / removed v5 APIs | → `cometchat-flutter-v6-migration`; never mix majors |

## When the docs and the compiler disagree, the compiler wins
Several `ui-kit/flutter` pages documented parameters that do not exist in 6.1.0 (thread header, search callbacks, style names). If a documented snippet will not compile, that is a **docs** bug: use the real signature, and flag the page (`RULES.md` §20) rather than working around it forever.

## Still stuck — collect this before escalating
Kit + SDK versions from `pubspec.lock` · the `flutter analyze` output · whether `init`/`login` reached `onSuccess` · the exact exception + stack · platform and whether it is a real device · the relevant Dashboard toggles. Most escalations are resolved by the first three.

## Verify it works
The specific symptom is gone, `flutter analyze` is clean, and the fix was to the HOST's wiring (gating, container, imports, config) — if the answer looked like "patch around the kit", re-check the table.
