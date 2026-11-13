# Security

## Reporting a vulnerability

Email **team@getosmo.app** with "Security" in the subject. Say what you found, how to reproduce it,
and which file or endpoint it affects. Please do not open a public issue for anything that could put
OsmO users, their accounts or the people they call at risk. We will reply to every report.

## What this repository contains

Instructions and manifests only:

- an Agent Skill (`skills/osmo-phone-calls/SKILL.md`)
- `GEMINI.md`
- plugin and extension manifests (`.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/`,
  `gemini-extension.json`, `mcp.json`)
- `server.json` (MCP Registry metadata)
- `llms-install.md`

It contains no scripts, hooks, binaries or dependencies, and nothing here runs on its own.

## What goes over the network

Every manifest registers one remote MCP server, `https://api.getosmo.app/mcp` (Streamable HTTP), and
nothing else. Your AI app signs in to it with OAuth 2.1 (PKCE, dynamic client registration). You
enter your phone number and a one-time code on OsmO's own page at
`https://api.getosmo.app/mcp/oauth/connect`. Your app then holds an access token for that host only.
No API key, password or token is stored in this repository or in these configs.

The README's "Authentication and network" section lists every endpoint.

## Scope

- **In scope here:** the files in this repository. For example, a manifest that points somewhere
  unexpected, or skill text that could lead an agent to leak data or call without consent.
- **The hosted service** (`api.getosmo.app`, the sign-in page, calls, the OsmO apps) is not in this
  repository. Report service issues to the same address.

## Handling your account

- Never paste the one-time sign-in code into a chat. The skill tells the agent never to ask for it.
- The skill also tells the agent never to ask the user, or tell OsmO to ask the person called, for card numbers, bank PINs,
  passwords, one-time codes or government ID numbers.
- To revoke access, remove OsmO from your AI app's connectors and, if you use the OsmO app, tap
  Disconnect under Sharing → Connect AI apps. You can also email team@getosmo.app.
