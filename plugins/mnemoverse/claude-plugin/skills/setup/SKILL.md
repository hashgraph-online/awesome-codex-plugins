---
name: setup
description: "Connects Mnemoverse memory for this plugin. Use when the user asks to connect or verify memory, when installed memory tools are missing, or when a memory call fails with an authentication error. Uses the current host's OAuth sign-in and verifies read access with memory_stats; no API key is pasted anywhere."
---

# Connecting Mnemoverse memory

This plugin talks to a hosted MCP server at `https://mcp.mnemoverse.com/mcp`. Authentication is a one-time browser sign-in (OAuth 2.1 with PKCE); there is no API key to paste.

## Check first

Identify this plugin's configured Mnemoverse server in the current host. A host-native entry may intentionally replace the plugin entry, as on Hermes Agent. Tool names may have a host prefix; similarly named tools from an unrelated server do not verify this connection. If the server cannot be identified, report that limitation instead of testing another connection.

If that server's `memory_stats` tool is available, call it with `{}` using the existing account context. It is read-only and takes no parameters; do not invent a domain filter. Confirm read access only when the tool returns a successful stats result, with neither `isError: true` nor an error payload. A valid result with `memory_count: 0` and `domains: []` still confirms the connection. An empty response, an error, or listed tools without a successful call does not.

Report only the connection status, without copying domains or memory content. Do not read stored memories, write synthetic memories, or change credentials, account, or access scopes just to test the connection. This check verifies read access, not writes. If setup was the only request, stop after reporting success. If the user already requested a memory task, continue it and report its actual tool result; the stats check does not establish that the task is complete.

## If tools or sign-in are missing

The user needs a Mnemoverse account: free tier at https://console.mnemoverse.com, no credit card. Use the current host's flow below. If the host is unknown, ask which app they are using before giving host-specific steps. Missing tools can mean the host has not enabled or loaded the configured server; inspect that entry before adding another server.

### Claude Code

The plugin declares the server, but installing it does not open a browser, and Claude Code does not start the sign-in by itself. Tell the user to run `/mcp`, select the Mnemoverse server (from this plugin it is listed as `plugin:mnemoverse:mnemoverse`) and choose Authenticate, then complete sign-in in the browser and approve the requested scopes, which include `memory:read` and `memory:write`.

Only if the server is absent from Claude Code's configuration, have the user add it for all their projects: `claude mcp add --transport http --scope user mnemoverse https://mcp.mnemoverse.com/mcp`, then authenticate from `/mcp`. Without `--scope user` the server is added for the current project only.

### Hermes Agent

Hermes Agent installs this repository as a plugin and loads its skills, but it does not start a sign-in for a server that comes from a plugin. Have the user add the hosted server once as Hermes' own entry, under the same name, in `~/.hermes/config.yaml`; preserve any existing configuration:

```yaml
mcp_servers:
  mnemoverse:
    url: "https://mcp.mnemoverse.com/mcp"
    auth: oauth
```

Then have the user run `hermes mcp login mnemoverse` (Hermes opens the browser and waits on a loopback callback). Check with `hermes mcp test mnemoverse`. Keep the name `mnemoverse`: the native entry shadows the plugin's copy, which cannot sign in. For a later authentication error, the same `hermes mcp login mnemoverse` starts a fresh sign-in. Full walkthrough: https://mnemoverse.com/docs/api/install-by-host#hermes-agent.

### Antigravity

The plugin's server is named `mnemoverse_mnemoverse` in Antigravity. Antigravity opens the browser for OAuth when that server first connects. Complete that sign-in in the browser. If it does not appear or fails, use Antigravity's connection controls for the same server and the [Antigravity setup guide](https://github.com/mnemoverse/claude-plugin/blob/main/antigravity/README.md). Do not run Claude Code's `/mcp` or add a Claude Code server to fix Antigravity.

### Other hosts

Follow the current host's [installation guide](https://mnemoverse.com/docs/api/install-by-host); for OpenClaw, use its [OpenClaw section](https://mnemoverse.com/docs/api/install-by-host#openclaw). Do not substitute Claude Code commands for another host's sign-in flow.

After tools become available or sign-in completes, repeat the read-only stats check above before reporting success. A host's probe or tool inventory alone does not replace it.

## If verification fails

- An authentication error (such as 401) means verification failed. Use the same host and configured server's authentication flow above. In Claude Code, choose Authenticate or Re-authenticate as offered; in Hermes, use `hermes mcp login mnemoverse`.
- A 403 means access was denied. Report the permission error; do not assume an expired token or broaden access to make the check pass.
- A timeout, transport failure, or other error leaves the connection unverified. Report the actual error without declaring sign-in successful or credentials invalid. Do not retry in a loop or switch accounts to make a check pass.

After the user completes authentication or the cause is resolved, repeat the read-only check before reporting success.

## What the connection exposes

The memory tools the remote server serves: read, write, newest-first listing, stats, usefulness feedback, shared rooms (beta), and a vault alias listing; the current list is at https://mcp.mnemoverse.com/.well-known/mcp/server-card.json. There is no delete tool on the remote server or in the local package, so a one-click sign-in can never wipe memory; deletion is an administrative REST operation, documented at https://mnemoverse.com/docs/api/remote-mcp-server.

## Privacy

Memory content is stored in the user's Mnemoverse account and follows the privacy policy at https://mnemoverse.com/docs/legal/privacy-policy. Never store passwords, API keys, tokens, payment data, MFA codes, government IDs or health records.
