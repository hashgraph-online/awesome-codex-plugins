---
name: cometchat-android-v6-builder-settings
description: "The CometChat Android v6 settings and session API reference — the assets/cometchat-settings.json file that initFromSettings reads (appId, region, credentials, uiKit toggles), the legacy UIKitSettings builder, and the CometChatUIKit session methods (login, loginWithAuthToken, logout, getLoggedInUser, createUser). Use when configuring init options or wiring auth beyond the core golden path. Triggers: 'cometchat settings json android', 'uikitsettings builder options', 'login with auth token android', 'create a cometchat user from the app', 'enable calling in settings'."
license: "MIT"
compatibility: "Android minSdk >=28; compileSdk >=36; Kotlin >=2.1; AGP >=8.9.1; JVM target 11; com.cometchat:chatuikit-kotlin-android ^6 OR com.cometchat:chatuikit-compose-android ^6 (6.0.x, verified 6.0.5); com.cometchat:chat-sdk-android ^5"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat android settings uikitsettings auth v6 login authtoken"
---

> **Ground truth:** the installed kit source `com.cometchat.uikit.core.CometChatUIKit` (6.0.5) + the live page `/ui-kit/android/methods` (init · authentication · logout · create user · message helpers). Symbols verified against catalog `android-v6.json`. Fetch exact signatures from the methods page; never guess an overload.

## Companion skills (read first)
- `cometchat-android-v6-core` — owns the DEFAULT path: `initFromSettings → login → render`, the settings file, and credential handling. Come HERE only when a task needs an option or auth variant beyond that default.

## Use this skill when
"what can go in the settings file?", "turn on calling in the settings", "log in with a server-minted auth token instead of the auth key", "create a CometChat user from the app", "check who's logged in", "what does the UIKitSettings builder do?".

## Prerequisites & install
Same kit + init as `core`. Everything here is `com.cometchat.uikit.core` — no extra dependency.

## The settings file (the DEFAULT input to `initFromSettings`)
`app/src/main/assets/cometchat-settings.json` — **gitignored** (it carries the dev Auth Key). Read by `CometChatUIKit.initFromSettings(context, callback)`, which parses it, builds the settings, and persists `integrationSource="ai-agent"` for telemetry:
```json
{
  "appId": "APP_ID",
  "region": "REGION",
  "credentials": { "authKey": "AUTH_KEY" },
  "uiKit": {
    "subscribePresenceForAllUsers": true,
    "enableCalling": false
  }
}
```
- `appId` + `region` are **required** — missing either fails with `ERR_SETTINGS_INVALID`; a missing file fails with `ERR_SETTINGS_FILE_NOT_FOUND`.
- `credentials.authKey` is **optional and dev-only** — omit it in production builds and log in with a server-minted auth token.
- `uiKit.subscribePresenceForAllUsers` defaults to `true`.
- `uiKit.enableCalling` defaults to `false`. Setting it `true` makes `initFromSettings` auto-initialize the **Calls SDK** — **which means the `com.cometchat:calls-sdk-android` dependency becomes MANDATORY.** Without it the app throws `NoClassDefFoundError: CometChatCalls$SessionSettingsBuilder` from `initCometChatCalls` **during `onCreate`, before any UI renders** (verified on device). The two must always change together (→ `cometchat-android-v6-calls`).
- The Chat SDK may read an optional `chatSDK` section from the same file. It is **not required** — init succeeds without it. `/sdk/android/v5/setup.md` documents only the classic programmatic `init()` + `AppSettings`, so it will NOT tell you the section's keys; do not send the user there for them.

## The legacy `UIKitSettings` builder (know it, don't default to it)
`UIKitSettings.UIKitSettingsBuilder()` with `.setAppId(...)`, `.setRegion(...)`, `.setAuthKey(...)`, `.setEnableCalling(...)`, `.subscribePresenceForAllUsers()`, `.build()` feeds the classic `CometChatUIKit.init(context, settings, callback)` overload. **It still exists, but it is NOT the default** — it skips the integration-source telemetry that `initFromSettings` persists. Use it only when a project genuinely cannot ship an assets file (e.g. credentials arrive at runtime from your own backend); say so explicitly when you do, and keep credentials out of source either way.

## Session / auth methods (`CometChatUIKit`)
| Method | Use |
|---|---|
| `getLoggedInUser(): User?` | **Synchronous** guard — non-null means a session already exists; skip `login`. |
| `login(uid, CallbackListener<User>)` | Dev/auth-key login for an **existing** user. |
| `loginWithAuthToken(authToken, CallbackListener<User>)` | **Production** login with a server-minted per-user token. Auth Key never ships to the client. |
| `logout(CallbackListener<String>)` | End the session. Unregister the push token BEFORE this (`cometchat-android-v6-push`). |
| `createUser(user, CallbackListener<User>)` | Create a user from the app — **dev/prototype only**; production should mint users server-side with the REST API. |

Ordering never changes: **init resolves → (guard) login resolves → chat UI**. Re-logging in a *different* user requires `logout` first. Full lifecycle detail (where to init, config changes, process death): `core/references/lifecycle.md`.

## Message-helper reference (on the same docs page)
`/ui-kit/android/methods` also documents date formatting and constructing `TextMessage` / `MediaMessage` / `CustomMessage` for programmatic sends — fetch that section rather than hand-rolling a message object; the SDK types are the Chat SDK's (`cometchat-android-v5-sdk` / `core/references/docs-map.md` → SDK section).

## Common pitfalls
Committing `cometchat-settings.json` (leaks the Auth Key) · shipping `credentials.authKey` in a release build · using the classic `init(...)` as the default (loses telemetry attribution) · calling `login` before init's `onSuccess` (fails silently) · re-logging in without `logout` · using `createUser` in production · assuming `enableCalling` alone adds calling (the Calls SDK artifact is still required) · reading `getLoggedInUser()` before init.

## Verify it works
Compile against the pinned kit (`./gradlew :app:assembleDebug   # in YOUR app (npm run verify:fences:android-v6 is a pack-repo gate)`). On device: with the settings file present, init reports success and login resolves; delete/rename the file → you get `ERR_SETTINGS_FILE_NOT_FOUND` surfaced as a readable error (not a crash); with `enableCalling: true` + the Calls artifact, call buttons appear (Views: automatic; Compose: only with `hideVoiceCallButton = false, hideVideoCallButton = false` on the header — `cometchat-android-v6-calls`); a release build contains no Auth Key (grep the merged assets). Confirm `cometchat-settings.json` is in `.gitignore`.
