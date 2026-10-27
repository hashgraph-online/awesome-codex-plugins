<!-- family-agnostic: per-platform-by-design — this reference IS the per-family table; lint-skills GATE R
     requires one entry per shipped family, so naming a single family here is the point, not a defect. -->

# Platform specifics — what differs per platform

This gate is framework-agnostic, but several of its beats have a platform-specific answer. The
entry keeps the neutral rule; the concrete values live here. Load when you have detected the
platform. **Every family that ships a `-core` in `peers.yaml` has a column below** — a missing
column means beat 1 gets improvised (`lint-skills.mjs` checks this table against the shipped cores).

## Detection fields (beat 1) — web

| | Web (React) | Web (Angular) |
|---|---|---|
| project marker | `package.json` (`react`, no `react-native`/`expo`) | `package.json` (`@angular/core`) + `angular.json` |
| dependency manager | npm/pnpm/yarn (from the lockfile) | npm/pnpm/yarn (from the lockfile) |
| build/bundler | `bundler` · `router` · `ssr_strategy` | Angular CLI (`angular.json` builder); `router` = `@angular/router` |
| UI framework | React | Angular standalone components (kebab-case selectors) |
| version floor | `framework_version` | Angular 17–21 (the kit's range — `cometchat-angular-v5-core`) |
| language | TS / JS | TS |
| credentials file | `.env` (with the framework's env prefix) | `src/environments/environment.ts` (build-time file replacement — NOT `.env`) |
| existing integration | `@cometchat/chat-uikit-react` in `package.json` | `@cometchat/chat-uikit-angular` in `package.json` |

## Detection fields (beat 1) — mobile

| | iOS (Swift) | Android (Kotlin) | React Native | Flutter |
|---|---|---|---|---|
| project marker | `*.xcodeproj` / `*.xcworkspace` / `Package.swift` | `settings.gradle(.kts)` + `app/build.gradle(.kts)` | `package.json` with `react-native` (+ `expo` ⇒ Expo; `app.json`, `metro.config.js`) | `pubspec.yaml` (+ `pubspec.lock`) |
| dependency manager | **SPM**. A `Podfile` is a DETECTION signal only — CocoaPods distribution is winding down, so never integrate through it | Gradle (Kotlin DSL or Groovy; version catalog if `gradle/libs.versions.toml`) + the Cloudsmith Maven repo | npm/yarn (lockfile); Expo vs bare decides the `patterns` skill (`expo-patterns` / `bare-patterns`) | pub |
| build/bundler | not applicable — no bundler, no SSR, no routing story | not applicable — record `android_variant` instead (below) | Metro — no bundler/SSR choice | not applicable |
| UI framework | **UIKit or SwiftUI** — ask if ambiguous; the shipped kit is UIKit | **`android_variant`: `views` (XML Views → `kotlin-*` skills) or `compose` (Jetpack Compose → `compose-*` skills)** — read it from the compose plugin / `androidx.compose` deps; `mixed`/`unknown` ⇒ ask | React Native components | Flutter widgets |
| version floor | `deployment_target` (the kit's floor is iOS 15.1) | `minSdk` / `compileSdk` / Kotlin / AGP — **UI Kit v6: minSdk 28, compileSdk 36, Kotlin 2.1, AGP 8.9.1**; **headless Calls SDK v5: minSdk 26** (its TRUE transitive floor — the docs overview's 24 fails the manifest merge; `cometchat-android-v5-calls-sdk`). Read the app's `minSdk` in beat 1 and put the bump in the plan | React Native ≥ 0.77 | Flutter ≥ 3.19, Dart ≥ 3.10.1 |
| language | Swift | Kotlin (Java is the legacy cohort) | TS / JS | Dart |
| credentials file | `Config/Secrets.xcconfig` → `Info.plist` → `Bundle.main` | `app/src/main/assets/cometchat-settings.json` (**gitignored**; read by `initFromSettings` — chat, UI Kit AND calls share the ONE file); build-time extras via `local.properties` → `BuildConfig` | `.env` | `cometchat-settings.json` — a **registered asset** in `pubspec.yaml`, not a dotenv file |
| existing integration | `CometChatUIKitSwift` in `Package.swift` / `Podfile` | any `com.cometchat:` coordinate in `app/build.gradle(.kts)` — `chatuikit-*` (UI Kit v6), `chat-sdk-android` (headless chat), `calls-sdk-android` (headless calls) | `@cometchat/chat-uikit-react-native` in `package.json` | `cometchat_chat_uikit` in `pubspec.yaml` |

There is no `env_prefix` on iOS/Android/Flutter, and no lockfile-derived package manager on
iOS/Android — asking for either signals the gate was not really platform-aware.

## Follow-the-OS theming (beat 3)

Whether the kit follows the OS by itself DIFFERS per platform — do not assume the web answer:

- **Web (React):** it does NOT. There is no `theme="system"`, so the core syncs `theme` ↔ the
  `prefers-color-scheme` media query (AUDIT-004).
- **Web (Angular):** the kit's `initFromPreference()` respects `prefers-color-scheme` and keeps its own
  `matchMedia` listener — one call, no host observer (`cometchat-angular-v5-customization`).
- **iOS:** it DOES, with no host code at all. The kit's components override
  `traitCollectionDidChange` and its palette uses dynamic colours, so light/dark follows the device
  automatically. Do not offer to "wire up" OS theming on iOS, and do not port the web recipe —
  `prefers-color-scheme` does not exist outside a web view, and the observer is unnecessary anyway.
- **Android:** it DEPENDS on the cohort. **Views:** it DOES with no extra code — extend
  `CometChatTheme.DayNight` (AppCompat DayNight follows the system `uiMode`). **Compose:** it does NOT
  by itself — the host MUST wrap the kit UI in `CometChatTheme(colorScheme = if (isSystemInDarkTheme())
  darkColorScheme() else lightColorScheme()) { … }`; with no wrapper the kit renders its light defaults
  and ignores the OS setting (like the React Native "supply BOTH light and dark" case below, NOT the
  automatic iOS case). The core Compose golden path emits this wrapper when theming is "Auto — follow
  OS"; full theming API is `cometchat-android-v6-compose-customization`.
- **React Native:** supply BOTH `light` and `dark` to the provider; the kit then follows the OS scheme —
  setting only `light` is the classic bug (`cometchat-react-native-customization`).
- **Flutter:** Flutter's own `themeMode: ThemeMode.system` — nothing CometChat-specific (`cometchat-flutter-v6-customization`).

## The feature menu (beat 2)

The offered capabilities come from the DETECTED platform's manifest, and they are not the same
list:

- **Web (React):** `features.json` · **Web (Angular):** `features.angular-v5.json`
- **iOS:** `features.ios-v5.json`
- **Android:** `features.android-v6.json` (UI Kit) · `features.sdk-android-v5.json` (headless chat) ·
  `features.android-calls-v5.json` (headless calling-first — `calling-first.md`)
- **React Native:** `features.rn-v5.json`
- **Flutter:** `features.flutter-v6.json`

Never offer a feature the detected platform does not ship. On iOS in particular there is **no
composite chat component** — the host composes header + list + composer and owns the list ↔ detail
navigation, so "a chat screen" is a composition task, not a single drop-in. On Android the
headless calls family is receive-only for screen share and has no virtual background — do not offer either.

## Scope / placement (beat 4)

The placement vocabulary is platform-specific — offer only the shapes that exist on the detected
platform, never the web menu everywhere:

- **Web (React · Angular):** full-page · **embedded** in an existing route/section · a docked
  **sidebar / side-panel** · a **popup / floating widget**.
- **Mobile (iOS · Android · React Native · Flutter):** a **full-screen route** · a dedicated **tab** ·
  a **pushed navigation-stack screen** (list → detail) · a **modal / bottom-sheet** · **embedded** as a
  panel inside an existing screen. There is **no sidebar and no popup** on mobile — do not offer them.
  The concrete recipes live in `cometchat-<family>-placement` (iOS also: iPad split view; Android: the
  Activity/Fragment flow per `android_variant`).

Default to the SMALLEST reasonable production-ready surface, not the full combined app.

## SDK-fallback lookup

Per-feature fallback resolves through the DETECTED platform's core docs-map, never React's by
default:

> **Web (React):** `cometchat-react-v7-core/references/docs-map.md`
> **Web (Angular):** `cometchat-angular-v5-core/references/docs-map.md`
> **iOS:** `cometchat-ios-core/references/docs-map.md`
> **Android:** `cometchat-android-v6-core/references/docs-map.md` (UI Kit) · `cometchat-android-v5-sdk/references/docs-map.md` (headless chat) · `cometchat-android-v5-calls-sdk/references/docs-map.md` (headless calls)
> **React Native:** `cometchat-react-native-core/references/docs-map.md`
> **Flutter:** `cometchat-flutter-v6-core/references/docs-map.md`
