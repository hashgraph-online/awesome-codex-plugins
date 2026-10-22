---
name: cometchat-react-v7-push
description: "Add web push notifications to a React app with the CometChat v7 SDK — FCM via Firebase, registered through CometChatNotifications, with the Dashboard FCM provider as the sender. THIN + docs-first: the full setup is FETCHED from CometChat's notifications docs; this skill bakes only the hardening deltas + the token lifecycle. Triggers: 'add push notifications', 'web push', 'FCM push', 'notify on new message when app closed', 'cometchat push react'."
license: "MIT"
compatibility: "React >=18; @cometchat/chat-uikit-react ^7 (7.1.x); @cometchat/chat-sdk-javascript ^4.1.9 (ships CometChatNotifications); firebase ^10.3.1 (FCM web SDK)"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat react push notifications fcm firebase web v7"
---

> **Ground truth — DOCS-FIRST.** Push is an EXTERNAL integration (Firebase/FCM + a service worker + a Dashboard FCM provider), not a UI Kit component. The full, current setup lives in **CometChat's notifications docs — FETCH them, don't bake a recipe here**: via `cometchat-react-v7-core/references/docs-map.md` → `/notifications/push-overview` · `/notifications/web-push-notifications` · `/notifications/preferences`. This skill is THIN: it points you at those docs as the SOURCE and bakes ONLY the hardening deltas + the exact SDK symbols (verified vs installed `@cometchat/chat-sdk-javascript`). **Symbols are baked; the step-by-step is fetched.**

## Companion skills (read first)
- `cometchat-react-v7-core` — install, credentials, `init→login→render`. This skill ASSUMES it (push registers AFTER login, on the SAME SDK).

## Use this skill when
"add push notifications", "web push", "notify me on a new message when the app is closed", "FCM push". For a NON-web platform (Android/iOS/RN/Flutter) push differs — that's not this skill.

## Build it — FETCH the docs, then apply the deltas
1. **FETCH the setup from the docs** (source of truth): `{DOCS_BASE}/notifications/web-push-notifications.md` (+ `push-overview.md`) via `docs-map.md`. Follow its Firebase project + FCM setup, the `firebase-messaging-sw.js` service worker, and the client registration flow. **Build FROM the docs; if the docs are wrong/missing a detail, that's a DOCS gap — flag it (RULES §20), don't bake a permanent workaround.**
2. **Dashboard prerequisite:** set up the **FCM provider in the CometChat Dashboard** (it is the SENDER). Self-hosted VAPID / a custom webhook is NOT the v7 web path. Confirm this is done or push delivers nothing.
3. **Install:** `npm i firebase@^10.3.1` (the FCM web SDK). `CometChatNotifications` ships with the already-installed `@cometchat/chat-sdk-javascript` — no extra CometChat package.

## Baked SDK symbols (verified vs installed 7.1.x SDK — do NOT guess these)
```ts
import { CometChat, CometChatNotifications } from "@cometchat/chat-sdk-javascript";
// Register AFTER login, with the FCM token you got from firebase getToken():
await CometChatNotifications.registerPushToken(
  fcmToken,                                    // string — from firebase messaging getToken({ vapidKey })
  CometChatNotifications.PushPlatforms.FCM_WEB,   // enum member
  providerId                                   // optional — your Dashboard FCM provider id
);
// On logout (before CometChatUIKit.logout()):
await CometChatNotifications.unregisterPushToken();
```
> Signature (installed source): `registerPushToken(pushToken: string, platform: PushPlatforms, providerId?: string)` · `unregisterPushToken()`. Fetch anything beyond these from the notifications docs.

## Hardening deltas (BAKED — the things the docs tend to under-emphasize)
- **Service-worker placement is per-bundler.** `firebase-messaging-sw.js` must be served from the ORIGIN ROOT: **Vite / CRA → `public/firebase-messaging-sw.js`** (copied to the web root); **Next.js → `public/firebase-messaging-sw.js`** (App or Pages router); **Astro → `public/firebase-messaging-sw.js`**. A SW under `src/` or a hashed asset path will NOT register. HTTPS (or `localhost`) is required.
- **Request permission ON A USER GESTURE, not on load.** Call `Notification.requestPermission()` from a click/tap (a browser blocks/annoys otherwise). Only call `getToken()` after permission is `granted`.
- **Token lifecycle = tie it to login/logout.** `registerPushToken(...)` AFTER `CometChatUIKit.login()` resolves; `unregisterPushToken()` BEFORE `CometChatUIKit.logout()`. Re-register on token refresh (`onTokenRefresh`/`getToken` again). Skipping unregister on logout leaks notifications to the wrong user.
- **iOS web push is PWA-only.** On iOS/iPadOS, web push works ONLY in an **installed PWA** (Add to Home Screen) on **iOS 16.4+** — not in a normal Safari tab. Tell the user; don't promise Safari-tab push on iOS.
- **The Dashboard FCM provider is the sender.** No self-hosted VAPID server / webhook for v7 web — configure the provider in the Dashboard (step 2).

## Common pitfalls (BAKED)
- SW not at the origin root → registration silently fails, no push. · Requesting permission on load → blocked/denied. · Forgetting `unregisterPushToken()` on logout → cross-user leakage. · Expecting Safari-tab push on iOS. · No Dashboard FCM provider → nothing delivers even with correct client code.

## Verify it works (honest — push can't be auto-smoked)
Static verification only: the SDK symbols resolve + the app compiles + the SW registers (check the browser Application → Service Workers). **Live delivery is a manual, device-dependent check** (real HTTPS origin + a registered SW + the Dashboard FCM provider + `granted` permission → send a message with the app backgrounded). This is the one skill whose live gate is inherently **blocked-external** — do NOT claim delivery works from a build alone.

## Close (after it builds)
End with the shared 3-option selectable menu and WAIT for the pick — **① add another feature** (suggest a few not-yet-wired) · **② customize theming** · **③ test it manually** (stop; let the user check). Same contract as the `cometchat-react-v7-core` close (`RULES.md` §19).
