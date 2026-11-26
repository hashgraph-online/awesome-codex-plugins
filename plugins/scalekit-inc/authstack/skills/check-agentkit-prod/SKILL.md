---
name: check-agentkit-prod
description: >
  Checks AgentKit go-live so an agent can sign off only when
  every item is PASS or WAIVE with a reason.
  Use when the user wants AgentKit production, or to go live
  AgentKit.
  It does not write a connected account or token (that's `integrate-agentkit`)
  or check SaaSKit go-live (that's `check-saaskit-prod`).
---

# Check AgentKit go-live

Complete the AgentKit go-live record with PASS or WAIVE plus a reason on every item. Then stop.

## Guardrails

- **MUST** record `PASS` or `WAIVE` plus a one-line reason on every item. Sign off only when the record is complete.
- **MUST** use production credentials. `SCALEKIT_ENVIRONMENT_URL` ends in `.scalekit.com`, not `.scalekit.dev`.
- **MUST** keep credentials in environment variables only.

## Gotchas

- Read SDK credentials from `SCALEKIT_ENVIRONMENT_URL`, `SCALEKIT_CLIENT_ID`, and `SCALEKIT_CLIENT_SECRET`.
- A **connection** is dashboard connector config. A **connected account** is one user authorized on that connection.
- The **connection** already exists from `setup-agentkit`. If it does not, name `setup-agentkit` and stop.
- Dashboard and browser OAuth steps are **user actions**. Run SDK and curl yourself. Pause when the user must open the dashboard or a browser.
- A waiver needs a one-line reason. An empty result is a fail.
- If the app re-fetches the connected account before each call, waive local token-store items with that reason. Do not add a local vault.
- If Scalekit hosts OAuth (the `integrate-agentkit` path), waive app-callback, auth-code, and CSRF-`state` items with that reason. Do not add a local callback.
- Use the SDK path from `integrate-agentkit` for smoke-test calls. Do not rewrite that skill here.
- Prefer a non-customer test user. The host app may be local. Credentials must still be production AgentKit env vars.

## Step 1 — Open the record

Create a go-live record. One row per item in Steps 2–7. Columns: item, result (`PASS` or `WAIVE`), reason (required on `WAIVE`).

Example row: `webhook signature validation | WAIVE | app has no webhook`.

**Done when:** the empty record exists and lists every item from Steps 2–7.

## Step 2 — Quick checks

Run:

```bash
echo $SCALEKIT_ENVIRONMENT_URL
echo $SCALEKIT_CLIENT_ID
[ -n "$SCALEKIT_CLIENT_SECRET" ] && echo "SCALEKIT_CLIENT_SECRET is set" || echo "SCALEKIT_CLIENT_SECRET is NOT set"

curl -s -o /dev/null -w "%{http_code}" -X POST "$SCALEKIT_ENVIRONMENT_URL/oauth/token" \
  -d "client_id=$SCALEKIT_CLIENT_ID&client_secret=$SCALEKIT_CLIENT_SECRET&grant_type=client_credentials"

rg -n --hidden -g '!**/.git/**' -g '!**/node_modules/**' -g '!**/.env*' 'skc_|SCALEKIT_CLIENT_SECRET\s*=' . || true
```

`SCALEKIT_ENVIRONMENT_URL` must be `https://<subdomain>.scalekit.com`. Token endpoint must return `200`. The search must find no real secrets committed — only env var names or placeholders.

Record `PASS` or `WAIVE` plus a reason for:

1. `SCALEKIT_ENVIRONMENT_URL` ends in `.scalekit.com`
2. `SCALEKIT_CLIENT_ID` is set
3. `SCALEKIT_CLIENT_SECRET` is set
4. Token endpoint returns 200
5. HTTPS on every auth endpoint
6. No hardcoded secrets in source
7. Connection redirect URI on Dashboard → AgentKit → Connections matches the provider OAuth app (user verifies)

**Done when:** all 7 rows have `PASS` or `WAIVE` plus a reason.

## Step 3 — OAuth and token flows

Record `PASS` or `WAIVE` plus a reason for:

1. Authorization URL generated with the correct scopes
2. Callback validates `state` (CSRF)
3. Authorization-code exchange returns access and refresh tokens
4. Access tokens are not in localStorage or logs
5. Access tokens refresh before expiry
6. Concurrent refresh has no race
7. Expired refresh token prompts re-authorize
8. Logout or revocation clears stored tokens

**Done when:** all 8 rows have `PASS` or `WAIVE` plus a reason.

## Step 4 — Per connection

Name every connection this app already ships. Look up tools at https://docs.scalekit.com/agentkit/connectors.md. Do not copy that page.

For each of those connections, record `PASS` or `WAIVE` plus a reason for:

1. OAuth end-to-end
2. Minimum required scopes only
3. One `execute_tool` call on that connection succeeds
4. Expired token triggers refresh
5. Permission denied (user revoked access in the third-party app) is handled

**Done when:** every shipped connection has all 5 rows as `PASS` or `WAIVE` plus a reason.

## Step 5 — Security

Record `PASS` or `WAIVE` plus a reason for:

1. Access tokens are not logged or shown in error messages
2. Refresh tokens are encrypted at rest
3. Token storage is scoped per user — no cross-user access
4. Webhook or callback validates signatures when the app has one

**Done when:** all 4 rows have `PASS` or `WAIVE` plus a reason.

## Step 6 — Monitoring

Ask the user to open Dashboard → Auth Logs. You cannot open the dashboard.

Record `PASS` or `WAIVE` plus a reason for:

1. Auth logs monitoring is on
2. Error tracking covers OAuth failures and token refresh errors
3. Alerts fire on repeated authorization failures
4. Log retention is set
5. Incident runbook exists (who to contact; how to revoke a compromised token)

After go-live, track token refresh success rate, OAuth completion rate (started vs finished), per-service API error rates, and token expiry distribution.

**Done when:** all 5 rows have `PASS` or `WAIVE` plus a reason.

## Step 7 — Final smoke

Use `integrate-agentkit` for SDK calls. Pause for the user on browser OAuth. Default language is Python.

Default smoke connection is the Connection Name already recorded. If none, GitHub, Connection Name `github-connect`. Confirm the tool name on the connector's page in https://docs.scalekit.com/agentkit/connectors.md or with `list_tools` before calling it.

Record `PASS` or `WAIVE` plus a reason for:

1. `get_or_create_connected_account` returns a connected account for a test user
2. Auth link → user completes OAuth → re-fetch status is `ACTIVE`
3. One `execute_tool` call for that connected account succeeds
4. After the provider token expires, another `execute_tool` call still succeeds (Scalekit refreshes)
5. User revokes access in the third-party app → the app errors without leaking tokens

**Done when:** all 5 rows have `PASS` or `WAIVE` plus a reason.

## Step 8 — Sign off

Print the full record. If any item has no result, go back to that step. Do not sign off.

**Done when:** every item from Steps 2–7 is `PASS` or `WAIVE` plus a reason, and the user has the signed record.

## Reach for

- `integrate-agentkit` to create a connected account and one `execute_tool` call
- `setup-agentkit` if the connection or env is missing
- `check-saaskit-prod` for SaaSKit login, SSO, or SCIM go-live
- `discover-connectors` for the live tool catalog

## Live lookups

- Docs index: https://docs.scalekit.com/llms.txt
- Connector catalog: https://docs.scalekit.com/agentkit/connectors.md
- MCP: https://mcp.scalekit.com
