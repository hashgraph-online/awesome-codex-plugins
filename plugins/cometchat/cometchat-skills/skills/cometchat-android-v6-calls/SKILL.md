---
name: cometchat-android-v6-calls
description: "Add voice and video calling to an Android v6 CometChat app — the Calls SDK dependency, the settings-file calling toggle, call buttons in the message header, a global incoming-call listener, outgoing/ongoing call UI, call logs, and the runtime permissions. Triggers: 'add calling to my android app', 'voice video call android cometchat', 'incoming call screen android', 'call logs android', 'why are the call buttons not showing'."
license: "MIT"
compatibility: "Android minSdk >=28; compileSdk >=36; Kotlin >=2.1; AGP >=8.9.1; JVM target 11; com.cometchat:chatuikit-kotlin-android ^6 OR com.cometchat:chatuikit-compose-android ^6 (6.0.x, verified 6.0.5); com.cometchat:calls-sdk-android ^5 (5.0.x); com.cometchat:chat-sdk-android ^5"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat android calls voice video v6 calling compose views"
---

> **Ground truth:** catalog `android-v6.json` + `features.android-v6.json` (`voice-video-calls`) + `contracts.android-v6.json` (`voice-video-calls`) + the live pages `calling-integration`, `call-features`, `components/{call-buttons,incoming-call,outgoing-call,call-logs}`, `guide-call-log-details`. Deep Calls-SDK behavior: the `/calls/android` docs tree. Verify symbols against the catalog; fetch params from docs; never trust memory.

## Companion skills (read first)
- `cometchat-android-v6-core` — install, credentials (`assets/cometchat-settings.json`), `initFromSettings → login → render`, sizing (`references/layout.md`), the fetch map. Assumed here, never repeated.
- `cometchat-android-v6-{kotlin,compose}-placement` — where the incoming-call surface sits in the app shell.

## Use this skill when
"add voice/video calling", "show call buttons in the chat", "handle incoming calls", "add a call history screen", "the call buttons aren't appearing", "call log details".

## Calls package + version
Add the Calls SDK **alongside** your cohort's UI Kit artifact (never instead of it):
```kotlin
dependencies {
    implementation("com.cometchat:chatuikit-compose-android:6.0.5")   // or chatuikit-kotlin-android for XML Views
    implementation("com.cometchat:calls-sdk-android:5.0.4")
}
```
> ⚠️ **REQUIRED whenever `android.enableJetifier=true` (which `core` mandates for the Chat SDK's
> pre-AndroidX transitive) — add a Jetifier ignore-list, or the build breaks the moment you add calling.**
> `calls-sdk-android` 5.0.x bundles a React-Native stack (`react-android` / `hermes` / `react-native-webrtc`),
> and Jetifier **cannot transform** `react-android-*.aar` — so with Jetifier on, the build dies at
> `checkDebugAarMetadata` with `Execution failed for JetifyTransform: react-android-0.77.2-debug.aar`
> (the app compiled fine BEFORE calling; adding the artifact breaks it — verified 2026-09-10). These
> AARs are already AndroidX, so exclude them from Jetifier in `gradle.properties`:
> ```properties
> android.jetifier.ignorelist=react-android,hermes-android,react-native-webrtc
> ```
⚠️ **The artifact and the flag are a PAIR — setting either alone breaks the app.**
> · flag `true`, artifact missing → **app crashes at launch** (`initFromSettings` → `initCometChatCalls` → `NoClassDefFoundError: CometChatCalls$SessionSettingsBuilder`)
> · artifact present, flag `false` → calling components crash when used (`RuntimeException: Please call the CometChatCalls.init() method …`)
>
> ⚠️ **BOTH are required — the artifact alone is not enough.** `uiKit.enableCalling: true` in
`assets/cometchat-settings.json` is what makes `initFromSettings` initialize `CometChatCalls`.
Without it, `CometChatCallLogs` throws `RuntimeException: Please call the CometChatCalls.init()
method …`; without the artifact it throws `NoClassDefFoundError`. Both compile fine — device-only
failures (verified 2026-08-21).

**The kit auto-detects the Calls SDK** and activates calling. Also set `"uiKit": { "enableCalling": true }` in `app/src/main/assets/cometchat-settings.json` so `CometChatUIKit.initFromSettings(...)` initializes the Calls SDK through the telemetry-aware path (it auto-inits Calls when that flag is on). Dashboard: calling must be enabled for the app.

**Header call buttons differ BY COHORT** (verified vs installed 6.0.5 source):
- **Views**: automatic — `CometChatMessageHeader`'s voice/video button visibility defaults follow `CallsUtils.isCallingEnabled()`, so the buttons render with no extra code once calling is enabled.
- **Compose**: NOT automatic — the `CometChatMessageHeader` composable defaults `hideVoiceCallButton = true` and `hideVideoCallButton = true`. Pass both explicitly:
  ```kotlin
  CometChatMessageHeader(user = user, hideVoiceCallButton = false, hideVideoCallButton = false)
  ```
  And do NOT use the header's `auxiliaryView` slot for other icons — it REPLACES the default auxiliary area that hosts the call buttons (they vanish). Extra header icons go in `trailingView` (see `cometchat-android-v6-compose-components`).

## Call-flow ordering (BAKED — invariant)
1. **Dependency + `enableCalling`** → call buttons appear in the message header (Views: nothing to wire; Compose: pass `hideVoiceCallButton = false, hideVideoCallButton = false` — see above).
2. **`initFromSettings` resolves → `login` resolves** (as always) — calling is unavailable before that.

> ⚠️ **Enabling calling in an app with EXISTING sessions — force a fresh login.** `CometChatUIKit.login()`
> short-circuits when the same uid is already logged in (persisted session): it returns `onSuccess`
> WITHOUT calling `loginCometChatCalls`, so the Calls SDK never gets an auth token (verified vs 6.0.5
> `CometChatUIKit.kt` login + on device 2026-08-25). Symptom: `CometChatCallLogs` shows a silent
> error state; logcat says `User auth token cannot be null`. When calling is FIRST enabled on an app
> whose users already have a session, users must re-login — `CometChatUIKit.logout(...)` then
> `CometChatUIKit.login(...)` (or force a fresh login path once, e.g. on a calling-feature version
> bump). During development, wire `onError` on `CometChatCallLogs` so this failure is not silent.
3. **Register a GLOBAL call listener** so an incoming call rings from anywhere in the app — the docs recommend an `Application` subclass, registering **before** the UI Kit is used:
```kotlin
import com.cometchat.chat.core.Call            // NOTE: chat.core, NOT chat.models
import com.cometchat.chat.core.CometChat

class BaseApplication : Application() {
    companion object {
        private val LISTENER_ID = "${BaseApplication::class.java.simpleName}${System.currentTimeMillis()}"
    }
    override fun onCreate() {
        super.onCreate()
        CometChat.addCallListener(LISTENER_ID, object : CometChat.CallListener() {
            override fun onIncomingCallReceived(call: Call) { /* show CometChatIncomingCall over the current screen */ }
            override fun onOutgoingCallAccepted(call: Call) { /* proceed to the ongoing-call surface */ }
            override fun onOutgoingCallRejected(call: Call) { /* dismiss the outgoing UI */ }
            override fun onIncomingCallCancelled(call: Call) { /* dismiss the incoming UI */ }
        })
    }
}
```
Register the Application class in the manifest (`android:name=".BaseApplication"`). **Views**: instantiate `CometChatIncomingCall(context)`, set its `call`, set `fitsSystemWindows = true`, wire its error handler, and present it (dialog / full-screen overlay). **Compose**: hold the incoming `Call` in app-level state and render the incoming-call composable above your nav host — fetch the composable's params from `components/incoming-call.md`.
4. **Permissions** — request `CAMERA` and `RECORD_AUDIO` at runtime before a call starts (video needs both; audio-only needs `RECORD_AUDIO`); declare them in the manifest. The kit ships `CometChatPermissionHandler` / `CometChatPermissionActivity` — prefer them over a hand-rolled flow.

> ℹ️ **SoLoader / bundled React-Native native libs (know this before an ACTIVE call).** `calls-sdk-android`
> 5.0.x bundles a React-Native stack (`react-android` / `hermes` / `react-native-webrtc`), declared at
> **`runtime` scope** in its POM — so they land on the runtime classpath and `initFromSettings` calls-init +
> `CometChatCallLogs` work with **no extra deps** (verified on device: init succeeds, call logs render).
> An **active** call surface loads those native `.so`s, which on RN ≥ 0.76 depend on `SoLoader`. If an
> active call fails to open with a `SoLoader`/`UnsatisfiedLinkError`/`NoClassDefFoundError` (React/JSI/
> Hermes symbols), add the RN + SoLoader artifacts on the **compile** classpath and init SoLoader once in
> `Application.onCreate` **before** the first call surface:
> ```kotlin
> // build.gradle.kts (only if an active call throws a SoLoader/native-link error)
> implementation("com.facebook.react:react-android:0.77.2")   // match what calls-sdk-android pulls
> implementation("com.facebook.soloader:soloader:0.12.1")
> // Application.onCreate: SoLoader.init(this, OpenSourceMergedSoMapping)
> ```
> Whether 5.0.x needs this for an active call is not yet settled from a single device — it is NOT needed for
> init or call logs. Verify with a real two-device call; treat this as the fix if (and only if) you hit that
> native-link error, not as an unconditional step.

## Calls component / API map (BAKED closed list)
`CometChatCallButtons` (auto-rendered in the message header; can also be placed standalone) · `CometChatIncomingCall` (ringing UI — accept/decline) · `CometChatOutgoingCall` (dialing UI) · `CometChatOngoingCall` + `CometChatOngoingCallActivity` / `CometChatCallActivity` (the in-call surface) · `CometChatCallLogs` (call history list) + `CometChatCallLogsListItem` · call bubbles in the message list: `CometChatCallActionBubble`, `CometChatMeetCallBubble` · `CometChatCallEvent` (call events → `cometchat-android-v6-events`). SDK-side (build-your-own flows): `CometChat.initiateCall` / `acceptCall` / `rejectCall` / `getActiveCall` / `clearActiveCall` / `addCallListener` / `removeCallListener` — see `core/references/docs-map.md` → SDK section.

The **minimum for "add calling"** (contract `voice-video-calls`): initiate (buttons) + incoming-call UI + outgoing-call UI + call logs. A call button with no incoming-call handler is a dead end — the callee never sees the ring.

```kotlin
// Minimum calls surface — four components for voice-video-calls contract
// CometChatCallButtons: auto-rendered in the message header; place standalone when needed
val callButtons = CometChatCallButtons(context)

// CometChatOutgoingCall: shown while the callee hasn't answered yet
val outgoingCall = CometChatOutgoingCall(context)
outgoingCall.call = pendingCall

// CometChatCallActivity / CometChatOngoingCallActivity: the in-call surface, launched
// automatically during a session. ⚠️ You do NOT declare these — BOTH are already declared in the
// UI-Kit AAR manifest and merge in automatically (verified vs 6.0.x). The cohort-correct classes:
//   Compose: com.cometchat.uikit.compose.calls.CometChatCallActivity
//            com.cometchat.uikit.compose.presentation.ongoingcall.ui.CometChatOngoingCallActivity
//   Views:   com.cometchat.uikit.kotlin.calls.CometChatCallActivity
//            com.cometchat.uikit.kotlin.presentation.ongoingcall.ui.CometChatOngoingCallActivity
// (There is NO `com.cometchat.chatuikit.calling.*` class in v6 — that's a v5/v4-era name; do not
// add a manual <activity> line for it or the merge/launch breaks.)

// CometChatCallLogs: call history tab
val callLogs = CometChatCallLogs(context)
```

## Deeper calling features → fetch
| Intent | Page (append `.md`) |
|---|---|
| calling overview / what's supported | `/ui-kit/android/call-features` |
| call buttons props | `/ui-kit/android/call-buttons` |
| incoming / outgoing UI props | `/ui-kit/android/incoming-call` · `/ui-kit/android/outgoing-call` |
| call logs + details recipe | `/ui-kit/android/call-logs` · `/ui-kit/android/guide-call-log-details` |
| custom in-call UI, layouts, recording, screen share, audio modes | the `/calls/android/*` pages (`call-layouts`, `custom-control-panel`, `audio-modes`, `background-handling`, `idle-timeout`, `events`, …) |

## Common pitfalls
Importing `com.cometchat.chat.models.Call` (it is **`com.cometchat.chat.core.Call`** — the wrong import compiles to an "Unresolved reference 'Call'" cascade) · manually declaring `CometChatCallActivity`/`CometChatOngoingCallActivity` in your manifest (they AUTO-MERGE from the UI-Kit AAR — a hand-written `<activity>` with the wrong/legacy `com.cometchat.chatuikit.calling.*` name breaks the launch) · Calls SDK missing (buttons never appear) · `enableCalling` not set in the settings file · Compose header without `hideVoiceCallButton = false` / `hideVideoCallButton = false` (buttons never appear — Compose defaults hide them) · Compose `auxiliaryView` used for a custom header icon (it replaces the call-button host — use `trailingView`) · calling enabled on an app with a persisted session without a re-login (Calls SDK tokenless — call logs silently error with "User auth token cannot be null") · no global call listener (incoming calls never ring) · listener registered per-Activity only (rings only on that screen) · registering in `Application` but forgetting `android:name` in the manifest · missing runtime CAMERA/RECORD_AUDIO permissions (call fails silently) · calling before `login` resolves · call UI not `fitsSystemWindows` / not full-bleed (controls under system bars) · leaking the listener (remove it if you register outside `Application`) · mixing a v4/v5 calls artifact with the v6 kit.

## Verify it works
Compile against the pinned kit (`./gradlew :app:assembleDebug   # in YOUR app (npm run verify:fences:android-v6 is a pack-repo gate)`). On device (TWO devices/emulators + two users — calling can't be verified single-ended): call buttons render in the message header; tapping starts an outgoing call; the OTHER device rings with the incoming UI from **any** screen; accept → ongoing call with audio/video; decline/cancel dismisses cleanly on both sides; the call appears in `CometChatCallLogs` and as a call bubble in the chat. No ring ⇒ listener not registered globally (or app not logged in). Permission denial ⇒ handle it and tell the user, don't fail silently.
