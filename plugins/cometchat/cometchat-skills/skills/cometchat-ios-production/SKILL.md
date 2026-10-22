---
name: cometchat-ios-production
description: "Ship a CometChat iOS (Swift) integration safely — server-minted auth tokens instead of the Auth Key, keeping secrets out of the app binary, and a pre-launch checklist. Triggers: 'is my cometchat ios production ready', 'auth token instead of auth key swift', 'secure cometchat ios', 'going live checklist ios', 'harden cometchat swift before launch'."
license: "MIT"
compatibility: "CometChatUIKitSwift 5.1.22 + CometChatSDK 4.1.7 (exact); Xcode 16+; iOS 15.1+; SPM only"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat ios swift production security auth-token hardening appstore"
---

> **Ground truth:** `CometChatUIKitSwift` 5.1.22 + `CometChatSDK` 4.1.7 (symbols verified vs `catalogs/ios-v5.json`). The login/auth-token API is FETCHED via `cometchat-ios-core/references/docs-map.md`; the REST auth-token endpoint is `{DOCS_BASE}/rest-api/auth-tokens`. **The iOS UI Kit docs have no single production-hardening page** — this checklist is the pack's own guidance from `RULES.md` §4 + `cometchat-ios-core/references/setup-credentials.md`, labelled as such. Tracked DOCS GAP.

## Companion skills (read first)
- `cometchat-ios-core` — `references/setup-credentials.md` (the `Secrets.xcconfig` → Info.plist → `Bundle.main` flow) and `references/swiftui.md` (the init→login launch hook) this hardens.
- `cometchat-security` — the enterprise auth model this client-side hardening plugs into: wiring your IdP / SSO into the token flow (your IdP → your server → mint the CometChat auth token; CometChat is **not** an IdP), token expiry/refresh + re-login, RBAC roles + group (SBAC) scopes, and Auth Key vs auth token vs REST API Key. Load it for a security review or any SSO question.

## Use this skill when
Moving off the development setup: TestFlight/App Store submission, a security review, or "is this safe to ship."

## The one thing that matters
**Never embed the Auth Key in the app binary.**

The Auth Key can mint a session for **any user in your app**. Anything baked into the app — an `xcconfig` value promoted into `Info.plist`, a string constant — is recoverable from the shipped `.ipa` (`strings`, class-dump). Treat it as public.

| | Development | Production |
| --- | --- | --- |
| Login | `CometChatUIKit.login(uid:...)` | `CometChatUIKit.login(authToken:...)` |
| Auth Key | in `Secrets.xcconfig` | **not in the build** |
| Token source | n/a | your backend, per authenticated user |
| REST API Key | never in the app | server only |

## The production login flow
1. Your app authenticates the user (your own auth / sign-in with Apple / your backend).
2. Your **server** mints a CometChat auth token for that user's UID via the REST API using the **REST API Key** (`{DOCS_BASE}/rest-api/auth-tokens`).
3. The server returns the token to the app over an authenticated HTTPS request.
4. The app calls `login(authToken:)`.

```swift
// UID comes from the SERVER session, never from the client
let authToken = try await fetchCometChatToken()   // your authenticated endpoint
CometChatUIKit.login(authToken: authToken) { result in /* handle success/failure */ }
```
`init` must resolve first (`initFromSettings`), then login — calling login before init resolves fails silently (`cometchat-ios-core`).

## Keep secrets out of the build
Development reads the Auth Key from a gitignored `Secrets.xcconfig` promoted into `Info.plist`. For production, ship **App ID + Region only** (not secrets — they identify the app) and log in with a token; leave the Auth-Key value empty in the release configuration.
```bash
# after an archive/build, confirm the key is not in the app binary
strings "$APP_BUNDLE/YourApp" | grep -q "<your-auth-key>" && echo "LEAK" || echo "clean"
```
Also verify `Secrets.xcconfig` is in `.gitignore` (only a committed placeholder), and that it is not bundled as a resource.

## Also before launch
- **Users are created server-side** as part of signup — not from the app with the Auth Key.
- **Log out properly**: `CometChatUIKit.logout()`, then clear derived state and unregister VoIP/APNs push tokens (`cometchat-ios-push`).
- **Pin exact versions** — the kit is a prebuilt binary compiled against one Chat SDK version; a drifting `CometChatSDK` breaks it (`cometchat-ios-core` Install).
- **App Transport Security**: keep HTTPS; do not add broad `NSAllowsArbitraryLoads` exceptions.
- **Calls need permissions**: `NSCameraUsageDescription` + `NSMicrophoneUsageDescription` with real strings, or App Review rejects; VoIP push needs the entitlement.
- **Region must match** the dashboard app.
- **Enable dashboard extensions/AI on the PRODUCTION app**, not just dev.

## Pre-launch checklist
- [ ] Auth Key not in the app binary (`strings`-verified)
- [ ] `login(authToken:)` in production; UID from the server session
- [ ] REST API Key server-side only
- [ ] `Secrets.xcconfig` gitignored; only a placeholder committed
- [ ] Exact kit/SDK/Calls versions pinned
- [ ] Camera/mic usage strings + VoIP entitlement present (if calling)
- [ ] Logout clears session, state and push tokens
- [ ] Dashboard extensions/AI enabled for the production app
- [ ] Tested against the production app's credentials

## Common pitfalls
1. **Auth Key recoverable from the `.ipa`** — the critical one.
2. **Token endpoint trusting a client-supplied UID** — impersonation.
3. **Login before init resolves** — silent no-render (order invariant).
4. **Missing usage-description strings** — App Review rejection for calling apps.
5. **Dashboard configured on the dev app only** — features silently missing in production.

## Verify it works
Archived build's binary contains no Auth Key (`strings`) · login works via token · a tampered UID is rejected by the server · logout fully clears · calls request permission and connect · features enabled on the production app.
