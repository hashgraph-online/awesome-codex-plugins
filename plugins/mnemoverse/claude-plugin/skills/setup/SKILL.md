---
name: setup
description: "Connects Mnemoverse memory for this plugin. Use when the user has installed the plugin but memory tools are missing, when a memory call fails with an authentication error, or when the user asks how to sign in to Mnemoverse. Walks through the one-time OAuth sign-in; no API key is pasted anywhere."
---

# Connecting Mnemoverse memory

This plugin talks to a hosted MCP server at `https://mcp.mnemoverse.com/mcp`. Authentication is a one-time browser sign-in (OAuth 2.1 with PKCE); there is no API key to paste.

## Check first

Look at the available tools. If tools named `memory_read`, `memory_write`, `memory_stats` and similar are present, the connection already works; nothing to set up. Tell the user and stop.

## If the tools are missing

1. The user needs a Mnemoverse account: free tier at https://console.mnemoverse.com, no credit card.
2. The plugin declares the server, but installing it does not open a browser, and Claude Code does not start the sign-in by itself. Tell the user to run `/mcp`, select the Mnemoverse server (from this plugin it is listed as `plugin:mnemoverse:mnemoverse`) and choose Authenticate, then complete the sign-in in the browser and grant the requested scopes, which include `memory:read` and `memory:write`.
3. If the server is not listed in `/mcp`, have the user add it for all their projects: `claude mcp add --transport http --scope user mnemoverse https://mcp.mnemoverse.com/mcp`, then authenticate from `/mcp` as in step 2. Without `--scope user` the server is added for the current project only.

## If a call fails after it used to work

An expired token normally refreshes on the next tool call. If it does not, have the user run `/mcp`, select the server and choose Re-authenticate.

## What the connection exposes

The memory tools the remote server serves: read, write, newest-first listing, stats, usefulness feedback, shared rooms, and a vault alias listing; the current list is at https://mcp.mnemoverse.com/.well-known/mcp/server-card.json. There is no delete tool on the remote server or in the local package, so a one-click sign-in can never wipe memory; deletion is an administrative REST operation, documented at https://mnemoverse.com/docs/api/remote-mcp-server.

## Privacy

Memory content is stored in the user's Mnemoverse account and follows the privacy policy at https://mnemoverse.com/docs/legal/privacy-policy. Never store secrets, API keys, passwords, payment data, or personal identifiers in memory regardless of backend.
