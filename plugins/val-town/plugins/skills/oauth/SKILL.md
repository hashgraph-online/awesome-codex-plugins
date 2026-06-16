---
name: oauth
description: Use when a val needs to require login with a Val Town account — gating routes behind authentication, identifying the current user, building user-specific dashboards. Covers std/oauth's `oauthMiddleware` and `getOAuthUserData`, the auto-managed `/auth/*` routes, and session behavior. For third-party OAuth providers (Google, GitHub, etc.) see the `third-party-integrations` skill instead.
triggers: [oauth, auth, login, signin, sign-in, logout, session, user, authentication, account, gated, protected, private]
---

# OAuth (std/oauth)

Val Town provides zero-config "Log in with Val Town" via `std/oauth`. No database setup, no provider config — wrap your Hono fetch handler and you get login, logout, and session management for free. Sessions are stored in encrypted cookies and last 30 days.

This is for **Val Town account login only**. For Google / GitHub / Slack / etc. OAuth, see the `third-party-integrations` skill — those flows are documented per-service.

## Imports

```ts
import {
  getOAuthUserData,
  oauthMiddleware,
} from "https://esm.town/v/std/oauth/middleware.ts";
```

## Wrapping your app

`oauthMiddleware(handler)` takes your Hono fetch handler and returns a wrapped handler that injects three auto-managed routes:

- `GET /auth/login` — starts the login flow
- `GET /auth/callback` — completes the login flow
- `POST /auth/logout` — clears the session

Export the wrapped handler as the val's default:

```ts
import { Hono } from "npm:hono";
import { oauthMiddleware } from "https://esm.town/v/std/oauth/middleware.ts";

const app = new Hono();
app.onError((err) => Promise.reject(err));

app.get("/", (c) => c.text("hello"));

export default oauthMiddleware(app.fetch);
```

You don't write the `/auth/*` routes yourself — the middleware adds them. Don't shadow them in your own app.

## Reading the current user

Call `getOAuthUserData(rawRequest)` from any route. In Hono, `rawRequest` is `c.req.raw`. It returns the session data if the request is authenticated, or `null` otherwise.

```ts
interface SessionData {
  user: {
    id: string;
    username: string | null;
    email: string | null;
    bio: string | null;
    tier: "free" | "pro" | null;
    type: "user" | "org";
    url: string;
    links: {
      self: string;
      profileImageUrl: string | null;
    };
  };
  accessToken: string; // Val Town API token (act on behalf of the user)
  refreshToken?: string;
  idToken?: string;
  expiresAt: number; // Unix timestamp (ms)
  isOrgMember?: boolean; // true if user belongs to this val's org
}
```

```ts
app.get("/", async (c) => {
  const session = await getOAuthUserData(c.req.raw);
  if (session?.user) {
    return c.html(
      `<p>Logged in as ${session.user.username}</p>` +
      `<form method="POST" action="/auth/logout"><button>Log out</button></form>`
    );
  }
  return c.html(`<a href="/auth/login">Log in with Val Town</a>`);
});
```

## Gating routes

There's no built-in "require login" helper — gate routes by checking `getOAuthUserData` and returning a 401 or redirecting to `/auth/login` when the session is missing:

```ts
app.get("/dashboard", async (c) => {
  const session = await getOAuthUserData(c.req.raw);
  if (!session?.user) return c.redirect("/auth/login");
  return c.html(`<h1>Welcome ${session.user.username}</h1>`);
});
```

## What you don't need to configure

- No env vars — credentials and redirect URLs are handled by the platform.
- No callback URL setup — `/auth/callback` is wired automatically.
- No session store — sessions live in encrypted cookies.

## Verifying changes

After adding OAuth, call `fetch_val_endpoint` on a gated route to confirm it redirects or 401s when unauthenticated. The full login flow requires a real browser session and can't be exercised by `fetch_val_endpoint` alone — share the live URL and have the user try logging in.
