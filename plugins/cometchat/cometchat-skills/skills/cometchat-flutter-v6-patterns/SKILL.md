---
name: cometchat-flutter-v6-patterns
description: "Project wiring for the Flutter v6 UI Kit — navigation (Navigator / go_router / auto_route), state management (bloc / riverpod / provider / getx), config & secrets, platform setup, and web/desktop caveats. Triggers: 'cometchat with go_router', 'cometchat with riverpod', 'where do I put init in flutter', 'dart-define cometchat', 'cometchat flutter web'."
license: "MIT"
compatibility: "Flutter >=3.38.9; cometchat_chat_uikit ^6 (6.1.x, verified 6.1.0)"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat flutter patterns navigation state-management go-router riverpod config v6"
---

> **Ground truth:** the CometChat side is `cometchat-flutter-v6-core`; this skill only adds the DELTA for a given toolchain. Framework mechanics (go_router, riverpod, `--dart-define`) are baked Flutter knowledge, not kit API. Kit symbols come from the catalog.

## Companion skills (read first)
- `cometchat-flutter-v6-core` — install, credentials, the settings asset, `init→login→render`. This skill ASSUMES it.
- `cometchat-flutter-v6-placement` — WHERE the surface goes; this skill is HOW it hooks into your app's plumbing.

## Use this skill when
Wiring the kit into a specific project shape, or debugging "where does init go" / "the theme resets on navigation" / "my secrets are in git".

## Prerequisites & install
Covered by core. No new package.

## Navigation (BAKED — the delta per router)
The kit uses plain `Navigator.push`/`pop` internally and in every recipe, which works under **all** of these — you do not have to convert its recipes.

- **Plain `Navigator`** — nothing to do. Core's recipes are already this.
- **`go_router`** — register chat screens as routes and push with `context.push('/chat/:uid')`. The kit's own internal pops still work because go_router sits on the same `Navigator`. Put the **init/login gate above the router** (wrap `MaterialApp.router`'s builder, or gate in `redirect`) so no chat route can build before login resolves.
- **`auto_route`** — same principle: an `AutoRouteGuard` that waits for login is the idiomatic gate.
- **Calling adds one requirement**: `navigatorKey: CallNavigationContext.navigatorKey` on `MaterialApp` (→ `-calls`). With `go_router`, pass the same key into the router config rather than creating a second one.

## State management (BAKED)
The kit is **self-contained** — every widget drives its own BLoC internally. You do **not** wire the kit into your app's state layer, and you do not need `flutter_bloc` yourself.
- **bloc / cubit** — expose the logged-in user from your auth cubit; gate chat routes on it. Do not try to own the kit's internal blocs.
- **riverpod** — a `FutureProvider` that performs `initFromSettings` + `login` and which chat screens `.when(...)` on, is the cleanest gate.
- **provider / getx** — same shape: one async init future, everything chat-related below it.
- **Reading kit state** — `CometChatUIKit.loggedInUser` is the sync getter. For list state, use the widget's `stateCallBack` / `onLoad`, not a global store.

## Config & secrets (BAKED — Flutter-specific)
`initFromSettings` reads a **bundled asset**, so it cannot read `--dart-define`. Two honest options; state the trade-off and let the user choose:
1. **Keep `initFromSettings`** and generate `cometchat-settings.json` at build time from your existing secret source (CI writes the file). Keeps `integrationSource="ai-agent"` telemetry.
2. **Use the classic `UIKitSettingsBuilder` + `CometChatUIKit.init(...)`** with `--dart-define` values. Works, but loses telemetry attribution.
> Either way the Auth Key ends up in the app bundle and is **dev-only** — production means a server-minted auth token + `loginWithAuthToken` (core's `lifecycle.md`). Do NOT gitignore the registered `cometchat-settings.json` asset (a fresh clone / CI build then fails with *"No file or variants found for asset"*) — commit a **placeholder** version (no real Auth Key) that dev/CI overwrite, and guard the real key with a pre-commit/CI check.

## Platform setup (BAKED)
- **Android** — `minSdk = 26` in `android/app/build.gradle.kts` (the docs' 24 is too low); INTERNET permission; calling adds camera/mic.
- **iOS** — `platform :ios, '15.1'` in the Podfile, then `pod install`; photo/camera/mic usage strings for attachments and calls. Both floors come from `cometchat_calls_sdk`, which the kit depends on unconditionally — they apply whether or not you use calling (DOCS-BACKLOG D7).
- **Web** — the kit supports web, but plugin-backed features (media picker, calling) behave differently; verify anything you promise. `flutter run -d chrome` with the same settings asset.
- **Desktop** — not a documented target; if asked, say so honestly rather than guessing.

## Common pitfalls (BAKED)
- **Init inside a screen that can be re-entered** (or inside a route builder) → repeated init. Gate ONCE at the root (`lifecycle.md`).
- **A chat route reachable before login resolves** → blank screen. Guard the route, not just the widget.
- **Expecting `initFromSettings` to read `--dart-define`** — it reads an asset. See above.
- **Adding `flutter_bloc` to "connect" the kit** — unnecessary; the kit owns its blocs.
- **Two navigator keys** when calling is on — the router and `CallNavigationContext` must share one.
- **`cometchat-settings.json` committed** — the Auth Key is in your repo.
- **Forgetting `WidgetsFlutterBinding.ensureInitialized()`** before an asset-reading init.

## Verify it works
The app builds on each target platform you claim; chat routes are unreachable until login resolves; navigating away and back does not re-init; secrets are not in git; with calling on, an incoming call presents from any route.
