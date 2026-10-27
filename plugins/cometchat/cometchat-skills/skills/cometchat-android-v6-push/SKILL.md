---
name: cometchat-android-v6-push
description: "Add push notifications (FCM) to an Android v6 CometChat app — Firebase + Dashboard provider setup, the push dependency, token registration after login, token refresh, unregister on logout, manifest/service wiring, badge count and notification navigation. THIN + docs-first: fetches the notifications docs for exact payloads. Triggers: 'add push notifications android cometchat', 'fcm cometchat android', 'notifications not arriving android', 'badge count android'."
license: "MIT"
compatibility: "Android minSdk >=28; compileSdk >=36; Kotlin >=2.1; AGP >=8.9.1; JVM target 11; com.cometchat:chatuikit-kotlin-android ^6 OR com.cometchat:chatuikit-compose-android ^6 (6.0.x); com.cometchat:chat-sdk-android ^5; Firebase BoM (firebase-messaging)"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat android push notifications fcm v6 firebase"
---

> **Ground truth:** `features.android-v6.json` (`push-notifications`) + the **live notifications docs** — `/notifications/android-push-notifications` is the manual (12 sections: Firebase+Dashboard prep, Gradle, manifest/services, application wiring, token registration, unregister, badge count, message/call pushes, payload customization, navigation). This skill is THIN and docs-first: it owns the ORDER and the traps; **fetch the page for exact payloads/snippets** (`core` → `references/docs-map.md`).

## Companion skills (read first)
- `cometchat-android-v6-core` — install, credentials, `initFromSettings → login`, lifecycle. Assumed here, never repeated.
- `cometchat-android-v6-calls` — call pushes ride the same channel (ConnectionService path in the docs).

## Use this skill when
"add push notifications", "set up FCM with CometChat", "pushes aren't arriving", "notification badge count", "open the right chat when a notification is tapped".

## Feature check (the oracle first)
`features.android-v6.json` → `push-notifications`: **`gradle-package`**, `needs_stitching: true`, `needs_dashboard: true`. So it is never "just code": it needs **(a)** a Firebase project + `google-services.json`, **(b)** an FCM **provider configured in the CometChat Dashboard** (you get a **Provider ID** — you'll need it in code), and **(c)** client wiring. Tell the user all three up front; you cannot do (a)/(b) for them.

## Enablement — the ordered path
1. **Firebase + Dashboard** — create/choose the Firebase project, add the Android app, download `google-services.json` into `app/`. In the CometChat Dashboard → Notifications, add the FCM provider (service-account credentials) and note the **Provider ID**.
2. **Gradle** — Google services plugin + `com.google.firebase:firebase-messaging` (via the Firebase BoM) alongside your kit + `chat-sdk-android`. Exact coordinates/versions: fetch the docs page (§2) rather than pinning from memory.
3. **Manifest + service** — the `POST_NOTIFICATIONS` runtime permission (Android 13+), your `FirebaseMessagingService` subclass registered in the manifest, and a notification channel. (docs §3, §5)
4. **Register the token AFTER login succeeds** — never before; the token binds to the logged-in user:
```kotlin
FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
    if (task.isSuccessful) {
        CometChatNotifications.registerPushToken(
            task.result,
            PushPlatforms.FCM_ANDROID,
            PROVIDER_ID,                       // from the Dashboard FCM provider
            object : CometChat.CallbackListener<String?>() {
                override fun onSuccess(uid: String?) { /* registered */ }
                override fun onError(e: CometChatException) { /* retry / surface */ }
            }
        )
    }
}
```
5. **Re-register on token refresh** — the same call inside your service's `onNewToken(token)`. **Without this, pushes stop silently after Firebase rotates the token.**
6. **Unregister on logout — BEFORE `CometChatUIKit.logout()`**:
```kotlin
CometChatNotifications.unregisterPushToken(object : CometChat.CallbackListener<String?>() {
    override fun onSuccess(s: String?) { /* then log out */ }
    override fun onError(e: CometChatException) { /* surface */ }
})
```
   Skipping this leaks notifications to the previous user on a shared device.
7. **Handle the payload** — message pushes (§9), call pushes via ConnectionService (§10), custom text/parsing (§11), tap-to-open navigation (§12), badge count (§8, needs the Dashboard badge toggle + a badge library). Fetch these sections; don't invent payload keys.

## Client token wiring — the rules that matter
- Registration is **per logged-in user per device**: register after every successful login, unregister before every logout, re-register on refresh.
- The **Provider ID must match** the Dashboard FCM provider — a wrong/blank ID registers fine and then delivers nothing.
- Handle `onError` — a failed registration is the single most common cause of "no notifications", and it fails quietly if you ignore it.
- Foreground behavior is yours: CometChat delivers the push; whether you show a notification while the chat is open is app logic.

## Common pitfalls
Registering before login (token bound to nobody) · no `onNewToken` re-registration (pushes die after rotation) · no unregister on logout · wrong/omitted Provider ID · missing `google-services.json` or the Google-services plugin · missing `POST_NOTIFICATIONS` permission on Android 13+ · no notification channel (notification silently dropped) · testing on an emulator without Play services · assuming the Dashboard provider exists — ask.

## Verify it works
Compile against the pinned kit (`./gradlew :app:assembleDebug   # in YOUR app (npm run verify:fences:android-v6 is a pack-repo gate)`). **Live delivery is a MANUAL device check — it cannot be auto-smoked** (blocked-external; be honest about this): install on a real device with Play services, log in, confirm the registration callback hit `onSuccess`, background the app, send a message from another user → the notification arrives, and tapping it opens the right chat. Then log out and confirm notifications stop. Nothing arriving ⇒ check, in order: registration `onError`, Provider ID, Dashboard provider config, `google-services.json`, notification permission/channel.
