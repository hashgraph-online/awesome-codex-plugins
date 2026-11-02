# Security

## Reporting a vulnerability

Email **info@seonix.ai** with the subject `Security: Seonix MCP`. Include the steps to reproduce, the affected endpoint or file, and what you observed. Please do not open a public GitHub issue for a vulnerability.

We acknowledge reports within 3 business days and keep you informed until the issue is resolved. Please give us a reasonable time to fix the problem before disclosing it.

## Scope

- The hosted MCP server at `https://api.seonix.ai/mcp` and its OAuth endpoints (`/oauth/*`, `/.well-known/*`).
- The consent and connect pages at `https://app.seonix.ai`.
- The files in this repository (manifests, skills).

## What this plugin does and does not do

- It contains no executable code: only JSON manifests, Markdown skills and image assets. It runs no hooks and no local server.
- It sends requests only to `https://api.seonix.ai`, authenticated with an OAuth token the client obtained after you approved the grant, or with an API key you configured yourself.
- Secrets never live in this repository. Do not commit an API key or an OAuth client secret here.
- Tool results mark content that came from your website or the web as untrusted (`"untrusted": true` / `untrusted_source`), and the skills tell the agent not to follow instructions found in that content.
- Write tools (`start_scan`, `apply_fix`, `rollback_fix`, `acknowledge_issue`, `unacknowledge_issue`) require the `write` scope and, by the skills' rules, the user's explicit confirmation before each call.

## Revoking access

Open **Account → Agents** at `https://app.seonix.ai/account/agents` and revoke the grant or key. Changing your password revokes all of them.
