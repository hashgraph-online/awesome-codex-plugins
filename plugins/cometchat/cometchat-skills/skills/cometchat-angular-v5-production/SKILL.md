---
name: cometchat-angular-v5-production
description: "Ship a CometChat Angular integration safely — server-minted auth tokens instead of the Auth Key, environment file replacement, key hygiene, build config and a pre-launch checklist. Triggers: 'is this production ready', 'auth token instead of auth key angular', 'secure my cometchat setup', 'production build config', 'going live checklist'."
license: "MIT"
compatibility: "@cometchat/chat-uikit-angular ^5 (5.1.0–5.2.0 verified); Angular 17-21"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat angular production v5 security auth-token hardening deployment"
---

> **Ground truth:** `@cometchat/chat-uikit-angular@5` (5.1.0–5.2.0 verified). The auth-token API is FETCHED from `{DOCS_BASE}/ui-kit/angular/methods.md` and `/integration.md` (base + paths in `cometchat-angular-v5-core/references/docs-map.md`). **The Angular UI Kit docs have no dedicated production-hardening page** — the checklist below is the pack's own guidance, derived from the credential rules in `RULES.md` §4 and what the kit ships; it is labelled as such rather than presented as documented. Treat that as a tracked DOCS GAP.

## Companion skills (read first)
- `cometchat-angular-v5-core` — `references/setup-credentials.md` covers the dev credential flow this replaces.
- `cometchat-security` — the enterprise auth model this client-side hardening plugs into: wiring your IdP / SSO into the token flow (your IdP → your server → mint the CometChat auth token; CometChat is **not** an IdP), token expiry/refresh + re-login, RBAC roles + group (SBAC) scopes, and Auth Key vs auth token vs REST API Key. Load it for a security review or any SSO question.

## Use this skill when
Moving off the development setup: going live, a security review, or "is this safe to ship".

## The one thing that matters
**Never ship the Auth Key in the browser bundle.**

The Auth Key can mint a session for **any user in your app**. Anything in `environment.ts` is compiled into JavaScript your users download, so an Auth Key there is public. Anyone can read it, log in as any UID, and read every conversation.

| | Development | Production |
| --- | --- | --- |
| Login | `CometChatUIKit.login(uid)` | `CometChatUIKit.loginWithAuthToken(token)` |
| Auth Key | in `environment.ts` | **absent from the bundle** |
| Token source | n/a | your backend, per authenticated user |
| REST API Key | never client-side | server only |

## The production login flow
1. Your app authenticates the user (your own auth — CometChat is not an identity provider).
2. Your **server** calls CometChat's REST API with the **REST API Key** to mint an auth token for that user's UID.
3. The server returns the token to the browser over an authenticated request.
4. The app calls `loginWithAuthToken(token)`.

```ts
import { inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { CometChatUIKit } from '@cometchat/chat-uikit-angular';

const http = inject(HttpClient);

async function loginForCurrentUser() {
  // your endpoint, protected by your own session
  const { authToken } = await firstValueFrom(
    http.get<{ authToken: string }>('/api/cometchat-token', { withCredentials: true }),
  );
  return CometChatUIKit.loginWithAuthToken(authToken);
}
```

The endpoint must derive the UID from the **server-side session**, never from a request parameter. Accepting `?uid=` lets any caller impersonate anyone.

## Environment files
```ts
// src/environments/environment.prod.ts
export const environment = {
  production: true,
  cometchat: { appId: 'APP_ID', region: 'REGION', authKey: '' },   // empty on purpose
};
```
App ID and Region are not secrets — they identify the app. The Auth Key is the secret, and it is empty here. Confirm `fileReplacements` is wired in the production configuration, then **grep the built bundle** for the key to be certain:
```bash
ng build --configuration production && grep -r "YOUR_AUTH_KEY" dist/ || echo "clean"
```
Run that in CI. A misconfigured `fileReplacements` fails silently and ships the dev file.

## Also before launch
- **Users are created server-side**, as part of your signup — not from the browser.
- **Log out properly**: `await CometChatUIKit.logout()`, then clear derived state and unregister push tokens (`cometchat-angular-v5-push`).
- **HTTPS everywhere** — required for calls (`getUserMedia`) and push.
- **Pin the kit** to an exact or `~` range so a minor cannot change component behaviour under you.
- **Set a log level**: `CometChatUIKit.setLogLevel(...)` — quieter in production.
- **Handle errors visibly**: every list EXCEPT `<cometchat-call-logs>` has an `(error)` output — verified vs 5.1.0, its only outputs are `itemClick` and `callButtonClicked`; it takes an `onError` INPUT callback instead, so `(error)` there binds a DOM listener that never fires. Conversations / Users / Groups / GroupMembers / MessageList all do have `(error)`; wrap the surface in `<cometchat-error-boundary>`.
- **Teardown** — `ngOnDestroy` on every subscription and listener; leaks are worse in a long-lived SPA.
- **Region must match** the dashboard app, in every configuration you build.

## Pre-launch checklist
- [ ] Auth Key absent from the production bundle (grep-verified in CI)
- [ ] `loginWithAuthToken` in production; UID from the server session
- [ ] REST API Key server-side only
- [ ] `fileReplacements` verified by building, not by reading config — note the production build FAILS on the default 1 MB budget until you raise it (`cometchat-angular-v5-core` Install); the grep below never runs otherwise
- [ ] HTTPS, valid certificate
- [ ] Logout clears session, state and push tokens
- [ ] Kit version pinned
- [ ] Error boundary + error outputs handled
- [ ] Dashboard extensions/AI enabled for the production app, not just dev
- [ ] Tested against the production app's credentials

## Common pitfalls
1. **Auth Key in the production bundle** — the critical one.
2. **Token endpoint trusting a client-supplied UID** — impersonation.
3. **`fileReplacements` assumed rather than verified** — dev config ships.
4. **Dashboard configured on the dev app only** — features silently missing in production.
5. **No logout teardown** — the next user inherits the session or the push token.

## Verify it works
Production build contains no Auth Key · login works via token · a tampered UID is rejected by the server · logout fully clears · calls and push work over HTTPS · features enabled on the production app.
