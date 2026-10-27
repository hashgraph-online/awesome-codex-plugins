---
name: cometchat-flutter-v6-production
description: "Take a CometChat Flutter integration to production — server-minted auth tokens instead of the Auth Key, secret handling in a Flutter bundle, logout/session hygiene, release build config, and the pre-ship checklist. Triggers: 'production auth cometchat', 'auth token flutter', 'is the auth key safe', 'ship cometchat to production', 'release build cometchat'."
license: "MIT"
compatibility: "Flutter >=3.38.9; cometchat_chat_uikit ^6 (6.1.x, verified 6.1.0); cometchat_sdk ^5.0.6"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat flutter production auth-token security release v6"
---

> **Ground truth:** `loginWithAuthToken` and `logout` are catalog-verified against 6.1.0. Token MINTING is a server-side REST call — its exact endpoint is FETCHED from the REST API docs, never guessed. The dev-vs-prod credential rule is `RULES.md` §4.

## Companion skills (read first)
- `cometchat-flutter-v6-core` — install, credentials, `init→login→render`, `lifecycle.md`. This skill ASSUMES it.
- `cometchat-flutter-v6-patterns` — where config comes from in your build pipeline.
- `cometchat-security` — the enterprise auth model this client-side hardening plugs into: wiring your IdP / SSO into the token flow (your IdP → your server → mint the CometChat auth token; CometChat is **not** an IdP), token expiry/refresh + re-login, RBAC roles + group (SBAC) scopes, and Auth Key vs auth token vs REST API Key. Load it for a security review or any SSO question.

## Use this skill when
Hardening before release: "is the Auth Key safe to ship", "set up production auth", "what do I check before shipping".

## Prerequisites & install
Core done. No new package.

## The one thing that actually matters: the Auth Key must not ship
An **Auth Key can log in as ANY user of your app.** Everything core writes for development puts it in `cometchat-settings.json`, which is bundled into the APK/IPA — and a bundle is not a secret. Anyone can extract it.

**Development (what core wired):** `credentials.authKey` in the settings asset → `CometChatUIKit.login(uid)`. Fine for building; never for release.

**Production (what you must move to):**
1. Your **server** mints a per-user auth token by calling CometChat's REST API with the **REST API Key** (which stays on the server, never in the app).
2. Your app authenticates the user your normal way, then asks YOUR backend for that token.
3. The app signs in with the token:
```dart
import 'package:cometchat_chat_uikit/cometchat_chat_uikit.dart';

Future<void> signIn(String authTokenFromYourServer) async {
  await CometChatUIKit.loginWithAuthToken(
    authTokenFromYourServer,
    onSuccess: (User user) {},
    onError: (CometChatException e) {},
  );
}
```
4. **Remove `credentials.authKey`** from the shipped settings file. Confirm by unzipping the release artifact and grepping for the key — do not take it on trust.
> Fetch the exact token-minting endpoint from the REST API docs (`../cometchat-flutter-v6-core/references/docs-map.md` → SDK/REST). Never invent a URL or payload.

## Session hygiene
- **Log out properly** — `CometChatUIKit.logout()` on your app's sign-out, and unregister the push token FIRST (`-push`), or the next user of the device receives the previous user's notifications.
- **One user per session.** `login` no-ops if that UID is already signed in, but switching users requires an explicit logout first.
- **Token expiry** — a server-minted token can expire; handle the login error by refetching from your backend rather than falling back to the Auth Key.

## Release build config
- **Android** — `minSdk 26` (the docs' 24 is too low — the kit's `cometchat_calls_sdk` dependency pins 26); INTERNET permission; calling adds camera/mic. If you use R8/ProGuard, verify the kit still works in a **release** build, not just debug.
- **iOS** — deployment target per the docs; usage-description strings for camera/mic/photos, or the OS kills the app on first use.
- **Settings asset** — a registered asset, so NOT gitignored (a fresh clone / CI `flutter build` fails with *"No file or variants found for asset"*): commit a placeholder (no real Auth Key) and have CI overwrite it at build time with the prod-flavoured file (no Auth Key).
- **Flavors** — dev and prod should point at different CometChat apps; do not test against production data.

## Pre-ship checklist
1. No Auth Key in the release artifact (verified by inspection, not assumption).
2. `loginWithAuthToken` is the only login path in prod code.
3. Logout clears the session **and** unregisters push.
4. Permission strings present on both platforms.
5. Release build (obfuscated) actually runs — chat renders, messages send.
6. Tested against the prod CometChat app, on real devices.
7. Errors surface to the user rather than being swallowed in an empty `onError`.

## Common pitfalls (BAKED)
- **Shipping the Auth Key** — the single most serious mistake here.
- **Assuming `--dart-define` is a secret** — it is compiled into the binary, same exposure.
- **Only testing debug builds** — obfuscation/minification problems appear only in release.
- **No logout path** → the session persists across users on a shared device.
- **Swallowing `onError`** → a production auth failure looks like a blank screen.
- **Minting tokens in the app** — that needs the REST key, which must never be in the client.

## Verify it works
The release artifact contains no Auth Key; sign-in goes through your backend; sign-out clears the session and push; a release build on a real device sends and receives; an expired token produces a clean re-auth rather than a blank screen.
