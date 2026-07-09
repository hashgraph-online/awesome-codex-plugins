---
name: coolify-setup
description: Connect, authenticate, configure, reset, or troubleshoot the Coolify Codex plugin connection. Use when the user asks to set up Coolify from the Codex marketplace, connect Coolify, configure saved credentials, log in, log out, switch Coolify instances, avoid environment variables, or resolve missing/invalid Coolify API token errors.
license: MIT
---

# Coolify Setup

Use this skill for first-time setup, marketplace onboarding, saved credentials, login/logout, and connection troubleshooting for the Coolify plugin.

## Marketplace Flow

Marketplace users should not need a repo checkout or shell command.

Before giving up on missing tools, call `tool_search` for `coolify_config_status coolify_configure mcp__coolify` when `tool_search` is available. The expected MCP namespace is `mcp__coolify`, and the setup tools are named `coolify_config_status`, `coolify_configure`, and `coolify_logout`.

1. Run `coolify_config_status` to see whether a connection is already saved.
2. If no usable connection exists, run `coolify_configure` without an `apiToken` argument.
3. Tell the user to complete the browser window that opens. The page first asks whether Coolify is Cloud-hosted or self-hosted; for self-hosted instances it asks for the URL before showing the matching token page.
4. Run `coolify_config_status` again after the user says they finished.
5. If configured, continue with the requested Coolify task or switch to the `coolify` skill for operational work.

`coolify_configure` returns a short-lived local setup URL. If the browser does not open automatically, provide that URL to the user.

If the Coolify MCP tools are not exposed in the thread after tool search, do not work around it by importing files from the current workspace or running repo-local setup code unless the user explicitly says they are developing this plugin from that checkout. For normal marketplace use, explain that the plugin's MCP tools did not load, ask the user to reinstall or update the plugin, and have them start a brand-new top-level thread so Codex can pick up the MCP server. Do not present a same-thread retry, delegated follow-up, or fork of the failed thread as the fix; those can preserve stale plugin capability metadata.

## Self-Hosted Instances

The browser setup handles self-hosted instances without requiring the user to paste a URL into chat.

If the user already gave the instance URL, call `coolify_configure` with `baseUrl` set to the instance root or `/api/v1` URL:

```json
{
  "baseUrl": "https://coolify.example.com"
}
```

The setup page links to the matching `/security/api-tokens` page after the instance URL is known.

## Storage

The token is stored locally:

- macOS Keychain when available.
- Windows Credential Manager when available.
- Linux Secret Service via `secret-tool` when available.
- Otherwise, a local config file under `CODEX_HOME` or `~/.codex` with owner-only permissions.

Environment variables are fallback-only for automation:

- `COOLIFY_BASE_URL`
- `COOLIFY_API_TOKEN`

Do not make marketplace users set these manually.

## Token Handling

- Coolify API authentication uses `Authorization: Bearer <token>`.
- Coolify does not currently document browser OAuth-style authorization for API clients.
- Ask users to create a least-privileged scoped token.
- Do not ask users to paste tokens into chat.
- Never print, summarize, or echo API tokens.

## Reset Or Switch Instance

- Use `coolify_logout` to forget the saved local connection.
- Then run `coolify_configure` again. The browser setup will ask whether the next connection is Coolify Cloud or self-hosted.

## Local Development Fallback

Use this only when the user is developing the plugin from a local checkout and specifically wants a terminal command. Marketplace users should use `coolify_configure` instead.

They can run:

```bash
npm run setup -- --save
```

For self-hosted instances:

```bash
npm run setup -- --save https://coolify.example.com
```
