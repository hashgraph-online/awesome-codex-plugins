# Security

## Reporting a vulnerability

Email contact@webly.ai with a description, steps to reproduce, and the affected URL or file. Please do not open a public issue for a security report.

## What this plugin contains

- `skills/webly/SKILL.md`: instructions for the agent.
- `skills/webly/scripts/webly.mjs`: a zero-dependency Node helper (Node 20+) that the skill runs to publish, sign in, and deploy. It sends files only when the user asks to publish or share them. When the user asks it to connect Webly, it runs the agent's own CLI (`claude plugin install` / `claude mcp add`, or `codex mcp add`) to register the Webly MCP server.
- `.mcp.json`: points to the hosted Webly MCP server at `https://api.webly.ai/v1/mcp` (OAuth sign-in, no API key).

## Network endpoints

| Endpoint | Used for |
| --- | --- |
| `https://api.webly.ai` | Publishing, sign-in, and the hosted MCP server |
| `http://127.0.0.1:<port>/callback` | Local OAuth sign-in callback |
| `https://raw.githubusercontent.com/Webly-AI/webly-plugin/main/...` | Checking for a newer plugin version |
| `https://*.webly.site` | Published sites |

## Credentials

The helper stores the anonymous site credential and sign-in state in `~/.webly/state.json` (file mode 0600) and sends it only to `https://api.webly.ai`.

## Data

Published sites are public unless the owner adds a password. Do not publish secrets or private data. See https://webly.ai/legal/privacy.
