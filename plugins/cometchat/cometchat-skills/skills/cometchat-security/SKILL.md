---
name: cometchat-security
description: "Enterprise auth & access control for CometChat — SSO/OIDC/SAML via your own IdP, server-minted auth tokens, token revocation & session control, and role-based access (RBAC app-wide roles + group scopes). Cross-family: the server/REST side is the same everywhere; client login lands in each family's core/production skill. Triggers: 'add SSO to cometchat', 'SAML/OIDC login', 'okta/auth0/cognito with cometchat', 'role based access control', 'restrict what a user can do', 'revoke a user session', 'rotate/flush auth tokens', 'secure cometchat for enterprise', 'multi-tenant cometchat'."
license: "MIT"
compatibility: "CometChat REST API v3 (auth tokens · roles · users · group members). Client login via any family's UI Kit / SDK. Server: any language over HTTPS."
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat security sso saml oidc rbac roles auth-token session enterprise multi-tenant"
---

> **Ground truth:** every REST shape here is FETCHED from the live docs — `{DOCS_BASE}/rest-api/auth-tokens`, `/rest-api/roles`, `/rest-api/rbac-overview`, `/rest-api/users`, `/rest-api/group-members` (`DOCS_BASE = https://www.cometchat.com/docs`; append `.md` for the raw twin). **CometChat is NOT an identity provider** — it does not do SAML/OIDC for your end users. "SSO with CometChat" means *your* IdP authenticates the user, then *your server* mints a CometChat auth token for that user's UID. Verify signatures against the docs; never invent an endpoint.

## Use this skill when
Taking a CometChat integration through an enterprise security review: SSO with your IdP, role-based permissions, session revocation, multi-tenant isolation, or "make our chat secure/compliant to ship." Client-side login wiring itself lives in `cometchat-<family>-core` / `-production`; this skill owns the server + access-control model those depend on.

## The auth model (get this right first)
Three credentials, three homes — mixing them up is the #1 security defect:

| Credential | Who holds it | Purpose |
| --- | --- | --- |
| **Auth Key** | client, **dev only** | quick `login(uid)` in development; can mint a session for ANY user — never ship it |
| **Auth token** | client, per user | production login with a per-user token — the call is per family (web/Angular/Android/Flutter `loginWithAuthToken(token)`, **iOS `login(authToken:)`**, **React Native `login({ authToken })`**); tied to one UID; revocable |
| **REST API Key** | **server only** | mint tokens, manage users/roles; full power — never in a client |

Production login is always **auth token**, never the Auth Key. Detail + the per-framework client call: `cometchat-<family>-production`.

## SSO / OIDC / SAML — through YOUR IdP
CometChat rides on the identity you already have. The flow is the same whether your IdP is Okta, Auth0, Cognito, Entra ID, Google Workspace, or your own:

1. The user signs in through your IdP (SAML/OIDC) — your normal app auth.
2. Your backend, on that **authenticated session**, maps the IdP subject to a CometChat **UID** (a stable, sanitized id — see `cometchat-migrate-from-*` `toCometChatId` for the alpha-dash/≤100/lowercase rules) and, if the user is new, creates it (`POST {DOCS_BASE}/rest-api/users`, `withAuthToken: true` returns a token in the same call).
3. Your backend mints an auth token: `POST /v3/users/{uid}/auth_tokens` with the **REST API Key** (`{DOCS_BASE}/rest-api/auth-tokens/create`).
4. It returns the token to the client over the authenticated request; the client logs in with it via its per-family call (web/Angular/Android/Flutter `loginWithAuthToken(token)`, iOS `login(authToken:)`, React Native `login({ authToken })` — see `cometchat-<family>-production`).

**The UID must come from the server session, never a request parameter.** Accepting `?uid=` lets any caller impersonate anyone — the single most common CometChat auth hole.

```http
POST https://{APP_ID}.api-{REGION}.cometchat.io/v3/users/{uid}/auth_tokens
apikey: {REST_API_KEY}          # server-side secret
content-type: application/json
```

## Session control & revocation
Auth tokens **do not expire by default** and CometChat keeps a **rolling 100 per user** (oldest auto-archived). For enterprise session control:
- **Log out one device** → `DELETE /v3/users/{uid}/auth_tokens/{authToken}`.
- **Kill every session** (deprovisioned employee, suspected compromise) → `DELETE /v3/users/{uid}/auth_tokens` (flush all).
- **Rotate on privilege change / password reset** → mint a fresh token, flush the rest.
- **Short-lived sessions** → issue a token per login and flush on logout; don't reuse one token forever.
Pages: `{DOCS_BASE}/rest-api/auth-tokens/{delete,flush}`.

## Access control — RBAC (app-wide) + SBAC (per group)
CometChat has two layers; an action must pass **both** or the API returns `ERR_PERMISSION_DENIED`:

| Layer | Scope | Set via | Use it for |
| --- | --- | --- | --- |
| **Role (RBAC)** | whole app, one role per user | user create/update (`/rest-api/users`), roles (`/rest-api/roles`) | who may create groups, send messages, start calls, … |
| **Scope (SBAC)** | inside one group | group membership (`/rest-api/group-members/change-scope`) | `admin` / `moderator` / `participant` within that group |

- Define roles server-side via the REST **Roles** endpoint (`POST https://{APP_ID}.api-{REGION}.cometchat.io/v3/roles`; see the docs at `{DOCS_BASE}/rest-api/roles`) — each user gets exactly one; unspecified → `default`.
- Set the fine-grained permissions per role via **RBAC** (`{DOCS_BASE}/rest-api/rbac-overview`). *(The older per-role `restrict-features` API is **deprecated** — use RBAC.)*
- Group scopes (`admin`/`moderator`/`participant`) are the SBAC layer; change with the change-scope API.
Model least privilege: a locked-down `default` role, elevated roles for staff/moderators, plus group scopes for in-group moderation.

## Multi-tenant isolation
- **Strongest:** one CometChat **app per tenant** (separate App ID/keys — full data isolation). Best for regulated or contractual isolation.
- **Lighter:** one app, tenant-scoped **groups** + a tenant id in user/message **metadata**, enforced by your token server (a user only ever gets a token for their tenant's UID) + RBAC. Cheaper, but isolation is only as strong as your server checks.
Pick per your compliance bar; document which you chose. Data residency/region selection is `cometchat-compliance`; self-hosting for full sovereignty is `cometchat-self-host`.

## Common pitfalls
1. **Auth Key shipped to the client in production** — it can log in as anyone. Grep the bundle/binary (`cometchat-<family>-production`).
2. **Token endpoint trusting a client-supplied UID** — impersonation. Derive the UID from the server session.
3. **"CometChat SSO" misread as CometChat being the IdP** — it isn't; integrate your IdP, then mint a token.
4. **No revocation on offboarding** — a deprovisioned user keeps chatting until you flush their tokens.
5. **RBAC assumed but never configured** — every user sits on `default`; define roles + permissions explicitly.
6. **Using the deprecated `restrict-features`** instead of RBAC.
7. **REST API Key in client or repo** — server-only; store in a secret manager.

## Verify it works
IdP login → server mints a token from the session UID → the client's per-family auth-token login succeeds (`loginWithAuthToken` / iOS `login(authToken:)` / RN `login({ authToken })`) · a tampered/`?uid=` request is rejected · flushing a user's tokens ends their sessions on every device · a `default`-role user is denied a restricted action (`ERR_PERMISSION_DENIED`) while an elevated role is allowed · no Auth Key or REST API Key anywhere in client code.
