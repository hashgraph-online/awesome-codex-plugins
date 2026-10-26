---
name: taisly-social-media-posting
description: Connect AI agents to Taisly through MCP to publish and schedule videos, inspect history, and manage reposts.
version: 0.2.10
metadata:
  publicName: Taisly Social Media Posting Skill
---

# Taisly social posting

Full documentation: https://docs.taisly.com/docs/mcp

## Remote MCP

Prefer the existing Taisly MCP connection. OAuth already provides access; do not install the package, request an API key, or run local setup/checkin tools when remote MCP is available.

If it is not connected, help the user add `https://app.taisly.com/mcp` as a remote Streamable HTTP MCP server with OAuth in a compatible client. Client settings or workspace policies may require human action. After authorization, refresh tools according to the client's instructions.

1. Call `taisly_auth_status` and `taisly_platforms_list`. An empty account list is not a login failure.
2. Match the user's requested destinations to exact returned platform IDs.
3. For a missing social account, get permission to start connection, show the `connectUrl` from `taisly_platform_connect_start`, wait for browser approval, then check connection.
4. Read `taisly_platform_schema` and validate the public video URL, caption, destinations and schedule with `taisly_posts_validate`.
5. Show the final video, caption, exact accounts and schedule. Obtain user approval before calling `taisly_posts_create` with `confirmed: true`.
6. Save `historyId` and check `taisly_posts_status`. Accepted is not published; report each destination's `PENDING`, `SUCCESS` or `FAILED` result accurately. A scheduled post has not yet been published.
7. List existing repost rules and confirm source and destination accounts before creating a requested rule.

Only call tools advertised by the server. Remote MCP does not expose `taisly_agent_setup_start` or `taisly_agent_checkin`. Never print credentials. If access expires, use the client's OAuth reconnect action, not CLI installation or an API-key fallback. Do not blindly retry creation after a timeout; check history first.

## Developer and local-file alternatives

Remote MCP cannot read local files or private chat attachments. Ask for a public downloadable video URL. If the user explicitly needs a local-file workflow, explain the optional local MCP or CLI package before installing anything.

Package guide: https://docs.taisly.com/en/docs/agents/agent-kit
REST API: https://docs.taisly.com/en/docs/api

API keys and the npm package are developer alternatives, not prerequisites for remote MCP.
