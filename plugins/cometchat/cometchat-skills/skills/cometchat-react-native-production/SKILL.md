---
name: cometchat-react-native-production
description: "Ship a CometChat React Native app safely — server-minted auth tokens instead of the Auth Key, what actually stays secret in a mobile bundle, release-build checks, and logout hygiene. Triggers: CometChat production React Native, auth token instead of auth key RN, secure CometChat RN, release build chat, is my auth key safe in the app."
license: "MIT"
compatibility: "React Native >=0.77; @cometchat/chat-uikit-react-native ^5.4.0; @cometchat/chat-sdk-react-native ^4.0.28"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "chat cometchat react-native production security auth-token release"
---

> **Ground truth:** `@cometchat/chat-uikit-react-native@5` + `catalogs/rn-sdk-v4.json`.
> Docs: `/ui-kit/react-native/react-native-cli-integration` · `/sdk/react-native/authentication-overview`.

## Companion skills (read first)
- `cometchat-react-native-core` — install, provider chain, init→login→render. Assumed, not repeated here.
- `cometchat-security` — the enterprise auth model this client-side hardening plugs into: wiring your IdP / SSO into the token flow (your IdP → your server → mint the CometChat auth token; CometChat is **not** an IdP), token expiry/refresh + re-login, RBAC roles + group (SBAC) scopes, and Auth Key vs auth token vs REST API Key. Load it for a security review or any SSO question.

## Use this skill when
- "is this safe to ship" · "swap the auth key for a token" · "prepare the release build"

## Prerequisites & install
None beyond `core`, plus a backend endpoint you control for minting tokens.

## The one rule: the Auth Key never ships

`login({ uid })` uses the **Auth Key**, which can create and impersonate any user in your app. Fine on
your laptop; unacceptable in a shipped binary.

### Nothing in a mobile app is secret
This is the part web developers get wrong. A React Native bundle is **not** a server. `.env` files,
`react-native-config`, `Constants.expoConfig`, obfuscation, ProGuard — all of them end up readable in
the shipped app. Anyone can unzip an IPA or APK.

"Hide the Auth Key in an env var" is not a mitigation. **Remove it.**

### Production shape

```tsx
import { CometChatUIKit } from "@cometchat/chat-uikit-react-native";

// your backend authenticates the user, then mints a short-lived CometChat
// auth token for that UID and returns it
const authToken: string = await fetchAuthTokenFromYourBackend();
await CometChatUIKit.login({ authToken });
```

The client never sees the Auth Key. The token is per-user, short-lived and revocable.
`UIKitSettings.authKey` is only needed for the `login({ uid })` path — a production build should not
carry it at all.

## User creation belongs on the server
`CometChat.createUser` needs the Auth Key, so it is a **backend** call made when your own signup
completes. A client that can create users can create *any* user.

## Logout hygiene
`CometChatUIKit.logout()` on sign-out, and **unregister the push token first** (see the `push` skill)
— otherwise the device keeps receiving the previous user's notifications. On a shared device that is
a privacy incident, not a bug.

## Before you ship
- **Test a release build**, not just debug. Some failures appear only there — most notably the
  `react-native-gesture-handler` import-ordering crash (`bare-patterns`).
- Build, then grep the output bundle for the Auth Key. It must not be present.
- Verify calls and push on **real devices** — neither is provable on a simulator.
- Check both platforms; Android and iOS diverge in native config, permissions and build failures.

## Common pitfalls
1. **Shipping the Auth Key** — env vars and obfuscation do not hide it.
2. **Creating users client-side** — needs the Auth Key; move it to the backend.
3. **Not unregistering push on logout** — the next user receives the previous user's messages.
4. **Signing off from a debug build** — release-only failures exist.
5. **Testing one platform only** — the native layer differs.

## Verify it works
- Every emitted symbol is in `catalogs/rn-sdk-v4.json` / `rn-v5.json`.
- `npm run verify:fences:rn-v5` is green.
- Grep a **release** bundle for the Auth Key — absent.
- Sign out, then confirm the device stops receiving that user's notifications.
