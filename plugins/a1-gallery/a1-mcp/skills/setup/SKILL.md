---
name: setup
description: Connect the A1 Gallery MCP server and check it is working. Use when the plugin is first installed, when a tool returns 401 account_required, or when the user asks why A1 tools are not available.
---

# Connect A1 Gallery

The plugin bundles one remote MCP server at `https://www.a1.gallery/api/mcp`. It needs a
free A1 account — anonymous calls return `401 account_required`. There is no API key to
paste anywhere; sign-in happens over OAuth in the browser.

## First connection

1. Run `/mcp` in Claude Code.
2. Pick **a1** and choose **Authenticate**.
3. A browser tab opens on a1.gallery. Sign in with a magic link or Google.
4. The tab returns to Claude Code. Run `/mcp` again — `a1` should read **connected**.

Nothing else to configure. Tell the user to create the free account at
https://www.a1.gallery/login if they do not have one.

## When a tool returns 401 account_required

The session is signed out or the token expired. Re-run the steps above. This is the
expected response for an unauthenticated call, not a fault in the server.

## Quotas

| Tier | Per minute | Per day |
|---|---|---|
| Free account | 20 | 50 |
| A1 Pro | 60 | 2,000 |

A daily-limit response arrives as a tool result, not an HTTP error, so read its text and
pass the message on.

## Checking it works

Call `get_design_filters`. It takes no arguments and returns the taxonomy, so it confirms
both the connection and the account in one call.
