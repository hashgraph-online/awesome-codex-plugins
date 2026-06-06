# MailAgent Codex Plugin

MailAgent gives Codex temporary inboxes for signup QA, OTP emails, and magic links.

## Install

Use this directory as a local Codex plugin during development:

```bash
cd examples/codex/plugin
cp .env.example .env
chmod +x scripts/run-mailagent-mcp.sh
```

Open `examples/codex/plugin` as a trusted Codex project, or install the plugin through your local
Codex plugin workflow when publishing it to a marketplace.

## Environment

Put secrets in `examples/codex/plugin/.env`. The file is ignored by git.

```dotenv
MAILAGENT_API_URL=https://api.webmailagent.com
MAILAGENT_API_KEY=ma_or_mak_replace_me
```

`MAILAGENT_API_URL` defaults to `https://api.webmailagent.com` when omitted. `MAILAGENT_API_KEY`
may also come from the parent process environment. Do not log or paste the key.

## Check MCP

The plugin has one MCP server entry, `mailagent`, which launches the published npm stdio package:

```bash
codex mcp list
```

Expected result: the `mailagent` server is listed and tools include
`mailagent_verify_signup` and `mailagent_create_inbox`.

## Verify Signup Flow

For a full Codex-controlled signup flow:

1. Call `mailagent_create_inbox` with a useful `label` and `service`.
2. Submit the returned `address` in the signup form.
3. Call `mailagent_wait_and_extract` with `inboxId` and a `subjectContains` hint.
4. Use the returned `otp` or `primaryLink` to finish signup.
5. Call `mailagent_delete_inbox` for cleanup.

When the form was already submitted and you have `inboxId`, use `mailagent_verify_signup` to wait
and extract in one call.

## Remote MCP OAuth Preset

For remote Streamable HTTP MCP without a local subprocess, exchange a team API key for a short-lived
`mat_` token and use the preset in `../config.remote-oauth.toml.example`.

```toml
[mcp_servers.mailagent-remote]
url = "https://api.webmailagent.com/mcp"

[mcp_servers.mailagent-remote.http_headers]
Authorization = "Bearer mat_REPLACE_AFTER_OAUTH"
Accept = "application/json, text/event-stream"
```

Keep the plugin `.mcp.json` on the local stdio preset so it has a single entry through
`npx -y -p @mailagent/mcp@0.2.5 mailagent-mcp`.

Pack for marketplace: `npm run package:codex` from repo root → `dist/mailagent-codex-plugin-0.2.5.tar.gz`.

Install from GitHub marketplace (Codex CLI):

```bash
codex plugin marketplace add Alex0nder/MailAgent
codex plugin install mailagent --source mailagent
# set MAILAGENT_API_KEY when prompted (or in plugin .env after install)
```

Docs: https://webmailagent.com/docs/codex.html
