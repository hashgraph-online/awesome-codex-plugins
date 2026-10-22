---
name: cometchat-angular-v5-push
description: "Web push notifications for a CometChat Angular app — the Notifications product, FCM registration, the service worker, and token lifecycle. Docs-first: fetches the current notifications docs rather than baking a version-specific recipe. Triggers: 'add push notifications to my angular app', 'notify users when the app is closed', 'fcm setup', 'register push token'."
license: "MIT"
compatibility: "@cometchat/chat-sdk-javascript ^4.1.13; Angular 17-21; requires the CometChat Notifications product"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat angular push v5 notifications fcm firebase service-worker"
---

> **Ground truth:** push is the CometChat **Notifications** product, not a UI Kit component — this skill is THIN and docs-first. Registration, payload shape and provider setup are FETCHED from the notifications docs via `cometchat-angular-v5-core/references/docs-map.md`; nothing about them is baked here. Live delivery cannot be auto-smoked — say so honestly rather than claiming verification.

## Companion skills (read first)
- `cometchat-angular-v5-core` — install, credentials, `init→login→render`. Assumed.

## Use this skill when
Delivering notifications while the app is closed or backgrounded.

## This skill is deliberately THIN — fetch the docs
Push spans a product (CometChat Notifications), a third-party provider (Firebase/FCM), a service worker, and browser permission rules. Every one of those changes independently, so a baked recipe goes stale fast.

**Start here:** `{SDK_DOCS_BASE}/notifications/overview.md`, then the web push integration page. Discover the current pages from the SDK index (`cometchat-angular-v5-core/references/docs-map.md`). Read before writing.

Angular's own docs cover push only inside `{DOCS_BASE}/ui-kit/angular/campaigns.md` — there is no dedicated Angular push page. That is a **known docs gap**; the product-level notifications docs are the source of truth.

## What is true regardless of version
**1. Push is a separate product.** It must be enabled and configured for the app in the dashboard, with provider credentials added there. No client code substitutes for that step.

**2. It is not the UI Kit.** Registration is SDK-level (`CometChatNotifications`), not a component. There is nothing to render.

**3. It needs a service worker at origin root.** `firebase-messaging-sw.js` must be served from `/`, not from a nested path. In Angular, add it to the app's `assets` in `angular.json` so it lands at the root of `dist/`, and confirm it is reachable at `/firebase-messaging-sw.js` after build — a 404 there is the single most common cause of "push does nothing".

**4. Permission requires a user gesture.** Call the permission request from a click. Browsers block it on load, and repeated silent blocks poison the origin.

**5. Token lifecycle is yours.** Register the FCM token after login; unregister on logout. Skipping the unregister sends the next user's notifications to the previous device.

**6. iOS Safari is PWA-only.** Web push on iOS requires the site installed to the home screen. Not a bug; set expectations.

## Angular specifics
- Register the token **after** `login()` resolves — see core's guarded-login pattern.
- Put registration in a service, not a component, so it does not re-run per route.
- If the app is SSR, guard all of it with `isPlatformBrowser` (`cometchat-angular-v5-patterns`).
- Unregister in the same place you call `CometChatUIKit.logout()`.

## Verify it works
Push cannot be verified in a headless browser: it needs a real device or browser profile, a live provider, and a backgrounded app. Expect to test by hand:
1. Load over HTTPS, grant permission from a click.
2. Confirm `/firebase-messaging-sw.js` returns 200.
3. Background the tab; send a message from a second account.
4. Notification arrives; tapping it focuses the app.
5. Log out; confirm notifications stop.

## Common pitfalls
1. **Notifications not enabled in the dashboard** — nothing works, no error.
2. **Service worker not at origin root** — silent failure.
3. **Permission requested on load** — blocked.
4. **Token registered before login** — no user to attach it to.
5. **No unregister on logout** — notifications follow the wrong user.
6. **Expecting iOS Safari to work outside a PWA.**
7. **Baking a recipe from memory** — fetch the docs; this area moves.
