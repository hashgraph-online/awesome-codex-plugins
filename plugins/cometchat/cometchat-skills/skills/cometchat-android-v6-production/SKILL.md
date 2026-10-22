---
name: cometchat-android-v6-production
description: "Ship a CometChat Android v6 app safely — server-minted auth tokens instead of the dev Auth Key, keeping credentials out of the APK, release-build and R8/ProGuard checks, user provisioning server-side, rate limits, and the Play Store publishing prerequisites. Triggers: 'is my cometchat android app production ready', 'auth token instead of auth key android', 'release build cometchat android', 'proguard cometchat', 'publish chat app play store'."
license: "MIT"
compatibility: "Android minSdk >=28; compileSdk >=36; Kotlin >=2.1; AGP >=8.9.1; JVM target 11; com.cometchat:chatuikit-kotlin-android ^6 OR com.cometchat:chatuikit-compose-android ^6 (6.0.x, verified 6.0.5); com.cometchat:chat-sdk-android ^5"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat android production release auth-token security v6 proguard"
---

> **Ground truth:** the installed kit source (`CometChatUIKit.loginWithAuthToken`) + `contracts.android-v6.json` (`prod-auth-token-guidance`) + the live SDK pages `/sdk/android/v5/rate-limits` and `/sdk/android/v5/publishing-app-on-playstore`. Fetch specifics from docs; never assert a limit or a ProGuard rule from memory.

## Companion skills (read first)
- `cometchat-android-v6-core` — install, credentials, `initFromSettings → login`, lifecycle. Assumed here, never repeated.
- `cometchat-android-v6-builder-settings` — the settings file + auth method reference · `cometchat-android-v6-testing` — pre-release verification · `cometchat-android-v6-push` (unregister on logout).
- `cometchat-security` — the enterprise auth model this client-side hardening plugs into: wiring your IdP / SSO into the token flow (your IdP → your server → mint the CometChat auth token; CometChat is **not** an IdP), token expiry/refresh + re-login, RBAC roles + group (SBAC) scopes, and Auth Key vs auth token vs REST API Key. Load it for a security review or any SSO question.

## Use this skill when
"are we production ready?", "switch from the Auth Key to auth tokens", "prepare the release build", "does CometChat need ProGuard rules?", "what are the rate limits?", "anything to do before Play Store submission?".

## Production golden path
1. **Auth: server-minted tokens, never the Auth Key.** The dev flow (`login(uid, …)` backed by `credentials.authKey` in the settings file) is **development only** — the Auth Key can create/authenticate any user, so shipping it in an APK is a full compromise (APKs are trivially decompiled). Production: your backend creates the user and mints a per-user **auth token** via the CometChat REST API, your app fetches it over your own authenticated channel, then:
   ```kotlin
   CometChatUIKit.loginWithAuthToken(authToken, object : CometChat.CallbackListener<User>() {
       override fun onSuccess(user: User) { /* unlock the chat UI */ }
       override fun onError(e: CometChatException) { /* surface + retry path */ }
   })
   ```
   Guard it the same way (`getLoggedInUser() != null` → skip). Token fetch failure must be a real error state, not a blank screen.
2. **Strip credentials from the release artifact.** Omit `credentials.authKey` from `app/src/main/assets/cometchat-settings.json` in release builds (or ship a release-flavored assets file); keep the file **gitignored**. `appId`/`region` are not secrets, the Auth Key is. Verify by unzipping the APK/AAB and grepping the merged assets — do this before every release.
3. **Provision users server-side.** `CometChatUIKit.createUser(...)` is for prototypes; production creates users through your backend + the CometChat REST API, in the same request that issues the auth token.
4. **Log out cleanly.** Unregister the push token BEFORE `CometChatUIKit.logout(...)` (`cometchat-android-v6-push`), and clear any cached uid/token in your own storage — otherwise the next user on a shared device inherits notifications.
5. **Release build sanity.** Build the **release** variant (not just debug) and run the app: minified/shrunk builds are where reflection-based failures appear. The kit ships its own consumer rules, so there is normally nothing to add — but **verify by running the release build**, and if a `ClassNotFoundException`/serialization failure appears, capture it and check the current kit docs before hand-writing `-keep` rules. Don't paste ProGuard rules from memory.
6. **Rate limits & scale.** The Chat SDK has documented limits (message rates, request sizes, listener/connection behavior) — fetch `/sdk/android/v5/rate-limits.md` before building anything that sends in bulk or fans out; paginate with request builders rather than unbounded fetches.
7. **Play Store prerequisites.** Fetch `/sdk/android/v5/publishing-app-on-playstore.md` — it covers what the SDK needs for a store submission. Also budget for: runtime permission rationale (CAMERA/RECORD_AUDIO for calls, POST_NOTIFICATIONS for push), a privacy-policy entry covering chat data, and Data-safety form answers reflecting what CometChat transmits.

## Known failure modes → fix
| Symptom | Cause | Fix |
|---|---|---|
| Auth works in debug, fails in release | release settings file has no `authKey` but code still uses `login(uid)` | switch the release path to `loginWithAuthToken` |
| Auth Key found in the APK | `credentials.authKey` shipped | remove for release; rotate the key in the Dashboard |
| Crash only in release | shrinking/obfuscation | reproduce on the release variant, read the real stack trace, then consult docs before adding keep rules |
| Notifications reach the wrong user | token not unregistered on logout | unregister before logout |
| Sends throttled / requests rejected | rate limits | batch + paginate; fetch the limits page |
| Blank chat after reinstall | token fetch failed and wasn't surfaced | render an error state + retry |

## Common pitfalls
Treating the dev Auth Key path as shippable · a settings file committed to git · never building the release variant before submission · creating users from the client in production · hand-written ProGuard rules copied from an old version · unbounded message/user fetches · no error state for token-fetch failure · leaving `enableCalling`/debug logging on when the product doesn't use calls.

## Verify it works
Compile (`./gradlew :app:assembleDebug   # in YOUR app (npm run verify:fences:android-v6 is a pack-repo gate)`). Then, on a **release** build installed on a device: login uses `loginWithAuthToken` and succeeds; unzipping the artifact shows **no Auth Key**; chat, calls (if used) and push all work post-minification; logout unregisters push and a second user's session is clean; an intentionally broken token fetch shows a readable error, not a blank screen. Anything you could not verify (store review, backend token endpoint) — say so explicitly rather than claiming it.
