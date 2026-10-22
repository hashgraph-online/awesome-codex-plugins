# Build-truth prerequisites — the evidence behind `SKILL.md` § Prerequisites (calls-sdk-android 5.0.4)

> Every floor and manifest line in `SKILL.md` was MEASURED on a real build/run (2026-09-07, emulator-5554, AGP 8.9.1,
> Gradle 8.11.1, Kotlin 2.1.20), not copied from the docs (`RULES.md` §2 build-truth). This file keeps the full error
> texts so a failing build is searchable; `SKILL.md` keeps the one-liners.

## minSdk 26 — the manifest merge decides (AUDIT-183 · DOCS-BACKLOG C11)
- `/calls/android/overview` says "Minimum SDK: API Level 24". A 24 app fails at `:app:processDebugMainManifest`:
  `uses-sdk:minSdkVersion 24 cannot be smaller than version 26 declared in library
  [com.facebook.react:react-native-svg:15.11.2-cometchat-21164567]` — pulled transitively by `calls-sdk-android:5.0.4`.
- Fix: `minSdk = 26` in `app/build.gradle(.kts)`. Verified: BUILD SUCCESSFUL, resolved `calls-sdk-android 5.0.4`,
  `react-android 0.77.2`, `soloader 0.12.1`.

## `<service>` for `CometChatOngoingCallService` — the AAR declares none (AUDIT-184 · DOCS-BACKLOG C12)
- The 5.0.4 AAR `AndroidManifest.xml` carries permissions only (`INTERNET`, `CAMERA`, `RECORD_AUDIO`,
  `MODIFY_AUDIO_SETTINGS`, `BLUETOOTH`, `FOREGROUND_SERVICE`, `FOREGROUND_SERVICE_MEDIA_PLAYBACK|MICROPHONE|CAMERA`,
  `POST_NOTIFICATIONS`). `/calls/android/background-handling` says "add the required permissions and service
  declaration" but its XML block has NO `<service>` element.
- Without it `CometChatOngoingCallService.launch(activity)` in `onSessionJoined` logs
  `ActivityManager: Unable to start service Intent { cmp=<app>/com.cometchat.calls.services.CometChatOngoingCallService } : not found`
  — no exception, no callback, no foreground service, no ongoing notification; the call is unprotected on Home.
- Fix (inside `<application>`):
  ```xml
  <service android:name="com.cometchat.calls.services.CometChatOngoingCallService"
      android:exported="false"
      android:foregroundServiceType="camera|microphone|mediaPlayback" />
  ```
  `foregroundServiceType` matches what the SDK passes to `startForeground(id, n, 194)` on API 34+
  (`javap`: `194 = camera|microphone|mediaPlayback`). Verified live: `dumpsys activity services` →
  `ServiceRecord{… CometChatOngoingCallService} isForeground=true types=0xC2` + the ongoing notification on channel
  `CometChat_Call_Ongoing_Conference` (category call, ONGOING|NO_CLEAR); ActivityManager "Background started FGS: Allowed".

## Jetifier for the ringing path (`chat-sdk-android`) (AUDIT-185)
- `chat-sdk-android:5.0.5 → android.arch.lifecycle:extensions:1.1.1 → com.android.support:support-compat/support-fragment
  26.1.0` (`./gradlew :app:dependencyInsight --dependency support-compat`). An AndroidX app then fails
  `checkDebugDuplicateClasses`: `Duplicate class android.support.v4.app.INotificationSideChannel … found in modules
  androidx.core:core:1.15.0 and com.android.support:support-compat:26.1.0` (×10).
- Fix: `gradle.properties` → `android.useAndroidX=true` + `android.enableJetifier=true` (or an `exclude` of
  `android.arch.lifecycle`). Verified: removing the line reproduces the failure; with it, chat-sdk 5.0.5 + calls-sdk 5.0.4
  build together. Meet-style (Calls SDK only) does not need it.

## SoLoader merged mapping (AUDIT-179 · DOCS-BACKLOG C10)
- The SDK's call surface is an embedded React Native 0.77.2 whose merged `libreactnative.so` resolves `hermes_executor`
  only through `SoLoader.init(ctx, OpenSourceMergedSoMapping)`; the published 5.0.4 classes never call it. First
  `joinSession` → `UnsatisfiedLinkError: dlopen failed: library "libhermes_executor.so" not found` (process dies).
- Fix: `SoLoader.init(this, OpenSourceMergedSoMapping)` first in `Application.onCreate()` with
  `com.facebook.react:react-android:0.77.2` + `com.facebook.soloader:soloader:0.12.1` on the compile classpath.

## How to re-measure on the next SDK bump
`./gradlew :app:processDebugMainManifest` at the claimed `minSdk` (floor) · unzip the AAR and read its
`AndroidManifest.xml` (undeclared components) · `dependencyInsight --dependency support-compat` (legacy transitives) ·
join a session, press Home, `dumpsys activity services` (the service is real) · two clients for peer-visible actions.

## Gradle heap `-Xmx4096m` — Jetifier OOMs the AS default (AUDIT-225)
- A brand-new project ships `org.gradle.jvmargs=-Xmx2048m`. Jetifier transforming the embedded
  `react-android:0.77.2` AAR (pulled by `calls-sdk-android` for the RN call surface) exceeds 2 GB →
  the FIRST `assembleDebug` fails: `Failed to transform react-android-0.77.2-debug.aar
  (com.facebook.react:react-android:0.77.2) … Execution failed for JetifyTransform … Java heap space`.
- Applies to the MEET-STYLE path too (the RN AAR is on the classpath regardless of ringing). This is
  NOT a docs bug — no docs page ships a from-scratch Gradle file — so the skill carries it.
- Fix: `org.gradle.jvmargs=-Xmx4096m` in `gradle.properties` (the pack's own harness uses this;
  `android.nonTransitiveRClass=true` also helps). Verified: `-Xmx2048m` reproduces the OOM,
  `-Xmx4096m` builds. compileSdk floor is 35 (androidx.core 1.15.0 fails `checkDebugAarMetadata` at 34, AUDIT-226).
