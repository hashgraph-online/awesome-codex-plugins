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
2. The plugin declares the server, so in most cases the first call simply opens a browser sign-in window. Tell the user to complete it and grant the requested scopes, which include `memory:read` and `memory:write`.
3. If no browser window appears, have the user run `/mcp` to inspect server status, or re-add manually: `claude mcp add --transport http mnemoverse https://mcp.mnemoverse.com/mcp`.

## If a call fails after it used to work

An expired token normally refreshes on the next tool call. If it does not, remove and re-add the server, then run the sign-in again.

## What the connection exposes

The memory tools the remote server serves: read, write, newest-first listing, stats, usefulness feedback, shared rooms, and a vault alias listing; the current list is at https://mcp.mnemoverse.com/.well-known/mcp/server-card.json. There is no delete tool on the remote server or in the local package, so a one-click sign-in can never wipe memory; deletion is an administrative REST operation, documented at https://mnemoverse.com/docs/api/remote-mcp-server.

## Privacy

Memory content is stored in the user's Mnemoverse account and follows the privacy policy at https://mnemoverse.com/privacy. Never store secrets, API keys, passwords, payment data, or personal identifiers in memory regardless of backend.
