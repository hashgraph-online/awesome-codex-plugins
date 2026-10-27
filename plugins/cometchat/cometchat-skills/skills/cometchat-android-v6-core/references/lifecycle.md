# lifecycle — init once, login guard, logout (Android v6)

> Ground truth: installed `chatuikit-core-android` 6.0.5 `CometChatUIKit.kt` (`initFromSettings`/`login`/`loginWithAuthToken`/`logout`/`getLoggedInUser`/`isSDKInitialized`) + `ui-kit/android/getting-started-kotlin.md` / `getting-started-jetpack.md` (gate pattern), verified 2026-08-20.

## Init once — via `initFromSettings`, and where it lives
The canonical init is **`CometChatUIKit.initFromSettings(context, callback)`** — it reads the gitignored `app/src/main/assets/cometchat-settings.json` (`setup-credentials.md` §4), persists `integrationSource="ai-agent"` for telemetry attribution, and auto-inits the Calls SDK when `uiKit.enableCalling` is true. A classic `init(context, UIKitSettings, callback)` overload also exists on `CometChatUIKit`, but **do not use it as the default — it loses the telemetry attribution** (AUDIT-084); reach for it only when a user explicitly needs programmatic settings.

Init is async; **nothing CometChat renders until `onSuccess` fires** (docs Warning: *"`init()` must resolve before you call `login()`. Calling `login()` before init completes will fail silently."*). Two valid placements:

- **Gate Activity (RECOMMENDED — the docs getting-started pattern):** the launcher/splash Activity runs `initFromSettings → login` and only then navigates to (Views) / renders (Compose) the chat UI. Failures surface on the gate screen instead of a blank chat.
- **Application.onCreate:** fine for init alone, but you still need a ready-gate before any `CometChat*` UI renders, and login usually depends on app auth state — so you end up building the gate anyway. Use it only when every screen needs CometChat from frame 1.

**Do NOT re-init per Activity/screen.** Init once per process. If a later entry point can't be sure init ran (deep link, notification tap, process death restoring a back stack), guard with `CometChatUIKit.isSDKInitialized()` — if false, route through the gate rather than sprinkling init calls through the app.

## The exact init shape (both cohorts — same code)
```kotlin
import com.cometchat.chat.core.CometChat
import com.cometchat.chat.exceptions.CometChatException
import com.cometchat.chat.models.User
import com.cometchat.uikit.core.CometChatUIKit

// Reads app/src/main/assets/cometchat-settings.json (appId, region, credentials.authKey,
// uiKit.subscribePresenceForAllUsers/enableCalling) and persists integrationSource="ai-agent".
CometChatUIKit.initFromSettings(this, object : CometChat.CallbackListener<String>() {
    override fun onSuccess(s: String) { loginUser() }             // init resolved — ONLY now login
    override fun onError(e: CometChatException?) {
        // SURFACE it — show e?.message on the gate screen; do NOT proceed to chat.
        // ERR_SETTINGS_FILE_NOT_FOUND → the assets JSON is missing; ERR_SETTINGS_INVALID → appId/region missing.
    }
})
```
(Compose cohort: hold `isReady`/`error` in `mutableStateOf` and let `setContent` render error → spinner → `ChatApp()` — the getting-started-jetpack gate; Views cohort: `startActivity` to the conversations screen only from login's `onSuccess`, as getting-started-kotlin does.)

## Login guard — skip if logged in; logout before switching users
```kotlin
private fun loginUser() {
    val existing = CometChatUIKit.getLoggedInUser()          // sync; null if nobody logged in
    if (existing != null && existing.uid == uid) { unlockChatUi(); return }   // same user → done
    // DIFFERENT user still logged in → logout FIRST, then login in its onSuccess
    CometChatUIKit.login(uid, object : CometChat.CallbackListener<User>() {
        override fun onSuccess(user: User) { unlockChatUi() }
        override fun onError(e: CometChatException) { /* surface e.message — e.g. ERR_UID_NOT_FOUND */ }
    })
}
```
- **Same UID re-login is safe:** the kit short-circuits and returns the cached user via `onSuccess` (verified in 6.0.5 source) — but the guard keeps intent obvious and skips a needless call.
- **Different UID while logged in:** call `CometChatUIKit.logout(...)` and only login in its `onSuccess` — logging in over an existing session errors.
- The UID comes from the user / dashboard (`setup-credentials.md` §7) — never hardcoded in shipped code.

## Production login — auth token, not Auth Key
Mint a per-user token server-side (CometChat REST API), then:
```kotlin
CometChatUIKit.loginWithAuthToken(authToken, object : CometChat.CallbackListener<User>() {
    override fun onSuccess(user: User) { unlockChatUi() }
    override fun onError(e: CometChatException) { /* surface */ }
})
```
Prod builds OMIT `credentials.authKey` from `cometchat-settings.json` (`appId`/`region` stay — they're not secrets). Never ship the Auth Key in a release build (docs Warning on both getting-started pages).

## Logout
```kotlin
CometChatUIKit.logout(object : CometChat.CallbackListener<String>() {
    override fun onSuccess(s: String) { /* route to your sign-in screen */ }
    override fun onError(e: CometChatException?) { /* surface */ }
})
```
Call on app sign-out (it also clears the calls session when calling is enabled). After logout, the next chat entry must pass back through the gate.

## Process death & configuration changes
- **Config change (rotation/theme):** the SDK is a process-level singleton — the Activity recreates, init/login state survives. Do NOT re-run init in every `onCreate` unconditionally; the gate + `isSDKInitialized()` / `getLoggedInUser()` guards make re-entry a no-op.
- **Process death:** Android may recreate a deep Activity with the process cold. Any Activity that hosts `CometChat*` views must tolerate this: check `CometChatUIKit.isSDKInitialized()` (and `getLoggedInUser() != null`) in `onCreate`; if not ready, bounce to the gate (which re-inits and re-logs-in via the guards) instead of rendering a dead chat surface.
- **Login session persists** across launches on the device — on warm starts `getLoggedInUser()` is non-null and the gate skips straight past login.

## Surfacing CometChatException — never swallow
Every callback's `onError` hands you a `CometChatException` — log it AND show the user something actionable (`e.message`; wrong Region, a missing settings file, and a missing UID are the three most common). A swallowed `onError` is the #1 cause of "blank screen, no errors" (`troubleshooting.md`). Do not block the main thread waiting for callbacks (no latches/`runBlocking`) — they already arrive on the main thread; drive UI state from them.
