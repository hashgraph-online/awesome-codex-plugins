# setup-credentials — App ID, Region, Auth Key on React Native

## The three values
From the CometChat dashboard: **App ID** · **Region** (`us` / `eu` / `in`) · **Auth Key**.
They go into `CometChat.CometChatSettings` — see `lifecycle.md`.

## Nothing in a mobile bundle is secret
This is the part web habits get wrong. A React Native bundle is **not** a server:

`.env` files · `react-native-config` · `Constants.expoConfig` · obfuscation · ProGuard —
**every one ends up readable in the shipped app.** Anyone can unzip an IPA or APK.

So "hide the Auth Key in an env var" is not a mitigation. It changes nothing.

## Dev vs production

| | Dev | Production |
|---|---|---|
| Login | `login({ uid })` with the Auth Key in settings | `login({ authToken })` |
| Auth Key ships? | acceptable locally | **never** |
| Token source | — | your backend mints a short-lived, per-user, revocable token |

```tsx
const authToken = await fetchAuthTokenFromYourBackend();
await CometChatUIKit.login({ authToken });
```

A production build should not carry `credentials.authKey` at all.

## Which UID to log in as
Use a UID that **already exists** in your dashboard app. The CometChat sample apps seed
`cometchat-uid-1` … `cometchat-uid-5`. **Never invent one** — login fails with a confusing error,
and it looks like a credential problem rather than a missing user.

Creating users needs the Auth Key, so `CometChat.createUser` is a **backend** call made when your own
signup completes. A client that can create users can create *any* user.

## Verify before shipping
Build a **release** bundle, then grep it for the Auth Key. It must not be present.
