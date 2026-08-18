---
name: restricted-access
description: Use when a val's HTTP endpoints should not be open to the whole internet — limiting an app to a team, understanding why an endpoint redirects to a login page, letting a webhook through, or identifying which Val Town user is viewing an app. Covers app access (`httpPrivacy`), org grants, bypass tokens for automation, and the `X-Val-Town-User` identity header. For building your own login flow inside a val, see the `oauth` skill instead.
triggers: [restricted, access, private, permission, grant, allowed, team, internal, intranet, bypass, token, viewer, identity, login, redirect, "302", gated, unauthorized, forbidden]
---

# Restricted App Access

A val has two independent access settings. Changing one does not change the other:

- **Code** (`privacy`: `public` / `unlisted` / `private`) — who can read the source on val.town.
- **App access** (`httpPrivacy`: `public` / `restricted`) — who can call the val's HTTP endpoints.

A val can have private code and a wide-open endpoint, or public code and a locked-down endpoint. `update_val`'s `privacy` field only moves the first one; app access is changed with `set_http_privacy`.

Restricted app access is available to organizations that have the feature enabled. Vals created in such an org may default to `restricted` — always read `httpPrivacy` off a `get_val_detail`, `list_vals`, `create_val`, or `remix_val` response rather than assuming a new val's URL is open.

## Is this the right tool?

Two different things both sound like "make my app require a login":

- **Restricted app access** (this skill) gates the endpoint at the platform edge, before your code runs. Requests from people without access never reach the val. You write no auth code. Access is granted to whole organizations, not to individuals.
- **`std/oauth`** (see the `oauth` skill) runs *inside* your val: you wrap your handler, and anyone with a Val Town account can log in. You control the session and can build per-user features.

Pick restricted access for an internal tool that only your team should reach. Pick `std/oauth` when any Val Town user may sign in and the app needs its own notion of a logged-in user.

Don't stack them by accident. Adding `oauthMiddleware` to an already-restricted val means the visitor authenticates twice — once at the gate, once in your code. If a restricted val needs to know *who* is viewing, use the identity header below instead of adding OAuth.

## Who gets through

Access is granted to **organizations**, not individual people. A viewer gets in when the val has a grant to an org *and* that viewer is a member of it. Removing either one revokes access on the very next request — nothing is cached for the length of a session.

Grants come from:

- **Direct grants** — `add_allowed_user` grants an org, `list_allowed_users` shows current grants, `remove_allowed_user` revokes one.
- **Domain rules** — a val can admit everyone with an email address at a given domain. These appear in `list_allowed_users` alongside direct grants.
- **Invitations** — someone outside a granted org can be invited by email and gains access when they accept.
- **Bypass tokens** — a project-scoped secret for machines; see below.

## What everyone else sees

An unauthenticated request does **not** reach the val. The platform answers with a `302` redirect to a Val Town login or authorization page. This is the single most common source of confusion when debugging a restricted val:

- `fetch_val_endpoint` reports a redirect it won't follow.
- `curl` shows a `302` to `val.town` instead of your response.
- An API client gets HTML from a login page where it expected JSON.
- A visitor without access who *is* logged in gets a `403` explaining they need access to their organization.

None of these mean the val's code is broken. Check `httpPrivacy` first — if it's `restricted`, the gate is doing its job. Make the val public with `set_http_privacy`, grant the caller's org, or use a bypass token.

## Automation and webhooks

Machines can't complete a login redirect, so a restricted val that receives webhooks (Stripe, GitHub, a cron job in another val) needs a **bypass token** — a secret scoped to that one val.

Create it with `create_bypass_token`; the secret is shown once and cannot be retrieved again. Manage tokens with `list_bypass_tokens` and `revoke_bypass_token`.

Present it either way:

```ts
// Header (preferred — keeps the secret out of logs and referrers)
await fetch(url, { headers: { "X-Val-Town-Access": Deno.env.get("MY_BYPASS_TOKEN")! } });

// Query param (for services that only accept a URL, e.g. some webhook configs)
await fetch(`${url}?val_town_access=${Deno.env.get("MY_BYPASS_TOKEN")}`);
```

The platform strips the header and the query param before your handler runs, so your code never sees them. A bypass-token request carries **no viewer identity** — it is an anonymous machine caller.

## Identifying the viewer

For a human viewer who came in through the gate, the platform forwards a short-lived signed `X-Val-Town-User` header. It is not the identity itself — exchange it for the viewer's profile using the val's own API token, which Val Town injects as the `valtown` environment variable:

```ts
const IDENTITY_HEADER = "X-Val-Town-User";

/** Returns the viewer's public profile, or null when there isn't one. */
async function getViewer(req: Request) {
  const signed = req.headers.get(IDENTITY_HEADER);
  if (!signed) return null;

  const res = await fetch("https://api.val.town/v3/val/viewer", {
    headers: {
      Authorization: `Bearer ${Deno.env.get("valtown")}`,
      [IDENTITY_HEADER]: signed,
    },
  });
  if (!res.ok) return null;

  // { id, username, type, bio, profileImageUrl, url, links }
  return await res.json();
}
```

Rules that matter:

- **Always treat the viewer as optional.** There is none on a public val or a bypass-token request. Never `!`-assert it or index into a null result.
- **Resolve it server-side, on each request.** The credential is short-lived and tied to your val — don't persist it, hand it to the browser, or attempt the lookup from client-side code.
- **Only public profile fields come back** — handle, bio, avatar, profile URL. No email address, no billing tier. Don't build a val that depends on those.

The transport above (`X-Val-Town-User` plus the `/v3/val/viewer` exchange) is how this works today and may change; the three rules hold regardless.

## Managing app access

| Task | Tool |
| --- | --- |
| Check the current setting | `get_val_detail` (`httpPrivacy` field) |
| Make an endpoint public or restricted | `set_http_privacy` |
| See who has access | `list_allowed_users` |
| Grant / revoke an org | `add_allowed_user` / `remove_allowed_user` |
| Create / list / revoke automation secrets | `create_bypass_token` / `list_bypass_tokens` / `revoke_bypass_token` |

Restricted vals can only be iframed by val.town, so an embed of one on an external site will be blocked by the browser regardless of who's logged in.
