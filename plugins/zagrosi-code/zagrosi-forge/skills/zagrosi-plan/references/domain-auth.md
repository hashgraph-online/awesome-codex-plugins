# Domain Pack: Auth And Identity

Use this when a plan touches login, sessions, OAuth, SSO, permissions, account
linking, user profile identity, API keys, service tokens, or authorization.

## Evidence To Gather

- Existing session creation and lookup paths.
- Existing auth middleware, guards, route adapters, and policy helpers.
- Provider config loading and secret handling.
- User/account/external identity storage.
- Tests for login, logout, permissions, token expiry, and rejected access.
- Logging policy for auth failures and sensitive payloads.

## Plan Must Decide

- Which module owns identity proofing.
- Which module owns session or token persistence.
- How invalid state, expired credentials, replay, and provider denial fail.
- Whether account linking is explicit, implicit, blocked, or out of scope.
- Which result/error shapes route handlers consume.
- Rollout and rollback path through configuration.

## Tests First

- Valid auth creates the expected local session or token.
- Invalid state, missing credentials, expired token, or denied provider fails.
- Ambiguous account linking does not silently create access.
- Permission checks reject cross-account or wrong-role access.
- Logs exclude tokens, secrets, cookies, and raw provider payloads.
