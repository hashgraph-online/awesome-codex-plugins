# 1:1 ringing — the recipe (Chat SDK v5 signaling + Calls SDK v5 media)

> Loaded from `SKILL.md` § 1:1 ringing. Symbols: `sdk-android-v5.json` (Chat SDK) + `android-calls-v5.json` (Calls SDK).
> Signatures: `references/docs-map.md` § "1:1 RINGING" → `/calls/android/ringing`. Verified live 2026-09-07
> (calls-sdk 5.0.4 + chat-sdk 5.0.5, two processes on one emulator — both roles).

## Prerequisites (on top of the meet-style ones)
- `implementation("com.cometchat:chat-sdk-android:5.0.5")` **+ `android.enableJetifier=true`** (with
  `android.useAndroidX=true`) in `gradle.properties` — `chat-sdk-android:5.0.5` still pulls
  `android.arch.lifecycle:extensions:1.1.1 → com.android.support:support-compat:26.1.0`; without Jetifier an AndroidX
  app fails `checkDebugDuplicateClasses` (`Duplicate class android.support.v4.app.INotificationSideChannel …`).
- Chat SDK init + login FIRST — `CometChat.initFromSettings(context, l)` → `CometChat.login(uid, authKey, l)` (the
  `cometchat-android-v5-sdk` recipe; same settings asset), THEN the Calls SDK init/login, THEN register the listener.
  A Calls-SDK login does NOT log the Chat SDK in — check `CometChat.getLoggedInUser()` separately
  (`initiateCall` on a chat-logged-out process fails `ERROR_USER_NOT_LOGGED_IN`).

## ⚠️ Foreground-only — the caveat the docs page does not state (verified live)
In the default **auto** socket mode the Chat SDK **disconnects its WebSocket the moment the app is backgrounded**
(`/sdk/android/v5/connection-behaviour`: "App in background — immediately disconnected"). Consequences, all reproduced:
- a **backgrounded CALLEE never receives `onIncomingCallReceived`** — the caller gets `onOutgoingCallRejected` when the
  `initiateCall` timeout (default 45 s) expires;
- a **backgrounded CALLER never receives `onOutgoingCallAccepted`**, and it is **NOT replayed** on return to the
  foreground — an un-reconciled caller sits on "Calling…" forever.
So "rings from any screen" means **any screen of a FOREGROUND app**. Background / killed-app ringing is the **VoIP push
path** — `/calls/android/voip-calling` (FCM + `ConnectionService`; docs-first, real device, class-E in the pack's
harness) — offer it explicitly instead of promising background ringing. **Manual** socket mode + `CometChat.ping()`
within every 30 s keeps the socket alive only while the process is alive (same docs page) — not a substitute for VoIP.

## Caller-side reconcile (bake it into YOUR outgoing UI)
1. Start a timer when `initiateCall` succeeds, equal to the timeout you passed (`initiateCall(call, timeoutSec, l)`;
   default 45 s). No `onOutgoingCallAccepted` / `onOutgoingCallRejected` by then ⇒ treat as **unanswered**: dismiss the
   outgoing UI and cancel with `CometChat.rejectCall(sessionId, CometChatConstants.CALL_STATUS_CANCELLED, l)` so the
   callee's prompt and the call log close cleanly.
2. On `onResume` after the app was backgrounded mid-ring, re-check the call state (`CometChat.getActiveCall()` in the
   Chat SDK method map) and either `joinSession(call.sessionId)` or dismiss — never rely on a replayed callback.
3. On the callee, `onIncomingCallCancelled` dismisses the prompt; a prompt still showing after the caller's timeout is a
   sign the listener was registered on a screen that was destroyed — register it ONCE in `Application`.

## The recipe (both roles)
`joinMedia` = the meet-style `joinRoom` in `SKILL.md`, with the call's `sessionId`, on BOTH sides.
```kotlin
import com.cometchat.calls.core.CallSession
import com.cometchat.chat.constants.CometChatConstants
import com.cometchat.chat.core.Call
import com.cometchat.chat.core.CometChat
import com.cometchat.chat.exceptions.CometChatException

object RingingSignaling {
    private const val LISTENER_ID = "app-call-listener"

    fun register(onIncoming: (Call) -> Unit, joinMedia: (sessionId: String) -> Unit, dismiss: () -> Unit) {
        CometChat.addCallListener(LISTENER_ID, object : CometChat.CallListener() {
            override fun onIncomingCallReceived(call: Call) = onIncoming(call)            // show YOUR incoming UI
            override fun onOutgoingCallAccepted(call: Call) = joinMedia(call.sessionId)  // caller joins the same session
            override fun onOutgoingCallRejected(call: Call) = dismiss()
            override fun onIncomingCallCancelled(call: Call) = dismiss()
            override fun onCallEndedMessageReceived(call: Call) { CallSession.getInstance().leaveSession(); dismiss() }
        })
    }
    fun unregister() = CometChat.removeCallListener(LISTENER_ID)                          // teardown

    fun call(peerUid: String, onRinging: (Call) -> Unit) {                                // caller
        val call = Call(peerUid, CometChatConstants.RECEIVER_TYPE_USER, CometChatConstants.CALL_TYPE_VIDEO)
        CometChat.initiateCall(call, object : CometChat.CallbackListener<Call>() {        // (call, timeoutSec, l) overload exists
            override fun onSuccess(outgoing: Call) = onRinging(outgoing)                   // show YOUR outgoing UI
            override fun onError(e: CometChatException) { /* e.code + e.message */ }
        })
    }
    fun accept(sessionId: String, joinMedia: (String) -> Unit) {                          // callee
        CometChat.acceptCall(sessionId, object : CometChat.CallbackListener<Call>() {
            override fun onSuccess(call: Call) = joinMedia(call.sessionId)
            override fun onError(e: CometChatException) { /* e.code + e.message */ }
        })
    }
    fun reject(sessionId: String) {                                                       // callee (caller cancels with CALL_STATUS_CANCELLED)
        CometChat.rejectCall(sessionId, CometChatConstants.CALL_STATUS_REJECTED, object : CometChat.CallbackListener<Call>() {
            override fun onSuccess(call: Call) {}
            override fun onError(e: CometChatException) { /* e.code + e.message */ }
        })
    }
    fun hangUp(sessionId: String) {                                                       // either side — BOTH SDKs
        CallSession.getInstance().leaveSession()                                          // Calls SDK: leave media
        CometChat.endCall(sessionId, object : CometChat.CallbackListener<Call>() {        // Chat SDK: peer gets onCallEndedMessageReceived + the log completes
            override fun onSuccess(call: Call) {}
            override fun onError(e: CometChatException) { /* e.code + e.message */ }
        })
    }
}
```
> **Testing ringing needs TWO live clients and two users**, each logged in (Chat SDK AND Calls SDK) with the listener
> registered and the app in the FOREGROUND — the caller's ringing UI alone proves nothing. Two processes on one emulator
> (two `applicationId`s / build types) work when a second device is unavailable.
