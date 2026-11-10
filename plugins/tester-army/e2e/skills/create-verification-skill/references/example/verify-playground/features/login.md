# Sign in and dashboard

A cookie session: sign in on `/login`, land on `/dashboard`, sign out.

## Sub-features

- `Username` and `Password` fields, `Sign in` button. A wrong password
  stays on `/login` and shows the `Invalid credentials` alert.
- `/dashboard` greets the user in the `Greeting` status and offers
  `Sign out`; signed out, `/dashboard` redirects to `/login`.

## How to get to it (user POV)

Nav link `Login`, or `/login`. Account: the `admin` credential in
`e2e.config.ts` (never the password itself; `type_secret` over MCP,
`credentials.user('admin')` in a test).

## Driving it with e2e

`tests/auth.setup.e2e.ts` saves the `admin` session (a fill, so later
screenshots are withheld) and `admin-cookie` (a cookie, screenshots
stay); `tests/dashboard.e2e.ts` uses both and pins sign out and the
wrong-password alert. Locators: `screen.getByLabel('Username')`,
`screen.getByLabel('Password')`, `screen.getByRole('button', 'Sign in')`,
`screen.getByRole('alert')`, `screen.getByRole('status', 'Greeting')`,
`screen.getByRole('link', 'Sign out')`.

## Proof

The URL is `/dashboard` and `Greeting` reads `Welcome back, admin!`.
Store: a `session` cookie exists (`browser.cookies()`); after sign out it
is gone and `/dashboard` lands on `/login`.

## Charters

```
login-errors|web|default|Starting at /login, try a wrong password, an unknown account, and an empty form; report errors that are missing, misleading, or leak detail
```

Signed in, run alone with `--session admin-cookie`:

```
dashboard-signout|web|skeptic|Starting at /dashboard signed in as admin, sign out and go back; report state that survives sign out
```

## Gotchas

- `admin` is the dev account the app ships with; its existence is not a
  finding. A charter that fills the password prints no screenshot
  evidence after it; use the cookie session to keep them.
