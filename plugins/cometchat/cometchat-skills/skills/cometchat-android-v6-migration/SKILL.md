---
name: cometchat-android-v6-migration
description: "Upgrade an Android app from the CometChat v5 UI Kit (Java, XML Views) to v6 (Kotlin — XML Views or Jetpack Compose): artifact and package changes, the CometChatThreadedMessagesHeader rename, LiveData→StateFlow, events→CometChatEvents SharedFlow, style objects→theme attributes/style data classes, and minSdk 28. Triggers: 'upgrade cometchat android v5 to v6', 'migrate android ui kit to v6', 'v6 import paths android', 'cometchat android breaking changes'."
license: "MIT"
compatibility: "FROM com.cometchat:chat-uikit-android 5.x (Java/XML Views, minSdk 24 — note the DIFFERENT artifact id; chatuikit-kotlin-android has no 5.x) TO 6.0.x — com.cometchat:chatuikit-kotlin-android (XML Views) or com.cometchat:chatuikit-compose-android (Compose) + chatuikit-core-android; Kotlin >=1.9 / AGP >=8; JVM 11; minSdk 28; compileSdk >=36; com.cometchat:chat-sdk-android ^5"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat android migration v5 v6 upgrade kotlin compose breaking-changes"
---

> **Ground truth:** the live page `/ui-kit/android/upgrading-from-v5` (the authoritative breaking-change map — every mapping below is quoted from it) + catalog `android-v6.json` (what exists AFTER the upgrade) + `COVERAGE.md` (the v5→v6 verdict table). Removed/renamed v5 names appear in PROSE only — never emit a v5 symbol in a code fence.


> ⚠️ **Before you touch code:** a v5→v6 upgrade hits two build blockers the moment the new artifact
> resolves. Set `android.useAndroidX=true` + `android.enableJetifier=true` in `gradle.properties`
> (the Chat SDK still pulls a pre-AndroidX transitive → `Duplicate class android.support.v4.*`) and
> keep `configurations.all { exclude(group = "org.jetbrains", module = "annotations-java5") }`.
> Floors also rise: **minSdk 28 · Kotlin 2.1 · AGP 8.9.1**.

## Companion skills (read first)
- `cometchat-android-v6-core` — the v6 install, credentials (`assets/cometchat-settings.json`), `initFromSettings → login → render`. The migration ENDS in core's golden path; this skill gets you there.
- After migrating: `cometchat-android-v6-{kotlin,compose}-customization` (styling moved), `cometchat-android-v6-events` (events moved).

## Use this skill when
"upgrade our Android UI Kit from v5 to v6", "we're on the Java UI Kit, move us to Kotlin/Compose", "what breaks in v6?", "fix these v5 imports". This is **reconciliation**, not onboarding — a `version_conflict` is expected here and resolving it IS the job.

## Prerequisites & install
Before touching code: confirm the current artifact + version, that the app builds, and **minSdk**. v6 requires **minSdk 28** (v5 allowed 24) — if the app targets lower, that's a product decision to raise it; surface it FIRST, it can block the whole migration.

## Breaking-change map (from the docs table)
| Area | V5 | V6 |
|---|---|---|
| Language | Java | Kotlin |
| Modules | single `com.cometchat:chat-uikit-android` (the v5 id — **not** `chatuikit-kotlin-android`, which only ever published 6.x) | `chatuikit-kotlin-android` (XML) **or** `chatuikit-compose-android` (Compose) + shared `chatuikit-core-android` |
| Import root | `com.cometchat.chatuikit.*` | `com.cometchat.uikit.kotlin.presentation.*` / `com.cometchat.uikit.compose.presentation.*` |
| `CometChatUIKit` | `com.cometchat.chatuikit.shared.cometchatuikit.CometChatUIKit` | `com.cometchat.uikit.core.CometChatUIKit` |
| `UIKitSettings` | `com.cometchat.chatuikit.shared.cometchatuikit.UIKitSettings` | `com.cometchat.uikit.core.UIKitSettings` |
| State | `LiveData` observers | `StateFlow` / coroutines |
| Architecture | View + ViewModel + Adapter (2 layers) | View → ViewModel → Repository → DataSource (4 layers) |
| Events | `CometChat*Events.addListener()/removeListener()` | `CometChatEvents` singleton, `SharedFlow` collected in a coroutine scope |
| Theming | `Palette` + `Typography` objects | XML attrs extending `CometChatTheme.DayNight`, or the `CometChatTheme {}` composable |
| Styling | `setStyle(ComponentStyle)` | XML `@StyleRes` theme attributes, or style data classes `.default().copy()` |
| ViewModel access | Java ViewModel + `LiveData` | Kotlin ViewModel + `StateFlow` (`getViewModel()`/`setViewModel()`) |
| List ops | adapter manipulation | `ListOperations<T>` (`addItem`, `removeItem`, `updateItem`, `moveItemToTop`, `batch {}`) |
| Repository | not exposed | swappable via factory (`*ViewModelFactory`) |
| minSdk | 24 | **28** |

**Component renames — only ONE**: `CometChatThreadedMessagesHeader` → **`CometChatThreadHeader`**. Everything else (`CometChatConversations`, `CometChatUsers`, `CometChatGroups`, `CometChatMessageHeader`, `CometChatMessageList`, `CometChatMessageComposer`, `CometChatIncomingCall`, `CometChatOutgoingCall`, `CometChatCallButtons`, `CometChatCallLogs`, `CometChatGroupMembers`) **keeps its name and only moves package**.

## Codemod / steps (in this order)
1. **Decide the cohort** — staying on XML Views (`chatuikit-kotlin-android`, smallest diff) or moving to Compose (`chatuikit-compose-android`, a UI rewrite of the chat screens). Ask; don't assume. Never ship both.
2. **Raise minSdk to 28** and confirm Kotlin/AGP/JVM 11 are in place.
3. **Swap the dependency** to the 6.x artifact for the chosen cohort (+ the CometChat Maven repo, `core` §Install). Remove the v5 artifact — grep the build file for **`com.cometchat:chat-uikit-android`** (that is the v5 id) — entirely — a leftover v5 dependency is the duplicate-class/`version_conflict` failure.
4. **Rewrite imports** (the bulk of the diff, mechanical):
   - `com.cometchat.chatuikit.shared.cometchatuikit.CometChatUIKit` → `com.cometchat.uikit.core.CometChatUIKit` (same for `UIKitSettings`).
   - `com.cometchat.chatuikit.<area>.<Component>` → `com.cometchat.uikit.kotlin.presentation.<area>.ui.<Component>` (XML Views) or `…uikit.compose.presentation.<area>.ui.<Component>` (Compose).
   - Grep targets: `com.cometchat.chatuikit.` (any hit is v5) and `CometChatThreadedMessagesHeader` (the one rename).
5. **Migrate init to v6** — the v6 default is `CometChatUIKit.initFromSettings(context, callback)` reading `app/src/main/assets/cometchat-settings.json`, then `login` in `onSuccess` (`core`). Move credentials out of source while you're here.
6. **Events** — replace every `addListener`/`removeListener` pair with a `CometChatEvents.<domain>Events.collect { }` in `lifecycleScope` (Views) or `LaunchedEffect` (Compose). No manual removal (→ `cometchat-android-v6-events`).
7. **State** — `LiveData.observe(...)` → collecting `StateFlow` in a lifecycle-aware scope.
8. **Styling/theming** — style objects → theme attributes (`themes.xml` extending `CometChatTheme.DayNight`) or Compose style data classes (→ `cometchat-android-v6-{kotlin,compose}-customization`).
9. **Compose only**: rebuild the chat screens as composables (`core`'s golden path / `cometchat-android-v6-{kotlin,compose}-placement` recipes) — XML layouts hosting kit views don't carry over.
10. **Build, then run** — fix per component using the docs page's "Component-by-Component Migration" section (fetch it: `/ui-kit/android/upgrading-from-v5.md`).

## Before → after patterns
```java
// V5 (Java) — imports + init
import com.cometchat.chatuikit.shared.cometchatuikit.CometChatUIKit;
import com.cometchat.chatuikit.conversations.CometChatConversations;
```
```kotlin
// V6 (Kotlin, XML Views cohort)
import com.cometchat.uikit.core.CometChatUIKit
import com.cometchat.uikit.kotlin.presentation.conversations.ui.CometChatConversations
```
```kotlin
// V6 events — the old addListener/removeListener pair becomes a scoped collect
lifecycleScope.launch {
    CometChatEvents.messageEvents.collect { event -> /* when (event) { … } */ }
}
```
> The thread header is the one rename to grep for; everything else is a package move. Full per-component diffs (Conversations, Users, Groups, Message Header/List/Composer): the docs page's component sections.

## Common pitfalls
Leaving the v5 artifact in the tree (duplicate classes) · mixing both v6 cohorts · missing the minSdk 28 bump · migrating imports but keeping `LiveData` observers · keeping `addListener`/`removeListener` for UI-Kit events (now flows) · missing the `CometChatThreadedMessagesHeader` → `CometChatThreadHeader` rename · carrying v5 style objects forward · keeping the classic `init(...)` instead of moving to `initFromSettings` · assuming Compose is a drop-in for XML screens · migrating code but leaving credentials hardcoded.

## Verify it works
Zero matches for `com.cometchat.chatuikit.` and `CometChatThreadedMessagesHeader` in the source; only ONE cometchat UI-Kit artifact resolves (`./gradlew :app:dependencies`); the fence gate compiles (`./gradlew :app:assembleDebug   # in YOUR app (npm run verify:fences:android-v6 is a pack-repo gate)`). On device: init + login succeed, conversations → messages works, threads/search round-trip, events fire once, theming still matches the brand, calls/push (if used) still work. Any capability that existed in v5 and has no v6 equivalent must be reported to the user, not silently dropped — see `COVERAGE.md`.
