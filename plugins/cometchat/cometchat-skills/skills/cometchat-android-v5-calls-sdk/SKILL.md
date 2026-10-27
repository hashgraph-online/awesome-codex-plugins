---
name: cometchat-android-v5-calls-sdk
description: "Add voice & video calling to any Android app FROM SCRATCH with the headless CometChat Calls SDK v5 (`com.cometchat:calls-sdk-android:5.0.4`) — no UI Kit. Kotlin: initFromSettings→login→generateToken→joinSession into a RelativeLayout, lifecycle-bound listeners, meet-style session rooms AND 1:1 ringing (Chat SDK v5 signaling + Calls SDK media), call logs, layouts, audio modes, recording, PiP, background service. Triggers: 'add calling from scratch android', 'standalone video call kotlin', 'headless calls sdk android', 'build my own call UI android', 'meeting room join by session id android', 'one-on-one ringing call without uikit android'."
license: "MIT"
compatibility: "Android minSdk >=26 (TRUE transitive floor of calls-sdk-android 5.0.x — react-native-svg declares 26; docs now agree); compileSdk >=35 (androidx.core 1.15.0 fails checkDebugAarMetadata at 34; match your androidx); Kotlin >=1.9 / AGP >=8; JVM target 11; com.cometchat:calls-sdk-android ^5 (5.0.x, verified 5.0.4). 1:1 ringing also needs com.cometchat:chat-sdk-android ^5 (5.0.5) for signaling. Kotlin (XML Views or Compose host via AndroidView)."
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat calls sdk v5 headless voice video android kotlin calling standalone"
---

> **Ground truth:** `com.cometchat:calls-sdk-android:5.0.4` + catalog `android-calls-v5.json` (the CLOSED list, `javap`-verified on the installed AAR). Docs: `/calls/android/**` = **v5** · Docs MCP. Fetch builder options, callback lists and filters from the docs (`references/docs-map.md`) — never memory. ⚠️ Where docs and AAR disagree, **the AAR wins** (drift list in `references/pitfalls.md`). **APPEND to the user's app — additive wiring only** (`RULES.md`). HEADLESS path (no UI Kit); for the prebuilt call UI use `cometchat-android-v6-calls`.

## Companion skills (read first)
- **Standalone/headless entry** — owns its own artifact (the Calls SDK), no `-core` sibling.
- **1:1 RINGING only** also drives the **Chat SDK** (`com.cometchat:chat-sdk-android:5.0.5`) for signaling — `references/ringing.md`; deeper Chat-SDK usage: `cometchat-android-v5-sdk`.
- **Prefer the UI Kit?** Chat + a prebuilt call UI ⇒ `cometchat-android-v6-core` + `cometchat-android-v6-calls`, not this skill.

## Use this skill when
"add calling from scratch / without the UI Kit", "standalone voice/video on Android", "build my own call screen", "headless calls SDK", "meeting room join by session id", "one-on-one ringing call". Precondition: the caller chose the **from-scratch / standalone** path (prebuilt call UI ⇒ see Companion skills).

## Prerequisites & install
```kotlin
// settings.gradle(.kts) → dependencyResolutionManagement.repositories
maven("https://dl.cloudsmith.io/public/cometchat/cometchat/maven/")
// app/build.gradle.kts
implementation("com.cometchat:calls-sdk-android:5.0.4")    // meet-style needs ONLY this (+ the two RN lines below)
implementation("com.cometchat:chat-sdk-android:5.0.5")     // + this for 1:1 RINGING (signaling)
implementation("com.facebook.react:react-android:0.77.2")  // the SDK's embedded RN runtime — see "SoLoader" below
implementation("com.facebook.soloader:soloader:0.12.1")    // (versions = what calls-sdk-android 5.0.4 pulls)
```
```properties
# gradle.properties — REQUIRED for the 1:1 RINGING path (chat-sdk-android 5.0.5 still pulls android.arch.lifecycle:extensions:1.1.1 → support-compat 26.1.0)
android.useAndroidX=true
android.enableJetifier=true
org.gradle.jvmargs=-Xmx4096m   # REQUIRED: Jetifier transforms the embedded react-android AAR — the AS-default -Xmx2048m OOMs (AUDIT-225)
```
```xml
<!-- AndroidManifest.xml, inside <application> — REQUIRED for background handling: the AAR declares NO <service> -->
<service android:name="com.cometchat.calls.services.CometChatOngoingCallService"
    android:exported="false"
    android:foregroundServiceType="camera|microphone|mediaPlayback" />
```
> Full error-text evidence for the four build gates below (minSdk, `<service>`, Jetifier, heap): **`references/build-truth.md`.**
- **minSdk 26 — the manifest merge is the floor.** `calls-sdk-android:5.0.4` pulls `react-native-svg` at `minSdkVersion 26`; a 24/25 app fails `process*MainManifest`. Docs now agree (AUDIT-229) — raise `minSdk` first.
- **The `<service>` above is REQUIRED.** The 5.0.4 AAR merges permissions only; without YOUR declaration `CometChatOngoingCallService.launch(activity)` fails **silently** (call dies on Home). Docs ship the `<service>` block (corrected upstream, verified 2026-09-09).
- **Jetifier (ringing only).** Without `android.enableJetifier=true`, an AndroidX app + `chat-sdk-android` fails `checkDebugDuplicateClasses`. Meet-style needs none.
- **⚠️ Gradle heap `-Xmx4096m` (MANDATORY — the FIRST build OOMs, meet-style too, AUDIT-225).** The AS-default `-Xmx2048m` OOMs Jetifier transforming the embedded `react-android` AAR; the `gradle.properties` line above fixes it.
- **⚠️ SoLoader (MANDATORY on 5.0.x; a REQUIRED skill step — the SDK doesn't self-init on the `joinSession` path).** The call surface is an embedded React Native 0.77; without the merged-mapping init `joinSession` **crashes the process** (`UnsatisfiedLinkError: … "libhermes_executor.so" not found`). Add ONCE, first in `Application.onCreate()` (hence the two RN artifacts on YOUR compile classpath):
  ```kotlin
  import com.cometchat.calls.core.CometChatCalls
  import com.facebook.react.soloader.OpenSourceMergedSoMapping
  import com.facebook.soloader.SoLoader

  SoLoader.init(this, OpenSourceMergedSoMapping)   // Application.onCreate(), BEFORE CometChatCalls.initFromSettings — idempotent
  ```
- **Manifest:** the AAR merges the call permissions (INTERNET, CAMERA, RECORD_AUDIO, FOREGROUND_SERVICE_*, POST_NOTIFICATIONS, …) — but NOT the `<service>` above. Java 11 `compileOptions`.
- **Runtime permissions are YOURS to request** (API 23+): `CAMERA` + `RECORD_AUDIO` (video) / `RECORD_AUDIO` (voice) **before** `joinSession`. Denied ⇒ tell the user; never join silently muted.
- **Credentials:** App ID · Region · Auth Key (dev only) live in the **gitignored** `app/src/main/assets/cometchat-settings.json` (same file the chat core uses; shape → `references/docs-map.md` § DOCS-GAP). Fetch via the CLI — `npx @cometchat/skills-cli@3 auth login` → `provision use --app-id <id> --json` (`@3` pins the CLI major that matches the v5 skills) — or paste from Dashboard → Credentials. Mint **auth tokens server-side** for production; never ship the Auth Key.

## Init & login ordering (BAKED — invariant)
`CometChatCalls.initFromSettings(context, listener)` resolves (`onSuccess`) → `CometChatCalls.login(uid, authKey, …)` (dev) **or** `login(authToken, …)` (prod) resolves → then `generateToken` / `joinSession` / listeners. Nothing joins before init+login resolve; before init every call fails with `ERROR_COMETCHAT_CALLS_SDK_INIT`.
- **DEFAULT to `initFromSettings`** — the ai-agent/telemetry-attributed path (`integrationSource="ai-agent"`, parallel to `CometChat.initFromSettings`; RULES §5, AUDIT-175). It reads `assets/cometchat-settings.json` (`appId`, `region`, optional `callsSDK` hosts). **Intentionally undocumented** (`@nodoc`); the documented `CometChatCalls.init(context, CallAppSettings.CallAppSettingBuilder(...).build(), listener)` is the FALLBACK only.
- **`authKey`** is read back out of the same asset (`credentials.authKey`) — never a second copy. Skip `login` only when `getLoggedInUser()?.uid == uid` — a DIFFERENT uid ⇒ **logout → RE-INIT → login** (`references/user-switch.md`); `!= null` alone calls as the PREVIOUS user. Init ONCE, in `Application.onCreate()`.
```kotlin
import com.cometchat.calls.core.CometChatCalls
import com.cometchat.calls.exceptions.CometChatException
import com.cometchat.calls.model.CallUser
import org.json.JSONObject

// Call from Application.onCreate(); it re-enters itself after a user-switch logout.
fun initThenLogin(uid: String) {
    CometChatCalls.initFromSettings(this, object : CometChatCalls.CallbackListener<String>() {   // telemetry default; init(context, CallAppSettings, …) is the doc fallback
        override fun onSuccess(result: String) {
            val current = CometChatCalls.getLoggedInUser()
            if (current?.uid == uid) return                                    // SAME user — already logged in
            if (current != null) {                                             // DIFFERENT user — NOT `!= null` → login (that calls as the PREVIOUS user)
                CometChatCalls.logout(object : CometChatCalls.CallbackListener<String>() {
                    // logout leaves isInitialized()==false → RE-INIT before login (ringing: CometChat.logout too — references/user-switch.md)
                    override fun onSuccess(msg: String) = initThenLogin(uid)
                    override fun onError(e: CometChatException) { /* surface e.code — never continue as the old user */ }
                })
                return
            }
            // dev: login(uid, authKey, l) — authKey from the SAME asset; prod: login(authToken, l), token minted server-side.
            val authKey = JSONObject(assets.open("cometchat-settings.json").bufferedReader().readText())
                .getJSONObject("credentials").getString("authKey")
            CometChatCalls.login(uid, authKey, object : CometChatCalls.CallbackListener<CallUser>() {
                override fun onSuccess(callUser: CallUser) { /* unlock calling */ }
                override fun onError(e: CometChatException) { /* surface e.code + e.message */ }
            })
        }
        override fun onError(e: CometChatException) { /* ERROR_SETTINGS_FILE_NOT_FOUND ⇒ the asset is missing */ }
    })
}
initThenLogin(uid)
```

## Two build modes (BAKED — the router picks one)
- **Meet-style (session room)** — Calls SDK ONLY: `generateToken(sessionId)` → `joinSession(token, sessionSettings, relativeLayout, …)` (or the `joinSession(sessionId, …)` overload); everyone on the same `sessionId` shares the call. No ringing.
- **1:1 ringing** — Chat SDK signals, Calls SDK carries media (§ 1:1 ringing below — FOREGROUND-only without VoIP push).

## SDK method map (BAKED closed list — from the catalog; signatures → FETCH from docs)
- **Lifecycle (`CometChatCalls` statics):** `initFromSettings` · `init` · `isInitialized` · `login(uid, authKey, l)` / `login(authToken, l)` · `logout` · `getLoggedInUser` · `getUserAuthToken`
- **Session:** `generateToken(sessionId, l)` → `GenerateToken.token` · `joinSession(token | sessionId, SessionSettings, RelativeLayout, l)` → `CallSession` (`startSession`/`CallSettingsBuilder` = **v4 path, do not use**) · builder `CometChatCalls.SessionSettingsBuilder()` (`setSessionType`/`setLayout`/`setAudioMode`/…, full list in the reference).
- **Active call (`CallSession.getInstance()`):** `isSessionActive` · `leaveSession` · lifecycle-bound listeners (`addSessionStatusListener(owner, …)` + siblings) · `clearAllListeners`.
- **Also (full enumeration → `references/method-map.md`):** In-call actions (CUSTOM controls only) · Call logs (`CallLogRequest`) · Transcription & closed captions (v5.0.4+, plan-gated) · Background (`CometChatOngoingCallService`) · Constants/enums (`SessionType`/`LayoutType`/`AudioMode`/`CometChatCallsConstants.*`).
> A **curated highlight, NOT the full surface** — the AUTHORITATIVE closed list is the **`android-calls-v5.json` catalog** (also transcription/streaming, `CometChatCallsEventsListener`, the v4-era `CallSettingsBuilder`). A symbol is real **iff it's in the catalog**; then fetch its page via `references/docs-map.md`. **Full method map: `references/method-map.md`.**

## Listener lifecycle (BAKED)
Every `CallSession` listener takes a **`LifecycleOwner`** and is removed with it — register from `joinSession`'s `onSuccess` with the Activity/Fragment as owner; no manual remove (`clearAllListeners()` for hard resets). Still yours by hand: `CallSession.getInstance().leaveSession()` on teardown, and for ringing `CometChat.removeCallListener(ID)`.

## Least-code recipe (meet-style, Kotlin Activity)
```kotlin
import android.Manifest
import android.os.Bundle
import android.view.ViewGroup
import android.widget.RelativeLayout
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import com.cometchat.calls.core.CallSession
import com.cometchat.calls.core.CometChatCalls
import com.cometchat.calls.exceptions.CometChatException
import com.cometchat.calls.listeners.SessionStatusListener
import com.cometchat.calls.model.GenerateToken
import com.cometchat.calls.model.LayoutType
import com.cometchat.calls.model.SessionType

class MeetCallActivity : AppCompatActivity() {           // init + login already resolved (Application)
    private lateinit var callContainer: RelativeLayout
    private val permissions = registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { granted ->
        if (granted.values.all { it }) joinRoom(intent.getStringExtra("SESSION_ID") ?: "team-room")
        else finish()                                     // tell the user — a call without mic/camera cannot start
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // The SDK renders its ENTIRE call UI into this view — a RelativeLayout with REAL size. No external controls.
        callContainer = RelativeLayout(this).apply {
            layoutParams = ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT)
        }
        setContentView(callContainer)
        permissions.launch(arrayOf(Manifest.permission.CAMERA, Manifest.permission.RECORD_AUDIO))
    }

    private fun joinRoom(sessionId: String) {
        val sessionSettings = CometChatCalls.SessionSettingsBuilder()      // fetch more options from /calls/android/session-settings
            .setSessionType(SessionType.VIDEO)                              // ⚠️ setSessionType — the docs' setType() does not exist here
            .setLayout(LayoutType.TILE)
            .setDisplayName("Me")
            .setIdleTimeoutPeriod(120)                                      // alone for 2 min ⇒ onSessionTimedOut
            .build()
        CometChatCalls.generateToken(sessionId, object : CometChatCalls.CallbackListener<GenerateToken>() {
            override fun onSuccess(token: GenerateToken) {
                CometChatCalls.joinSession(token, sessionSettings, callContainer, object : CometChatCalls.CallbackListener<CallSession>() {
                    override fun onSuccess(callSession: CallSession) {
                        // Listeners are LIFECYCLE-BOUND (owner = this Activity) — register here, after join.
                        callSession.addSessionStatusListener(this@MeetCallActivity, object : SessionStatusListener() {
                            override fun onSessionLeft() { finish() }
                            override fun onSessionTimedOut() { finish() }
                            override fun onConnectionClosed() { finish() }
                        })
                    }
                    override fun onError(e: CometChatException) { /* show e.code + e.message, then finish() */ }
                })
            }
            override fun onError(e: CometChatException) { /* ERROR_AUTH_TOKEN ⇒ not logged in; show it */ }
        })
    }

    override fun onDestroy() {
        if (CallSession.getInstance().isSessionActive) CallSession.getInstance().leaveSession()   // never leak a live session
        // If you called CometChatOngoingCallService.launch(...), ALSO CometChatOngoingCallService.abort(this) here —
        // onSessionLeft is NOT delivered on Activity destroy (BACK), so callback-only abort leaks the FGS (AUDIT-227).
        super.onDestroy()
    }
}
```
Compose host: the same code inside `AndroidView(factory = { RelativeLayout(it) })` filling `Modifier.fillMaxSize()`; declare the Activity with `configChanges` (Rotation pitfall, `references/pitfalls.md`).

## 1:1 ringing (Chat SDK signaling + Calls SDK media)
Register the `CallListener` **once, globally** (`Application.onCreate`, after `CometChat.initFromSettings` + `CometChat.login` — the `cometchat-android-v5-sdk` recipe) so the callee rings from any screen **of a FOREGROUND app**. Full recipe (both roles, Kotlin) + the ringing prerequisites: **`references/ringing.md`** — `initiateCall` → peer `onIncomingCallReceived` → `acceptCall`/`rejectCall` → `joinSession(call.sessionId)` on BOTH sides → hang-up = `leaveSession` **and** `CometChat.endCall`.
- **Foreground-only (verified live).** In auto socket mode the Chat SDK **drops its WebSocket the instant the app is backgrounded** — a backgrounded callee never gets `onIncomingCallReceived` and a backgrounded caller never gets `onOutgoingCallAccepted` (not replayed on return). Background / killed-app ringing = the VoIP push path (`/calls/android/voip-calling`). Never promise it from this recipe. Full evidence + the caller-side reconcile (dismiss on timeout, `onResume` re-check): **`references/ringing.md`.**

## Common pitfalls (BAKED)
> One-liners here; **full evidence + reasoning for every one — see `references/pitfalls.md`.** minSdk-26 floor + missing `<service>` are in Prerequisites (evidence: `references/build-truth.md`).
- **Don't duplicate the built-in call controls (the #1 mistake).** `joinSession` renders a COMPLETE call UI (mute, camera, switch, audio mode, layout, participants, raise hand, recording, invite, timer, red leave) into your `RelativeLayout` — no custom control row unless the ask is "replace the controls" (then `hideControlPanel(true)` FIRST).
- **Docs ≠ AAR (verified vs 5.0.4):** `setType`→`setSessionType` · `unMuteAudio`→`unmuteAudio` · `unPinParticipant`→`unpinParticipant` · `pinParticipant(uid)`→`(uid, pid)` · `MediaEventsListener.onScreenShareStarted/Stopped` don't exist (they're on `ParticipantEventListener`) · `raiseHand`/`setLayout`/`startRecording` are no-ops. Per-page notes: `references/docs-map.md`.
- **Wrong container** — `joinSession` needs a real-sized `RelativeLayout`; `wrap_content`/zero size renders invisibly (`ERROR_CALLING_VIEW_REF_NULL` if null).
- **`joinSession` crashes `libhermes_executor.so not found`** — SoLoader merged-mapping init missing; see Prerequisites § SoLoader.
- **Joining before init+login resolve** — `ERROR_COMETCHAT_CALLS_SDK_INIT` / `ERROR_AUTH_TOKEN`; chain off the callbacks.
- **`ERROR_COMETCHAT_CALLS_SDK_INIT` after a user switch is MISLEADING** (AUDIT-194) — re-init between logout and login: `references/user-switch.md`.
- **No runtime permissions** — the call joins with a dead mic/camera; request `CAMERA` + `RECORD_AUDIO` first.
- **Listeners registered before join** — register in `joinSession`'s `onSuccess` with a `LifecycleOwner`.
- **Hang-up on one SDK only (ringing)** — `leaveSession` without `CometChat.endCall` leaves the peer in-call; do both.
- **Android can't START screen share** (receive-only), and has **no virtual-background page** — don't promise either.
- **Rotation / Home kill the call** — `configChanges` (+ `supportsPictureInPicture`); keep alive with `CometChatOngoingCallService.launch(activity)` (needs the `<service>`).
- **Ongoing-call service LEAKS if you only `.abort` in `onSessionLeft` (AUDIT-227)** — also `CometChatOngoingCallService.abort(this)` in `onDestroy`; abort on EVERY teardown path.
- **No-op in-call actions (5.0.4 SDK bug, AUDIT-187):** `raiseHand`/`lowerHand`, mid-call `setLayout`, `startRecording`/`stopRecording` — no effect/callback/error; prefer the SDK's own buttons.
- **Backgrounded apps do not ring and do not hear the accept** — foreground only; VoIP push for the rest (§ 1:1 ringing).
- **Mixing majors** — Calls SDK is **5.x** (`joinSession`); `startSession`/`CallSettingsBuilder` + `/calls/v4/android` are the OLD tree.

## Verify it works
- **Tier-1 catalog:** every emitted symbol is in `android-calls-v5.json` (`node test-suite/scripts/verify-catalog.mjs`).
- **Tier-2 fences:** the Kotlin compiles against the installed `calls-sdk-android:5.0.4` (`npm run verify:fences:android-v6`); your app builds at `minSdk 26` (the manifest merge is the floor check).
- **Tier-3 device:** `./gradlew :app:assembleDebug` (at `minSdk 26`), then on an emulator/device: grant mic+camera → `joinSession` shows the SDK call surface with its own controls → a second device on the same `sessionId` appears as a tile → Home shows the ongoing-call notification (the `<service>` works) → leave ends cleanly (`onSessionLeft`). Ringing: two devices/users, BOTH apps FOREGROUND — accept joins both, hang-up ends both; then background the callee and confirm your outgoing UI times out cleanly (no callback comes). The pack's reviewer proves the round-trip via `CallsSmokeTests`.
