---
name: cometchat-android-v6-troubleshooting
description: "Diagnose a broken CometChat Android v6 integration — dependency and version conflicts, init/login failures, blank or stuck screens, empty lists, missing realtime updates, keyboard/inset layout bugs, release-only crashes, permission and push problems — with a symptom → cause → fix path and what evidence to collect before escalating. Triggers: 'cometchat android not working', 'could not find com.cometchat', 'chat screen is blank android', 'messages not arriving in real time android', 'composer hidden by keyboard'."
license: "MIT"
compatibility: "Android minSdk >=28; compileSdk >=36; Kotlin >=2.1; AGP >=8.9.1; JVM target 11; com.cometchat:chatuikit-kotlin-android ^6 OR com.cometchat:chatuikit-compose-android ^6 (6.0.x, verified 6.0.5); com.cometchat:chat-sdk-android ^5"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat android troubleshooting v6 diagnostics errors debugging"
---

> **Ground truth:** catalog `android-v6.json` + the kit's real error codes (`ERR_SETTINGS_FILE_NOT_FOUND`, `ERR_SETTINGS_INVALID`, `CometChatException.code/message`) + the live page `/ui-kit/android/troubleshooting`. This skill goes DEEPER than `core/references/troubleshooting.md` (the quick table) — read that first for the common four; come here for the full path and for escalation.

## Companion skills (read first)
- `cometchat-android-v6-core` — install, credentials, `initFromSettings → login → render`, **`references/troubleshooting.md`** (the first-stop table), `references/anti-patterns.md`, `references/layout.md`. Assumed here, never repeated.

## Use this skill when
"it doesn't work", "the build fails", "the chat screen is blank/stuck", "messages don't arrive until I reopen", "the composer is under the keyboard", "it works in debug but crashes in release", "calls/push don't work" — and you need a systematic path, not a guess.

## Diagnostics entry — run these three, in order, before theorizing
1. **Does it BUILD?** `./gradlew :app:assembleDebug`. Dependency-resolution and duplicate-class failures are config, not code.
2. **What does LOGCAT say at startup?** Filter for `CometChat`. You are looking for exactly two things: init's `onSuccess`/`onError`, then login's `onSuccess`/`onError`. **Almost every "nothing works" report is one of these two failing and being swallowed** — if your callbacks don't log `e.code` + `e.message`, fix that first; an empty `onError {}` is the bug.
3. **What's the SESSION state?** `CometChatUIKit.getLoggedInUser()` — null after a "successful" login means login didn't actually complete.

## Symptom → root cause → fix
**Build / dependencies**
| Symptom | Cause | Fix |
|---|---|---|
| `Could not find com.cometchat:chatuikit-…` | CometChat Maven repo missing | add `maven("https://dl.cloudsmith.io/public/cometchat/cometchat/maven/")` to `settings.gradle(.kts)` `dependencyResolutionManagement.repositories` |
| **`sendMessage` returns `onSuccess` but the message NEVER arrives** (receiver connected, listener registered) | a Dashboard **moderation rule blocked it server-side** — the send genuinely succeeded, so no client error is raised. The UI Kit surfaces "Your message was blocked due to moderation policies"; a headless build sees nothing at all | Dashboard → **Moderation** → check rules/lists. Do NOT chase INTERNET permission or connection status — both are healthy in this case |
| `Duplicate class android.support.v4.*` (jetifier off) **or** `contains AndroidX dependencies, but the 'android.useAndroidX' property is not enabled` (useAndroidX off) — on a **clean, single-cohort** app | NOT a version conflict. `chat-sdk-android` pulls a pre-AndroidX transitive (`android.arch.lifecycle:extensions` → `com.android.support:support-compat:26.1.0`) that collides with `androidx.core` | set BOTH in `gradle.properties`: `android.useAndroidX=true` + `android.enableJetifier=true` (verified on a clean app; removing either reproduces it) |
| `Duplicate class org.jetbrains.annotations.*` at dexing | `io.noties:prism4j` pulls `annotations-java5:17` vs `annotations:23` | `configurations.all { exclude(group = "org.jetbrains", module = "annotations-java5") }` |
| **`Execution failed for JetifyTransform: react-android-*.aar`** at `checkDebugAarMetadata` — appears only AFTER adding **calling** | `calls-sdk-android` 5.0.x bundles a React-Native stack (`react-android`/`hermes`/`react-native-webrtc`) that Jetifier can't transform, and `core` mandates `android.enableJetifier=true` for the Chat SDK's pre-AndroidX transitive — so the two collide the moment calling is added | add to `gradle.properties`: `android.jetifier.ignorelist=react-android,hermes-android,react-native-webrtc` (they're already AndroidX). See `cometchat-android-v6-calls` |
| `requires Android Gradle plugin 8.9.1 or higher` | AGP floor is **8.9.1**, not 8.9 | bump AGP |
| `kotlin-stdlib … metadata is 2.2.0, expected 2.0.0` / internal compiler error | Kotlin floor is **2.1+**; 2.0.21 fails | bump Kotlin |
| Duplicate class / conflicting versions | **version_conflict**: a v4/v5 `chat-uikit-android` alongside v6 `chatuikit-*` | remove the old artifact — never mix majors; migrate via `cometchat-android-v6-migration` |
| Odd theme/duplicate UI, two kits resolve | both cohorts (`chatuikit-kotlin-android` AND `chatuikit-compose-android`) in one module | pick ONE cohort |
| `Unsupported class file major version` / Kotlin errors | JVM target mismatch | JVM 11: `compileOptions` + `kotlin { compilerOptions { jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_11) } }` (fully-qualified — a mid-file `import` breaks a `.kts`; the `kotlinOptions{}` DSL is deprecated/removed on Kotlin 2.2+) |

**Init / login**
| Symptom | Cause | Fix |
|---|---|---|
| `ERR_SETTINGS_FILE_NOT_FOUND` | no `app/src/main/assets/cometchat-settings.json` | create it (`core` §4); confirm it's in `assets/`, not `res/` |
| `ERR_SETTINGS_INVALID` | `appId` or `region` missing/empty in that JSON | fill both |
| init `onError` about app/auth | wrong **Region** (most common) or wrong App ID | match the Dashboard exactly (`us`/`eu`/`in`) |
| login `onError` ERR_UID_NOT_FOUND | the UID doesn't exist in this app | use a real user from Dashboard → Users (fresh apps seed `cometchat-uid-1…`), or create it server-side |
| login "fails silently" / nothing happens | **login called before init resolved** (docs warning) | call login only inside init's `onSuccess` |
| login error on an already-logged-in user | re-login without logout | guard with `getLoggedInUser() != null`; to switch users, `logout` first |
| Auth works debug, fails release | release build has no Auth Key but still uses `login(uid)` | use `loginWithAuthToken` (→ `cometchat-android-v6-production`) |

**Blank / empty / stuck UI**
| Symptom | Cause | Fix |
|---|---|---|
| Splash never advances | the gate never unlocks because an `onError` is swallowed | log + render errors; never leave `onError` empty |
| Chat screen blank/white | UI rendered before login resolved | gate the UI on login success |
| Component renders as a sliver / crammed | `wrap_content` or an unsized parent — the kit fills its parent | `match_parent`/`0dp`+weight (Views) or `fillMaxSize()`/`weight(1f)` (Compose) — `core/references/layout.md` |
| Conversation list empty | fresh app with no conversations, or wrong credentials/region | seed a conversation from another user or the Dashboard; re-check App ID/region |
| List scrolls oddly / doesn't load more | `CometChatMessageList` nested in another scrollable | never nest it in a ScrollView/`verticalScroll` Column |

**Realtime / features**
| Symptom | Cause | Fix |
|---|---|---|
| Messages only appear after reopening | listener not registered, or removed too early | register in the right lifecycle; remove only on teardown (`cometchat-android-v6-events`) |
| Nothing realtime at all | no internet permission, or connection down | `android.permission.INTERNET` in the manifest; check connection status (SDK `getConnectionStatus`/`addConnectionListener`) |
| A feature doesn't appear | Dashboard toggle off, or session started before enabling | enable in Dashboard for THIS app, then re-login (`cometchat-android-v6-extensions`) |
| Thread replies never send | thread list/composer missing the `user`/`group` target (parent id alone isn't enough) | pass BOTH the conversation target and the parent message id |
| Tapping an affordance does nothing | default-on affordance not wired (thread/search) | wire the destination or hide it |

**Layout / platform**
| Symptom | Cause | Fix |
|---|---|---|
| Composer hidden by the keyboard | no IME handling | `windowSoftInputMode="adjustResize"` (Views) / `imePadding()` (Compose) |
| Header/composer under the status or nav bar | edge-to-edge without insets | `enableEdgeToEdge()` + inset padding (`core/references/layout.md`) |
| Crash only in release | shrinking/obfuscation | reproduce on the release variant, read the real trace, then check docs before adding keep rules |
| Camera/mic fails on a call | runtime permissions not granted | request CAMERA/RECORD_AUDIO (`cometchat-android-v6-calls`) |
| Push never arrives | registration failed / no `onNewToken` / wrong Provider ID | `cometchat-android-v6-push` verify path |
| Crash: lifecycle-related on a kit view | host isn't a lifecycle-aware Activity | use `AppCompatActivity`/`ComponentActivity`/`FragmentActivity` |

## Escalating to CometChat support — bring this
Kit **cohort + exact version** (`chatuikit-compose-android` / `chatuikit-kotlin-android` 6.0.x) and `chat-sdk-android` version · App ID + **region** (never the Auth Key) · the **full `CometChatException`** (`code` AND `message`) from init/login/the failing call · a minimal repro (which component, which screen) · logcat around the failure · device/API level · whether it reproduces in debug and release. Confirm first that it isn't a version_conflict, a Region mismatch, or a swallowed `onError` — those three cover most reports.

## Common pitfalls (of debugging itself)
Empty `onError` blocks · assuming the kit is broken when the container is unsized · changing several things at once · testing against a Dashboard app you didn't verify · treating a debug-only symptom as release-safe (or vice versa) · asking support before capturing the exception code.

## Verify it works
After the fix: rebuild, watch logcat for init `onSuccess` → login `onSuccess`, and re-run the original repro. Then re-check the surrounding invariants — surface fills its parent, keyboard/insets fine, thread and search round-trip, realtime arrives without reopening, and (if touched) the release variant still runs. Confirm the fix's cause was the one you claimed; if you changed several things, revert the unnecessary ones.
