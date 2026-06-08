# MailAgent Codex Plugin

MailAgent gives Codex temporary inboxes for signup QA, OTP emails, and magic links.

Bundled in [awesome-codex-plugins](https://github.com/hashgraph-online/awesome-codex-plugins) at `plugins/Alex0nder/mailagent`.

## Install

```bash
codex plugin marketplace add hashgraph-online/awesome-codex-plugins
codex plugin install mailagent --source mailagent
```

Or from the MailAgent repo marketplace:

```bash
codex plugin marketplace add Alex0nder/MailAgent
codex plugin install mailagent --source mailagent
```

## Setup

```bash
cd plugins/Alex0nder/mailagent
cp .env.example .env
chmod +x scripts/run-mailagent-mcp.sh
```

Put secrets in `.env` (gitignored). `MAILAGENT_API_URL` defaults to `https://api.webmailagent.com`.
`MAILAGENT_API_KEY` may also come from the parent process environment. Do not log or paste the key.

Get a key: https://webmailagent.com/dashboard.html (Team keys).

## Check MCP

```bash
codex mcp list
```

Expected: `mailagent` server with `mailagent_verify_signup` and `mailagent_create_inbox`.

## Verify signup flow

1. `mailagent_create_inbox` with `label` and `service`.
2. Submit returned `address` in the signup form.
3. `mailagent_wait_and_extract` with `inboxId` and `subjectContains`.
4. Use `otp` or `primaryLink` to finish signup.
5. `mailagent_delete_inbox` for cleanup.

If the form is already submitted, use `mailagent_verify_signup` to wait and extract in one call.

## Remote MCP (OAuth)

For Streamable HTTP without a local subprocess, see
[OAuth IdP docs](https://webmailagent.com/docs/oauth-idp.html) and use `https://api.webmailagent.com/mcp`
with a short-lived `mat_` bearer token.

This bundle keeps stdio MCP via `npx -y -p @mailagent/mcp@0.2.5 mailagent-mcp`.

Docs: https://webmailagent.com/docs/codex.html · Upstream: https://github.com/Alex0nder/MailAgent
