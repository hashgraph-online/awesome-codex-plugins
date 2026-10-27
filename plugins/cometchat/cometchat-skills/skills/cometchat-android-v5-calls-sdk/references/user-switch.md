# Switching users (account switch / shared device) — Calls SDK v5

> **Verified live 2026-09-08** on two emulators (Pixel_10 + Pixel_8), `calls-sdk-android 5.0.4` +
> `chat-sdk-android 5.0.5`. The docs' authentication page does NOT cover this path (DOCS-BACKLOG C13).

## The trap

`CometChatCalls.logout()` — **and the implicit logout inside `login(<a different uid>)`** — leaves the
Calls SDK **de-initialized**: `CometChatCalls.isInitialized()` returns `false` afterwards. Nothing in the
docs says so, and `login()` for the new user still reports **`onSuccess`**. The failure only surfaces one
call later:

```
generateToken FAILED: ERROR_COMETCHAT_CALLS_SDK_INIT
  "Please call the CometChatCalls.init() method preferably in the onCreate() method of the
   application class before calling any other methods related to CometChatCalls"
```

That message sends you hunting for a missing `init()` in `Application.onCreate()` — which **is** there and
**did** resolve (`Init Successful`) at process start. The real cause is the logout that happened since.

**Evidence (measured, same device, same build):**

| Sequence | `isInitialized()` | `generateToken` |
|---|---|---|
| init → login(uid-3) → generateToken *(no switch)* | `true` | **OK** → `onSessionJoined` |
| init → login(uid-2) with uid-3 still logged in | — | **FAILS** `ERROR_COMETCHAT_CALLS_SDK_INIT` |
| init → logout both → login(uid-2) | **`false`** before login, `false` after | **FAILS** (same error) |
| init → logout both → **re-init** → login(uid-2) | **`true`** | **OK** → `onSessionJoined` |

Logging out is not enough on its own — **the re-init is the step that fixes it.**

## The sequence (BAKED)

Switching from `current` to `uid` — do all four, in order, each chained off the previous callback:

1. `CometChatCalls.logout(listener)` — Calls SDK
2. `CometChat.logout(listener)` — Chat SDK (ringing only; also clears the stale chat session)
3. `CometChatCalls.initFromSettings(context, listener)` — **re-init, and WAIT for `onSuccess`**
4. `CometChatCalls.login(uid, authKey, listener)` (+ `CometChat.login` for ringing)

```kotlin
fun switchUser(uid: String, authKey: String, then: () -> Unit) {
    val current = CometChatCalls.getLoggedInUser()
    if (current == null) { loginBoth(uid, authKey, then); return }        // nobody logged in
    if (current.uid == uid) { then(); return }                            // SAME user — nothing to do

    CometChatCalls.logout(object : CometChatCalls.CallbackListener<String>() {
        override fun onSuccess(msg: String) {
            CometChat.logout(object : CometChat.CallbackListener<String>() {   // ringing builds only
                override fun onSuccess(m: String) = reinitThenLogin(uid, authKey, then)
                override fun onError(e: com.cometchat.chat.exceptions.CometChatException) =
                    reinitThenLogin(uid, authKey, then)                   // stale chat session is non-fatal
            })
        }
        override fun onError(e: CometChatException) { /* surface e.code; do NOT continue silently */ }
    })
}

private fun reinitThenLogin(uid: String, authKey: String, then: () -> Unit) {
    // MANDATORY: logout left isInitialized() == false. Re-init BEFORE login or generateToken
    // will fail with the misleading ERROR_COMETCHAT_CALLS_SDK_INIT.
    CometChatCalls.initFromSettings(context, object : CometChatCalls.CallbackListener<String>() {
        override fun onSuccess(result: String) = loginBoth(uid, authKey, then)
        override fun onError(e: CometChatException) { /* surface e.code */ }
    })
}
```

## Rules

- **Never guard login with `getLoggedInUser() != null` alone.** That is the docs' snippet
  (`if (getLoggedInUser() == null) login(...)`) and it only handles "same user". On a shared or
  re-used device it silently places calls **as the previous user**. Branch on the **uid**:
  `getLoggedInUser()?.uid == uid`.
- **Leave the call first.** `CallSession.getInstance().leaveSession()` (and `CometChat.endCall` if the
  session came from ringing) before logging out — a switch during a live session leaks it.
- **Re-register the ringing `CallListener`** after the new login; listener IDs from the old session are
  bound to the old user (`references/ringing.md`).
- **Fresh installs are unaffected** — the trap needs a pre-existing session, which is exactly why it
  survives testing on a clean emulator and then bites on a real user's device.

## Upstream status

- **Docs (DOCS-BACKLOG C13):** `/calls/android/authentication` documents `logout()` as "clears the local
  session" with no mention that it also de-initializes the SDK, and its login guard covers only the
  null case. Both need the switch path.
- **SDK (class C):** `login(<different uid>)` reporting `onSuccess` while leaving the SDK de-initialized,
  then failing one call later with an error naming the wrong cause, is an SDK defect (AUDIT-194).
  Drop this workaround's re-init step if a 5.0.x ships that re-initializes on login.
