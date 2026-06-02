---
name: codex-proxy-login
description: Use when configuring the local Codex CLI to authenticate with a ChatGPT account (OAuth) so the plugin marketplace, remote connections, and Codex Mobile stay usable, while routing all model traffic through an OpenAI-compatible relay/proxy (sub2api-style) with its own API key. Covers the login-first ordering, the experimental_bearer_token requirement, and recovering after Codex rewrites config.toml.
---

# Codex Proxy Login

## What This Solves

Pure API-key login (`auth_mode: apikey`) lets Codex talk to a third-party
OpenAI-compatible gateway, but it disables the plugin marketplace, remote
connections, and Codex Mobile. ChatGPT login (`auth_mode: chatgpt`) unlocks all
of those, but normally pins traffic to OpenAI's own endpoint.

This skill combines both: log in with a ChatGPT account to unlock the platform
features, then route model traffic through a relay/proxy using the proxy's own
bearer token. The result: plugins + Codex Mobile work *and* requests bill
against the proxy.

## Placeholders

Adapt before running. Never commit real values.

- proxy id: `<provider-id>` (e.g. `myrelay`)
- proxy base URL: `<proxy-base-url>` (must end in `/v1`, e.g. `https://api.example.com/v1`)
- proxy API key: `<proxy-api-key>` (the relay's own key, in its own key format)
- Codex home: `~/.codex/` (`config.toml`, `auth.json`)

## Critical Ordering — Log In First

`auth_mode: chatgpt` only works if `auth.json` already holds valid OAuth tokens.
A bare API-key `auth.json` has none, so flipping the mode by hand fails.

**Always run login before editing config:**

```bash
codex login        # choose "Sign in with ChatGPT"; opens a browser
# headless/remote host:
codex login --device-auth
```

Login writes `auth.json` to roughly:

```json
{ "auth_mode": "chatgpt", "OPENAI_API_KEY": null, "tokens": { ... }, "last_refresh": "..." }
```

Do **not** hand-edit `auth.json` — login produces the correct shape.

## config.toml — Proxy Provider Block

After login, ensure `~/.codex/config.toml` contains:

```toml
model_provider = "<provider-id>"

[model_providers.<provider-id>]
name = "<provider-id>"
base_url = "<proxy-base-url>"              # MUST end in /v1
experimental_bearer_token = "<proxy-api-key>"
requires_openai_auth = true

[features]
remote_connections = true
remote_control = true
```

## Gotchas (Each One Cost a Round-Trip)

1. **`requires_openai_auth = true` alone → `401 INVALID_API_KEY`.**
   Without `experimental_bearer_token`, Codex forwards the ChatGPT OAuth token as
   the Bearer credential, which the proxy rejects. The proxy needs *its own* key,
   supplied via `experimental_bearer_token`. Keep `requires_openai_auth = true`
   so Codex still injects the OpenAI-style auth headers the proxy expects.

2. **`base_url` must include `/v1`.** A bare host (no `/v1`) yields 401/404 from
   most relays. The error URL (e.g. `.../responses`) tells you which path Codex hit.

3. **Do not add `wire_api = "responses"` unless the proxy requires it.** The
   working setup omits it; adding it changed behavior and produced auth errors on
   at least one relay.

4. **`codex login` rewrites `config.toml` and drops custom lines.** After every
   login the `model_provider`, the `[model_providers.*]` block, and
   `remote_control` are frequently gone. **Re-verify and re-add after each login.**

5. **OAuth access tokens expire (~10 days).** When Codex shows "logged out" or
   reverts to ChatGPT-quota billing, the token lapsed — re-run `codex login`, then
   re-check config (see gotcha 4).

6. **Config switchers (cc-switch and similar):** keep the Codex entry on the
   official ChatGPT provider. The proxy routing lives in `config.toml`, not in the
   switcher — do not switch providers there.

## Verify

```bash
sh scripts/check-codex-proxy.sh        # reports any missing keys; prints no secret values
```

Or manually confirm presence (not values) of the required keys:

```bash
grep -nE 'model_provider|experimental_bearer_token|requires_openai_auth|remote_connections|remote_control' ~/.codex/config.toml
```

`auth.json` should show `auth_mode": "chatgpt"`, `OPENAI_API_KEY` null, and a
non-empty `tokens` object with a recent `last_refresh`.

Then restart Codex and confirm the plugin marketplace loads and a model turn
succeeds (billed against the proxy, not ChatGPT quota).

## Recovery Checklist

After a "logged out" or quota-reverted symptom:

1. `codex login` (ChatGPT).
2. Run the verify step — re-add any dropped provider/features lines.
3. Confirm `auth.json` has fresh tokens and `OPENAI_API_KEY: null`.
4. Restart Codex; test one turn.
