---
name: cometchat-react-v7-production
description: "Ship a CometChat React v7 integration safely — server-minted auth tokens instead of the Auth Key, correct env prefixes per bundler, bundle hygiene, and a pre-launch checklist. Triggers: 'is this production ready', 'auth token instead of auth key react', 'secure my cometchat react setup', 'production build config react', 'going live checklist react', 'harden cometchat before launch'."
license: "MIT"
compatibility: "@cometchat/chat-uikit-react ^7 (7.1.x–7.2.x verified); React 18–19; Vite / Next.js / CRA / React Router / Astro"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat react v7 production security auth-token hardening deployment"
---

> **Ground truth:** `@cometchat/chat-uikit-react@7`. The auth-token / login API is FETCHED from the docs via `cometchat-react-v7-core/references/docs-map.md` (`/ui-kit/react/integration-react` + the JS SDK auth pages); the REST auth-token endpoint is `{DOCS_BASE}/rest-api/auth-tokens`. **The React UI Kit docs have no single production-hardening page** — this checklist is the pack's own guidance from `RULES.md` §4 (Credentials) + what the kit ships, labelled as such, not presented as documented. Tracked DOCS GAP.

## Companion skills (read first)
- `cometchat-react-v7-core` — `references/setup-credentials.md` + `references/lifecycle.md` cover the dev credential flow this replaces and the init→login→render order.
- `cometchat-react-v7-patterns` — the per-bundler env prefix + build specifics referenced below.
- `cometchat-security` — the enterprise auth model this client-side hardening plugs into: wiring your IdP / SSO into the token flow (your IdP → your server → mint the CometChat auth token; CometChat is **not** an IdP), token expiry/refresh + re-login, RBAC roles + group (SBAC) scopes, and Auth Key vs auth token vs REST API Key. Load it for a security review or any SSO question.

## Use this skill when
Moving off the development setup: going live, a security review, or "is this safe to ship."

## The one thing that matters
**Never ship the Auth Key in the browser bundle.**

The Auth Key can mint a session for **any user in your app**. Every `VITE_`/`NEXT_PUBLIC_`/`REACT_APP_`/`PUBLIC_`-prefixed value is compiled into JavaScript your users download — so an Auth Key there is public. Anyone can read it, log in as any UID, and read every conversation.

| | Development | Production |
| --- | --- | --- |
| Login | `CometChatUIKit.login(uid)` | `CometChatUIKit.loginWithAuthToken(token)` |
| Auth Key | in the client env | **absent from the bundle** |
| Token source | n/a | your backend, per authenticated user |
| REST API Key | never client-side | server only |

## The production login flow
1. Your app authenticates the user (your own auth — CometChat is not an identity provider).
2. Your **server** calls CometChat's REST API with the **REST API Key** to mint an auth token for that user's UID (`{DOCS_BASE}/rest-api/auth-tokens`).
3. The server returns the token to the browser over an authenticated request.
4. The app calls `loginWithAuthToken(token)`.

```tsx
// the endpoint derives the UID from the SERVER session — never from a query param
const res = await fetch("/api/cometchat-token", { credentials: "include" });
const { authToken } = await res.json();
await CometChatUIKit.loginWithAuthToken(authToken);
```
Accepting `?uid=` (or any client-supplied UID) lets a caller impersonate anyone. The UID must come from the server-side session.

## Env prefix — do NOT ship the key
Init reads the Auth Key from the client env in development. Production must set it empty and log in with a token instead. The prefix is bundler-specific (`cometchat-react-v7-patterns`): Vite `VITE_`, Next `NEXT_PUBLIC_` (`.env.local`), CRA `REACT_APP_`, Astro `PUBLIC_`. App ID and Region are not secrets — they identify the app; the Auth Key is the secret. **Grep the built bundle to be certain:**
```bash
npm run build && grep -rll "<your-auth-key>" dist/ build/ .next/ 2>/dev/null && echo "LEAK" || echo "clean"
```
Run that in CI — a stray `.env` or a wrong prefix ships the key silently.

## Also before launch
- **Users are created server-side**, as part of your signup — not from the browser (no `createUser` with the Auth Key in client code).
- **Log out properly**: `await CometChatUIKit.logout()`, then clear derived React state and unregister push tokens (`cometchat-react-v7-push`).
- **HTTPS everywhere** — required for calls (`getUserMedia`) and push.
- **Pin the kit** to an exact or `~` range so a minor cannot change component behaviour under you.
- **Keep `CometChatErrorBoundary`** wrapping the surface so a render error shows a fallback, not a white screen (it is not the initializer — init/login still run first).
- **SSR/StrictMode:** guard init+login so React 18/19 StrictMode's double-invoke does not race two logins (`cometchat-react-v7-patterns`); never init during SSR — gate on the client.
- **Region must match** the dashboard app in every build.
- **Enable dashboard extensions/AI on the PRODUCTION app**, not just dev.

## Pre-launch checklist
- [ ] Auth Key absent from the production bundle (grep-verified in CI)
- [ ] `loginWithAuthToken` in production; UID from the server session
- [ ] REST API Key server-side only
- [ ] Correct env prefix for the bundler; `.env` gitignored
- [ ] HTTPS, valid certificate
- [ ] Logout clears session, React state and push tokens
- [ ] Kit version pinned; `CometChatErrorBoundary` in place
- [ ] Dashboard extensions/AI enabled for the production app
- [ ] Tested against the production app's credentials

## Common pitfalls
1. **Auth Key in the production bundle** — the critical one; wrong env prefix is the usual cause.
2. **Token endpoint trusting a client-supplied UID** — impersonation.
3. **Init/login run during SSR or twice under StrictMode** — races and "already logged in" errors.
4. **Dashboard configured on the dev app only** — features silently missing in production.
5. **No logout teardown** — the next user inherits the session or the push token.

## Verify it works
Production build contains no Auth Key (grep) · login works via token · a tampered UID is rejected by the server · logout fully clears · calls and push work over HTTPS · features enabled on the production app.
